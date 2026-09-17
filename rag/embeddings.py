"""Simple local embedding utilities for BORO BHAI."""

from __future__ import annotations

import hashlib
import math
import re

EMBEDDING_DIM = 128


def embed_text(text: str, dimension: int = EMBEDDING_DIM) -> list[float]:
    """Return a deterministic local embedding vector for text."""
    if not text or not text.strip():
        return [0.0 for _ in range(dimension)]

    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    if not tokens:
        return [0.0 for _ in range(dimension)]

    vector = [0.0 for _ in range(dimension)]
    for index, token in enumerate(tokens):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        position = int.from_bytes(digest[:4], byteorder="big") % dimension
        vector[position] += 1.0 + (index / max(1, len(tokens)))

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return [0.0 for _ in range(dimension)]
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    if len(left) != len(right):
        raise ValueError("Embedding vectors must be the same length.")

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
