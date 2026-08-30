### 2. Q&A (`/kb ask [question]` or "kb ask")

**Where this file's cross-references resolve.** This file is Mode 2 of the knowledge-base skill; `SKILL.md` is read first and stays loaded alongside it. "The frontmatter block" below resolves to the `## The frontmatter block` section of `SKILL.md`, not to `references/inbox.md`. The helper commands (`kb-search`) are defined under `## Helper commands` there. Do not open any other mode file.

Answer questions grounded in the indexed knowledge base.

#### Step 1: Consult the index first (mandatory)

Per the index-first gate in `SKILL.md`, start here before any folder scan. Read `topics.md` to narrow which topic folders matter, run `kb-search search <terms>` to surface full-text hits (**without the script, the `grep -ril` fallback in Mode 4**, which returns unranked exact matches), and `grep index.md` for the question's key terms (title words, author surnames, concepts) to catch catalogued items the full-text index misses. Never read `index.md` whole into context. Only then proceed to Step 2.

#### Step 2: Identify relevant sources

Based on the question, select the 5-15 most relevant documents. Read their `_summary.md` files.

Also scan `materials/` subfolders across topic folders for `.md` files whose names or topic context look relevant to the question. Read any that match. Skip binary files under `materials/` (PDF, images, Office documents), since reference-material Q&A is markdown-only. When citing content from `materials/`, label it as reference material rather than an indexed entry, since it is not in `index.md`.

#### Step 3: Synthesize answer

Write a grounded answer that:
- Cites sources by author and date (Chicago Author-Date)
- Distinguishes between what sources say and inference or synthesis
- Distinguishes between the user's own published positions (`[blog]` entries) and external sources when both are relevant
- Notes gaps (aspects of the question not covered by any indexed source)
- Flags contradictions between sources
- Flags sources whose `source_basis` is not full-text, citing them as excerpt-built or partial reconstructions, never as the publication itself; and flags a source carrying `capture_caveat:` by quoting that sentence with the citation, since a caveat is recorded doubt about completeness that nothing downstream stops on

#### Step 4: Optionally save the answer

Offer to save the answer as a `.md` file in the knowledge base:

> "Save this answer to the knowledge base? It will be saved for future reference and browsable in the file tree, but it is not indexed or searchable (it will not appear in `index.md` or `kb search`)."

If accepted, save as `YYYY-MM-DD Query. [Short description]_notes.md` as its own artifact in a per-document subfolder of the most relevant topic folder (matching the Pattern A convention), beginning with the frontmatter block with `type: qa-answer` and `level: lite`, `topic:` set to the destination folder, and `tags:` defaulted to `[<topic>]`. `qa-answer` is a value of the `type:` enum in `SKILL.md`'s frontmatter block, reserved for this artifact. This is a `_notes.md` artifact, not a `_summary.md`: it is not walked by the index generator or the full-text reindexer, so it never gets an `index.md` row, is not `kb search`-able, and never appears as a `--type` filter value.
