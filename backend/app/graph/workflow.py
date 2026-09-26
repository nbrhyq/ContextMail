from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.agents.context_agent import ContextAgent
from app.agents.llm_planner import LLMPlanner
from app.agents.planner import RuleBasedPlanner
from app.agents.research_agent import ResearchAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.writer import WriterAgent
from app.graph.state import WorkflowState
from app.models.domain import ApprovalStatus, NextAction, ReviewDecision, TraceEvent
from app.tools.document_reader import LocalDocumentReader
from app.services.llm_service import create_llm
from app.tools.web_search import create_search_tool


class GraphState(TypedDict):
    data: WorkflowState


class ContextMailWorkflow:
    def __init__(self, use_llm: bool = True, llm=None) -> None:
        self.planner = RuleBasedPlanner()
        llm = llm or (create_llm() if use_llm else None)
        self.llm_planner = LLMPlanner(llm, self.planner) if llm else None
        self.context_agent = ContextAgent(LocalDocumentReader())
        self.research_agent = ResearchAgent(create_search_tool())
        self.writer = WriterAgent(llm)
        self.reviewer = ReviewerAgent(llm)
        self.graph = self._build()

    def _build(self):
        graph = StateGraph(GraphState)
        graph.add_node("planner", self._plan)
        graph.add_node("context", self._context)
        graph.add_node("research", self._research)
        graph.add_node("writer", self._write)
        graph.add_node("reviewer", self._review)
        graph.add_node("replan", self._replan)
        graph.add_node("ready", self._ready)
        graph.set_entry_point("planner")
        graph.add_conditional_edges("planner", self._after_plan, {
            "context": "context", "research": "research", "writer": "writer", "stop": END,
        })
        graph.add_conditional_edges("context", self._after_context, {"research": "research", "writer": "writer"})
        graph.add_edge("research", "writer")
        graph.add_conditional_edges("writer", self._after_write, {"reviewer": "reviewer", "ready": "ready"})
        graph.add_conditional_edges("reviewer", self._after_review, {"ready": "ready", "replan": "replan", "stop": END})
        graph.add_conditional_edges("replan", self._after_replan, {"research": "research", "writer": "writer", "stop": END})
        graph.add_edge("ready", END)
        return graph.compile()

    async def run(self, state: WorkflowState) -> WorkflowState:
        result = await self.graph.ainvoke({"data": state})
        return result["data"]

    async def _plan(self, graph_state: GraphState) -> GraphState:
        state = graph_state["data"]
        if self.llm_planner:
            decision = await self.llm_planner.plan(state.user_request, state.recipient, state.uploaded_documents)
            state.intent = decision.intent
            state.goal = decision.goal
            state.risk_level = decision.risk_level
            state.available_context = decision.available_context
            state.missing_context = decision.missing_context
            state.selected_agents = decision.agents_required
            state.execution_plan = decision.execution_plan
            state.next_action = decision.next_action.value
            state.llm_call_count += 1
        else:
            state = self.planner.apply(state)
        state.workflow_status = "PLANNED"
        # LIVE evaluation showed repeated reviewer loops added large latency without
        # improving completion. Permit one targeted retry, then stop/ask the user.
        if "reviewer_agent" in state.selected_agents:
            state.max_iterations = min(state.max_iterations, 1)
        state.execution_trace.append(TraceEvent(
            actor="planner", action="plan", status="COMPLETED",
            summary=f"Intent {state.intent.value}; selected {', '.join(state.selected_agents)}",
        ))
        return {"data": state}

    async def _context(self, graph_state: GraphState) -> GraphState:
        return {"data": await self.context_agent.run(graph_state["data"])}

    async def _research(self, graph_state: GraphState) -> GraphState:
        return {"data": await self.research_agent.run(graph_state["data"])}

    async def _write(self, graph_state: GraphState) -> GraphState:
        return {"data": await self.writer.run(graph_state["data"])}

    async def _review(self, graph_state: GraphState) -> GraphState:
        return {"data": await self.reviewer.run(graph_state["data"])}

    async def _replan(self, graph_state: GraphState) -> GraphState:
        state = graph_state["data"]
        state.iteration_count += 1
        decision = state.review_result.decision if state.review_result else ReviewDecision.REVISE
        state.execution_trace.append(TraceEvent(
            actor="planner", action="replan", status="COMPLETED",
            summary=f"Re-planning after {decision.value}; iteration {state.iteration_count}/{state.max_iterations}",
        ))
        return {"data": state}

    async def _ready(self, graph_state: GraphState) -> GraphState:
        state = graph_state["data"]
        state.approval_status = ApprovalStatus.PENDING
        state.next_action = NextAction.REQUIRE_APPROVAL.value
        state.workflow_status = "READY_FOR_APPROVAL"
        state.execution_trace.append(TraceEvent(
            actor="system", action="approval_boundary", status="WAITING",
            summary="Draft is ready for explicit user approval",
        ))
        return {"data": state}

    @staticmethod
    def _after_plan(graph_state: GraphState) -> str:
        state = graph_state["data"]
        if state.next_action != NextAction.EXECUTE.value:
            state.workflow_status = "NEEDS_INPUT" if state.next_action == NextAction.ASK_USER.value else "STOPPED"
            return "stop"
        if "context_agent" in state.selected_agents:
            return "context"
        if "research_agent" in state.selected_agents:
            return "research"
        return "writer"

    @staticmethod
    def _after_context(graph_state: GraphState) -> str:
        return "research" if "research_agent" in graph_state["data"].selected_agents else "writer"

    @staticmethod
    def _after_write(graph_state: GraphState) -> str:
        return "reviewer" if "reviewer_agent" in graph_state["data"].selected_agents else "ready"

    @staticmethod
    def _after_review(graph_state: GraphState) -> str:
        state = graph_state["data"]
        if state.review_result and state.review_result.decision == ReviewDecision.PASS:
            return "ready"
        if state.can_replan:
            return "replan"
        state.workflow_status = "FAILED"
        return "stop"

    @staticmethod
    def _after_replan(graph_state: GraphState) -> str:
        state = graph_state["data"]
        if state.review_result and state.review_result.decision == ReviewDecision.NEED_MORE_EVIDENCE:
            return "research"
        if state.review_result and state.review_result.decision == ReviewDecision.NEED_USER_INFORMATION:
            state.workflow_status = "NEEDS_INPUT"
            state.next_action = NextAction.ASK_USER.value
            return "stop"
        return "writer"
