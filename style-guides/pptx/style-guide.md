# PowerPoint Style Guide

Apply this style guide when creating PowerPoint presentations. Follow all specifications exactly.

This guide is a five-file bundle. This file carries the rules; the code that enforces them lives beside it:

| File | Role |
|------|------|
| `style-guide.md` | The rules (this file). Read in full before generating any PPTX. |
| `pptx_lib.py` | Shared helper library: layout constants, palette, and every helper named in this guide. Import it; never re-type helpers into a deck script. |
| `quality_check.py` | The pre-save structural quality check (`run_quality_check()`), importable or runnable from the CLI on a saved deck. |
| `generator_template.py` | The canonical generator scaffold. Copy it as the starting point for every new deck script. |
| `conversion-workflow.md` | The Beamer-to-PPTX conversion procedure. Loaded in addition to this file for conversions only. |

## Note on Body-Text Color Across Media

The accent palette in this style guide matches the Beamer style guide exactly. **Body text differs intentionally:** PPTX uses Charcoal `#4D4D4D`, while Beamer uses CharText `#3A3A3A` (slightly darker). The rationale: PowerPoint output is typically projected via screen-mirror or shared in PDF viewers where `#3A3A3A` reads as visually heavy on backlit displays; LaTeX-rendered PDFs are typically printed or viewed at higher contrast where `#3A3A3A` reads correctly. If you generate a deck via Beamer and later convert to PPTX (or vice versa), expect body text to shift slightly between the two outputs. This is by design.

## Critical Rules (Most-Violated, Read First)

These rules are violated in nearly every PPTX generation. They override any conflicting code example or default assumption elsewhere in this file.

1. **Font size is role-based and computed, never a floor written as a literal.** Text must match the role-to-size hierarchy below. A single flat floor is wrong; citations legitimately use 11pt and diagram micro-labels use 14-16pt, while body text must stay at 22pt+. For every text element, compute the largest size in the role's range that fits the box (`fit_font_size()` in `pptx_lib.py`), then clamp at the role floor; a floor is what the computed size may not go below, never the size you assign. A generator that writes `size=22` as the default for every body run is the uniform-at-floor defect the quality check blocks. See "Role-Based Font Hierarchy" below.
2. **All readable text uses Charcoal (#4D4D4D).** Never use #B0AFA8 (MedGray) or #6C7A89 (Medium Gray) on body text, labels, headings, date labels, or any element that must be readable when projected. #B0AFA8 is exclusively for citation text boxes (`add_citation()`). #6C7A89 is for connector lines and neutral shape outlines only.
3. **No inline source references.** Present findings as factual statements. Author attribution goes exclusively in `add_citation()` text boxes at the canonical citation band (T=8.00"). Never write "Smith et al. (2024) found that..." in body text.
4. **Citations at canonical position only.** L=1.10", T=8.00", W=13.80", H=0.25", 11pt Calibri non-italic, #B0AFA8, right-aligned. Multi-line citations grow upward (H=0.50 at T=7.75; H=0.75 at T=7.50), never downward. Use `add_citation(slide, text, lines=N)`.
5. **The quality check is mandatory and blockers must be fixed.** Run `run_quality_check(prs)` before every `prs.save()`. Fix all errors (not just warnings) before saving.
6. **Native objects, not image embeds.** Colored boxes, flowcharts, box-and-arrow diagrams, tables, and standard charts must be recreated as native PowerPoint objects. Image embed is a last resort for irreducible visual complexity (Bezier curves, mathematical plots). If you are about to embed a full-slide image, stop and reclassify.
7. **Lock shape dimensions with `auto_size = MSO_AUTO_SIZE.NONE` on every text-containing text frame.** Every shape or text box that holds text (rounded rectangles with labels, cards, citations, text boxes, callouts) must explicitly set `text_frame.auto_size = MSO_AUTO_SIZE.NONE` immediately after the shape is created. python-pptx defaults vary by shape type, and Keynote's PDF export silently resizes auto-sized shapes (cards misalign, text frames grow beyond their coded height). Coded dimensions are only honored when `auto_size` is locked. Bake this into every wrapper helper (`add_rounded_card()`, `add_citation()`, direct `add_textbox()` calls). **Exempt:** purely decorative shapes that contain no text (e.g., a thin accent sliver or a background rectangle) do not need `auto_size` locked; there is nothing to resize. Also exempt: chart title/axis frames managed by python-pptx's chart API, and the Title placeholder provided by the template.
8. **Prevent PowerPoint "repaired and removed content" warnings.** python-pptx generates two structures that PowerPoint's strict validator flags as malformed; both must be neutralized in every PPTX:
   - **Auto-added `<p:style>` block on autoshapes.** When `add_shape()` creates a rounded rectangle (or any preset autoshape), python-pptx attaches a `<p:style>` element that references theme scheme colors (accent1, lt1, etc.). When the generator also sets explicit RGB fill and line via `spPr` (which `add_rounded_card()` does), PowerPoint sees the conflict and silently strips shapes during repair. **Fix:** remove the `<p:style>` element from the shape after `add_shape()` returns. `add_rounded_card()` does this automatically; if you create a custom autoshape helper with explicit fills, do the same.
   - **`<a:buChar>` without a paired `<a:buFont>`.** PowerPoint requires a typeface to render the bullet character. `set_bullet()` adds `<a:buFont typeface="Arial"/>` immediately before `<a:buChar>` to satisfy the schema. Do not write a custom bullet helper that emits only `<a:buChar>`.
   These regressions surface as "PowerPoint couldn't read some content - Repaired and removed it" on file open, which silently drops shapes the user expects to see. Both checks are enforced by `run_quality_check()` (see "Pre-Save Structural Quality Check"). Do not bypass either guard.
9. **Render via `soffice --headless`, never PowerPoint AppleScript except as documented fallback.** When converting a saved PPTX to PDF for review, audit, or sharing, the canonical render command is `soffice --headless --convert-to pdf "<deck.pptx>" --outdir "<dir>/"`. PowerPoint AppleScript is permitted **only** when LibreOffice has already been run and produced a defect that the code says should not be there. No LibreOffice attempt means no basis for the fallback, so no PowerPoint launch. See "Rendering for Review" for the full canonical path and the documented fallback procedure.
10. **When the user specifies a base PPTX, that file is the destination, not a source.** A splice that pulls the user's base into a clean template file loses the base's slide master, theme, layouts, animations on untouched slides, and embedded media references. Start the working file as a copy of the base, then append the new slides into it. Reserve the clean template only for first-time generation where no user base exists. The reflex to "start clean for style consistency" is the wrong tradeoff: the base's master is what carries the visual identity the user is asking you to preserve.

### Role-Based Font Hierarchy

Every text element on a slide has a role. Match the role to its target font size. Floors are blocking; above-target is acceptable if the content warrants emphasis.

| Role | Target | Floor (blocking) | Typical position/shape |
|---|---|---|---|
| Title | 36pt | 32pt | Title placeholder, T≈0.33", H≈1.49" |
| Category header (section label in a box) | 32pt | 28pt | Top of a rounded rectangle or column |
| Body primary (main text audience reads) | 24-28pt | 22pt | Bullet lists, paragraph body |
| Body secondary (supporting text, sub-bullets) | 22pt | 20pt | Continuation text, inset bullets |
| In-shape label (word inside a diagram node, row/column label) | 18-22pt | 16pt | Rounded rectangles or label boxes <3.5"W and <1.2"H, connector nodes |
| Diagram micro-label (connector annotation) | 14-16pt | 12pt | Small text boxes <2.5"W and <0.6"H |
| Chart axis, legend, data labels | 14pt | 14pt | Inside charts (handled by `fix_chart_fonts()`) |
| Chart caption (figure support line below a figure) | 22pt | 18pt | Left-aligned at figure width; computed up to 22pt, floor 18 (see "Chart captions"). Tagged `FigCaption` by `add_caption()` |
| Chart annotation (short label beside a chart) | 12pt | 11pt | Short label adjacent to a chart |
| Citation | 11pt (fixed) | 11pt | Canonical citation band, T=8.00" |
| Footer, slide number | Template default | Template default | Footer placeholder |

Shape-size signals the role. A text box narrower than 2.5" and shorter than 0.6" is an annotation, not body text: allow down to 14pt. A text box occupying most of the slide width (>10") with standing multi-line content is body: floor at 22pt. Citations are identified by position (T between 7.5 and 8.25, H ≤ 0.80). A figure caption is the left-aligned support line directly below a chart or figure; it is tagged `FigCaption` (set by `add_caption()`) and held to the caption role (floor 18pt), one tier above the 11pt citation.

**Compute the size, then clamp (mandatory).** For each text element: start at the role's target ceiling (28pt for body primary), use `estimate_text_height()` to step down until the content fits the box, and apply `max(computed, floor)`. `fit_font_size()` in `pptx_lib.py` implements this; compute the size at the call site and pass the result as `size=`. Two guards so the computation cannot be gamed: the box itself must respect the content-area and grid-layout limits (a size only "fits" in a legitimately sized box, not an inflated one), and the overflow check still runs after sizing. The floor is reached only when content is already minimal; it is never the starting value.

When body content does not fit at its role's target, **reduce content**: split the slide, remove a bullet, condense phrasing. Never drop body text below 22pt. Symmetrically, when content sits far below its box capacity at the floor, the size was never computed: recompute upward toward the role ceiling rather than shipping small text in an under-filled box.

### Accent Colors on Card Category Headers

Card category headers (the label at the top of a rounded-rectangle card or column) default to **Charcoal** (`#4D4D4D`), matching body text. A palette accent color is appropriate when the card is **statistic-led**: its purpose is to surface a single headline number or short emphatic phrase, not to deliver prose.

| Card type | Header color | Example |
|---|---|---|
| Statistic-led (card leads with a large number or short emphasis) | Palette accent (DeepTeal, BurntOrange, SlateNavy, WarmAmber) | A three-card row showing "82%", "4.3x", "$1.2B" with short captions beneath |
| Content-led (card contains a paragraph, bullet list, or descriptive text) | Charcoal | A three-card row showing "Context", "Finding", "Implication" with explanatory text beneath |

This is positive guidance, not a blocking rule. Rule #2 (no grays on body text) remains the enforced floor; accent colors on statistic-led card headers are permitted above that floor.

---

## Typography

| Element | Specification |
|---------|---------------|
| Slide titles | 36pt Calibri Bold, #4D4D4D, in Title placeholder |
| Section headers within slides | 24-28pt Calibri Bold |
| Body text | **24-28pt target, 22pt floor** Calibri Regular, #4D4D4D (per the Role-Based Font Hierarchy, the canonical spec) |
| Minimum text size | Role floors per the Role-Based Font Hierarchy (body 22pt, body secondary 20pt, in-shape label 16pt; 14pt for chart axis labels and table content only) |
| Subtitles | NEVER use subtitles; title only, content below |

**Font size principle: compute the largest size that fits attractively, then clamp at the role floor.** The Role-Based Font Hierarchy in Critical Rules is the single canonical size spec; this table summarizes it and defers to it wherever they could be read to differ. Body text starts at its 24-28pt target and steps down via `fit_font_size()` only as the box requires; it reaches the 22pt floor only when content is already minimal (split the slide, remove a bullet, condense phrasing first). Never use 16pt or smaller for slide body text, and never write a floor value as a default.

## Layout Principles

- **Aspect ratio:** 16:9
- **Generous margins** and white space between elements
- **One main idea per slide**
- **Footer and citation zones:** Body content must stay above `CONTENT_BOTTOM = 8.00"`. The citation band occupies T=8.00 to T=8.25. The footer placeholder (slide number, copyright) occupies T=8.38 to T=8.86. On a 16x9 slide this gives 8.00 - 1.95 = 6.05" of content height below the title.
- **No title slide:** The template provides the title slide; never generate one

### Layout Selection

**Use the "Title Only" slide layout for every slide.** Do not use "Blank", "Title and Content", or any other layout. The title of every slide must be placed in the Title placeholder of the "Title Only" layout.

### Template File

Store a master `.pptx` template at a known path and set the `TEMPLATE_PATH` constant in `pptx_lib.py` to point to it. The template should carry the correct slide master, theme colors, fonts, footer placeholders, and the "Title Only" layout. **Always load this template** when initializing a new presentation. Do not use `Presentation()` (blank) when the template is available.

### python-pptx Implementation

Template loading, slide clearing, layout lookup, and title formatting are implemented in `generator_template.py` and `pptx_lib.py` (`remove_existing_slides()`, `add_title()`); start from the template rather than writing this setup by hand (see "Canonical Generator Template").

**Critical rules:**
- Always load the template file (never start from `Presentation()` blank if the template exists)
- Always clear pre-existing slides from the template before adding new ones
- Never use hardcoded layout indices; always find "Title Only" by name
- Never create a text box for the title; always use `slide.placeholders[0]`
- All slide content (shapes, charts, text boxes) goes below the title placeholder

### Hidden Slide Detection

PowerPoint's "Hide Slide" feature sets `show="0"` on the slide XML element. Use `is_hidden(slide)` / `set_hidden(slide)` in `pptx_lib.py` to detect and mark hidden slides when reading or editing existing PPTX files.

**Convention:** Hidden slides are treated as **presenter notes**, not visible to the audience. They typically appear before a title slide and contain background details, reading notes, or preparation context.

**Rules for hidden slides:**
- **When reading/analyzing a PPTX:** Detect hidden slides and label them as `[HIDDEN - presenter notes]`. Do not recommend replacing, redesigning, or removing them. Do not critique their content density, font sizes, or visual design. They are notes, not presentation material.
- **When editing a PPTX:** Hidden slides can be edited or added when requested. Use `set_hidden(slide)` to mark new notes slides. Hidden slides do not need to follow the style guide's visual rules (font targets, color palette, layout constants).
- **When converting or rebuilding:** Preserve hidden slides and their hidden status. Do not convert them to visible slides or merge their content into presented slides.
- **In the quality check:** Skip hidden slides entirely (they are not presented, so style compliance is irrelevant).

### Content Area Layout Constants

The template is **16" × 9"**. Use these exact constants for all content positioning; do not guess or derive from Beamer coordinates:

```python
# Slide dimensions
SLIDE_W = 16.0   # inches
SLIDE_H = 9.0    # inches

# Title placeholder (from template — do not change)
TITLE_LEFT = 1.10   # inches
TITLE_TOP  = 0.33   # inches
TITLE_W    = 13.80  # inches
TITLE_H    = 1.49   # inches  (bottom edge at 1.82")

# Content area — use these for ALL shapes, charts, text boxes
CONTENT_LEFT  = 1.10   # left margin (aligns with title)
CONTENT_TOP   = 1.95   # just below title bottom (1.82" + 0.13" gap)
CONTENT_W     = 13.80  # full content width (aligns with title)
FOOTER_TOP    = 7.70   # do not place content below this line (footer zone)

# Derived: usable content height
CONTENT_H = FOOTER_TOP - CONTENT_TOP  # = 5.75 inches
```

These values are mirrored in `pptx_lib.py`; change both together.

Every shape, chart, and text box must fit within `CONTENT_LEFT` to `CONTENT_LEFT + CONTENT_W` horizontally, and `CONTENT_TOP` to `FOOTER_TOP` vertically. Content positioned outside these bounds will be clipped by the footer or pushed off the edge of the slide.

**Do not use arbitrary offsets.** Shapes must start at `CONTENT_LEFT = 1.10"` (or inset from it), not at `0.5"`, `0.8"`, `2.0"` or other guessed values. Column widths must sum to `CONTENT_W = 13.80"` minus any gap, not to arbitrary narrower widths.

## Complete Color Palette

These values are mirrored in `pptx_lib.py`; change both together.

### Accent Colors (for outlines and emphasis)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Primary accent | DeepTeal | #0D7377 | Primary accent for outlines, headers, emphasis |
| Secondary accent | Cyan Blue | #0077B6 | Theory, models, formulas, technical content |
| Tertiary accent | Dusty Plum | #9B5978 | Third accent for charts, diagrams, general emphasis |

### Fill Colors (use white text on all fills)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Primary fill** | SlateNavy | #1B2A4A | Block titles, emphasis boxes within diagrams, dark-background slides |
| Alert fill | WarmAmber | #E8913A | Alert blocks, highlighted annotations |
| Positive fill | Green | #27AE60 | Positive outcomes, solutions, "after" states |
| Warning fill | Soft Red | #DC5C5C | Warnings, errors, negative outcomes |
| Problem fill | Burnt Orange | #BF5700 | Problems, trade-offs, "before" states |
| Problem fill (severe) | AccentRed | #C0392B | Challenges, critical issues |

### Structural & Indicator Colors

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Primary text | Charcoal | #4D4D4D | All body text, titles |
| Default outline | Slate Blue | #425563 | Thin borders, divider lines, default outlines |
| Subtle backgrounds | PaleBlue | #E8F0F8 | Secondary containers, neutral boxes, alternating table rows |
| Light background | LightGray | #F0EFEC | Spare light fill |
| Neutral connector | Medium Gray | #6C7A89 | Neutral states, connectors, transitions |
| Background | White | #FFFFFF | Main slide background |

## Color Application Rules

### Colors Per Slide
- **Target:** 3 accent colors per slide (beyond black, gray, white)
- **Maximum:** 4 colors when necessary for clarity

### Filled Content Boxes
- **Primary fill:** SlateNavy (#1B2A4A) with white text for block headers and emphasis boxes
- **Alert fill:** WarmAmber (#E8913A) with white text for alert blocks, highlighted annotations
- **Positive fill:** Green (#27AE60) with white text for solutions, "after" states
- **Problem fill:** Burnt Orange (#BF5700) with white text for problems, trade-offs, "before" states
- **Problem fill (severe):** AccentRed (#C0392B) with white text for critical issues
- **Warning fill:** Soft Red (#DC5C5C) with white text for errors, warnings

### Outlined Content Boxes
- **Default outline:** Slate Blue (#425563) for standard content boxes
- **Accent outlines:** DeepTeal (#0D7377), Cyan Blue (#0077B6), or Dusty Plum (#9B5978)

## Visual Elements

### DO
- Use solid color-blocked rectangles with rounded or square corners
- Keep icons and graphics flat, vector, high-contrast
- Use accent bars (thin vertical rectangles) for left-edge emphasis
- Use SlateNavy (#1B2A4A) as primary fill for block titles, in-diagram emphasis boxes, and standalone reinforcement callouts; recreate callouts as editable filled text boxes, used selectively as in the source, not on every slide
- Stick to 3 colors per slide, expand to 4 only when needed

### DON'T
- Use gradients, glows, drop shadows, or bevels on any element (text, shapes, charts, images)
- Use text shading, text highlighting, text background fills behind running text, or text shadows (a deliberate reinforcement callout box, a filled shape with its own text, is not a text background fill and is permitted)
- Add subtitles under titles
- Clutter slides with too many elements
- Use more than 4 accent colors on a single slide
- Forget to leave footer space at the bottom
- Create title slides (template provides these)
- Embed charts as images when they can be recreated as native PowerPoint charts

## Beamer-to-PPTX Conversion (module)

The full Beamer-to-PPTX conversion procedure lives in `conversion-workflow.md` in this folder: the workflow Steps 1-4 (source read, per-slide categorization, image-embed decision rules, callout conversion, filename rule, plan-approval checkpoint), the Font Size Rule for Conversion, source-citation extraction, chart number formatting, chart/diagram source-matching, and chart data fidelity. A conversion reads this file (core) AND `conversion-workflow.md` in full before writing any code; direct PPTX generation does not load the module. The code helpers are imported from `pptx_lib.py` and `quality_check.py`, never re-typed.

## Source Citation Handling

Every source citation in the Beamer source (e.g., a `\sourcecite{}` footer macro) must be carried over to the PPTX as a citation text box. Citations are not optional content; they are part of the slide.

**Canonical placement:** Fixed position at `L=1.10", T=8.00", W=13.80", H=0.25"` on a 16x9 slide. The citation band sits above the footer strip (footer placeholder occupies `T=8.38"` to `T=8.86"`). Right-aligned text within the full-width box.

**Canonical formatting:** 11pt Calibri non-italic, color #B0AFA8, right-aligned.

**Multi-source citations:** Separate sources with `; ` (semicolon space). Target a single line. If text would wrap, grow the box **upward** (reduce `T` while keeping the bottom edge fixed at `T + H = 8.25"`) so the citation never enters the footer strip.

| Lines | T | H |
|---|---|---|
| 1 | 8.00 | 0.25 |
| 2 | 7.75 | 0.50 |
| 3 | 7.50 | 0.75 |

**Implementation:** `add_citation(slide, text, lines=N)` in `pptx_lib.py` is the single required path; it bakes in the canonical position, upward growth, formatting, and the `auto_size` lock (rule #7).

**Extraction from a Beamer source:** the citation parsing and line-count estimation rules are in `conversion-workflow.md` ("Source citation extraction").

## Vertical Text Alignment

Vertical alignment is set by the shape's role, deterministically:

- **Body, prose, and multi-paragraph cards → TOP.** Set `text_frame.vertical_anchor = MSO_ANCHOR.TOP`. python-pptx defaults rounded rectangles to middle, which pushes prose down from the top edge and creates uneven spacing, so set TOP explicitly on every body shape.
- **Label-role shapes → MIDDLE.** A short diagram, cycle, or connector label in a small box (the `in-shape label` role: width < 3.5" and height < 1.2") is vertically centered: `text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE`. This holds even when the label wraps to two or three lines; a centered multi-line label is correct, not a defect. `add_rounded_card(..., role='label')` sets MIDDLE for you.

**Implementation:** `add_rounded_card()` and `add_body_textbox()` in `pptx_lib.py` set the anchor (and the rule #7 `auto_size` lock) by role; on a raw `add_textbox()` set `tf.vertical_anchor` explicitly.

The quality check enforces this split: check #9 flags MIDDLE only on **body-role** shapes (a prose column that should be TOP). Label-role, micro-label, and caption shapes are exempt, because MIDDLE is their intended setting. Build labels with `add_rounded_card(..., role='label')` (or set `MSO_ANCHOR.MIDDLE` explicitly on a label-role text box), and keep TOP for any box holding a heading plus body text, multi-paragraph prose, or bullet lists.

## Text Box Consolidation

Related text content on a slide must go in **one continuous text box** with paragraph-level formatting, not split into multiple separate text boxes.

**Rule:** When a Beamer slide has a text column containing a heading followed by bullet points (or multiple formatted paragraphs), recreate this as a single text box with multiple paragraphs. Use paragraph-level properties for differentiation:

- **Section headers within a text box:** Bold run, 20-24pt
- **Bullet points:** Normal weight, 22pt (drop to 20pt if density requires), with `paragraph.level` set to create indent
- **Sub-bullets:** 20pt, `paragraph.level = 1` for additional indent
- **Spacing between sections:** Use `paragraph.space_before = Pt(12)` to separate logical sections within one text box

**Do not** create separate text boxes for a heading and its bullets, or for each bullet point individually. A single text column should be ONE text box with multiple paragraphs.

**Implementation:** build the box with `add_body_textbox()` and stack paragraphs with `add_paragraph()` (both in `pptx_lib.py`, with header/bullet/spacing options); `generator_template.py`'s example slide shows the header-plus-bullets pattern.

## Bullet Preservation

When the Beamer source uses `\begin{itemize}` or `\begin{enumerate}`, the PPTX must reproduce those as native PowerPoint bullets or numbered lists, not as plain text with dashes or asterisks.

**Implementation:** use `set_bullet(paragraph, level=N)` in `pptx_lib.py` (or `add_paragraph(..., bullet=True)`, which applies it plus the hanging indent). It always pairs `<a:buFont typeface="Arial"/>` with `<a:buChar/>`; PowerPoint flags `<a:buChar>` alone as malformed and strips the bullet during repair (Critical Rule 8). For enumerated lists, emit `<a:buAutoNum type="arabicPeriod"/>` instead of `<a:buChar>` (same paired-element discipline).

## Bullet Indentation (Hanging Indents)

All bullet lists must use hanging indents. Continuation lines align under the text start, not under the bullet marker. python-pptx does not create hanging indents automatically; the paragraph properties `marL` (left margin) and `indent` (negative for hanging) must be set explicitly via XML. `set_hanging_indent(paragraph)` in `pptx_lib.py` does this (defaults: 0.30" margin, -0.25" indent).

Apply `set_hanging_indent()` to every bullet paragraph. The pre-save quality check flags bullet paragraphs without an explicit `indent` attribute set.

## Source Attribution

Never reference authors by name in slide body text (e.g., "Brynjolfsson et al. (2023) find that..."). Present findings as factual statements in the body and attribute the source exclusively via `add_citation()` at the bottom of the slide. This mirrors the Beamer source-citation footer rule.

---

## Charts

Chart rules shared by direct generation and conversion. Conversion-only chart content (source-matching, chart number formatting, and chart data fidelity) is in `conversion-workflow.md`.

### Chart font sizes: mandatory XML fix

python-pptx generates charts with hardcoded small font sizes (10-12pt) embedded in `<c:txPr>/<a:defRPr sz="...">` elements. These are never overridden by general style settings. **You must explicitly fix them for every chart:** call `fix_chart_fonts(chart_shape.chart)` in `pptx_lib.py` immediately after `add_chart()`.

Target sizes:
- Axis tick labels: **14pt** (cannot be 18pt, but must be readable, not 10-11pt)
- Legend text: **14pt**
- Data labels: **14pt**
- Do NOT modify `chartSpace` txPr (that controls the chart title default)

### Chart legend rules

**Line charts:** Legend always on the **RIGHT** (`XL_LEGEND_POSITION.RIGHT`), outside the plot area.

**Bar/column charts:** Legend on **TOP** or **RIGHT**; match the Beamer source. If the bar chart has a callout or annotation box below the chart, ensure the legend does not overlap it.

**All charts:** `include_in_layout = False` (legend sits outside plot area, does not shrink it).

```python
from pptx.enum.chart import XL_LEGEND_POSITION

chart.legend.position = XL_LEGEND_POSITION.RIGHT   # line charts always
chart.legend.include_in_layout = False
```

### BAR_CLUSTERED clipping risk

Horizontal bar charts (`BAR_CLUSTERED`, `BAR_STACKED`) can clip the first and last bars depending on chart height, series count, and axis default settings. python-pptx does not auto-pad the category axis. If clipping occurs in the rendered output (first or last category's bar cut off at the plot edge), either:

- Switch to `COLUMN_CLUSTERED` (vertical bars), which eliminates the failure mode entirely and is often visually stronger anyway when category labels are short
- Or explicitly configure category-axis padding via the chart's plot area / axis range settings

This is format-geometry-dependent, not a category-count rule: 5 categories may clip at one chart height and render fine at another. Verify by rendering the PPTX to PDF and inspecting the first/last bars in every horizontal bar chart.

### Bar charts with negative values

When a bar/column chart contains series with negative values, explicitly disable `invertIfNegative` to preserve the fill color for negative bars. If this is not set, PowerPoint defaults to inverting the fill (bars appear white or unfilled). Call `fix_invert_if_negative(chart)` in `pptx_lib.py` on every bar/column chart whose data contains negative values.

### Chart captions
Every chart or diagram that has a caption or figure label in the source **must** include that caption as a text box directly below the chart in the PowerPoint slide. Do not omit captions. The caption is **left-aligned** at the chart's width, **upright**, Charcoal, at the **caption size (computed up to 22pt, floor 18; see Role-Based Font Hierarchy)**, with **no function-announcing run-in head** ("How to read:", "Note:"). A left-aligned source caption must never be recreated centered. Color-key terms only when the caption decodes a color-coded chart.

**Implementation:** Use the mandated `add_caption(slide, figure_shape, text)` helper in `pptx_lib.py`. It computes the caption size in [18, 22] with `fit_font_size(role='caption')`, sizes the box from the wrapped text, left-aligns at figure width, sets Charcoal non-italic, and tags the shape `FigCaption` so the quality check classifies it as a caption however it wraps. Do not hand-roll a caption text box with a literal point size; a typed `Pt(11)` is the defect this replaces. `add_caption()` is the caption analog of `add_citation()`: the single required path for every figure caption.

**Verification step:** After generating the PPTX, scan every slide that contains a chart or figure. Cross-reference against the `.tex` source to confirm every figure caption present in Beamer is represented as a left-aligned caption text box at chart width in the corresponding PowerPoint slide. Flag any slide where a caption is missing and add it before saving the final file.

### Use images only as a last resort
Only embed a chart or diagram as an image when it is too complex to accurately reproduce in PowerPoint (e.g., multi-layered TikZ diagrams with custom paths, complex mathematical annotations, or highly customized pgfplots with dozens of overlays). When embedding as an image, export at high resolution (300+ DPI).

**Image positioning (mandatory):** All embedded images must fit proportionally within the content area. **"Fill the content area" means fit proportionally within, centered horizontally, top-aligned; never stretch an image to fill the full width and height regardless of its native aspect ratio.** This applies to all embedded image types: paper figures, charts exported as images, photographs, and interface screenshots.

PIL/Pillow is an assumed dependency for all image handling. Install if needed: `pip3 install Pillow`.

Use `add_image_proportional(slide, img_path, area_left, area_top, area_w, area_h)` in `pptx_lib.py` for all embedded image placement. The four worked placement patterns (full-width figure, figure with caption below, two images side by side, hybrid text-plus-image columns) are in `generator_template.py` as commented examples.

**Never** position images at hardcoded offsets like `left=2.0"` or size them with explicit `width` and `height` that ignore the native aspect ratio. Every embedded image (paper figures, photographs, chart screenshots) must go through `add_image_proportional()`.

## Tables

### Cell alignment
- **Header row:** center-align text, bold, set explicit font size (16pt minimum; prefer 16-18pt for table content)
- **Data rows:** center-align numbers; left-align labels/text in the first column if the table has a label column
- **Never rely on default alignment;** always call `para.alignment = PP_ALIGN.CENTER` or `PP_ALIGN.LEFT` explicitly

### Font in table cells: mandatory XML fix

Table cells do NOT inherit slide defaults, and the python-pptx API (`run.font.size`) alone is insufficient. It only sets the run-level `<a:rPr>` but misses empty cells that have no runs, and can be overridden by paragraph defaults. **Always call `fix_table_fonts(table_shape, size_pt=18, align='ctr')` in `pptx_lib.py` after populating any table.** It sets font size and alignment on every cell via XML (paragraph defaults plus explicit run properties).

Target: **18pt** for all table text. Use 14pt only when a table has dense content that genuinely cannot fit at 18pt.

### Table style: mandatory XML fix

python-pptx's `add_table()` produces a table whose `<a:tableStyleId>` is the **null GUID** `{00000000-0000-0000-0000-000000000000}`. This GUID **crashes LibreOffice 26 on PPTX import** (confirmed 2026-05-06 on controlled variants). Setting a real built-in style GUID avoids the crash. The canonical safe choice is `{2D5ABB26-0587-4C30-8999-92F81FD0307C}` ("No Style, No Grid"), which provides no visual styling and does not override cell-level paragraph alignment.

Two GUIDs are forbidden:
- `{00000000-0000-0000-0000-000000000000}` (null): crashes LibreOffice 26.
- `{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}` ("Medium Style 2 - Accent 1"): silently overrides `para.alignment = PP_ALIGN.CENTER` and similar cell-level specs.

Call `fix_table_style(table_shape)` in `pptx_lib.py` after `add_table()` and `fix_table_fonts()`; it sets the canonical safe GUID.

### Table positioning
Tables must start at `CONTENT_LEFT = 1.10"` and span `CONTENT_W = 13.80"` (full content width) unless there is a side-by-side chart or other content. In that case, scale the table and chart proportionally to together fill the full content width. Never let a table float to the right or center at a narrower width than the surrounding shapes.

## Multi-Box Layouts

When a slide has 2 to 4 equal-sized boxes side by side:
- **All boxes must be equal width**
- **The group must fill the full content width** (`CONTENT_W = 13.80"`)
- **Gap between boxes:** 0.5"
- **Formula:** `box_w = (CONTENT_W - (n - 1) * 0.5) / n` where n = number of boxes

```python
n = 3  # or 2, or 4
GAP = 0.5
box_w = (CONTENT_W - (n - 1) * GAP) / n   # e.g. n=3: 4.267"

for k in range(n):
    left = CONTENT_LEFT + k * (box_w + GAP)
    # add_shape(left=Inches(left), width=Inches(box_w), ...)
```

Never create boxes of unequal widths unless the content explicitly requires different sizes (e.g., a 60/40 comparison layout). Never leave a gap on the right side of the slide (the last box should end at `CONTENT_LEFT + CONTENT_W = 14.90"`).

## Content Fitting

python-pptx provides no API to measure rendered text height. Text that overflows a shape is invisible in code but renders as clipped or overlapping content in PowerPoint. **Always estimate text height before assigning box dimensions.**

### Text-Height Estimation

Use `estimate_text_height(text, box_width_inches, font_size_pt)` in `pptx_lib.py` (the same estimate `run_quality_check()` uses to detect overflow after the fact).

**Usage during generation:** Before creating a text box or content box, estimate the height needed for its text. If the estimated height exceeds the allocated space, reduce content or change the layout before writing any shapes. `fit_font_size()` builds on it: compute the largest in-role size whose stacked estimated height fits the box, then clamp at the role floor.

### Grid Layout Limits

Grid layouts (2x2, 2x3, 3x2) with content boxes are constrained by `CONTENT_H = 5.75"`. Apply these rules:

| Grid | Max rows | Row height (approx) | Content per box |
|------|----------|---------------------|-----------------|
| 2 boxes (1 row) | 1 | 5.50" | Full paragraphs OK |
| 3 boxes (1 row) | 1 | 5.50" | Full paragraphs OK |
| 4 boxes (2x2) | 2 | 2.50" | 2-3 short lines at 20pt |
| 6 boxes (2x3 or 3x2) | 2 | 2.50" | 1-2 short lines at 20pt |

**Rules:**
1. **Never use paragraph-length descriptions in 2-row grids.** At 20pt in a 4.27"-wide box, one line holds ~14 characters. A 100-character description needs ~7 lines (~2.7"). A 2.50" box cannot hold it.
2. **If descriptions exceed 2 lines per box, switch layout:** use a bulleted list, a table, or split across slides.
3. **Stat callout boxes** (large number + short label) work in grids. Stat boxes with explanatory paragraphs do not.
4. **Always run `estimate_text_height()` on the longest box's content** before committing to a grid layout. If any box overflows, the layout is wrong.

## Slide Structure Patterns

### Standard Content Slide
1. Title in placeholder (36pt Calibri Bold, #4D4D4D); the title IS the key message
2. Bullet points or content area, starting directly below the title placeholder
3. Optional visualization or supporting graphic
4. Blank space at bottom for footer

### Comparison Slide
- Two or three **equal-width** boxes side by side, filling CONTENT_W
- Use contrasting colors to differentiate options
- Limit to 3 colors total (e.g., outline + two fills)

### Progression Slide
- Three **equal-width** boxes showing stages, filling CONTENT_W
- Color progression: Medium Gray outline → Burnt Orange fill → Green fill
- Shows evolution from neutral → active → positive

### Summary Slide
- May use up to 4 colors for different categories
- Four-box layout for strategic frameworks

## Canonical Generator Template

**Start every generator from `generator_template.py` in this folder.** Copy it, replace the example slide section with the deck's real content, and keep its structure (template load, `remove_existing_slides()`, "Title Only" layout lookup, per-slide build, quality gate, save). It imports `pptx_lib.py`, whose helpers encode this guide's rules (auto_size locked, Charcoal default, canonical citation band, hanging indents, chart/table XML fixes, compute-then-clamp sizing via `fit_font_size()` / `ROLE_RANGES`). **Do not re-implement helpers inline**; import them, and do not edit the lib's function bodies without a clear reason.

**Extension guidance:**

- For charts, call `fix_chart_fonts(chart)` immediately after `add_chart()` (see "Charts" for axis/legend rules), and `fix_invert_if_negative(chart)` on bar charts with negative values.
- For tables, use `add_table()` then call `fix_table_fonts()` and `fix_table_style()` (see "Tables").
- For multi-column layouts, compute column widths from `CONTENT_W` using the formula `(CONTENT_W - (n-1)*GAP) / n` (see "Multi-Box Layouts").
- For multi-line citations, pass `lines=2` or `lines=3` to `add_citation()`.
- If a body shape needs `MSO_ANCHOR.MIDDLE` (single-line label), use `add_rounded_card(..., role='label')` or set `tf.vertical_anchor = MSO_ANCHOR.MIDDLE` explicitly; do not remove the `auto_size = NONE` assignment.

## Pre-Save Structural Quality Check

**Run this check on every PPTX before calling `prs.save()`.** It catches the generation errors that are invisible to visual inspection of the code: overlapping or out-of-bounds shapes, hardcoded small fonts in chart XML, bad table style GUIDs, legend, color, alignment, and bullet violations, PowerPoint repair-warning triggers, text overflow, uniform-at-floor sizing, and box or caption under-fill.

The check lives in `quality_check.py` in this folder (the full `run_quality_check()` source, with its per-check docstring). Invoke it; never re-type it into a generator.

- **In a generator script (before save):**
  - `import sys; sys.path.insert(0, '<path to this style-guide folder>')`
  - `from quality_check import run_quality_check, report_and_exit`
  - `issues = run_quality_check(prs)` for direct generation; `issues = run_quality_check(prs, conversion_source='<path to slides.tex>')` for a Beamer conversion.
  - `report_and_exit(prs, issues)` prints the standard error/warning report and raises SystemExit on errors; then call `prs.save()`.
- **On a saved deck (CLI):** `python3 quality_check.py <deck.pptx> [--conversion-source <slides.tex>]` (nonzero exit when errors are found).

**Severity contract (a calling conversion workflow may parse these message strings; do not reword them):** `run_quality_check` returns a list of issue strings. Entries prefixed `WARNING:` do not block save; every other entry is an error that blocks save. The uniform-at-floor check (#18) is an ERROR at direct generation and a `WARNING ... room_count=N ...` message at conversion (`conversion_source` set), where `room_count` counts at-floor body shapes whose text area affords a larger size; a caller can key "fix in the PPTX" (`room_count>=1`) vs "reduce content, ask the user" (`room_count==0`) off that integer.

Fix every reported issue before saving. Do not skip or suppress the check. Common fixes:
- **Overlap**: adjust `top` or `height` of one of the overlapping shapes so bounding boxes no longer intersect
- **Out of bounds**: correct `left`, `top`, `width`, or `height` to fit within the content area constants
- **Chart fonts**: call `fix_chart_fonts(chart)` immediately after `add_chart()`
- **Line legend**: set `chart.legend.position = XL_LEGEND_POSITION.RIGHT` and `include_in_layout = False`
- **invertIfNegative**: call `fix_invert_if_negative(chart)` to set `<c:invertIfNegative val="0">` on each bar series (see Bar Charts section above)
- **Table style**: call `fix_table_style(table_shape)` to set the canonical safe GUID `{2D5ABB26-0587-4C30-8999-92F81FD0307C}` ("No Style, No Grid"). Never use the null GUID `{00000000-...}`; it crashes LibreOffice 26 on PPTX import
- **Table fonts**: call `fix_table_fonts(table_shape)` after populating the table
- **Text box fonts**: increase to `Pt(22)` (target) or at minimum `Pt(20)`; if text does not fit, reduce content or split the slide rather than reducing font size
- **Conversion coverage**: reclassify image-only slides as hybrid (text column native + image column embedded), native shapes (colored boxes, flowcharts, box-and-arrow diagrams), or native charts (bar/line/scatter) per `conversion-workflow.md` Step 2 decision rules
- **Chart number format**: set `chart.value_axis.tick_labels.number_format` to the appropriate format string ($, %, #,##0, 0, etc.) and set `number_format_is_linked = False`; cross-reference the Beamer `.tex` source for data units
- **Hanging indent**: call `set_hanging_indent(paragraph)` on every bullet paragraph to set proper `marL` and negative `indent`
- **Below-target font (WARNING)**: try setting to `Pt(24)` first; if content overflows, reduce content (fewer bullets, shorter text, split slide); only drop to `Pt(22)` or `Pt(20)` after content is already minimal
- **Text overflow**: reduce text content (shorten descriptions, remove items), increase box height (fewer items per slide = taller boxes), or change layout (switch from grid to bulleted list or table). Never ignore overflow; the rendered PPTX will clip or overlap
- **Off-spec gray**: change the run's color to `RGBColor(0x4D, 0x4D, 0x4D)` (Charcoal). The check only fires on gray-toned colors (R≈G≈B) that are not in the approved palette grays, so near-Charcoal values like `#3A3A3A`, `#555555`, or `#333333` will be flagged. Colored accent runs (SlateNavy, DeepTeal, DustyPlum, etc.) are not affected
- **UNIFORM-AT-FLOOR (generation)**: the floor was written as a default. Recompute every body box's size with `fit_font_size()` (start at the role ceiling, step down to fit, clamp at floor); where content is genuinely too dense for anything above the floor, reduce content. Never bump sizes without re-checking fit
- **UNIFORM-AT-FLOOR (conversion warning)**: read `room_count` from the warning. If `room_count >= 1`, recompute every body box via `fit_font_size()` against its text area and re-save (fixed in the PPTX); if `room_count == 0`, surface a reduce-content decision to the user. Never hand-pick emphasis sizes or inflate fonts to clear it (see "Font Size Rule for Conversion" in `conversion-workflow.md`)
- **Box under-fill (WARNING)**: compute the size with `fit_font_size()` and re-set the runs, or shrink the box to its content; a deliberately airy layout (hero stat, spacious card) can be accepted explicitly
- **Caption under-fill (ERROR)**: the caption is smaller than its box affords. Generate it with `add_caption()`, which computes the size in [18, 22] with `fit_font_size(role='caption')` and sizes the box to the text. Never hand-roll a caption text box with a literal point size
- **`<p:style>` conflict (PowerPoint repair warning)**: after `add_shape()`, find and remove the auto-added `<p:style>` element when you also set explicit `srgb` fill or line on the shape's `spPr`. `add_rounded_card()` does this automatically; if you wrote a custom autoshape helper, copy the `sp_el.find(qn('p:style'))` cleanup pattern from there
- **`<a:buChar>` missing typeface (PowerPoint repair warning)**: use `set_bullet()`, which always emits a paired `<a:buFont typeface="Arial"/>` immediately before `<a:buChar/>`. Never write a custom bullet helper that only sets `<a:buChar>`

## Implementation Checklist

When generating slides, verify:

**Layout:**
- [ ] Title in placeholder, 36pt Calibri Bold, #4D4D4D (Charcoal); title is the key message
- [ ] No subtitle added; no title slide generated
- [ ] Callout boxes present in the source are recreated as editable filled text boxes (`add_rounded_card()` + a white text run), matching the source fill and white text, never rasterized; do not add callouts the source does not have
- [ ] Content starts at `CONTENT_TOP = 1.95"`, never at 1.6", 1.35", or above the title bottom (1.826")
- [ ] All shapes start at `CONTENT_LEFT = 1.10"` or further right, never at 0.5", 0.6", 0.8", 1.0"
- [ ] All shapes fill `CONTENT_W = 13.80"`; no narrower layouts that leave gaps on the right
- [ ] Body content stays above `CONTENT_BOTTOM = 8.00"`. Citation band is T=8.00 to 8.25. Footer placeholder begins at T=8.38.

**Typography:**
- [ ] Body text ≥ 22pt (the body role floor per the Role-Based Font Hierarchy; body secondary ≥ 20pt); never below the role floor for slide content; reduce content instead
- [ ] Use largest font that fits attractively: compute from the body role's 24-28pt target via `fit_font_size()`, then clamp at the 22pt floor; never write the floor as a default
- [ ] Table cells: explicit font size set (never rely on inherited defaults)
- [ ] Table cells: alignment explicitly set (never rely on inherited defaults)

**Multi-box layouts:**
- [ ] Equal-width boxes when layout is symmetric
- [ ] Box group fills full `CONTENT_W = 13.80"` with 0.5" gaps; no gap on right side

**Charts:**
- [ ] Line charts: legend = RIGHT
- [ ] Bar charts with negative values: `invertIfNegative` = 0 on all series
- [ ] Chart layout matches Beamer source (axis ranges, legend position, data labels)
- [ ] Chart axis number formats set explicitly ($, %, #,##0, etc.) matching Beamer source data units

**Citations:**
- [ ] Every source citation in the Beamer source is reproduced as a citation text box in the PPTX
- [ ] Citation text boxes are at canonical position: `L=1.10", T=8.00", W=13.80", H=0.25"` (single-line)
- [ ] Multi-line citations grow upward only: `T=7.75, H=0.50` for 2 lines; `T=7.50, H=0.75` for 3 lines. Bottom edge always at `T+H=8.25`, never inside footer strip (`T≥8.38`).
- [ ] Citation formatting: 11pt Calibri **non-italic**, #B0AFA8, right-aligned
- [ ] Multi-source citations use `; ` (semicolon space) between sources

**Text structure:**
- [ ] Related text (heading + bullets) is in ONE continuous text box, not split into separate boxes
- [ ] Beamer `\begin{itemize}` and `\begin{enumerate}` are reproduced as native PPTX bullets/numbered lists
- [ ] Bullet indentation uses `paragraph.level`, not manual spaces or dashes

**Visual:**
- [ ] Maximum 3-4 colors per slide
- [ ] No gradients, shadows, text shading, or effects
- [ ] White text on all filled boxes
- [ ] Pre-save structural quality check passes with no errors (run `run_quality_check(prs)` before `prs.save()`)
- [ ] No text overflow errors (estimated text height fits within shape height for every text box)
- [ ] Below-target font warnings reviewed and addressed where possible
- [ ] Grid layouts verified with `estimate_text_height()` on longest content before committing to layout

## Rendering for Review

When producing a review PDF of a saved PPTX (to inspect rendered slides, audit visually, or share for feedback), use **LibreOffice headless** as the export engine. PowerPoint is the documented fallback when LibreOffice misrenders. Never use Keynote.

**Why LibreOffice over PowerPoint:** PowerPoint on macOS is sandboxed and cannot read files in `/private/tmp/...` or other restricted paths without a per-file "Grant File Access" prompt that the user must dismiss every time. LibreOffice runs headless with no GUI and no permission prompts. LibreOffice respects coded dimensions when Critical Rule #7 (`auto_size = MSO_AUTO_SIZE.NONE`) is applied, the same condition under which PowerPoint respects them.

**Why not Keynote:** Keynote's PDF export applies its own auto-size to text frames on open, which silently resizes shapes that were coded with explicit dimensions. This produces cards with misaligned bottoms, overgrown callouts, and label positions that do not match the coded coordinates, even when the PPTX itself is correct.

**Canonical render path:**

```bash
soffice --headless --convert-to pdf "/absolute/path/to/deck.pptx" --outdir "/absolute/path/to/outdir/"
```

The output PDF lands at `/absolute/path/to/outdir/deck.pdf`. The command exits cleanly when the conversion completes; no application window opens.

Then render PNGs from the PDF with `pdftoppm -png -r 120 deck.pdf deck-slide`. The `-png` flag is required; without it, `pdftoppm` defaults to uncompressed PPM (≈6 MB per slide vs ≈200 KB for PNG). At `-r 120` a standard 16:9 slide renders at 1600×900, sharp enough for visual layout audits while staying under common image-size limits for AI review tools.

**PowerPoint fallback.** If a LibreOffice export shows visual defects that the code says should not be there (rare; usually involves obscure chart features or font-substitution surprises), re-export via PowerPoint:

```bash
osascript -e 'tell application "Microsoft PowerPoint"
    open POSIX file "/absolute/path/to/deck.pptx"
    set theDoc to active presentation
    save theDoc in POSIX file "/absolute/path/to/deck.pdf" as save as PDF
    close theDoc saving no
end tell'
```

PowerPoint cannot read `/private/tmp/...` without a permission prompt; copy the deck into the project folder (or `~/Library/Caches/`) before running the AppleScript fallback.
