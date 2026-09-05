# Survey to Qualtrics

Turn a survey you have already written into a Qualtrics import file, and turn a Qualtrics export back into something you can read and edit.

## Problem

You write a survey in a document: twenty questions, a couple of grids, a "choose up to three", an "Other, please describe", and an instruction to skip a section. Getting it into Qualtrics means retyping all of it into the web editor and setting each option by hand. Reusing last term's survey means the same work again, because the exported file is not something you can read.

Qualtrics can import a `.qsf` file, which would solve this, except that the format is undocumented and Qualtrics tells you not to edit it. A rejected import says only "Something went wrong and the project wasn't created", with no reason given.

## Approach

The skill does not work from documentation, because there is none worth working from. It works from files Qualtrics itself produced.

You give it exports from your own account. `profile_qsf.py` reads them structurally, recording which keys each question type carries and which are optional, and writes that to a profile. The builder then generates new surveys in the shapes the profile actually observed, and says out loud when it has used a construct no export evidenced.

The second half matters as much as the first. Because a generated file cannot be checked by reading it, `qsf_read.py` reads the finished `.qsf` back into markdown, showing what Qualtrics will see rather than what the build intended. A separate agent compares that readback against the survey as written. Most defects in this format import cleanly and produce the wrong survey, so this is where they get caught.

## The Flow

1. **Write the spec.** The skill reads your survey and decides the Qualtrics type for each question: which items are one grid, which instruction is an enforced limit, which option needs a write-in box, which sentence is a skip.
2. **Build.** The `.qsf` is generated, with a report of what to check in Qualtrics afterwards.
3. **Validate.** Checks the internal links Qualtrics does not check: a question in no block, a block outside the flow, a skip pointing at a choice position instead of its key, a carry-forward pipe naming a question that no longer exists.
4. **Read back.** The finished file is rendered as markdown.
5. **Audit.** An agent that did not build the file compares the readback to your original survey, question by question.
6. **Report.** You get the readback, the findings, and the file. The upload is yours.

Reading an existing export runs step 4 alone, and produces both a readable markdown version and an editable spec.

## Usage

Ask for it in your own words: "make this a Qualtrics survey", "build the qsf", "get this survey into Qualtrics", "read this qsf", "rebuild last term's survey".

**Good uses**
- A survey already written in a document or in the conversation
- Reusing or revising a survey from a previous term
- Reading an export you inherited and cannot make sense of

**Not good uses**
- Designing or wording the questions, which happens before this skill runs
- Analyzing responses after the survey closes
- Anything requiring the skill to open Qualtrics, which it never does

**Tips**
- Give the profiler every export you have, not one. A key that every question in a single file happens to carry looks mandatory until a second file shows one without it.
- An import always creates a new survey, so a bad file costs an upload attempt and nothing already in your account.

## Installation

This skill needs more than one file. Copy the whole directory:

```
~/.claude/skills/survey-qsf/
  SKILL.md
  references/qsf-format.md
  references/survey-spec.md
  scripts/build_qsf.py
  scripts/profile_qsf.py
  scripts/qsf_read.py
  scripts/validate_qsf.py
  assets/qsf-profile.json
```

This file, `README.md`, is documentation for you rather than something the skill reads, so copying it alongside is optional. Python 3 with the standard library is all it needs. Restart Claude Code after copying.

**One setup step before your first build.** The bundled `assets/qsf-profile.json` is anonymized: the account, brand, theme, and message-library identifiers are blank, along with the survey password, the end-of-survey redirect, and the header, footer, and title text. A survey built from it imports with the Qualtrics default theme instead of yours and ends with the Qualtrics default message. Export any survey from your own Qualtrics account and run:

```bash
python3 ~/.claude/skills/survey-qsf/scripts/profile_qsf.py <your-export.qsf> [<more-exports.qsf> ...]
```

That writes a profile carrying your account's own settings. If you later share the profile, regenerate it with `--anonymize`, which blanks all of the above plus the source filenames.

## Output

- The `.qsf` file, which you upload to Qualtrics by hand
- A markdown readback of that finished file
- A JSON spec, which is the editable version of the survey
- A build report of what to check in Qualtrics afterwards

## Design Rationale

**Account settings and structural shapes are derived, not hardcoded.** The survey options, the scaffolding, and which keys each question type actually requires are all recomputed from whatever exports you supply, rather than written into the scripts. What the scripts do hold is the payload shape for each question type they can emit, documented with its evidence in `references/qsf-format.md`. Profiling a new export evidences a question type, which stops the build report flagging it; it does not by itself teach the builder to generate a type it has no shape for.

**A generated file is checked by reading it back, never by reading the generator.** The failures in this format are silent: a question defined but listed in no block simply does not appear, and the import reports success. Comparing the readback against the original survey is the only check that catches this class.

**Constructs the profile has not observed are named, not hidden.** The build report lists them alongside anything a conservative build left out, and they are the first things to look at in Qualtrics after an upload.

**Nothing the spec cannot express is passed over quietly.** An earlier version documented carry-forward as unsupported and then destroyed it on rebuild without saying so. A construct the spec cannot carry is now named out loud during the run.

**The skill stops at the file.** It never opens Qualtrics and never uploads. The upload is the only thing that proves the file works, and it stays a deliberate human step.

## Acknowledgments

The scripts started from the archetypes in `skill-engineer-master` by **Antony Evans** (edge-brain-lite), CC BY 4.0.

- [GitHub](https://github.com/antonyevans/edge-brain-lite)
