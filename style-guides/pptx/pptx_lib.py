"""PPTX style-guide shared helper library.

Canonical implementations of the style guide's rules (style-guide.md in this
folder). Every generator imports these helpers; never re-type them into a
deck script — a drifted copy reintroduces the defects they prevent
(auto_size unlocked, missing <a:buFont>, <p:style> repair warnings,
hand-picked floor sizes).

The layout constants and palette values below mirror the human-readable
"Content Area Layout Constants" and "Complete Color Palette" blocks in
style-guide.md; change both together.

Usage:
    import sys, os
    sys.path.insert(0, '<path to this style-guide folder>')
    from pptx_lib import *
"""
import math
import os

from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

# Point this at your own 16x9 template with a "Title Only" layout
# (see style-guide.md "Template File" and the pptx README).
TEMPLATE_PATH = os.path.expanduser('~/path/to/your-template.pptx')  # edit me

IN = 914400   # EMU per inch

# --- Layout constants (mirror style-guide.md "Content Area Layout Constants")
SLIDE_W = 16.0   # inches
SLIDE_H = 9.0    # inches

# Title placeholder (from template — do not change)
TITLE_LEFT = 1.10
TITLE_TOP  = 0.33
TITLE_W    = 13.80
TITLE_H    = 1.49   # bottom edge at 1.82"

# Content area — use these for ALL shapes, charts, text boxes
CONTENT_LEFT   = 1.10   # left margin (aligns with title)
CONTENT_TOP    = 1.95   # just below title bottom (1.82" + 0.13" gap)
CONTENT_W      = 13.80  # full content width (aligns with title)
FOOTER_TOP     = 7.70   # do not place content below this line (footer zone)
CONTENT_H      = FOOTER_TOP - CONTENT_TOP   # = 5.75 inches
CONTENT_BOTTOM = 8.00   # absolute body-content limit (citation band starts here)

# Citation band
CITATION_LEFT   = 1.10
CITATION_W      = 13.80
CITATION_BOTTOM = 8.25   # fixed — citation never extends below this
CITATION_LINE_H = 0.25   # height per line

# --- Palette (mirror style-guide.md "Complete Color Palette") ---------------
CHARCOAL     = RGBColor(0x4D, 0x4D, 0x4D)   # body text default
SLATE_NAVY   = RGBColor(0x1B, 0x2A, 0x4A)   # primary fill
DEEP_TEAL    = RGBColor(0x0D, 0x73, 0x77)   # primary accent
CYAN_BLUE    = RGBColor(0x00, 0x77, 0xB6)   # secondary accent
DUSTY_PLUM   = RGBColor(0x9B, 0x59, 0x78)   # tertiary accent
WARM_AMBER   = RGBColor(0xE8, 0x91, 0x3A)   # alert fill
GREEN        = RGBColor(0x27, 0xAE, 0x60)   # positive fill
SOFT_RED     = RGBColor(0xDC, 0x5C, 0x5C)   # warning fill
BURNT_ORANGE = RGBColor(0xBF, 0x57, 0x00)   # problem fill
ACCENT_RED   = RGBColor(0xC0, 0x39, 0x2B)   # problem fill (severe)
SLATE_BLUE   = RGBColor(0x42, 0x55, 0x63)   # default outline
PALE_BLUE    = RGBColor(0xE8, 0xF0, 0xF8)   # subtle backgrounds
LIGHT_GRAY   = RGBColor(0xF0, 0xEF, 0xEC)   # spare light fill
MEDIUM_GRAY  = RGBColor(0x6C, 0x7A, 0x89)   # connectors / neutral outlines ONLY
MED_GRAY     = RGBColor(0xB0, 0xAF, 0xA8)   # citations ONLY
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)


def tint(rgb, pct):
    """Mix rgb with white. pct=12 → 12% of color, 88% white."""
    r = int(rgb[0] + (255 - rgb[0]) * (1 - pct / 100))
    g = int(rgb[1] + (255 - rgb[1]) * (1 - pct / 100))
    b = int(rgb[2] + (255 - rgb[2]) * (1 - pct / 100))
    return RGBColor(r, g, b)


# --- Hidden slides -----------------------------------------------------------
def is_hidden(slide):
    """Check if a slide is marked as hidden in PowerPoint."""
    return slide._element.get('show') == '0'


def set_hidden(slide, hidden=True):
    """Mark a slide as hidden (or visible)."""
    slide._element.set('show', '0' if hidden else '1')


# --- Text helpers (rules baked in) ------------------------------------------
def set_bullet(paragraph, level=0, bullet_char='•', typeface='Arial'):
    """Set a bullet character on a paragraph.

    Always pairs <a:buFont typeface="..."/> with <a:buChar/>; PowerPoint
    flags <a:buChar> alone as malformed and strips the bullet during repair
    (Critical Rule 8). Bullet font must precede bullet char per OOXML schema
    order. For enumerated lists, emit <a:buAutoNum type="arabicPeriod"/>
    instead of <a:buChar>.
    """
    paragraph.level = level
    pPr = paragraph._p.get_or_add_pPr()
    for existing in pPr.findall(qn('a:buFont')):
        pPr.remove(existing)
    buFont = etree.SubElement(pPr, qn('a:buFont'))
    buFont.set('typeface', typeface)
    for existing in pPr.findall(qn('a:buChar')):
        pPr.remove(existing)
    buChar = etree.SubElement(pPr, qn('a:buChar'))
    buChar.set('char', bullet_char)


def set_hanging_indent(paragraph, margin_inches=0.30, indent_inches=-0.25):
    """Set hanging indent so wrapped text aligns under text start, not bullet."""
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set('marL', str(int(Inches(margin_inches))))
    pPr.set('indent', str(int(Inches(indent_inches))))


def add_citation(slide, text, lines=1):
    """Canonical citation band. Grows upward for multi-line; bottom fixed at 8.25.

    11pt Calibri non-italic, MED_GRAY (#B0AFA8), right-aligned, full content
    width. Default: single-line, T=8.00, H=0.25. For multi-source or long
    citations that must wrap, pass lines=2 or lines=3; the box grows upward
    while the bottom edge stays fixed at 8.25.
    """
    h = CITATION_LINE_H * lines
    t = CITATION_BOTTOM - h
    tb = slide.shapes.add_textbox(
        Inches(CITATION_LEFT), Inches(t), Inches(CITATION_W), Inches(h))
    tf = tb.text_frame
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    r = p.add_run()
    r.text = text
    r.font.size = Pt(11)
    r.font.italic = False
    r.font.name = "Calibri"
    r.font.color.rgb = MED_GRAY
    return tb


def add_rounded_card(slide, left, top, w, h, border_rgb, fill_rgb, role='body'):
    """Rounded rectangle with canonical text-frame setup.

    role='body' (default): multi-paragraph card content; vertical_anchor=TOP.
    role='label': a short diagram / cycle / connector label; vertical_anchor=MIDDLE so
    the text centers in the card. Pair label cards with bold runs and
    fit_font_size(role='label'), and size sibling labels uniformly (the group minimum).
    See style-guide.md "Vertical Text Alignment"."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(w), Inches(h))
    shape.line.color.rgb = border_rgb
    shape.line.width = Pt(1)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_rgb
    shape.adjustments[0] = 0.08
    # Strip the auto-added <p:style> theme-color block. python-pptx attaches
    # it on every preset autoshape, but it conflicts with the explicit srgb
    # fill/line set above and causes PowerPoint to "repair and remove" the
    # shape on file open. (Critical Rule 8.)
    sp_el = shape._element
    style_el = sp_el.find(qn('p:style'))
    if style_el is not None:
        sp_el.remove(style_el)
    tf = shape.text_frame
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.20)
    tf.margin_top = tf.margin_bottom = Inches(0.15)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE if role == 'label' else MSO_ANCHOR.TOP
    return shape


def add_body_textbox(slide, left, top, w, h):
    """Plain text box with canonical defaults (auto_size locked, TOP anchor)."""
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    return tb


def add_paragraph(tf, text, size=24, bold=False, color=CHARCOAL,
                  bullet=False, space_before=None, alignment=PP_ALIGN.LEFT,
                  first=False):
    """Add a paragraph; `first=True` reuses tf.paragraphs[0] (empty default).

    bullet=True applies set_bullet() + set_hanging_indent(). Compute `size`
    at the call site via fit_font_size(); never pass a role floor as a default.
    """
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = alignment
    if space_before is not None:
        p.space_before = Pt(space_before)
    if bullet:
        set_bullet(p)
        set_hanging_indent(p)
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = "Calibri"
    r.font.color.rgb = color
    return p


# --- Sizing ------------------------------------------------------------------
def estimate_text_height(text, box_width_inches, font_size_pt, line_spacing=1.25):
    """Estimate rendered text height in inches.

    Use BEFORE setting shape height to verify content fits; run_quality_check()
    uses the same estimate to detect overflow after the fact.
    """
    chars_per_line = max(1, box_width_inches * 72 / (font_size_pt * 0.50))
    lines_needed = math.ceil(len(text) / chars_per_line)
    return lines_needed * font_size_pt * line_spacing / 72


ROLE_RANGES = {              # (ceiling, floor) pt, per Role-Based Font Hierarchy
    'body':           (28, 22),
    'body_secondary': (22, 20),
    'caption':        (22, 18),
    'label':          (26, 18),
    'micro':          (16, 12),
}


def fit_font_size(paragraph_texts, box_w, box_h, role='body'):
    """Largest size in the role's range whose stacked estimated height fits the box.

    Compute-then-clamp (Critical Rule 1): start at the role ceiling, step down
    1pt while the estimated total height exceeds the box height, stop at the
    role floor. The floor is a clamp on the computed value, never the starting
    size — do not write a floor literal as a default. The box itself must
    respect the content-area and grid limits (an oversized box does not make a
    size "fit"), and the overflow check in run_quality_check() still applies.
    """
    ceiling, floor = ROLE_RANGES[role]
    size = ceiling
    while size > floor:
        total = sum(estimate_text_height(t, box_w, size) for t in paragraph_texts)
        if total <= box_h * 0.96:    # margin for paragraph spacing
            return size
        size -= 1
    return floor


def add_caption(slide, figure_shape, text):
    """Figure caption below a chart/picture: computed 18-22pt, Charcoal, left-aligned
    at figure width, one tier above the 11pt citation.

    Mandated path for every figure caption (the caption analog of add_citation).
    Computes the size, sizes the box from the wrapped text, and tags the shape
    'FigCaption' so run_quality_check classifies it as a caption by name —
    independent of how many lines it wraps to, so a 2-line caption never trips
    the body floor."""
    fig_w = figure_shape.width / IN
    cap_pt = fit_font_size([text], box_w=fig_w, box_h=0.95, role='caption')
    box_h = estimate_text_height(text, fig_w, cap_pt) + 0.08   # reserve from actual text
    top = figure_shape.top + figure_shape.height + Inches(0.05)
    tb = slide.shapes.add_textbox(
        figure_shape.left, top, figure_shape.width, Inches(box_h))
    tb.name = "FigCaption"                          # deterministic classification marker
    tf = tb.text_frame
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT                      # matches the source; never centered
    r = p.add_run()
    r.text = text
    r.font.size = Pt(cap_pt)
    r.font.italic = False
    r.font.name = "Calibri"
    r.font.color.rgb = CHARCOAL
    return tb


def add_title(slide, text):
    """Set the Title placeholder: 36pt Calibri Bold, Charcoal, left-aligned."""
    ph = slide.placeholders[0]
    ph.text = ""
    p = ph.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    r.font.size = Pt(36)
    r.font.bold = True
    r.font.name = "Calibri"
    r.font.color.rgb = CHARCOAL
    return ph


def remove_existing_slides(prs):
    """Clear the template's pre-existing slides. Drops the relationship first
    to avoid duplicate-name warnings in the saved ZIP."""
    xml_slides = prs.slides._sldIdLst
    for sldId in list(xml_slides):
        prs.part.drop_rel(sldId.get(qn('r:id')))
        xml_slides.remove(sldId)


# --- Charts ------------------------------------------------------------------
def fix_chart_fonts(chart, axis_pt=14, legend_pt=14):
    """Set font size on all chart text elements (axes, legend, data labels).

    python-pptx generates charts with hardcoded small sizes (10-12pt) in
    <c:txPr>/<a:defRPr sz="..."> that general style settings never override.
    Call immediately after add_chart(), for every chart. Leaves the
    chartSpace-level default (chart title) alone.
    """
    chart_el = chart._element
    for txpr in chart_el.iter(qn('c:txPr')):
        parent_tag = txpr.getparent().tag.split('}')[1]
        if parent_tag == 'chartSpace':
            continue   # leave the chart-level default alone
        target_sz = str((legend_pt if parent_tag == 'legend' else axis_pt) * 100)
        defrpr = txpr.find('.//' + qn('a:defRPr'))
        if defrpr is not None:
            defrpr.set('sz', target_sz)
        else:
            for p in txpr.findall('.//' + qn('a:p')):
                ppr = p.find(qn('a:pPr'))
                if ppr is None:
                    ppr = etree.SubElement(p, qn('a:pPr'))
                    p.insert(0, ppr)
                dr = etree.SubElement(ppr, qn('a:defRPr'))
                dr.set('sz', target_sz)


def fix_invert_if_negative(chart):
    """Disable invertIfNegative on every series so negative bars keep their fill.

    Without this, PowerPoint defaults to inverting the fill on negative values
    (bars render white or unfilled). Call on any bar/column chart whose data
    contains negative values.
    """
    for series in chart.series:
        ser_el = series._element
        for old in ser_el.findall(qn('c:invertIfNegative')):
            ser_el.remove(old)
        inv = etree.SubElement(ser_el, qn('c:invertIfNegative'))
        inv.set('val', '0')
        # Position after <c:tx> element
        tx_el = ser_el.find(qn('c:tx'))
        if tx_el is not None:
            tx_el.addnext(inv)


# --- Fills -------------------------------------------------------------------
def set_fill_alpha(shape, alpha_pct=20):
    """Inject <a:alpha> into a solid fill's srgbClr. OOXML alpha = thousandths of a percent.

    Gives a shape a translucent solid fill while fill.fore_color.rgb stays the
    literal hex (useful for banner or overlay shapes). Same XML-edit pattern as
    fix_chart_fonts() and add_rounded_card()'s <p:style> removal.
    Usage: shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor(0xF0, 0xEF, 0xEC)
           set_fill_alpha(shape, 20)
    """
    srgb = shape.fill._xPr.find('.//' + qn('a:solidFill') + '/' + qn('a:srgbClr'))
    if srgb is not None and srgb.find(qn('a:alpha')) is None:
        srgb.append(srgb.makeelement(qn('a:alpha'), {'val': str(alpha_pct * 1000)}))


# --- Images ------------------------------------------------------------------
def add_image_proportional(slide, img_path, area_left, area_top, area_w, area_h):
    """Fit image proportionally within bounding box: centered horizontally, top-aligned.

    The single required path for every embedded image (Critical Rule 6 makes
    image embed a last resort). Never stretch an image to fill both dimensions
    regardless of its native aspect ratio. Requires Pillow.
    """
    from PIL import Image   # deferred: Pillow only needed when embedding images
    with Image.open(img_path) as im:
        native_w, native_h = im.size
    aspect = native_w / native_h
    if area_w / area_h > aspect:
        fit_h = area_h
        fit_w = area_h * aspect
    else:
        fit_w = area_w
        fit_h = area_w / aspect
    left = area_left + (area_w - fit_w) / 2.0
    top = area_top
    return slide.shapes.add_picture(
        img_path, Inches(left), Inches(top), Inches(fit_w), Inches(fit_h))


# --- Tables ------------------------------------------------------------------
def fix_table_fonts(table_shape, size_pt=18, align='ctr'):
    """Set font size AND alignment on all table cells via XML.

    Table cells do not inherit slide defaults; run.font.size alone misses
    empty cells and can be overridden by paragraph defaults. Call after
    populating any table. Target 18pt; 14pt only for genuinely dense tables.
    """
    sz_val = str(size_pt * 100)
    tbl_el = None
    for el in table_shape._element.iter():
        if el.tag.split('}')[-1] == 'tbl':
            tbl_el = el
            break
    if tbl_el is None:
        return
    for tc in tbl_el.iter(qn('a:tc')):
        for p in tc.iter(qn('a:p')):
            ppr = p.find(qn('a:pPr'))
            if ppr is None:
                ppr = etree.SubElement(p, qn('a:pPr'))
                p.insert(0, ppr)
            ppr.set('algn', align)                     # alignment
            dr = ppr.find(qn('a:defRPr'))
            if dr is None:
                dr = etree.SubElement(ppr, qn('a:defRPr'))
            dr.set('sz', sz_val)                       # paragraph default font
            for rpr in p.iter(qn('a:rPr')):
                rpr.set('sz', sz_val)                  # explicit run font


def fix_table_style(table_shape):
    """Set table style to the canonical safe built-in GUID.

    {2D5ABB26-0587-4C30-8999-92F81FD0307C} = "No Style, No Grid": minimal
    styling, no alignment override, LibreOffice 26 compatible. python-pptx's
    default null GUID {00000000-...} crashes LibreOffice 26 on PPTX import;
    {5C22544A-...} ("Medium Style 2 - Accent 1") silently overrides cell-level
    alignment. Call after add_table() and fix_table_fonts().
    """
    SAFE_STYLE = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'
    tbl_el = None
    for el in table_shape._element.iter():
        if el.tag.split('}')[-1] == 'tbl':
            tbl_el = el
            break
    if tbl_el is None:
        return
    tbl_pr = tbl_el.find(qn('a:tblPr'))
    if tbl_pr is None:
        tbl_pr = etree.SubElement(tbl_el, qn('a:tblPr'))
        tbl_el.insert(0, tbl_pr)
    sid = tbl_pr.find(qn('a:tableStyleId'))
    if sid is None:
        sid = etree.SubElement(tbl_pr, qn('a:tableStyleId'))
    sid.text = SAFE_STYLE
