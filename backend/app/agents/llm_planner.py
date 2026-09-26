from typing import Optional

from app.agents.planner import RuleBasedPlanner
from app.models.domain import PlannerDecision, Recipient, UploadedDocument
from app.services.llm_service import StructuredLLM


class LLMPlanner:
    def __init__(self, llm: StructuredLLM, fallback: Optional[RuleBasedPlanner] = None) -> None:
        self.llm = llm
        self.fallback = fallback or RuleBasedPlanner()

    async def plan(self, user_request: str, recipient: Optional[Recipient], documents: list[UploadedDocument]) -> PlannerDecision:
        fallback = self.fallback.plan(user_request, recipient, documents)
        prompt = {
            "user_request": user_request,
            "recipient": recipient.model_dump() if recipient else None,
            "documents": [document.filename for document in documents],
            "deterministic_precheck": fallback.model_dump(mode="json"),
        }
        try:
            result = await self.llm.generate_structured(
                system_prompt=(
                    "You are ContextMail's planner. Classify intent without forcing ambiguity. "
                    "Select only necessary agents from context_agent, research_agent, writer_agent, reviewer_agent. "
                    "Tools are pdf_reader, docx_reader, txt_reader, web_search and retrieval. "
                    "If required user information is absent, use ASK_USER. Never select an email-sending agent. "
                    "Return only data matching the supplied JSON schema."
                ),
                user_prompt=str(prompt),
                schema=PlannerDecision.model_json_schema(),
            )
            decision = PlannerDecision.model_validate(result)
            # Deterministic safety checks take precedence over model optimism.
            if fallback.confidence >= 0.8:
                decision.intent = fallback.intent
                decision.confidence = max(decision.confidence, fallback.confidence)
            if fallback.missing_context:
                decision.missing_context = list(dict.fromkeys(decision.missing_context + fallback.missing_context))
                decision.next_action = fallback.next_action
            if fallback.complexity.value == "LOW":
                decision.agents_required = fallback.agents_required
                decision.tools_required = fallback.tools_required
                decision.execution_plan = fallback.execution_plan
            return decision
        except Exception:
            return fallback
