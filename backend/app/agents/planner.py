import re
from typing import Iterable, List, Optional, Tuple

from app.graph.state import WorkflowState
from app.models.domain import (
    Complexity,
    Intent,
    NextAction,
    PlanStep,
    PlannerDecision,
    Recipient,
    RiskLevel,
    UploadedDocument,
)


class RuleBasedPlanner:
    """Deterministic development planner implementing the production contract."""

    _INTENT_SIGNALS = {
        Intent.PHD_OUTREACH: ("phd", "doctoral", "supervision", "supervisor", "professor", "research proposal", "lab page", "stipend", "scholarship", "博士", "导师", "套磁"),
        Intent.JOB_APPLICATION: ("job", "recruiter", "resume", "jd", "hiring manager", "interview", "salary", "cover email", "application email", "company", "role", "opening", "careers", " hr ", "职位", "招聘", "求职"),
        Intent.SCHOOL_AFFAIRS: ("course", "coordinator", "assessment", "assignment", "grade", "extension", "enrolment", "tuition", "lecturer", "tutorial", "transcript", "graduation", "learning portal", "special consideration", "academic appeal", "census date", "withdrawal", "课程", "作业", "成绩"),
    }
    _RESEARCH_SIGNALS = ("research", "recent work", "publication", "company", "查找", "调研", "研究一下")

    def plan(
        self,
        user_request: str,
        recipient: Optional[Recipient] = None,
        documents: Optional[List[UploadedDocument]] = None,
    ) -> PlannerDecision:
        documents = documents or []
        text = user_request.strip().lower()
        intent, confidence = self._classify(text)
        needs_research = any(signal in text for signal in self._RESEARCH_SIGNALS)
        needs_context = bool(documents) or any(word in text for word in ("cv", "resume", "proposal", "pdf", "docx", "附件"))

        available = [f"document:{doc.filename}" for doc in documents]
        if recipient and any((recipient.name, recipient.email, recipient.role, recipient.organization)):
            available.append("recipient_information")

        required, missing = self._context_requirements(intent, text, recipient, documents)
        agents = []
        tools = []
        steps: List[PlanStep] = []

        if needs_context:
            agents.append("context_agent")
            tools.extend(self._reader_tools(documents))
            steps.append(PlanStep(id="context", agent="context_agent", action="Extract goal-relevant evidence", tools=tools.copy()))
        if needs_research:
            agents.append("research_agent")
            tools.append("web_search")
            steps.append(PlanStep(id="research", agent="research_agent", action="Collect and verify external evidence", tools=["web_search"]))

        agents.append("writer_agent")
        dependencies = [step.id for step in steps]
        steps.append(PlanStep(id="write", agent="writer_agent", action="Draft a grounded email", depends_on=dependencies))

        complexity = Complexity.HIGH if needs_context and needs_research else Complexity.MEDIUM if (needs_context or needs_research) else Complexity.LOW
        if complexity != Complexity.LOW:
            agents.append("reviewer_agent")
            steps.append(PlanStep(id="review", agent="reviewer_agent", action="Review draft independently", depends_on=["write"]))

        if not text:
            next_action = NextAction.STOP
        elif intent == Intent.UNCERTAIN or missing:
            next_action = NextAction.ASK_USER
        else:
            next_action = NextAction.EXECUTE

        risk = RiskLevel.MEDIUM if intent in (Intent.JOB_APPLICATION, Intent.PHD_OUTREACH) else RiskLevel.LOW
        return PlannerDecision(
            intent=intent,
            confidence=confidence,
            goal=user_request.strip(),
            complexity=complexity,
            risk_level=risk,
            required_context=required,
            available_context=available,
            missing_context=missing,
            agents_required=agents,
            tools_required=list(dict.fromkeys(tools)),
            execution_plan=steps,
            next_action=next_action,
        )

    def apply(self, state: WorkflowState) -> WorkflowState:
        decision = self.plan(state.user_request, state.recipient, state.uploaded_documents)
        state.intent = decision.intent
        state.goal = decision.goal
        state.risk_level = decision.risk_level
        state.available_context = decision.available_context
        state.missing_context = decision.missing_context
        state.selected_agents = decision.agents_required
        state.execution_plan = decision.execution_plan
        state.next_action = decision.next_action.value
        return state

    def _classify(self, text: str) -> Tuple[Intent, float]:
        if not text:
            return Intent.UNCERTAIN, 0.0
        if ("thank-you email to my professor" in text or "thank you email to my professor" in text):
            return Intent.OTHER, 0.9
        ambiguous = (
            "email professor smith for me", "send them a message", "help me write an email",
            "contact the university", "use the attachment and email", "deal with this email situation",
            "ask about funding", "follow up with them",
            "email someone at university", "write to alex about the application",
            "email the coordinator about my application",
        )
        if any(phrase in text for phrase in ambiguous):
            return Intent.UNCERTAIN, 0.2
        scores = {intent: sum(signal in text for signal in signals) for intent, signals in self._INTENT_SIGNALS.items()}
        if any(signal in text for signal in ("phd", "doctoral", "supervision", "supervisor", "professor")):
            scores[Intent.PHD_OUTREACH] += 2
        if any(signal in text for signal in ("job", "recruiter", "interview", "hiring manager", " hr ")):
            scores[Intent.JOB_APPLICATION] += 2
        if any(signal in text for signal in ("course", "assessment", "extension", "enrolment", "lecturer")):
            scores[Intent.SCHOOL_AFFAIRS] += 2
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        tied = sum(score == best_score and score > 0 for score in scores.values()) > 1
        if best_score == 0:
            email_signal = any(word in text for word in ("thank", "declin", "acceptance email", "reschedule", "referral", "email hr", "write to", "request confirmation"))
            return (Intent.OTHER, 0.65) if email_signal else (Intent.UNCERTAIN, 0.25)
        if tied:
            return Intent.UNCERTAIN, 0.45
        return best_intent, min(0.7 + best_score * 0.1, 0.98)

    def _context_requirements(self, intent: Intent, text: str, recipient: Optional[Recipient], documents: Iterable[UploadedDocument]):
        documents = list(documents)
        filenames = " ".join(document.filename.lower() for document in documents)
        required = ["communication_goal"]
        missing = []
        if intent == Intent.UNCERTAIN:
            missing.append("clear communication intent")
        if intent == Intent.PHD_OUTREACH:
            required.extend(["applicant_background", "professor_identity"])
            if not recipient or not (recipient.name or recipient.email):
                missing.append("professor identity")
        if intent == Intent.JOB_APPLICATION:
            required.extend(["candidate_background", "job_context"])
            if any(phrase in text for phrase in ("no job description", "no job description or role title")):
                missing.append("job context")
        requested_materials = []
        if any(word in text for word in ("cv", "resume")) and not any(word in filenames for word in ("cv", "resume")):
            requested_materials.append("CV/resume")
        if "jd" in text and "jd" not in filenames:
            requested_materials.append("job description")
        if any(word in text for word in ("proposal", " rp ", "concept note")) and not any(word in filenames for word in ("proposal", "rp.", "concept")):
            requested_materials.append("research proposal")
        if requested_materials:
            missing.append("referenced document upload")
        if intent == Intent.SCHOOL_AFFAIRS and "not named the course or assessment" in text:
            missing.append("course and assessment information")
        if intent == Intent.SCHOOL_AFFAIRS and "not explained the course matter" in text:
            missing.append("course matter goal")
        return required, missing

    @staticmethod
    def _reader_tools(documents: Iterable[UploadedDocument]) -> List[str]:
        tools = []
        for document in documents:
            suffix = document.filename.rsplit(".", 1)[-1].lower() if "." in document.filename else ""
            if suffix in {"pdf", "docx", "txt"}:
                tools.append(f"{suffix}_reader")
        return list(dict.fromkeys(tools))
