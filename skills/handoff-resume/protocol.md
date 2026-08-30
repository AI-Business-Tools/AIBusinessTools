# Handoff and Resume Protocol

This file is the canonical source for writing session log entries, handoffs, and per-session changelog files, and for the Resume and Context session-start procedures. Skills and ad-hoc work both follow these templates.

**Install this as a separate file that is read on demand, not as a block pasted into `CLAUDE.md`.** `CLAUDE.md` auto-loads in full at the start of every session, so a protocol pasted into it is paid for in every session whether or not a handoff is written. See `README.md` for the installation step.

A handoff is a structured summary written to `CLAUDE.local.md` that captures session state for the next thread. It is different from a raw conversation export, which dumps the full transcript. A handoff is concise, structured, and optimized for a new session to pick up where this one left off.

**Manual trigger:** when the user says "write a handoff," write a handoff entry to `CLAUDE.local.md` in the working directory.

**Auto-trigger (optional):** if your skills have Session Log sections, configure them to ask whether to write a handoff, but only when the session involved multiple rounds of edits, troubleshooting, or content iteration. A clean single-pass run does not prompt for a handoff.

---

## Where things live

- **`CLAUDE.local.md`** (project root, auto-loaded): the rolling state file. Short session log entries plus exactly one handoff entry, the most recent.
- **`changelog/`** (in the project folder, or a single shared changelog folder; not auto-loaded): per-session detailed records with file-level edit detail, key decisions, and rationale. This is the audit trail for rollback. It is reached from `CLAUDE.local.md` through the **Detail** field.
- **`CLAUDE.md`, your project standards files, and your skill files** (durable rules): rulings that should shape future work go here, not in a rotating log. A project-scoped rule goes in that project's `CLAUDE.md`; a rule that applies across projects goes wherever your setup keeps cross-project instructions; a rule a skill enforces goes in that skill file.

A durable rule in a rotating log is lost at the next rotation, and a durable rule in a changelog is never read, because changelog files are not loaded at session start. Route it to a file that is read.

---

## When to write what

| Session type | Session log entry? | Changelog file? | Handoff entry? |
|---|---|---|---|
| Routine work in a project folder | Yes | No | Only if the session involved multi-round edits or troubleshooting |
| Session that edits skills, scripts, protocols, or other durable configuration | Yes | Yes | Usually yes |
| Ad-hoc research or lookups producing no changes | No | No | No |
| Trivial edits | No | No | No |

---

## Session log entry format

Terse, targeting 3 to 5 lines.

```markdown
## [YYYY-MM-DD] - [topic]
- **Skill:** [skill name, or `ad-hoc`]
- **Summary:** [1-2 sentences, 30 words maximum. What changed; not why or how.]
- **Status:** [complete / pending / partial]
- **Detail:** [YYYY-MM-DD-topic.md](changelog/YYYY-MM-DD-topic.md)  (optional; omit when there is no changelog file)
```

The Summary cap is a ceiling, not a target. When you need more than two sentences, write a changelog file and point at it from **Detail**. Do not let the Summary grow into a small changelog, which is the failure this format exists to prevent. 30 words is the recommended default.

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

Which kind of session gets which kind of entry: a session that changed something a later session must find gets an entry; a session that answered a question and changed nothing does not. A session that changed durable configuration gets an entry and a changelog file, because that is the class of change someone will later need to trace or reverse.

---

## Handoff entry format

```markdown
## [YYYY-MM-DD] - Handoff
- **Session summary:** [1-2 sentences on what was accomplished]
- **Open issues:** ["none blocking", with nothing after it, is the expected outcome of a clean session and a stronger report than a list. An item earns this field only if it blocks the user, changes a deliverable they will use, or needs a decision only they can make now. Where the project keeps a status record, name it by path and stop there; the record holds the open set, and re-listing its rows here duplicates the file that is supposed to win. A defect you could fix now is not an open issue: fix it and omit it. This field is not an exemption from carry-forward below; the bar decides what is listed here, not what survives, and an item that fails the bar moves to the status record rather than being dropped.]
- **Next steps:** [work the next session does. Anything requiring a decision from the user is raised in the session itself, where it stays visible until answered, rather than parked here where it dies at the next rotation. What remains is informational, and each item names what goes wrong if nobody does it, in terms the user recognizes.]
- **Context for next session:** [anything the next thread needs to know that is not obvious from the files themselves]
- **Context sources:** [files and folders the next session should read at startup, in priority order, with paths relative to the project folder. Prefer digested files over raw sources. Scope each pointer to what the next session must actually read inside it: the part of the file, the condition for reading it at all, or how to read it. A bare path means the whole file, and the whole file is what a resume will read. Name files rather than a folder wherever you can; a folder's weight cannot be measured when the handoff is written.]
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

The retired handoff's paired session log entry is its permanent record. **Leave nothing in its place:** no tombstone line, no "retired here per the retention rule" note, no marker of any kind. The session log entry above it already is that record, and the file's size budget pays for every duplicate of it. Such notes accumulate, and they are billed to whichever entry precedes them, so an entry can fail its size check on text its own author never wrote.

### Carry-forward is mandatory

**Before deleting the prior handoff, copy every still-open item from its Open issues and Context for next session into the new handoff.** The new handoff must stand alone; nothing open may exist only in the entry about to be deleted. Without this rule, single-entry retention silently drops open work at every rotation.

**Next steps is deliberately excluded, and is the one field whose items are re-earned rather than inherited.** An action survives only where the session writing the handoff decides to write it again. An inherited next-steps list grows without limit and stops being read, because nothing in it was chosen by the session presenting it.

**Rewrite each carried item into the description-plus-identifier form above rather than copying it verbatim.** A bare identifier written once is otherwise reproduced by this rule in every handoff and every resume report until the item closes.

A handoff is a session-to-session instrument, not an archive. Anything that must outlive one session belongs in the project's status record, or in the destination the size budget routing names below, never in a handoff alone.

---

## Changelog files

Create a changelog file when a session touches skills, scripts, protocols, or other durable configuration, meaning anything that would need an audit trail if something breaks. Skip it for routine content processing, single-deliverable builds, or one-off research, unless the session made structural changes.

Naming: `YYYY-MM-DD-topic.md`, where topic is a short kebab-case descriptor.

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

## Close the status list in the same step

If the project keeps a status list (a tracker's open section, a punch list, a phase table), update it in the same step as the changelog write, not later. Shipping work and leaving its line open is what makes a tracker lie.

Two rules keep such a list trustworthy:

- **One place holds status.** Everything else in the document is narrative and history. A heading elsewhere saying "Queued next" or "Pending" describes what was true when it was written. Say so in the document, so a later reader does not mistake prose for state.
- **Every open item carries the check that proves it is still open**: a command, a search, a validator run, or a file condition. Then answering "what is open" means running the checks rather than reading the list. Items that cannot be reduced to a check (a judgment call, a design decision, something needing the user's eye) go in a separate section with an owner, or stay in the list with the check recorded as "none, by nature" and an owner named, never with a fabricated check.

Reporting an item as open is a claim about state and takes the same verification as reporting one done. Both directions fail in practice: work that shipped days earlier reported as still open, and a defect asserted from a source file without opening the artifact that would have shown it absent.

---

## Size budget

`CLAUDE.local.md` auto-loads in full at the start of every session in its folder, so its length is a fixed tax on every session in that project, paid whether or not the session ever looks at it. The entry formats above cap the parts; nothing caps the whole. This does.

**Recommended defaults, two of them enforced:**

| What | Ceiling | Enforced? |
|---|---|---|
| The whole `CLAUDE.local.md` file | 20,000 characters | Yes |
| The handoff entry | 6,000 characters | Yes |
| The session log entry just written | 2,000 characters | Advisory; report, never fail |
| The Summary field of the entry just written | 30 words | Advisory |

Measure at the end of every handoff write, before reporting the result. The file total is one command:

```bash
wc -c CLAUDE.local.md
```

For a single entry, from its heading to the next `## ` heading:

```bash
awk -v h="## 2026-03-14 - Handoff" 'index($0,h)==1{f=1} f && $0!~"^"h && /^## /{f=0} f' CLAUDE.local.md | wc -c
```

This is a rough check: it mismeasures when two entries share a heading string, which real files do carry as duplicate-dated headings, and it does not know which ceiling applies, so compare its number against 6,000 for a handoff heading and against the advisory 2,000 for anything else. If you automate the check, have the script report the file total, any handoff entry over its ceiling, the newest session log entry against the advisory ceiling, and the count of Summary fields over the word cap, and have it count multi-line Summary fields correctly, which a one-line text filter will not.

**Why only two of the four are enforced, and why the third looks at one entry.** The writer of today's handoff can fix the file total and the handoff entry. It cannot fix a session log entry written months ago. There is exactly one handoff in the file under the retention rule, so the enforced entry is always the one just written. The log ceiling reaches the same place by narrowing: it measures only the newest session log entry. A check that fires on old entries nobody will repair prints a flag forever, and that is how a reader learns to ignore the check that matters.

**A useful addition: report what the handoff's pointer fields will cost.** Count the files that **Context sources** and **Pre-digested** name and total their size, and report that number alongside the file total. Give it no ceiling. The number is the whole instrument: a reading list that states its own weight stops being append-only.

### When a ceiling is exceeded

- **The handoff entry is over its ceiling.** Trim narrative, evidence, and restatement of files the resume already reads, moving that detail into the session's changelog file and pointing at it from **Detail**. Never trim an open issue, a next step, or a context source to meet the ceiling. When open items alone push the handoff over, they belong in the project's status record and the handoff points at it by path; where the project has no status record, the handoff exceeds the ceiling and the writer reports the overage and the reason in one line. An over-budget handoff that carries the truth beats a compliant one that does not.
- **The file is over its ceiling.** First move the oldest session log entries, in date order, into a project archive file (an existing history folder, or `history/session-log-archive.md` created where neither exists), until the file is under. Entries are moved verbatim, never deleted. Leave one line in their place: `*Session log entries before YYYY-MM-DD are archived in [path] (N entries).*` If archiving history cannot bring the file under, trim the handoff bodies themselves, and relocate any durable rule per the routing below.
- **The new Summary is over the word cap.** The entry names more than the format holds. That is a changelog file and a **Detail** pointer, not a longer Summary. Pre-existing over-cap Summaries in old entries are history; leave them and archive them in due course.
- **The newest session log entry is over the advisory ceiling.** Same reading: shorten the one being written. This never fails the check.

**Make one cut sized to the whole overage, then re-measure once.** Converging in small shavings is the common failure: three or more check runs on a single write means the cuts are too small, not that the entry is too long.

**What a trim should cut.** Most of what a trim removes is the same facts written smaller, or content that moves to another file; only a small share is genuinely disposable, and that share is almost entirely one thing: re-listing the rows of a status record inside a handoff whose own text says the record wins. Cut that first. Relocation is the expensive disposition and the last to reach for, because text moved out of one file is usually rewritten longer in the file it lands in, and it may land somewhere the project does not read at session start.

### Where the overflow goes

Narrative, evidence, and reasoning go to the changelog. That is their right home and they stay one read away.

**A durable rule never goes to the changelog, because the changelog is not read at session start.** Route it instead:

- a project guardrail goes into the project's `CLAUDE.md`, which auto-loads every session, and is the first choice wherever one exists;
- a detailed convention goes into the project's standards file, read on demand;
- where no `CLAUDE.md` exists, the project's root `README.md`, which the resume reads, carries the guardrail;
- a rule a skill enforces goes into that skill file.

A carry-forward rule trimmed into a changelog to meet a byte budget is silently lost, which is the failure this budget exists to prevent, not to cause.

---

## The handoff confirmation

**Three slots, no fourth:** what was written, the measured total and any flags, and the result of any sync or push that ran. Anything needing the user's attention is raised before the handoff is written, so nothing is left to add by the time the confirmation is composed. Where something does survive to this point, it goes into the handoff or the status record and the confirmation names it by path rather than restating it. Nothing appears in the confirmation for the first time.

---

## General rules

- **Append new session log entries; never overwrite or delete them.** Session log entries accumulate. Handoffs rotate under the retention rule. Moving the oldest entries verbatim into the archive file, with the pointer line left in place, is relocation rather than deletion, and is the one sanctioned way history leaves this file.
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

---

## Resume

**This section is what a resume reads, and it is meant to be read alone.** Two rules elsewhere in this file bind the report below, so a resume reads those two as well and nothing else: "Delegation lives in the verb" and "A description travels with every identifier," both under **Handoff entry format**. Everything else in this file governs writing a handoff, a session log entry, or a changelog file, which a resume does not do; when the session later writes one, it reads the rest then.

When the user types **"resume"** at the start of a session:

1. **Read `CLAUDE.local.md`** in the working directory. Find the handoff entry and scan all `## [date] - [description]` session log entries for a project timeline.

2. **Read context sources.** Follow the **Context sources** field in the order given. For folders, list the contents first and read the most relevant files, preferring `_text.md`, `_summary.md`, `_notes.md`, outlines, and index files over raw sources or large data files. For files, read them directly.

   **Also read `README.md` at the working directory root when one exists, whether or not the handoff names it.** A project's front-door README orients the session, and where the project has no `CLAUDE.md` it also carries the durable rules. A handoff rotates, and its Context sources list is one careless entry away from dropping the pointer. Read only that root-level file, never READMEs deeper in the tree, and where the file turns out to be a developer setup guide rather than a project front door, note it and move on.

   **Read the project's status record too, where it keeps one, and print its open items in the step 4 report:** every open item, in priority order, one line each, never a summary and never prose in place of the list. The record is the open set and the handoff is not. A handoff froze when it was written, and its **Open issues** field points at the record rather than listing its rows, so a resume that reads only the handoff reports no open work however much is open.

   Where an open item names a check that is a single command, run it, and where the result shows the item's own premise no longer holds, say so in the report and name the item for closing. Do not close it in the resume, which reports and waits, and do not go looking for checks an item does not name.

   A project `CLAUDE.md`, where one exists, auto-loads at session start the same way `CLAUDE.local.md` does. Its rules are already in context, so do not re-read it as a ritual step. When a project defines its own session-start ritual in its `CLAUDE.md`, that ritual extends this procedure; it never replaces the steps here.

3. **Read pre-digested files.** Read anything listed in **Pre-digested** that step 2 did not already cover.

4. **Report.** Respond with a brief status. Put the summary fields in the quoted block, and render **Open items**, the handoff's **Next steps**, and **Todos**, when present, as top-level numbered lists below it, never nested under a bullet and never inside the quoted block. A blank line separates the quoted block, each heading, each numbered list, and the closing line, so a renderer cannot pull a list back inside the quote and relabel it. Identical source and on-screen numbering lets the user select an item by number.

   **The handoff froze when it was written.** Report its state fields as of its date, not as current fact, and before asserting any specific claim that a proposed next step depends on, re-read the file or run the check that confirms it. Only those claims: this is not a sweep of the whole project.

   > **Resumed from [date] handoff.**
   > - Session history: [one line per entry, format: `YYYY-MM-DD: description (skill)`]
   > - Read: [files and folders read]
   > - Project state (as of [handoff date]): [1-2 sentence summary from the handoff]
   > - Active skill: [from the handoff, or "none specified"]

   **Open items** (from [status record path]; omit this heading and its list where the project keeps no record):

   1. `[ID]` - [at most twelve words of plain language, never the item body]
   2. `[ID]` - [...]

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

---

## Context (full load)

When the user types **"context"**, run the full Resume protocol above (steps 1 to 5), then additionally:

6. **Scan for context folders.** List the working directory and check for any immediate subfolder whose name matches, case-insensitively: `context`, `content`, `content for context`, or any name starting with `aa context`. Also check for names containing "context for this".

7. **Read context folders in full.** For each matching folder, read every file in it, without recursing into sub-subfolders. For PDFs over 4 pages, read the first 4 pages only and note that the remainder was skipped. For binary files (images, `.pptx`, `.xlsx`), note their presence but do not read them.

8. **Amended report.** Add as the last line of the quoted summary block in the step 4 report:

   > - Context folders read: [folder names and file counts]

If no context folders are found, report that and proceed normally.

**Triggers:** "context", "full context", "load context"
