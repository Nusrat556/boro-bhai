"""Safe text file reader for BORO BHAI."""

from __future__ import annotations

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"
MAX_FILE_SIZE_BYTES = 1_000_000


def _resolve_allowed_path(file_path: str) -> Path:
    """Resolve a requested file path and ensure it stays inside the approved data directory."""
    requested = str(file_path).replace("\\", "/")
    if requested.startswith("./"):
        requested = requested[2:]
    if requested.startswith("data/"):
        requested = requested[len("data/") :]
    elif requested.startswith("data\\"):
        requested = requested[len("data\\") :]

    target = Path(requested)
    if target.is_absolute():
        resolved = target
    else:
        resolved = (DATA_DIR / target).resolve(strict=False)

    try:
        resolved.relative_to(DATA_DIR.resolve())
    except ValueError as exc:
        raise ValueError("Access denied: file must be inside the approved data directory.") from exc

    return resolved


def read_text_file(file_path: str) -> str:
    """Read a text file from the approved data directory."""
    resolved = _resolve_allowed_path(file_path)

    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"File not found: {resolved}")

    if resolved.suffix.lower() != ".txt":
        raise ValueError("Only .txt files are allowed.")

    if resolved.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise ValueError("File is too large to read safely.")

    return resolved.read_text(encoding="utf-8")
