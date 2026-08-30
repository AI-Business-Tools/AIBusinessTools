# Handoff and Resume Protocol

Carry project context across Claude Code sessions without losing state.

---

## Problem

Every Claude Code session starts with an empty context window. On a single-session project this is fine. On a multi-session project it creates a recurring tax: re-explaining what was built, what decisions were made, what remains to be done, and which tools or conventions are in use. The longer a project runs, the higher the tax.

Raw conversation exports exist but are the wrong solution. A full transcript is large, unstructured, and expensive to re-read. It gives equal weight to productive exchanges and dead ends, and it cannot be used without another round of processing.

The handoff protocol solves this by capturing exactly what the next session needs: a concise structured snapshot written at the end of each session, reconstructed at the start of the next one.

---

## How It Works

At the end of a session you say "handoff" (or one of the trigger phrases). Claude Code writes two entries to `CLAUDE.local.md` in the working directory: a terse session log entry that stays forever, and a handoff entry that captures the current state and is replaced the next time you write one. Both are written every time you trigger a handoff, however light the session was. The only part that depends on what the session did is the changelog file: sessions that changed durable configuration also get a dated one holding the file-level detail and the reasoning.

At the start of the next session you say "resume." Claude Code reads `CLAUDE.local.md`, follows the context sources the handoff lists, reads the project's root `README.md` and its status record (the file where the project keeps its open items, if it keeps one), reads the pre-digested summaries, and reports a brief status before waiting for instructions.

The protocol is file-based. `CLAUDE.local.md` travels with the project, and every session in that directory shares the same history. It holds one person's working state, so in a shared repository add it to `.gitignore` and commit it only where everyone on the project wants the same session history.

---

## The Handoff Entry

The handoff entry has seven required fields, plus two optional ones. Every field serves a specific purpose.

**Session summary** captures what was accomplished in 1-2 sentences. This is what you scan when you have forgotten what you were working on.

**Open issues** captures what is actually blocked or undecided. "None blocking" is the expected outcome of a clean session and a stronger report than a list. Where the project keeps a status record, meaning whichever single file holds its open items, this field names it by path rather than copying its rows, because two copies of the open set means one of them is wrong. Many projects keep no status record, and there this field is the open set: items stay in it and are carried forward at every rotation.

**Next steps** lists what the next session does, with the consequence of not doing it. Anything needing a decision from you is raised in the session itself rather than parked here, where it would disappear at the next rotation.

**Context for next session** holds what the next thread needs to know that is not visible from the files: conventions adopted, tools installed, external dependencies, and decisions still pending.

**Context sources** tells the resume protocol what to read and in what order. This is how the next session avoids both under-loading and over-loading. Each pointer is scoped to the part of the file that matters, because a bare path means the whole file and the whole file is what a resume will read.

**Pre-digested** lists processed summary or notes files that already exist and are current. Reading a `_summary.md` is cheaper than re-processing the raw source, and the resume protocol uses these preferentially.

**Active skill** records which skill was last used or should be used next, which prevents the next session defaulting to the wrong workflow.

**Detail** (optional) points at the session's changelog file.

**Todos** (optional) captures tasks to surface prominently on resume, included only when the handoff trigger carried "todo" items.

**File lists and rationale are not handoff fields.** They live in the changelog file, which is reached from **Detail**. See the design rationale below for why.

---

## The Session Log Entry

The session log entry is the permanent half of the dual write and is deliberately tiny: a dated heading, the skill used, a summary held to the 30-word cap, a status, and an optional pointer to the changelog. It records that something happened and where to look; it does not record what happened in detail.

The cap is the point. A summary allowed to grow becomes a small changelog, and the entry stops doing the job it exists for, which is to say that something happened and where the detail lives.

---

## Retention and Carry-Forward

`CLAUDE.local.md` keeps exactly one handoff entry: the most recent. On each write the new entry is appended first and the retired one deleted after, so the file is never momentarily without a handoff.

Session log entries, by contrast, are never deleted. When enough of them have accumulated to be in the way, the oldest move verbatim into a project archive file with one pointer line left in their place, which is relocation rather than deletion.

Single-entry retention only works because carry-forward is mandatory. Before the prior handoff is deleted, every still-open item in its **Open issues** and **Context for next session** is copied into the new one. The new handoff must stand alone. Without that rule, rotation silently drops open work, and the drop is invisible because the evidence is deleted in the same step.

**Next steps is the one field excluded from carry-forward, on purpose.** Its items are re-earned rather than inherited: an action survives only where the session writing the handoff decides to write it again. An inherited list of next steps grows without limit and stops being read, because nothing in it was chosen by the session presenting it.

---

## Where Durable Rules Go

Everything in `CLAUDE.local.md` moves: the handoff entry is replaced on the next write, and a session log entry is history the moment it is written. So a rule that should shape future work cannot live there, and it cannot live in a changelog file either, because changelog files are read only when someone goes looking for the history of one session. A rule parked in either place is lost silently: the next session simply never learns it exists, and nothing in the files says anything is missing.

Durable rules go to a file that is actually read at the moment it is needed: the project's `CLAUDE.md`, which loads every session; its standards file, read on demand; its root `README.md`, which the resume reads, where the project has no `CLAUDE.md`; or the skill that enforces the rule.

---

## The Changelog

A changelog file is written when a session touches skills, scripts, protocols, or other durable configuration, meaning anything that would need an audit trail if it later breaks. Routine content work does not get one.

Naming is `YYYY-MM-DD-topic.md`, and the `changelog/` folder has to exist before the file is written, since a **Detail** link is a path and resolves only once the folder and the file are both there. The file holds the three things the rolling state file no longer carries: which files changed and where, why the choices were made, and what was open at the time. It is linked from the **Detail** field of both the session log entry and the handoff, which is the only way it gets found. The protocol deliberately keeps no index of changelog files: an index duplicates every file it links to and goes stale unread, while a directory listing and a recursive search do the job.

---

## The Resume Protocol

When you type "resume," Claude Code runs a five-step sequence before doing anything else.

1. Read `CLAUDE.local.md`. Find the handoff entry and scan the session log entries for a timeline.
2. Read context sources in the order given, plus the working directory's root `README.md` and the project's status record.
3. Read pre-digested files not already covered.
4. Report: session history, files read, project state as of the handoff's date, active skill, the open items (from the status record, or from the handoff's Open issues field where the project keeps no record), next steps, and todos where present. End with "Ready to continue."
5. Wait. Do not begin work until you confirm or redirect.

Two details in step 2 and step 4 are worth calling out.

**The root README is read whether or not the handoff names it.** A project's front door orients the session, and where the project has no `CLAUDE.md` the README carries the durable rules. The handoff rotates, and its list of context sources is one careless entry away from dropping the pointer.

**The handoff is frozen.** It describes the project as it stood on the date it was written, and that date may be weeks back. The resume reports its state fields as of that date rather than as current fact, and re-checks any specific claim a proposed next step depends on before asserting it. This is targeted, not a sweep of the project.

The **context** trigger runs the same five steps, then scans the working directory for immediate subfolders named `context` or `content`, or whose name contains the word "context", reads every file in each match, and adds a context folders line to the report.

---

## Design Rationale

**Why a structured file instead of a conversation export?**

A structured file is written by the model that had full context of the session. It compresses what matters and discards what does not. An export preserves everything equally and makes the next session re-read and re-interpret it. The handoff file is already interpreted.

**Why dual write (session log plus handoff)?**

The session log is permanent history and gives the project a timeline. The handoff is a rotating snapshot optimized for reconstruction. Combining them into one entry would either bloat the snapshot or truncate the history.

**Why exactly one handoff rather than two?**

An earlier version of this protocol kept two, current and previous, on the theory that the older one was a safety net. In practice it was not. A superseded handoff describes a state that has already changed, and a new session reading both has to work out which one is true. The real safety net is carry-forward: everything still open is copied into the new entry, so the older one holds nothing the newer one lacks. Once carry-forward is in place, the second entry is pure cost against a file that loads on every session. The session log entries, which are never deleted, preserve the history for anything you need to trace further back.

**Why did file lists and rationale move out of the handoff?**

Both grew without bound, and neither was what the next session needed at the moment it read the handoff. A file list is the least useful thing a handoff can offer a session that is about to open those files anyway. Rationale is valuable, but it is valuable when someone asks why, which is rare, not at the start of every session, which is constant. Moving both into a changelog file keeps them one read away and keeps the handoff a snapshot.

**Why install the protocol as a separate file instead of pasting it into `CLAUDE.md`?**

`CLAUDE.md` is loaded in full at the start of every session. A protocol this long sitting inside it is charged to every session in every project, including the many that never write a handoff. The protocol is needed at exactly two moments, the end of a session and the beginning of the next one, so it belongs in a file read on demand at those moments. The same reasoning shapes `CLAUDE.local.md`, which carries terse entries and a pointer to the changelog rather than the detail itself: what loads on every session should hold only what every session needs.

**Why list context sources explicitly rather than reading the whole directory?**

Projects accumulate files that are not equally relevant. Reading everything on every resume is slow and wastes the context window. Explicit sources let the session that wrote the handoff, which knows what matters, tell the next session where to look. Scoping each pointer to a section or a condition matters as much as naming the file, because an unscoped path means the whole file gets read.

**Why the "wait for instructions" step?**

The resume report is a status, not a proposal. Starting work automatically from the next steps field would be presumptuous: you may want to redirect, add constraints, or ask questions first. The protocol surfaces state and then stops.

---

## Installation

**Save `protocol.md` as a standalone file that Claude Code reads on demand.** The natural home is `~/.claude/protocols/handoff-and-resume.md`, inside your Claude Code configuration directory (`~/.claude/`), which makes the one copy available in every project.

**Then add one pointer to your `CLAUDE.md`,** something like:

```markdown
## Handoff, Resume, and Context

The full protocol lives in `~/.claude/protocols/handoff-and-resume.md`. Read it before
producing any handoff entry, session log entry, resume report, or context report, never
from memory.

These three procedures run ONLY when I type one of the trigger phrases below. Resume runs
at the start of a session, handoff at the end of one. Do not apply this protocol on any
other turn, and never write or offer a handoff on your own judgment. The short forms "ho"
and "re" count only when they are my entire message, never as those letters inside a
sentence.

- **Handoff** (only when I type a trigger): write a session log entry plus a handoff entry
  to `CLAUDE.local.md`. Both are written every time, whatever the session held. Triggers:
  "handoff", "write a handoff", "save a handoff", "handoff for next session", "ho",
  "ho todo [tasks]", "handoff todo [tasks]".
- **Resume** (only when I type a trigger): read the most recent handoff and its context
  sources, report project state, then wait. Triggers: "resume", "pick up", "catch me up", "re".
- **Context** (only when I type a trigger): run Resume, then read any context folders in the
  working directory in full. Triggers: "context", "full context", "load context".
```

If you would rather keep the protocol inside a single project instead of in `~/.claude/`, save it as `protocols/handoff-and-resume.md` in that project and change the path in the pointer to match; the pointer's path is read relative to the file it sits in, so an absolute path and a project-relative one are not interchangeable.

Do not paste the protocol body into `CLAUDE.md`. That file loads in full on every session, and the protocol is only needed when a handoff is written or read.

**Upgrading from an earlier version of this protocol.** Earlier releases told you to copy the protocol body straight into `CLAUDE.md`. If you did that, Claude reads the whole protocol, including its judgment-based guidance, on every single turn, and the common symptom is Claude offering or writing a handoff after ordinary turns instead of once at the end of a session. The fix: delete that block from your `CLAUDE.md`, save `protocol.md` as a separate file, and paste the short pointer above in its place.

The protocol is self-contained and does not depend on any other skill in this repository. It works in any Claude Code project where `CLAUDE.local.md` can be written to the working directory. The triggers are plain text phrases and need no configuration.

If you write your own skills, you can configure one to offer a handoff at the end of a long session. See the note for skill authors near the top of `protocol.md`. Without that configuration, Claude never offers one; the trigger phrases are the only way these procedures run.
