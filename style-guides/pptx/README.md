# PPTX Style Guide

PowerPoint presentation formatting using python-pptx, including a Beamer-to-PPTX conversion workflow.

## What's in the Bundle

This style guide is a five-file bundle: the rules live in one markdown file, the code that enforces them lives in three Python files, and the conversion procedure lives in its own module.

| File | Role |
|------|------|
| [style-guide.md](style-guide.md) | The rules: typography, role-based font hierarchy, layout constants, color palette, chart/table rules, quality gate, rendering for review. Read in full before generating any PPTX. |
| [pptx_lib.py](pptx_lib.py) | Shared helper library: layout constants, palette, and helpers (`add_citation()`, `add_rounded_card()`, `add_caption()`, `fit_font_size()`, `fix_chart_fonts()`, `fix_table_fonts()`, `fix_table_style()`, `set_bullet()`, `set_hanging_indent()`, `estimate_text_height()`, `add_image_proportional()`, and more). Import it; never re-type helpers into a deck script. |
| [quality_check.py](quality_check.py) | `run_quality_check(prs)`: ~19 automated pre-save checks (bounds, overlap, chart fonts, legend position, table styles, vertical alignment, text overflow, role-based font floors, repair-warning prevention, uniform-at-floor sizing, box and caption under-fill). Importable, or run from the CLI on a saved deck. |
| [generator_template.py](generator_template.py) | Copy-paste starter scaffold for every new deck script, with the quality gate and helper imports already wired. |
| [conversion-workflow.md](conversion-workflow.md) | The Beamer-to-PPTX conversion procedure: per-slide categorization, image-embed decision rules, conversion font sizing, citation extraction, chart number formatting, and chart data fidelity. Loaded in addition to style-guide.md for conversions only. |

## Requirements

### Python

Python 3.8+ with the `python-pptx` library (and Pillow if you embed images):

```bash
pip install python-pptx Pillow
```

Verify:
```bash
python3 -c "import pptx; print('python-pptx', pptx.__version__)"
```

### PowerPoint Template

The style guide expects a `.pptx` template file with:
- A "Title Only" slide layout (used as the base for all content slides)
- 16:9 aspect ratio
- Your institutional branding (logo, footer, colors) pre-applied to the template

## Setup

1. Install python-pptx (see above)
2. Create or obtain a `.pptx` template with your branding
3. Copy all five files to your Claude Code skills reference location (keep them in one folder; the Python files import each other by folder)
4. Set `TEMPLATE_PATH` in `pptx_lib.py` to point to your template
5. Update the color palette hex values (in both `style-guide.md` and `pptx_lib.py`; they mirror each other) if your institution's colors differ from the defaults
6. In `generator_template.py`, point the `sys.path.insert` line at the folder holding `pptx_lib.py` and `quality_check.py`

## Changed in This Version

- **The guide is now a five-file bundle.** Earlier versions were one large markdown file with all code inlined; the helper library, quality check, and generator scaffold are now real importable Python files, and the conversion workflow is its own module. The rules are unchanged by the split; generators should import `pptx_lib.py` / `quality_check.py` instead of copying code out of the markdown.
- New critical rule: when the user supplies a base PPTX, that file is the destination (copy it and append slides into it); never splice the user's base into a clean template, which discards the base's master, theme, and animations.
- Figure captions are now a first-class role: `add_caption()` computes an 18-22pt left-aligned caption below the figure and tags it `FigCaption`; a caption under-fill check (blocking) prevents captions from shrinking toward citation size.
- Chart data fidelity at conversion: chart points must be read from the `.tex` source by a shared parser and verified after the build, never re-keyed by eye.

## Customization

See the [parent README](../README.md) for how to adapt colors, fonts, and layout constants to your institution.
