"""PDF text reader for BORO BHAI."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"
MAX_FILE_SIZE_BYTES = 5_000_000


def _resolve_pdf_path(file_path: str) -> Path:
    requested = str(file_path).replace("\\", "/")
    if requested.startswith("./"):
        requested = requested[2:]
    if requested.startswith("data/"):
        requested = requested[len("data/") :]
    elif requested.startswith("data\\"):
        requested = requested[len("data\\") :]

    target = Path(requested)
    resolved = target if target.is_absolute() else (DATA_DIR / target).resolve(strict=False)
    try:
        resolved.relative_to(DATA_DIR.resolve())
    except ValueError as exc:
        raise ValueError("Access denied: PDF must be inside the approved data directory.") from exc
    return resolved


def read_pdf_text(file_path: str) -> str:
    """Read and extract text from a PDF inside the allowed data directory."""
    resolved = _resolve_pdf_path(file_path)

    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"PDF file not found: {resolved}")
    if resolved.suffix.lower() != ".pdf":
        raise ValueError("Only .pdf files are allowed.")
    if resolved.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise ValueError("PDF is too large to read safely.")

    reader = PdfReader(str(resolved))
    text_blocks = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text_blocks.append(text)
    return "\n".join(block.strip() for block in text_blocks if block.strip())
