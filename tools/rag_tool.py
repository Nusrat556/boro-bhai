"""RAG access tool for BORO BHAI."""

from __future__ import annotations

import os

from rag.retriever import build_rag_context, retrieve_context
from tools.result import ToolResult


def rag_query(query: str, top_k: int = 3, store_path: str | None = None) -> ToolResult:
    """Query the local knowledge base and return the relevant chunks."""
    if not query or not query.strip():
        return ToolResult(False, "rag_query", error="Query is empty.")
    if top_k <= 0:
        return ToolResult(False, "rag_query", error="top_k must be positive.")

    path = store_path or os.getenv("BORO_BHAI_RAG_STORE")
    try:
        if path:
            from rag.vector_store import VectorStore
            matches = VectorStore(path).search(query, top_k=top_k)
        else:
            matches = retrieve_context(query, top_k=top_k)
    except Exception as exc:  # pragma: no cover - defensive external failure path
        return ToolResult(False, "rag_query", error=f"Knowledge base retrieval failed: {exc}")

    if not matches:
        return ToolResult(False, "rag_query", error="No relevant chunks were found.", metadata={"query": query, "result_count": 0})

    return ToolResult(
        True,
        "rag_query",
        result={
            "query": query,
            "matches": matches,
            "context": build_rag_context(query, top_k=top_k),
        },
        metadata={"query": query, "result_count": len(matches)},
    )
