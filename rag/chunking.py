"""Chunking utilities for local RAG."""

from __future__ import annotations

import re


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    """Split text into overlapping chunks. Returns an empty list for blank input."""
    if not text or not text.strip():
        return []

    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= chunk_size:
        return [normalized]

    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 2)

    step = chunk_size - overlap
    chunks = []
    for start in range(0, len(normalized), step):
        chunk = normalized[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(normalized):
            break
    return chunks
