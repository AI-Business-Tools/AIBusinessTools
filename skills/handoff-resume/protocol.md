# Handoff and Resume Protocol

This file is the canonical source for writing session log entries, handoffs, and per-session changelog files, and for the Resume and Context session-start procedures. Skills and ad-hoc work both follow these templates.

**Install this as a separate file that is read on demand, not as a block pasted into `CLAUDE.md`.** `CLAUDE.md` auto-loads in full at the start of every session, so a protocol pasted into it is paid for in every session whether or not a handoff is written. See `README.md` for the installation step.

A handoff is a structured summary written to `CLAUDE.local.md` that captures session state for the next thread. It is different from a raw conversation export, which dumps the full transcript. A handoff is concise, structured, and optimized for a new session to pick up where this one left off.

## When this fires

**A handoff is written once, at the end of a session, and only when the user types one of the handoff trigger phrases listed at the end of this file. Resume runs only at the start of a session, on its own trigger. On every other turn this protocol does nothing.**

Never write, offer, or prepare a handoff on your own judgment, and never write more than one per trigger. Finishing a piece of work is not a trigger. Editing several files is not a trigger. A session that feels like a good stopping point is not a trigger. The user's word is the only trigger.

**Optional, for skill authors. This paragraph is not an instruction to Claude.** If you write your own skills, you may configure one to offer a handoff at the end of a long session. Absent that configuration, Claude never offers one.

---

## Where things live

- **`CLAUDE.local.md`** (project root, auto-loaded): the rolling state file. Short session log entries plus exactly one handoff entry, the most recent. It holds one person's working state, so in a shared repository add it to `.gitignore`; commit it only where the whole team wants the same session history, and never where it would push private working notes into a public repo.
- **`changelog/`** (in the project folder, or a single shared changelog folder; not auto-loaded): per-session detailed records with file-level edit detail, key decisions, and rationale. This is the audit trail for rollback. It is reached from `CLAUDE.local.md` through the **Detail** field. Create the folder the first time a changelog file is written: a **Detail** link resolves only once the folder and the file it names both exist.
- **The project's status record** (optional; many projects have none): whichever single file the project keeps its open items in, such as a tracker's open section, a punch list, a phase table, or an issues file. It is the open set, so a handoff points at it by path instead of copying its rows, and a resume prints its items. **Where a project keeps none, the handoff's Open issues field is the open set**, and every still-open item survives by being carried forward into each new handoff under the carry-forward rule below. Start a status record once that list outgrows a few lines.
- **`CLAUDE.md`, your project standards files, and your skill files** (durable rules): rulings that should shape future work go here, not in a rotating log. A project-scoped rule goes in that project's `CLAUDE.md`; a rule that applies across projects goes wherever your setup keeps cross-project instructions; a rule a skill enforces goes in that skill file.

**A durable rule in a rotating log is lost at the next rotation, and a durable rule in a changelog is never read, because changelog files are not loaded at session start.** A rule parked in either place disappears without anyone noticing, which is the one failure in this protocol that leaves no evidence behind. Route it to a file that is read:

- a project guardrail goes into the project's `CLAUDE.md`, which auto-loads every session, and is the first choice wherever one exists;
- a detailed convention goes into the project's standards file, read on demand;
- where no `CLAUDE.md` exists, the project's root `README.md`, which the resume reads, carries the guardrail;
- a rule a skill enforces goes into that skill file.

---

## When to write what

**This section is consulted only after the user has triggered a handoff. It never decides whether to start one.**

**Once the user triggers a handoff, both records are always written: the session log entry and the handoff entry.** Neither is conditional. A short session, a session of small edits, and a session that only answered questions all get both, because the user asked for a handoff and a trigger that produces nothing is a broken trigger. The one judgment left is whether the session also warrants a changelog file, and that is what this table answers.

| Session type | Changelog file? |
|---|---|
| Routine work in a project folder | No |
| Session that edits skills, scripts, protocols, or other durable configuration | Yes |
| Ad-hoc research or lookups producing no changes | No |
| Trivial edits | No |

---

## Session log entry format

Terse, targeting 3 to 5 lines.

```markdown
## [YYYY-MM-DD] - [topic]
- **Skill:** [skill name, or `ad-hoc`]
- **Summary:** [1-2 sentences, within the 30-word cap. What changed; not why or how.]
- **Status:** [complete / pending / partial]
- **Detail:** [YYYY-MM-DD-topic.md](changelog/YYYY-MM-DD-topic.md)  (optional; omit when there is no changelog file)
```

The 30-word cap is a ceiling, not a target. When you need more than two sentences, write a changelog file and point at it from **Detail**. Do not let the Summary grow into a small changelog, which is the failure this format exists to prevent.

Worked example:

```markdown
## 2026-03-14 - Report generator refactor
- **Skill:** ad-hoc
- **Summary:** Split the report generator into a data layer and a rendering layer, and moved the date handling into one helper. Output is unchanged.
- **Status:** complete
- **Detail:** [2026-03-14-report-generator-refactor.md](changelog/2026-03-14-report-generator-refactor.md)
```

A skill may add one skill-specific field, for example **Source:** for a content-driven skill or **Deliverables:** for a generator skill.

**The session log entry carries no file list and no rationale paragraph.** File-level detail and reasoning go in the changelog file when the session warrants one, and nowhere when the session does not. Durable rulings go to the files named under "Where things live."

Every triggered handoff writes this entry, whatever the session held. What varies is the changelog file beside it: a session that changed durable configuration gets one, because that is the class of change someone will later need to trace or reverse, and a session that answered a question and changed nothing does not.

---

## Handoff entry format

```markdown
## [YYYY-MM-DD] - Handoff
- **Session summary:** [1-2 sentences on what was accomplished]
- **Open issues:** ["none blocking", with nothing after it, is the expected outcome of a clean session and a stronger report than a list. An item earns this field only if it blocks the user, changes a deliverable they will use, or needs a decision only they can make now. Where the project keeps a status record, name it by path and stop there; the record holds the open set, and re-listing its rows here duplicates the file that is supposed to win. A defect you could fix now is not an open issue: fix it and omit it. This field is not an exemption from carry-forward below; the bar decides what is listed here, not what survives, and an item that fails the bar moves to the status record rather than being dropped. Where the project keeps no status record, this field is the open set: the item stays here and is carried forward.]
- **Next steps:** [work the next session does. Anything requiring a decision from the user is raised in the session itself, where it stays visible until answered, rather than parked here where it dies at the next rotation. What remains is informational, and each item names what goes wrong if nobody does it, in terms the user recognizes.]
- **Context for next session:** [anything the next thread needs to know that is not obvious from the files themselves]
- **Context sources:** [files and folders the next session should read at startup, in priority order, with paths relative to the project folder. Prefer digested files over raw sources. Scope each pointer to what the next session must actually read inside it: the part of the file, the condition for reading it at all, or how to read it. A bare path means the whole file, and the whole file is what a resume will read. Name files rather than a folder wherever you can; what a folder will hold cannot be known when the handoff is written.]
- **Pre-digested:** [any `_text.md`, `_summary.md`, `_notes.md`, or other processed files that exist and are current. These are cheaper to read than re-processing the source.]
- **Active skill:** [which skill was last used or should be used next, so the next session routes correctly without asking]
- **Detail:** [YYYY-MM-DD-topic.md](changelog/YYYY-MM-DD-topic.md)  (optional; omit when there is no changelog file)
- **Todos:** [tasks to surface on resume. Present only when the handoff was triggered with "todo" items. One bullet per todo.]
```

Seven fields are always present. **Detail** and **Todos** are optional.

**Delegation lives in the verb.** When a next step is meant to run in a subagent, the step's leading verb says so ("Launch an agent to build X", not "Build X (run it in an agent)"). A delegation instruction trailing at the end of a sentence is read past, and the work starts in the main thread.

**A description travels with every identifier.** A tracked row, a rule code, or a decision number carries a plain-language description of what it is in the same sentence, every time it is named, not only on first mention. A bare identifier makes the reader open a file to learn what is being discussed, which is the cost the record exists to avoid. This binds the **Next steps** and **Open issues** fields, and any report rendered from them. The identifier is never dropped either; both travel together.

**A handoff does not re-gate a decision the user has already made.** A next step pointing at work the user already chose carries no approval condition. Writing one on makes the next session stop for an approval it already has, and it will obey the handoff over the protocol.

---

## Dual write on handoff

Every handoff writes two entries to `CLAUDE.local.md`:

1. **Session log entry** (permanent history), in the terse format above. Never deleted.
2. **Handoff entry** (rotating snapshot), in the handoff format above. Rotates per the retention rule below.

Write the session log entry first, then the handoff entry. If a skill's Session Log section already logged the session's work, skip the session log entry and write only the handoff. If the session warrants a changelog file, write it before the session log entry and reference it from the **Detail** field of both.

**Todo variant:** when the trigger includes "todo" followed by one or more tasks (for example `ho todo run the backup, update the index`), parse the tasks into the **Todos** field. Tasks may be comma-separated or on separate lines. When no "todo" follows the trigger, omit the field entirely.

---

## Retention rule

**Keep exactly one handoff entry in `CLAUDE.local.md`: the most recent.** On each handoff write, append the new handoff entry first, then delete the retired one, so the file never has a moment with no handoff. When two handoff entries share a date, the retired one is the earlier in file order, and the day's second and later are headed `Handoff (2)`, `Handoff (3)`.

The retired handoff's paired session log entry is its permanent record. **Leave nothing in its place:** no tombstone line, no "retired here per the retention rule" note, no marker of any kind. The session log entry above it already is that record, so a marker says nothing the file does not already say, and such markers accumulate into a layer of bookkeeping every later session reads past.

### Carry-forward is mandatory

**Before deleting the prior handoff, copy every still-open item from its Open issues and Context for next session into the new handoff.** The new handoff must stand alone; nothing open may exist only in the entry about to be deleted. Without this rule, single-entry retention silently drops open work at every rotation.

**Next steps is deliberately excluded, and is the one field whose items are re-earned rather than inherited.** An action survives only where the session writing the handoff decides to write it again. An inherited next-steps list grows without limit and stops being read, because nothing in it was chosen by the session presenting it.

**Rewrite each carried item into the description-plus-identifier form above rather than copying it verbatim.** A bare identifier written once is otherwise reproduced by this rule in every handoff and every resume report until the item closes.

A handoff is a session-to-session instrument, not an archive. Anything that must outlive one session belongs in the project's status record, or in the destination named under "Where things live" above, never in a handoff alone. Where the project keeps no status record, the handoff is the only carrier the item has, and the carry-forward rule above is the whole of what keeps it alive; that fragility is the argument for starting a status record.

---

## Changelog files

Create a changelog file when a session touches skills, scripts, protocols, or other durable configuration, meaning anything that would need an audit trail if something breaks. Skip it for routine content processing, single-deliverable builds, or one-off research, unless the session made structural changes.

Naming: `YYYY-MM-DD-topic.md`, where topic is a short kebab-case descriptor. Create the `changelog/` folder if the project does not have one yet, before writing the file; a **Detail** link points at a path, and the path resolves only once the folder and the file both exist.

Content: full file-level edit detail (which files, which sections or lines), key decisions and rationale, and open issues at the time of the session. This is the detail that would otherwise bloat `CLAUDE.local.md`.

```markdown
# YYYY-MM-DD - [Topic]

**Skill:** [skill name, or ad-hoc]
**Status:** [complete / pending / partial]

## Files created/modified
[bullet list with paths, with section or line specificity where it helps]

## Key decisions and rationale
[paragraphs explaining why; the narrative that ties several file edits together]

## Open issues (at time of session)
[anything that did not get done and should be tracked]
```

**The Detail pointer is how a changelog file is found.** Link it from the **Detail** field of the session log entry and from the **Detail** field of the handoff that owns it. Name it in **Context sources** as well when the next session needs it.

**Do not build an index of changelog files.** Each index entry duplicates the file it links to and goes stale unread. `ls changelog/` is the listing, and a recursive grep across the bodies is the search; it finds what an index misses.

---

## The handoff confirmation

The confirmation is the short message sent to the user in chat once the handoff is written, and it has **three slots, no fourth:** which entries were written and to which files, anything the write itself turned up (an open item that could not be carried, a pointer that no longer resolves), and the result of any commit, sync, or backup that ran. For example: `Wrote the session log entry and the handoff entry to CLAUDE.local.md, plus changelog/2026-03-14-report-generator-refactor.md. Nothing flagged. No commit run.` Anything needing the user's attention is raised before the handoff is written, so nothing is left to add by the time the confirmation is composed. Where something does survive to this point, it goes into the handoff or the status record and the confirmation names it by path rather than restating it. Nothing appears in the confirmation for the first time.

---

## General rules

- **Append new session log entries; never overwrite or delete them.** Session log entries accumulate; handoffs rotate under the retention rule. When the accumulated entries have grown long enough to be in the way, move the oldest ones, in date order, verbatim into a project archive file, and leave one line in their place: `*Session log entries before YYYY-MM-DD are archived in [path] (N entries).*` That relocation is the one sanctioned way history leaves this file. Deleting an entry is not.
- **Relative paths.** File references in `CLAUDE.local.md` are relative to the folder containing it, not absolute. Changelog files may use absolute paths, since they are write-once audit records.
- **If `CLAUDE.local.md` does not exist**, create it with:

  ```markdown
  # Project Context

  Session log entries appended by Claude Code. Detailed per-session records in changelog/.
  ```

- **Reading `CLAUDE.local.md` at session start:** use it to understand project state, but do not summarize or repeat it back unless asked.
- **Do not write duplicates.** If a skill wrote an entry, do not write another.
- **Ad-hoc work** (no skill invoked) uses the same entry format, with **Skill:** set to `ad-hoc`.

**Handoff triggers:** "handoff", "write a handoff", "save a handoff", "handoff for next session", "ho", "ho todo [tasks]", "handoff todo [tasks]"

**The short forms `ho` and `re` are recognized only when they are the user's entire message**, never when those two letters appear inside a sentence.

---

## Resume

**This section is what a resume reads, and it is meant to be read alone.** Two rules elsewhere in this file bind the report below, so a resume reads those two as well and nothing else: "Delegation lives in the verb" and "A description travels with every identifier," both under **Handoff entry format**. Everything else in this file governs writing a handoff, a session log entry, or a changelog file, which a resume does not do; when the session later writes one, it reads the rest then.

When the user types **"resume"** at the start of a session:

1. **Read `CLAUDE.local.md`** in the working directory. Find the handoff entry and scan all `## [date] - [description]` session log entries for a project timeline.

2. **Read context sources.** Follow the **Context sources** field in the order given. For folders, list the contents first and read the most relevant files, preferring `_text.md`, `_summary.md`, `_notes.md`, outlines, and index files over raw sources or large data files. For files, read them directly.

   **Also read `README.md` at the working directory root when one exists, whether or not the handoff names it.** A project's front-door README orients the session, and where the project has no `CLAUDE.md` it also carries the durable rules. A handoff rotates, and its Context sources list is one careless entry away from dropping the pointer. Read only that root-level file, never READMEs deeper in the tree, and where the file turns out to be a developer setup guide rather than a project front door, note it and move on.

   **Read the project's status record too, where it keeps one, and print its open items in the step 4 report:** every open item, in priority order, one line each, never a summary and never prose in place of the list. The status record is whichever single file the project keeps its open items in, a tracker's open section, a punch list, a phase table, or an issues file; many projects keep none, and there the handoff's own **Open issues** field is the open set. The record is the open set and the handoff is not. A handoff froze when it was written, and its **Open issues** field points at the record rather than listing its rows, so a resume that reads only the handoff reports no open work however much is open.

   A project `CLAUDE.md`, where one exists, auto-loads at session start the same way `CLAUDE.local.md` does. Its rules are already in context, so do not re-read it as a ritual step. When a project defines its own session-start ritual in its `CLAUDE.md`, that ritual extends this procedure; it never replaces the steps here.

3. **Read pre-digested files.** Read anything listed in **Pre-digested** that step 2 did not already cover.

4. **Report.** Respond with a brief status. Put the summary fields in the quoted block, and render **Open items**, the handoff's **Next steps**, and **Todos**, when present, as top-level numbered lists below it, never nested under a bullet and never inside the quoted block. A blank line separates the quoted block, each heading, each numbered list, and the closing line, so a renderer cannot pull a list back inside the quote and relabel it. Identical source and on-screen numbering lets the user select an item by number.

   **The handoff froze when it was written.** Report its state fields as of its date, not as current fact, and before asserting any specific claim that a proposed next step depends on, re-read the file or run the check that confirms it. Only those claims: this is not a sweep of the whole project.

   > **Resumed from [date] handoff.**
   > - Session history: [one line per entry, format: `YYYY-MM-DD: description (skill)`]
   > - Read: [files and folders read]
   > - Project state (as of [handoff date]): [1-2 sentence summary from the handoff]
   > - Active skill: [from the handoff, or "none specified"]

   **Open items** (from [status record path], or from the handoff's **Open issues** field where the project keeps no status record; omit this heading and its list where there are none):

   1. [the item's ID first where the record uses IDs, and nothing in its place where it does not, then at most twelve words of plain language, never the item body]
   2. [same]

   **Next steps** (from the handoff):

   1. [item, then what goes wrong if nobody does it]
   2. [item]

   **Todos** (only when the handoff has a Todos field; omit the heading and its list entirely when there are none):

   1. [first todo]
   2. [second todo]

   Ready to continue.

5. **Wait for instructions.** Do not begin work until the user confirms or redirects.

If no handoff entry exists in `CLAUDE.local.md`, read the most recent session log entry instead and report what was found, including the full session history timeline. If `CLAUDE.local.md` does not exist, say so and ask what to work on.

**Triggers:** "resume", "pick up", "catch me up", "re"

**The short forms `re` and `ho` are recognized only when they are the user's entire message**, never when those two letters appear inside a sentence.

---

## Context (full load)

When the user types **"context"**, run the full Resume protocol above (steps 1 to 5), then additionally:

6. **Scan for context folders.** List the working directory and check for any immediate subfolder whose name, case-insensitively, is `context` or `content`, or contains the word "context" (for example `context for this project`, or a name your own filing convention prefixes).

7. **Read context folders in full.** For each matching folder, read every file in it, without recursing into sub-subfolders. For PDFs over 4 pages, read the first 4 pages only and note that the remainder was skipped. For binary files (images, `.pptx`, `.xlsx`), note their presence but do not read them.

8. **Amended report.** Add as the last line of the quoted summary block in the step 4 report:

   > - Context folders read: [folder names and file counts]

If no context folders are found, report that and proceed normally.

**Triggers:** "context", "full context", "load context"
