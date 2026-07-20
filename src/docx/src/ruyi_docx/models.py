from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TypeAlias


class Alignment(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class Orientation(StrEnum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class CalloutKind(StrEnum):
    NOTE = "note"
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"


@dataclass(frozen=True, slots=True)
class PageSpec:
    orientation: Orientation = Orientation.PORTRAIT
    width_cm: float = 21.0
    height_cm: float = 29.7
    margin_top_cm: float = 2.2
    margin_bottom_cm: float = 2.0
    margin_left_cm: float = 2.4
    margin_right_cm: float = 2.2

    def __post_init__(self) -> None:
        dimensions = (
            self.width_cm,
            self.height_cm,
            self.margin_top_cm,
            self.margin_bottom_cm,
            self.margin_left_cm,
            self.margin_right_cm,
        )
        if any(value <= 0 for value in dimensions):
            raise ValueError("page dimensions and margins must be positive")


@dataclass(frozen=True, slots=True)
class FontSpec:
    latin_name: str = "Aptos"
    east_asia_name: str = "Microsoft YaHei"
    size_pt: float = 10.5
    color: str = "263238"

    def __post_init__(self) -> None:
        if self.size_pt <= 0:
            raise ValueError("font size must be positive")
        if len(self.color) != 6:
            raise ValueError("font color must be a six-character RGB value")


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    title: str = ""
    subject: str = ""
    author: str = "RuyiDify"
    keywords: tuple[str, ...] = ()
    comments: str = ""


@dataclass(frozen=True, slots=True)
class Heading:
    text: str
    level: int = 1

    def __post_init__(self) -> None:
        if not 1 <= self.level <= 9:
            raise ValueError("heading level must be between 1 and 9")


@dataclass(frozen=True, slots=True)
class Paragraph:
    text: str
    style_name: str | None = None
    alignment: Alignment = Alignment.LEFT
    bold: bool = False
    italic: bool = False
    keep_with_next: bool = False


@dataclass(frozen=True, slots=True)
class ListBlock:
    items: tuple[str, ...]
    ordered: bool = False
    level: int = 0

    def __post_init__(self) -> None:
        if not self.items:
            raise ValueError("list items cannot be empty")
        if self.level < 0:
            raise ValueError("list level cannot be negative")


@dataclass(frozen=True, slots=True)
class TableBlock:
    rows: tuple[tuple[str, ...], ...]
    has_header: bool = True
    column_widths_cm: tuple[float, ...] | None = None
    style_name: str = "Table Grid"

    def __post_init__(self) -> None:
        if not self.rows or not self.rows[0]:
            raise ValueError("table rows cannot be empty")
        column_count = len(self.rows[0])
        if any(len(row) != column_count for row in self.rows):
            raise ValueError("all table rows must have the same number of columns")
        if self.column_widths_cm is not None:
            if len(self.column_widths_cm) != column_count:
                raise ValueError("column widths must match table column count")
            if any(width <= 0 for width in self.column_widths_cm):
                raise ValueError("column widths must be positive")


@dataclass(frozen=True, slots=True)
class ImageBlock:
    path: Path
    width_cm: float | None = None
    caption: str | None = None

    def __post_init__(self) -> None:
        if self.width_cm is not None and self.width_cm <= 0:
            raise ValueError("image width must be positive")


@dataclass(frozen=True, slots=True)
class PageBreak:
    pass


@dataclass(frozen=True, slots=True)
class CodeBlock:
    code: str
    language: str = "text"


@dataclass(frozen=True, slots=True)
class Callout:
    title: str
    text: str
    kind: CalloutKind = CalloutKind.NOTE


@dataclass(frozen=True, slots=True)
class Hyperlink:
    text: str
    url: str

    def __post_init__(self) -> None:
        if not self.text or not self.url:
            raise ValueError("hyperlink text and url cannot be empty")


@dataclass(frozen=True, slots=True)
class TableOfContents:
    title: str = "目录"
    max_level: int = 3

    def __post_init__(self) -> None:
        if not 1 <= self.max_level <= 9:
            raise ValueError("table of contents max_level must be between 1 and 9")


Block: TypeAlias = (
    Heading
    | Paragraph
    | ListBlock
    | TableBlock
    | ImageBlock
    | PageBreak
    | CodeBlock
    | Callout
    | Hyperlink
    | TableOfContents
)


@dataclass(frozen=True, slots=True)
class DocumentSpec:
    blocks: tuple[Block, ...]
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    page: PageSpec = field(default_factory=PageSpec)
    body_font: FontSpec = field(default_factory=FontSpec)
    header_text: str = ""
    footer_text: str = ""


@dataclass(frozen=True, slots=True)
class TableSnapshot:
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, slots=True)
class DocumentSnapshot:
    paragraphs: tuple[str, ...]
    tables: tuple[TableSnapshot, ...]
    metadata: DocumentMetadata
    section_count: int


@dataclass(frozen=True, slots=True)
class ValidationReport:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    paragraph_count: int = 0
    table_count: int = 0


@dataclass(frozen=True, slots=True)
class EditResult:
    output: Path
    changed_items: int
