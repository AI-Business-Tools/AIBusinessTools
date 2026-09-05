#!/usr/bin/env python3
"""
profile_qsf.py — Derive a structural profile from a real Qualtrics .qsf export.

Adapted from the validate_output.py archetype in skill-engineer-master by Antony Evans
(edge-brain-lite, https://github.com/antonyevans/edge-brain-lite), CC BY 4.0.

Qualtrics publishes no schema for the .qsf format and warns against editing the file, so
the only trustworthy description of the format is a file Qualtrics itself produced. This
script turns such a file into the profile that build_qsf.py builds against and that
validate_qsf.py checks against. When Qualtrics changes the format, export any survey, re-run
this, and both scripts are current again; nothing else in the skill hardcodes a format
snapshot.

The profile carries structure and settings, never survey content. Question text, choice text,
and block names are dropped; what is kept per question type is the set of key names and their
JSON types, which is what a generator needs and what a reader of the profile should be able to
see without reading someone's survey. The survey's own name and its respondent-facing chrome
do reach the survey-options block, so --anonymize blanks those; see ACCOUNT_KEYS below.

Usage:
  python3 profile_qsf.py <export.qsf> [<export2.qsf> ...]
  python3 profile_qsf.py <export.qsf> -o /path/to/qsf-profile.json
  python3 profile_qsf.py <export.qsf> --anonymize      # blank the account IDs and the source filenames
  python3 profile_qsf.py <export.qsf> --print          # summarize to stdout, write nothing

Give it every export you have. Coverage is the obvious gain, but the bigger one is honesty
about which keys are optional: a key that all of one file's questions happen to carry looks
mandatory until a second file shows one without it. Account settings and the survey options
come from the first file named; question shapes are pooled across all of them.

Output: writes the profile JSON and prints a summary of what was found.

Error taxonomy:
  exit 0 — profile written
  exit 1 — the input is not a readable QSF (not JSON, or missing SurveyEntry/SurveyElements)
  exit 2 — bad arguments or unwritable output path
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

# Keys in SurveyEntry and in the SO (Survey Options) payload that identify a Qualtrics
# account, brand, or personal library rather than describing the survey's structure. They
# are kept by default because copying them forward is what makes a generated survey land in
# the right brand with the right theme; --anonymize blanks them for a profile that will be
# shared or published. These are not the only identifying values in a profile: the source
# filenames go with them, and build_profile blanks both under the same flag.
ACCOUNT_KEYS = (
    "SurveyOwnerID",       # the user; also doubles as their personal message library ID
    "SurveyBrandID",       # the Qualtrics brand (institution) the survey belongs to
    "DivisionID",          # sub-unit within the brand, often null
    "CreatorID",           # who created the source survey
    "SkinLibrary",         # brand theme library slug; wrong value silently falls back to default
    "Skin",                # named theme inside that library
    "SkinType",            # theme engine generation
    "EOSMessage",          # end-of-survey message ID, points into a message library
    "EOSMessageLibrary",   # the library holding it; equals SurveyOwnerID in practice
    "libraryId",
    "ThankYouEmailMessageLibrary",
    "ValidationMessageLibrary",
    "InactiveMessageLibrary",
    # Not account identifiers, but they are copied verbatim from a real export and carry a
    # secret or a real address when the source survey set one, so they are blanked by the same
    # flag. Empty in every export profiled here, which is exactly why they were missed.
    "Password",            # a password-protected source survey's password, in clear
    "RefererURL",          # the site a respondent must arrive from; a real institutional domain
    "EOSRedirectURL",      # where the survey sends people at the end; can be a real URL
    "nextButtonMid",       # the four *Mid keys are message-library IDs, set when the source
    "previousButtonMid",   # survey uses custom button, header, or footer text
    "headerMid",
    "footerMid",
    # Survey chrome, shown to respondents and copied whole from the source export. A branded
    # survey puts an institution's name, logo URL, contact address, or stylesheet here. All five
    # are Qualtrics defaults in the exports profiled so far, which is why they went unnoticed.
    "Header",              # banner on every page; holds a logo img tag and a name when branded
    "Footer",              # footer on every page; holds a contact address when branded
    "SurveyTitle",         # the browser tab title
    "ExternalCSS",         # URL of a stylesheet, usually on the institution's own server
    "InactiveMessage",     # what a respondent sees when they open a closed survey
    "SurveyName",          # the SO payload repeats the source survey's own name
    "ValidationMessage",   # free text shown when an answer fails validation
    "ThankYouEmailMessage",
    "SurveyLinkCompletedMessage",
)

# SurveyEntry keys that describe THIS survey rather than the account or the format. They are
# regenerated for every build, so the profile records only that they exist, not their values.
SURVEY_SPECIFIC_ENTRY_KEYS = (
    "SurveyID", "SurveyName", "SurveyDescription", "SurveyActiveResponseSet",
    "SurveyCreationDate", "LastModified", "LastAccessed", "LastActivated",
)

# Payload keys whose values are survey content and must never reach the profile.
CONTENT_KEYS = (
    "QuestionText", "QuestionText_Unsafe", "QuestionText_Safe", "QuestionDescription",
    "Choices", "Answers", "Description", "DataExportTag", "QuestionID",
)


def json_type(value):
    """Name the JSON type of a value, the way the profile records it."""
    if value is None:
        return "null"
    if isinstance(value, bool):          # checked before int: bool is a subclass of int
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def load_qsf(path: Path) -> dict:
    """Read a .qsf and confirm it is shaped like one. Exits 1 with a diagnosis if not."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error: could not read {path}: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(
            f"Error: {path} is not valid JSON ({e}).\n"
            "A .qsf exported from Qualtrics is plain JSON. If this file came from somewhere "
            "else, or was opened and re-saved by an editor that changed its encoding, "
            "re-export it from Qualtrics and retry.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not isinstance(data, dict) or "SurveyEntry" not in data or "SurveyElements" not in data:
        print(
            f"Error: {path} is JSON but not a QSF: a QSF has exactly two top-level keys, "
            "SurveyEntry and SurveyElements. Export the survey again from Qualtrics "
            "(Survey tab > Tools > Import/Export > Export Survey) and retry.",
            file=sys.stderr,
        )
        sys.exit(1)
    return data


def blocks_of(bl_payload):
    """Yield block objects from a BL payload, which is a dict in some Qualtrics versions and
    an array in others. Handling both is why this is a function and not an inline loop."""
    if isinstance(bl_payload, dict):
        return list(bl_payload.values())
    if isinstance(bl_payload, list):
        return list(bl_payload)
    return []


def build_profile(sources, anonymize: bool) -> dict:
    """Merge one or more exports into a single profile.

    Several exports are strictly better than one, and not only for coverage. A key that every
    instance in ONE file happens to carry looks mandatory; seen across four surveys it is
    revealed as optional. Profiling a single file produced exactly that false positive, warning
    that a grid was missing a randomization setting because all three grids in that one file
    were randomized.

    Account settings, survey options, and the scaffolding elements come from the FIRST export
    given, since those are one account's settings rather than something to average. Question
    shapes, validation shapes, and block forms are pooled across all of them.
    """
    primary_data, primary_name = sources[0]
    entry = primary_data.get("SurveyEntry", {})

    by_element = defaultdict(list)
    for el in primary_data.get("SurveyElements", []):
        if isinstance(el, dict):
            by_element[el.get("Element")].append(el)

    # Every SQ element across every export, which is what the question shapes are pooled from.
    all_sq = []
    for data, name in sources:
        for el in data.get("SurveyElements", []):
            if isinstance(el, dict) and el.get("Element") == "SQ":
                all_sq.append(el)

    # --- Survey options: the 54-key settings block, copied whole. These are settings, not
    # content, and copying them is what makes a generated survey behave like the source's
    # sibling rather than a Qualtrics default.
    survey_options = {}
    if by_element.get("SO"):
        survey_options = dict(by_element["SO"][0].get("Payload") or {})

    account = {}
    for key in ACCOUNT_KEYS:
        if key in entry:
            account[key] = entry[key]
        elif key in survey_options:
            account[key] = survey_options[key]
    if anonymize:
        account = {k: ("" if isinstance(v, str) else None) for k, v in account.items()}
        for key in ACCOUNT_KEYS:
            if key in survey_options:
                survey_options[key] = "" if isinstance(survey_options[key], str) else None

    # --- SurveyEntry: record the key set and the values of everything that is neither
    # account-specific nor regenerated per survey (SurveyLanguage, SurveyStatus, the zeroed
    # date fields), so the builder emits the same shape.
    entry_defaults = {
        k: v for k, v in entry.items()
        if k not in SURVEY_SPECIFIC_ENTRY_KEYS and k not in ACCOUNT_KEYS
    }

    # --- Fixed scaffolding elements. PROJ carries the schema version, and SCO and STAT are
    # small constant payloads; emitting them costs nothing and avoids finding out the hard
    # way whether they are required.
    scaffold = {}
    for name in ("PROJ", "SCO", "STAT"):
        if by_element.get(name):
            el = by_element[name][0]
            scaffold[name] = {
                "PrimaryAttribute": el.get("PrimaryAttribute"),
                "SecondaryAttribute": el.get("SecondaryAttribute"),
                "TertiaryAttribute": el.get("TertiaryAttribute"),
                "Payload": el.get("Payload"),
            }

    # --- Question profiles, keyed by the type triple that decides a question's shape, pooled
    # across every export supplied.
    question_profiles = {}
    validation_shapes = Counter()
    configuration_shapes = defaultdict(Counter)
    key_counts = defaultdict(Counter)
    for el in all_sq:
        payload = el.get("Payload") or {}
        combo = "/".join(
            str(payload.get(k)) for k in ("QuestionType", "Selector", "SubSelector")
            if payload.get(k) is not None
        )
        prof = question_profiles.setdefault(combo, {"count": 0, "keys": {}})
        prof["count"] += 1
        for key, value in payload.items():
            # Key names and JSON types only; a value here would be someone's question text.
            prof["keys"].setdefault(key, json_type(value))
            key_counts[combo][key] += 1
        validation = payload.get("Validation")
        if isinstance(validation, dict):
            settings = validation.get("Settings")
            if isinstance(settings, dict):
                validation_shapes[json.dumps(settings, sort_keys=True)] += 1
        config = payload.get("Configuration")
        if isinstance(config, dict):
            configuration_shapes[combo][json.dumps(sorted(config.keys()))] += 1

    # A key on every instance of a type is required; one on some of them is optional. Pooling
    # several exports is what makes this honest, because a single file's coincidences look
    # like rules.
    for combo, prof in question_profiles.items():
        seen = key_counts[combo]
        prof["optional_keys"] = sorted(k for k, n in seen.items() if n < prof["count"])
        prof["required_keys"] = sorted(k for k, n in seen.items() if n == prof["count"])

    # --- Block and flow shape. Which of the two BL forms this account emits decides what the
    # builder writes; a reader has to handle both regardless.
    bl_forms, block_types, flow_node_types = set(), set(), set()
    for data, name in sources:
        for el in data.get("SurveyElements", []):
            if not isinstance(el, dict):
                continue
            if el.get("Element") == "BL":
                payload = el.get("Payload")
                bl_forms.add("dict" if isinstance(payload, dict)
                             else "array" if isinstance(payload, list) else "unknown")
                block_types.update(
                    b.get("Type") for b in blocks_of(payload) if isinstance(b, dict)
                )
            elif el.get("Element") == "FL":
                flow = (el.get("Payload") or {}).get("Flow") or []
                flow_node_types.update(n.get("Type") for n in flow if isinstance(n, dict))

    # A source filename is survey content in every way that matters for sharing: these are
    # named after the course, the term, and the institution that ran them. Blanking the
    # account keys and leaving the filenames produced a profile that read as anonymized and
    # still carried two course codes and a school name.
    if anonymize:
        source_names = [f"export {i + 1}" for i in range(len(sources))]
        settings_source = "export 1"
        note = (
            "Derived from Qualtrics exports by profile_qsf.py --anonymize. Structure and "
            "settings only; no question, choice, or block text. Account identifiers and "
            "source filenames are blanked, so a survey built from this profile lands in the "
            "Qualtrics default theme. Re-derive without --anonymize from an export of the "
            "account being uploaded to before building a survey for that account."
        )
    else:
        source_names = [name for _, name in sources]
        settings_source = primary_name
        note = (
            "Derived from a Qualtrics export by profile_qsf.py. Structure and settings only; "
            "no question, choice, or block text. The 'account' section identifies a specific "
            "Qualtrics account, and the source filenames name real surveys; run --anonymize, "
            "which blanks both, before this profile is shared or published."
        )

    return {
        "generated": date.today().isoformat(),
        "sources": source_names,
        "settings_from": settings_source,
        "note": note,
        "schema_version": (scaffold.get("PROJ", {}).get("TertiaryAttribute")),
        "account": account,
        "survey_entry_defaults": entry_defaults,
        "survey_options": survey_options,
        "scaffold": scaffold,
        "question_profiles": question_profiles,
        "validation_shapes": [
            {"settings": json.loads(shape), "count": n}
            for shape, n in validation_shapes.most_common()
        ],
        "configuration_key_sets": {
            combo: [{"keys": json.loads(ks), "count": n} for ks, n in counter.most_common()]
            for combo, counter in configuration_shapes.items()
        },
        "block_payload_forms": sorted(bl_forms),
        "block_types": sorted(t for t in block_types if t),
        "flow_node_types": sorted(t for t in flow_node_types if t),
    }


def summarize(profile: dict) -> str:
    lines = [
        f"Profiled {len(profile['sources'])} export(s) "
        f"(Qualtrics schema {profile.get('schema_version')}); "
        f"settings from {profile['settings_from']}",
        *(f"    {n}" for n in profile["sources"]),
        f"  Block payload form(s): {', '.join(profile['block_payload_forms'])}"
        f"   Block types: {', '.join(profile['block_types'])}",
        f"  Flow node types: {', '.join(profile['flow_node_types'])}",
        f"  Survey options captured: {len(profile['survey_options'])} keys",
        f"  Account-specific values: {'blanked' if not any(profile['account'].values()) else 'kept'}",
        "  Question types evidenced across these exports:",
    ]
    for combo, prof in sorted(profile["question_profiles"].items(), key=lambda kv: -kv[1]["count"]):
        lines.append(f"    {combo:<34} {prof['count']:>3} instance(s), {len(prof['keys'])} keys")
    lines.append(f"  Validation shapes observed: {len(profile['validation_shapes'])}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Derive a structural profile from a real Qualtrics .qsf export."
    )
    parser.add_argument("exports", nargs="+",
                        help="One or more .qsf files exported from Qualtrics. Settings come "
                             "from the first; question shapes are pooled across all.")
    parser.add_argument(
        "-o", "--output",
        help="Where to write the profile (default: ../assets/qsf-profile.json beside this script)",
    )
    parser.add_argument(
        "--anonymize", action="store_true",
        help="Blank account, brand, theme, and message-library IDs before writing",
    )
    parser.add_argument(
        "--print", dest="print_only", action="store_true",
        help="Print the summary and write nothing",
    )
    ns = parser.parse_args()

    sources = []
    for name in ns.exports:
        src = Path(name)
        if not src.exists():
            print(f"Error: {src} does not exist. Check the path.", file=sys.stderr)
            sys.exit(2)
        sources.append((load_qsf(src), src.name))

    profile = build_profile(sources, ns.anonymize)

    print(summarize(profile))

    if ns.print_only:
        return

    out = Path(ns.output) if ns.output else Path(__file__).resolve().parent.parent / "assets" / "qsf-profile.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as e:
        print(f"Error: could not write {out}: {e}", file=sys.stderr)
        sys.exit(2)
    print(f"\nProfile written to {out}")


if __name__ == "__main__":
    main()
