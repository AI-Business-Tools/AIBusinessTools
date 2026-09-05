#!/usr/bin/env python3
"""
validate_qsf.py — Check a .qsf for the internal links Qualtrics does not check for you.

Adapted from the validate_output.py archetype in skill-engineer-master by Antony Evans
(edge-brain-lite, https://github.com/antonyevans/edge-brain-lite), CC BY 4.0.

Qualtrics publishes no schema and reports no import errors worth acting on, so a broken file
does not announce itself: a question missing from its block's element list is dropped from the
survey silently, a flow pointing at a block that is not there loses that block silently, and a
skip locator naming a choice position instead of a choice key sends respondents to the wrong
answer with no sign anything is wrong. Every check here exists because getting it wrong
produces a file that imports cleanly and is not the survey that was written.

Runs against any .qsf, generated or exported, so it can be pointed at a real Qualtrics export
to confirm the checks themselves are right.

Usage:
  python3 validate_qsf.py <file.qsf>
  python3 validate_qsf.py <file.qsf> --profile <qsf-profile.json>   # add shape conformance
  python3 validate_qsf.py <file.qsf> --quiet                        # errors only

Output: PASS or FAIL with every finding, each naming what breaks and what to do about it.

Error taxonomy:
  exit 0 — no errors (warnings may still be printed)
  exit 1 — at least one error: the file would import into the wrong survey
  exit 2 — bad arguments, or the file is not a readable QSF
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


# Every id body in a real Qualtrics export is 15 characters after its prefix. Prefixes that
# do NOT follow this rule are excluded: QID is a plain integer, FL_ is a sequential integer,
# and a preview link is a UUID.
EXPECTED_ID_BODY = 15
ID_PREFIX_RE = re.compile(r'"(SV_|RS_|BL_|URH_|MS_)([A-Za-z0-9]+)"')
EMBEDDED_PIPE_RE = re.compile(r'\$\{e://Field/([^}]+)\}')


def ID_SHAPES(qsf):
    """Yield (prefix, set of full ids) for every prefixed Qualtrics id in the file."""
    found = {}
    for prefix, body in ID_PREFIX_RE.findall(json.dumps(qsf)):
        found.setdefault(prefix, set()).add(prefix + body)
    return sorted(found.items())


class Findings:
    """Errors break the survey; warnings are cosmetic or unproven but import fine."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def blocks_of(bl_payload):
    """A BL payload is a dict keyed by stringified index in some Qualtrics versions and an
    array in others. A reader must handle both; only a writer gets to pick one."""
    if isinstance(bl_payload, dict):
        return list(bl_payload.values())
    if isinstance(bl_payload, list):
        return list(bl_payload)
    return []


def check(qsf, profile, f: Findings):
    entry = qsf.get("SurveyEntry") or {}
    elements = qsf.get("SurveyElements") or []

    by_element = {}
    for el in elements:
        by_element.setdefault(el.get("Element"), []).append(el)

    survey_id = entry.get("SurveyID")

    # --- ID shape. Qualtrics remaps IDs on import but checks their shape first: a file whose
    # IDs were 16 characters after the prefix instead of 15 was rejected outright, with no
    # message beyond "Something went wrong and the project wasn't created". Measured across
    # 221 IDs in five real exports, every one is 15.
    for prefix, found in ID_SHAPES(qsf):
        wrong = sorted({i for i in found if len(i) - len(prefix) != EXPECTED_ID_BODY})
        if wrong:
            f.error(
                f"{len(wrong)} {prefix} id(s) have a body that is not {EXPECTED_ID_BODY} "
                f"characters: {wrong[:3]}. Every id in a real Qualtrics export is "
                f"{EXPECTED_ID_BODY}, and an import rejects the file outright when they are "
                f"not, without saying why."
            )

    # --- Every element must carry the survey's own ID. A mismatched one is a sign the file was
    # assembled from two sources, and Qualtrics attributes the element to a survey that is not
    # this one.
    mismatched = [
        el.get("PrimaryAttribute") for el in elements if el.get("SurveyID") != survey_id
    ]
    if mismatched:
        f.error(
            f"{len(mismatched)} element(s) carry a SurveyID that is not the survey's own "
            f"({survey_id}): {mismatched[:5]}. Rebuild rather than patch; a file assembled "
            f"from two surveys will import as neither."
        )

    # --- The active response set must exist as an RS element.
    rs_ids = {el.get("PrimaryAttribute") for el in by_element.get("RS", [])}
    active = entry.get("SurveyActiveResponseSet")
    if active and active not in rs_ids:
        f.error(
            f"SurveyActiveResponseSet is {active} but no RS element declares it "
            f"(found: {sorted(rs_ids) or 'none'}). Responses would have nowhere to land."
        )

    # --- The load-bearing triangle: questions, blocks, and flow.
    sq_by_qid = {}
    for el in by_element.get("SQ", []):
        qid = el.get("PrimaryAttribute")
        payload = el.get("Payload") or {}
        if qid in sq_by_qid:
            f.error(f"Two SQ elements both claim {qid}. Question IDs must be unique.")
        sq_by_qid[qid] = payload
        if payload.get("QuestionID") != qid:
            f.error(
                f"{qid}: element PrimaryAttribute and Payload.QuestionID disagree "
                f"({qid} vs {payload.get('QuestionID')}). Qualtrics reads both."
            )
        if el.get("SecondaryAttribute") != payload.get("QuestionDescription"):
            f.warn(
                f"{qid}: element SecondaryAttribute does not match Payload.QuestionDescription. "
                f"Cosmetic; it is the label shown in the editor."
            )

    if not by_element.get("BL"):
        f.error("No BL element: the file declares no blocks, so it contains no survey.")
        return
    bl_payload = by_element["BL"][0].get("Payload")
    blocks = blocks_of(bl_payload)
    if not blocks:
        f.error("The BL element carries no blocks.")
        return

    # Every block ID is collected before any skip is checked. A skip almost always points
    # forward to a block that has not been reached yet, so checking as we go would report a
    # valid forward jump as a dangling reference.
    block_ids = {}
    for block in blocks:
        bid = block.get("ID")
        if bid in block_ids:
            f.error(f"Two blocks share the ID {bid}. Block IDs must be unique.")
        block_ids[bid] = block

    referenced_qids = Counter()
    for block in blocks:
        desc = block.get("Description")
        for item in block.get("BlockElements") or []:
            if item.get("Type") == "Page Break":
                continue
            qid = item.get("QuestionID")
            referenced_qids[qid] += 1
            if qid not in sq_by_qid:
                f.error(
                    f"Block {desc!r} lists {qid}, but no SQ element defines it. "
                    f"Qualtrics will show an empty slot or drop the block's ordering."
                )
            for skip in item.get("SkipLogic") or []:
                check_skip(skip, qid, sq_by_qid.get(qid) or {}, block_ids, set(sq_by_qid), f)
                # Qualtrics enforces this and says so in its own words: "Invalid Skip Logic:
                # cannot find destination in the block." A question-targeted skip can only
                # reach a question in the SAME block; crossing into the next one is what
                # ENDOFBLOCK is for. The file still imports, then shows this error in the
                # editor, so it is caught here rather than after an upload.
                dest = skip.get("SkipToDestination")
                if isinstance(dest, str) and dest.startswith("QID"):
                    here = {i.get("QuestionID") for i in (block.get("BlockElements") or [])}
                    if dest not in here:
                        f.error(
                            f"{qid}: skips to {dest}, which is in a different block. Qualtrics "
                            f"refuses this with \"cannot find destination in the block\". Use "
                            f"ENDOFBLOCK to reach the start of the next block, or move the "
                            f"target question into this one."
                        )

    # --- A question defined but never listed in a block is silently dropped from the survey.
    # This is the single most expensive failure the format allows, because the file imports
    # cleanly and the question is simply not there.
    trash_qids = {
        item.get("QuestionID")
        for block in blocks
        if block.get("Type") == "Trash"
        for item in block.get("BlockElements") or []
    }
    orphans = [q for q in sq_by_qid if q not in referenced_qids and q not in trash_qids]
    if orphans:
        f.error(
            f"{len(orphans)} question(s) are defined but listed in no block, so they will not "
            f"appear in the survey: {orphans}. Add them to a block's BlockElements."
        )
    duplicated = [q for q, n in referenced_qids.items() if n > 1]
    if duplicated:
        f.error(f"Question(s) listed in more than one place: {duplicated}. Each belongs to exactly one block.")

    # --- Every real export, and the one third-party generator whose output is known to
    # import, carries a Trash block. Whether Qualtrics requires it is unproven, but a file
    # without one differs from every known-good file in a way worth flagging.
    if not any(b.get("Type") == "Trash" for b in blocks):
        f.warn(
            "No Trash block. Every real export carries one, empty or not, and it is absent "
            "from the flow by design. Unproven as a requirement; emitted because every "
            "known-good file has one."
        )

    # --- Flow.
    if not by_element.get("FL"):
        f.error("No FL element: without a flow, Qualtrics does not know what order to show blocks in.")
    else:
        flow_payload = by_element["FL"][0].get("Payload") or {}
        flow = flow_payload.get("Flow") or []
        flow_block_ids = [n.get("ID") for n in flow if n.get("Type") in ("Block", "Standard")]
        for bid in flow_block_ids:
            if bid not in block_ids:
                f.error(
                    f"The flow points at block {bid}, which no BL entry defines. "
                    f"That block's questions will not be shown."
                )
        for bid, block in block_ids.items():
            if block.get("Type") == "Trash":
                continue
            if bid not in flow_block_ids:
                f.error(
                    f"Block {block.get('Description')!r} ({bid}) is defined but absent from the "
                    f"flow, so none of its questions will be shown."
                )
        seen_flow_ids = [n.get("FlowID") for n in flow]
        if len(seen_flow_ids) != len(set(seen_flow_ids)):
            f.error("Two flow nodes share a FlowID. Each node needs its own.")

    # --- Piped question references. Carry-forward and piped text address another question by
    # its ID from inside question, choice, or answer text. Nothing in Qualtrics reports a pipe
    # that names a question which is not there; it renders as nothing for every respondent.
    for qid, payload in sq_by_qid.items():
        for target, where in piped_references(payload):
            if target not in sq_by_qid:
                f.error(
                    f"{qid}: {where} carries a piped reference to {target}, which is not a "
                    f"question in this file. Every respondent sees an empty space where that "
                    f"text should be, and nothing reports it. This is what a rebuild produces "
                    f"when question ids are re-minted and the pipe text is copied across "
                    f"unchanged."
                )

    # --- A survey set to redirect must say where. Qualtrics accepts the file either way and
    # sends the respondent to a bare query string, which reads as a broken link at the exact
    # moment the survey ends, so nobody who finishes it reports the problem.
    so_payload = (by_element.get("SO") or [{}])[0].get("Payload") or {}
    if so_payload.get("SurveyTermination") == "Redirect" and not so_payload.get("EOSRedirectURL"):
        f.error(
            "the survey ends with a Redirect but EOSRedirectURL is empty, so respondents "
            "finishing it are sent to a bare query string. Set 'redirect_url' under "
            "'end_of_survey' in the spec, or end with the default message instead."
        )
    if so_payload.get("SurveyTermination") == "DisplayMessage" and not so_payload.get("EOSMessage"):
        f.error(
            "the survey ends on a custom message but names none, so respondents finishing it "
            "see a blank ending. Set 'message' under 'end_of_survey' in the spec, or end with "
            "the default message instead."
        )

    # --- Hidden-field references from question text. A question that pipes in an embedded
    # field the flow never declares renders an empty space for every respondent, the same
    # silent failure as a dangling carry-forward. Scoped to question, choice, and answer text
    # on purpose: EOSRedirectURL in the survey options legitimately pipes an undeclared field
    # in every real export, so a whole-file version of this check is a false positive.
    declared = set()
    if by_element.get("FL"):
        for node in ((by_element["FL"][0].get("Payload") or {}).get("Flow") or []):
            if node.get("Type") == "EmbeddedData":
                declared.update(fd.get("Field") for fd in (node.get("EmbeddedData") or []))
    for qid, payload in sq_by_qid.items():
        blob = json.dumps({k: payload.get(k) for k in ("QuestionText", "Choices", "Answers")})
        for field in set(EMBEDDED_PIPE_RE.findall(blob)):
            if field not in declared:
                f.error(
                    f"{qid}: pipes in the hidden field {field!r}, which the survey flow does "
                    f"not declare. It renders as nothing for every respondent. A rebuild that "
                    f"dropped the flow's embedded data does exactly this."
                )

    # --- Per-question internals.
    for qid, payload in sq_by_qid.items():
        check_orders(qid, payload, f)
        if profile:
            check_shape(qid, payload, profile, f)

    # --- QC's SecondaryAttribute is a high-water mark, not a count. It only has to exceed
    # every short-form QID in use; the export carries 116 against 26 questions. Questions
    # copied in from another survey keep that survey's 10-digit ID, which this counter never
    # issued and does not track, so they are excluded rather than compared against.
    if by_element.get("QC"):
        raw = by_element["QC"][0].get("SecondaryAttribute")
        numbers = [
            int(q[3:]) for q in sq_by_qid
            if q.startswith("QID") and q[3:].isdigit() and len(q[3:]) <= 6
        ]
        try:
            if numbers and int(raw) < max(numbers):
                f.warn(
                    f"QC high-water mark is {raw} but the largest question number in use is "
                    f"{max(numbers)}. Qualtrics recomputes this; harmless, but it should be at "
                    f"least as large."
                )
        except (TypeError, ValueError):
            f.warn(f"QC SecondaryAttribute {raw!r} is not a number.")


def check_skip(skip, enclosing_qid, payload, block_ids, all_qids, f: Findings):
    """A skip is the one place where being off by one silently sends people somewhere else.

    Deliberately permissive about shape, because a real Qualtrics export uses more forms than
    an obvious reading of the format suggests: a destination can be a question rather than a
    block boundary, a locator can address something other than a selectable choice, and the
    two locator fields can legitimately differ.
    """
    if skip.get("QuestionID") != enclosing_qid:
        f.error(
            f"{enclosing_qid}: a skip rule names QuestionID {skip.get('QuestionID')}, but it is "
            f"attached to {enclosing_qid}. The two must match."
        )
    choices = payload.get("Choices") or {}
    for field in ("ChoiceLocator", "Locator"):
        locator = skip.get(field)
        if not locator:
            f.error(f"{enclosing_qid}: a skip rule has no {field}.")
            continue
        # Only a SelectableChoice locator names a choice key. Real exports also use
        # ChoiceDisplayed and ChoiceTextEntryValue, which address the question as a whole and
        # have no key to check; checking those as keys reported a valid export as broken.
        if "/SelectableChoice/" in str(locator):
            key = str(locator).rsplit("/", 1)[-1]
            if key not in choices:
                f.error(
                    f"{enclosing_qid}: skip {field} points at choice key {key!r}, which this "
                    f"question does not have (its keys are {sorted(choices)}). The locator takes "
                    f"the choice's KEY, not its position on screen, so this sends respondents to "
                    f"the wrong answer."
                )
    destination = skip.get("SkipToDestination")
    if (destination not in ("ENDOFBLOCK", "ENDOFSURVEY")
            and destination not in block_ids and destination not in all_qids):
        f.error(
            f"{enclosing_qid}: skip destination {destination!r} is not ENDOFBLOCK, ENDOFSURVEY, "
            f"a block in this file, or a question in this file."
        )


PIPE_RE = re.compile(r"\$\{q://(QID[0-9]+)/")


def piped_references(payload):
    """Yield (target question id, where it was found) for every piped question reference.

    Pipes hide in three places, and a survey that carries them usually uses all three: the
    question text, the text of individual choices, and a matrix's answer labels.
    """
    for target in PIPE_RE.findall(payload.get("QuestionText") or ""):
        yield target, "the question text"
    for key, entry in (payload.get("Choices") or {}).items():
        if isinstance(entry, dict):
            for target in PIPE_RE.findall(entry.get("Display") or ""):
                yield target, f"choice {key}"
    for key, entry in (payload.get("Answers") or {}).items():
        if isinstance(entry, dict):
            for target in PIPE_RE.findall(entry.get("Display") or ""):
                yield target, f"answer {key}"


def check_orders(qid, payload, f: Findings):
    """ChoiceOrder and AnswerOrder must name exactly the keys that exist, and the Next* counters
    must exceed every key in use. The counters are an inequality, never max+1: the export has a
    question keyed 6,7,8,9 whose NextChoiceId is 11."""
    for keys_field, order_field, counter_field, what in (
        ("Choices", "ChoiceOrder", "NextChoiceId", "choice"),
        ("Answers", "AnswerOrder", "NextAnswerId", "answer"),
    ):
        keys = payload.get(keys_field)
        order = payload.get(order_field)
        if keys is None and order in (None, []):
            continue
        keys = keys or {}
        order = order or []
        # Order entries are compared as strings: a real export mixes ints and strings in one
        # array, so the numeric type carries no meaning.
        key_set = {str(k) for k in keys}
        order_set = {str(o) for o in order}
        missing = key_set - order_set
        extra = order_set - key_set
        if missing:
            f.error(
                f"{qid}: {sorted(missing)} exist in {keys_field} but are absent from "
                f"{order_field}, so they will not be displayed."
            )
        if extra:
            f.error(
                f"{qid}: {order_field} names {sorted(extra)}, which do not exist in "
                f"{keys_field}."
            )
        if len(order) != len(order_set):
            f.error(f"{qid}: {order_field} lists the same key more than once.")
        counter = payload.get(counter_field)
        numeric = [int(k) for k in key_set if str(k).lstrip("-").isdigit()]
        if numeric and isinstance(counter, int) and counter <= max(numeric):
            f.error(
                f"{qid}: {counter_field} is {counter} but a {what} key of {max(numeric)} is in "
                f"use. It must be strictly greater, or a new {what} added in Qualtrics will "
                f"collide with an existing one."
            )


def check_shape(qid, payload, profile, f: Findings):
    """Compare a question against the key set a real Qualtrics export uses for its type.

    A missing key is a warning rather than an error: the export itself shows several keys
    appearing on some instances of a type and not others, so absence is often legitimate.
    What this catches is a whole shape drifting away from what Qualtrics produces.
    """
    combo = "/".join(
        str(payload.get(k)) for k in ("QuestionType", "Selector", "SubSelector")
        if payload.get(k) is not None
    )
    profiles = profile.get("question_profiles", {})
    if combo not in profiles:
        f.warn(
            f"{qid}: question type {combo!r} does not appear in the profile's source export, so "
            f"its shape here is reconstructed rather than observed. Check this question first "
            f"after the upload."
        )
        return
    required = set(profiles[combo].get("required_keys") or [])
    missing = sorted(required - set(payload))
    if missing:
        f.warn(
            f"{qid} ({combo}): every {combo} in the source export carries {missing}, and this "
            f"one does not."
        )


def main():
    parser = argparse.ArgumentParser(description="Check a .qsf for broken internal links")
    parser.add_argument("qsf", help="Path to the .qsf to check")
    parser.add_argument(
        "--profile",
        help="Path to qsf-profile.json for shape conformance "
             "(default: ../assets/qsf-profile.json beside this script; pass 'none' to skip)",
    )
    parser.add_argument("--quiet", action="store_true", help="Print errors only")
    ns = parser.parse_args()

    path = Path(ns.qsf)
    if not path.exists():
        print(f"Error: {path} does not exist.", file=sys.stderr)
        sys.exit(2)
    try:
        qsf = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: {path} is not valid JSON ({e}).", file=sys.stderr)
        sys.exit(2)
    if not isinstance(qsf, dict) or "SurveyElements" not in qsf:
        print(f"Error: {path} is not a QSF (no SurveyElements).", file=sys.stderr)
        sys.exit(2)

    profile = None
    if ns.profile != "none":
        profile_path = Path(ns.profile) if ns.profile else Path(__file__).resolve().parent.parent / "assets" / "qsf-profile.json"
        if profile_path.exists():
            try:
                profile = json.loads(profile_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                print(f"Warning: profile {profile_path} is not valid JSON; skipping shape checks.")

    f = Findings()
    check(qsf, profile, f)

    if f.errors:
        print(f"FAIL: {len(f.errors)} error(s) in {path.name}")
        for e in f.errors:
            print(f"  ERROR  {e}")
    if f.warnings and not ns.quiet:
        for w in f.warnings:
            print(f"  warn   {w}")
    if not f.errors:
        questions = sum(1 for el in qsf["SurveyElements"] if el.get("Element") == "SQ")
        print(f"PASS: {path.name}, {questions} questions, every internal link resolves.")
        if f.warnings and not ns.quiet:
            print(f"  ({len(f.warnings)} warning(s) above; none of them stops an import.)")
    sys.exit(1 if f.errors else 0)


if __name__ == "__main__":
    main()
