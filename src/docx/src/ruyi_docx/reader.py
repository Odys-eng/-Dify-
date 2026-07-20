from __future__ import annotations

from pathlib import Path

from docx import Document

from ruyi_docx.models import DocumentMetadata, DocumentSnapshot, TableSnapshot


def read_document(path: Path) -> DocumentSnapshot:
    """Read top-level paragraphs, tables, metadata, and section count from a DOCX."""
    if not path.is_file():
        raise FileNotFoundError(f"document does not exist: {path}")
    document = Document(path)
    properties = document.core_properties
    metadata = DocumentMetadata(
        title=properties.title or "",
        subject=properties.subject or "",
        author=properties.author or "",
        keywords=tuple(item.strip() for item in (properties.keywords or "").split(",") if item.strip()),
        comments=properties.comments or "",
    )
    tables = tuple(
        TableSnapshot(rows=tuple(tuple(cell.text for cell in row.cells) for row in table.rows))
        for table in document.tables
    )
    return DocumentSnapshot(
        paragraphs=tuple(paragraph.text for paragraph in document.paragraphs),
        tables=tables,
        metadata=metadata,
        section_count=len(document.sections),
    )


def extract_text(path: Path, *, include_tables: bool = True) -> str:
    """Extract top-level readable text for simple indexing and inspection."""
    snapshot = read_document(path)
    parts = [text for text in snapshot.paragraphs if text]
    if include_tables:
        for table in snapshot.tables:
            parts.extend("\t".join(row) for row in table.rows)
    return "\n".join(parts)
