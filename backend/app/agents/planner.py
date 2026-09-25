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
        Intent.PHD_OUTREACH: ("phd", "doctoral", "supervision", "research proposal", "博士", "导师", "套磁"),
        Intent.JOB_APPLICATION: ("job", "recruiter", "application", "resume", "cv", "jd", "职位", "招聘", "求职"),
        Intent.SCHOOL_AFFAIRS: ("course", "coordinator", "assessment", "assignment", "grade", "课程", "作业", "成绩"),
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
        scores = {intent: sum(signal in text for signal in signals) for intent, signals in self._INTENT_SIGNALS.items()}
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        tied = sum(score == best_score and score > 0 for score in scores.values()) > 1
        if best_score == 0:
            email_signal = any(word in text for word in ("email", "mail", "邮件", "write to", "contact"))
            return (Intent.OTHER, 0.65) if email_signal else (Intent.UNCERTAIN, 0.25)
        if tied:
            return Intent.UNCERTAIN, 0.45
        return best_intent, min(0.7 + best_score * 0.1, 0.98)

    def _context_requirements(self, intent: Intent, text: str, recipient: Optional[Recipient], documents: Iterable[UploadedDocument]):
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
        referenced_material = any(word in text for word in ("cv", "resume", "proposal", "jd", "pdf", "docx", "附件"))
        if referenced_material and not list(documents):
            missing.append("referenced document upload")
        return required, missing

    @staticmethod
    def _reader_tools(documents: Iterable[UploadedDocument]) -> List[str]:
        tools = []
        for document in documents:
            suffix = document.filename.rsplit(".", 1)[-1].lower() if "." in document.filename else ""
            if suffix in {"pdf", "docx", "txt"}:
                tools.append(f"{suffix}_reader")
        return list(dict.fromkeys(tools))
