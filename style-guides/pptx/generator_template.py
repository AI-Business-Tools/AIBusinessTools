"""Canonical PPTX generator template (style-guide bundle).

Copy this file as the starting point for every new PPTX generator, then
replace the example slide section with the deck's real content. All rule
enforcement lives in pptx_lib.py (auto_size=NONE, Charcoal default,
canonical citation band, hanging indents, chart/table XML fixes) and
quality_check.py (pre-save structural gate). Import them; never re-type
their code into this script.
"""
import os
import sys

# Point this at the folder containing pptx_lib.py and quality_check.py.
sys.path.insert(0, os.path.expanduser('~/path/to/pptx-style-guide'))  # edit me

from pptx import Presentation
from pptx.util import Inches, Pt

from pptx_lib import (
    TEMPLATE_PATH, IN,
    CONTENT_LEFT, CONTENT_TOP, CONTENT_W, CONTENT_H, CONTENT_BOTTOM, FOOTER_TOP,
    CHARCOAL, SLATE_NAVY, DEEP_TEAL, CYAN_BLUE, DUSTY_PLUM, WARM_AMBER,
    GREEN, SOFT_RED, BURNT_ORANGE, ACCENT_RED, SLATE_BLUE, PALE_BLUE,
    LIGHT_GRAY, MEDIUM_GRAY, MED_GRAY, WHITE,
    tint, is_hidden, set_hidden,
    set_bullet, set_hanging_indent, add_citation, add_rounded_card,
    add_body_textbox, add_paragraph, estimate_text_height, ROLE_RANGES,
    fit_font_size, add_caption, add_title, remove_existing_slides,
    fix_chart_fonts, fix_invert_if_negative, add_image_proportional,
    fix_table_fonts, fix_table_style,
)
from quality_check import run_quality_check, report_and_exit

OUTPUT_PATH = '/absolute/path/to/deck.pptx'   # edit me

# --- Load template -----------------------------------------------------------
prs = Presentation(TEMPLATE_PATH)
remove_existing_slides(prs)

title_only = next(
    (l for l in prs.slide_layouts if l.name == "Title Only"),
    prs.slide_layouts[5])

# ------ Slide 1 (replace with real content) ------
slide = prs.slides.add_slide(title_only)
add_title(slide, "Your Title Here (the key message)")

card = add_rounded_card(slide,
    left=CONTENT_LEFT, top=CONTENT_TOP + 0.10,
    w=CONTENT_W, h=5.00,
    border_rgb=DEEP_TEAL, fill_rgb=tint(DEEP_TEAL, 8))
tf = card.text_frame
# Compute the body size for this box, then pass it — never hardcode a floor.
bullets = ["First supporting bullet.", "Second supporting bullet."]
body_pt = fit_font_size(["Section header"] + bullets, box_w=CONTENT_W - 0.4, box_h=4.6, role='body')
add_paragraph(tf, "Section header", size=body_pt + 4, bold=True, first=True)
add_paragraph(tf, bullets[0], size=body_pt, bullet=True, space_before=10)
add_paragraph(tf, bullets[1], size=body_pt, bullet=True, space_before=10)

add_citation(slide, "Author, First. YYYY. Title. Publication.")

# ------ Add more slides the same way ------
#
# Charts:  chart_shape = slide.shapes.add_chart(...); then immediately
#          fix_chart_fonts(chart_shape.chart); fix_invert_if_negative(...)
#          on bar charts with negative values; legend rules per style-guide.md.
# Tables:  table_shape = slide.shapes.add_table(...); populate; then
#          fix_table_fonts(table_shape); fix_table_style(table_shape).
# Captions: add_caption(slide, figure_shape, "Caption text.") under every
#          chart/figure that has a caption in the source.
#
# Embedded-image placement patterns (all images go through
# add_image_proportional; never hardcoded offsets or stretched dimensions):
#
# Full-width figure slide (no caption):
#   add_image_proportional(slide, img_path, CONTENT_LEFT, CONTENT_TOP, CONTENT_W, CONTENT_H)
#
# Figure with caption below — reserve only what the caption needs (computed
# from its text), place the image in the remainder, then add_caption():
#   cap_pt = fit_font_size([cap_text], CONTENT_W, 0.95, role='caption')
#   cap_h  = estimate_text_height(cap_text, CONTENT_W, cap_pt) + 0.13
#   img = add_image_proportional(slide, img_path, CONTENT_LEFT, CONTENT_TOP,
#                                CONTENT_W, CONTENT_H - cap_h)
#   add_caption(slide, img, cap_text)
#
# Two images side by side:
#   col_w = (CONTENT_W - 0.50) / 2   # 0.50" gap between images
#   add_image_proportional(slide, img1_path, CONTENT_LEFT,                CONTENT_TOP, col_w, CONTENT_H)
#   add_image_proportional(slide, img2_path, CONTENT_LEFT + col_w + 0.50, CONTENT_TOP, col_w, CONTENT_H)
#
# Hybrid slide — text column (left) + image column (right):
#   COL_GAP   = 0.50
#   TEXT_W    = CONTENT_W * 0.52                     # text takes ~52% of content width
#   IMG_COL_W = CONTENT_W - TEXT_W - COL_GAP         # image gets the remainder
#   IMG_COL_LEFT = CONTENT_LEFT + TEXT_W + COL_GAP
#   # Text column: add_body_textbox() at CONTENT_LEFT, width=Inches(TEXT_W), computed body size
#   add_image_proportional(slide, img_path, IMG_COL_LEFT, CONTENT_TOP, IMG_COL_W, CONTENT_H)

# --- Quality check + save ----------------------------------------------------
issues = run_quality_check(prs)   # pass conversion_source='<slides.tex>' for a Beamer conversion
report_and_exit(prs, issues)      # prints the report; raises SystemExit on errors

prs.save(OUTPUT_PATH)
print(f"Saved: {OUTPUT_PATH}")
