#!/usr/bin/env python3
"""Pre-Save Structural Quality Check for style-guide PPTX decks.

The issue-message strings, the WARNING: prefix convention, the error-vs-warning
split, and the room_count message format are load-bearing: a calling conversion
workflow may parse them to decide dispositions. Do not reword any message string.

Usage (import, in a generator script before prs.save()):
    import sys; sys.path.insert(0, '<path to this style-guide folder>')
    from quality_check import run_quality_check
    issues = run_quality_check(prs)                                  # direct generation
    issues = run_quality_check(prs, conversion_source='slides.tex')  # Beamer conversion

Usage (CLI, on a saved deck):
    python3 quality_check.py <deck.pptx> [--conversion-source <slides.tex>]

Exit status: nonzero when any blocking error is found; 0 on pass (with or
without warnings).
"""

from pptx.util import Pt


def run_quality_check(prs, conversion_source=None):
    """
    Structural quality check. Returns a list of issue strings.
    Empty list = all clear. Run before prs.save().

    conversion_source: path to the Beamer slides.tex when this PPTX is a
    conversion; None for direct generation. Controls the severity of the
    uniform-at-floor check (#18): blocking error at generation (the generator
    controls sizes and must compute them), surfaced warning carrying room_count
    at conversion. room_count (at-floor body shapes whose text area affords a
    larger size) tells the calling workflow whether the fix is a per-box
    recompute in the PPTX (room_count>=1 -> fix in place) or a reduce-content
    decision (room_count==0 -> surface to the user); it is not categorically
    upstream.

    Catches:
      1. Shapes outside content area bounds
      2. Overlapping shapes on the same slide
      3. Chart axis/legend font < 14pt (hardcoded in XML by python-pptx)
      4. Line chart legend not positioned RIGHT
      5. Bar chart series missing invertIfNegative=0 (causes unfilled negative bars)
      6. Table using built-in style GUID that overrides cell alignment
      7. Table cell font < 14pt
      8. Conversion coverage — flags when >40% of slides are single-image-only
         (with reclassification guidance: hybrid, native shapes, or native chart)
      9. Vertical alignment is MIDDLE on multi-line content shapes (should be TOP)
     10. Text box body font < 20pt (excludes chart axes, tables, and captions; a caption is
         recognized by its FigCaption shape name (set by add_caption()), or by geometry as a
         fallback, and held to the 18pt caption floor — one tier above the 11pt citation)
     11. Chart axis number format left as default (warns to apply explicit number_format)
     12. Bullet paragraphs missing hanging indent (negative indent attribute)
     13. Text box body font below target (20-21pt) — warning, not blocker
     14. Text overflow — estimated text height exceeds shape height by >10%
     15. Off-spec gray color on body text — gray-toned run color not in the approved
         gray whitelist (catches regressions like #3A3A3A in place of Charcoal)
     18. Uniform-at-floor signature — >50% of body-role runs within 1pt of the 22pt
         floor (min 8 body runs). ERROR at generation; WARNING carrying room_count
         (at-floor body shapes that afford a larger size) when conversion_source is set.
     19. Box under-fill — estimated text height under 60% of the box height while a
         larger in-role size would fit (WARNING; compute the size, then clamp)
     20. Caption under-fill — a caption (FigCaption name, or wide-and-short geometry)
         rendered more than 1pt below the largest caption-role size its own box affords
         (ERROR; the caption tier is the regression this hardens — the caption analog of
         #19, but blocking, because a caption shrunk toward the citation is the defect)
    """
    from pptx.oxml.ns import qn
    from pptx.enum.chart import XL_LEGEND_POSITION

    IN = 914400
    CONTENT_LEFT = 1.10;  CONTENT_TOP = 1.95
    CONTENT_W   = 13.80
    # Body content must end above CONTENT_BOTTOM (leaves room for citation band).
    # Citations live in the citation band at T=8.00 to T=8.25.
    # Actual footer placeholder begins at 8.38.
    CONTENT_BOTTOM  = 8.00   # body content max bottom edge
    CITATION_BOTTOM = 8.25   # citation max bottom edge
    FOOTER_TOP      = CONTENT_BOTTOM  # legacy alias
    MAX_RIGHT = CONTENT_LEFT + CONTENT_W   # 14.90

    # Null GUID — python-pptx's add_table() default. Crashes LibreOffice 26
    # on PPTX import (confirmed 2026-05-06). Treat as a save blocker.
    NULL_STYLE = '{00000000-0000-0000-0000-000000000000}'
    # "Medium Style 2 - Accent 1" — silently overrides cell-level paragraph alignment.
    OVERRIDE_STYLE = '{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}'
    # Canonical safe built-in: "No Style, No Grid" — minimal styling, no alignment override.
    SAFE_STYLE = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'

    LINE_TYPES = {
        'LINE', 'LINE_MARKERS', 'LINE_STACKED', 'LINE_MARKERS_STACKED',
        'LINE_100_PERCENT', 'LINE_MARKERS_100_PERCENT',
    }
    BAR_TYPES = {
        'BAR_CLUSTERED', 'BAR_STACKED', 'BAR_STACKED_100',
        'COLUMN_CLUSTERED', 'COLUMN_STACKED', 'COLUMN_STACKED_100',
    }

    issues = []

    for si, slide in enumerate(prs.slides, start=1):
        # Skip hidden slides (presenter notes, not presented)
        if slide._element.get('show') == '0':
            continue
        lbl = f"Slide {si}"

        # Collect non-placeholder, non-background content shapes
        content = []
        for s in slide.shapes:
            if s.is_placeholder or s.left is None:
                continue
            l, t = s.left/IN, s.top/IN
            w, h = s.width/IN, s.height/IN
            if l <= 0.1 and t <= 0.1 and w >= 14 and h >= 8:
                continue  # intentional full-slide background — skip
            content.append((s, l, t, w, h))

        # 1. Position bounds (role-aware)
        for s, l, t, w, h in content:
            n = s.name
            # Detect citation role by position — allowed in citation band
            is_citation = (7.4 <= t <= 8.3 and h <= 0.85)
            if l < CONTENT_LEFT - 0.05:
                issues.append(f"{lbl} '{n}': left={l:.2f}\" (need ≥{CONTENT_LEFT}\")")
            if t < CONTENT_TOP - 0.05 and not is_citation:
                issues.append(f"{lbl} '{n}': top={t:.2f}\" (need ≥{CONTENT_TOP}\")")
            # Body content stays above CONTENT_BOTTOM; citations stay above CITATION_BOTTOM
            if is_citation:
                if t + h > CITATION_BOTTOM + 0.05:
                    issues.append(f"{lbl} '{n}': citation bottom={t+h:.2f}\" (need ≤{CITATION_BOTTOM}\" — would enter footer strip)")
            else:
                if t + h > CONTENT_BOTTOM + 0.05:
                    issues.append(f"{lbl} '{n}': bottom={t+h:.2f}\" (need ≤{CONTENT_BOTTOM}\" — citation band)")
            if l + w > MAX_RIGHT + 0.10:
                issues.append(f"{lbl} '{n}': right={l+w:.2f}\" (need ≤{MAX_RIGHT}\")")

        # 2. Bounding-box overlap between shapes on the same slide
        for i, (s1, l1, t1, w1, h1) in enumerate(content):
            for s2, l2, t2, w2, h2 in content[i+1:]:
                h_overlap = l1 < l2 + w2 - 0.02 and l2 < l1 + w1 - 0.02
                v_overlap = t1 < t2 + h2 - 0.02 and t2 < t1 + h1 - 0.02
                if h_overlap and v_overlap:
                    issues.append(f"{lbl}: shapes overlap — '{s1.name}' and '{s2.name}'")

        # 3-5. Chart checks
        for s in slide.shapes:
            if not s.has_chart:
                continue
            chart  = s.chart
            ct     = chart.chart_type.name if chart.chart_type else ''
            sn     = s.name

            # 3. Axis / legend font size must be ≥ 14pt (python-pptx defaults to 10-11pt)
            for txpr in chart._element.iter(qn('c:txPr')):
                parent = txpr.getparent().tag.split('}')[1]
                if parent == 'chartSpace':
                    continue
                dr = txpr.find('.//' + qn('a:defRPr'))
                if dr is not None:
                    sz = dr.get('sz', '')
                    if sz and int(sz) < 1400:
                        issues.append(
                            f"{lbl} '{sn}': chart {parent} font {int(sz)//100}pt "
                            f"(need ≥14pt) — run fix_chart_fonts()"
                        )

            # 4. Line chart legend must be RIGHT
            if ct in LINE_TYPES:
                if chart.legend is None:
                    issues.append(f"{lbl} '{sn}': line chart has no legend")
                elif chart.legend.position != XL_LEGEND_POSITION.RIGHT:
                    issues.append(
                        f"{lbl} '{sn}': line chart legend is not RIGHT "
                        f"(currently {chart.legend.position}) — set to XL_LEGEND_POSITION.RIGHT"
                    )

            # 5. Bar chart series must have invertIfNegative=0
            if ct in BAR_TYPES:
                for ser in chart.series:
                    inv = ser._element.find(qn('c:invertIfNegative'))
                    if inv is None or inv.get('val', '1') != '0':
                        issues.append(
                            f"{lbl} '{sn}': bar series '{ser.name}' missing "
                            f"invertIfNegative=0 — negative bars will appear white/unfilled"
                        )

        # 6-7. Table checks
        for s in slide.shapes:
            if not s.has_table:
                continue
            sn = s.name
            tbl_el = next(
                (el for el in s._element.iter() if el.tag.split('}')[-1] == 'tbl'), None
            )
            if tbl_el is None:
                continue

            # 6. Table style GUID checks.
            #    a) Null GUID crashes LibreOffice 26 on PPTX import (BLOCKER).
            #    b) OVERRIDE_STYLE silently overrides cell-level paragraph alignment.
            tbl_pr = tbl_el.find(qn('a:tblPr'))
            if tbl_pr is not None:
                sid = tbl_pr.find(qn('a:tableStyleId'))
                if sid is not None and sid.text:
                    sid_norm = sid.text.strip().upper()
                    if sid_norm == NULL_STYLE.upper():
                        issues.append(
                            f"{lbl} '{sn}': table uses null GUID {NULL_STYLE} "
                            f"— crashes LibreOffice 26 on PPTX import. Run "
                            f"fix_table_style(table_shape) to set {SAFE_STYLE} "
                            f"(\"No Style, No Grid\")."
                        )
                    elif sid_norm == OVERRIDE_STYLE.upper():
                        issues.append(
                            f"{lbl} '{sn}': table uses built-in style {OVERRIDE_STYLE} "
                            f"which overrides cell alignment — run "
                            f"fix_table_style(table_shape) to set {SAFE_STYLE}."
                        )

            # 7. Table cell font size must be ≥ 14pt
            reported = False
            for tc in tbl_el.iter(qn('a:tc')):
                if reported: break
                for p in tc.iter(qn('a:p')):
                    ppr = p.find(qn('a:pPr'))
                    if ppr is not None:
                        dr = ppr.find(qn('a:defRPr'))
                        if dr is not None:
                            sz = dr.get('sz', '')
                            if sz and int(sz) < 1400:
                                issues.append(
                                    f"{lbl} '{sn}': table cell defRPr {int(sz)//100}pt "
                                    f"(need ≥18pt) — run fix_table_fonts()"
                                )
                                reported = True; break
                    if reported: break
                    for rpr in p.iter(qn('a:rPr')):
                        sz = rpr.get('sz', '')
                        if sz and int(sz) < 1400:
                            issues.append(
                                f"{lbl} '{sn}': table cell rPr {int(sz)//100}pt "
                                f"(need ≥18pt) — run fix_table_fonts()"
                            )
                            reported = True; break
                    if reported: break

    # 8. Conversion coverage — flag blanket image embedding
    image_only_slides = 0
    for si2, slide2 in enumerate(prs.slides, start=1):
        shapes = [s for s in slide2.shapes if not s.is_placeholder]
        if len(shapes) == 1 and shapes[0].shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            image_only_slides += 1
    total = len(prs.slides)
    if total > 0 and image_only_slides / total > 0.4:
        issues.append(
            f"CONVERSION COVERAGE: {image_only_slides} of {total} slides "
            f"({image_only_slides*100//total}%) contain only a single embedded image "
            f"with no native charts, tables, or text boxes. Reclassify each image-only "
            f"slide as: (a) Hybrid — if the Beamer slide has a text column and a visual "
            f"column, recreate text natively at 22pt+ and image-embed only the visual; "
            f"(b) Native shapes — if the visual is colored boxes, flowcharts, or "
            f"box-and-arrow diagrams, recreate entirely with add_shape(); "
            f"(c) Native chart — if the visual is a standard bar/line/scatter chart, "
            f"recreate with add_chart(). A full-slide image embed is only permitted "
            f"when the slide has no separable text content AND the visual cannot be "
            f"decomposed into rectangles, arrows, and text labels."
        )

    # _role_floor: classify a shape's role from name, then position and size.
    # Hoisted here (ahead of check #9) so #9 can exempt label-role shapes; reused by
    # #10, #18, #19, #20. In-shape label floor is 18pt (a label card holds short,
    # readable, usually bold text; 16pt was the conversion under-fill defect).
    def _role_floor(left_in, top_in, width_in, height_in, name=""):
        if name.startswith("FigCaption"):
            return ("caption", 18)
        if 7.4 <= top_in <= 8.3 and height_in <= 0.85:
            return ("citation", 11)
        if width_in < 2.5 and height_in < 0.6:
            return ("micro-label", 12)
        if width_in >= 3.5 and height_in < 0.6:
            return ("caption", 18)
        if width_in < 3.5 and height_in < 1.2:
            return ("in-shape label", 18)
        return ("body", 22)

    # 9. Vertical alignment must be TOP on multi-line BODY content shapes.
    #    Label-role shapes (short text in a small box) are deliberately centered
    #    (MIDDLE) and are exempt — see "Vertical Text Alignment".
    for si_va, slide_va in enumerate(prs.slides, start=1):
        if slide_va._element.get('show') == '0':
            continue
        lbl_va = f"Slide {si_va}"
        for s in slide_va.shapes:
            if s.is_placeholder or not s.has_text_frame:
                continue
            if s.shape_type == 13:  # picture
                continue
            if s.left is None:
                continue
            sn = s.name
            role_va, _flva = _role_floor(s.left/IN, s.top/IN, s.width/IN, s.height/IN, sn)
            if role_va != 'body':
                continue   # labels, captions, micro-labels may be MIDDLE
            bodyPr = s.text_frame._txBody.find(qn('a:bodyPr'))
            if bodyPr is not None:
                anc = bodyPr.get('anchor', 't')  # default is top
                # Count text paragraphs with content
                para_count = sum(1 for p in s.text_frame.paragraphs if p.text.strip())
                if anc == 'ctr' and para_count > 1:
                    issues.append(
                        f"{lbl_va} '{sn}': vertical alignment is MIDDLE on multi-line "
                        f"body content shape — set text_frame.vertical_anchor = MSO_ANCHOR.TOP"
                    )

    # 10. Role-based font floor check.
    #     Role is inferred from the shape name first, then position and size:
    #       - Name starts with "FigCaption" (set by add_caption()): floor = 18pt — the
    #         primary, deterministic caption path, independent of how the caption wraps.
    #       - Citation band (T in 7.4-8.3, H <= 0.85): floor = 11pt
    #       - Small annotation (W < 2.5" AND H < 0.6"): floor = 12pt (micro-label role)
    #       - Caption by geometry (W >= 3.5" AND H < 0.6"): floor = 18pt — fallback for a
    #         wide ~1-line caption in a deck this guide did not generate (no FigCaption name).
    #       - In-shape label (W < 3.5" AND H < 1.2"): floor = 18pt (label role)
    #       - Everything else: floor = 22pt (body role)
    #     Violations below the role floor are errors.
    #     _role_floor is defined above (hoisted ahead of check #9 so #9 can use it).

    for si3, slide3 in enumerate(prs.slides, start=1):
        lbl3 = f"Slide {si3}"
        for s in slide3.shapes:
            # Skip placeholders, charts, tables, and images
            if s.is_placeholder or s.has_chart or s.has_table:
                continue
            if s.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                continue
            if not s.has_text_frame:
                continue
            if s.left is None:
                continue
            sn = s.name
            l_in, t_in = s.left/IN, s.top/IN
            w_in, h_in = s.width/IN, s.height/IN
            role, floor_pt = _role_floor(l_in, t_in, w_in, h_in, sn)
            for p in s.text_frame.paragraphs:
                for run in p.runs:
                    if run.font.size is not None and run.font.size < Pt(floor_pt):
                        issues.append(
                            f"{lbl3} '{sn}': {role} font {run.font.size.pt:.0f}pt "
                            f"(need >={floor_pt}pt for this role) — "
                            f"{'reduce content' if role == 'body' else 'adjust role or size'}"
                        )
                        break  # one issue per shape is enough
                else:
                    continue
                break  # break out of paragraph loop too

    # 10. Chart axis number format — warn if left as default "General"
    for si4, slide4 in enumerate(prs.slides, start=1):
        lbl4 = f"Slide {si4}"
        for s in slide4.shapes:
            if not s.has_chart:
                continue
            chart = s.chart
            sn = s.name
            # Check value axis number format
            try:
                va = chart.value_axis
                if va and va.tick_labels:
                    nf = va.tick_labels.number_format
                    if nf in (None, '', 'General', '0.##############'):
                        issues.append(
                            f"{lbl4} '{sn}': chart value axis uses default number format "
                            f"'{nf}' — set explicit number_format ($, %, #,##0, etc.) "
                            f"matching the Beamer source data units"
                        )
            except Exception:
                pass  # some chart types lack a value axis

    # 11. Bullet paragraphs missing hanging indent
    for si5, slide5 in enumerate(prs.slides, start=1):
        lbl5 = f"Slide {si5}"
        for s in slide5.shapes:
            if s.is_placeholder or not s.has_text_frame:
                continue
            sn = s.name
            for p in s.text_frame.paragraphs:
                pPr = p._p.find(qn('a:pPr'))
                if pPr is None:
                    continue
                # Check if paragraph has a bullet (buChar or buAutoNum)
                has_bullet = (pPr.find(qn('a:buChar')) is not None or
                              pPr.find(qn('a:buAutoNum')) is not None)
                if has_bullet:
                    indent = pPr.get('indent')
                    if indent is None or int(indent) >= 0:
                        issues.append(
                            f"{lbl5} '{sn}': bullet paragraph missing hanging indent "
                            f"— call set_hanging_indent(paragraph)"
                        )
                        break  # one issue per shape

    # 12. BODY text box font below target (22-24pt) but above minimum (20pt).
    #     WARNING only — does not block save. Surfaces below-target body sizing
    #     so the generator must consciously decide rather than silently accepting.
    #     Scoped to body role (like check #9): labels (18-26) and captions (18-22)
    #     have their own ranges, so a 20-21pt label/caption is in-range, not below target.
    warnings = []
    for si6, slide6 in enumerate(prs.slides, start=1):
        lbl6 = f"Slide {si6}"
        for s in slide6.shapes:
            if s.is_placeholder or s.has_chart or s.has_table:
                continue
            if s.shape_type == 13:
                continue
            if not s.has_text_frame:
                continue
            if s.left is None:
                continue
            role6, _fl6 = _role_floor(s.left/IN, s.top/IN, s.width/IN, s.height/IN, s.name)
            if role6 != 'body':
                continue   # labels/captions have their own role floors
            sn = s.name
            for p in s.text_frame.paragraphs:
                for run in p.runs:
                    if run.font.size is not None and Pt(20) <= run.font.size < Pt(22):
                        warnings.append(
                            f"{lbl6} '{sn}': text box font {run.font.size.pt:.0f}pt "
                            f"(target is 22-24pt) — can content be reduced to allow "
                            f"a larger font?"
                        )
                        break
                else:
                    continue
                break
    if warnings:
        for w in warnings:
            issues.append(f"WARNING: {w}")

    # 13. Text overflow — estimated text height exceeds shape height
    import math
    for si7, slide7 in enumerate(prs.slides, start=1):
        lbl7 = f"Slide {si7}"
        for s in slide7.shapes:
            if s.is_placeholder or not s.has_text_frame:
                continue
            if s.has_chart or s.has_table:
                continue
            if s.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                continue
            sn = s.name
            shape_w = s.width / IN
            shape_h = s.height / IN
            if shape_h < 0.1:
                continue  # skip decorative/spacer shapes
            total_text_h = 0
            for p in s.text_frame.paragraphs:
                p_text = p.text
                if not p_text.strip():
                    total_text_h += 0.15  # blank paragraph spacing
                    continue
                font_pt = 20  # default assumption
                if p.runs and p.runs[0].font.size is not None:
                    font_pt = p.runs[0].font.size.pt
                chars_per_line = max(1, shape_w * 72 / (font_pt * 0.50))
                lines = math.ceil(len(p_text) / chars_per_line)
                total_text_h += lines * font_pt * 1.25 / 72
            if total_text_h > shape_h * 1.1:  # 10% tolerance
                overflow_pct = int((total_text_h / shape_h - 1) * 100)
                issues.append(
                    f"{lbl7} '{sn}': TEXT OVERFLOW — estimated {total_text_h:.2f}\" "
                    f"of text in {shape_h:.2f}\" box ({overflow_pct}% over) — "
                    f"reduce content, increase box height, or split across slides"
                )

    # 15. Off-spec gray color on body text.
    #     A run's color is "gray-toned" when max(R,G,B) - min(R,G,B) <= 15.
    #     Gray-toned runs must match one of the approved palette grays below.
    #     This catches near-Charcoal regressions like #3A3A3A, #555555, #333333
    #     without flagging colored accent runs (SlateNavy emphasis, DeepTeal
    #     highlight text, etc.), which are NOT gray-toned and so are skipped.
    #
    #     Carve-outs (already implied by the gray-tone filter; stated for clarity):
    #       - Citation text boxes are skipped by position (citation band).
    #       - Charts are skipped (has_chart).
    #       - Tables are skipped (has_table).
    #       - Images are skipped (shape_type == 13).
    #       - Accent-colored runs are skipped because their colors are not gray-toned.
    APPROVED_GRAYS = {
        (0x4D, 0x4D, 0x4D),  # Charcoal — primary body text
        (0xB0, 0xAF, 0xA8),  # MedGray — citation only
        (0x6C, 0x7A, 0x89),  # Medium Gray — connectors/neutral states
        (0x42, 0x55, 0x63),  # Slate Blue — default outlines
        (0xF0, 0xEF, 0xEC),  # LightGray — spare fill
        (0xFF, 0xFF, 0xFF),  # White — text on dark fills
        (0x00, 0x00, 0x00),  # Black — occasional emphasis
    }
    for si8, slide8 in enumerate(prs.slides, start=1):
        if slide8._element.get('show') == '0':
            continue
        lbl8 = f"Slide {si8}"
        for s in slide8.shapes:
            if s.is_placeholder or s.has_chart or s.has_table:
                continue
            if s.shape_type == 13:
                continue
            if not s.has_text_frame:
                continue
            # Skip citation shapes (authorized MedGray by role)
            if s.left is not None:
                t_in = s.top / IN
                h_in = s.height / IN
                if 7.4 <= t_in <= 8.3 and h_in <= 0.85:
                    continue
            sn = s.name
            reported_this_shape = False
            for p in s.text_frame.paragraphs:
                if reported_this_shape:
                    break
                for run in p.runs:
                    try:
                        rgb = run.font.color.rgb
                    except AttributeError:
                        continue
                    if rgb is None:
                        continue
                    hex_str = str(rgb)
                    if len(hex_str) != 6:
                        continue
                    try:
                        r = int(hex_str[0:2], 16)
                        g = int(hex_str[2:4], 16)
                        b = int(hex_str[4:6], 16)
                    except ValueError:
                        continue
                    spread = max(r, g, b) - min(r, g, b)
                    if spread > 15:
                        continue   # colored accent, not gray-toned — skip
                    if (r, g, b) in APPROVED_GRAYS:
                        continue
                    issues.append(
                        f"{lbl8} '{sn}': off-spec gray #{hex_str.upper()} on body text "
                        f"— use #4D4D4D (Charcoal); MedGray #B0AFA8 is reserved for citations"
                    )
                    reported_this_shape = True
                    break

    # 16. PowerPoint repair-warning prevention: <p:style> conflicting with explicit srgb fill.
    #     python-pptx auto-attaches a <p:style> theme-color block to every preset autoshape.
    #     When the generator also sets explicit srgb fill or line via spPr (as add_rounded_card
    #     does), PowerPoint detects the conflict and silently strips the shape during repair
    #     ("PowerPoint couldn't read some content - Repaired and removed it"). Critical Rule 8.
    #
    #     Detection: shape has both <p:style> AND explicit <a:solidFill> in spPr. Either:
    #       - drop <p:style> after add_shape() (preferred; bake into helpers), or
    #       - rely on <p:style> theme colors and remove the explicit srgb fill.
    p_ns = 'http://schemas.openxmlformats.org/presentationml/2006/main'
    a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    for si9, slide9 in enumerate(prs.slides, start=1):
        if slide9._element.get('show') == '0':
            continue
        lbl9 = f"Slide {si9}"
        for s in slide9.shapes:
            if s.is_placeholder or s.has_chart or s.has_table:
                continue
            if s.shape_type == 13:  # picture
                continue
            sp_el = s._element
            style_el = sp_el.find(f'{{{p_ns}}}style')
            sp_pr = sp_el.find(f'{{{p_ns}}}spPr')
            if style_el is not None and sp_pr is not None:
                has_explicit_fill = sp_pr.find(f'{{{a_ns}}}solidFill') is not None
                has_explicit_line = sp_pr.find(f'{{{a_ns}}}ln') is not None
                if has_explicit_fill or has_explicit_line:
                    issues.append(
                        f"{lbl9} '{s.name}': <p:style> theme-color block conflicts with "
                        f"explicit srgb fill/line in spPr — PowerPoint will repair-and-remove "
                        f"on file open. Drop the <p:style> element after add_shape(); see "
                        f"add_rounded_card() for the canonical fix."
                    )

    # 17. PowerPoint repair-warning prevention: <a:buChar> without paired <a:buFont>.
    #     PowerPoint requires a typeface to render the bullet character. A bare <a:buChar>
    #     element is flagged as malformed and the bullet is stripped during repair, so the
    #     paragraph renders without its leading bullet. Critical Rule 8.
    for si10, slide10 in enumerate(prs.slides, start=1):
        if slide10._element.get('show') == '0':
            continue
        lbl10 = f"Slide {si10}"
        for s in slide10.shapes:
            if not s.has_text_frame:
                continue
            sn = s.name
            for p in s.text_frame.paragraphs:
                pPr = p._p.find(qn('a:pPr'))
                if pPr is None:
                    continue
                buChar = pPr.find(qn('a:buChar'))
                if buChar is None:
                    continue
                buFont = pPr.find(qn('a:buFont'))
                if buFont is None or not buFont.get('typeface'):
                    issues.append(
                        f"{lbl10} '{sn}': <a:buChar> without paired <a:buFont typeface=...> "
                        f"— PowerPoint will repair-and-remove the bullet. Use set_bullet() "
                        f"which always pairs the two."
                    )
                    break  # one issue per shape

    # _affords_room: largest body size (28->22) whose estimated text height fits
    # the shape's TEXT AREA (saved box minus live text-frame margins). Same
    # compute-then-clamp as fit_font_size(role='body'); shared by #18 (room_count)
    # and #19 so the two cannot drift. Read live tf.margin_* (a card reads
    # 0.20/0.15, a plain textbox 0.10/0.05); fall back to 0.20/0.15 only on None
    # (a conservative under-measure that fails safe toward surfacing a decision).
    def _affords_room(shape):
        tf = shape.text_frame
        def _m(v, d):
            return (v / IN) if v is not None else d
        ml = _m(tf.margin_left, 0.20); mr = _m(tf.margin_right, 0.20)
        mt = _m(tf.margin_top, 0.15);  mb = _m(tf.margin_bottom, 0.15)
        text_w = max(0.1, shape.width/IN - ml - mr)
        text_h = max(0.1, shape.height/IN - mt - mb)
        texts = [p.text for p in tf.paragraphs if p.text.strip()]
        if not texts:
            return 22.0
        def _est_h(t, w_in, pt):
            cpl = max(1, w_in * 72 / (pt * 0.50))
            return math.ceil(len(t) / cpl) * pt * 1.25 / 72
        size = 28
        while size > 22:
            if sum(_est_h(t, text_w, size) for t in texts) <= text_h * 0.96:
                return float(size)
            size -= 1
        return 22.0

    # 18. Uniform-at-floor signature — the floor written as a default. Fires when
    #     >50% of body-role runs sit within 1pt of the 22pt floor (22.0-22.9pt;
    #     >=8 body runs; "within 1pt" so nudging a few to 23pt cannot game it).
    #     Then measure room_count: at-floor body SHAPES whose text area affords a
    #     larger size (_affords_room >= floor+2 = 24pt). The conversion-branch
    #     message carries room_count; a calling workflow can key off it.
    #       - Generation (conversion_source=None): ERROR. Compute via fit_font_size()
    #         / _affords_room before saving, or reduce content. Never inflate fonts.
    #       - Conversion (conversion_source set): WARNING carrying room_count.
    #         room_count>=1 -> the conversion under-sized boxes with room; recompute
    #         per box IN the PPTX (fix in place). room_count==0 -> boxes genuinely
    #         full at the floor; reduce content (a user decision). Not upstream.
    body_run_sizes = []
    at_floor_shapes = 0
    room_count = 0
    for si11, slide11 in enumerate(prs.slides, start=1):
        if slide11._element.get('show') == '0':
            continue
        for s in slide11.shapes:
            if s.is_placeholder or s.has_chart or s.has_table:
                continue
            if s.shape_type == 13 or not s.has_text_frame or s.left is None:
                continue
            role, _fl = _role_floor(s.left/IN, s.top/IN, s.width/IN, s.height/IN, s.name)
            if role != 'body':
                continue
            shape_sizes = []
            for p in s.text_frame.paragraphs:
                for run in p.runs:
                    if run.font.size is not None and run.text.strip():
                        body_run_sizes.append(run.font.size.pt)
                        shape_sizes.append(run.font.size.pt)
            # At-floor body shape: largest body run within 1pt of the floor.
            if shape_sizes and 22.0 <= max(shape_sizes) < 23.0:
                at_floor_shapes += 1
                if _affords_room(s) >= 24:
                    room_count += 1
    if len(body_run_sizes) >= 8:
        at_floor = sum(1 for sz in body_run_sizes if 22.0 <= sz < 23.0)
        if at_floor / len(body_run_sizes) > 0.5:
            msg = (
                f"UNIFORM-AT-FLOOR: {at_floor} of {len(body_run_sizes)} body runs sit at "
                f"the 22pt floor — the floor was written as a default, not a clamp on a "
                f"computed size. "
            )
            if conversion_source:
                issues.append(
                    f"WARNING: {msg}room_count={room_count} of {at_floor_shapes} "
                    f"at-floor body shapes afford a larger size (>=24pt) against their "
                    f"text area. The calling workflow keys off room_count: "
                    f"room_count>=1 means the conversion under-sized boxes with room, so "
                    f"recompute each body box via fit_font_size() against its text area "
                    f"(fix in the PPTX); room_count==0 means boxes are genuinely full at "
                    f"the floor, so reduce content (a user decision). Never inflate fonts "
                    f"or hand-pick emphasis sizes to clear this."
                )
            else:
                issues.append(
                    f"{msg}Compute each box's size with fit_font_size() (start at the "
                    f"role ceiling, step down to fit, clamp at floor) or reduce content "
                    f"so a larger size fits. Do not inflate fonts without checking fit."
                )

    # 19. Box under-fill — the inverse of overflow check #14: text rattling
    #     around a much larger box at a size below the role ceiling means the
    #     size was never computed upward. WARNING (a deliberately airy stat
    #     callout can legitimately sit under 60%), surfaced for a decision.
    for si12, slide12 in enumerate(prs.slides, start=1):
        if slide12._element.get('show') == '0':
            continue
        lbl12 = f"Slide {si12}"
        for s in slide12.shapes:
            if s.is_placeholder or s.has_chart or s.has_table:
                continue
            if s.shape_type == 13 or not s.has_text_frame or s.left is None:
                continue
            shape_w, shape_h = s.width/IN, s.height/IN
            if shape_h < 0.6:
                continue   # labels/citations/slivers — not under-fill candidates
            role, _fl = _role_floor(s.left/IN, s.top/IN, shape_w, shape_h, s.name)
            if role != 'body':
                continue
            sizes = [r.font.size.pt for p in s.text_frame.paragraphs
                     for r in p.runs if r.font.size is not None and r.text.strip()]
            texts = [p.text for p in s.text_frame.paragraphs if p.text.strip()]
            if not sizes or not texts:
                continue
            cur = max(sizes)
            if cur >= 28:
                continue   # already at the body ceiling
            def _est_h(t, w_in, pt):   # self-contained, mirrors estimate_text_height
                cpl = max(1, w_in * 72 / (pt * 0.50))
                return math.ceil(len(t) / cpl) * pt * 1.25 / 72
            est = sum(_est_h(t, shape_w, cur) for t in texts)
            # 60%-emptiness gate on the RAW shape height (visible airiness).
            if est < shape_h * 0.6:
                # Room test via the shared helper (text-area basis, aligns with #18).
                if _affords_room(s) >= cur + 2:
                    issues.append(
                        f"WARNING: {lbl12} '{s.name}': box under-fill — ~{est:.1f}\" of text "
                        f"in a {shape_h:.1f}\" box at {cur:.0f}pt, and a larger in-role size "
                        f"fits its text area. Compute the size with fit_font_size() (largest "
                        f"in-role size that fits), or shrink the box to its content."
                    )

    # 20. Caption under-fill — a caption sized below what its own box affords.
    #     The caption analog of #19 (body under-fill), but ERROR not WARNING and with NO
    #     <0.6" height skip, because the caption tier is the regression this change hardens.
    #     Classify by name (primary) / geometry (fallback); recompute the largest caption-role
    #     size that fits the caption's actual box and flag a run more than 1pt below it.
    #     add_caption() sizes the box to the chosen font, so its own output recomputes to the
    #     same value (want == cur) and never trips this; it bites only a hand-built under-sized
    #     caption sitting in a box that affords larger. A long caption that legitimately floors
    #     at 18 recomputes to 18 and passes. The 1pt tolerance absorbs helper/audit rounding.
    CAP_CEIL, CAP_FLOOR = 22, 18
    def _est_cap_h(t, w_in, pt):       # self-contained, mirrors estimate_text_height
        cpl = max(1, w_in * 72 / (pt * 0.50))
        return math.ceil(len(t) / cpl) * pt * 1.25 / 72
    def _fit_caption(t, w_in, h_in):   # largest in [18,22] whose est height fits the box
        sz = CAP_CEIL
        while sz > CAP_FLOOR:
            if _est_cap_h(t, w_in, sz) <= h_in * 0.96:
                return sz
            sz -= 1
        return CAP_FLOOR
    for si13, slide13 in enumerate(prs.slides, start=1):
        if slide13._element.get('show') == '0':
            continue
        lbl13 = f"Slide {si13}"
        for s in slide13.shapes:
            if s.is_placeholder or s.has_chart or s.has_table:
                continue
            if s.shape_type == 13 or not s.has_text_frame or s.left is None:
                continue
            role, _fl = _role_floor(s.left/IN, s.top/IN, s.width/IN, s.height/IN, s.name)
            if role != 'caption':
                continue
            text = " ".join(p.text for p in s.text_frame.paragraphs if p.text.strip())
            sizes = [r.font.size.pt for p in s.text_frame.paragraphs
                     for r in p.runs if r.font.size is not None and r.text.strip()]
            if not text or not sizes:
                continue
            want = _fit_caption(text, s.width/IN, s.height/IN)
            cur = max(sizes)
            if cur < want - 1:
                issues.append(
                    f"{lbl13} '{s.name}': caption at {cur:.0f}pt where {want:.0f}pt fits its "
                    f"box — compute via add_caption() / fit_font_size(role='caption'); the "
                    f"caption must read one tier above the 11pt citation."
                )

    return issues


# --- Run before prs.save() (error/warning run-wrapper) ------------------------
def report_and_exit(prs, issues):
    """Print the check result.

    Errors raise SystemExit (nonzero exit); warnings and a clean pass return.
    The caller (a generator script) performs its own prs.save() afterward.
    """
    errors = [i for i in issues if not i.startswith("WARNING:")]
    warnings = [i for i in issues if i.startswith("WARNING:")]
    if errors:
        print(f"\nQUALITY CHECK FAILED — {len(errors)} error(s) found:")
        for e in errors:
            print(f"  • {e}")
        if warnings:
            print(f"\n  Plus {len(warnings)} warning(s):")
            for w in warnings:
                print(f"  • {w}")
        raise SystemExit("Fix the errors above before saving.")
    elif warnings:
        print(f"\nQuality check passed with {len(warnings)} warning(s) ({len(prs.slides)} slides):")
        for w in warnings:
            print(f"  • {w}")
        print("Warnings do not block save. Review and address if content can be reduced.")
    else:
        print(f"Quality check passed ({len(prs.slides)} slides).")


def main(argv=None):
    import argparse
    from pptx import Presentation

    parser = argparse.ArgumentParser(
        description="Run the style guide's pre-save structural quality check "
                    "on a saved .pptx deck."
    )
    parser.add_argument("deck", help="Path to the .pptx file to check")
    parser.add_argument(
        "--conversion-source", default=None, metavar="SLIDES_TEX",
        help="Path to the Beamer slides.tex when the deck is a conversion; "
             "omit for direct generation. Controls check #18's severity "
             "(ERROR at generation, WARNING carrying room_count at conversion).",
    )
    args = parser.parse_args(argv)
    prs = Presentation(args.deck)
    issues = run_quality_check(prs, conversion_source=args.conversion_source)
    report_and_exit(prs, issues)


if __name__ == "__main__":
    main()
