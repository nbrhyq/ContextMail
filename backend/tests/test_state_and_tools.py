import pytest

from app.graph.state import WorkflowState
from app.models.domain import ApprovalStatus, EmailDraft
from app.tools.mock_tools import MockEmailTool


def test_workflow_iteration_limit():
    state = WorkflowState(user_request="Draft an email", iteration_count=3, max_iterations=3)
    assert state.can_replan is False


@pytest.mark.asyncio
async def test_email_tool_requires_explicit_approval():
    tool = MockEmailTool()
    draft = EmailDraft(recipient="person@example.com", subject="Hello", body="Hi")

    with pytest.raises(PermissionError):
        await tool.send(draft, ApprovalStatus.PENDING)

    message_id = await tool.send(draft, ApprovalStatus.APPROVED)
    assert message_id.startswith("mock_email_")
