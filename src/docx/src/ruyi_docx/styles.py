from __future__ import annotations

from docx.document import Document as DocxDocument
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from ruyi_docx.models import DocumentSpec, Orientation
from ruyi_docx.ooxml import add_page_number


def apply_document_styles(document: DocxDocument, spec: DocumentSpec) -> None:
    """Apply stable page, body, heading, header, and footer styles."""
    section = document.sections[0]
    width_cm = spec.page.width_cm
    height_cm = spec.page.height_cm
    if spec.page.orientation == Orientation.LANDSCAPE:
        section.orientation = WD_ORIENT.LANDSCAPE
        width_cm, height_cm = max(width_cm, height_cm), min(width_cm, height_cm)
    section.page_width = Cm(width_cm)
    section.page_height = Cm(height_cm)
    section.top_margin = Cm(spec.page.margin_top_cm)
    section.bottom_margin = Cm(spec.page.margin_bottom_cm)
    section.left_margin = Cm(spec.page.margin_left_cm)
    section.right_margin = Cm(spec.page.margin_right_cm)

    body = document.styles["Normal"]
    body.font.name = spec.body_font.latin_name
    body._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), spec.body_font.east_asia_name)
    body.font.size = Pt(spec.body_font.size_pt)
    body.font.color.rgb = RGBColor.from_string(spec.body_font.color)
    body.paragraph_format.space_after = Pt(6)
    body.paragraph_format.line_spacing = 1.35

    heading_sizes = {1: 17, 2: 14, 3: 12}
    for level in range(1, 4):
        style = document.styles[f"Heading {level}"]
        style.font.name = spec.body_font.latin_name
        style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), spec.body_font.east_asia_name)
        style.font.size = Pt(heading_sizes[level])
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string("1F5C78")
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(12 if level == 1 else 8)
        style.paragraph_format.space_after = Pt(6)

    code = document.styles["Code"] if "Code" in document.styles else document.styles.add_style("Code", 1)
    code.font.name = "Cascadia Mono"
    code._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    code.font.size = Pt(9)
    code.paragraph_format.left_indent = Cm(0.4)
    code.paragraph_format.right_indent = Cm(0.4)
    code.paragraph_format.space_before = Pt(3)
    code.paragraph_format.space_after = Pt(3)

    if spec.header_text:
        header = section.header.paragraphs[0]
        header.text = spec.header_text
        header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for run in header.runs:
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor.from_string("64748B")

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if spec.footer_text:
        run = footer.add_run(f"{spec.footer_text} | ")
        run.font.size = Pt(8)
    add_page_number(footer)
