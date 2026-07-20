from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from ruyi_docx.models import (
    Alignment,
    Block,
    Callout,
    CalloutKind,
    CodeBlock,
    DocumentSpec,
    Heading,
    Hyperlink,
    ImageBlock,
    ListBlock,
    PageBreak,
    Paragraph,
    TableBlock,
    TableOfContents,
)
from ruyi_docx.ooxml import (
    add_hyperlink,
    add_table_of_contents,
    repeat_table_header,
    set_cell_margins,
    set_cell_shading,
    set_paragraph_shading,
)
from ruyi_docx.styles import apply_document_styles


ALIGNMENTS = {
    Alignment.LEFT: WD_ALIGN_PARAGRAPH.LEFT,
    Alignment.CENTER: WD_ALIGN_PARAGRAPH.CENTER,
    Alignment.RIGHT: WD_ALIGN_PARAGRAPH.RIGHT,
    Alignment.JUSTIFY: WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _write_metadata(document: DocxDocument, spec: DocumentSpec) -> None:
    properties = document.core_properties
    properties.title = spec.metadata.title
    properties.subject = spec.metadata.subject
    properties.author = spec.metadata.author
    properties.keywords = ", ".join(spec.metadata.keywords)
    properties.comments = spec.metadata.comments


def add_block(document: DocxDocument, block: Block) -> None:
    """Append one typed content block to a document."""
    if isinstance(block, Heading):
        document.add_heading(block.text, level=block.level)
        return
    if isinstance(block, Paragraph):
        paragraph = document.add_paragraph(style=block.style_name)
        paragraph.alignment = ALIGNMENTS[block.alignment]
        paragraph.paragraph_format.keep_with_next = block.keep_with_next
        run = paragraph.add_run(block.text)
        run.bold = block.bold
        run.italic = block.italic
        return
    if isinstance(block, ListBlock):
        style = "List Number" if block.ordered else "List Bullet"
        for item in block.items:
            paragraph = document.add_paragraph(item, style=style)
            if block.level:
                paragraph.paragraph_format.left_indent = Cm(0.63 * block.level)
        return
    if isinstance(block, TableBlock):
        table = document.add_table(rows=len(block.rows), cols=len(block.rows[0]))
        table.style = block.style_name
        for row_index, source_row in enumerate(block.rows):
            for column_index, value in enumerate(source_row):
                cell = table.cell(row_index, column_index)
                cell.text = value
                set_cell_margins(cell)
                if block.column_widths_cm is not None:
                    cell.width = Cm(block.column_widths_cm[column_index])
                if block.has_header and row_index == 0:
                    set_cell_shading(cell, "D9EAF0")
                    for run in cell.paragraphs[0].runs:
                        run.bold = True
        if block.has_header:
            repeat_table_header(table.rows[0])
        return
    if isinstance(block, ImageBlock):
        if not block.path.is_file():
            raise FileNotFoundError(f"image does not exist: {block.path}")
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        kwargs = {"width": Cm(block.width_cm)} if block.width_cm is not None else {}
        run.add_picture(str(block.path), **kwargs)
        if block.caption:
            caption = document.add_paragraph(block.caption)
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            caption.style = "Caption"
        return
    if isinstance(block, PageBreak):
        document.add_page_break()
        return
    if isinstance(block, CodeBlock):
        paragraph = document.add_paragraph(style="Code")
        set_paragraph_shading(paragraph, "F1F5F9")
        lines = block.code.splitlines() or [""]
        for index, line in enumerate(lines):
            if index:
                paragraph.runs[-1].add_break()
            paragraph.add_run(line)
        return
    if isinstance(block, Callout):
        fills = {
            CalloutKind.NOTE: "E8F1F5",
            CalloutKind.INFO: "E0F2FE",
            CalloutKind.WARNING: "FEF3C7",
            CalloutKind.SUCCESS: "DCFCE7",
        }
        table = document.add_table(rows=1, cols=1)
        table.style = "Table Grid"
        cell = table.cell(0, 0)
        set_cell_shading(cell, fills[block.kind])
        set_cell_margins(cell, top=120, start=160, bottom=120, end=160)
        title = cell.paragraphs[0]
        title.add_run(block.title).bold = True
        cell.add_paragraph(block.text)
        return
    if isinstance(block, Hyperlink):
        paragraph = document.add_paragraph()
        add_hyperlink(paragraph, block.text, block.url)
        return
    if isinstance(block, TableOfContents):
        document.add_heading(block.title, level=1)
        paragraph = document.add_paragraph()
        add_table_of_contents(paragraph, block.max_level)
        return
    raise TypeError(f"unsupported block type: {type(block).__name__}")


def create_document(spec: DocumentSpec, output: Path) -> Path:
    """Create a DOCX from a typed specification and return its resolved path."""
    document = Document()
    apply_document_styles(document, spec)
    _write_metadata(document, spec)
    for block in spec.blocks:
        add_block(document, block)
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    return output.resolve()
