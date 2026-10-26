"""Citation-first lexical retrieval used before introducing vector search."""

from __future__ import annotations

import re


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]{2,}", value.lower())}


def rank_documents(documents: list[dict], query: str, symbol: str | None = None, limit: int = 5) -> list[dict]:
    """Rank documents by title/content overlap and return citation metadata."""
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    ranked: list[tuple[int, dict]] = []
    for document in documents:
        if symbol and document.get("symbol") not in {None, symbol.upper()}:
            continue
        title_tokens = _tokens(document.get("source_title", ""))
        content_tokens = _tokens(document.get("content", ""))
        score = len(query_tokens & content_tokens) + (2 * len(query_tokens & title_tokens))
        if score:
            ranked.append((score, document))
    ranked.sort(key=lambda item: (-item[0], item[1].get("created_at", "")))
    return [{"score": score, "citation": {"document_id": document["id"], "title": document["source_title"], "url": document["source_url"]}, "excerpt": document["content"][:500]} for score, document in ranked[:limit]]
