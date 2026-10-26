from src.research_retrieval import citations_are_valid, rank_documents


def test_retrieval_returns_citations_and_supports_symbol_scope() -> None:
    documents = [
        {"id": "a", "symbol": "INFY.NS", "source_title": "Infosys earnings", "source_url": "https://example.com/infy", "content": "Infosys reported strong quarterly revenue growth.", "created_at": "2026-01-01"},
        {"id": "b", "symbol": "RELIANCE.NS", "source_title": "Reliance update", "source_url": "https://example.com/reliance", "content": "Reliance expanded its energy business.", "created_at": "2026-01-02"},
    ]

    results = rank_documents(documents, "quarterly revenue", symbol="INFY.NS")

    assert len(results) == 1
    assert results[0]["citation"]["document_id"] == "a"
    assert results[0]["citation"]["url"] == "https://example.com/infy"
    assert results[0]["retrieval"] == "hybrid"
    assert citations_are_valid(results)


def test_retrieval_supports_phrase_matching_and_rejects_missing_citations() -> None:
    results = rank_documents([{"id": "a", "source_title": "Risk report", "source_url": "https://example.com/risk", "content": "Revenue growth slowed and debt increased."}], "revenue growth")
    assert results
    assert citations_are_valid(results)
    assert not citations_are_valid([{"citation": {"document_id": "", "url": ""}}])


def test_retrieval_requires_query_terms() -> None:
    assert rank_documents([], "") == []
