"""Safe, typed supervisor workflow for evidence-backed research analysis."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import asdict, dataclass
from enum import StrEnum
from time import monotonic
from uuid import uuid4


class ToolName(StrEnum):
    RETRIEVE_RESEARCH = "retrieve_research"
    READ_PORTFOLIO = "read_portfolio"
    PLACE_ORDER = "place_order"
    SEND_MESSAGE = "send_message"


SAFE_TOOLS = {ToolName.RETRIEVE_RESEARCH, ToolName.READ_PORTFOLIO}


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
    checkpoint_id: str
    approval_required: bool


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    status: str
    completed_agents: list[str]
    created_at_monotonic: float


def _evidence(results: list[dict]) -> list[AgentEvidence]:
    items: list[AgentEvidence] = []
    for result in results:
        citation = result.get("citation", {})
        if citation.get("document_id") and citation.get("url"):
            items.append(AgentEvidence(citation.get("title", "Source"), citation["url"], result.get("excerpt", ""), citation["document_id"]))
    return items


def run_supervisor(question: str, results: list[dict], timeout_seconds: float = 3.0, retries: int = 1, requested_tool: str | None = None) -> dict:
    """Run bounded research agents with permissions, retries, and a checkpoint."""
    checkpoint = Checkpoint(str(uuid4()), "running", [], monotonic())
    if requested_tool and requested_tool not in {tool.value for tool in ToolName}:
        return asdict(SupervisorResult("blocked", question, [], False, ["Unknown tool is not permitted."], checkpoint.checkpoint_id, False))
    if requested_tool and requested_tool not in {tool.value for tool in SAFE_TOOLS}:
        return asdict(SupervisorResult("awaiting_approval", question, [], False, [f"Human approval is required before using {requested_tool}."], checkpoint.checkpoint_id, True))
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
        for index, future in enumerate(futures):
            completed = False
            for attempt in range(retries + 1):
                try:
                    outputs.append(future.result(timeout=timeout_seconds))
                    completed = True
                    break
                except TimeoutError:
                    if attempt == retries:
                        outputs.append(AgentOutput("supervisor", "timeout", "Analysis timed out safely; no unsupported result was returned.", [], ["Retry with a narrower question."]))
                        warnings.append("One analysis agent timed out.")
            if completed:
                checkpoint = Checkpoint(checkpoint.checkpoint_id, "running", [*checkpoint.completed_agents, ("research", "risk")[index]], checkpoint.created_at_monotonic)

    evidence_valid = all(item.url and item.document_id for output in outputs for item in output.evidence)
    if not evidence_valid:
        warnings.append("Every included claim must have a valid source citation.")
    checkpoint = Checkpoint(checkpoint.checkpoint_id, "complete", checkpoint.completed_agents, checkpoint.created_at_monotonic)
    return asdict(SupervisorResult("complete" if outputs else "failed", question, outputs, evidence_valid, warnings, checkpoint.checkpoint_id, False))
