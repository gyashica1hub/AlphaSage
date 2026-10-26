from src.agent_analysis import run_supervisor


def test_supervisor_returns_typed_cited_outputs() -> None:
    result = run_supervisor("revenue risk", [{"citation": {"document_id": "doc-1", "title": "Annual report", "url": "https://example.com/report"}, "excerpt": "Revenue grew."}])
    assert result["status"] == "complete"
    assert result["evidence_valid"] is True
    assert result["outputs"][0]["agent"] == "research"


def test_supervisor_is_explicit_when_evidence_is_missing() -> None:
    result = run_supervisor("unknown", [])
    assert result["outputs"][0]["status"] == "insufficient_evidence"
    assert result["evidence_valid"] is True
