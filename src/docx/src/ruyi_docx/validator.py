from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile, ZipFile

from docx import Document

from ruyi_docx.models import ValidationReport


REQUIRED_PARTS = frozenset(
    {
        "[Content_Types].xml",
        "_rels/.rels",
        "word/document.xml",
        "word/_rels/document.xml.rels",
    }
)


def validate_document(path: Path) -> ValidationReport:
    """Validate DOCX package integrity and python-docx readability."""
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return ValidationReport(valid=False, errors=(f"document does not exist: {path}",), warnings=())
    try:
        with ZipFile(path) as archive:
            names = frozenset(archive.namelist())
            missing = sorted(REQUIRED_PARTS - names)
            if missing:
                errors.append(f"missing required DOCX parts: {', '.join(missing)}")
            corrupt_member = archive.testzip()
            if corrupt_member:
                errors.append(f"corrupt ZIP member: {corrupt_member}")
    except BadZipFile:
        return ValidationReport(valid=False, errors=("file is not a valid ZIP-based DOCX package",), warnings=())

    paragraph_count = 0
    table_count = 0
    try:
        document = Document(path)
        paragraph_count = len(document.paragraphs)
        table_count = len(document.tables)
        if paragraph_count == 0 and table_count == 0:
            warnings.append("document contains no top-level paragraphs or tables")
    except Exception as exc:
        errors.append(f"python-docx cannot open the package: {exc}")
    return ValidationReport(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        paragraph_count=paragraph_count,
        table_count=table_count,
    )


def require_valid_document(path: Path) -> ValidationReport:
    """Validate a document and raise a descriptive ValueError on failure."""
    report = validate_document(path)
    if not report.valid:
        raise ValueError("; ".join(report.errors))
    return report
