#!/usr/bin/env python3
"""
qsf_read.py — Render a .qsf as a readable markdown survey.

Adapted from the validate_output.py archetype in skill-engineer-master by Antony Evans
(edge-brain-lite, https://github.com/antonyevans/edge-brain-lite), CC BY 4.0.

Two jobs, one piece of code. It is the review gate on a build, where it answers the only
question that matters before an upload: did the generator understand the survey. And it is
the reverse direction on its own, turning a survey exported from Qualtrics back into a
document that can be revised and rebuilt, so last term's survey is edited rather than retyped.

It reads the finished file rather than the spec that produced it, which is the point. A
readback of the spec would show what the build intended; this shows what Qualtrics will
actually read.

Usage:
  python3 qsf_read.py <file.qsf>                  # to stdout
  python3 qsf_read.py <file.qsf> -o <out.md>
  python3 qsf_read.py <file.qsf> --spec <out.json>   # also emit a survey spec

--spec writes a build_qsf.py spec alongside the markdown, which is what makes an exported
survey editable: read it back, change the spec, rebuild.

Error taxonomy:
  exit 0 — rendered
  exit 1 — the file is not a readable QSF
  exit 2 — bad arguments or unwritable output
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

# Reverse of the selector tables in build_qsf.py, plus the selectors a Qualtrics survey can
# carry that the builder does not emit. Anything absent here is reported by its raw code
# rather than guessed at, because a wrong plain-English label is worse than an honest one.
CHOICE_LAYOUTS = {
    "SAVR": ("single", "vertical"), "SAHR": ("single", "horizontal"),
    "SACOL": ("single", "columns"), "DL": ("single", "dropdown"), "SB": ("single", "select"),
    "MAVR": ("multi", "vertical"), "MAHR": ("multi", "horizontal"),
    "MACOL": ("multi", "columns"), "MSB": ("multi", "multiselect"),
}
TEXT_SIZES = {"SL": "single line", "ML": "a few lines", "ESTB": "essay box", "FORM": "form fields"}


def plain(text):
    """Strip the HTML Qualtrics stores question text as, back to readable prose."""
    if not text:
        return ""
    text = re.sub(r"<div><br\s*/?></div>", "\n\n", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</div>\s*<div>", "\n", text, flags=re.I)
    # Qualtrics' editor emits <div>, but text pasted into it keeps whatever markup it came
    # with, and real exports carry <p> and <ul><li> too. Those were stripped as ordinary tags,
    # which joined their contents with nothing between: a three-item list read back as
    # "Attended meetingsDid their shareCommunicated well", and the rebuild wrote that
    # word-jammed line into the new survey. A paragraph boundary is a blank line and a list
    # item is a line; the bullet character itself cannot survive, which section 6 of
    # references/survey-spec.md records.
    text = re.sub(r"</p>\s*<p\b[^>]*>", "\n\n", text, flags=re.I)
    text = re.sub(r"</?(?:p|li|ul|ol|tr|h[1-6])\b[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# A piped question reference addresses another question by its Qualtrics ID. Both directions
# matter here: the markdown shows it in words, and the spec rewrites it to the spec's own id so
# a rebuild re-points it instead of leaving it aimed at an id that no longer exists.
PIPE_RE = re.compile(r"\$\{q://(QID[0-9]+)(/[^}]*)?\}")


def pipes_to_words(text, qid_to_id):
    """Render a piped reference as something a person can check, for the markdown readback."""
    def repl(m):
        target = qid_to_id.get(m.group(1), m.group(1))
        kind = (m.group(2) or "").strip("/")
        if kind.startswith("ChoiceGroup/Selected"):
            return f"[the answers they chose in {target}]"
        return f"[carried forward from {target}]"
    return PIPE_RE.sub(repl, text or "")


def pipes_to_spec_ids(value, qid_to_id):
    """Rewrite every piped reference from a Qualtrics ID to the spec id, recursively.

    Without this a rebuilt survey keeps pointing at the ids of the survey it came from, which
    no longer exist, and every respondent sees an empty space where a name should be.
    """
    if isinstance(value, str):
        return PIPE_RE.sub(
            lambda m: "${q://" + qid_to_id.get(m.group(1), m.group(1)) + (m.group(2) or "") + "}",
            value,
        )
    if isinstance(value, dict):
        return {k: pipes_to_spec_ids(v, qid_to_id) for k, v in value.items()}
    if isinstance(value, list):
        return [pipes_to_spec_ids(v, qid_to_id) for v in value]
    return value


def blocks_of(bl_payload):
    """A BL payload is a dict in some Qualtrics versions and an array in others."""
    if isinstance(bl_payload, dict):
        return list(bl_payload.values())
    if isinstance(bl_payload, list):
        return list(bl_payload)
    return []


def ordered(items, order):
    """Return (key, display) pairs in display order, which is the order array and never the
    numeric order of the keys: a scale point added later can be shown first."""
    items = items or {}
    out = []
    for key in order or []:
        entry = items.get(str(key), items.get(key))
        if isinstance(entry, dict):
            out.append((str(key), plain(entry.get("Display", ""))))
    # Anything not named by the order array would not display in Qualtrics either, but it is
    # shown here so a missing entry is visible rather than silently absent.
    for key, entry in items.items():
        if str(key) not in {k for k, _ in out} and isinstance(entry, dict):
            out.append((str(key), plain(entry.get("Display", "")) + "  [not in display order]"))
    return out


def describe_randomization(payload):
    """Say in words what a Randomization block does, for the review gate.

    "Choices randomized" is not enough to check: the whole question is WHICH choices move, and
    a list whose "Other" and "I do not know" options have been shuffled into the middle reads
    as a mistake to every respondent.
    """
    rand = payload.get("Randomization")
    if not rand:
        return None
    # Qualtrics writes a Randomization block even for a question deliberately NOT randomized.
    # Describing that as "choices randomized" told the review gate the opposite of the truth,
    # and the audit agent reads this line rather than the payload.
    if rand.get("Type") == "None":
        return None
    if rand.get("Type") == "All":
        return "choices shown in random order"
    advanced = rand.get("Advanced") or {}
    order = advanced.get("FixedOrder") or []
    if not order:
        return "choices randomized"
    # Positions come from the display order, never from FixedOrder, which keeps a slot for
    # every choice the question ever had: a 10-choice question with 13 stale slots was
    # reported as "first 12 shown in random order, last 1 at the end".
    choices = payload.get("Choices") or {}
    display = [str(k) for k in (payload.get("ChoiceOrder") or list(choices))]
    pinned_keys = {str(s) for s in order if not str(s).startswith("{~")} & set(display)
    positions = [i + 1 for i, key in enumerate(display) if key in pinned_keys]
    moving = len(display) - len(positions)
    if positions and positions == list(range(len(display) - len(positions) + 1, len(display) + 1)):
        return (f"first {moving} choices shown in random order, "
                f"last {len(positions)} always at the end")
    if positions:
        return (f"{moving} choices shown in random order, "
                f"{len(positions)} held in place at positions "
                f"{', '.join(str(p) for p in positions)}")
    return "choices shown in random order"


def describe_required(validation):
    settings = (validation or {}).get("Settings") or {}
    force = settings.get("ForceResponse")
    if force == "ON":
        return "required"
    if force == "RequestResponse":
        return "prompts if skipped"
    return "optional"


def describe_limits(validation):
    settings = (validation or {}).get("Settings") or {}
    bits = []
    if settings.get("MaxChoices"):
        bits.append(f"choose at most {settings['MaxChoices']}")
    if settings.get("MinChoices"):
        bits.append(f"choose at least {settings['MinChoices']}")
    if settings.get("TotalSum"):
        bits.append(f"must total {settings['TotalSum']}")
    return bits


def render_question(payload, skips, block_names, qid_to_id=None, question_names=None):
    """One question as markdown: its text, a plain-English line saying what it is, and its
    options. The description line is the part being checked at the review gate."""
    lines = []
    tag = payload.get("DataExportTag", "")
    text = plain(payload.get("QuestionText", ""))
    qtype = payload.get("QuestionType")
    selector = payload.get("Selector")
    subselector = payload.get("SubSelector")
    validation = payload.get("Validation")

    qid_to_id = qid_to_id or {}
    question_names = question_names or {}
    text = pipes_to_words(text, qid_to_id)
    lines.append(f"**{tag}. {text}**" if text else f"**{tag}.**")

    facts = []
    if qtype == "DB":
        facts.append("Text shown to the respondent; collects no answer")
    elif qtype == "MC":
        select, layout = CHOICE_LAYOUTS.get(selector, ("?", selector or "?"))
        facts.append(
            f"Multiple choice, {'one answer' if select == 'single' else 'several answers'}, {layout}"
        )
    elif qtype == "Matrix":
        rows = len(payload.get("Choices") or {})
        cols = len(payload.get("Answers") or {})
        one = (subselector or "SingleAnswer") == "SingleAnswer"
        facts.append(
            f"Grid, {rows} row{'s' if rows != 1 else ''} by {cols} column{'s' if cols != 1 else ''}, "
            f"{'one answer per row' if one else 'several answers per row'}"
        )
    elif qtype == "TE":
        facts.append(f"Written answer, {TEXT_SIZES.get(selector, selector or '?')}")
    elif qtype == "Slider":
        config = payload.get("Configuration") or {}
        bars = len(payload.get("Choices") or {})
        facts.append(
            f"Slider from {config.get('CSSliderMin')} to {config.get('CSSliderMax')}, "
            f"{bars} bar{'s' if bars != 1 else ''}"
        )
    elif qtype == "NPS":
        facts.append("Net promoter score, 0 to 10")
    elif qtype == "RO":
        facts.append("Rank order")
    elif qtype == "CS":
        facts.append("Constant sum")
    else:
        facts.append(f"Qualtrics type {qtype}/{selector}" + (f"/{subselector}" if subselector else ""))

    if qtype != "DB":
        facts.append(describe_required(validation))
    facts.extend(describe_limits(validation))
    randomization = describe_randomization(payload)
    if randomization:
        facts.append(randomization)
    # Each fact is its own sentence in the description line, so each is capitalized rather
    # than run together lowercase after the type.
    facts = [fact[:1].upper() + fact[1:] if fact else fact for fact in facts]
    lines.append(f"*{'. '.join(facts)}.*")
    lines.append("")

    if qtype == "Matrix":
        rows = ordered(payload.get("Choices"), payload.get("ChoiceOrder"))
        cols = ordered(payload.get("Answers"), payload.get("AnswerOrder"))
        lines.append("Scale: " + " | ".join(display for _, display in cols))
        lines.append("")
        for _, display in rows:
            lines.append(f"- {display}")
        lines.append("")
    elif qtype in ("MC", "RO", "CS") or (qtype == "TE" and selector == "FORM"):
        for key, display in ordered(payload.get("Choices"), payload.get("ChoiceOrder")):
            entry = (payload.get("Choices") or {}).get(key) or {}
            suffix = "  [with a write-in box]" if entry.get("TextEntry") else ""
            lines.append(f"- {pipes_to_words(display, qid_to_id)}{suffix}")
        lines.append("")
    elif qtype == "Slider":
        for _, display in ordered(payload.get("Choices"), payload.get("ChoiceOrder")):
            lines.append(f"- {display}")
        lines.append("")

    for skip in skips or []:
        locator = str(skip.get("ChoiceLocator") or "")
        key = locator.split("/")[-1]
        entry = (payload.get("Choices") or {}).get(key) or {}
        choice_text = plain(entry.get("Display", "")) or f"choice {key}"
        destination = skip.get("SkipToDestination")
        where = {
            "ENDOFBLOCK": "the end of this section",
            "ENDOFSURVEY": "the end of the survey",
        }.get(destination) or block_names.get(destination) or (
            f"question {question_names[destination]}" if destination in question_names
            else destination
        )
        if skip.get("Condition") == "Displayed":
            lines.append(f"> Skip: if this question is shown at all, jump to {where}.")
        else:
            verb = "do not choose" if skip.get("Condition") == "NotSelected" else "choose"
            lines.append(f"> Skip: if they {verb} **{choice_text}**, jump to {where}.")
        lines.append("")

    return lines


def render(qsf, source_name):
    entry = qsf.get("SurveyEntry") or {}
    elements = qsf.get("SurveyElements") or []
    by_element = {}
    for el in elements:
        by_element.setdefault(el.get("Element"), []).append(el)

    sq = {el.get("PrimaryAttribute"): (el.get("Payload") or {}) for el in by_element.get("SQ", [])}
    # Questions are addressed by Qualtrics ID inside pipes and skip destinations, and by their
    # export tag everywhere a person reads. This maps one to the other so both are legible.
    qid_to_id = {qid: (p.get("DataExportTag") or qid) for qid, p in sq.items()}
    blocks = blocks_of((by_element.get("BL") or [{}])[0].get("Payload"))
    block_by_id = {b.get("ID"): b for b in blocks}
    block_names = {bid: b.get("Description") for bid, b in block_by_id.items()}

    flow = ((by_element.get("FL") or [{}])[0].get("Payload") or {}).get("Flow") or []
    ordered_ids = [n.get("ID") for n in flow if n.get("Type") in ("Block", "Standard")]
    # Blocks the flow does not name would not be shown to a respondent either; they are
    # rendered last, clearly marked, rather than dropped without comment.
    unflowed = [
        b.get("ID") for b in blocks
        if b.get("ID") not in ordered_ids and b.get("Type") != "Trash"
    ]

    total_questions = sum(
        1 for b in blocks if b.get("Type") != "Trash"
        for item in b.get("BlockElements") or [] if item.get("Type") == "Question"
    )

    out = [
        f"# {entry.get('SurveyName') or 'Untitled survey'}",
        "",
        f"*Read back from `{source_name}`: {total_questions} questions in "
        f"{len(ordered_ids)} section{'s' if len(ordered_ids) != 1 else ''}. "
        f"This is what the file actually contains, not what was intended.*",
        "",
    ]

    hidden = [f.get("Field") for n in flow if n.get("Type") == "EmbeddedData"
              for f in (n.get("EmbeddedData") or [])]
    if hidden:
        out.append(
            f"*Hidden fields recorded with every response, supplied by whatever launches the "
            f"survey rather than answered by the respondent: {', '.join(hidden)}. "
            f"These are what attach a response to a person.*"
        )
        out.append("")

    for bid in ordered_ids + unflowed:
        block = block_by_id.get(bid)
        if not block:
            out.append(f"> The flow names block `{bid}`, which is not in the file.")
            out.append("")
            continue
        out.append("---")
        out.append("")
        heading = block.get("Description") or "Untitled section"
        if bid in unflowed:
            heading += "  [NOT IN THE SURVEY FLOW: respondents will not see this section]"
        out.append(f"## {heading}")
        out.append("")
        for item in block.get("BlockElements") or []:
            if item.get("Type") == "Page Break":
                out.append("*(new page)*")
                out.append("")
                continue
            payload = sq.get(item.get("QuestionID"))
            if payload is None:
                out.append(f"> Block lists `{item.get('QuestionID')}`, which the file does not define.")
                out.append("")
                continue
            out.extend(render_question(payload, item.get("SkipLogic"), block_names,
                                       qid_to_id, qid_to_id))

    trash = [b for b in blocks if b.get("Type") == "Trash" and (b.get("BlockElements") or [])]
    if trash:
        count = sum(len(b.get("BlockElements") or []) for b in trash)
        out.append("---")
        out.append("")
        out.append(f"*{count} question(s) sit in the Qualtrics trash and are not part of the survey.*")
        out.append("")

    return "\n".join(out)


def to_spec(qsf):
    """Rebuild a build_qsf.py spec from a .qsf, so an exported survey can be revised.

    Constructs the spec has no field for (display logic, quotas) are dropped, which is why the
    markdown readback stays the thing a person checks: it renders what is there, while this
    renders what can be rebuilt. Carry-forward is not one of them: pipes_to_spec_ids rewrites
    those to spec ids below and build_qsf.py rewrites them back, so they survive a rebuild.
    """
    entry = qsf.get("SurveyEntry") or {}
    by_element = {}
    for el in qsf.get("SurveyElements") or []:
        by_element.setdefault(el.get("Element"), []).append(el)
    sq = {el.get("PrimaryAttribute"): (el.get("Payload") or {}) for el in by_element.get("SQ", [])}
    blocks = blocks_of((by_element.get("BL") or [{}])[0].get("Payload"))
    block_by_id = {b.get("ID"): b for b in blocks}
    block_names = {bid: b.get("Description") for bid, b in block_by_id.items()}
    flow = ((by_element.get("FL") or [{}])[0].get("Payload") or {}).get("Flow") or []
    ordered_ids = [n.get("ID") for n in flow if n.get("Type") in ("Block", "Standard")]

    qid_to_id = {qid: (p.get("DataExportTag") or qid) for qid, p in sq.items()}
    spec_blocks = []
    for bid in ordered_ids:
        block = block_by_id.get(bid)
        if not block:
            continue
        questions = []
        for item in block.get("BlockElements") or []:
            if item.get("Type") == "Page Break":
                questions.append({"type": "page_break"})
                continue
            payload = sq.get(item.get("QuestionID"))
            if payload is None:
                continue
            questions.append(question_to_spec(payload, item.get("SkipLogic"), block_names,
                                              qid_to_id))
        spec_blocks.append({"name": block.get("Description") or bid, "questions": questions})

    # Rewrite every piped reference to name the spec's own ids. Without this the rebuilt survey
    # points at the ids of the survey it came from, which is silent breakage: the file
    # validates, imports, and shows an empty space to every respondent.
    # The hidden fields the survey collects without asking. They live in the flow, not on any
    # question, so nothing above would have picked them up, and losing them turns an identified
    # survey into an anonymous one with no sign that anything changed.
    embedded = []
    for node in flow:
        if node.get("Type") != "EmbeddedData":
            continue
        for field in node.get("EmbeddedData") or []:
            item = {"field": field.get("Field"),
                    "source": "custom" if field.get("Type") == "Custom" else "recipient"}
            if field.get("Description") and field.get("Description") != field.get("Field"):
                item["description"] = field["Description"]
            if "Value" in field:
                item["value"] = field["Value"]
            embedded.append(item)

    # A survey ending any way other than Qualtrics' default message said so deliberately, so a
    # rebuild keeps it. A survey written from scratch has no such setting and build_qsf.py
    # defaults it, which is what stops a new survey inheriting the profile source's own ending.
    so_payload = ((by_element.get("SO") or [{}])[0].get("Payload") or {})
    termination = so_payload.get("SurveyTermination")

    spec = {"survey_name": entry.get("SurveyName"), "blocks": spec_blocks}
    if termination and termination != "DefaultMessage":
        end_of_survey = {"termination": termination}
        # Carry the address out with the mode. Reading a redirecting survey and rebuilding it
        # without this would re-point it at whatever the profile inherited, which is the same
        # silent substitution the builder now refuses to make unannounced.
        if termination == "Redirect" and so_payload.get("EOSRedirectURL"):
            end_of_survey["redirect_url"] = so_payload["EOSRedirectURL"]
        # A custom end-of-survey message lives in a message library and is named by id. Carrying
        # the mode without the id rebuilt a survey that ends on a custom message pointing at no
        # message, which is a blank page at the moment the respondent finishes.
        if termination == "DisplayMessage":
            for key, field in (("message", "EOSMessage"), ("message_library", "EOSMessageLibrary")):
                if so_payload.get(field):
                    end_of_survey[key] = so_payload[field]
        spec["end_of_survey"] = end_of_survey
    if embedded:
        spec["embedded_data"] = embedded
    return pipes_to_spec_ids(spec, qid_to_id)


def question_to_spec(payload, skips, block_names, qid_to_id=None):
    qtype, selector = payload.get("QuestionType"), payload.get("Selector")
    validation = (payload.get("Validation") or {}).get("Settings") or {}
    force = validation.get("ForceResponse")
    required = True if force == "ON" else ("request" if force == "RequestResponse" else False)
    q = {"id": payload.get("DataExportTag"), "text": plain(payload.get("QuestionText", ""))}
    # "request" is build_qsf.py's default and needs no field. The other two both do, and False
    # is the one that used to go missing: writing this only when truthy dropped every optional
    # question's optionality, the default then filled the hole, and a rebuilt survey prompted on
    # questions its author had deliberately left skippable. Measured across three real exports:
    # 32 optional questions, none of them still optional after a rebuild.
    if required != "request":
        q["required"] = required
    # The export column name is the survey's link to any analysis already written against it.
    # The builder regenerates tags per block position, which renamed 29 of 34 questions in one
    # real rebuild, so carry the original and let the builder keep it.
    if payload.get("DataExportTag"):
        q["export_tag"] = payload["DataExportTag"]

    choices = [display for _, display in ordered(payload.get("Choices"), payload.get("ChoiceOrder"))]
    write_in = {
        str(k) for k, v in (payload.get("Choices") or {}).items()
        if isinstance(v, dict) and v.get("TextEntry")
    }
    if write_in:
        choices = [
            {"text": display, "write_in": True} if key in write_in else display
            for key, display in ordered(payload.get("Choices"), payload.get("ChoiceOrder"))
        ]

    if qtype == "DB":
        q["type"] = "descriptive"
    elif qtype == "MC":
        select, layout = CHOICE_LAYOUTS.get(selector, ("single", "vertical"))
        q.update({"type": "choice", "select": select, "layout": layout, "choices": choices})
        if validation.get("MaxChoices"):
            q["max_choices"] = int(validation["MaxChoices"])
        if validation.get("MinChoices"):
            q["min_choices"] = int(validation["MinChoices"])
    elif qtype == "Matrix":
        q.update({
            "type": "matrix",
            "select": "single" if (payload.get("SubSelector") or "SingleAnswer") == "SingleAnswer" else "multi",
            "rows": [d for _, d in ordered(payload.get("Choices"), payload.get("ChoiceOrder"))],
            "columns": [d for _, d in ordered(payload.get("Answers"), payload.get("AnswerOrder"))],
        })
    elif qtype == "TE":
        size = {"SL": "line", "ML": "box", "ESTB": "essay", "FORM": "form"}.get(selector, "essay")
        q.update({"type": "text", "size": size})
        if size == "form":
            # Carries the choice objects rather than their text, because a form field can have
            # a write-in box attached and flattening to strings drops it silently.
            q["fields"] = choices
    elif qtype == "Slider":
        config = payload.get("Configuration") or {}
        q.update({
            "type": "slider",
            "rows": [d for _, d in ordered(payload.get("Choices"), payload.get("ChoiceOrder"))],
            "min": config.get("CSSliderMin", 0), "max": config.get("CSSliderMax", 100),
            "decimals": config.get("NumDecimals", 0), "grid_lines": config.get("GridLines", 10),
        })
    elif qtype == "NPS":
        q["type"] = "nps"
    elif qtype == "RO":
        q.update({"type": "rank", "choices": choices})
    elif qtype == "CS":
        q.update({"type": "constant_sum", "choices": choices})
        if validation.get("TotalSum"):
            q["total"] = int(validation["TotalSum"])
    else:
        q["type"] = f"UNSUPPORTED:{qtype}/{selector}"

    rand = payload.get("Randomization")
    # Type "None" is a question deliberately NOT randomized, and Qualtrics writes the block
    # anyway rather than omitting it. Treating the block's presence as the signal inverted the
    # setting: a department list pinned in a chosen order read back as randomize:true and
    # rebuilt as Type "All", shuffling every choice, which this skill's own spec reference
    # says never to do to an ordered list.
    if rand and rand.get("Type") != "None":
        if rand.get("Type") == "All":
            q["randomize"] = True
        else:
            order = (rand.get("Advanced") or {}).get("FixedOrder") or []
            pinned = [i for i, slot in enumerate(order) if not str(slot).startswith("{~")]
            if pinned and pinned == list(range(len(order) - len(pinned), len(order))):
                # A trailing run of pinned choices, which is the common case and the one the
                # spec can state most legibly.
                q["randomize"] = {"except_last": len(pinned)}
            elif pinned:
                # A pinned slot holds the choice's KEY, not its position, and FixedOrder keeps a
                # slot for every choice the question ever had, so it routinely outruns the live
                # list. Indexing the displayed choices by slot position therefore resolved the
                # wrong choice or none at all: pins at slots 6 and 8 over four live choices came
                # back as an empty 'fixed', which the builder accepted as "randomize everything",
                # silently unpinning the options a pin exists to hold down.
                by_key = dict(ordered(payload.get("Choices"), payload.get("ChoiceOrder")))
                fixed = [by_key[str(order[i])] for i in pinned if str(order[i]) in by_key]
                lost = len(pinned) - len(fixed)
                if fixed:
                    q["randomize"] = {"fixed": fixed}
                    if lost:
                        print(f"Note: {payload.get('DataExportTag')}: {lost} pinned choice(s) "
                              f"name keys this question no longer has; the rest are kept.",
                              file=sys.stderr)
                else:
                    # Every pin is unresolvable. The question plainly meant to hold choices in
                    # place, so leaving randomization off preserves the written order; saying
                    # randomize:true here would shuffle exactly what was pinned.
                    print(f"Note: {payload.get('DataExportTag')}: randomization pins none of "
                          f"this question's current choices, so it is left unrandomized. Check "
                          f"it in Qualtrics.", file=sys.stderr)
            else:
                q["randomize"] = True

    spec_skips = []
    for skip in skips or []:
        key = str(skip.get("ChoiceLocator") or "").split("/")[-1]
        entry = (payload.get("Choices") or {}).get(key) or {}
        destination = skip.get("SkipToDestination")
        # A destination is a block boundary, a named block, or a specific question. The last
        # is evidenced in a real export and has to survive the round trip as a question id.
        to = ({"ENDOFBLOCK": "end_of_block", "ENDOFSURVEY": "end_of_survey"}.get(destination)
              or block_names.get(destination)
              or (qid_to_id or {}).get(destination)
              or destination)
        cond = skip.get("Condition")
        if cond == "Displayed":
            # Fires because the question was shown at all, so there is no choice to name.
            skip_entry = {"condition": "displayed", "to": to}
        else:
            skip_entry = {"when": plain(entry.get("Display", "")), "to": to}
            if cond == "NotSelected":
                skip_entry["condition"] = "not_selected"
        spec_skips.append(skip_entry)
    if spec_skips:
        q["skip"] = spec_skips
    return q


def main():
    parser = argparse.ArgumentParser(description="Render a .qsf as a readable markdown survey")
    parser.add_argument("qsf", help="Path to the .qsf")
    parser.add_argument("-o", "--output", help="Write the markdown here (default: stdout)")
    parser.add_argument("--spec", help="Also write a build_qsf.py spec to this path")
    ns = parser.parse_args()

    path = Path(ns.qsf)
    if not path.exists():
        print(f"Error: {path} does not exist.", file=sys.stderr)
        sys.exit(2)
    try:
        qsf = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: {path} is not valid JSON ({e}).", file=sys.stderr)
        sys.exit(1)
    if not isinstance(qsf, dict) or "SurveyElements" not in qsf:
        print(f"Error: {path} is not a QSF (no SurveyElements).", file=sys.stderr)
        sys.exit(1)

    markdown = render(qsf, path.name)
    if ns.output:
        try:
            Path(ns.output).parent.mkdir(parents=True, exist_ok=True)
            Path(ns.output).write_text(markdown + "\n", encoding="utf-8")
        except OSError as e:
            print(f"Error: could not write {ns.output}: {e}", file=sys.stderr)
            sys.exit(2)
        print(f"Readback written to {ns.output}")
    else:
        print(markdown)

    if ns.spec:
        try:
            Path(ns.spec).parent.mkdir(parents=True, exist_ok=True)
            Path(ns.spec).write_text(
                json.dumps(to_spec(qsf), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        except OSError as e:
            print(f"Error: could not write {ns.spec}: {e}", file=sys.stderr)
            sys.exit(2)
        print(f"Spec written to {ns.spec}")


if __name__ == "__main__":
    main()
