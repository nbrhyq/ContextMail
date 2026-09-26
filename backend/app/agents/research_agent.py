from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.graph.state import WorkflowState
from app.models.domain import Evidence, EvidenceSourceType, Intent, TraceEvent
from app.services.evidence_store import EvidenceStore
from app.tools.interfaces import WebSearchTool
from app.tools.mock_tools import MockWebSearch


@dataclass(frozen=True)
class ResearchPlan:
    missing_information: List[str]
    queries: List[str]
    preferred_domains: List[str]


class ResearchAgent:
    """Plans research and retains traceable evidence; search remains a dumb tool."""

    def __init__(self, search_tool: WebSearchTool | None = None) -> None:
        self.search_tool = search_tool or MockWebSearch()

    def plan(self, state: WorkflowState) -> ResearchPlan:
        recipient = state.recipient
        organization = recipient.organization if recipient else None
        preferred = []
        if organization and "." in organization and " " not in organization:
            preferred = [organization.removeprefix("https://").removeprefix("http://").strip("/")]
        identity = " ".join(filter(None, [
            recipient.name if recipient else None,
            recipient.organization if recipient else None,
        ])).strip()
        if state.intent == Intent.PHD_OUTREACH:
            subject = identity or "the named professor"
            return ResearchPlan(
                ["official profile", "research interests", "recent publications", "research overlap"],
                [f'{subject} official university profile research interests', f'{subject} recent publications lab'],
                preferred,
            )
        if state.intent == Intent.JOB_APPLICATION:
            subject = identity or "the target company and role"
            return ResearchPlan(
                ["official role and company context"],
                [f'{subject} official careers product role'],
                preferred,
            )
        if state.intent == Intent.SCHOOL_AFFAIRS:
            subject = identity or state.goal
            return ResearchPlan(
                ["official course or policy information"],
                [f'{subject} official university course policy'],
                preferred,
            )
        return ResearchPlan(["external context explicitly requested by user"], [state.goal], [])

    async def run(self, state: WorkflowState) -> WorkflowState:
        recipient = state.recipient
        if recipient and any((recipient.name, recipient.role, recipient.organization)):
            details = ", ".join(filter(None, [recipient.name, recipient.role, recipient.organization]))
            state.evidence = EvidenceStore.merge(state.evidence, [Evidence(
                claim="Recipient identity and affiliation",
                source_type=EvidenceSourceType.USER_INPUT,
                source_name="recipient_information",
                content=details,
                relevance="Recipient identity and affiliation supplied by the user",
                verified=True,
            )])

        plan = self.plan(state)
        collected: List[Evidence] = []
        failures: List[str] = []
        for query in plan.queries:
            try:
                collected.extend(await self.search_tool.search(query, preferred_domains=plan.preferred_domains))
            except Exception as exc:
                failures.append(f"{type(exc).__name__}: {exc}")
        state.evidence = EvidenceStore.merge(state.evidence, collected)
        provider = type(self.search_tool).__name__
        state.tool_results["web_search"] = {
            "status": "failed" if failures and not collected else "completed",
            "provider": provider,
            "missing_information": plan.missing_information,
            "queries": plan.queries,
            "results": len(collected),
            "failures": failures,
        }
        if failures:
            state.errors.extend(f"Research search failed: {failure}" for failure in failures)
        state.execution_trace.append(TraceEvent(
            actor="research_agent", action="research", status="FAILED" if failures and not collected else "COMPLETED",
            summary=f"Planned {len(plan.queries)} quer{'y' if len(plan.queries) == 1 else 'ies'}; retained {len(collected)} evidence item(s)",
            tool="web_search",
        ))
        return state
