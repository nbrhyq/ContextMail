from pathlib import Path

import httpx
import pytest

from app.agents.research_agent import ResearchAgent
from app.graph.state import WorkflowState
from app.models.domain import ApprovalStatus, EmailDraft, Evidence, EvidenceSourceType, Intent, Recipient
from app.tools.outlook_email import OutlookEmailTool


class SuccessfulSearch:
    async def search(self, query, *, preferred_domains=None):
        return [Evidence(
            claim="Professor profile lists multimodal research",
            content="Research interests include multimodal learning.",
            source_name="Example University",
            source_url="https://example.edu/profile",
            source_type=EvidenceSourceType.WEB,
            relevance="Official profile",
            verified=True,
        )]


class FailingSearch:
    async def search(self, query, *, preferred_domains=None):
        raise httpx.ConnectError("offline")


@pytest.mark.asyncio
async def test_research_success_creates_traceable_evidence():
    state = WorkflowState(
        user_request="Research Professor Chen", intent=Intent.PHD_OUTREACH,
        goal="Research Professor Chen", recipient=Recipient(name="Professor Chen"),
    )
    result = await ResearchAgent(SuccessfulSearch()).run(state)
    web = [item for item in result.evidence if item.source_type == EvidenceSourceType.WEB]
    assert web[0].source_url == "https://example.edu/profile"
    assert web[0].evidence_id.startswith("evidence_")
    assert result.tool_results["web_search"]["status"] == "completed"


@pytest.mark.asyncio
async def test_research_failure_is_recorded_without_fake_evidence():
    state = WorkflowState(user_request="Research company", intent=Intent.JOB_APPLICATION, goal="Research company")
    result = await ResearchAgent(FailingSearch()).run(state)
    assert result.tool_results["web_search"]["status"] == "failed"
    assert not [item for item in result.evidence if item.source_type == EvidenceSourceType.WEB]
    assert result.errors


class TokenProvider:
    async def get_access_token(self):
        return "redacted-test-token"


@pytest.mark.asyncio
async def test_outlook_blocks_without_approval():
    tool = OutlookEmailTool(TokenProvider(), "https://graph.microsoft.test")
    with pytest.raises(PermissionError):
        await tool.send(EmailDraft(recipient="a@example.com", subject="Hi", body="Hello"), ApprovalStatus.PENDING)


@pytest.mark.asyncio
async def test_outlook_approved_send_supports_attachment(tmp_path: Path):
    attachment = tmp_path / "cv.txt"
    attachment.write_text("resume", encoding="utf-8")

    def handler(request: httpx.Request):
        assert request.url.path == "/me/sendMail"
        assert request.headers["Authorization"].startswith("Bearer ")
        assert b"contentBytes" in request.content
        return httpx.Response(202)

    tool = OutlookEmailTool(TokenProvider(), "https://graph.microsoft.test", transport=httpx.MockTransport(handler))
    message_id = await tool.send(
        EmailDraft(recipient="a@example.com", subject="Hi", body="Hello", attachments=[str(attachment)]),
        ApprovalStatus.APPROVED,
    )
    assert message_id.startswith("outlook_accepted_")
