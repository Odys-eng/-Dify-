class DocumentError(Exception):
    """Base error for deterministic document operations."""


class DocumentValidationError(DocumentError):
    """Raised when a DOCX package is malformed or cannot be opened."""


class OptionalDependencyError(DocumentError):
    """Raised when an optional document capability is not installed."""


class RenderError(DocumentError):
    """Raised when an office renderer cannot produce the requested output."""


class UnsafePathError(DocumentError):
    """Raised when an adapter attempts to access a path outside its allowed root."""
