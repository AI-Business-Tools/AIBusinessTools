### 3. Move Project (`kb move <source_dir> <topic>`)

**Where this file's cross-references resolve.** This file is Mode 3 of the knowledge-base skill; `SKILL.md` is read first and stays loaded alongside it. "The same rules as Mode 1 Step 2" below resolves to the `## Citation metadata and naming` section of `SKILL.md`; "the frontmatter block" resolves to the `## The frontmatter block` section of `SKILL.md`; "the one-sentence rule in Index Format" resolves to `SKILL.md`'s `## Index Format`. The helper commands (`kb-index`, `kb-dup-check`, `kb-recents`, `kb-search`) are defined under `## Helper commands` there. Do not open `references/inbox.md`.

Move all artifacts from a source directory into a topic folder. Use this when a content skill (a slides skill, a summary skill, and so on) has already processed a document outside the knowledge base, and the output needs to be filed.

**Triggers:** `kb move`, `move to [topic]`, `file this in [topic]`, or any request to move pipeline output into a topic folder.

**Not a valid destination:** `materials/` subfolders. Pipeline output must not be filed into `materials/`. If the user asks to `kb move` into a path under `materials/`, decline and ask for a real topic folder instead. `materials/` is for hand-placed reference items only.

#### Step 1: Inventory the source directory

List all files in the source directory. Classify each file against the artifact pattern list:

| Pattern | Examples | What it is |
|---------|----------|------------|
| Source file | `.pdf`, `.md`, `.docx`, `.html`, `.tex`, `.rtf` | Original document |
| `*_summary.md` | `paper_summary.md` | Structured summary |
| `*_text.md` | `paper_text.md` | Full-text extraction |
| `*_slides.pptx`, `*.pptx` | `paper_slides.pptx`, `paper.pptx` | Editable deck, the deliverable |
| `*_slides.pdf` | `paper_slides.pdf` | Beamer slide output, or a review render |
| `*_build/` | `Downloads_build/` | Build artifacts (LaTeX intermediates, splits, notes) |
| `*-analysis.md` | `paper-analysis.md` | Companion analysis |
| `*_notes.md` | `paper_notes.md` | Reading notes (split-pdf output) |

Ignore `.DS_Store` and other OS metadata files.

Present the inventory:

> **Source directory:** `/path/to/source/`
>
> | # | File | Pattern | Action |
> |---|------|---------|--------|
> | 1 | `paper.pdf` | source | rename + move |
> | 2 | `paper_summary.md` | summary | rename + move |
> | 3 | `paper_slides.pdf` | slides | rename + move |
> | 4 | `Downloads_build/` | build | move as subfolder |
>
> **Target:** `knowledge-base/relationships/`
> **Storage pattern:** A (per-document subfolder)
>
> Proceed?

Wait for confirmation before moving.

#### Step 2: Storage pattern (always Pattern A)

All `kb move` output goes into a per-document subfolder: `<topic>/<date> <Author>. <Title>/` containing every artifact (source, `_summary.md`, `_text.md`, any slides, build folder). Pattern B (flat) is legacy only and is never produced by new filing.

#### Step 3: Rename artifacts

Apply the naming convention (`YYYY-MM-DD Last. Title`) to all artifacts:

- Source file: `YYYY-MM-DD Last. Title.ext`
- Summary: `YYYY-MM-DD Last. Title_summary.md`
- Text: `YYYY-MM-DD Last. Title_text.md`
- Deck: `YYYY-MM-DD Last. Title_slides.pptx` (a bare `.pptx` is filed under this name too, so both engines land on one form)
- Slides: `YYYY-MM-DD Last. Title_slides.pdf`
- Analysis: `YYYY-MM-DD Last. Title-analysis.md`
- Notes: `YYYY-MM-DD Last. Title_notes.md`
- Build folder: `YYYY-MM-DD Last. Title_build/` (or `<topic>_build/` for a legacy Pattern B item)

If a `_summary.md` exists, extract citation metadata from it. Otherwise, extract from the source file using the same rules as Mode 1 Step 2.

If the source file is already in citation format, preserve its name and derive artifact names from it.

Once the renamed stem is settled, run the duplicate check before moving anything: `kb-dup-check "<renamed stem>" [--url <url from the _summary.md frontmatter>]`. On `DUP` or `NEAR`, report the match and wait for the user's direction (move anyway, or stop); on `ERROR`, say the check could not complete and ask whether to proceed.

**Without the script, run the targeted lookup instead:** `grep -i -F "<renamed stem>" index.md`, plus `grep -i -F "<url>" index.md` when the frontmatter carries one. A hit is a `DUP` (show the matched row), no hit is an `OK`, and a grep that cannot run, because `index.md` is missing or unreadable, is an `ERROR`. `NEAR` has no fallback and needs the script. **Never eyeball-compare against a whole-file `index.md` read.** That prohibition is about reading the index into context and judging by eye; a `grep` for one stem reads back one line and is the sanctioned substitute.

#### Step 4: Move all artifacts

Use `mv` (not `cp`) for every file. After moving:

1. **Verify** all files arrived at the destination (ls the target).
2. **Check** the source directory is empty (ignoring `.DS_Store`).
3. **Report** what was moved and what remains.

If the source directory is empty after the move, offer to remove it. If files remain, list them explicitly.

#### Step 5: Update index, recents, and search (Mode 3)

- Ensure the moved `_summary.md` carries the frontmatter block, adding it if the source predates frontmatter (deriving `index_line` per the one-sentence rule in Index Format), with `topic:` set to the destination folder and `tags:` defaulted to `[<topic>]`. Then run `kb-index`; without the script, regenerate the whole table from every summary's frontmatter, never by appending one row (`SKILL.md`, Helper commands).
- Rebuild `aa-recents/` by running `kb-recents` (same script as Mode 1); without the script, skip the rebuild and say so once. It is a browse view and nothing else reads it.
- Refresh the full-text database so the moved item is findable via `kb search` and future `kb ask`:
  ```bash
  kb-search reindex --incremental
  ```
  Best-effort; do not block the move report on a reindex failure.
