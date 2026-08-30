---
name: knowledge-base-update
description: Knowledge base sync and health check for the knowledge-base skill. Scans all topic folders for unindexed documents, removes index entries for missing files, refreshes topic descriptions, cleans up stale split directories, and reports health issues (missing summaries, naming inconsistencies, orphaned files, duplicate content).
triggers: kb update, kb up, update kb, kb sync
allowed-tools: Bash(python*), Bash(pip*), Bash(ls*), Bash(mv*), Bash(cp*), Bash(mkdir*), Bash(find*), Bash(wc*), Bash(file*), Read, Write, Edit, Glob, Grep, Agent
model: sonnet
effort: medium
---

# Knowledge Base Update

Sync the `knowledge-base` skill's index with the contents of the knowledge base on disk, then run a health check. Companion skill to `knowledge-base`: where `knowledge-base` processes new documents one at a time and answers queries, this skill keeps the index honest and surfaces drift.

## Knowledge Base Location

Edit the path below to match the knowledge base root used by the `knowledge-base` skill on this system:

```
<knowledge-base-root>/
```

All paths in this skill are relative to that root. A common default is `~/knowledge-base/`.

## Directory Structure

The knowledge base supports two document storage patterns:

**Pattern A: Per-document subfolder** (output of a content pipeline like `slides-content`)
```
<knowledge-base-root>/
├── topic-folder/
│   ├── 2026-01-28 Author. Title./
│   │   ├── Title._text.md
│   │   ├── Title._summary.md
│   │   └── Title._slides.pdf
```

**Pattern B: Flat files** (output of the `knowledge-base` Process Inbox mode)
```
<knowledge-base-root>/
├── topic-folder/
│   ├── 2026-03-18 Author. Title.pdf
│   ├── 2026-03-18 Author. Title._text.md
│   └── 2026-03-18 Author. Title._summary.md
```

Topic folders are dynamic: any immediate subdirectory of the knowledge base root other than the inbox folder, any blog folder, any auxiliary folders (for example, a recents or symlink folder, a search-index or database folder, or a documentation folder that describes the knowledge base process itself rather than holding indexable content), and any `*_build/` directory is a topic folder. When scanning, search both patterns:
- Flat: `<topic-folder>/*_summary.md`
- Subfolder: `<topic-folder>/*/*_summary.md`

**Reference material (`materials/` subfolders):** any subfolder named `materials/` at any depth inside the knowledge base is reference-only. Skip its contents entirely during sync and health checks. No scanning, no index entries, no missing-summary warnings, no naming checks. Use this to park files that should live inside a topic folder for proximity but are not indexable knowledge base content (third-party reference docs, working notes, artifacts from external projects).

**Intentional non-documents (`.kbskip` sentinel):** a folder that holds real files but is not a knowledge base document (a working capture, a parked external project) can carry a `.kbskip` file. Presence is what matters; the content is optional. The health check in Step 2 then does not flag it for a missing summary. It reports it under SKIP-SUPPRESSED instead, so nothing is silently dropped and a real document added later resurfaces. Unlike `materials/`, this moves and hides nothing: the folder stays where it is, and its content stays findable if it has a summary. Put the sentinel in the specific subfolder, never at a topic root. A root sentinel suppresses nothing and should be reported so it can be moved into the subfolder it was meant for.

## Index Format

`index.md` is a markdown table at the knowledge base root, derived from the `_summary.md` files rather than maintained by hand:

```markdown
| Date | Author | Title | Topic | Summary |
|------|--------|-------|-------|---------|
| 2026-03-18 | Last | Document Title | topic-folder | One-line summary of the document |
```

Each row comes from one summary's frontmatter, so the summaries are the source of truth and the table is the rendering. Regenerate a row from its summary rather than editing the row in place; a hand-edited row is the first thing to go stale, because nothing downstream knows it was changed. If you script the regeneration, the script owns the whole file; if you do not, have Claude rebuild the affected rows from the frontmatter it reads.

**Summary cell rule:** the Summary cell is one sentence that locates and disambiguates the document. It does not summarize it, because the `_summary.md` holds the detail. Target 30 words or fewer. A single dense sentence carrying distinguishing figures may run longer, but it stays one sentence and never becomes a paragraph.

## Topics File Format

`topics.md` describes each topic folder:

```markdown
# Knowledge Base Topics

## topic-folder
One- to two-sentence description of what this folder collects.
```

## Update Steps

### Step 1: Sync the index

Scan all topic folders for documents not in `index.md`. Do not descend into any subfolder named `materials/`; its contents are reference-only and must not appear in the index.

For each unindexed document found:
- If it has a `_summary.md`, read it and append an index entry
- If it has a source file but no `_summary.md`, note it as missing (do not generate; report it)
- Remove entries in `index.md` for files that no longer exist on disk

Update `topics.md` with current folder descriptions based on the contents of each folder. Existing descriptions are not overwritten if the folder's purpose has not changed; new folders get a draft description for the user to refine.

The refresh maintains decision tests, not just descriptions. If any filing was corrected since the last update, meaning a document was moved out of the folder it was first assigned, propose a one-line test that would have sent it to the right folder the first time. Where two topic descriptions would both plausibly claim a recent document, propose a test for that border. These are proposals; the user approves each `topics.md` edit.

### Step 1b: Clean up inbox build folder

Scan the inbox build folder (e.g., `<inbox>/<inbox>_build/`) for split directories (`split_*/`). For each split directory, check whether the corresponding source file still exists in the inbox. If the source file has already been moved out of the inbox (i.e., it no longer exists there), the splits are stale and can be deleted.

Present the list of stale split folders with their sizes, then delete them after confirmation. If the inbox build folder is empty after cleanup, remove it too.

### Step 2: Health check

Skip any path under a `materials/` subfolder. Report any issues found:

- **Missing summaries:** source files without a corresponding `_summary.md`. Flag a folder only when it actually holds a real source file or a non-empty source subfolder. A folder that is empty, holds only build artifacts, holds only a `materials/` subfolder, carries a `.kbskip` sentinel, or is already summarized is not a finding. Build output and a project state file such as `CLAUDE.local.md` are not sources. Without these guards the check reports the same false positives on every run, which is how a report stops being read.
- **Orphaned summaries:** `_summary.md` files without a corresponding source file
- **Naming inconsistencies:** files not matching the expected convention (the default is `YYYY-MM-DD Last. Title.ext`; adjust to whatever convention the `knowledge-base` skill uses on this system). Optional: if your knowledge base intentionally lets legacy and current naming conventions coexist permanently, turn this check off so it does not propose the same renames on every run. The same applies to empty or sparse topic folders kept as deliberate placeholders; do not flag them as defects.
- **Duplicate content:** files with very similar titles or content across different folders
- **Topic suggestions:** documents that might fit better in a different folder based on their summary content
- **Gaps:** topics with few sources where more research would strengthen the knowledge base

Offer to fix automatically where possible (e.g., move misplaced files, rename inconsistencies). Wait for user confirmation before making any moves or renames.

### Step 2b: Overflow re-homing review

Scoped to catch-all folders only, meaning the one or two topic folders that collect anything without an obvious home. The topic-suggestion check above already covers misfits everywhere else, so no other folder gets this sweep.

When a catch-all folder passes about 50 items, count by its `_summary.md` files across both storage patterns, read those items' frontmatter fields rather than the whole `index.md`, and propose specific re-homes into better-fitting topic folders. Approved re-homes run as normal move operations so the frontmatter, the index, and any search index stay in step. Below the threshold, skip this step silently rather than reporting that it did not run.

The threshold is a default, not a constant. It exists because a catch-all folder is fine while it is small and becomes a second unsorted inbox once it is large, and the review costs more than it returns until then.

## Constraints

- **Never delete original source files.** Rename and move only; never delete a source.
- **Never overwrite existing summaries.** If a summary already exists, skip unless the user explicitly asks to regenerate.
- **The summaries are the source of truth, not the index.** Add rows for new documents and remove rows for files that are gone, and take a row's content from its summary's frontmatter rather than editing the row directly. Do not silently change what a summary says in order to change how a row reads.
- **Topic folders are user-created.** Suggest new folders but wait for approval before creating them.
- **Read-only on `materials/`.** Never index, scan, or report on anything under a `materials/` subfolder.

## Customization

This skill assumes the `knowledge-base` skill's directory and naming conventions. If your conventions differ, edit:

- The knowledge base root path at the top of this file
- The directory pattern descriptions if you use a different layout (e.g., topics nested under categories)
- The naming convention used in the health check
- The list of "skip" folder names (`aa-inbox/`, `aa-blog/`, `aa-recents/`, and any search-index or documentation folder) if yours are named differently
