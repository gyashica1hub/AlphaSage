from src.research_retrieval import rank_documents


def test_retrieval_returns_citations_and_supports_symbol_scope() -> None:
    documents = [
        {"id": "a", "symbol": "INFY.NS", "source_title": "Infosys earnings", "source_url": "https://example.com/infy", "content": "Infosys reported strong quarterly revenue growth.", "created_at": "2026-01-01"},
        {"id": "b", "symbol": "RELIANCE.NS", "source_title": "Reliance update", "source_url": "https://example.com/reliance", "content": "Reliance expanded its energy business.", "created_at": "2026-01-02"},
    ]

    results = rank_documents(documents, "quarterly revenue", symbol="INFY.NS")

    assert len(results) == 1
    assert results[0]["citation"]["document_id"] == "a"
    assert results[0]["citation"]["url"] == "https://example.com/infy"


def test_retrieval_requires_query_terms() -> None:
    assert rank_documents([], "") == []
