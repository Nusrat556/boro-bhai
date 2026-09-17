"""Persistent local vector store for BORO BHAI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from rag.chunking import chunk_text
from rag.embeddings import cosine_similarity, embed_text

DEFAULT_STORE_PATH = os.getenv("BORO_BHAI_RAG_STORE", os.path.join("data", "rag_store.json"))


@dataclass
class IndexedChunk:
    """A chunk plus its metadata and embedding."""
    text: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)


class VectorStore:
    """Simple JSON-backed vector store."""

    def __init__(self, store_path: str = DEFAULT_STORE_PATH):
        self.store_path = store_path
        self.documents: list[IndexedChunk] = []
        self._ensure_parent_dir()
        self._load()

    def _ensure_parent_dir(self) -> None:
        directory = os.path.dirname(self.store_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _load(self) -> None:
        if not os.path.exists(self.store_path):
            self.documents = []
            return

        try:
            with open(self.store_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (json.JSONDecodeError, OSError):
            self.documents = []
            return

        self.documents = [
            IndexedChunk(
                text=item.get("text", ""),
                source=item.get("source", "unknown"),
                metadata=item.get("metadata", {}),
                embedding=item.get("embedding", []),
            )
            for item in raw.get("documents", [])
        ]

    def _save(self) -> None:
        payload = {
            "documents": [
                {
                    "text": document.text,
                    "source": document.source,
                    "metadata": document.metadata,
                    "embedding": document.embedding,
                }
                for document in self.documents
            ]
        }
        with open(self.store_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def add_document(self, text: str, source: str, metadata: dict[str, Any] | None = None) -> list[IndexedChunk]:
        """Chunk and index a document. Returns the created chunk entries."""
        if not text or not text.strip():
            return []

        created: list[IndexedChunk] = []
        chunks = chunk_text(text)
        for index, chunk in enumerate(chunks):
            chunk_metadata = {
                "source": source,
                "chunk_index": index,
                "chunk_count": len(chunks),
            }
            if metadata:
                chunk_metadata.update(metadata)
            embedded = IndexedChunk(
                text=chunk,
                source=source,
                metadata=chunk_metadata,
                embedding=embed_text(chunk),
            )
            self.documents.append(embedded)
            created.append(embedded)

        self._save()
        return created

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Return matching chunks with similarity scores."""
        if not query or not query.strip() or not self.documents:
            return []

        query_embedding = embed_text(query)
        scored = []
        for document in self.documents:
            if not document.embedding:
                continue
            score = cosine_similarity(query_embedding, document.embedding)
            scored.append({
                "text": document.text,
                "source": document.source,
                "metadata": document.metadata,
                "score": round(float(score), 4),
            })

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[: max(1, top_k)]

    def clear(self) -> None:
        self.documents = []
        if os.path.exists(self.store_path):
            os.remove(self.store_path)
