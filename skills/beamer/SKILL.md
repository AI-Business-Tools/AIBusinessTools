---
name: beamer
description: Beamer slide generation with citation strategy decision, code-first matplotlib figures, outline checkpoint with content inventory, structure-aware rhetoric, Devil's Advocate slides, code blocks, and transition slides. Two optional axes tune the deck: `structure=` (mba [default], teaching, faculty, professional, consulting, working) selects the slide skeleton and rhetoric balance; `register=` (business [default], technical) selects the language level, where business translates or glosses the source's domain jargon for a non-specialist reader and technical keeps the source vocabulary intact. `audience=` is a deprecated alias for `structure=`. Quality audit runs as a single agent on a strong model. Beyond generate mode, it supports edit, audit, and convert-to-PPTX modes for working on a previously generated deck, including a version snapshot of each delivered edit round and an optional PDF-vs-PPTX conversion audit. Edit mode auto-activates when the working directory contains a `*_build/slides.tex`. Adapted from Scott Cunningham's beautiful_deck approach. Triggers on "beamer", "beamer slides", "deck", "edit beamer", "revise beamer", "fix beamer slides", "audit beamer", and "convert beamer to pptx".
when_to_use: Use when the user asks for Beamer slides or a LaTeX deck built from notes or a summary already in hand, and when they ask to edit, revise, fix, audit, or convert to PPTX a deck this skill generated earlier. Edit mode is the right choice whenever the working directory already holds a *_build/slides.tex, so slide changes in a finished project folder come here rather than being made by hand. Use slides-content instead when the request starts from a source document, such as a paper, an article, or a set of notes, that has to be read and summarized first.
allowed-tools: Bash(pdflatex*), Bash(xelatex*), Bash(lualatex*), Bash(latexmk*), Bash(bibtex*), Bash(biber*), Bash(python*), Bash(pip*), Bash(pdftoppm*), Bash(cd*), Bash(mkdir*), Bash(ls*), Bash(cp*), Bash(mv*), Bash(rm*), Bash(which*), Bash(type*), Bash(kpsewhich*), Bash(tlmgr*), Bash(texhash*), Bash(mactex*), Bash(mktexlsr*), Bash(fmtutil*), Bash(updmap*), Bash(brew*), Bash(find*), Bash(system_profiler*), Bash(fc-list*), Bash(eval*), Bash(export*), Bash(cat*), Bash(grep*), Bash(head*), Bash(tail*), Bash(wc*), Read, Write, Edit, Glob, Grep, Agent
argument-hint: [content-notes-or-summary] [structure=mba|teaching|faculty|professional|consulting|working] [register=business|technical]
---

# Beamer Slide Generator

Generate an original Beamer presentation from source content (structured notes, summaries, or raw material). This skill handles the full cycle: structure and register triage, outline checkpoint, code-first figure generation, design, authoring the `.tex` file, compilation, and verification through multi-agent review.

Six additions from Scott Cunningham's beautiful_deck approach are integrated: code-first figures (matplotlib), an outline checkpoint, structure-aware rhetoric, Devil's Advocate slides, code blocks, and transition slides.

Beyond generating a new deck, the skill also works on an existing one through three additional modes (edit, audit, and convert-to-PPTX); see Mode Selection below. Edit mode auto-activates when the current working directory already contains a `*_build/slides.tex`.

## Input

This skill expects one or more of:
- A `notes.md` file with structured extraction from a deep reading (for example, from `../split-pdf/SKILL.md`)
- A `summary.md` file with a structured summary
- Raw content, pasted text, or other source material

Two optional parameters tune the deck. `structure=` selects a domain pattern from `domain_patterns.md`: mba (the default), teaching, faculty, professional, consulting, or working. `register=` selects the language level: business (the default) translates or glosses the source's domain jargon for a non-specialist reader; technical keeps the source vocabulary intact. The legacy `audience=` parameter is accepted as a deprecated alias for `structure=` with the same value set.

If invoked standalone, ask the user what content to build slides from. If invoked as part of a slides workflow, notes and summary files will already exist in the working subdirectory.

## Working Directory

Save all output files in the current working subdirectory. If no subdirectory has been established, create one named after the source material (for example, `slides_smith_2024/`).

If figures are extracted from the source PDF, save them to `figures/` inside the working subdirectory, with original full-page renders in `figures/originals/`.

---

## Mode Selection

Default mode: **generate** (build a new deck from source content). This skill also supports three additional modes for working with an existing deck. Generate-mode behavior is unchanged whether or not callers pass a `mode=` argument.

**Edit mode** activates when ANY of the following is true:
- The invocation includes `mode=edit`.
- The user invoked via an edit, revise, or fix trigger ("edit beamer", "revise beamer", "fix beamer slides", "update beamer deck").
- The current working directory contains a `*_build/slides.tex` and no `mode=generate` was passed.

**Audit mode** (`mode=audit`, or an audit trigger) re-runs the Quality Audit pass against an existing compiled deck. No content edits beyond audit-fix remediation. Use when revisiting a deck after a long pause, or to confirm a previously generated deck still passes the checklist.

**PPTX mode** (`mode=pptx`, or a "convert to pptx" trigger) runs only the PPTX conversion block against an existing compiled deck. No audit, no edits.

| Mode | When it runs | What it does |
|---|---|---|
| `generate` | Default; new content provided | Full pipeline (Step 0 to Output). Unchanged from prior behavior. |
| `edit` | Edit trigger, `mode=edit`, or CWD auto-detect | Locate existing deck, load context, present menu, apply edits, run Compilation Cycle, iteration prompt |
| `audit` | `mode=audit` or audit trigger | Locate existing deck, load PDF and .tex, run Compilation Cycle Step 3 (Quality Audit) then Step 4 (Fix), report |
| `pptx` | `mode=pptx` or "convert to pptx" trigger | Locate existing deck, run the Output PPTX conversion block |

**In any non-generate mode:** skip everything from Step 0.1 through Figure Extraction (Step 0.1 Pre-flight Deliverable Check, Step 0.5 Structure and Register Triage, Step 0.6 Citation Strategy, Step 0.7 Outline Checkpoint, Step 0.8 Code-First Figure Generation, Design Requirements, Content Requirements, Visual Mechanism Selection, Number Formatting, Acronyms and Abbreviations, Quality Standards, Figure Extraction). All of these are generate-time prep that does not apply to a previously generated deck. Jump from Step 0 (LaTeX verification) directly into the **Edit Mode** section below for the locate and load-context steps, then dispatch per the chosen mode. The Edit Mode E2 step is the entry-point backup counterpart to Step 0.1; running both would produce duplicate timestamped backups.

**In generate mode:** proceed with every step as usual. There is no behavior change for workflows that call this skill in generate mode.

**`structure=` and `register=` in non-generate modes:** both parameters only take effect in generate mode (via Step 0.5 Structure and Register Triage). In edit, audit, or pptx mode, both are silently ignored; the deck's structure and register were set at generate time and are not reconfigurable mid-flight. To use a different structure, regenerate the deck from scratch with `mode=generate`. (`audience=` is the deprecated alias for `structure=` and is ignored here too.)

**Auto-detection ambiguity:** if the CWD contains multiple `*_build/slides.tex` subdirectories, auto-detection still fires (edit mode is chosen), and Step E1 below prompts the user to pick which deck.

**Trigger vs CWD-auto-detect precedence:** if the user invokes via an explicit generate trigger ("create beamer slides", "generate beamer deck", "make latex slides", "beamer presentation from this") AND new source content is provided in the same turn, run generate mode even if the CWD contains a `*_build/slides.tex`. Auto-detect only fires when the invocation is ambiguous (no explicit trigger family, or no source content). Rationale: a user who explicitly asks to create new slides in a directory that happens to already contain a deck is starting a second deck, not editing the first.

---

## Edit Mode

This section runs when the skill is invoked in `edit`, `audit`, or `pptx` mode (per Mode Selection above). It performs the locate-and-load steps, presents the menu when in edit mode, and dispatches into the relevant Compilation Cycle and Output blocks. **Skip this entire section in generate mode.**

### E1: Locate the Output and Build Subdirectories

The base directory is **the current working directory** at the time the skill is invoked.

**If the user specifies a file or folder name:**
- If the user provides a source file name (for example, `smith_2024.pdf`), look for the matching output subdirectory (for example, `smith_2024/`) and its build subdirectory (for example, `smith_2024/smith_2024_build/`).
- If the user provides a subdirectory name directly (for example, `smith_2024`), use that as the output subdirectory and look for `<name>_build/` inside it.

**If no name is provided:** list the subdirectories in the current working directory that contain a `*_build/slides.tex` file. If exactly one is found, use it. If multiple are found, present the list and ask the user to pick. If none are found, report the error and stop.

**Validation:** confirm that `slides.tex` exists in the build subdirectory. If it does not, report the error and stop.

### E2: Pre-flight Deliverable Check (entry-point version snapshot)

Before loading context or applying any edits, preserve the deck being edited as a version snapshot. This start-of-round capture fires here at entry and again at each E8 loop-back (once per edit round).

1. **Version-snapshot the deck.** The deck about to be edited is the current compiled deck `<build>/slides.pdf`, paired with its source `<build>/slides.tex`. If it exists, preserve it as the next milestone:
   - Glob existing `<content_name>_slides v*.pdf` in the **output subdirectory**. Next N = highest existing `vNN` + 1, zero-padded to two digits; if none exist, N = `01`. Generation writes no `vNN`, so the first edit creates `v01`, the backup of the generated deck.
   - Snapshot suffix:
     - **`v01` (no prior `vNN`):** the deck being preserved is the generated baseline. Suffix = `v01 structure-<x> register-<y>`, where `<x>`/`<y>` are the structure and register the deck was generated with, read from the deck's generate-time entry in the project session log (`CLAUDE.local.md` if you keep one). If no record exists, use `structure-mba register-business` and say so in the report.
     - **`v02`+:** suffix = `v0N <label>`, a 1-3 word descriptor of the change that defined the version being preserved. For an in-conversation E8 loop-back, derive the label from the edits just applied in that round.
   - Copy the PDF: `cp "<build>/slides.pdf" "<output>/<content_name>_slides <suffix>.pdf"`. (Fallback: if `<build>/slides.pdf` is absent but the output deliverable exists, copy `<output>/<content_name>_slides.pdf`.)
   - Copy its source, paired: `cp "<build>/slides.tex" "<build>/slides <suffix>.tex"`, so the version recompiles and diffs, not only views. The `.tex` must be taken now, before this round's edits overwrite it in place.
2. **Version-snapshot the PPTX** (if present), per Output's "PPTX version snapshots (`vNN`)": if `<content_name>.pptx` exists and is not already byte-identical to the newest `<content_name> v*.pptx` (`cmp -s`), snapshot it as the next `vNN`. If it is already preserved as the latest `vNN`, do nothing.

Report: "Snapshotted the deck being edited as `<content_name>_slides <suffix>.pdf` (+ source `slides <suffix>.tex`)."

One snapshot per edit **round** (one batch of changes the user reviews): here at entry, and again at each E8 loop-back. Intra-round audit-fix recompiles do not snapshot. This is the safety net: every delivered version is preserved before the next round overwrites it.

Convention recap: `<content_name>_slides.pdf` is always the latest; the `vNN` files are the preserved version history beneath it, each paired with its `slides vNN ....tex` source in `_build/`. `v01` is the backup of the generated deck (made at the first edit), tagged with the deck's structure and register; later versions carry change-labels. After N edit rounds there are N `vNN` files; a count short of the rounds applied means a snapshot was skipped.

If no deck exists yet (no `<build>/slides.pdf` and no deliverable), proceed silently.

### E3: Load Context

Read the following files (silently skip any that do not exist):

From the **build subdirectory** (`<name>_build/`):
1. **`notes.md`**: deep-reading extraction notes
2. **`slides.tex`**: the current Beamer source
3. **`figures/`**: if this directory exists, note it silently. The existing figures are available for reference in the `.tex` source; do not move or rename them. If the user's edits require adding new figures from the source PDF, follow the Figure Extraction protocol later in this skill (pdftoppm at 300 DPI, PIL crop, save to `figures/`, originals to `figures/originals/`).

From the **output subdirectory**:
4. **`<content_name>_summary.md`**: structured summary (filename matches the output subdirectory name)

**Do not load the PDF at this stage.** The compiled PDF is only needed for the quality audit. If the dispatched path requires it (audit mode, or edit-mode menu option 2), load it then, gated to the four-page rule: if the compiled deck is **4 pages or fewer**, read it directly in the main thread; if it is **more than 4 pages**, do not read it in the main thread. The Compilation Cycle Step 3 audit agent reads the full compiled PDF itself inside a subagent, so the main thread does not need the page images at all; hand off to Step 3 without a main-thread read. For all other paths, `slides.tex` is sufficient.

### E4: Mode Dispatch

Branch on the active mode:

- **`mode=audit`**: jump directly to Compilation Cycle Step 3 (Quality Audit), which loads the full compiled PDF itself inside its audit subagent; no main-thread PDF read is needed here. After Step 4 (Fix and Recompile) completes, proceed to Output. Skip the menu in E5.
- **`mode=pptx`**: jump directly to the Output section's PPTX conversion block. Skip the menu in E5.
- **`mode=edit`**: continue to E5.

### E5: Present Menu (edit mode only)

After loading context, **pause and present this menu** to the user:

> "Loaded slides for *[title]*. The deck has [N] slides.
> Available context: [list which of notes.md, summary.md, slides.pdf were loaded]
>
> What would you like to do?
> 1. **Edit the slides**: make content, layout, or style changes and recompile
> 2. **Run the quality audit**: read the compiled PDF slide-by-slide and report visual or formatting issues
> 3. **Convert to PPTX**: convert the existing compiled PDF to a styled PowerPoint file
> 4. **Something else**: describe what you need"

**Wait for user response.** Then route:

| Choice | Action |
|--------|--------|
| 1. Edit | Continue to E6 (Response Discipline), then apply edits in E7, then proceed to Compilation Cycle Step 1. E8 iteration prompt fires after Step 4. |
| 2. Quality audit | Jump to Compilation Cycle Step 3, whose audit agent loads the full compiled PDF itself inside a subagent; no main-thread PDF read is needed. **Treat the rest of the flow as audit mode for E8 purposes; do not return to E8 after Step 4.** The user picked audit-only and expects to land at Output, not back at the iteration menu. |
| 3. PPTX | Jump to the Output section's PPTX conversion block. Skips Compilation Cycle entirely; E8 does not fire. |
| 4. Something else | Clarify with the user, then proceed accordingly. If the clarification resolves to one of choices 1 to 3, follow that choice's E8 rule. |

### E6: Response Discipline (edit mode only)

When the user reports a visual problem, defect, or issue with the slides:

1. **Read the relevant slides** in the compiled PDF to verify the problem, gated to the four-page rule. If the compiled deck is **4 pages or fewer**, read it directly in the main thread. If it is **more than 4 pages**, do not read it in the main thread: split it into 4-page chunks with the **split-pdf** skill and launch a subagent to read the chunk(s) covering the reported slide(s). Instruct the subagent to return slide-level detail (for each slide in scope: the slide title, the verbatim text, numbers, and labels involved, and a concrete visual description of the defect, namely what overlaps, clips, overflows, or is mispositioned, and where on the slide), not a one-line summary. You need enough fidelity to locate and fix the exact element in `slides.tex`.
2. **Describe what you found** and propose a specific fix.
3. **End with a question:** "Should I apply this fix?" or "How would you like to handle this?"
4. **Do not edit `slides.tex` in the same response.** Wait for the user's approval before making any file changes.

This applies whether the problem was reported via screenshots, verbal description, or discovered during the quality audit. The user may want to handle the fix differently, redirect to a different priority, or provide additional context that changes the approach.

### E7: Apply Edits (edit mode only)

Apply the user's requested edits to `slides.tex` in the build subdirectory. Follow the Beamer style guide at `../../style-guides/beamer/style-guide.md` for all design decisions. Read it before making any edits if not already loaded. Use the loaded `notes.md` (from build) and `<content_name>_summary.md` (from output) as source material when the user asks to add, expand, or rework content.

**Edit types** (handle any combination):
- **Content changes**: add, remove, reorder, or reword slides or bullet points
- **Figure or chart changes**: modify TikZ diagrams, pgfplots charts, data values, labels, colors
- **Layout changes**: split dense slides, merge sparse slides, change column widths
- **Style changes**: adjust colors, fonts, spacing (within the style guide)
- **Structural changes**: add new slides, remove slides, change slide order

After edits are written, proceed to Compilation Cycle Step 1.

### E8: Iteration Prompt (edit mode only)

After Compilation Cycle Step 4 completes in edit mode, before proceeding to Output, ask:
> "Edits applied and recompiled. Would you like to make further changes, or are you done?"

- If the user requests more edits (or an audit, or any further change to the deck): this is a new edit round. **First re-run the E2 version-snapshot step** to preserve the round just reviewed as the next `vNN` (PDF + paired `.tex`), then loop back to E5 (or E6 if a specific problem is reported). Re-firing the snapshot here, once per round, is the load-bearing rule: skipping it is the version-snapshot miss this guards against.
- If the user is done: proceed to Output and stop after the deliverable PDF copy.

**Do not raise PPTX in this prompt.** PPTX is offered at most once, at the end of the turn that first delivers the deck, and is never re-asked across edit iterations or later turns. If the user wants PowerPoint, they will ask ("pptx this deck") or pass `mode=pptx`, which routes to the Output PPTX conversion block at any time.

This iteration prompt does not fire in generate, audit, or pptx modes.

---

## Step 0: Verify LaTeX Installation

Before doing anything else, confirm that LaTeX and Beamer are installed and available in the PATH.

### Set up PATH for TeX

MacTeX installs to `/Library/TeX/texbin`. Claude Code sessions may not have this in the PATH by default. Always run this first:

```bash
export PATH="/Library/TeX/texbin:$PATH"
```

Then verify:
```bash
which pdflatex && pdflatex --version | head -1 && kpsewhich beamer.cls
```

### If pdflatex is still not found

Check alternate locations:
```bash
ls /Library/TeX/texbin/pdflatex 2>/dev/null
ls /usr/local/texlive/*/bin/*/pdflatex 2>/dev/null
```

If TeX binaries exist at a different path, add that path to PATH instead.

If no TeX installation is found at all, stop and tell the user:

> "LaTeX/MacTeX is not installed on this machine. Please install it by running these commands in your terminal:
> ```
> /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
> brew install --cask mactex
> ```
> Then restart and try again."

Do not attempt to install MacTeX from within the agent because it requires `sudo` and interactive password entry.

### If everything is already installed

Proceed silently. Do not report to the user unless there was a problem.

---

## Step 0.1: Pre-flight Deliverable Check

Before writing any `.tex` file or compiling, check for existing deliverable PDFs that would be overwritten:

1. Check the parent directory (one level above the build directory) for any `*_slides.pdf` file.
2. Check the build directory for existing `slides.pdf` or `slides_tmp.pdf`.

If any deliverable PDF already exists, create a timestamped backup (`cp "<file>" "<file_without_ext> YYYY-MM-DD-HHMMSS.pdf"`) before proceeding, and report: "Backed up existing deliverable: [filename]"

If no deliverables exist, proceed silently.

**This step is non-negotiable.** Overwriting a deliverable without backup destroys work from previous sessions that may not be recoverable.

**Version snapshots (`vNN`) are an edit-mode behavior** (Edit Mode E2 entry and each E8 loop-back, one per edit round), not generate mode. Generation writes no `vNN`; it uses the timestamped backup above and creates only `<base_name>_slides.pdf`. The first `vNN` is created at the first edit, as the backup of the generated deck (`v01`).

---

## Step 0.5: Structure and Register Triage

This step resolves two independent axes and reports both.

**Structure axis (`structure=`, the deck shape).**

1. Resolve the structure value:
   - No `structure=` and no `audience=`: `mba` (the default).
   - `structure=mba`, or the deprecated aliases `academic` / `default`, or `audience=` naming any of those: `mba`.
   - `structure=<value>` or `audience=<value>` naming `teaching`, `faculty`, `professional`, `consulting`, or `working`: that structure. (`audience=` is the deprecated alias for `structure=`; same value set.)
   - Any unrecognized value: fall through to `mba`. This preserves callers that pass level words such as `Executive MBA` or `undergraduate`; those are not structural tokens and resolve to the default.
2. Read `domain_patterns.md` (in this skill's directory) and load the resolved structure's entry:
   - `mba` (and aliases / unrecognized values) maps to **MBA / Executive (default)**
   - `teaching` or `lecture` maps to **Teaching Lecture**
   - `faculty` maps to **Faculty Development**
   - `professional` maps to **Professional Audience**
   - `consulting` or `workshop` maps to **Consulting Workshop**
   - `working` maps to **Working Deck**
3. Apply that entry's structural template, rhetoric balance (logos/ethos/pathos), slide-count range, density, Devil's Advocate inclusion, code block inclusion, and transition slide inclusion throughout all subsequent steps.

**Register axis (`register=`, the language level).**

4. Resolve the register value: no `register=` resolves to `business` (the default); `register=technical` resolves to technical. Record it; it governs the domain-translation rule and the audit checklist's Content Quality #14.
   - `register=business` (default): the reader is a business or executive audience, not a specialist in the source's field. Translate or gloss every domain term on first use, state each chart's metric and baseline in the audience's words, and keep a translated term consistent across the deck. Content Quality #14 (the register and translation scan) is enforced at audit time.
   - `register=technical`: the reader is a specialist; keep the source's domain vocabulary. The translation rule and Content Quality #14 are suppressed.

Structure and register are separate axes. The default deck pairs an academic-shaped structure (`mba`) with a business register; the academic structure does not imply a technical register. A scholarly, keep-the-jargon deck is `register=technical` on whatever structure.

5. Report to the user which pattern is active:

> "Structure: [entry name] (from invocation, or default `mba`). Register: [business|technical]. [One-line summary of rhetoric balance and slide count range from domain_patterns.md]."

---

## Step 0.6: Citation Strategy Decision

Before reading the style guide or writing any content, determine and state the deck's citation pattern:

- **Single-source** (one paper, report, or dataset drives 80 percent or more of content slides): the title slide carries a "Based on [Author. Year. Title. Publication.]" line. Content slides carry `\sourcecite{}` only when they draw on a different source. Repeated identical citations on every slide add visual noise; this is enforced by the audit checklist's Deck-Level Checks.
- **Multi-source** (slides draw on different sources): every content slide carries its own `\sourcecite{}`.

Refer to the Citation Strategy section in `../../style-guides/beamer/style-guide.md` for both rendering patterns.

State the decision explicitly to the user before proceeding, for example: "Citation strategy: single-source. Title-slide attribution: Smith. 2024. Paper Title. Publication. Slides with different sources: none." or "Citation strategy: multi-source. Per-slide `\sourcecite{}` on every content slide."

This is a generation-time decision, not a post-hoc audit catch. Get it right before writing any `.tex` content. Do not produce per-slide citations on a single-source deck without explicit override slides identified at this step.

---

## Design Requirements

**First action: use the Read tool to read these four files now, in order:**

1. `../writing-voice-guide/README.md` (or equivalent) -- guidance on creating a writing voice layer; slide-specific tone rules (factual titles, no over-narration, no selling the session, takeaway discipline)
2. `../../style-guides/beamer/style-guide.md` -- visual design: colors, fonts, templates, macros, chart styling, TikZ patterns, table formatting, slide type patterns, and the complete LaTeX preamble to copy verbatim from its Quick Reference section
3. `audit-checklist.md` (in this skill's directory) -- the quality audit checklist used in Step 3
4. `domain_patterns.md` (in this skill's directory) -- structure-specific guidelines for the active entry

Do not write any `.tex` content before completing all four reads. Do not reconstruct the preamble from memory. The style guide is the single source of truth for visual design. Do not deviate from its color definitions, font settings, or template configurations.

Apply the structure-specific guidelines from the matched domain pattern throughout generation: structural template, rhetoric balance (logos/ethos/pathos), slide count range, density level, Devil's Advocate inclusion, code block inclusion, and transition slide inclusion. Apply the register (Step 0.5) to all slide language: under `register=business`, translate or gloss the source's domain terms; under `register=technical`, keep them.

---

## Step 0.7: Outline Checkpoint

**This checkpoint is mandatory.** Write a brief outline and present it to the user before proceeding. The outline must include:

1. **Structure, register, and rhetoric balance:** The active structure entry name, the register (business or technical), and the structure's logos/ethos/pathos percentages.
2. **Slide sequence with assertion titles:** One line per slide showing the slide number, assertion title, and slide type (for example: title, hook, finding, chart, table, diagram, code, Devil's Advocate, transition, takeaway, closing). Follow the structural template from the active domain pattern.
3. **Figure plan:** For each planned figure, indicate whether it will be:
   - **pgfplots** (inline in .tex)
   - **matplotlib** (standalone script, included as PDF)
   - **TikZ diagram** (inline in .tex)
   - **Extracted from source** (cropped from source PDF)

   Reference the decision matrix in `figure_generation.md` to determine which path each figure takes. Default to pgfplots; use matplotlib only when the figure exceeds pgfplots' comfortable range per the matrix.
4. **Devil's Advocate slide:** Whether included or omitted, and why (per the active domain pattern's rules).
5. **Source content inventory:** Enumerate every major table and figure cataloged in `notes.md` (or the source's text extract). For each item, decide one of three handlings and record a one-line reason:
   - **Render**: produce a slide that includes the magnitudes (numeric values, percentage points, coefficients). The reader sees the source's quantitative content.
   - **Compress** (high bar; default is Render). Fold into a parent slide as a categorical or summarized treatment, deliberately dropping some magnitudes. Eligible only when another already-Rendered slide carries the same magnitude pattern. Two distinct findings (different magnitudes, different countries, different mechanisms, or different time periods) get two distinct slides; folding them into one is a defect, not an optimization. Reason must be specific (for example, "the magnitude pattern is shown in Figure X already" or "audience does not need per-site detail"). Forbidden patterns: folding findings about different countries with different magnitudes into one card-set slide; folding sector, location, occupation, and other mechanism findings into a single "no single pathway" slide when each has a distinct mechanism; folding a country exception into a parent slide as a footer when the exception itself has a distinct magnitude or mechanism.
   - **Drop**: omit entirely. Reason must be specific (for example, "robustness check that does not change the main finding" or "appendix-level methodological detail").

   Report a single inventory line such as: "Source content inventory: N tables/figures cataloged. M rendered, K compressed, L dropped." Then list each Compress and Drop decision with its one-line reason. Render decisions do not need individual reasons. The most common information-loss pattern in this skill is silently collapsing two information-dense tables (for example, a "rises" table and a "falls" table, each with per-row magnitudes) into one categorical slide that strips the magnitudes. Make these decisions explicit at outline time, not implicitly during slide writing. If a Compress or Drop reason reads as "for brevity" or "to fit the slide count," reconsider whether the content should be preserved as its own slide.

   **Diagnostic signal (not a numerical floor):** if the final deck has fewer than 8 slides for an academic paper, working paper, long-form report, or whitepaper, suspect over-compression. The signal is "too few for the source," not "below a numerical floor"; if the source has only three distinct findings, the deck legitimately stays small. Inspect every Compress decision and restore any whose folded items have different magnitudes, countries, mechanisms, or time periods. Audit-time backstop is `audit-checklist.md` Deck-Level Checks.
6. **Citation strategy recap:** Restate the decision from Step 0.6 (single-source or multi-source) and which slides, if any, carry overrides. This pins the strategy into the approved outline so it cannot drift during slide writing.
7. **Text-column mechanism inventory:** for every content slide, declare the mechanism used in its text content. Add these lines to the inventory:
   - Slide K text column: **itemize**, N parallel claims (default for 3+ parallel claims; use `\textbf{\color{DeepTeal}...}` or `\textbf{\color{SlateNavy}...}` lead-ins on the key facts).
   - Slide K text column: **prose**, N paragraphs (only when content is genuinely narrative: story, scenario walkthrough, single argument with no parallel structure).
   - Slide K text column: **TikZ card(s)**, N siblings (for visual cards using empty-box-plus-overlay; bullet content inside uses minipage+itemize per `audit-checklist.md` Box Text Anchoring #4).
   - Slide K text column: **table**, N rows (for structured comparison data).

   This declaration is the planning-time defense against the source-prose-to-slide-prose trap. If the source material (notes.md, summary.md) is written as prose, the slides do not inherit that style. Decompose source prose into discrete claims first, then pick the mechanism. A slide whose declared mechanism is "prose, 3+ paragraphs" with parallel claims is the defect class this step catches: most such slides should be itemize. Write-time enforcement lives in Step 1 (Column Content Invariant), audit-time backstop in `audit-checklist.md` Content Quality #11.

Save the outline as `outline.md` in the build directory.

Show the outline to the user and **wait for approval** before proceeding. If the user requests changes, revise the outline, update `outline.md`, and re-present. Do not begin writing `.tex` content or generating figures until the user approves.

---

## Step 0.8: Code-First Figure Generation

Read `figure_generation.md` (in this skill's directory).

For each figure identified in the approved outline as needing **matplotlib**:

1. Create the `scripts/` directory in the build directory if it does not exist:
   ```bash
   mkdir -p scripts
   ```
2. Write a standalone Python script to `scripts/` following the conventions in `figure_generation.md`:
   - All imports at the top
   - Palette dict at the top (copy from `figure_generation.md`)
   - Data defined or loaded at the top
   - Figure construction in the middle
   - `plt.savefig()` at the bottom, saving to `../figures/<figname>.pdf`
   - Standalone: a reader can run it with `python3 scripts/<figname>.py` and reproduce the figure
3. Create the `figures/` directory if it does not exist:
   ```bash
   mkdir -p figures
   ```
4. Run the script to generate the figure PDF:
   ```bash
   python3 scripts/<figname>.py
   ```
5. Verify the figure renders correctly by reading the output PDF with the Read tool. Check:
   - Colors match the deck palette
   - Labels are legible at projection size
   - Axes match the slide background (white)
   - No chartjunk (unnecessary gridlines, borders, or axis marks)
   - If the figure has curved arrows with `connectionstyle='arc3'`, the Bezier helper functions from `figure_generation.md` are used for label placement

If any figure fails verification, fix the script and regenerate.

For figures that stay in **pgfplots**, proceed as normal (they will be authored inline in the .tex file during the content writing step). The decision matrix from `figure_generation.md` determines which path each figure takes.

If the approved outline has **no matplotlib figures**, skip this step entirely. No `scripts/` directory is needed.

---

## Content Requirements

The deck must cover the **key themes from all parts** of the source material. Do not skip or underweight any major section.

### Methodology Slide Template

When the deck includes a methodology slide (typically for empirical studies, research papers, or studies with a defined population and method), use this template. The slide is one frame, structured into seven ordered elements; drop any element that is not load-bearing for the source.

**The seven elements (left column = study setup, right column = evaluation):**

| Order | Element | Column | What it captures |
|---|---|---|---|
| 1 | Question | Left (setup) | What the research is trying to answer |
| 2 | Method | Left (setup) | The approach (intervention, framework, algorithm, instrument) |
| 3 | Data | Left (setup) | Source, size, time period |
| 4 | Population | Left (setup) | Who or what was studied |
| 5 | Outcomes | Right (evaluation) | Variables measured and how operationalized |
| 6 | Comparison | Right (evaluation) | Baseline or counterfactual the method is judged against |
| 7 | Analysis | Right (evaluation) | Statistical or computational lens applied |

**Layout:** two equal columns. Left column holds the elements present from {Question, Method, Data, Population} (study setup). Right column holds the elements present from {Outcomes, Comparison, Analysis} (evaluation). Order moves question to measurement to analysis: left top to left bottom, then right top to right bottom.

**Visual treatment:** each element is **one short phrase**, not a paragraph or bullet list. Label each phrase with the element name as a bold colored lead: `\textbf{\color{DeepTeal}Question:}` then the phrase. All seven labels use DeepTeal; do not vary color across labels. The bold-colored label is the visual anchor; the phrase carries the content.

**Drop what is not load-bearing.** The template is a checklist of what could be on the slide, not what must be. Examples:

- A behavioral RCT often drops Method (the design is the method) and emphasizes Population and Comparison.
- A methods paper often drops Population and emphasizes Comparison and Analysis.
- A descriptive empirical paper often drops Comparison (there is no counterfactual).
- A non-empirical source (opinion piece, position paper, blog) drops the whole slide.

**Column balance after drops.** If dropping elements leaves one column with fewer than 2 elements, rebalance: move Outcomes to the left column, or collapse to a single-column layout. Do not ship a methodology slide with one column at near-capacity and the other near-empty.

**Sanity check.** A reader who finishes the slide should be able to predict the shape of the findings slides that follow. If they can't, an element is missing: restore one of the dropped elements, or rewrite an existing phrase to carry more weight.

### Limitations Slide Template

When the source material has an **Issues section** with substantive limitations, include a **"Limitations and Critique"** slide near the end of the deck (in Act III, before the closing). Present 2-3 of the strongest objections, each rendered in the three-part Devil's Advocate format below.

**Three-part format for each item:**

- **Concern:** what a skeptic would say (the objection in its strongest form).
- **Why reasonable:** why the concern is legitimate (steel-man the skeptic; do not dismiss).
- **Response:** how the source addresses the concern, or how the limitation is acknowledged when it cannot be fully resolved.

Each item gets its own card or block. Visual treatment: 2-3 colored cards side-by-side or stacked, with bolded section labels (e.g., `\textbf{\color{DeepTeal}Concern:}`, `\textbf{\color{SlateNavy}Why reasonable:}`, `\textbf{\color{DeepTeal}Response:}`). Loose prose paragraphs without the three-part labels are a defect: the three-part format reads as a Devil's Advocate exchange, which is the pedagogical pattern this slide is designed for; loose prose loses that affordance.

**Structure modifiers.** The active domain pattern determines whether this slide is required, optional, or omitted:

- **MBA / Executive (default):** Include when the source has substantive limitations; an academic source almost always does.
- **Teaching Lecture:** Include when the source has an Issues section.
- **Faculty Development:** Include (faculty audiences are skeptical by nature).
- **Professional Audience:** Optional (depends on whether the talk makes a claim or reports findings).
- **Consulting Workshop:** Built into the exercise debrief framing; do not add a standalone slide.
- **Working Deck:** Not needed.

---

## Visual Mechanism Selection

**Before writing any slide content, classify each planned slide's content and select the appropriate LaTeX mechanism.** Do not default to TikZ for everything. The goal is beautiful, graphical slides, and the right mechanism for the content type produces better visuals than forcing everything into freeform TikZ placement.

### Decision rule

Every TikZ diagram must contain at least one element that cannot be represented as a list item or table cell: an arrow showing causation, a spatial position conveying meaning, a data-driven axis, or a geometric relationship between elements. If the slide content is a list of items rendered as labeled boxes without meaningful spatial relationships between them, use a table or formatted list instead.

### Mechanism by content type

| Content type | Signal | Mechanism | Example |
|---|---|---|---|
| **Spatial** (flows, timelines, cycles, hierarchies, cause-effect) | "A leads to B", process steps, directional relationships | TikZ diagram | Process flow, technology adoption lifecycle |
| **Quantitative** (data series, distributions, comparisons by magnitude) | Numbers, percentages, trends over time | pgfplots chart | Agreement rates by round, ROI comparison bars |
| **Tabular** (structured comparisons, multi-attribute data, problem/solution pairs) | Rows and columns, parallel structure across items | booktabs table with colored cells, `\rowcolor`, `$\to$` arrows | Failure modes with fixes, feature comparison matrix |
| **Sequential** (ranked items, numbered priorities, key takeaways, lessons learned) | "Five priorities", "three lessons", ordered list without spatial relationships | enumerate/itemize with styled formatting (colored numbers, bold lead text, `\itemsep` for rhythm) | Five priorities, key takeaways |
| **Mixed** (explanatory text alongside a visual) | Description plus diagram, narrative plus chart | Two-column: text column uses the appropriate text mechanism, visual column uses TikZ or pgfplots | Case study description plus calculation chain |
| **Code** (API calls, scripts, prompts, tool configurations) | Code in the source content, programming examples, API usage | listings environment (from style guide) | Skill structure, Python API call, prompt template |

### What "graphical" means for non-TikZ mechanisms

Tables and formatted lists are visual representations when properly styled:
- A booktabs table with alternating `PaleBlue` row shading, colored header cells, and icon-like symbols (`$\to$`, `$\checkmark$`, `$\times$`) is graphical.
- An enumerate list with `DeepTeal` numbered items, `SlateNavy` bold lead text, and generous `\itemsep` spacing is graphical.
- A two-column layout with a styled text block and a chart is graphical.

"Graphical" means the slide communicates visually, not that every slide contains a TikZ diagram. Five colored boxes stacked vertically with no arrows or spatial relationships is not more graphical than a well-formatted table; it is a table that is harder to maintain and more likely to render with non-uniform heights.

---

## Number Formatting

**Years must never have comma separators.** "2024" not "2,024". This is a common LaTeX problem that occurs in multiple contexts. Apply all of the following preventive measures:

- **pgfplots axis labels:** Always disable thousand separators on any axis that displays years:
  ```latex
  /pgf/number format/.cd, set thousands separator={}
  ```
  Or per-axis: `xticklabel style={/pgf/number format/1000 sep={}}`

- **siunitx:** If using `siunitx`, configure it to not group year-like numbers. Prefer writing years as plain text (`2024`) rather than `\num{2024}`.

- **Tables and text:** Never wrap years in `\num{}` or any number-formatting macro. Write years as literal text.

- **pgfplotstable:** If using `pgfplotstable`, set `columns/year/.style={int detect, 1000 sep={}}` or similar.

This applies to all four-digit years anywhere in the deck: axis labels, table cells, slide text, figure annotations, and captions.

---

## Acronyms and Abbreviations

**Define every non-exempt acronym on first use.** First appearance in the deck uses the form `Term (ACRONYM)`; every subsequent appearance uses the bare `ACRONYM`. "First use" means the first time the acronym appears anywhere in the deck, not the first time it appears on each slide. Frametitles follow the same rule: if a frametitle is where the acronym first appears, the title uses `Term (ACRONYM)`; later frametitles can use the bare acronym.

This rule applies to all original deck content. Acronyms inside extracted figures from the source paper (`\includegraphics{...}` from the source) are not bound by this rule: the figure carries the source's own conventions.

### Exemption list (no expansion needed)

These acronyms are widely recognized and stay bare on every appearance:

- **Geographic / political:** US, USA, UK, EU, UN, NATO, OECD, G7, G20, NYC, LA, SF, DC
- **Business roles and education:** CEO, CFO, COO, CTO, CIO, CMO, VP, HR, PR, MBA, PhD, MD, JD, BA, BS, MS, MA, IRB
- **Tech generic:** AI, ML, LLM, NLP, IT, API, URL, PDF, HTML, CSS, SQL, CSV, JSON, XML, HTTP, HTTPS, GUI, OS, USB, GPS, ATM, GPU, CPU, RAM, WiFi
- **Business and finance:** ROI, KPI, OKR, B2B, B2C, SaaS, SEO, UX, UI, CRM, ERP, IPO, M&A, P&L, EBITDA, R&D, GDP, FAQ
- **US agencies and regulation:** FBI, CIA, IRS, FDA, SEC, EPA, DOJ, NASA, GDPR, HIPAA

Anything not on this list is expanded on first use. Paper-specific or domain-specialized acronyms (e.g., RCT, GMM, IV, DID, DPO, SFT, RLHF, RAG) are always expanded on first use, even when the source paper assumes the reader knows them. Adapt the exemption list to your audience: a deck for ML researchers might add ML-specific acronyms to the exempt list; a deck for medical professionals might add medical acronyms.

---

## Quality Standards

- **Consistent narrative flow** with technical rigor maintained throughout
- **Optimal cognitive density:** distribute content evenly across slides so that no individual slide is overloaded, but the deck as a whole covers the material thoroughly
- **Right mechanism for the content:** use the Visual Mechanism Selection table above (TikZ for spatial relationships, pgfplots for data, booktabs for structured comparisons, enumerate for sequential items); every slide should fill its available space effectively
- **Beautiful figures:** create high-quality TikZ diagrams, charts, and visual representations; use appropriate chart types (bar, line, scatter, etc.) for the data being presented
- **Beautiful tables:** well-formatted tables with clean typography and appropriate spacing
- **Images from the source:** include figures or images from the source material when they are informative and reproducible
- **Data visualization:** prioritize clear, accurate visual representation of quantitative findings

---

## Figure Extraction

**Complete this step before writing any `.tex` content.** Review the notes and source material to inventory every figure that will appear in the deck, decide how each will be handled, then extract any that require it.

Note: This step handles figures pulled from source documents. Code-first figure generation (Step 0.8) handles newly created matplotlib figures. Both may apply to the same deck.

### Decision Criteria

| Figure type | Handling |
|---|---|
| Simple chart (bar, line, scatter, box plot) with data extractable from the source | **Recreate in pgfplots** (matches deck palette, fully editable, projects well) |
| Multi-panel figure where each panel is a simple chart | **Recreate if 1-2 panels; extract if 4+** (diminishing returns on recreation effort) |
| Complex chart (choropleth map, many overlapping visual elements) | **Extract from source PDF** |
| Figure where the paper's own color encoding carries the meaning (party-line colors, heatmaps, categorical color maps) | **Extract from source PDF** (color encoding must be preserved) |
| Photograph (person, place, object, interface screenshot, physical phenomenon) | **Always extract** (cannot be recreated in TikZ) |
| Time series with annotations (reference lines, labeled periods, event markers) | **Recreate in pgfplots** (annotations need deck-palette colors and readable font sizes) |

**Color trade-off:** Extracted figures retain the paper's own color scheme, which typically will not match the deck palette. When color consistency matters more than exact reproduction, prefer pgfplots recreation. When the paper's visual encoding must be preserved, extract and accept the color mismatch.

**Projection readability:** Extracted figures were designed for printed pages (letter/A4, read at arm's length). When projected on a screen, axis labels, legends, and annotations are often too small to read. This is the strongest reason to prefer recreation for simple charts: pgfplots charts use the deck's font sizes and are legible when projected.

### If No Figures Need Extraction

If all figures in the deck will be recreated in TikZ/pgfplots or generated by matplotlib scripts (Step 0.8), skip this step and proceed to the Compilation Cycle. No `figures/` directory is needed unless matplotlib scripts already created one.

### Chart Recreation from Source

When recreating a paper's chart in pgfplots:

**Data extraction:** Academic papers typically provide enough information to approximate key data points: tables with exact values, text describing specific numbers, or axis ranges visible in the original figure. Use these to construct coordinate lists. Label approximated values with a comment: `% approximated from figure`.

**Annotation patterns for labeled periods or generations:**
- Use short dashed line segments spanning only the relevant time window, not full-width lines. Full-width dashed lines create visual clutter, especially when multiple reference levels are close together.
- Color each segment and label to match the deck palette's semantic assignment for that category.
- Position labels to avoid crossing the main data line. Use `anchor=south` for labels above the line, `anchor=north` for below.

**Common pitfalls from experience:**
- Full-width reference lines at similar y-values visually merge and obscure the data line. Use short segments scoped to each category's active period.
- Labels placed with `anchor=west` at the right edge of the chart get clipped. Add padding to `xmax` or position labels inside the chart area.
- Smooth time series need enough coordinate points (every 2-3 years) to avoid angular segments, especially at inflection points.

### Extraction Pipeline

For each figure to extract, work in the build directory.

**1. Create the figures directory**

```bash
mkdir -p figures/originals
```

**2. Render the page and visually verify before cropping**

```bash
pdftoppm -r 300 -png -f <page_num> -l <page_num> <path_to_source_pdf> figures/originals/<figname>
```

**CRITICAL: Read the rendered PNG with the Read tool before cropping.** Do not assume the page number from text annotations is correct; PDF page numbers in text files can be offset from physical pages. Visual verification catches:
- Wrong page (references section instead of figure)
- Multiple figures on one page (requires manual crop coordinates, not whitespace detection)
- Figure title and source notes that should be excluded from the crop

**3. Crop to the chart area only**

The goal is to include the chart axes, data, and legend, but exclude:
- The figure title unless needed for context
- Source notes and methodology text below the chart
- Page numbers and headers

For single-figure pages: whitespace detection may work as a starting point, but always verify the result visually and trim source notes manually if included.

For multi-figure pages: use manual pixel coordinates. After reading the rendered PNG, estimate the vertical position of each figure as a fraction of page height and crop with PIL:

```python
from PIL import Image
img = Image.open('figures/originals/page-35.png')
w, h = img.size
# Figure 3 is the bottom chart on this page, roughly 50-75% of page height
fig3 = img.crop((40, int(h*0.50), w-40, int(h*0.75)))
fig3.save('figures/fig3_income_curves.png')
```

Iterate on the crop bounds until the chart fills the image without source notes or adjacent figures.

**4. Verify aspect ratio for 16:9 slides**

After cropping, check the image dimensions. A crop wider than 3:1 will render as a narrow strip on a 16:9 slide. If the chart is very wide and short (for example, two side-by-side panels), accept the aspect ratio rather than adding whitespace, but use `height=0.68\textheight,keepaspectratio` to prevent overflow:

```latex
\includegraphics[width=0.85\textwidth,height=0.68\textheight,keepaspectratio]{figures/fig3_name}
```

Always include both `width` and `height` with `keepaspectratio` for extracted figures. Without the height constraint, tall images overflow the frame.

**5. Name and reference**

- Cropped figures: `figures/fig<N>_<descriptive_name>.png`
- Original page renders: `figures/originals/` (preserved for re-cropping)
- Reference in `.tex`: `\includegraphics[width=0.85\textwidth,height=0.68\textheight,keepaspectratio]{figures/fig3_mechanism}`

---

## Compilation Cycle

### Step 1: Validate Any Existing Work, Write, and Compile

**If `slides.tex` already exists** in the working directory (that is, this session is continuing prior work), validate its preamble before touching anything:
- Confirm `\usetheme{default}`; if any other theme (Madrid, Warsaw, Berlin, etc.) is present, stop and notify the user before continuing
- Confirm `aspectratio=169` in the document class options
- Confirm no `fontspec`, `\setmainfont`, or `luatexja` (markers of lualatex-specific code incompatible with the style guide)

If any check fails, report the violation to the user and ask how to proceed. Do not silently continue with a broken preamble.

1. Write the complete `.tex` file, copying the preamble verbatim from the Quick Reference section of `../../style-guides/beamer/style-guide.md`.
   - **TikZ box invariant (width, height, list typography).** When using the empty-box-plus-overlay pattern (or any TikZ node with `minimum width` or `minimum height` and a separate text overlay), compute and verify all three properties *before* writing the overlay content.

     **Width invariant (mandatory):** For every TikZ node with a `minimum width=Wcm` and an overlay node with `text width=Tcm` at the same anchor, the overlay must satisfy `T <= W - 2 * inner_sep`. At the style guide default `inner_sep=6pt` (about 0.21cm), this is `T <= W - 0.42cm`. Common settings: `minimum_width=4.4cm` requires `text_width <= 3.98cm`; `minimum_width=4.6cm` requires `text_width <= 4.18cm`. Violating this formula pushes the text overlay past the right edge of the box, which causes (a) systematic mid-word hyphenation as TeX tries to fit oversize lines, and (b) text fragments visibly extending past the box border. Both defects are guaranteed by the geometry, not random.

     **Height invariant (mandatory):** Compute `chars_per_line = (text_width - indent) / avg_char_width` (1.7mm for `\footnotesize`, 1.5mm for `\scriptsize`, 1.9mm for `\small`), write each bullet or line item to fit within that count, then compute `total_content_height` per the procedure in the style guide under "Comparison / Category Boxes". Verify `total_content_height < minimum_height - top_shift`.

     **List typography (mandatory):** If the node will contain three or more parallel items (bullet-like content), generate the `minipage` plus `itemize` form, not `\\`-separated segments. Three patterns are prohibited as content layouts inside TikZ nodes: manual bullet glyphs (`$\bullet$~Item one\\$\bullet$~Item two\\$\bullet$~Item three`), manual line breaks alone (`Item one\\Item two\\Item three`), and comma-separated grouped lines. All three produce flat stacked text with no hanging indent and no consistent inter-item spacing. Use this pattern instead: `\node{\begin{minipage}{Wcm}\setlength{\leftmargini}{1em}\begin{itemize}\setlength{\itemsep}{2pt}\item Item one \item Item two \item Item three\end{itemize}\end{minipage}};` where `Wcm` matches the node's `text width`. Two-or-fewer items may remain as inline prose. **Do not** use `\begin{itemize}[leftmargin=*]`: it requires `\usepackage{enumitem}` in the preamble, which silently overrides Beamer's bullet template and strips visible bullet glyphs from every itemize in the deck. This rule is parallel to `audit-checklist.md` Box Text Anchoring #4 and applies regardless of node width or height.

     **If any invariant fails:** shorten the text, increase the box dimensions uniformly across sibling cards, change the list pattern, or change the visual mechanism. Never rely on post-compilation visual inspection to catch overflow. At PDF page resolution, 2-3mm of overflow is invisible and 5mm of horizontal text-past-box is hard to spot at thumbnail.

     **Pre-write checklist:** for every TikZ node with `minimum width`, `minimum height`, and overlay content, write the arithmetic check as a comment in the `.tex` source above the node:

     ```latex
     % Width invariant: text_width(3.9cm) <= 4.4cm - 0.42cm = 3.98cm OK
     % Height invariant: 7 content lines * 3.5mm + ~10mm overhead = 34.5mm < 48mm box OK
     % List typography: 3+ items -> minipage+itemize OK   (or "2 items -> inline OK")
     ```

     The comment is for the audit agent and any future reader; it forces the generator to do the arithmetic before writing.
   - **Column content invariant (mandatory).** Before writing the text column of any two-column slide (or any non-TikZ content block), count the parallel claims in the planned content. If three or more, write as `itemize` with `\textbf{\color{DeepTeal}...}` or `\textbf{\color{SlateNavy}...}` lead-ins on the key facts, not as `\vskip`-separated paragraphs. Prose is allowed only when the content is genuinely narrative (story, scenario walkthrough, single sustained argument where removing one sentence breaks the flow). Default: itemize.

     **Source style is not slide style.** The `summary.md` or `notes.md` is prose. The slide is not. Decompose source prose into discrete claims, then bullet them. The source-prose-to-slide-prose trap is the most common content-design failure mode in this skill: source material is read as prose and transcribed as prose into slide columns when it should have been decomposed into bullets first. Planning-time defense lives in Step 0.7 (text-column mechanism inventory). Audit-time backstop is `audit-checklist.md` Content Quality #11. This invariant is the write-time defense between them.

     **Pre-write comment requirement:** above every two-column slide's text column and every standalone non-TikZ content block, write the mechanism decision as a comment:

     ```latex
     % Mechanism: itemize, 4 parallel claims, DeepTeal lead-ins
     \begin{column}{0.46\textwidth}
       \begin{itemize}\setlength{\itemsep}{6pt}
         \item \textbf{\color{DeepTeal}Key fact 1.} Supporting detail.
         \item \textbf{\color{DeepTeal}Key fact 2.} Supporting detail.
         \item ...
     ```

     The comment must match the Step 0.7 inventory declaration for that slide. If the inventory said "Slide K text column: itemize, 4 claims" and the writer is about to produce 4 prose paragraphs, the mismatch surfaces immediately.
2. Compile with `pdflatex` at least twice. The `\sourcecite{}` macro uses `remember picture,overlay`, which requires two passes to stabilize absolute page coordinates. A single pass will produce incorrect citation placement on new or restructured slides. Always run: `pdflatex` (first pass, writes coordinates to `.aux`), then `pdflatex` (second pass, reads coordinates and places nodes correctly). Do not use lualatex or xelatex. The style guide's preamble uses pdflatex-compatible packages and is incompatible with lualatex's fontspec-based font loading. If you encounter a font error, fix it within pdflatex constraints rather than switching compilers.
3. Run `bibtex`/`biber` if references are used, then add a third `pdflatex` pass.
4. Recompile further if the log reports "Label(s) may have changed."
5. **Dropbox-synced directories:** If the working directory is inside a Dropbox-synced folder, compile to a temporary filename (`pdflatex -jobname=slides_tmp slides.tex`) to prevent Dropbox from silently overwriting the output during rapid edit-compile cycles. After verifying the output, copy the temporary file to the final `slides.pdf` location.

### Step 2: Fix Compilation Warnings

After initial compilation, review the log file and fix **ALL**:
- Overfull `\hbox` warnings
- Underfull `\hbox` warnings
- Overfull `\vbox` warnings
- Underfull `\vbox` warnings

No matter how small. Every single one.

Common fixes:
- Adjust text width, margins, or column widths
- Reword text to fit line breaks
- Adjust `\parbox` or `minipage` widths
- Fix spacing commands

**Compression limit:** If fixing overfull warnings on a single slide requires more than two compression passes (reducing font size, shrinking spacing, narrowing widths), stop compressing. The slide is overloaded. Restructure instead: split into two slides, simplify the diagram, replace a dense TikZ diagram with a table or two-column layout, or change the visual mechanism. Repeated compression produces illegible slides that pass compilation but fail visual review.

Recompile and verify all warnings are eliminated.

### Step 3: Quality Audit (Merged)

After the deck compiles cleanly, perform a **comprehensive quality audit** of the final PDF and `.tex` source. This audit is not optional; it must happen every time. This single audit replaces the former three-agent pipeline (deck evaluation, graphics verification, quality audit) to avoid loading the full source into context three times.

Launch **one audit agent** (using the Agent tool) with `subagent_type: general-purpose` and `model: opus`. The audit is rule-application against the published checklist, and the work is "scan every slide for every applicable pattern": exactly where sonnet has been observed to spot-check rather than exhaustively apply. Sonnet may be specified in the launcher only when the deck is small (under 10 slides) and has no TikZ boxes or charts.

The agent reads these files before examining any slides:
1. The **Beamer Style Guide** at `../../style-guides/beamer/style-guide.md`
2. The **audit checklist** at `audit-checklist.md` (in this skill's directory)
3. The full compiled PDF (all pages)
4. The `.tex` source

**Mandatory source-level grep checks (perform these before checklist application):**

The audit agent must perform these specific source-level scans on `slides.tex` and report findings. Each scan corresponds to an audit-checklist rule that has been observed to be missed when the agent relied on visual inspection alone. The scans are pre-computed pattern matches; they are cheap and do not depend on visual judgment.

1. **Automatic hyphenation in TikZ node body content.** Run `pdftotext -f 1 -l <N> -layout slides.pdf -` and scan the output for any line that ends with `-` immediately followed (on the next line) by a continuation fragment of the same word. Cross-reference against `slides.tex` to confirm the source did not contain an explicit hyphen. Every match is a defect per `audit-checklist.md` Hyphenation #3. Fix by adding `\hyphenpenalty=10000\exhyphenpenalty=10000\sloppy` to the affected node body, or by rewording.

2. **TikZ box width formula compliance.** For every TikZ node with both `minimum width=Wcm` and a corresponding overlay node with `text width=Tcm` at the same anchor, verify `T <= W - 0.42` (where `0.42cm` is `2 * inner_sep` at the style guide default `inner_sep=6pt`). If `inner_sep` is set explicitly to a different value, substitute accordingly. Every violation is a defect per `audit-checklist.md` Content Quality #10. Fix by reducing `text_width` to satisfy the formula or by increasing `minimum_width` and the box spacing.

3. **TikZ box height vs content height.** For every TikZ node using the empty-box-plus-overlay pattern, extract the box `minimum_height` and compute the total content height per the procedure in the style guide. Verify `total_content_height < minimum_height - top_shift`. Every violation is a defect per `audit-checklist.md` Content Quality #10. Fix by shortening the content or increasing the box height uniformly across sibling cards. **For sibling node groups:** identify every group of sibling TikZ nodes (multiple nodes positioned in a row or grid with the same style) and report the entire group when any one node fails, not just the offending node. Non-uniform expansion is the visible defect, so the fix must apply to all siblings.

4. **Facilitator prompts outside teaching/lecture structures.** When the active structure is mba, faculty, professional, consulting, or working, grep `slides.tex` for `\textit{Discuss:`, `\textit{Activity:`, `\textit{Reflect:`, `\textit{Think about:`, `\textit{Ask the room:`, and similar facilitator-prompt patterns. Every match is a defect per `audit-checklist.md` Deck-Level Checks #4. Skip this grep entirely when the active structure is teaching or lecture.

5. **`\addlegendentry` math tokens.** Grep `slides.tex` for `\addlegendentry{[^}]*\$`. Every match is a defect: math symbols inside `\addlegendentry{...}` must be wrapped with `\ensuremath{token}`, never with `$token$`. Math-mode dollars inside legend labels corrupt pgfplots state when the legend has 2+ entries and another frame follows, producing a fatal `Missing control sequence inserted / \inaccessible` error attributed to the wrong frame's `\end{frame}` (off-by-one). Fix by replacing every `$math$` inside `\addlegendentry` with `\ensuremath{math}`.

6. **`\highlight{}` inside itemize/enumerate.** Grep `slides.tex` for `\highlight` and verify each match is inside a TikZ diagram, not inside a `\begin{itemize}` or `\begin{enumerate}` block. Every match inside a list is a defect per `audit-checklist.md` Style Guide Compliance #7.

7. **Manual list typography inside TikZ nodes.** Grep `slides.tex` for TikZ node body content containing three or more segments separated by `\\` (with or without `[Npt]` spacing). Three patterns count: manual bullet glyphs (`$\bullet$~Item one\\$\bullet$~Item two\\$\bullet$~Item three`), manual line breaks alone (`Item one\\Item two\\Item three`), and comma-separated grouped lines. Every match is a defect per `audit-checklist.md` Box Text Anchoring #4. Fix by replacing the manual layout with `\node{\begin{minipage}{Wcm}\setlength{\leftmargini}{1em}\begin{itemize}\setlength{\itemsep}{2pt}\item Item one \item Item two \item Item three\end{itemize}\end{minipage}};` where `Wcm` matches the node's text width. Two-or-fewer items may remain as inline prose.

Report each grep finding before applying the rest of the checklist. The greps are cheap and catch the highest-frequency defect classes.

The agent checks every slide against every item in the audit checklist, covering all three former audit domains in a single pass:

**Deck evaluation** (narrative and design):
- Narrative flow, logical consistency, and technical rigor
- Cognitive density balance (no slide too dense, no slide too sparse)
- Design originality and professionalism
- `\highlight{}` inside `itemize` or `enumerate` (style violation; replace with `\textbf{\color{DeepTeal}...}`)

**Graphics verification** (charts and diagrams):
- Label positioning errors (overlapping, clipped, outside visible area)
- Coordinate placement errors and bounding box arithmetic for TikZ node overlap
- Numerical accuracy against source material
- Axis containment, scaling, `axis lines=left` with `axis on top`, no `clip=false`, no `symbolic x coords`
- Frame shrink prohibition (no `[shrink=N]`)
- `nodes near coords` formatting (`/pgf/number format/fixed`)
- Brace and annotation collisions (account for amplitude and label height)
- Dual-label collisions (`nodes near coords` combined with manual `\node` annotations)
- Diagram centering (parent elements centered over children)
- Color and readability

**Checklist audit** (all items in `audit-checklist.md`):
- Sourcecite clearance, hyphenation, text overflow, citation strategy, style guide compliance, and all other checklist items
- Narrative arc (pedagogical ordering, opening hook, closing takeaway)
- Bezier curve clearance (bend-angle math and safe zone)
- Code block audit (language specifier, length, font, palette, runnable script)
- TikZ list typography (three or more parallel items inside a node must use a real bulleted list, not comma-separated grouped lines or manual line breaks)
- Prose-vs-bullet match for parallel claims in non-TikZ columns (Content Quality #11)
- Bullet rendering visibility in the compiled PDF (Content Quality #12)
- Deck-level Limitations format (each card or item follows the three-part structure: what a skeptic would say, why the concern is reasonable, how it is addressed)
- Deck-level facilitator-prompt placement (only on teaching/lecture decks; Deck-Level Checks #4)
- Deck-level Compress decision audit (each Compress is content-tested, not count-tested; Deck-Level Checks #5)
- Register and domain translation (Content Quality #14): when `register=business` (the default), flag untranslated domain terms on first use, charts that do not state their metric and baseline in the audience's words, and a translated term that drifts across the deck. Skip this scan entirely when `register=technical`.

The agent returns a structured report.

#### Report Format

Present the audit results to the user as a single numbered findings list. Deck-level findings (citation strategy, cross-deck terminology, Limitations format) belong in this same list with the same fix-it-now status as slide-level findings; do not segregate them into a separate "note," "advisory," or "deck-level observation" section. The audit checklist's Deck-Level Checks section contains gating rules, not optional suggestions. Only list slides with issues; skip clean slides:

> **Quality Audit: [N] issues found:**
>
> - **Deck-level:** 14 of 15 content slides cite the same primary source. Per audit checklist Deck-Level Checks, consolidate to a single title-slide "Based on [Author. Year. Title.]" line and remove per-slide `\sourcecite{}` from those 14 slides. Slides citing a different source retain their `\sourcecite{}`.
> - **Slide 3** "Title of Slide": bar chart x-axis labels extend beyond right edge of frame; "methodology" hyphenated awkwardly in subtitle
> - **Slide 7** "Title of Slide": TikZ flow diagram arrow from node 3 to node 4 is clipped; left column text overlaps the column divider
> - **Slide 12** "Title of Slide": table values show 2,024 instead of 2024; title is generic ("Data Overview"), should state the finding

If the audit finds **zero issues**, report:

> **Quality Audit: all [N] slides clean. No issues found.**

Then proceed to Output.

Proceed immediately to Step 4 to fix all reported issues. Do not pause for user confirmation. The audit findings are objective defects with one correct fix each; no decision gate adds value here.

### Step 4: Fix and Recompile

Fix all reported issues in the `.tex` source. Then:

1. Recompile.
2. Verify the log is clean (no new hbox/vbox warnings introduced).
3. **Re-read every slide that was fixed** and verify each original issue is resolved (do not assume the fix worked). For each fixed issue, confirm:
   - The specific element that was wrong is now correct
   - The fix did not introduce a new collision, overlap, or layout problem nearby
   - For legend repositioning: verify the legend does not still overlap data at its new position
4. **Cross-category re-verification:** if a fix changed an element's position, re-check that element against all other applicable checklist categories. A fix that resolves one issue but creates another counts as a new finding and must be fixed before finalizing.

If fixes introduced new problems, fix those too before finalizing.

#### Circuit Breaker

After three different fix attempts on the same compile error or audit defect, **stop editing**. Do not attempt a fourth approach. Instead, report to the user:

1. The specific error or defect
2. What three approaches were tried
3. Why each attempt failed or introduced new problems

Ask the user how to proceed. The cost of stopping is two minutes. The cost of spiraling is an hour and a .tex file that is worse than after attempt two, because each fix introduces side effects that obscure the original error.

This limit applies per-error, not per-cycle. If the audit reports five defects and three are fixed cleanly but one resists three attempts, stop on that one and report. Do not abandon the fixes that worked.

After the final clean compile, report what the audit found and what was changed:

> **Audit fixes applied ([N] issues across [M] slides):**
> - Slide 3: [what was fixed]
> - Slide 7: [what was fixed]
> - ...

If the audit found zero issues, no report is needed; proceed silently to Output.

---

## Re-audit on Content Change

If slides are added, removed, or substantially edited after Step 3 (Quality Audit) has already run in the current session, return to Step 3 and re-run the full audit on the modified deck before producing the final deliverable. A slide-count change between the initial audit and the deliverable is the explicit trigger.

Re-run the full audit, not a spot check on new slides only. Content changes can shift adjacent slides and introduce side effects: new hyphenations from text reflow, new overfull boxes from added items, citation drift, and frame-number renumbering breaking cross-references.

Skip the re-audit only when post-audit edits are limited to whitespace, comments, or single-character typo fixes that cannot affect layout. When in doubt, re-audit; one subagent call is cheap, a defect shipped is not.

---

## Output

### Build artifacts (stay in `_build/`)

- `slides.tex` (the Beamer source)
- `slides.pdf` (the compiled output)
- `outline.md` (the approved outline from Step 0.7)
- `figures/`: extracted figures from the source (if any were embedded) and matplotlib-generated figures (if any)
- `figures/originals/`: full-page PDF renders at 300 DPI (preserved for re-cropping)
- `scripts/`: standalone Python scripts for matplotlib-generated figures (if any)
- `tables/`: `.tex` table fragments (if any were generated separately)
- `.aux`, `.log`, `.nav`, `.out`, `.snm`, `.toc` (LaTeX intermediates)

### Deliverable PDF (auto-placed in parent folder)

After successful compilation, always copy `slides.pdf` from the build directory to its parent folder with a standardized name:

1. Take the build directory name (for example, `ai-energy-detailed-slides_build`)
2. Strip the `_build` suffix to get the base name (for example, `ai-energy-detailed-slides`)
3. **Backup before overwrite (mode-aware).** No `<base_name>_slides.pdf` is overwritten without the version being replaced first preserved.
   - **Generate mode:** before copying, if `<base_name>_slides.pdf` already exists in the parent folder, timestamp-copy it as `<base_name>_slides YYYY-MM-DD-HHMMSS.pdf` before overwriting. This fires on **every** copy in the session (entry via Step 0.1, each audit-fix round, and final delivery), so no deliverable is overwritten without a recoverable prior version. An audit-fix cycle is a major change, not a minor edit.
   - **Edit / audit / pptx modes:** the deck was preserved as `vNN` milestones at round starts (E2 entry and each E8 loop-back), so the version being overwritten here is already recoverable as a `vNN`; do not additionally timestamp the deck, just overwrite `<base_name>_slides.pdf` with the latest. Insurance guard: if no `vNN` exists for this deck (no round-start capture ran this session), timestamp-copy the existing deliverable before overwriting.
4. Copy `slides.pdf` from the build folder as `<base_name>_slides.pdf` into the parent folder

This applies to all invocations (standalone and called by workflows). When a calling workflow provides an explicit content name that differs from the build directory base name, the calling workflow's name takes precedence.

**Example:**
```
my_project/                              <-- parent folder
  topic_a_slides.pdf                     <-- deliverable (auto-placed by beamer)
  topic_a_build/                         <-- build directory
    slides.tex
    slides.pdf
    outline.md
    figures/
    scripts/
```

**Confirm with the user; the report format depends on the active mode:**

- **Generate mode (invoked from a slides workflow):** "Beamer slides compiled and verified. Deliverable saved as `<base_name>_slides.pdf`." Do not offer PPTX here; the calling workflow owns the single end-of-turn PPTX offer, so offering again would double-ask.
- **Generate mode (standalone):** "Beamer slides complete. Deliverable saved as `<base_name>_slides.pdf`. If you want a PowerPoint version, say so (or `pptx this deck`); I will not ask again." Make this single offer once, at the end of the turn that produces the deck, and never re-raise it.
- **Edit / audit / pptx modes:** list every deliverable that exists in the output subdirectory (`<content_name>_slides.pdf`; `<content_name>.pptx` only if it was generated this session or already exists), point the user to the build folder for working files, and close with "Would you like to adjust anything else?"

**PPTX is offered at most once per deck, and never re-asked.** The single offer happens at the end of the turn that first delivers a newly generated deck (standalone generate mode above, or the calling workflow's own offer). Do not re-offer PPTX in the edit-mode iteration prompt (E8), in audit or pptx modes, in later edit turns, or in the session log. An unconverted deck is complete, not pending. If the user wants PowerPoint at any point, they request it explicitly ("pptx this deck" or `mode=pptx`).

### PPTX version snapshots (`vNN`)

The PPTX deliverable is version-snapshotted on the same `vNN` convention as the deck PDF, as its own independent series. `<base_name>.pptx` is always the latest; `<base_name> vNN <label>.pptx` are its preserved history. A PPTX `vNN` has no paired source file: the recompilable source for any PPTX version is the `.tex`/PDF `vNN` of the deck it was built from.

- **Number:** glob the output folder for `<base_name> v*.pptx`; next N = highest existing `vNN` + 1, zero-padded to two digits, `v01` if none. This is the PPTX's own counter, independent of the PDF's, because the PPTX is overwritten per conversion, not per `.tex` edit round.
- **Label:** `v01` = `structure-<x> register-<y>` (the deck's generate-time structure and register); `v02`+ = a 1-3 word descriptor of the change that defined the version being preserved (reuse the deck-change label from the round that produced it, or a brief `reconvert` tag).
- **When it fires:** before any overwrite of `<base_name>.pptx` (a re-conversion, or applying conversion-audit fixes), preserve the existing `<base_name>.pptx` as the next `vNN`. Idempotency guard: if the existing `<base_name>.pptx` is already byte-identical to the newest `<base_name> v*.pptx` (`cmp -s` matches), do not mint a duplicate; just overwrite. The Edit Mode E2 entry check applies this same guard, so an unchanged PPTX does not spawn identical milestones across edit rounds.

**PPTX conversion:** When converting to PowerPoint, follow the Beamer-to-PPTX Conversion Workflow in `../../style-guides/pptx/style-guide.md` exactly. This includes reading the .tex source and PDF, creating a per-slide conversion plan with native/hybrid/image categorization, presenting the plan for approval, using all font size specifications (22pt body floor with role-based floors for citations and labels, 14pt table/chart floor), calling the quality check function before saving, and fixing all reported issues before the file is written. Do not write ad-hoc conversion code that bypasses this workflow.

### PDF-vs-PPTX Conversion Audit (optional, offered after every PPTX conversion)

After the PPTX is saved, **always offer** a comparison audit:

> "Run a PDF-vs-PPTX conversion audit? This compares the compiled Beamer PDF against the saved PPTX slide-by-slide and reports text, chart, table, and image divergences. Report-and-ask only, no auto-fix. Adds about 2 to 5 minutes. (yes / skip)"

If the user picks `skip`, proceed to the Session Log.

If the user picks `yes`:

1. **Launch a comparison agent** (Agent tool, `subagent_type: general-purpose`) on a strong model. The audit is exhaustive rule-application across slides, the same rationale as the Compilation Cycle Step 3 audit tier. The agent prompt must include the absolute path to the compiled Beamer PDF, the absolute path to the saved PPTX, the comparison dimensions below, and the report format below.

2. **Comparison dimensions the agent checks slide-by-slide:**
   - **Slide count match.** PDF and PPTX have the same number of slides; report any extra or missing slides with their positions.
   - **Slide title match.** The frametitle in the PDF appears as the slide title in the PPTX (verbatim or with the same words).
   - **Body text content.** Every body bullet, paragraph, and callout in the PDF appears in the PPTX. Watch for truncations, dropped bullets, and reflowed content.
   - **Numeric content.** Every number, percentage, dollar amount, year, citation date, statistical value, and coefficient in the PDF appears in the PPTX with the same value. This catches the most consequential conversion defects (for example, "47%" rendered as "4.7%", or "$1.2B" as "$1.2M").
   - **Table contents.** Every table cell in the PDF appears in the PPTX with the same value, including header and footnote rows.
   - **Chart values.** For pgfplots and matplotlib charts, the bar heights, line points, labels, and axis ranges in the PPTX render match the PDF. The agent extracts chart values from `python-pptx` (native chart) or compares visually (image embed).
   - **Image presence.** Every `\includegraphics{}` figure in the PDF appears in the PPTX at the correct slide position.
   - **Citation footers.** Every footer citation in the PDF appears as a footer text box in the PPTX.
   - **Color palette.** Spot-check that key colored elements (headers, callouts, row shading) carry the correct palette colors from the style guide.

3. **How the agent does the comparison.**
   - Read the PDF with the Read tool (in chunks for long decks via the `pages` parameter).
   - Use `python-pptx` to extract text, table cells, chart data, and image references from the PPTX programmatically (cheap and exact for text content).
   - For visual content (chart appearance, image placement, color correctness): render the PPTX to PDF via `soffice --headless --convert-to pdf "<pptx_path>" --outdir "<build_dir>"` and read the resulting PDF page-by-page alongside the Beamer PDF. Reuse any verification PDF the conversion already produced.
   - Cross-reference every dimension above against the matching slide in both formats.

4. **Report format.** The agent returns a numbered findings list, one entry per divergence, with the slide number, dimension, what was in the PDF, what was in the PPTX, and a one-line proposed fix:

   > **PDF-vs-PPTX Audit: [N] divergences found:**
   >
   > 1. **Slide 7** (numeric content): PDF shows "47% adoption rate"; PPTX shows "4.7%". Likely a decimal-point insertion during text extraction. Fix: edit the slide 7 text run in the PPTX to read "47%".
   > 2. **Slide 12** (table contents): PDF table row 3 column 2 reads "$1,247M"; PPTX cell reads "$1,247". Trailing "M" dropped. Fix: append "M" to the cell.
   > 3. **Slide 15** (chart values): PDF bar chart shows bars at [12, 24, 36, 48]; PPTX shows [12, 24, 36, **45**]. Fix: set chart series position 4 to 48.

   If the agent finds zero divergences, it reports: `PDF-vs-PPTX Audit: all [N] slides match. No divergences found.`

5. **Present findings and ask.** After the agent returns, present the numbered list to the user and ask:

   > "How would you like to handle these? Apply all fixes, pick per-finding (list numbers), or skip and accept the current PPTX as-is?"

   - **Apply all:** re-run the PPTX conversion workflow with the findings list as input, or apply scoped text and cell edits directly via `python-pptx`. Preserve the prior PPTX as its next `vNN` (per "PPTX version snapshots" above) before re-saving.
   - **Per-finding:** prompt the user for the comma-separated numbers; apply only those.
   - **Skip:** report "Accepted PPTX as-is" and proceed to the Session Log.

6. **After fixes are applied,** re-run the comparison audit once and report whether all selected findings are resolved. If any remain (rare; usually because the proposed fix was wrong or introduced a new divergence), report them and ask again, same loop. Cap at two re-run passes; on the third, report the residual findings and ask the user to handle manually.

This audit is offered after **every** PPTX conversion regardless of mode (generate, edit, audit, pptx). It is the only place in this skill where audit findings are presented for user approval rather than auto-fixed; conversion divergences are often judgment calls (LaTeX-versus-Office rendering drift on subtle visual elements may not be a defect), so the user is the right decider.

---

## Session Log

After the deliverable is confirmed (and after optional PPTX conversion), append a session log entry to `CLAUDE.local.md` in the project root (the parent of the build directory). If `CLAUDE.local.md` does not exist, create it with a header first.

**Entry contents:**
```markdown
## [YYYY-MM-DD] - Beamer slides: [topic/description]
- **Skill:** beamer
- **Files created/modified:** [build directory path, slides.pdf deliverable path, PPTX if generated]
- **Key decisions:** [source content used, slide count, structure and register (for example, `structure=mba register=business`), any notable design choices]
- **Status:** complete
- **Next steps:** [none, or note if user mentioned future edits]
```

**PPTX is not a tracked deliverable.** Do not record PPTX conversion as pending, deferred, or "offered, not yet run" in the session log, and do not carry it into a handoff's next steps. An unconverted deck is complete. PPTX is produced only on an explicit user request; per the standing rule above, the single offer happens at delivery and is never re-asked.

**Handoff trigger:** If this session involved troubleshooting (Step 4 Fix and Recompile was used, or multiple compilation rounds were needed), ask:

> "This session involved troubleshooting. Write a handoff for the next session?"

If the session was a clean single-pass compilation, do not ask. Just log the entry silently.
