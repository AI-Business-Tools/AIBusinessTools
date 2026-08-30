# Handoff and Resume Protocol

Carry project context across Claude Code sessions without losing state.

---

## Problem

Every Claude Code session starts with an empty context window. On a single-session project this is fine. On a multi-session project it creates a recurring tax: re-explaining what was built, what decisions were made, what remains to be done, and which tools or conventions are in use. The longer a project runs, the higher the tax.

Raw conversation exports exist but are the wrong solution. A full transcript is large, unstructured, and expensive to re-read. It gives equal weight to productive exchanges and dead ends, and it cannot be used without another round of processing.

The handoff protocol solves this by capturing exactly what the next session needs: a concise structured snapshot written at the end of each session, reconstructed at the start of the next one.

---

## How It Works

At the end of a session you say "handoff" (or one of the trigger phrases). Claude Code writes two entries to `CLAUDE.local.md` in the working directory: a terse session log entry that stays forever, and a handoff entry that captures the current state and is replaced the next time you write one. Sessions that changed durable configuration also get a dated changelog file holding the file-level detail and the reasoning.

At the start of the next session you say "resume." Claude Code reads `CLAUDE.local.md`, reads the project's root `README.md` and its status record, follows the context sources the handoff lists, reads the pre-digested summaries, and reports a brief status before waiting for instructions.

The protocol is file-based. `CLAUDE.local.md` travels with the project, and every session in that directory shares the same history.

---

## The Handoff Entry

The handoff entry has seven required fields, plus two optional ones. Every field serves a specific purpose.

**Session summary** captures what was accomplished in 1-2 sentences. This is what you scan when you have forgotten what you were working on.

**Open issues** captures what is actually blocked or undecided. "None blocking" is the expected outcome of a clean session and a stronger report than a list. Where the project keeps a status record, this field names it by path rather than copying its rows, because two copies of the open set means one of them is wrong.

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

The session log entry is the permanent half of the dual write and is deliberately tiny: a dated heading, the skill used, a summary capped at a recommended 30 words, a status, and an optional pointer to the changelog. It records that something happened and where to look; it does not record what happened in detail.

The cap is the point. A summary allowed to grow becomes a small changelog inside a file that auto-loads on every session, and the cost is paid by every session in the project forever.

---

## Retention and Carry-Forward

`CLAUDE.local.md` keeps exactly one handoff entry: the most recent. On each write the new entry is appended first and the retired one deleted after, so the file is never momentarily without a handoff.

Single-entry retention only works because carry-forward is mandatory. Before the prior handoff is deleted, every still-open item in its **Open issues** and **Context for next session** is copied into the new one. The new handoff must stand alone. Without that rule, rotation silently drops open work, and the drop is invisible because the evidence is deleted in the same step.

**Next steps is the one field excluded from carry-forward, on purpose.** Its items are re-earned rather than inherited: an action survives only where the session writing the handoff decides to write it again. An inherited list of next steps grows without limit and stops being read, because nothing in it was chosen by the session presenting it.

---

## The Size Budget

`CLAUDE.local.md` auto-loads in full at the start of every session in its folder. Its length is therefore a standing tax on every session in that project, paid whether or not the session ever looks at the file. The entry formats cap the parts; the size budget caps the whole.

The recommended defaults are 20,000 characters for the file and 6,000 for the handoff entry, both enforced, plus an advisory 2,000 for the session log entry just written and the 30-word summary cap. The two enforced numbers are the two the current session can actually fix. An entry written months ago cannot be repaired by today's writer, so measuring it would print a flag forever, and a check that always fires is a check nobody reads.

When the file goes over, the remedy is archival, not deletion: the oldest session log entries move verbatim into a project archive file, leaving a single pointer line behind. When the handoff entry goes over, narrative and evidence move to the changelog, and open items move to the project's status record. Open issues, next steps, and context sources are never trimmed to hit a number.

**Where the overflow goes matters more than that it went.** Narrative belongs in the changelog. A durable rule never does, because changelog files are not read at session start; a rule trimmed there to save bytes is silently lost. Durable rules go to the project's `CLAUDE.md`, its standards file, its root `README.md`, or the skill that enforces them.

---

## The Changelog

A changelog file is written when a session touches skills, scripts, protocols, or other durable configuration, meaning anything that would need an audit trail if it later breaks. Routine content work does not get one.

Naming is `YYYY-MM-DD-topic.md`, and the file holds the three things the rolling state file no longer carries: which files changed and where, why the choices were made, and what was open at the time. It is linked from the **Detail** field of both the session log entry and the handoff, which is the only way it gets found. The protocol deliberately keeps no index of changelog files: an index duplicates every file it links to and goes stale unread, while a directory listing and a recursive search do the job.

---

## The Resume Protocol

When you type "resume," Claude Code runs a five-step sequence before doing anything else.

1. Read `CLAUDE.local.md`. Find the handoff entry and scan the session log entries for a timeline.
2. Read context sources in the order given, plus the working directory's root `README.md` and the project's status record.
3. Read pre-digested files not already covered.
4. Report: session history, files read, project state as of the handoff's date, active skill, the status record's open items, next steps, and todos where present. End with "Ready to continue."
5. Wait. Do not begin work until you confirm or redirect.

Two details in step 2 and step 4 are worth calling out.

**The root README is read whether or not the handoff names it.** A project's front door orients the session, and where the project has no `CLAUDE.md` the README carries the durable rules. The handoff rotates, and its list of context sources is one careless entry away from dropping the pointer.

**The handoff is frozen.** It describes the project as it stood on the date it was written, and that date may be weeks back. The resume reports its state fields as of that date rather than as current fact, and re-checks any specific claim a proposed next step depends on before asserting it. This is targeted, not a sweep of the project.

The **context** trigger runs the same five steps, then scans the working directory for folders named `context`, `content`, `aa context`, or similar, reads every file in each match, and adds a context folders line to the report.

---

## Design Rationale

**Why a structured file instead of a conversation export?**

A structured file is written by the model that had full context of the session. It compresses what matters and discards what does not. An export preserves everything equally and makes the next session re-read and re-interpret it. The handoff file is already interpreted.

**Why dual write (session log plus handoff)?**

The session log is permanent history and gives the project a timeline. The handoff is a rotating snapshot optimized for reconstruction. Combining them into one entry would either bloat the snapshot or truncate the history.

**Why exactly one handoff rather than two?**

An earlier version of this protocol kept two, current and previous, on the theory that the older one was a safety net. In practice it was not. A superseded handoff describes a state that has already changed, and a new session reading both has to work out which one is true. The real safety net is carry-forward: everything still open is copied into the new entry, so the older one holds nothing the newer one lacks. Once carry-forward is in place, the second entry is pure cost against a file that loads on every session. The session log entries, which are never deleted, preserve the history for anything you need to trace further back.

**Why did file lists and rationale move out of the handoff?**

Both grew without bound and both were paid for on every session in the project. A file list is the least compressible content in a handoff and the least useful to a session that is about to read the files anyway. Rationale is valuable, but it is valuable at the moment someone asks why, which is rare, not at the start of every session, which is constant. Moving both to a changelog file keeps them one read away and takes them off the standing bill.

**Why install the protocol as a separate file instead of pasting it into `CLAUDE.md`?**

`CLAUDE.md` is loaded in full at the start of every session. A protocol this long sitting inside it is charged to every session in every project, including the many that never write a handoff. The protocol is needed at exactly two moments, the end of a session and the beginning of the next one, so it belongs in a file read on demand at those moments. The same reasoning drives the size budget on `CLAUDE.local.md`: anything that auto-loads is a standing tax, and the way to keep it honest is to measure it.

**Why list context sources explicitly rather than reading the whole directory?**

Projects accumulate files that are not equally relevant. Reading everything on every resume is slow and wastes the context window. Explicit sources let the session that wrote the handoff, which knows what matters, tell the next session where to look. Scoping each pointer to a section or a condition matters as much as naming the file, because an unscoped path means the whole file gets read.

**Why the "wait for instructions" step?**

The resume report is a status, not a proposal. Starting work automatically from the next steps field would be presumptuous: you may want to redirect, add constraints, or ask questions first. The protocol surfaces state and then stops.

---

## Installation

**Save `protocol.md` as a standalone file that Claude Code reads on demand.** A natural home is `protocols/handoff-and-resume.md` inside your Claude Code configuration directory, or a `protocols/` folder in the project itself.

**Then add one pointer to your `CLAUDE.md`,** something like:

```markdown
## Handoff, Resume, and Context

The full protocol lives in `protocols/handoff-and-resume.md`. Read it before producing
any handoff entry, session log entry, resume report, or context report, never from memory.

- **Handoff:** write a session log entry plus a handoff entry to `CLAUDE.local.md`.
  Triggers: "handoff", "write a handoff", "ho", "ho todo [tasks]".
- **Resume:** read the most recent handoff and its context sources, report project state,
  then wait. Triggers: "resume", "pick up", "catch me up", "re".
- **Context:** run Resume, then read any context folders in the working directory in full.
  Triggers: "context", "full context", "load context".
```

Do not paste the protocol body into `CLAUDE.md`. That file loads in full on every session, and the protocol is only needed when a handoff is written or read.

The protocol is self-contained and does not depend on any other skill in this repository. It works in any Claude Code project where `CLAUDE.local.md` can be written to the working directory. The triggers are plain text phrases and need no configuration.

If you use skills with their own Session Log sections, you can configure them to ask whether to write a handoff at the end of a multi-round session. See the **Auto-trigger** note in `protocol.md`.
