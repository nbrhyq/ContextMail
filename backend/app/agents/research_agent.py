from app.graph.state import WorkflowState
from app.models.domain import Evidence, EvidenceSourceType, TraceEvent


class ResearchAgent:
    """Mock-safe research agent. A real WebSearchTool can be injected later."""

    async def run(self, state: WorkflowState) -> WorkflowState:
        recipient = state.recipient
        if recipient and any((recipient.name, recipient.role, recipient.organization)):
            details = ", ".join(filter(None, [recipient.name, recipient.role, recipient.organization]))
            state.evidence.append(Evidence(
                source_type=EvidenceSourceType.USER_INPUT,
                source="recipient_information",
                content=details,
                relevance="Recipient identity and affiliation supplied by the user",
                verified=True,
            ))
        state.tool_results["web_search"] = {
            "status": "mocked",
            "query": state.goal,
            "results": 0,
            "note": "No external claims were added in mock mode.",
        }
        state.execution_trace.append(TraceEvent(
            actor="research_agent", action="research", status="COMPLETED",
            summary="Research evaluated; external search is mocked", tool="web_search",
        ))
        return state

