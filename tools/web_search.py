"""Web search tool for BORO BHAI."""

from __future__ import annotations

import html
import re
import urllib.error
import urllib.parse
import urllib.request

from tools.result import ToolResult


def _clean_query(query: str) -> str:
    """Validate and normalize a search query."""
    cleaned = (query or "").strip()
    if not cleaned:
        raise ValueError("Invalid search query.")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if len(cleaned) > 200:
        raise ValueError("Search query is too long.")
    return cleaned


def _normalize_url(raw_url: str) -> str:
    """Extract a usable URL from DuckDuckGo result markup."""
    candidate = raw_url.strip()
    if not candidate:
        return ""
    if "uddg=" in candidate:
        parsed = urllib.parse.urlparse(candidate)
        values = urllib.parse.parse_qs(parsed.query)
        if "uddg" in values:
            candidate = urllib.parse.unquote(values["uddg"][0])
    elif candidate.startswith("/"):
        candidate = urllib.parse.urljoin("https://duckduckgo.com/", candidate)
    return candidate


def _extract_search_results(html_text: str, max_results: int = 5):
    """Extract a small number of result titles and URLs from DuckDuckGo HTML."""
    matches = re.findall(
        r'<a[^>]*class="[^"]*result-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    results = []
    seen = set()
    for url, title_html in matches[:max_results * 4]:
        title = html.unescape(re.sub(r"<.*?>", " ", title_html)).strip()
        if not title:
            continue
        normalized_url = _normalize_url(url)
        if not normalized_url or normalized_url in seen:
            continue
        seen.add(normalized_url)
        results.append({"title": title, "url": normalized_url})
        if len(results) >= max_results:
            break

    return results


def web_search(query: str, max_results: int = 5) -> ToolResult:
    """Search the web for current information and return a structured tool result."""
    try:
        cleaned_query = _clean_query(query)
    except ValueError as exc:
        return ToolResult(False, "web_search", error=str(exc), metadata={"query": query or ""})

    if max_results <= 0:
        return ToolResult(False, "web_search", error="max_results must be positive.", metadata={"query": cleaned_query})

    encoded_query = urllib.parse.quote_plus(cleaned_query)
    request = urllib.request.Request(
        f"https://duckduckgo.com/html/?q={encoded_query}",
        headers={
            "User-Agent": "BORO-BHAI/1.0 (+https://github.com/Nusrat556/boro-bhai)",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            page_html = response.read().decode("utf-8", errors="replace")
    except (TimeoutError, urllib.error.URLError, ValueError) as exc:
        return ToolResult(
            False,
            "web_search",
            error=f"Web search failed: {exc}",
            metadata={"query": cleaned_query, "result_count": 0},
        )

    results = _extract_search_results(page_html, max_results=max_results)
    if not results:
        return ToolResult(
            False,
            "web_search",
            error="No search results were returned for that query.",
            metadata={"query": cleaned_query, "result_count": 0},
        )

    return ToolResult(
        True,
        "web_search",
        result=results,
        metadata={"query": cleaned_query, "result_count": len(results)},
    )
