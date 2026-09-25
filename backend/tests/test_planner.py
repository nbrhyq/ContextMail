from app.agents.planner import RuleBasedPlanner
from app.models.domain import Intent, NextAction, Recipient, UploadedDocument


def test_phd_plan_activates_context_research_and_review():
    decision = RuleBasedPlanner().plan(
        "Use my CV and research proposal, research Professor X's recent work, and draft a PhD inquiry.",
        recipient=Recipient(name="Professor X"),
        documents=[UploadedDocument(filename="cv.pdf"), UploadedDocument(filename="proposal.docx")],
    )

    assert decision.intent == Intent.PHD_OUTREACH
    assert decision.next_action == NextAction.EXECUTE
    assert decision.agents_required == ["context_agent", "research_agent", "writer_agent", "reviewer_agent"]
    assert set(decision.tools_required) == {"pdf_reader", "docx_reader", "web_search"}


def test_simple_thank_you_uses_only_writer():
    decision = RuleBasedPlanner().plan("Write a short thank-you email to my professor.")

    assert decision.intent == Intent.OTHER
    assert decision.agents_required == ["writer_agent"]
    assert decision.tools_required == []


def test_uncertain_request_is_not_forced_into_supported_intent():
    decision = RuleBasedPlanner().plan("Can you help me with this?")

    assert decision.intent == Intent.UNCERTAIN
    assert decision.next_action == NextAction.ASK_USER


def test_referenced_missing_document_asks_user():
    decision = RuleBasedPlanner().plan("Use my CV and this JD to draft an email to the recruiter.")

    assert decision.intent == Intent.JOB_APPLICATION
    assert "referenced document upload" in decision.missing_context
    assert decision.next_action == NextAction.ASK_USER


def test_empty_request_stops_planning():
    decision = RuleBasedPlanner().plan("   ")
    assert decision.next_action == NextAction.STOP
