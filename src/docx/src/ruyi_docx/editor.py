from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph as DocxParagraph

from ruyi_docx.models import Block, EditResult
from ruyi_docx.writer import add_block


def _iter_table_paragraphs(table: Table) -> Iterator[DocxParagraph]:
    for row in table.rows:
        for cell in row.cells:
            yield from cell.paragraphs
            for nested_table in cell.tables:
                yield from _iter_table_paragraphs(nested_table)


def _iter_paragraphs(document: DocxDocument, *, include_headers_footers: bool) -> Iterator[DocxParagraph]:
    yield from document.paragraphs
    for table in document.tables:
        yield from _iter_table_paragraphs(table)
    if include_headers_footers:
        for section in document.sections:
            for container in (section.header, section.footer):
                yield from container.paragraphs
                for table in container.tables:
                    yield from _iter_table_paragraphs(table)


def _replace_once(paragraph: DocxParagraph, old: str, new: str) -> int:
    if not old or old not in paragraph.text:
        return 0
    full_text = "".join(run.text for run in paragraph.runs)
    positions: list[int] = []
    search_from = 0
    while (position := full_text.find(old, search_from)) != -1:
        positions.append(position)
        search_from = position + len(old)

    for start in reversed(positions):
        full_text = "".join(run.text for run in paragraph.runs)
        end = start + len(old)
        spans: list[tuple[int, int]] = []
        cursor = 0
        for run in paragraph.runs:
            spans.append((cursor, cursor + len(run.text)))
            cursor += len(run.text)
        start_index = next(index for index, (_, span_end) in enumerate(spans) if start < span_end)
        end_index = next(index for index, (span_start, span_end) in enumerate(spans) if span_start < end <= span_end)
        start_offset = start - spans[start_index][0]
        end_offset = end - spans[end_index][0]
        if start_index == end_index:
            run = paragraph.runs[start_index]
            run.text = run.text[:start_offset] + new + run.text[end_offset:]
        else:
            start_run = paragraph.runs[start_index]
            end_run = paragraph.runs[end_index]
            start_run.text = start_run.text[:start_offset] + new
            end_run.text = end_run.text[end_offset:]
            for index in range(start_index + 1, end_index):
                paragraph.runs[index].text = ""
    return len(positions)


def replace_text(
    source: Path,
    output: Path,
    replacements: Mapping[str, str],
    *,
    include_headers_footers: bool = True,
) -> EditResult:
    """Replace text across runs while preserving unaffected run formatting."""
    document = Document(source)
    changed = 0
    for paragraph in _iter_paragraphs(document, include_headers_footers=include_headers_footers):
        for old, new in replacements.items():
            changed += _replace_once(paragraph, old, new)
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    return EditResult(output=output.resolve(), changed_items=changed)


def append_blocks(source: Path, output: Path, blocks: Iterable[Block]) -> EditResult:
    """Append typed blocks to an existing document."""
    document = Document(source)
    changed = 0
    for block in blocks:
        add_block(document, block)
        changed += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    return EditResult(output=output.resolve(), changed_items=changed)


def delete_paragraphs_containing(source: Path, output: Path, marker: str) -> EditResult:
    """Delete body or table paragraphs containing a marker string."""
    if not marker:
        raise ValueError("marker cannot be empty")
    document = Document(source)
    matches = [
        paragraph for paragraph in _iter_paragraphs(document, include_headers_footers=False) if marker in paragraph.text
    ]
    for paragraph in matches:
        element = paragraph._element
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    return EditResult(output=output.resolve(), changed_items=len(matches))


def apply_paragraph_style(source: Path, output: Path, marker: str, style_name: str) -> EditResult:
    """Apply a named Word style to body and table paragraphs matching text."""
    document = Document(source)
    changed = 0
    for paragraph in _iter_paragraphs(document, include_headers_footers=False):
        if marker in paragraph.text:
            paragraph.style = style_name
            changed += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    return EditResult(output=output.resolve(), changed_items=changed)
