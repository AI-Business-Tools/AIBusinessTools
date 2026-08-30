# Knowledge Base Update

Companion skill to `knowledge-base`. Where `knowledge-base` processes one document at a time (the Process Inbox flow) or answers a question, `knowledge-base-update` sweeps the entire knowledge base and reconciles the index against what is actually on disk.

## Problem

A knowledge base drifts. You drop a file into a topic folder manually, you rename a folder, you delete an obsolete summary, you forget to file something. The `index.md` accumulates errors silently: stale entries for files that no longer exist, missing entries for files that were never indexed, naming inconsistencies that make search unreliable. Without a maintenance pass, the index becomes untrustworthy and the value of the whole system erodes.

## Approach

This skill runs a periodic sweep with two phases.

**Phase 1: Sync.** Scan every topic folder. Add index entries for documents that are present on disk but missing from `index.md`. Remove index entries for files that no longer exist. Refresh `topics.md` based on current folder contents.

**Phase 2: Health check.** Surface drift the user should look at: source files without summaries, summaries without source files, files that violate the naming convention, possible duplicates, and topic-folder placement suggestions.

The skill never deletes source files and never overwrites summaries. It proposes renames and moves; the user confirms.

## The Flow

1. **Identify the knowledge base root.** Edit the path placeholder in `SKILL.md` to match where your knowledge base lives.
2. **Step 1: Sync the index.** The skill reads `index.md`, scans all topic folders, and computes the diff: entries to add (documents on disk but not indexed), entries to remove (indexed but missing), and `topics.md` updates.
3. **Step 1b: Clean up the inbox build folder.** Stale split directories from the `knowledge-base` Process Inbox flow are identified and removed if the source file has already been filed.
4. **Step 2: Health check.** The skill reports missing summaries, orphaned summaries, naming inconsistencies, duplicate content, and topic placement suggestions. Each issue is presented with a proposed fix; the user confirms before any changes are made. A folder is flagged for a missing summary only when it holds a real source, and a folder that is deliberately not a document can carry a `.kbskip` sentinel so it is reported as suppressed rather than flagged on every run.
5. **Step 2b: Overflow re-homing review.** Once a catch-all folder passes about 50 items, the skill reads the frontmatter of what is in it and proposes specific re-homes, so the folder that absorbs everything without an obvious home does not quietly become a second inbox.

## Usage

**Trigger phrases:**
- "kb update"
- "kb up"
- "update kb"
- "kb sync"

**Good uses:**
- Periodic maintenance pass (weekly or monthly)
- After a manual reorganization (moving files between folders, renaming a topic)
- Before relying on the knowledge base for a query-heavy workflow
- After a long break when you've forgotten what was filed where

**Not good uses:**
- One-document indexing: use the `knowledge-base` skill's Process Inbox flow instead
- Summary generation: this skill reports missing summaries but does not generate them
- Querying the knowledge base: use the `knowledge-base` skill's Q&A flow

**Tip:** Run `kb update` after every batch processing session. It is much faster to keep the index honest as you go than to clean up months of drift in a single sitting.

## Installation

1. Copy `SKILL.md` into `~/.claude/skills/knowledge-base-update/SKILL.md`.
2. Open the file and replace the `<knowledge-base-root>` placeholder at the top with the actual path to your knowledge base (e.g., `~/knowledge-base/`). Adjust the directory pattern descriptions, naming convention, and skip-folder list to match your conventions.
3. Restart Claude Code (or run `/skills` to reload).
4. Trigger by saying "kb update" or any other listed trigger phrase.

The `knowledge-base` skill is a soft prerequisite. `knowledge-base-update` does not call into it, but it assumes the same on-disk structure (topic folders, `_summary.md` and `_text.md` companion files, `index.md` and `topics.md` at the root). If you use the `knowledge-base` skill's defaults, no further customization is needed.

## Output

`knowledge-base-update` does not produce a deliverable file beyond the changes it makes to `index.md` and `topics.md` in your knowledge base. It produces an interactive report with sections:

- **Sync summary:** N entries added, M entries removed, K folders refreshed in `topics.md`
- **Stale build folders:** list of split directories cleaned up
- **Health check:** missing summaries, orphaned summaries, naming issues, duplicates, placement suggestions

The user is asked to confirm fixes before any moves or renames are applied.

## Design Rationale

**Why a separate skill, not a flag on `knowledge-base`?** The skills are different in flow. `knowledge-base` is event-driven (a document arrives, process it; a question arrives, answer it). `knowledge-base-update` is sweep-driven (look at everything at once). Keeping them separate makes each easier to reason about and lets the user invoke maintenance independently of any specific document.

**Why never delete source files?** Files are user-curated artifacts. Even if a source has no summary and seems like a dead entry, it might be intentionally parked. The skill flags but does not act.

**Why interactive confirmation for moves and renames?** Topic-folder placement and naming conventions are judgment calls. The skill's suggestions are advisory; the user is the authority.

**Why is `materials/` skipped?** A topic folder may contain reference material that should sit physically near related kb content but is not itself indexable (third-party PDFs, working notes, external project artifacts). The `materials/` convention provides an opt-out without requiring a separate location.
