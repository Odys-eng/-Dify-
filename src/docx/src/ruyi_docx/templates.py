from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from docx import Document

from ruyi_docx.errors import OptionalDependencyError


def render_template(template: Path, output: Path, context: Mapping[str, object]) -> Path:
    """Render a DOCX Jinja template with docxtpl."""
    try:
        from docxtpl import DocxTemplate
    except ImportError as exc:
        raise OptionalDependencyError("template rendering requires the 'templates' extra with docxtpl") from exc
    if not template.is_file():
        raise FileNotFoundError(f"template does not exist: {template}")
    document = DocxTemplate(template)
    document.render(dict(context))
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    return output.resolve()


def merge_documents(sources: Sequence[Path], output: Path) -> Path:
    """Merge complete DOCX files while preserving their styles and sections."""
    if not sources:
        raise ValueError("at least one source document is required")
    missing = [path for path in sources if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"source document does not exist: {missing[0]}")
    try:
        from docxcompose.composer import Composer
    except ImportError as exc:
        raise OptionalDependencyError("document merging requires the 'templates' extra with docxcompose") from exc
    master = Document(sources[0])
    composer = Composer(master)
    for source in sources[1:]:
        composer.append(Document(source))
    output.parent.mkdir(parents=True, exist_ok=True)
    composer.save(output)
    return output.resolve()
