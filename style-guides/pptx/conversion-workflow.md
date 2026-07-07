# Beamer-to-PPTX Conversion Workflow (style-guide module)

This module carries the conversion-only procedure for turning a compiled Beamer deck into native PowerPoint. It is loaded **in addition to** the core `style-guide.md` (which carries the Critical Rules, the Role-Based Font Hierarchy, the palette, the layout constants, and every generation-time rule): a conversion reads both files in full before writing any code. Direct PPTX generation does not load this module. The code helpers named below are imported from `pptx_lib.py` and `quality_check.py` in this folder, never re-typed.

## Beamer-to-PPTX Conversion Workflow

**Full-slide image embedding of Beamer pages is NOT conversion.** The purpose of this workflow is to recreate slide content as native, editable PowerPoint objects (charts, shapes, text boxes, tables). Image embed is reserved for irreducible visual complexity (mathematical curves, Bezier paths) and requires written justification per slide. If your implementation renders PDF pages as PNGs and embeds them, you have not followed this workflow.

**Task agent delegation:** If this conversion is delegated to a subagent, the agent must read the core style guide (`style-guide.md`) and this entire module in full as its first action. The per-slide categorization (Step 2), user-approval checkpoint (Step 4), and pre-save quality check are non-negotiable steps that cannot be summarized or skipped. Pass both file paths in the agent prompt.

When converting Beamer output to PPTX, follow this workflow in order. Do not write any python-pptx code until Steps 1-4 are complete.

### Step 1: Read the .tex source and compiled PDF

- Read `slides.tex` from the build directory
- Read the compiled PDF. For a long PDF read in a context-limited session, prefer an existing text extract if one exists, or split the PDF into ~4-page chunks and read them in a subagent that writes notes, then read the notes. When the conversion is already delegated to a subagent, read the PDF directly there.
- Identify the content name from the calling workflow (BASENAME, content_name, etc.) or from the working directory name

### Step 2: Per-slide conversion plan

For each Beamer slide, categorize every visual element into one of four types:

| Type | When to use | PowerPoint implementation |
|------|------------|--------------------------|
| **Native chart** | Standard bar, line, scatter, pie charts. Read the data points from the `.tex` source with a chart-data reader (see "Chart data fidelity" below); never re-key them by eye | `add_chart()` + `fix_chart_fonts()` + palette colors |
| **Native table** | Data tables | `add_table()` + `fix_table_fonts()` + `fix_table_style()` |
| **Native shapes/text** | Bullet points, text boxes, simple box layouts, colored boxes with text labels, box-and-arrow diagrams, flowcharts, stacked/layered layouts | `add_shape()` + `add_textbox()` with Calibri formatting |
| **Hybrid (text + image)** | Two-column Beamer slides where one column is text/bullets and the other is a complex visual | Native text box(es) for the text column + `add_image_proportional()` for the visual column |
| **Image embed** | LAST RESORT. The visual contains mathematical curve plots with axis annotations, or TikZ paths with Bezier curves/decorative elements that have no PowerPoint shape equivalent, AND it cannot be decomposed into rectangles, arrows, and text labels | Render at 300 DPI, crop, `add_image_proportional()` |

**Two-column Beamer slides:** Always recreate the text column as native text boxes at the computed fill size (body target 24-28pt via `fit_font_size()`, clamped at the 22pt floor; see "Font Size Rule for Conversion"). Then classify the slide by its visual column: standard bar/line/scatter/column chart → `native chart`; colored boxes, flowcharts, box-and-arrow diagrams, cards, comparison layouts → `native shapes`; data table → `native table`; complex visual that cannot be recreated (Bezier paths, choropleth maps, multi-panel composites) → `hybrid (text + image)`. The `hybrid` classification is reserved for when the visual column genuinely requires an image embed. A two-column slide with bullets + a native pgfplots bar chart is `native chart`, not hybrid. A full-slide image embed is only permitted when the slide has no separable text content.

**Image embed decision rules:**

- **ALWAYS native shapes** (never image embed): colored rectangles/boxes with text labels, box-and-arrow diagrams, flowcharts, stacked/layered layouts with labeled sections, simple node-and-edge diagrams, comparison layouts, tables, process flows with labeled steps
- **MAY be image embed** (requires written justification): mathematical function plots with axis annotations, complex pgfplots with many overlapping series and fill regions, TikZ diagrams with decorative elements (braces, Bezier curves, custom path decorations), choropleth maps, multi-panel composite figures

**For each slide marked "image embed," write one sentence justifying why it cannot be recreated natively.** If no justification exists, reclassify as native or hybrid.

**Callout boxes.** If the Beamer source uses a reinforcement-callout macro (a standalone box with a dark fill and white bold text), recreate it as a native editable filled text box: `add_rounded_card(slide, ..., border_rgb, fill_rgb)` plus a white text run, never a rasterized image, matching the source fill color. Reproduce only the callouts the Beamer source contains; never add new ones. Contrast: white text is recreated only on the dark source fills (SlateNavy, DeepTeal, AccentRed, DustyPlum, CyanBlue, BurntOrange). Positive/alert valences (green, amber, soft red) arrive as bold colored text on white (an ordinary editable text run, no fill). If you ever see white text on a light fill, that is a defect to correct, not reproduce.

### Step 3: Specify output filename

The PPTX must be named `<content_name>.pptx` using the content name from the calling workflow. Never use generic names like `slides.pptx`. If no content name was provided by a calling workflow, derive one from the working directory name or ask the user.

### Step 4: Present the plan

Present the conversion plan to the user in table format before writing any code:

```
Slide | Type           | Elements                                      | Notes
1     | image          | Complex multi-layer TikZ flow diagram          | 12 positioned nodes with crossing arrows
2     | native chart   | Clustered bar chart (3 series, 5 categories)   | Data: [values from .tex]
3     | native shapes  | 3-box comparison layout with text              | DeepTeal/CyanBlue/DustyPlum outlines
...
```

Wait for user approval before proceeding to code generation. Then follow the core style guide (and the rest of this module) for implementation.

**Exception:** When a calling workflow specifies "without pause" or "proceed directly," skip the pause and execute the plan immediately. Still produce the plan internally and log it in the output, but do not wait for explicit approval.

## Font Size Rule for Conversion

Conversion sizes are **computed from the source's hierarchy, then clamped at the role floors**, never flattened to one value. Two steps per text element:

1. **Carry the Beamer hierarchy proportionally.** Map the source's relative sizes so the deck's visual hierarchy survives: `\normalsize` body anchors at ~24pt; `\large` above it (~28pt); `\Large`/`\LARGE` map to section-header/title sizes; `\small` body lands ~22-24pt; `\footnotesize` secondary text lands at the body-secondary tier; `\scriptsize` maps to its role (citation band, micro-label). A figure caption maps to the **caption role** (target 22pt, floor 18pt) by its function, not by its size token: a caption reads one tier above the citation and is never collapsed onto it. A `\large` heading must come out larger than a `\normalsize` body line; flattening every run to one size erases the hierarchy the Beamer deck had.
2. **Compute the largest in-role size that fits the box, then clamp at the floor.** The mapped source size sets the role and the relative ordering; the actual size is the largest in-role size that fits the shape's **text area** (box minus its text-frame margins) via `fit_font_size()`, not the mapped value pinned and not the floor written as a default. A flat source converts to flat-but-box-filling output (uniform enlargement is not manufactured hierarchy); a source with headers keeps its hierarchy because headers map to a higher role ceiling. "Verify fit" means compute up to fill, not only step down. (Floors: body 22pt, body secondary 20pt, per the Role-Based Font Hierarchy in `style-guide.md`.)

**A uniform-at-floor conversion is fixed by recompute when the boxes have room; it is upstream only when they are genuinely full.** When the quality check's uniform-at-floor signature fires on a conversion, it carries `room_count` (the number of at-floor body shapes whose text area affords a larger size). **`room_count >= 1`**: the conversion under-sized boxes that have room, so recompute each body box via `fit_font_size()` against its text area (the per-box fill this rule already mandates) and re-run; this is a fix in the PPTX, not an upstream punt. **`room_count == 0`**: every at-floor body box is genuinely full at 22pt, and the only larger-size path is reducing content, which is a decision to surface to the user. Never silently inflate fonts or hand-pick emphasis sizes to clear it: the recompute is the deterministic per-box `fit_font_size`, so a flat source comes out flat-but-larger (no manufactured hierarchy). The signature fires on `body`-role runs, which on a card-dominated deck includes any card converting to a shape at or above 3.5" wide (it classifies as `body`, so it does trip the check). If your Beamer pipeline has its own design-quality pass, that remains the primary net for inherited under-fill; this is the conversion-side backstop. Apply sizing before the text-fidelity verification pass, and re-run the quality check after any post-verification correction (corrected text can change wrapping).

If the Beamer source has dense text that would require fonts below the role floor to fit in a PPTX text box, **reduce content, not font size.** Split the text across two slides, remove less critical bullets, or condense phrasing.

This applies to all native text boxes: bullet lists, labels, standalone text, hybrid slide text columns, and annotation text. The only exceptions are chart axis labels (14pt per chart font rules), table content (14pt minimum per table rules), and caption text (18-22pt per the caption role, its own floor).

## Source citation extraction (conversion)

Every source citation in the Beamer source (e.g., a `\sourcecite{}` footer macro, or however your Beamer template marks slide sources) must be carried over to the PPTX as a citation text box. Citations are not optional content; they are part of the slide. The canonical placement, formatting, and grow-upward spec is "Source Citation Handling" in `style-guide.md`; `add_citation(slide, text, lines=N)` in `pptx_lib.py` is the single required path.

**Extraction:** Parse each slide's citation content from the `.tex` source. Strip LaTeX formatting (drop `\textit{}` wrappers to produce plain text; backslash escapes become their characters). If a slide has a source citation, the PPTX slide must have a citation text box. If a slide has none, do not add one.

**Line count estimation:** With Calibri 11pt at a 13.80" width, a single line fits approximately 160-180 characters. Pass `lines=2` when the citation text exceeds ~160 characters or when it contains two or more sources joined by `; `. Pass `lines=3` only for genuinely long multi-source citations (>320 characters).

## Chart Number Formatting

When converting Beamer charts to native PowerPoint charts, axis labels and data labels must use appropriate number formatting. Do not leave axes with raw unformatted numbers.

**Common format strings for `number_format` on chart axes and data labels:**

| Data type | Format string | Example |
|-----------|--------------|---------|
| Currency (millions) | `'$#,##0"M"'` | $150M |
| Currency (billions) | `'$#,##0.0"B"'` | $2.5B |
| Currency (exact) | `'$#,##0'` | $1,500 |
| Percentage | `'0%'` or `'0.0%'` | 45% or 45.0% |
| Percentage (from decimal) | `'0%'` | 0.45 displays as 45% |
| Comma-separated | `'#,##0'` | 1,500 |
| Year (no commas) | `'0'` | 2026 |
| Decimal | `'0.0'` or `'0.00'` | 3.5 or 3.50 |

**Apply to axes:**
```python
chart.value_axis.tick_labels.number_format = '$#,##0"M"'
chart.value_axis.tick_labels.number_format_is_linked = False
```

**Apply to data labels:**
```python
plot = chart.plots[0]
plot.has_data_labels = True
plot.data_labels.number_format = '0%'
plot.data_labels.number_format_is_linked = False
```

**Rule:** Cross-reference the Beamer `.tex` source for the data units. If the pgfplots axis shows `ylabel={Revenue (\$M)}`, the PPTX value axis must use `'$#,##0"M"'`. If percentages are plotted, use `'0%'`. If years are on the category axis, use `'0'` (no comma separators). Never leave chart axes with the default unformatted number display.

## Chart and Diagram Conversion

When converting Beamer/LaTeX charts and diagrams to PowerPoint:

### Match the Beamer source

When converting Beamer charts and diagrams to PowerPoint, the PPTX chart should match the PDF as closely as possible:
- Same axis ranges and tick marks
- Same data label format and placement
- Same legend position (see "Chart legend rules" in `style-guide.md`)
- Same series colors (using the core guide's palette)
- Same chart type (bar, line, scatter, etc.)

Cross-reference the `.tex` source and the compiled PDF when making layout decisions.

### Use native PowerPoint charts (default)
Recreate charts using python-pptx's chart API (`add_chart()`). This includes bar charts, line charts, pie charts, scatter plots, and other standard chart types. Native charts are editable, scalable, and professional.

**Formatting requirements:**
- Number formatting (decimal places, percentages, currency) must match the Beamer source exactly
- Axis label formatting (font size, orientation, number format) must match the Beamer source
- Data labels must use the same format as the Beamer chart
- Bar/series colors must use the style guide palette
- No shadows, gradients, or 3D effects on any chart element

### Chart data fidelity: read the points, do not re-key them

**The data for a native chart must be READ from `slides.tex`, never transcribed by eye.** Re-keying chart numbers from a glance at the source is how a 17-point monthly curve once became a 4-point yearly one with nobody noticing: the result looked plausible and no check compared the data (only text and composition were checked). A shared reader removes the eyeball step, and a verification pass compares the built chart back against the source.

**Build the reader once, as a shared module.** Write (or adopt) a small parser that extracts pgfplots coordinate data from `slides.tex`: one chart record per `\begin{axis}` in document order, each carrying the frame title, whether it is a bar chart, whether x is numeric or categorical, its series (each a list of `(x, y)` points plus a legend label), any reference lines drawn with `\draw (axis cs:..) -- (axis cs:..)`, and any raw spans it refused to parse. Exclude forget-plot and fill-region series from the data series. Coalesce the one-`\addplot`-per-bar idiom into a single series so a bar chart reads as one series of N points, matching its single PPTX category series. Import that module in every conversion; never paste its body into a deck script (a drifted copy reintroduces the exact bug it prevents).

**Prevention: feed the read points into the chart.** When building a native chart, take its points from the matching parsed chart record (keyed on frame title), not from a mental summary:

```python
src = {c.frame_title: c for c in read_charts(TEX_PATH)}
c = src["New Software Supply Surged; End-User Usage Did Not"]
for s in c.data_series:
    xs = [p[0] for p in s.points]
    ys = [p[1] for p in s.points]
    # add this series with its exact xs / ys and s.legend
```

**Axis-type rule.** When the source x-coordinates are continuous or unevenly spaced (true time, decimals, gaps), build an **XY chart** (`XL_CHART_TYPE.XY_SCATTER_LINES*` with `XyChartData`), not a category chart. Collapsing a numeric time axis onto evenly-spaced text categories silently distorts the chart. Use a category chart (`CategoryChartData`) only when x is sequential integer positions or symbolic categories (the bar idiom, or a categorical x axis).

**Markers.** If the source draws reference lines (e.g., a dashed vertical marker at a threshold year), reproduce each as a thin two-point series (or a line shape) at its exact x, so the marker survives into the PPTX.

**Charts the reader cannot read.** If a chart record has unparseable spans (a function/expression plot, error bars) or the figure is a matplotlib `\includegraphics` image, the reader cannot supply points; hand-build the chart AND flag it as unverified for manual review. Never hand-key a chart silently.

**Verification (mandatory, pre-save).** After the deck is built and `run_quality_check()` passes, run a chart-fidelity verification that compares every native chart's series against the source coordinates (matching by slide title, then series name) and reports:

- **Divergence**: a value differs; the source is truth, correct the PPTX series and re-run.
- **Unverified**: a structural mismatch (point or series count), or a source the reader could not read (so the chart was hand-built); review it, do not ship it silently.
- **Marker**: a source reference line with no matching PPTX series; confirm it was preserved.

An empty report means every native chart matched the source within tolerance. A non-empty report is never a silent pass; surface it. This is the chart analog of a text-fidelity verification pass, and it inherits the same fail-loud contract: a chart this cannot confirm is reported, never assumed correct.
