from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from ruyi_docx.editor import (
    append_blocks,
    apply_paragraph_style,
    delete_paragraphs_containing,
    replace_text,
)
from ruyi_docx.models import Block, DocumentSnapshot, DocumentSpec, EditResult, ValidationReport
from ruyi_docx.reader import extract_text, read_document
from ruyi_docx.renderer import render_pdf
from ruyi_docx.templates import merge_documents, render_template
from ruyi_docx.validator import validate_document
from ruyi_docx.writer import create_document


class WordDocumentService:
    """Stable facade for DOCX creation, inspection, modification, rendering, and validation."""

    def create(self, spec: DocumentSpec, output: Path) -> Path:
        return create_document(spec, output)

    def read(self, path: Path) -> DocumentSnapshot:
        return read_document(path)

    def extract_text(self, path: Path, *, include_tables: bool = True) -> str:
        return extract_text(path, include_tables=include_tables)

    def replace(
        self,
        source: Path,
        output: Path,
        replacements: Mapping[str, str],
        *,
        include_headers_footers: bool = True,
    ) -> EditResult:
        return replace_text(
            source,
            output,
            replacements,
            include_headers_footers=include_headers_footers,
        )

    def append(self, source: Path, output: Path, blocks: Iterable[Block]) -> EditResult:
        return append_blocks(source, output, blocks)

    def delete_paragraphs(self, source: Path, output: Path, marker: str) -> EditResult:
        return delete_paragraphs_containing(source, output, marker)

    def apply_style(self, source: Path, output: Path, marker: str, style_name: str) -> EditResult:
        return apply_paragraph_style(source, output, marker, style_name)

    def render_template(self, template: Path, output: Path, context: Mapping[str, object]) -> Path:
        return render_template(template, output, context)

    def merge(self, sources: Sequence[Path], output: Path) -> Path:
        return merge_documents(sources, output)

    def render_pdf(self, source: Path, output_dir: Path, *, executable: Path | None = None) -> Path:
        return render_pdf(source, output_dir, executable=executable)

    def validate(self, path: Path) -> ValidationReport:
        return validate_document(path)
