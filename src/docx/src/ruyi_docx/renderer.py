from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ruyi_docx.errors import RenderError


WINDOWS_CANDIDATES = (
    Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
    Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
)


def find_soffice() -> Path | None:
    """Locate a LibreOffice executable without mutating the host environment."""
    command = shutil.which("soffice") or shutil.which("libreoffice")
    if command:
        return Path(command)
    return next((candidate for candidate in WINDOWS_CANDIDATES if candidate.is_file()), None)


def render_pdf(source: Path, output_dir: Path, *, executable: Path | None = None, timeout: int = 120) -> Path:
    """Render a DOCX to PDF using LibreOffice headless mode."""
    if not source.is_file():
        raise FileNotFoundError(f"document does not exist: {source}")
    soffice = executable or find_soffice()
    if soffice is None or not soffice.is_file():
        raise RenderError("LibreOffice was not found; install it or pass an explicit soffice executable")
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        str(soffice),
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir.resolve()),
        str(source.resolve()),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    output = output_dir / f"{source.stem}.pdf"
    if result.returncode != 0 or not output.is_file():
        detail = (result.stderr or result.stdout or "renderer did not create a PDF").strip()
        raise RenderError(f"LibreOffice rendering failed: {detail}")
    return output.resolve()
