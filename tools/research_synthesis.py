"""Web research synthesis for BORO BHAI."""

from __future__ import annotations

import re

from app.llm import generate_response
from tools.result import ToolResult
from tools.web_search import web_search


def _clean_query(query: str) -> str:
    cleaned = (query or "").strip()
    if not cleaned:
        raise ValueError("Research query cannot be empty.")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if len(cleaned) > 200:
        raise ValueError("Research query is too long.")
    return cleaned


def _summarize_search_results(search_result):
    if not search_result or not getattr(search_result, "success", False):
        return []
    items = search_result.result or []
    normalized = []
    for item in items:
        if isinstance(item, dict):
            normalized.append({
                "title": str(item.get("title", "Untitled result")).strip(),
                "url": str(item.get("url", "")).strip(),
            })
    return normalized


def research_and_synthesize(query: str, max_results: int = 5) -> ToolResult:
    """Search the web and synthesize a concise answer using the local LLM."""
    try:
        cleaned_query = _clean_query(query)
    except ValueError as exc:
        return ToolResult(False, "research_synthesis", error=str(exc), metadata={"query": query or ""})

    search_result = web_search(cleaned_query, max_results=max_results)
    if not search_result.success:
        return ToolResult(
            False,
            "research_synthesis",
            error=search_result.error or "No research results were available.",
            metadata={"query": cleaned_query, "sources": []},
        )

    sources = _summarize_search_results(search_result)
    prompt = (
        "You are BORO BHAI. Synthesize the following web research results into a concise and factual answer. "
        "Keep the answer grounded in the result list and clearly preserve the source title and URL for each claim.\n\n"
        f"Query: {cleaned_query}\n\n"
        f"Results:\n{sources}\n\n"
        "Return a short summary with a 'Summary:' section and a 'Sources:' section listing each title and URL."
    )

    try:
        answer = generate_response(prompt).strip()
    except Exception as exc:  # pragma: no cover - defensive guard around external model failure
        return ToolResult(
            False,
            "research_synthesis",
            error=f"Research synthesis failed: {exc}",
            metadata={"query": cleaned_query, "sources": sources},
        )

    return ToolResult(
        True,
        "research_synthesis",
        result={
            "answer": answer,
            "sources": sources,
        },
        metadata={"query": cleaned_query, "source_count": len(sources)},
    )
