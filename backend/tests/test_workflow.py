import pytest

from app.graph.state import WorkflowState
from app.graph.workflow import ContextMailWorkflow
from app.models.domain import ApprovalStatus, EmailDraft, Recipient, ReviewDecision
from app.agents.reviewer import ReviewerAgent


@pytest.mark.asyncio
async def test_simple_workflow_stops_at_approval_boundary():
    state = WorkflowState(
        user_request="Write a short thank-you email to my professor.",
        recipient=Recipient(name="Professor Lee", email="lee@example.edu"),
    )

    result = await ContextMailWorkflow(use_llm=False).run(state)

    assert result.workflow_status == "READY_FOR_APPROVAL"
    assert result.approval_status == ApprovalStatus.PENDING
    assert result.draft is not None
    assert result.draft.recipient == "lee@example.edu"
    assert [event.actor for event in result.execution_trace] == ["planner", "writer_agent", "system"]


@pytest.mark.asyncio
async def test_missing_required_context_stops_before_writing():
    state = WorkflowState(user_request="Use my CV to draft an email to a recruiter.")

    result = await ContextMailWorkflow(use_llm=False).run(state)

    assert result.workflow_status == "NEEDS_INPUT"
    assert result.draft is None
    assert "referenced document upload" in result.missing_context


@pytest.mark.asyncio
async def test_reviewer_requests_research_and_workflow_replans():
    workflow = ContextMailWorkflow(use_llm=False)
    state = WorkflowState(
        user_request="Research a current claim and draft an email",
        draft=EmailDraft(subject="Claim", body="This statement is [needs evidence]."),
    )
    state = await ReviewerAgent().run(state)
    assert state.review_result.decision == ReviewDecision.NEED_MORE_EVIDENCE
    state.selected_agents = ["research_agent", "writer_agent", "reviewer_agent"]
    replanned = await workflow._replan({"data": state})
    assert replanned["data"].iteration_count == 1
    assert workflow._after_replan(replanned) == "research"
