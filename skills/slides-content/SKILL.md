---
name: slides-content
description: Multi-step workflow to create presentation slides from content (academic papers, articles, notes). Reads the source (splitting PDFs, extracting text from Word/RTF, or reading markdown/text/LaTeX directly), summarizes the content, generates Beamer slides with figures and tables, then converts to PPTX using the style guide. Reuses any pre-existing text extract or summary in the output directory to avoid redundant work. Default deck opens Title, then Methodology, then Summary (a preview of conclusions) and includes Limitations and Conclusions slides near the end, each when appropriate. Optional `structure=` parameter (mba [default], teaching, faculty, professional, consulting, working) and `register=` parameter (business [default], technical) forward to the beamer skill to select the deck skeleton and language level; `audience=` is accepted as a deprecated alias for `structure=`. Triggers on "slide this", "slides from this", "create slides from this", "make a deck from this", "turn this into slides", "slides from this paper", "presentation from this article", and "build a deck".
when_to_use: Use when the user points at a source, a paper, an article, a report, a set of notes, a URL, or a local file, and wants slides made out of it, since this skill reads and summarizes that source before any deck is generated. Use beamer directly instead when there is no source to read, or when an existing generated deck is being edited, audited, or converted to PPTX.
allowed-tools: Bash(python*), Bash(pip*), Bash(curl*), Bash(wget*), Bash(mkdir*), Bash(ls*), Bash(pdflatex*), Bash(xelatex*), Bash(lualatex*), Bash(latexmk*), Bash(bibtex*), Bash(biber*), Bash(cd*), Bash(cp*), Bash(mv*), Bash(rm*), Bash(which*), Bash(type*), Bash(kpsewhich*), Bash(tlmgr*), Bash(texhash*), Bash(mactex*), Bash(mktexlsr*), Bash(fmtutil*), Bash(updmap*), Bash(brew*), Bash(find*), Bash(system_profiler*), Bash(fc-list*), Bash(sudo*), Bash(eval*), Bash(export*), Bash(cat*), Bash(grep*), Bash(head*), Bash(tail*), Bash(wc*), Bash(textutil*), Read, Write, Edit, WebSearch, WebFetch, Glob, Grep, Task
argument-hint: [optional: file-path, url, or leave blank to pick from menu] [structure=mba|teaching|faculty|professional|consulting|working] [register=business|technical]
---

# Slides from Content: Four-Step Workflow

Create a polished presentation deck from source content (academic paper, article, notes, or other material). This is a sequential four-step process. Complete each step fully before proceeding to the next. **Do not pause for confirmation between steps.** Move automatically from one step to the next once the current step is complete.

## Prerequisites: Content Selection

**If the user provided a file path, URL, or pasted content as an argument**, use it directly; skip the menu and proceed to the Working Directory section.

**If no content was provided**, present this menu exactly as written:

> What content would you like me to build slides from? Please provide one of:
> - **Single file in this folder** (default): I'll use the only supported file here
> - **Choose a file in this folder**: I'll list the supported files and you pick
> - **A file path** to a local file (PDF, markdown, Word, text, LaTeX, RTF)
> - **A URL** to an article or paper
> - **Pasted text or notes**
> - **Something else**

Supported file types: `.pdf`, `.md`, `.txt`, `.docx`, `.doc`, `.rtf`, `.tex`

Then wait for the user's response and handle it as follows:

### "Single file in this folder" (or no response / pressing Enter)

List all supported files (`.pdf`, `.md`, `.txt`, `.docx`, `.doc`, `.rtf`, `.tex`) in the current working directory (not recursively). Then:
- **Exactly one supported file found** → proceed using that file without confirmation
- **Multiple supported files found** → fall through to "Choose a file in this folder" behavior: list them and ask the user to pick
- **No supported files found** → tell the user no supported files were found in the current directory and ask them to provide a file path or URL

### "Choose a file in this folder"

List supported files in the current working directory, numbered, up to a maximum of **8**. If more than 8 exist, show the first 8 and add a note: "*(and N more; provide a file path to use one not listed)*". Ask the user to pick one by number or name. Use the selected file.

### "A file path"

Ask the user to provide the path. Use the provided path.

### "A URL"

Ask the user to provide the URL. Fetch the content via WebFetch and use it.

### "Pasted text or notes"

Ask the user to paste the content. Use the pasted text.

### "Something else"

Ask the user to describe what they have. Adapt appropriately.

## Working Directory

**Directory structure rule:** Two tiers: an **output directory** for the source file and deliverables, and a **build subdirectory** for all working files.

### Determine `<content_name>`

`<content_name>` is the name used to prefix all deliverables and the build directory. It is determined as follows:

1. **If the user provides a name**, use exactly what the user provides.
2. **Otherwise**, use the source filename without its extension, exactly as it appears on disk. Never abbreviate, shorten, or paraphrase.

Examples:
- `smith_2024.pdf` → `<content_name>` = `smith_2024`
- `notes.md` → `<content_name>` = `notes`
- `A large-scale investigation of everyday moral dilemmas. 2025-05-13.pdf` → `<content_name>` = `A large-scale investigation of everyday moral dilemmas. 2025-05-13`
- User says "call it moral_dilemmas" → `<content_name>` = `moral_dilemmas`

All deliverables use `<content_name>` as their prefix: `<content_name>_summary.md`, `<content_name>_slides.pdf`, `<content_name>.pptx`. The build directory is `<content_name>_build/` (named after the document, sitting inside the per-document output directory).

### Determine the output directory

The output directory is a **per-document subfolder** named `<content_name>/` inside the folder containing the source file. This ensures each document's source, deliverables, and build artifacts are self-contained.

**KB source promotion (Pattern B to Pattern A):** When the source file lives flat in a knowledge base topic folder (Pattern B: source, `_text.md`, and `_summary.md` sitting directly in the topic folder), promote to Pattern A before generating slides. Create `<content_name>/` inside the topic folder and move the source file, `_text.md`, and `_summary.md` into it. This becomes the output directory. The `_build` folder then goes inside this subfolder as `<content_name>_build/`.

**Non-KB sources:** When the source file is not in a KB topic folder, the output directory is the folder containing the source file. If the source is already inside a per-document subfolder, use that folder as-is.

### Final structure

```
<parent_folder>/                               # topic folder (KB) or any parent directory
└── <content_name>/                            # output directory: source + deliverables
    ├── <content_name>.<ext>                   # original source file (pdf, md, txt, docx, etc.)
    ├── <content_name>_summary.md              # structured summary
    ├── <content_name>_text.md                 # full-text extraction (PDF sources)
    ├── <content_name>_slides.pdf              # compiled Beamer PDF
    ├── <content_name>.pptx                    # PowerPoint (if generated)
    └── <content_name>_build/                  # build subdirectory
        ├── split_<content_name>/              # split chunks from split-pdf
        │   ├── <content_name>_pp1-4.pdf
        │   ├── <content_name>_pp5-8.pdf
        │   └── ...
        ├── figures/                           # extracted source figures (if any)
        │   ├── fig1_name.png
        │   └── originals/                    # full-page PDF renders at 300 DPI
        ├── notes.md                           # deep-reading extraction notes
        ├── slides.tex                         # Beamer source
        └── [any other working files]          # .aux, .log, .nav, images, scripts, etc.
```

**This is mandatory.**
- **`<content_name>` = the user-provided name, or the source filename without its extension if no name is given.** Never abbreviate or paraphrase the filename.
- The output directory is a per-document subfolder `<content_name>/`. Deliverables and source sit together inside it.
- Deliverables (`<content_name>_summary.md`, `<content_name>_slides.pdf`, `<content_name>.pptx`) go in the output directory alongside the source file.
- **All** working files (notes, .tex, splits, .aux, .log) go in `<content_name>_build/` inside the output directory. The build folder is named after the document, not the parent folder.
- After compilation, the beamer skill auto-places `<build_base>_slides.pdf` in the parent folder (where `<build_base>` is the build directory name minus `_build`). Since `<content_name>_build/` is inside `<content_name>/`, the auto-placed PDF lands in the output directory with the correct name.

---

## Step 1: Read the Source Content

**Skip this step entirely if the input is pasted text, notes, or a web article via URL.** Proceed directly to Step 2 with the raw content.

### If the input is a PDF

**Pre-flight: reuse existing text extract if one is already present.**

Before splitting, check whether `<content_name>_text.md` exists in the output directory. If it does, the deep-read has already been done (typically by a prior knowledge-base pipeline run, or by an earlier slide build). Skip splitting and the deep-read agent entirely:

1. Create the build directory (`<content_name>_build/`) if it does not already exist.
2. Copy `<output_dir>/<content_name>_text.md` to `<content_name>_build/notes.md`. The beamer skill reads `notes.md` from the build directory; the copy makes the existing extract available under the expected name.
3. Report:
   > Reusing existing text extract at `<output_dir>/<content_name>_text.md` (last modified: YYYY-MM-DD). Skipping PDF splitting and deep-read. Delete the file and re-run if you want a fresh extraction.
4. Proceed immediately to Step 2.

This is the default behavior; do not ask whether to reuse. The deep-read agent is the single most expensive step in this skill (large agent token cost); skipping it when the extract already exists is a substantial saving. The Step 2 reuse-summary pre-flight follows the same pattern.

If `<content_name>_text.md` does not exist, continue with the splitting logic below.

First check for existing splits before splitting. Look for `<content_name>_build/split_<content_name>/` in the output directory. If it exists and contains `.pdf` files, ask:
> "Splits already exist for `<content_name>` (N chunks). Reuse existing splits, or re-split from scratch?"
- **Reuse**: skip splitting, use the existing files, and proceed to deep-read below
- **Re-split**: delete the split folder and proceed with splitting below

Split the PDF into 4-page chunks using split-pdf's Python splitting script. Store splits in `<content_name>_build/split_<content_name>/`.

See `../split-pdf/SKILL.md` for the full splitting procedure and Agent Isolation Protocol.

**Read the splits in a subagent** per split-pdf's Agent Isolation Protocol. Launch an Agent to read all splits (3 at a time) and write `notes.md` in the build subdirectory. The agent prompt should specify:
- The split directory path and ordered file list
- Notes output path: `<content_name>_build/notes.md`
- Extraction dimensions: research question, audience, method, data (sources, sample, period), statistical methods, findings, contributions, replication feasibility
- No pause between batches

After the agent completes, read `notes.md` (plain text) in the parent conversation and continue to Step 2.

**CRITICAL:** Never read PDF files in the parent conversation. All PDF reads happen inside the subagent.

### If the input is not a PDF (.md, .txt, .tex, .docx, .doc, .rtf)

Skip splitting. Create the build directory (`<content_name>_build/`) if it does not already exist, then read the file directly:
- For `.md`, `.txt`, and `.tex`: read the file contents using the Read tool
- For `.docx`, `.doc`, `.rtf`: extract text using macOS built-in `textutil -convert txt "<file_path>" -output "<build_dir>/extracted.txt"`, then read the extracted text file. Note that `textutil` extracts text only; embedded charts, images, and shapes in the Word or RTF source are not captured and will not appear in the generated deck. If the source has substantive visual content that matters for the deck, supply a PDF version of the document instead.

Save extracted content to `notes.md` in the build subdirectory, using the same structured format as the PDF deep-read (research question, audience, method, findings, etc., where applicable).

### Proceed

When notes are complete, proceed immediately to Step 2.

---

## Step 2: Summarize the Content

**Pre-flight: reuse existing summary if one is already present.**

Before running the summary step, check whether `<content_name>_summary.md` already exists in the output directory. If it does, reuse it without regeneration and report:

> Reusing existing summary at `<output_dir>/<content_name>_summary.md` (last modified: YYYY-MM-DD). Skipping summary regeneration. Delete the file and re-run if you want a fresh summary.

Then skip the rest of Step 2 and proceed to Step 3. This is the default behavior; do not ask whether to reuse. This matters when the user has already processed the source through a knowledge-base or summarization pipeline that produced a `_summary.md` equivalent to what this step would generate.

If `<content_name>_summary.md` does not exist, continue with the MANDATORY FIRST ACTIONS below.

**MANDATORY FIRST ACTIONS (before writing any summary content):**
1. Auto-detect content type based on the source material or `notes.md`:
   - **Academic** (has methods section, literature review, formal citations, peer review, formal methodology) → read `../summary-academic/SKILL.md` in full
   - **General** (news, blog, opinion, report, interview, informal writing) → read `../summary-general/SKILL.md` in full
   - **Ambiguous** → default to academic
2. Do not write any summary content before completing the read. The skill file defines the exact output format, section headings, and style requirements that must be followed precisely.

If Step 1 produced `notes.md`, use those notes as the basis for the summary. If Step 1 was skipped, summarize directly from the provided content.

### If Academic Paper

Apply the **academic summary skill** (`../summary-academic/SKILL.md`). Academic content includes: peer-reviewed journal articles, conference proceedings, working papers, preprints, dissertations, and technical reports with formal methodology sections.

Produce the full structured summary (citation, thesis, key points, conclusions, population, implications, concepts, issues, summary paragraph) following all style requirements from that skill.

### If General Content

Apply the **general summary skill** (`../summary-general/SKILL.md`). General content includes: news articles, blog posts, opinion pieces, reports, interviews, podcasts, videos, and informal writing.

Produce the full structured summary (citation, thesis, themes, issues if applicable, summary paragraph) following all style requirements from that skill.

### If Unclear

Default to the **academic summary skill** for anything with a methods section, literature review, or formal citations. Otherwise use the **general summary skill**. If genuinely ambiguous, ask the user.

Save the summary output to `<content_name>_summary.md` in the output directory (not the build subdirectory, since the summary is a deliverable).

Proceed immediately to Step 3. This skill's purpose is to generate slides; no confirmation is needed after the summary step.

---

## Step 3: Generate Beamer Slides

**MANDATORY FIRST ACTIONS (before writing any `.tex` content):**
1. Read `../beamer/SKILL.md` in full using the Read tool
2. Read the Beamer style guide (referenced in `../beamer/SKILL.md`) in full using the Read tool

Do not proceed without completing both reads. The style guide contains the exact LaTeX preamble to copy verbatim; generating slides without reading it produces output that violates the design spec.

Apply the **beamer skill** (`../beamer/SKILL.md`) using the deep-reading notes (`notes.md` from the build subdirectory) and the summary (`<content_name>_summary.md` from the output subdirectory) as input. All compilation work happens in the build subdirectory.

**Structure and register forwarding:** if this skill was invoked with a `structure=` parameter (for example, `structure=consulting`) and/or a `register=` parameter (`register=technical`), pass them through to the beamer skill so its Step 0.5 Structure and Register Triage runs with them. A legacy `audience=` parameter is forwarded unchanged; the beamer skill treats it as the deprecated alias for `structure=`. If neither is passed, do not invent one; the beamer skill's default structure (`mba`) with the default `business` register applies (Title, then Methodology, then Summary preview, then findings, then Limitations, Conclusions, Key Takeaways, and Closing; Methodology, Summary, Limitations, and Conclusions each appear when appropriate).

The beamer skill handles the full Beamer generation cycle:
- Original aesthetic design targeted at a professional or graduate student audience
- Content covering all key themes from the source material
- Visual figures (TikZ), tables, and data visualizations
- Four-step compilation cycle:
  1. Write and compile (two-pass pdflatex minimum)
  2. Fix all overfull/underfull/vbox/hbox warnings
  3. Quality audit (merged): single agent reads style guide, audit checklist, PDF, and .tex source; checks deck evaluation, graphics, and full checklist in one pass; auto-fixes all reported issues and reports what changed
  4. Fix confirmed issues and recompile

Output: `slides.tex` and all LaTeX artifacts in the build subdirectory. The beamer skill auto-places the deliverable PDF in the parent folder. If the auto-placed name differs from `<content_name>_slides.pdf`, rename it.

**Pause here and ask the user:** "Beamer slides for *[title of the content]* compiled and verified. Would you like me to convert to PowerPoint (.pptx)?"

Use the actual title of the paper, article, or content being processed. Wait for the user to confirm before proceeding to Step 4. If the user declines, stop here. This is the deck's single PPTX offer: do not re-raise PowerPoint in later turns or session logs. An unconverted deck is complete; if the user wants PPTX later, they ask for it.

---

## Step 4: Convert to PPTX

**MANDATORY FIRST ACTION (PPTX style selection):**
Before writing any PPTX code:
1. Read `../../style-guides/pptx/style-guide.md` in full
2. The style guide contains the template path, content area constants, color palette, font-fix functions, and the pre-save quality check, all of which must be applied exactly as specified

Do not write any python-pptx code before completing this read.

Follow the Beamer-to-PPTX Conversion Workflow in the PPTX style guide to recreate the Beamer slide content as native PowerPoint objects. This requires:

1. Per-slide element categorization (native chart, native table, native shapes, hybrid, or image embed as last resort)
2. Conversion plan presented to the user for approval before any code is written
3. Native-first object creation (charts via `add_chart()` + font-fix functions, shapes via `add_shape()`, tables via `add_table()` + font-fix functions)
4. Apply all specifications from the style guide exactly: template, typography, layout constants, color palette
5. Run `run_quality_check(prs)` before `prs.save()` and fix all reported issues

### Output

Save the final file as `<content_name>.pptx` in the output subdirectory (alongside `<content_name>_summary.md` and `<content_name>_slides.pdf`).

Report to the user:
> "Deck complete. Files saved to [output subdirectory]:
> - `<content_name>_summary.md`: structured summary
> - `<content_name>_slides.pdf`: compiled Beamer PDF
> - `<content_name>.pptx`: PowerPoint deck (styled per your guide)
>
> Build files (notes.md, slides.tex, splits, LaTeX artifacts) are in `[name]_build/`.
>
> Would you like me to adjust anything?"

---

## Quick Reference

| Step | Action | Skill Used | Output Location |
|------|--------|------------|-----------------|
| **1. Read Source** | Split PDF and deep-read in batches; or read non-PDF files directly | `../split-pdf/SKILL.md` (PDF only) | `_build/notes.md`, `_build/split_*/` (PDF) |
| **2. Summarize** | Academic or general summary | `../summary-academic/SKILL.md` or `../summary-general/SKILL.md` | `<content_name>_summary.md` (output dir) |
| **3. Beamer Slides** | Design, compile, evaluate, verify graphics | `../beamer/SKILL.md` | `_build/slides.tex` → `<content_name>_slides.pdf` (auto-placed by beamer skill; renamed if needed) |
| **4. Convert to PPTX** | Apply PowerPoint style guide | `../../style-guides/pptx/style-guide.md` | `<content_name>.pptx` (output dir) |

---

## Session Log

After delivering the final output (slides PDF and optional PPTX), append a session log entry to `CLAUDE.local.md` in the project root (the parent of the build directory). If `CLAUDE.local.md` does not exist, create it with a header first.

**Entry contents:**
```markdown
## [YYYY-MM-DD] - Slides from content: [source name]
- **Skill:** slides-content
- **Source:** [file path or URL]
- **Files created:** [summary path, slides PDF path, PPTX if generated]
- **Key decisions:** [slide count, summary type used, notable design choices]
- **Status:** complete
- **Next steps:** [none, or note if user mentioned future edits]
```

**Handoff trigger:** If this session involved troubleshooting or multiple rounds of revision, ask:

> "This session involved multiple rounds of revision. Write a handoff for the next session?"

If the session was a clean single-pass run, do not ask. Just log the entry silently.
