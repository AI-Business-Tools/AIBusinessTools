#!/usr/bin/env python3
"""
build_qsf.py — Expand a survey spec into a Qualtrics .qsf import file.

Adapted from the validate_output.py archetype in skill-engineer-master by Antony Evans
(edge-brain-lite, https://github.com/antonyevans/edge-brain-lite), CC BY 4.0.

The spec (references/survey-spec.md) says what each question is; this expands that into the
cross-referenced JSON Qualtrics reads. The expansion is deterministic and mechanical, which
is the whole reason it is a script: the file's integrity rests on links that are invisible
when you write them by hand and silent when you get them wrong. A question missing from its
block's element list vanishes from the survey with no error, and a skip that names a choice's
screen position instead of its key sends people to the wrong answer.

Structural facts and account settings come from assets/qsf-profile.json, derived by
profile_qsf.py from a real Qualtrics export. Nothing about the format is hardcoded here
except the per-question-type shapes, which are documented with their evidence in
references/qsf-format.md.

Usage:
  python3 build_qsf.py <spec.json> -o <output.qsf>
  python3 build_qsf.py <spec.json> -o <output.qsf> --profile <qsf-profile.json>
  python3 build_qsf.py <spec.json> -o <output.qsf> --conservative

--conservative omits the reconstructed extras hung on a question: choice limits, write-in
boxes, and constant-sum totals. Question types are always kept, because dropping one does not
produce a safer file, it produces no file. Use it when a normal build has been rejected by
Qualtrics, to get a file that imports and needs those few settings added by hand.

Output: writes the .qsf and prints a build report listing what to check in Qualtrics after
the upload: unevidenced constructs, deliberate --conservative omissions, and advisories.

Error taxonomy:
  exit 0 — file written
  exit 1 — the spec is invalid (unknown type, bad skip target, missing required field)
  exit 2 — bad arguments, unreadable spec or profile, unwritable output
"""

import argparse
import json
import random
import re
import string
import sys
import uuid
from datetime import datetime
from html import escape as html_escape
from pathlib import Path

# Qualtrics IDs are mixed-case alphanumerics (base 62), FIFTEEN characters after the prefix.
# Measured across 221 IDs in five real exports (147 SV_, 46 BL_, 14 URH_, 10 RS_, 4 MS_):
# every single one is 15. An earlier reading of a single file said 16, and a file built with
# 16-character IDs was rejected by Qualtrics on import with "Something went wrong and the
# project wasn't created". Qualtrics does remap IDs on import, but it evidently checks their
# shape first, so this is a hard requirement rather than a cosmetic match.
ID_ALPHABET = string.ascii_letters + string.digits
ID_LENGTH = 15

# Question type triples: spec type -> (QuestionType, Selector, SubSelector).
# "evidenced" means the shape appears in the profile's source export, so it is known to be
# what this Qualtrics account actually produces. The rest are reconstructed from the format's
# documented conventions and are flagged in the build report; see references/qsf-format.md.
CHOICE_SELECTORS = {
    ("single", "vertical"):    ("MC", "SAVR", "TX"),
    ("single", "horizontal"):  ("MC", "SAHR", "TX"),
    ("single", "columns"):     ("MC", "SACOL", "TX"),
    ("single", "dropdown"):    ("MC", "DL", None),
    ("single", "select"):      ("MC", "SB", None),
    ("multi", "vertical"):     ("MC", "MAVR", "TX"),
    ("multi", "horizontal"):   ("MC", "MAHR", "TX"),
    ("multi", "columns"):      ("MC", "MACOL", "TX"),
    ("multi", "multiselect"):  ("MC", "MSB", None),
}
TEXT_SELECTORS = {"line": "SL", "box": "ML", "essay": "ESTB", "form": "FORM"}

# Layout defaults per select mode, applied when the spec omits "layout".
DEFAULT_LAYOUT = {"single": "vertical", "multi": "vertical"}

# QuestionDescription is the editor-facing label Qualtrics derives from the question text:
# plain text, collapsed whitespace, cut at a word boundary to at most this many characters
# including the trailing ellipsis. Matching the export's own derivation costs nothing.
DESCRIPTION_MAX = 100

# The order a real export writes SurveyEntry's keys in. Reordered to match for the reason given
# where it is used: an importer that gives no reason for a rejection makes every unnecessary
# difference from its own output a liability.
ENTRY_KEY_ORDER = (
    "SurveyID", "SurveyName", "SurveyDescription", "SurveyOwnerID", "SurveyBrandID",
    "DivisionID", "SurveyLanguage", "SurveyActiveResponseSet", "SurveyStatus",
    "SurveyStartDate", "SurveyExpirationDate", "SurveyCreationDate", "CreatorID",
    "LastModified", "LastAccessed", "LastActivated", "Deleted",
)


class SpecError(Exception):
    """A problem in the spec that the caller must fix. Message names the question."""


def mint(prefix: str, rng: random.Random) -> str:
    return prefix + "".join(rng.choice(ID_ALPHABET) for _ in range(ID_LENGTH))


def to_html(text: str, is_html: bool) -> str:
    """Render spec text as Qualtrics question HTML.

    Qualtrics' editor emits paragraphs as <div> and blank lines as <div><br></div>, and that
    is what this writes. Text pasted into the editor keeps whatever markup it arrived with,
    so real exports also contain <p> and <ul><li>; qsf_read.py turns those into line breaks
    on the way back, but a rebuild re-emits them as <div>, and the bullets do not survive.
    Plain text is escaped so that an ampersand or a less-than in a question does not silently
    become markup.
    """
    if is_html:
        return text
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if len(paragraphs) <= 1:
        return html_escape(paragraphs[0] if paragraphs else "", quote=False)
    parts = []
    for i, para in enumerate(paragraphs):
        if i:
            parts.append("<div><br></div>")
        parts.append(f"<div>{html_escape(para, quote=False)}</div>")
    return "".join(parts)


def to_description(html: str) -> str:
    """Derive QuestionDescription from question HTML the way the export does."""
    plain = re.sub(r"<[^>]+>", " ", html)
    plain = plain.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= DESCRIPTION_MAX:
        return plain
    cut = plain[: DESCRIPTION_MAX - 3]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut + "..."


# Carry-forward, and piped text generally, references another question by its Qualtrics ID:
# ${q://QID30/ChoiceGroup/SelectedChoices} shows whatever the respondent picked in QID30. A
# spec cannot know the minted IDs, so it names questions by its own ids and these rewrite them.
# ${answers:Q3} is the shorthand for the common case, the selected choices of question Q3.
PIPE_RE = re.compile(r"\$\{q://([^/}]+)((?:/[^}]*)?)\}")
ANSWERS_ALIAS_RE = re.compile(r"\$\{answers:([^}]+)\}")


def substitute_pipes(value, id_map, label):
    """Rewrite every piped question reference from a spec id to its minted Qualtrics ID.

    Walks the whole payload rather than named fields, because pipes appear in question text,
    in choice text, and in matrix answer text, and a missed one is not an error anywhere: it
    is a placeholder that silently renders as nothing for every respondent.

    Embedded-data pipes (${e://Field/...}) are left alone; they name a field, not a question.
    """

    def resolve(target):
        target = target.strip()
        if target in id_map:
            return id_map[target]
        raise SpecError(
            f"{label}: a piped reference names question {target!r}, which is not a question id "
            f"in this spec. Carry-forward names a question by its spec 'id', and the builder "
            f"translates that to the Qualtrics id. Known ids: {sorted(k for k in id_map if not k.startswith('QID'))}"
        )

    if isinstance(value, str):
        value = ANSWERS_ALIAS_RE.sub(
            lambda m: "${q://" + resolve(m.group(1)) + "/ChoiceGroup/SelectedChoices}", value
        )
        return PIPE_RE.sub(lambda m: "${q://" + resolve(m.group(1)) + m.group(2) + "}", value)
    if isinstance(value, dict):
        return {k: substitute_pipes(v, id_map, label) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute_pipes(v, id_map, label) for v in value]
    return value


def validation_settings(required, max_choices=None, min_choices=None, conservative=False,
                        notes=None, choice_count=None):
    """Build the Validation.Settings block.

    ForceResponse is the live switch; ForceResponseType remembers the last mode chosen and is
    only emitted alongside a matching ForceResponse, because the export shows the two drifting
    out of sync whenever ForceResponse is set to OFF.
    """
    if required is True:
        settings = {"ForceResponse": "ON", "ForceResponseType": "ON", "Type": "None"}
    elif required == "request":
        settings = {"ForceResponse": "RequestResponse", "ForceResponseType": "RequestResponse", "Type": "None"}
    else:
        settings = {"ForceResponse": "OFF", "Type": "None"}

    if max_choices or min_choices:
        if conservative:
            if notes is not None:
                notes.append("choice limit omitted (conservative build); set it in Qualtrics by hand")
        else:
            # Evidenced in a real export: Qualtrics writes a "choose up to N" limit as a single
            # ChoiceRange carrying BOTH bounds as strings. It does not name one bound in Type.
            # An unstated lower bound is 1, which is what a real up-to-N question carries; an
            # unstated upper bound is every choice there is.
            settings["Type"] = "ChoiceRange"
            settings["MinChoices"] = str(min_choices or 1)
            settings["MaxChoices"] = str(max_choices or choice_count or 1)
            # The only observed ChoiceRange in a real export carries BOTH bounds, so a spec
            # that states one bound gets the other filled in. That is a rule the survey did
            # not ask for, and it must never be applied silently: an audit caught a
            # "choose up to 3" question that had quietly become "choose 1 to 3".
            if notes is not None and not min_choices:
                notes.append(
                    "a choice limit stated only as a maximum was written as a range with a "
                    "minimum of 1, because that is the only shape a real export uses; say "
                    "min_choices in the spec to make it deliberate"
                )
    return {"Settings": settings}


def build_randomization(setting, texts, label):
    """Build the Randomization block from a spec setting.

    Two real shapes. `true` randomizes every choice and is the simple form Qualtrics writes as
    Type "All". Pinning some choices takes the Advanced form, where FixedOrder carries one slot
    per choice: the marker {~Randomized~} for a slot the shuffled pool fills, or the choice's
    own key for a slot that stays put. Both shapes come from real exports.

    Pinning matters more than it looks. A list ending in "Nothing is standing in the way",
    "I do not know", and "Other (please describe)" reads as nonsense once those are shuffled
    into the middle, so the useful form is almost always "randomize all but the last few".
    """
    if setting in (True, "all"):
        return {"Advanced": None, "Type": "All", "TotalRandSubset": ""}
    if not isinstance(setting, dict):
        raise SpecError(
            f"{label}: 'randomize' must be true, or an object with 'except_last' (a count of "
            f"trailing choices to leave in place) or 'fixed' (the exact text of each choice to "
            f"leave in place)."
        )
    n = len(texts)
    fixed = set()
    if "except_last" in setting:
        keep = int(setting["except_last"])
        if not 0 <= keep < n:
            raise SpecError(
                f"{label}: 'except_last' is {keep}, but the question has {n} choices, so there "
                f"would be nothing left to shuffle."
            )
        fixed = set(range(n - keep + 1, n + 1))
    elif "fixed" in setting:
        if not setting["fixed"]:
            raise SpecError(
                f"{label}: 'randomize.fixed' is empty. An empty pin list used to build as "
                f"'randomize everything', which is the opposite of what pinning means. Name "
                f"the choices to hold in place, or drop 'randomize' from this question."
            )
        for text in setting["fixed"]:
            if text not in texts:
                raise SpecError(
                    f"{label}: 'randomize.fixed' names {text!r}, which is not one of this "
                    f"question's choices. Choices are: {texts}"
                )
            fixed.add(texts.index(text) + 1)
    else:
        raise SpecError(f"{label}: 'randomize' needs either 'except_last' or 'fixed'.")
    if len(fixed) >= n:
        raise SpecError(f"{label}: every choice is pinned, so nothing would be randomized.")
    return {
        "Type": "Advanced",
        "Advanced": {
            "FixedOrder": [
                str(i) if i in fixed else "{~Randomized~}" for i in range(1, n + 1)
            ],
            "RandomizeAll": [str(i) for i in range(1, n + 1) if i not in fixed],
            "RandomSubSet": [],
            "ScaleReversal": [],
            "Undisplayed": [],
            "TotalRandSubset": 0,
        },
        "ConsistentScaleReversal": False,
        "EvenPresentation": False,
        "TotalRandSubset": "",
    }


def build_choices(items, conservative, notes, kind="choice"):
    """Turn a spec choice list into Choices, ChoiceOrder, and the next free key.

    Choice keys are opaque stringified ints. They are minted 1..n here, but nothing downstream
    may assume that: a skip locator must use the key, and NextChoiceId only has to exceed
    every key in use, never equal max+1.
    """
    choices, order = {}, []
    for i, item in enumerate(items, start=1):
        key = str(i)
        if isinstance(item, dict):
            text = item.get("text")
            if not text:
                raise SpecError("a choice object has no 'text'")
            entry = {"Display": html_escape(text, quote=False)}
            if item.get("write_in"):
                if conservative:
                    notes.append(f"write-in box on '{text}' omitted (conservative build)")
                else:
                    # The flag's VALUE differs by where the box sits, which is not something
                    # any documentation says and is visible only in real exports: a
                    # multiple-choice option carries "true", a form field carries "on" plus
                    # its input size. Emitting "on" on a multiple-choice option was wrong.
                    if kind == "form":
                        entry["TextEntry"] = "on"
                        entry["InputHeight"] = 29
                        entry["InputWidth"] = 60
                    else:
                        entry["TextEntry"] = "true"
        else:
            entry = {"Display": html_escape(str(item), quote=False)}
        choices[key] = entry
        order.append(i)
    return choices, order, len(items) + 1


def build_answers(items):
    """Matrix scale points. AnswerOrder is emitted as strings, matching the export."""
    answers, order = {}, []
    for i, item in enumerate(items, start=1):
        answers[str(i)] = {"Display": html_escape(str(item), quote=False)}
        order.append(str(i))
    return answers, order, len(items) + 1


def base_payload(qid, tag, html, qtype, selector, subselector=None):
    payload = {
        "QuestionText": html,
        "QuestionText_Unsafe": html,
        "QuestionType": qtype,
        "Selector": selector,
        "Configuration": {"QuestionDescriptionOption": "UseText"},
        "QuestionDescription": to_description(html),
        "DataExportTag": tag,
        "QuestionID": qid,
        "DataVisibility": {"Private": False, "Hidden": False},
        "GradingData": [],
        "Language": [],
        "DefaultChoices": False,
        "NextChoiceId": 1,
        "NextAnswerId": 1,
    }
    if subselector:
        payload["SubSelector"] = subselector
    return payload


def build_question(q, qid, tag, evidenced, conservative, notes):
    """Build one question payload. Raises SpecError with a fixable message on bad input."""
    qtype = q.get("type")
    label = q.get("id") or tag
    text = q.get("text")
    if qtype != "page_break" and not text:
        raise SpecError(f"{label}: every question needs 'text'")
    html = to_html(text or "", bool(q.get("html")))
    # The default: a question not marked optional prompts once if it is skipped and
    # lets the respondent continue. Only "required": false makes it silently skippable, and
    # only "required": true blocks them.
    required = q.get("required", "request")

    def note_if_unevidenced(combo):
        # A reconstructed question TYPE is reported but never refused, including under
        # --conservative. Refusing one does not produce a safer file, it produces no file:
        # a survey with a multi-select question cannot be built without a multi-select
        # question. What --conservative drops is the reconstructed extras hung on a type,
        # which a survey can lose and still be the same survey.
        if combo not in evidenced:
            notes.append(f"{label}: question type '{combo}' is not evidenced in the profile")

    if qtype == "descriptive":
        note_if_unevidenced("DB/TB")
        payload = base_payload(qid, tag, html, "DB", "TB")
        payload["ChoiceOrder"] = []
        payload["Validation"] = {"Settings": {"Type": "None"}}
        return payload

    if qtype == "choice":
        select = q.get("select", "single")
        if select not in ("single", "multi"):
            raise SpecError(f"{label}: 'select' must be 'single' or 'multi', got {select!r}")
        layout = q.get("layout", DEFAULT_LAYOUT[select])
        key = (select, layout)
        if key not in CHOICE_SELECTORS:
            raise SpecError(
                f"{label}: layout {layout!r} is not available for a {select}-answer question. "
                f"Options: {sorted(l for s, l in CHOICE_SELECTORS if s == select)}"
            )
        qt, sel, sub = CHOICE_SELECTORS[key]
        note_if_unevidenced("/".join(p for p in (qt, sel, sub) if p))
        choices = q.get("choices") or []
        if not choices:
            raise SpecError(f"{label}: a choice question needs a non-empty 'choices' list")
        max_choices = q.get("max_choices")
        min_choices = q.get("min_choices")
        if (max_choices or min_choices) and select != "multi":
            raise SpecError(
                f"{label}: choice limits apply only to a multi-select question. "
                f"Set select to 'multi', or remove max_choices and min_choices."
            )
        # A limit nobody can satisfy makes the question impossible to answer, and Qualtrics
        # enforces it rather than noticing it is unreachable: the respondent is simply stuck.
        if min_choices and max_choices and min_choices > max_choices:
            raise SpecError(
                f"{label}: min_choices ({min_choices}) is greater than max_choices "
                f"({max_choices}), so no answer can satisfy both and nobody can move past "
                f"this question."
            )
        if min_choices and min_choices > len(choices):
            raise SpecError(
                f"{label}: min_choices is {min_choices} but the question offers only "
                f"{len(choices)} choice(s), so the requirement can never be met and nobody "
                f"can move past this question."
            )
        payload = base_payload(qid, tag, html, qt, sel, sub)
        payload["Choices"], payload["ChoiceOrder"], payload["NextChoiceId"] = build_choices(
            choices, conservative, notes
        )
        payload["Validation"] = validation_settings(
            required, max_choices, min_choices, conservative, notes,
            choice_count=len(choices),
        )
        if q.get("randomize"):
            payload["Randomization"] = build_randomization(
                q["randomize"], [c.get("text") if isinstance(c, dict) else str(c) for c in choices],
                label)
        return payload

    if qtype == "matrix":
        select = q.get("select", "single")
        sub = "SingleAnswer" if select == "single" else "MultipleAnswer"
        note_if_unevidenced(f"Matrix/Likert/{sub}")
        rows, columns = q.get("rows") or [], q.get("columns") or []
        if not rows or not columns:
            raise SpecError(f"{label}: a matrix needs both 'rows' (statements) and 'columns' (the scale)")
        payload = base_payload(qid, tag, html, "Matrix", "Likert", sub)
        payload["Choices"], payload["ChoiceOrder"], payload["NextChoiceId"] = build_choices(
            rows, conservative, notes
        )
        payload["Answers"], payload["AnswerOrder"], payload["NextAnswerId"] = build_answers(columns)
        payload["ChoiceDataExportTags"] = False
        payload["AnswerColumns"] = len(columns)
        payload["Configuration"] = {
            "QuestionDescriptionOption": "UseText",
            "TextPosition": "inline",
            "ChoiceColumnWidth": 25,
            "MobileFirst": True,
            "NumColumns": 1,
            "RepeatHeaders": "none",
            "WhiteSpace": "OFF",
        }
        payload["Validation"] = validation_settings(required, conservative=conservative, notes=notes)
        if q.get("randomize"):
            payload["Randomization"] = build_randomization(q["randomize"], list(rows), label)
        return payload

    if qtype == "text":
        size = q.get("size", "essay")
        if size not in TEXT_SELECTORS:
            raise SpecError(f"{label}: 'size' must be one of {sorted(TEXT_SELECTORS)}, got {size!r}")
        sel = TEXT_SELECTORS[size]
        note_if_unevidenced(f"TE/{sel}")
        payload = base_payload(qid, tag, html, "TE", sel)
        payload["SearchSource"] = {"AllowFreeResponse": "false"}
        if size == "form":
            fields = q.get("fields") or []
            if not fields:
                raise SpecError(f"{label}: a form question needs a 'fields' list of input labels")
            payload["Choices"], payload["ChoiceOrder"], payload["NextChoiceId"] = build_choices(
                fields, conservative, notes, kind="form"
            )
        payload["Validation"] = validation_settings(required, conservative=conservative, notes=notes)
        return payload

    if qtype == "slider":
        note_if_unevidenced("Slider/HSLIDER")
        rows = q.get("rows") or [text]
        payload = base_payload(qid, tag, html, "Slider", "HSLIDER")
        payload["Choices"], payload["ChoiceOrder"], payload["NextChoiceId"] = build_choices(
            rows, conservative, notes
        )
        payload["Labels"] = []
        payload["Configuration"] = {
            "QuestionDescriptionOption": "UseText",
            "CSSliderMin": q.get("min", 0),
            "CSSliderMax": q.get("max", 100),
            "GridLines": q.get("grid_lines", 10),
            "SnapToGrid": False,
            "NumDecimals": q.get("decimals", 0),
            "ShowValue": True,
            "CustomStart": False,
            "NotApplicable": False,
            "MobileFirst": False,
        }
        payload["Validation"] = validation_settings(required, conservative=conservative, notes=notes)
        return payload

    if qtype == "nps":
        note_if_unevidenced("NPS/NPS")
        payload = base_payload(qid, tag, html, "NPS", "NPS")
        payload["Validation"] = validation_settings(required, conservative=conservative, notes=notes)
        return payload

    if qtype == "rank":
        note_if_unevidenced("RO/DND/TX")
        choices = q.get("choices") or []
        if not choices:
            raise SpecError(f"{label}: a rank question needs a 'choices' list")
        payload = base_payload(qid, tag, html, "RO", "DND", "TX")
        payload["Choices"], payload["ChoiceOrder"], payload["NextChoiceId"] = build_choices(
            choices, conservative, notes
        )
        payload["Validation"] = validation_settings(required, conservative=conservative, notes=notes)
        return payload

    if qtype == "constant_sum":
        note_if_unevidenced("CS/TB")
        choices = q.get("choices") or []
        if not choices:
            raise SpecError(f"{label}: a constant sum question needs a 'choices' list")
        payload = base_payload(qid, tag, html, "CS", "TB")
        payload["Choices"], payload["ChoiceOrder"], payload["NextChoiceId"] = build_choices(
            choices, conservative, notes
        )
        if conservative:
            payload["Validation"] = validation_settings(required, conservative=True, notes=notes)
            notes.append(f"{label}: constant sum total omitted (conservative build)")
        else:
            payload["Validation"] = {
                "Settings": {
                    # Same three states as every other question type. This read "ON" or "OFF"
                    # only, so a constant-sum question with no 'required' field was built
                    # silently skippable while the documented default is request response.
                    "ForceResponse": ("ON" if required is True
                                      else "OFF" if required is False else "RequestResponse"),
                    "Type": "TotalSum",
                    "TotalSum": str(q.get("total", 100)),
                }
            }
            notes.append(f"{label}: constant sum total uses an unevidenced Validation shape")
        return payload

    raise SpecError(
        f"{label}: unknown question type {qtype!r}. "
        f"Supported: descriptive, choice, matrix, text, slider, nps, rank, constant_sum, page_break. "
        f"See references/survey-spec.md."
    )


def build(spec, profile, conservative):
    rng = random.Random()
    notes = []
    evidenced = set(profile.get("question_profiles", {}).keys())

    survey_id = mint("SV_", rng)
    response_set = mint("RS_", rng)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    blocks_spec = spec.get("blocks") or []
    if not blocks_spec:
        raise SpecError("the spec has no blocks. A survey needs at least one block of questions.")

    # Pass 1: mint every block ID first, so a skip can name a block that appears later.
    block_ids = {}
    for i, block in enumerate(blocks_spec):
        name = block.get("name") or f"Block {i + 1}"
        if name in block_ids:
            raise SpecError(f"two blocks are both named {name!r}; block names must be unique so a skip can name one")
        block_ids[name] = mint("BL_", rng)

    # Pass 2: assign every question its Qualtrics ID before building any of them, and record
    # what each spec id maps to. Carry-forward pipes name another question, and a question may
    # pipe one that appears later in the survey, so no payload can be built until every id
    # exists. Skipping this pass is what silently broke carry-forward: the pipe text survived
    # a rebuild unchanged while the questions underneath it were renumbered.
    id_map = {}
    first_question_of_block = {}
    question_block = {}          # minted QID -> index of the block it sits in
    block_index_by_name = {}     # block name -> its index
    next_qid = 1
    # Tags carried over from a readback are claimed before any are generated. Inserting a
    # question at the head of a block otherwise generated "Q1.1" for it while the question
    # below still held "Q1.1" from the original survey, and the rebuild died on a duplicate id
    # the author never typed. Adding a question to last term's survey is the revision this
    # skill exists for, so it has to work.
    reserved_tags = {
        q["export_tag"]
        for block in blocks_spec
        for q in (block.get("questions") or [])
        if q.get("export_tag")
    }
    for block_index, block in enumerate(blocks_spec):
        question_position = 0
        for q in block.get("questions") or []:
            if q.get("type") == "page_break":
                continue
            question_position += 1
            qid = f"QID{next_qid}"
            next_qid += 1
            # DataExportTag is Q<block position>.<question position in block>, matching how
            # the export numbers its columns. Analysis downstream reads these, which is why a
            # survey read back from an export carries its original tags forward in 'export_tag'
            # rather than being renumbered: regenerating them renamed 29 of 34 columns in one
            # real rebuild, quietly breaking anything already written against last term's data.
            tag = q.get("export_tag")
            if not tag:
                # Keep the Q<block>.<position> shape but step past any position a carried-over
                # tag already holds, so a new question lands on the first free column name.
                position = question_position
                tag = f"Q{block_index + 1}.{position}"
                while tag in reserved_tags:
                    position += 1
                    tag = f"Q{block_index + 1}.{position}"
                reserved_tags.add(tag)
            q["_qid"], q["_tag"] = qid, tag
            block_name = block.get("name") or f"Block {block_index + 1}"
            first_question_of_block.setdefault(block_name, qid)
            block_index_by_name[block_name] = block_index
            question_block[qid] = block_index
            for key in (q.get("id"), tag, qid):
                if key:
                    if key in id_map and id_map[key] != qid:
                        raise SpecError(
                            f"two questions both use the id {key!r}. Question ids must be "
                            f"unique, because a carry-forward pipe names a question by its id."
                        )
                    id_map[key] = qid

    sq_elements = []
    bl_payload = {}

    for block_index, block in enumerate(blocks_spec):
        name = block.get("name") or f"Block {block_index + 1}"
        elements = []
        for q in block.get("questions") or []:
            if q.get("type") == "page_break":
                elements.append({"Type": "Page Break"})
                continue
            qid, tag = q["_qid"], q["_tag"]
            payload = build_question(q, qid, tag, evidenced, conservative, notes)
            # Rewrite carry-forward pipes now that every id is known, then re-derive the
            # description from the rewritten text so the editor label matches the question.
            payload = substitute_pipes(payload, id_map, q.get("id") or tag)
            payload["QuestionDescription"] = to_description(payload["QuestionText"])
            sq_elements.append(
                {
                    "SurveyID": survey_id,
                    "Element": "SQ",
                    "PrimaryAttribute": qid,
                    "SecondaryAttribute": payload["QuestionDescription"],
                    "TertiaryAttribute": None,
                    "Payload": payload,
                }
            )
            element = {"Type": "Question", "QuestionID": qid}
            skips = q.get("skip") or []
            if skips:
                element["SkipLogic"] = build_skip_logic(
                    q, qid, skips, block_ids, name, id_map, first_question_of_block,
                    question_block, block_index_by_name, block_index)
            elements.append(element)
        bl_payload[str(block_index)] = {
            "Type": "Default" if block_index == 0 else "Standard",
            "SubType": "",
            "Description": name,
            "ID": block_ids[name],
            "BlockElements": elements,
        }

    # Every real export carries a Trash block, the holding pen for deleted questions, and so
    # does the one third-party generator whose output is known to import. One export's is
    # empty, which is the shape copied here. It is deliberately absent from the Flow: a block
    # the flow does not name is not shown, which is exactly what the trash is for.
    bl_payload[str(len(blocks_spec))] = {
        "Type": "Trash",
        "Description": "Trash / Unused Questions",
        "ID": mint("BL_", rng),
        "BlockElements": [],
    }

    flow = [
        {"Type": "Block", "ID": bl_payload[str(i)]["ID"], "FlowID": f"FL_{i + 2}", "Autofill": []}
        for i in range(len(blocks_spec))
    ]

    # Embedded data: the hidden fields a survey collects without asking, handed over by
    # whatever launched it. A survey launched from a learning-management system carries the
    # university id this way, and they are what attach a response to a person. They live in
    # the flow rather than on any question, so a rebuild that only carries blocks drops them
    # and the survey silently starts collecting anonymous responses.
    embedded = spec.get("embedded_data") or []
    if embedded:
        entries = []
        for item in embedded:
            field = item.get("field") if isinstance(item, dict) else str(item)
            if not field:
                raise SpecError("an embedded_data entry has no 'field' name")
            source = (item.get("source") if isinstance(item, dict) else None) or "recipient"
            if source not in ("recipient", "custom"):
                raise SpecError(
                    f"embedded data {field!r}: 'source' must be 'recipient' (the value arrives "
                    f"from the panel or the launch URL) or 'custom' (this survey sets it)."
                )
            entry = {
                "Description": item.get("description", field) if isinstance(item, dict) else field,
                "Type": "Recipient" if source == "recipient" else "Custom",
                "Field": field,
                "VariableType": "String",
                "DataVisibility": [],   # an array here; a question's DataVisibility is an object
                "AnalyzeText": False,
            }
            # A Recipient field carries no Value key at all, not an empty one: that is what
            # makes Qualtrics show "Value will be set from Panel or URL".
            if source == "custom":
                entry["Value"] = item.get("value", "") if isinstance(item, dict) else ""
            entries.append(entry)
        flow.append(
            {"Type": "EmbeddedData", "FlowID": f"FL_{len(flow) + 2}", "EmbeddedData": entries}
        )

    account = profile.get("account", {})
    # SurveyEntry keys are emitted in the order a real export writes them. JSON is officially
    # order-independent and this should not matter; it is matched anyway because the importer
    # rejects files without saying why, and every gratuitous difference from a file Qualtrics
    # made itself is one more thing that cannot be ruled out.
    defaults = dict(profile.get("survey_entry_defaults", {}))
    entry = {}
    for key in ENTRY_KEY_ORDER:
        if key in defaults:
            entry[key] = defaults[key]
    for key, value in defaults.items():
        entry.setdefault(key, value)
    entry.update(
        {
            "SurveyID": survey_id,
            "SurveyName": spec.get("survey_name") or "Untitled survey",
            "SurveyDescription": spec.get("survey_description"),
            "SurveyOwnerID": account.get("SurveyOwnerID"),
            "SurveyBrandID": account.get("SurveyBrandID"),
            "DivisionID": account.get("DivisionID"),
            "SurveyActiveResponseSet": response_set,
            "SurveyStatus": "Inactive",
            "SurveyStartDate": "0000-00-00 00:00:00",
            "SurveyExpirationDate": "0000-00-00 00:00:00",
            "SurveyCreationDate": now,
            "CreatorID": account.get("CreatorID") or account.get("SurveyOwnerID"),
            "LastModified": now,
            "LastAccessed": "0000-00-00 00:00:00",
            "LastActivated": "0000-00-00 00:00:00",
            "Deleted": None,
        }
    )

    survey_options = dict(profile.get("survey_options", {}))
    survey_options["ActiveResponseSet"] = None

    # How the survey ends is the source survey's setting, not this survey's, and inheriting it
    # is how a new survey acquires someone else's ending. A profile derived from a survey that
    # a learning-management system launches carries SurveyTermination "Redirect" to a field
    # that system supplies at launch: inside it the redirect hands the respondent back, and
    # outside it nothing declares the field, so it resolves to nothing and the respondent is
    # sent to a bare query string. A new survey ends with Qualtrics' own end-of-survey message
    # unless the spec asks otherwise.
    #
    # EOSRedirectURL is deliberately left as the profile has it when the survey ends with the
    # default message. All seven real exports measured carry the same stale value regardless of
    # their termination mode, including the two that end with DefaultMessage, so Qualtrics never
    # clears it and an emptied or absent one is a shape no export evidences. It is not read then.
    #
    # A survey that DOES redirect is a different matter: where it sends people is part of that
    # survey, not of whichever export the profile happened to be built from. The spec states it,
    # and where the spec does not, the inherited address is used but named in the build report,
    # because a redirect nobody chose is one nobody checks.
    eos = spec.get("end_of_survey") or {}
    termination = eos.get("termination")
    survey_options["SurveyTermination"] = termination or "DefaultMessage"
    if termination == "Redirect":
        redirect_url = eos.get("redirect_url")
        if redirect_url:
            survey_options["EOSRedirectURL"] = redirect_url
        else:
            redirect_url = survey_options.get("EOSRedirectURL")
            if not redirect_url:
                raise SpecError(
                    "end_of_survey asks for a Redirect but gives no 'redirect_url', and the "
                    "profile carries no EOSRedirectURL to fall back on. Add the address."
                )
            notes.append(
                f"redirect address not stated in the spec; using the profile's: {redirect_url}"
            )
    elif termination == "DisplayMessage":
        for key, field in (("message", "EOSMessage"), ("message_library", "EOSMessageLibrary")):
            if eos.get(key):
                survey_options[field] = eos[key]
        if not survey_options.get("EOSMessage"):
            notes.append(
                "the survey ends on a custom message but names none, in the spec or the "
                "profile, so respondents finishing it see a blank ending; set it in Qualtrics "
                "or end with the default message instead"
            )

    def element(name, primary, payload, secondary=None, tertiary=None):
        return {
            "SurveyID": survey_id,
            "Element": name,
            "PrimaryAttribute": primary,
            "SecondaryAttribute": secondary,
            "TertiaryAttribute": tertiary,
            "Payload": payload,
        }

    scaffold = profile.get("scaffold", {})
    elements = [
        element("BL", "Survey Blocks", bl_payload),
        # Every real export carries a preview link. It was first left out as inferred-optional;
        # the file without it was rejected on import, so it is emitted rather than reasoned
        # about. Its ID is a UUID, unlike every other ID in the format.
        element(
            "PL",
            "Preview Link",
            {"PreviewType": "Brand", "PreviewID": str(uuid.uuid4())},
        ),
        element(
            "FL",
            "Survey Flow",
            {"Type": "Root", "FlowID": "FL_1", "Flow": flow, "Properties": {"Count": len(flow) + 1}},
        ),
        element(
            "PROJ",
            scaffold.get("PROJ", {}).get("PrimaryAttribute", "CORE"),
            scaffold.get("PROJ", {}).get("Payload", {"ProjectCategory": "CORE", "SchemaVersion": "1.1.0"}),
            tertiary=scaffold.get("PROJ", {}).get("TertiaryAttribute", "1.1.0"),
        ),
        # QC's SecondaryAttribute is a QID high-water mark, not a count of questions. The
        # export carries 116 against 26 questions. Any value above every QID in use is fine.
        element("QC", "Survey Question Count", None, secondary=str(next_qid + 10)),
        element("RS", response_set, None),
        element("SCO", "Scoring", scaffold.get("SCO", {}).get("Payload")),
        element("SO", "Survey Options", survey_options),
        *sq_elements,
        element("STAT", "Survey Statistics", scaffold.get("STAT", {}).get("Payload")),
    ]

    for block in blocks_spec:
        for q in block.get("questions") or []:
            q.pop("_qid", None)
            q.pop("_tag", None)

    entry = {k: entry[k] for k in ENTRY_KEY_ORDER if k in entry} | {
        k: v for k, v in entry.items() if k not in ENTRY_KEY_ORDER
    }
    # A real export orders SurveyElements alphabetically by Element, then by PrimaryAttribute as
    # a string. Nothing about the format depends on it (block order lives in BlockElements and
    # display order in the Flow), but it costs nothing to match.
    elements.sort(key=lambda e: (str(e.get("Element")), str(e.get("PrimaryAttribute"))))

    return {"SurveyEntry": entry, "SurveyElements": elements}, notes


def to_block_name(block_index_by_name, index):
    """The block name for an index, for checking that a target is a block's first question."""
    for name, i in block_index_by_name.items():
        if i == index:
            return name
    return None


def build_skip_logic(q, qid, skips, block_ids, current_block, id_map, first_question_of_block,
                     question_block, block_index_by_name, current_block_index):
    """Attach skip logic to a block element.

    The locator addresses a choice by its KEY, not its screen position. Choice keys are minted
    1..n by build_choices, so the key equals the position here, but the locator is derived from
    the choice list rather than assumed, because that stops being true the moment a spec is
    edited and rebuilt against different keys.

    A skip lands at the end of a block, the end of the survey, the start of a named block, or
    a specific question. The last of those is evidenced in a real export, which skips straight
    to two named questions; an earlier version of this skill wrongly refused it.
    """
    choices = q.get("choices") or []
    texts = [c.get("text") if isinstance(c, dict) else str(c) for c in choices]
    logic = []
    for i, skip in enumerate(skips, start=1):
        when, to = skip.get("when"), skip.get("to")
        condition = skip.get("condition", "selected")
        conditions = {"selected": "Selected", "not_selected": "NotSelected", "displayed": "Displayed"}
        if condition not in conditions:
            raise SpecError(
                f"{q.get('id') or qid}: skip condition {condition!r} is not recognized. "
                f"Use 'selected' (the default), 'not_selected', or 'displayed'."
            )
        if condition == "displayed":
            # Evidenced in a real export: a skip that fires because the question was shown at
            # all, rather than on any answer. It addresses the question rather than a choice,
            # which is why its two locator fields differ and neither names a choice key.
            key = None
        elif when not in texts:
            raise SpecError(
                f"{q.get('id') or qid}: skip condition {when!r} is not one of this question's "
                f"choices. Choices are: {texts}. A skip that should fire because the question "
                f"was shown at all, rather than on an answer, takes condition 'displayed' "
                f"and no 'when'."
            )
        else:
            key = texts.index(when) + 1
        if to == "end_of_block":
            destination = "ENDOFBLOCK"
        elif to == "end_of_survey":
            destination = "ENDOFSURVEY"
        else:
            # Resolving a skip target, under the one rule Qualtrics enforces and states in its
            # own error: "cannot find destination in the block". A skip that names a question
            # can only reach a question in the SAME block. Both question-targeted skips in the
            # one real export that has any stay inside their block. Reaching the next block is
            # what ENDOFBLOCK is for, and it lands on that block's first question.
            target_block = None
            target_qid = None
            if to in block_index_by_name:
                target_block = block_index_by_name[to]
            elif to in id_map:
                target_qid = id_map[to]
                target_block = question_block.get(target_qid)
            else:
                raise SpecError(
                    f"{q.get('id') or qid}: skip target {to!r} is not a block name, a question "
                    f"id, 'end_of_block', or 'end_of_survey'. Known blocks: "
                    f"{sorted(block_index_by_name)}. Known question ids: "
                    f"{sorted(k for k in id_map if not k.startswith('QID'))}"
                )

            if target_qid is not None and target_block == current_block_index:
                destination = target_qid
            elif target_block == current_block_index + 1 and (
                target_qid is None or target_qid == first_question_of_block.get(to_block_name(
                    block_index_by_name, target_block))):
                # The next block, entered at its start. Qualtrics spells this ENDOFBLOCK.
                destination = "ENDOFBLOCK"
            elif target_block is not None and target_block <= current_block_index:
                raise SpecError(
                    f"{q.get('id') or qid}: skip target {to!r} is not after this question. "
                    f"A skip only moves forward."
                )
            else:
                raise SpecError(
                    f"{q.get('id') or qid}: skip target {to!r} is in a later block, but not the "
                    f"very next one, or not at its start. Qualtrics can only skip to a question "
                    f"in the SAME block, or to the end of this block, which lands on the start "
                    f"of the next one. Split or reorder the blocks so the target begins the "
                    f"block immediately after this one, or use 'end_of_survey'."
                )

        # A choice-based skip points both locator fields at the same choice key. A
        # displayed-based one points them at two different things, which is what a real export
        # carries and why the validator no longer requires the two to agree.
        if key is None:
            choice_locator = f"q://{qid}/ChoiceTextEntryValue"
            locator = f"q://{qid}/ChoiceDisplayed"
        else:
            choice_locator = locator = f"q://{qid}/SelectableChoice/{key}"
        summary = "End of Block" if destination == "ENDOFBLOCK" else (
            "End of Survey" if destination == "ENDOFSURVEY" else to
        )
        # Description and SkipToDescription are the editor's own human-readable summary of the
        # rule. Qualtrics regenerates them, so they are cosmetic, but a stale one misleads
        # anyone reading the survey in the builder.
        if condition == "displayed":
            clause = "Condition: <strong>Question Is Displayed</strong>. "
        else:
            shown = html_escape(when or "", quote=False)
            title = html_escape(when or "", quote=True)
            verb = "Is Selected" if condition == "selected" else "Is Not Selected"
            clause = (
                "Condition: <strong title=" + '"' + title + '">' + shown
                + "</strong> <strong>" + verb + "</strong>. "
            )
        description = (
            clause + "Skip To: <strong>" + html_escape(summary, quote=False) + "</strong>."
        )
        logic.append(
            {
                "SkipLogicID": i,
                "ChoiceLocator": choice_locator,
                "Locator": locator,
                "Condition": conditions[condition],
                "SkipToDestination": destination,
                "SkipToDescription": summary,
                "Description": description,
                "QuestionID": qid,
            }
        )
    return logic


def serialize(qsf) -> str:
    """Render the QSF the way a Qualtrics export is written.

    Compact separators, no trailing newline, and forward slashes escaped as \\/ inside strings,
    which is what Qualtrics' own encoder emits. A JSON parser cannot tell the difference; the
    point is to leave the importer nothing to object to that is not the survey itself. Escaping
    every "/" is safe because in a JSON document that character only ever occurs inside a
    string literal.
    """
    return json.dumps(qsf, separators=(",", ":"), ensure_ascii=False).replace("/", "\\/")


def main():
    parser = argparse.ArgumentParser(description="Expand a survey spec into a Qualtrics .qsf")
    parser.add_argument("spec", help="Path to the survey spec JSON")
    parser.add_argument("-o", "--output", required=True, help="Path to write the .qsf")
    parser.add_argument(
        "--profile",
        help="Path to qsf-profile.json (default: ../assets/qsf-profile.json beside this script)",
    )
    parser.add_argument(
        "--conservative", action="store_true",
        help="Omit reconstructed choice limits, write-in boxes, and constant-sum totals",
    )
    ns = parser.parse_args()

    spec_path = Path(ns.spec)
    profile_path = Path(ns.profile) if ns.profile else Path(__file__).resolve().parent.parent / "assets" / "qsf-profile.json"

    for path, what in ((spec_path, "spec"), (profile_path, "profile")):
        if not path.exists():
            print(f"Error: {what} file {path} does not exist.", file=sys.stderr)
            sys.exit(2)

    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: {e}. Fix the JSON syntax and re-run.", file=sys.stderr)
        sys.exit(2)

    try:
        qsf, notes = build(spec, profile, ns.conservative)
    except SpecError as e:
        print(f"Spec error: {e}", file=sys.stderr)
        sys.exit(1)

    out = Path(ns.output)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(serialize(qsf), encoding="utf-8")
    except OSError as e:
        print(f"Error: could not write {out}: {e}", file=sys.stderr)
        sys.exit(2)

    questions = sum(1 for el in qsf["SurveyElements"] if el["Element"] == "SQ")
    # The Trash block is in the payload and is not a section of the survey, so counting the
    # payload reported one block more than the readback did for the same file.
    payload = qsf["SurveyElements"][0]["Payload"]
    entries = payload.values() if isinstance(payload, dict) else payload
    blocks = sum(1 for b in entries if (b or {}).get("Type") != "Trash")
    print(f"Built {out}")
    sources = profile.get("sources") or []
    print(f"  {questions} questions in {blocks} block(s), profile from "
          f"{len(sources)} export(s)" + (f": {', '.join(sources)}" if sources else ""))
    if notes:
        # These are not all unevidenced constructs. The list also holds deliberate omissions
        # from a --conservative build and plain advisories, and calling a conservative build's
        # own omissions "not evidenced" said the opposite of what had happened.
        print(f"  {len(notes)} thing(s) to check in Qualtrics after the upload:")
        for n in dict.fromkeys(notes):
            print(f"    - {n}")
    else:
        print("  Every construct used is evidenced, and nothing was omitted.")


if __name__ == "__main__":
    main()
