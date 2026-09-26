from app.graph.state import WorkflowState
from typing import Optional

from app.models.domain import ReviewDecision, ReviewResult, TraceEvent
from app.services.llm_service import StructuredLLM


class ReviewerAgent:
    def __init__(self, llm: Optional[StructuredLLM] = None) -> None:
        self.llm = llm

    async def run(self, state: WorkflowState) -> WorkflowState:
        draft = state.draft
        missing = []
        unsupported = []
        if not draft:
            missing.append("email draft")
        elif not draft.body.strip() or not draft.subject.strip():
            missing.append("complete subject and body")
        if draft and "[unsupported]" in draft.body.lower():
            unsupported.append("Draft contains an explicitly unsupported placeholder")
        needs_evidence = bool(draft and "[needs evidence]" in draft.body.lower())

        if missing:
            decision = ReviewDecision.NEED_USER_INFORMATION
        elif needs_evidence:
            decision = ReviewDecision.NEED_MORE_EVIDENCE
        elif unsupported:
            decision = ReviewDecision.REVISE
        else:
            decision = ReviewDecision.PASS
        fallback = ReviewResult(
            factuality="PASS" if not (unsupported or needs_evidence) else "FAIL",
            personalization="PASS" if state.recipient else "LIMITED",
            tone="PASS",
            unsupported_claims=unsupported,
            missing_information=missing,
            decision=decision,
            revision_instructions=["Collect reliable evidence or weaken/remove the claim"] if (unsupported or needs_evidence) else [],
        )
        state.review_result = fallback
        if self.llm and draft:
            try:
                result = await self.llm.generate_structured(
                    system_prompt=(
                        "You are an independent email reviewer. Compare every factual statement in the draft "
                        "against verified evidence. Do not rewrite the email. Return PASS, REVISE, "
                        "NEED_MORE_EVIDENCE, or NEED_USER_INFORMATION using the JSON schema."
                    ),
                    user_prompt=(
                        f"GOAL:\n{state.goal}\n\nDRAFT:\n{draft.model_dump_json()}\n\n"
                        f"VERIFIED EVIDENCE:\n{[item.model_dump(mode='json') for item in state.evidence if item.verified]}"
                    ),
                    schema=ReviewResult.model_json_schema(),
                )
                state.review_result = ReviewResult.model_validate(result)
                decision = state.review_result.decision
            except Exception as exc:
                state.errors.append(f"Ollama reviewer fallback used: {exc}")
        if self.llm:
            state.llm_call_count += 1
        state.execution_trace.append(TraceEvent(
            actor="reviewer_agent", action="review", status="COMPLETED",
            summary=f"Review decision: {decision.value}", token_usage=0,
        ))
        return state
