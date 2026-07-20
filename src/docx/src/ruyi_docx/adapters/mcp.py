from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ruyi_docx.errors import OptionalDependencyError, UnsafePathError
from ruyi_docx.models import DocumentMetadata, DocumentSpec, Heading, Paragraph
from ruyi_docx.service import WordDocumentService


@dataclass(frozen=True, slots=True)
class PathPolicy:
    """Resolve adapter paths while enforcing a fixed filesystem boundary."""

    allowed_root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_root", self.allowed_root.resolve())

    def resolve(self, relative_path: str, *, must_exist: bool = False) -> Path:
        candidate = (self.allowed_root / relative_path).resolve()
        if not candidate.is_relative_to(self.allowed_root):
            raise UnsafePathError(f"path is outside the allowed root: {relative_path}")
        if must_exist and not candidate.is_file():
            raise FileNotFoundError(f"document does not exist: {relative_path}")
        return candidate


def build_mcp_server(allowed_root: Path):
    """Build a FastMCP server with path-restricted DOCX tools."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise OptionalDependencyError("MCP support requires the 'mcp' extra") from exc

    policy = PathPolicy(allowed_root)
    service = WordDocumentService()
    server = FastMCP("ruyi-docx")

    @server.tool()
    def create_document(output_path: str, title: str, paragraphs: list[str]) -> dict[str, object]:
        """Create a professionally styled DOCX below the allowed root."""
        output = policy.resolve(output_path)
        blocks = (Heading(title, level=1), *(Paragraph(text) for text in paragraphs))
        result = service.create(
            DocumentSpec(blocks=blocks, metadata=DocumentMetadata(title=title), footer_text=title),
            output,
        )
        report = service.validate(result)
        return {"path": str(result), "validation": asdict(report)}

    @server.tool()
    def read_document(path: str) -> dict[str, object]:
        """Read paragraphs, tables, metadata, and section count from a DOCX."""
        snapshot = service.read(policy.resolve(path, must_exist=True))
        return asdict(snapshot)

    @server.tool()
    def replace_text(source_path: str, output_path: str, replacements: dict[str, str]) -> dict[str, object]:
        """Replace text across body, tables, headers, and footers and save a new DOCX."""
        result = service.replace(
            policy.resolve(source_path, must_exist=True),
            policy.resolve(output_path),
            replacements,
        )
        return {"path": str(result.output), "changed_items": result.changed_items}

    @server.tool()
    def append_paragraphs(source_path: str, output_path: str, paragraphs: list[str]) -> dict[str, object]:
        """Append paragraphs to an existing DOCX and save a new file."""
        result = service.append(
            policy.resolve(source_path, must_exist=True),
            policy.resolve(output_path),
            (Paragraph(text) for text in paragraphs),
        )
        return {"path": str(result.output), "changed_items": result.changed_items}

    @server.tool()
    def validate_document(path: str) -> dict[str, object]:
        """Validate ZIP integrity, required OOXML parts, and python-docx readability."""
        return asdict(service.validate(policy.resolve(path, must_exist=True)))

    @server.tool()
    def render_pdf(source_path: str, output_directory: str) -> dict[str, str]:
        """Render a DOCX to PDF with LibreOffice when available."""
        result = service.render_pdf(
            policy.resolve(source_path, must_exist=True),
            policy.resolve(output_directory),
        )
        return {"path": str(result)}

    return server
