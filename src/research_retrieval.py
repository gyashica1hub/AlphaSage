"""Citation-first hybrid retrieval for local research documents."""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]{2,}", value.lower())}


def rank_documents(documents: list[dict], query: str, symbol: str | None = None, limit: int = 5) -> list[dict]:
    """Rank documents using phrase, token, title, and fuzzy semantic-like overlap."""
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    ranked: list[tuple[int, dict]] = []
    for document in documents:
        if symbol and document.get("symbol") not in {None, symbol.upper()}:
            continue
        title_tokens = _tokens(document.get("source_title", ""))
        content_tokens = _tokens(document.get("content", ""))
        normalized_query = " ".join(query.lower().split())
        normalized_text = " ".join(f"{document.get('source_title', '')} {document.get('content', '')}".lower().split())
        phrase_bonus = 3 if normalized_query in normalized_text else 0
        fuzzy_bonus = int(SequenceMatcher(None, normalized_query, normalized_text[:1200]).ratio() * 2)
        score = len(query_tokens & content_tokens) + (2 * len(query_tokens & title_tokens)) + phrase_bonus + fuzzy_bonus
        if score:
            ranked.append((score, document))
    ranked.sort(key=lambda item: (-item[0], item[1].get("created_at", "")))
    return [{"score": score, "citation": {"document_id": document["id"], "title": document["source_title"], "url": document["source_url"]}, "excerpt": document["content"][:700], "symbol": document.get("symbol"), "retrieval": "hybrid"} for score, document in ranked[:limit]]


def citations_are_valid(results: list[dict]) -> bool:
    """Require every result to carry an identifiable source citation."""
    return all(result.get("citation", {}).get("document_id") and result.get("citation", {}).get("url") for result in results)
