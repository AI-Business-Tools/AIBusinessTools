# The QSF format: what is known, how it is known, and what breaks

Read this when a build hits something the spec cannot express, when an upload is rejected, or before extending the generator to a new question type. Ordinary runs do not need it.

## Table of contents
1. What the format is, and what stands behind this skill's knowledge of it
2. Evidence tiers: proven, reconstructed, and unknown
3. The traps
4. When an upload fails
5. The documented fallback: Advanced TXT
6. Refreshing the profile

---

## 1. What the format is, and what stands behind this skill's knowledge of it

A `.qsf` is a JSON file with exactly two top-level keys, `SurveyEntry` (the survey's own settings) and `SurveyElements` (an array in which blocks, the flow, the survey options, and every question are each one entry).

Qualtrics publishes **no schema for it**, describes it only as "a special file format only Qualtrics can read," and carries this warning on its import and export page:

> Do not edit the QSF file! Editing the file can corrupt the contents and make it unable to upload to your account. You may only rename the file, if desired, but do not change the contents or file type.

Generating one from scratch is not addressed anywhere in Qualtrics' documentation. It is a stronger version of the act that warning prohibits. That is the honest position, and it is why this skill's design puts so much weight on reading the finished file back before it is uploaded.

**The evidence this skill rests on is a set of real exports**, not a published spec and not a community write-up. `assets/qsf-profile.json` is derived by `profile_qsf.py` from surveys Qualtrics itself produced, and it supplies the account settings, the survey options, the scaffolding elements, and the pooled key set for every question type across them. The widely circulated community reference for the QSF format is a reader's map written for an R package that parses exports; its prose has not changed since February 2017, it opens by disclaiming its own shelf life, and it never discusses import, required fields, or validation at all. It is useful for naming things and worthless as a guarantee.

**Round-trip evidence.** Every profiled export passes the validator, and every one survives being read into a spec, rebuilt, and validated again. That proves the validator's rules match what Qualtrics really writes. **It does not prove the rebuilt survey asks the same questions**, and that gap has been real: a rebuild once turned every optional question into a prompting one, inverted a question marked "do not randomize" into a shuffled one, and renamed 29 of 34 export columns, all while validating clean. Those three are fixed and measured, but the lesson holds, so a rebuild is compared field by field against the original rather than being trusted because it validated. Nor does any of this prove Qualtrics accepts a rebuilt file; only an upload does that.

**The validator is checked against real exports, not only against generated ones.** An earlier version rejected a genuine export with five errors, all of them its own: it assumed a skip could only land at a block boundary, that a locator always named a choice key, and that a skip's two locator fields always agreed. A rule that a real file breaks is a wrong rule.

## 2. Evidence tiers: proven, reconstructed, and unknown

`build_qsf.py` reports which tier every construct it used falls into, so a build says out loud where it is guessing. The tiers are not fixed: they are computed from whatever exports the profile was built from, so evidencing a new type is a matter of exporting a survey that contains one and re-running `profile_qsf.py`.

**Profile several exports, not one.** Coverage is the obvious gain. The subtler one is that a single file's coincidences look like rules: profiling one survey concluded that a grid must carry a randomization setting, because all three grids in that one file happened to be randomized, and warned about every grid that did not. A key is only required if every instance across every export carries it.

**Tier 1, observed in a real export.** Copied rather than reconstructed: descriptive text blocks, single-answer multiple choice in vertical and column layouts, multi-answer vertical multiple choice, matrix grids with a single answer per row, all four text-entry sizes, horizontal sliders, blocks, page breaks, choice randomization, required and request-response validation, choice limits, write-in boxes, carry-forward pipes, and skip logic in all four of its forms: to the end of a block, to a named question, on a not-selected condition, and on a was-displayed condition.

**Tier 2, reconstructed from the format's own conventions.** The generator emits these and flags them. They follow the patterns Tier 1 establishes, but nothing in the evidence base confirms them: horizontal single-answer layout (`SAHR`), horizontal and select-box multi-answer layouts (`MAHR`, `MSB`), dropdown and select-box single-answer layouts (`DL`, `SB`), matrix with several answers per row, net promoter score, rank order, and constant sum.

**Unknown, and out of scope.** Display logic, quotas, loop and merge, side-by-side, hot spot, heat map, drill down, file upload, and signature questions. None of the profiled exports uses any of them. A survey that needs one gets built without it, and the gap is named rather than passed over.

## 3. The traps

Every one of these produces a file that imports cleanly and is not the survey that was written. `validate_qsf.py` checks all of them; this is the list of what it is checking and why.

**Every id is 15 characters after its prefix, and Qualtrics checks.** `SV_`, `RS_`, `BL_`, `URH_`, and `MS_` ids all carry a 15-character base-62 body. Measured across 221 ids in five real exports: every one is 15. Qualtrics remaps ids on import, which made it look as though only internal consistency mattered, but it evidently validates their shape first. A file built with 16-character ids was **rejected outright** with no message beyond "Something went wrong and the project wasn't created". `QID` and `FL_` are integers and a preview link is a UUID; those three do not follow the rule.

**Every real export carries a `PL` (preview link) element** with `PreviewType: "Brand"` and a UUID. It was first left out as inferred-optional. Emit it; reasoning about which scaffolding elements are dispensable is not worth a rejected import that says nothing about why.

**A question in no block disappears.** A question is defined in one place (an `SQ` element) and positioned in another (a block's `BlockElements` list). Nothing links them except the ID appearing in both. A question defined but never listed is silently absent from the survey, with no error at import.

**A block outside the flow disappears.** Same shape one level up. Blocks are defined in the `BL` element and ordered in the `FL` element. A block the flow never names is not shown. The Qualtrics trash block is the deliberate case of this, which is why it is excluded rather than treated as a fault.

**A skip locator takes a choice's key, not its position.** The locator reads `q://QID51/SelectableChoice/3`, and the `3` is the choice's key in the `Choices` object. Keys are opaque and need not be contiguous: a real question has keys `{"1", "3"}`, where the choice displayed second has key 3. Using the screen position sends respondents to a different answer than the one intended, silently.

**Three fields look like counts and are not.** `QC.SecondaryAttribute` is a question-ID high-water mark, 116 in an export with 26 questions. `FL.Properties.Count` is a flow-ID high-water mark, 9 against 7 nodes. The `BL` payload's keys are sparse indexes, `0,1,2,8,10,12,14` for 7 blocks, where the gaps are deleted blocks. Treating any of the three as a length produces a wrong number that Qualtrics mostly recomputes and occasionally does not.

**`NextChoiceId` is an inequality, not a successor.** It must be strictly greater than every key in use, and in the export it exceeds the highest key by two on some questions, because the counter is monotonic and never reuses a key. Setting it to `max + 1` happens to be valid; asserting that it equals `max + 1` when reading is not.

**Display order lives in the order arrays, never in the keys.** `ChoiceOrder` and `AnswerOrder` are the on-screen order. One matrix in the export has `AnswerOrder` of `["8","5","4","3","2","1"]`, because the scale point keyed 8 was added later and belongs first. Sorting by key silently reorders a scale. The same holds one level up: the flow array's order is the block order, and its `FlowID` values are not in sequence.

**Order arrays mix integers and strings.** One real `ChoiceOrder` is `[1, 2, "3"]`. Compare as strings; the numeric type carries no meaning.

**`BL.Payload` is a dict in some exports and an array in others, from the same account.** One survey exported as a dict keyed by sparse index and another as a plain array, so this is not a version the profile can pin down and not an account setting. A reader must handle both, always. A writer picks one; this skill writes the dict form.

**Survey options use stringified booleans, question payloads use real ones.** `SO` carries `"BackButton": "true"` as a string, while a question's `Configuration` carries `"MobileFirst": true` as a bool. Mixing them up is a plausible rejection.

**A piped reference names a question by ID, and a rebuild renumbers questions.** Carry-forward is written as `${q://QID30/ChoiceGroup/SelectedChoices}` inside question text, choice text, or a matrix's answer labels. Nothing links it to the question it names except the number. Re-mint the IDs without rewriting the pipes and every reference dangles, the file still validates and imports, and every respondent sees an empty space where a name should be. `build_qsf.py` rewrites pipes from spec ids to minted ids, `qsf_read.py` rewrites them back, and `validate_qsf.py` fails any file whose pipes name a question that is not there.

**The write-in flag's value depends on where the box sits.** A multiple-choice option carries `"TextEntry": "true"`; a form field carries `"TextEntry": "on"` plus `InputHeight` and `InputWidth`. No documentation says this and only real exports show it. Emitting `"on"` on a multiple-choice option was a live defect here.

**A choice limit is one `ChoiceRange`, not a `Type` naming one bound.** Qualtrics writes "choose up to 3" as `{"Type": "ChoiceRange", "MinChoices": "1", "MaxChoices": "3"}`, both bounds present and both strings. An earlier guess at `{"Type": "MaxChoices", "MaxChoices": "3"}` looked plausible and is not what the format uses.

**Never emit `QuestionText_Safe`.** It appears on exactly one question in the export and its content is an unrelated question left over from a copy. `QuestionText` and `QuestionText_Unsafe` are emitted as an identical pair; the third is Qualtrics' own leftover.

## 4. When an upload fails

Qualtrics publishes no import error codes, no rejection criteria, and no partial-import behavior, so a failure gives little to work with. Work through this in order.

0. **Run the validator first.** It now catches the one rejection cause actually observed, an id of the wrong length, plus the missing scaffolding element that went with it. Both were found by comparing the rejected file against real exports, which is the move that generalizes: Qualtrics says nothing useful about why, so the answer is always in the difference between your file and one it made itself.

1. **Confirm it actually failed.** Qualtrics' own documentation says a successful import may not appear until the account is refreshed. Refresh before concluding anything.
2. **Check the file is UTF-8 and unmodified.** The scripts write UTF-8; an editor that re-saves as UTF-16 breaks Qualtrics' importers, which its documentation calls out repeatedly.
3. **Rebuild with `--conservative`.** This omits the reconstructed extras hung on a question: choice limits, write-in boxes, and constant-sum totals. It keeps every question type, including the reconstructed ones, because dropping a type does not produce a safer file, it produces no file: a survey with a multi-select question cannot be built without one. If the conservative file imports and the normal one does not, the difference is the omitted list in the build report, and that list is short enough to add by hand in the builder.
4. **Bisect by block.** Cut the spec to its first block, build, and upload. Adding blocks back one at a time finds the question responsible faster than reading JSON.
5. **Re-derive the profile.** If the export the profile came from is old, Qualtrics may have moved. Export any current survey and re-run `profile_qsf.py`.

An import always creates a **new** survey, so a rejected or wrong file costs an upload attempt and nothing else. Nothing already in the account is at risk.

## 5. The documented fallback: Advanced TXT

Qualtrics does publish a complete tag vocabulary for a plain-text import format, with a worked example. It is the only import format Qualtrics documents well enough to target deliberately, and it is the fallback if QSF generation ever stops working.

It covers multiple choice (single, multi, dropdown, select, multi-select, and horizontal or vertical layout), matrix tables (single and multiple answer), text entry (single line, essay, form), constant sum, rank order, descriptive text, blocks, page breaks, embedded data, and recode values. Tags are written `[[Tag]]` on their own line, the file opens with `[[AdvancedFormat]]`, and question text sits between the tags.

**What it cannot express**, and therefore what this skill would lose by falling back to it: choice limits, write-in boxes on a choice, skip logic, and sliders. A survey needing those would import with its questions intact and those four settings added by hand.

It is not implemented here. Implementing it is a small job against a documented spec, and the point of naming it is that the fallback exists and is cheap, so an upload rejection is a setback rather than a dead end.

## 6. Refreshing the profile

```bash
python3 ~/.claude/skills/survey-qsf/scripts/profile_qsf.py <any-export.qsf>
```

Do this when an upload behaves oddly, when a new question type needs evidencing, or after any Qualtrics release that changes the survey editor noticeably. Export any survey from the account the generated surveys will be uploaded to, run the command, and the generator and the validator are both current.

The profile carries **structure and settings only**, never question, choice, or block text. It does carry the account's own identifiers: the owner ID, the brand, and the theme library and skin, which is what makes a generated survey land in the right brand with the right look. Those identify a specific Qualtrics account, so a profile that leaves this machine is regenerated with `--anonymize` first, which blanks them. A generated survey then imports with the default theme, which is a cosmetic loss and nothing more.
