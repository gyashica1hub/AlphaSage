"""Safe, typed supervisor workflow for evidence-backed research analysis."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AgentEvidence:
    title: str
    url: str
    excerpt: str
    document_id: str


@dataclass(frozen=True)
class AgentOutput:
    agent: str
    status: str
    summary: str
    evidence: list[AgentEvidence]
    warnings: list[str]


@dataclass(frozen=True)
class SupervisorResult:
    status: str
    question: str
    outputs: list[AgentOutput]
    evidence_valid: bool
    warnings: list[str]


def _evidence(results: list[dict]) -> list[AgentEvidence]:
    items: list[AgentEvidence] = []
    for result in results:
        citation = result.get("citation", {})
        if citation.get("document_id") and citation.get("url"):
            items.append(AgentEvidence(citation.get("title", "Source"), citation["url"], result.get("excerpt", ""), citation["document_id"]))
    return items


def run_supervisor(question: str, results: list[dict], timeout_seconds: float = 3.0) -> dict:
    """Run bounded research agents and reject unsupported conclusions."""
    evidence = _evidence(results)

    def research_agent() -> AgentOutput:
        summary = "Relevant research was found. Review the cited excerpts before drawing a conclusion." if evidence else "No supporting research was found for this question."
        return AgentOutput("research", "complete" if evidence else "insufficient_evidence", summary, evidence, [] if evidence else ["Add a source document or broaden the question."])

    def risk_agent() -> AgentOutput:
        warning = "This workflow does not provide personalized investment advice."
        return AgentOutput("risk", "complete", "Check uncertainty, source freshness, and concentration before acting.", evidence[:3], [warning])

    outputs: list[AgentOutput] = []
    warnings: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(agent) for agent in (research_agent, risk_agent)]
        for future in futures:
            try:
                outputs.append(future.result(timeout=timeout_seconds))
            except TimeoutError:
                outputs.append(AgentOutput("supervisor", "timeout", "Analysis timed out safely; no unsupported result was returned.", [], ["Retry with a narrower question."]))
                warnings.append("One analysis agent timed out.")

    evidence_valid = all(item.url and item.document_id for output in outputs for item in output.evidence)
    if not evidence_valid:
        warnings.append("Every included claim must have a valid source citation.")
    return asdict(SupervisorResult("complete" if outputs else "failed", question, outputs, evidence_valid, warnings))
