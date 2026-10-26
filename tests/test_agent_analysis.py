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


def test_sensitive_tools_require_human_approval() -> None:
    result = run_supervisor("send report", [], requested_tool="send_message")
    assert result["status"] == "awaiting_approval"
    assert result["approval_required"] is True


def test_unknown_tools_are_blocked() -> None:
    result = run_supervisor("test", [], requested_tool="delete_everything")
    assert result["status"] == "blocked"
    assert result["approval_required"] is False
