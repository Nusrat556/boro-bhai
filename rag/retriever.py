"""Document ingestion and retrieval for BORO BHAI."""

from __future__ import annotations

import csv
from pathlib import Path

from pypdf import PdfReader

from rag.vector_store import DEFAULT_STORE_PATH, VectorStore

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"


def _resolve_document_path(file_path: str) -> Path:
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
        raise ValueError("Access denied: documents must be inside the approved data directory.") from exc
    return resolved


def read_document_text(file_path: str) -> str:
    """Read text from a supported document format."""
    resolved = _resolve_document_path(file_path)
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"Document not found: {resolved}")

    suffix = resolved.suffix.lower()
    if suffix == ".txt":
        return resolved.read_text(encoding="utf-8")
    if suffix == ".csv":
        with resolved.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        if not rows:
            return ""
        return "\n".join(", ".join(row) for row in rows)
    if suffix == ".pdf":
        reader = PdfReader(str(resolved))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)
        return "\n".join(pages)

    raise ValueError("Unsupported document type. Use .txt, .csv, or .pdf.")


def ingest_document(file_path: str, store: VectorStore | None = None) -> list[dict[str, object]]:
    """Ingest a single document into a vector store and return inserted chunks."""
    resolved = _resolve_document_path(file_path)
    text = read_document_text(str(resolved))
    vector_store = store or VectorStore(DEFAULT_STORE_PATH)
    chunks = vector_store.add_document(text, source=str(resolved), metadata={"document_name": resolved.name, "file_type": resolved.suffix.lower()})
    return [
        {
            "text": chunk.text,
            "source": chunk.source,
            "metadata": chunk.metadata,
            "score": 1.0,
        }
        for chunk in chunks
    ]


def retrieve_context(query: str, top_k: int = 3, store: VectorStore | None = None) -> list[dict[str, object]]:
    """Retrieve the most relevant chunks for a query."""
    if not query or not query.strip():
        return []
    vector_store = store or VectorStore(DEFAULT_STORE_PATH)
    return vector_store.search(query, top_k=top_k)


def build_rag_context(query: str, top_k: int = 3, store: VectorStore | None = None) -> str:
    """Convert retrieved chunks into a context string for the LLM."""
    matches = retrieve_context(query, top_k=top_k, store=store)
    if not matches:
        return ""
    lines = []
    for match in matches:
        lines.append(f"Source: {match['source']}\n{match['text']}")
    return "\n\n---\n\n".join(lines)
