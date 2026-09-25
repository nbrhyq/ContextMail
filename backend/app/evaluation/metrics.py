from typing import Optional

from pydantic import BaseModel, Field


class EvaluationSample(BaseModel):
    task_id: str
    expected_intent: Optional[str] = None
    predicted_intent: Optional[str] = None
    completed: bool = False
    unsupported_claims: int = Field(default=0, ge=0)
    accepted_without_edit: Optional[bool] = None
    edit_distance: Optional[int] = Field(default=None, ge=0)
    time_to_ready_ms: Optional[int] = Field(default=None, ge=0)
    llm_calls: int = Field(default=0, ge=0)
    estimated_cost_usd: Optional[float] = Field(default=None, ge=0)


class EvaluationSummary(BaseModel):
    sample_count: int
    intent_accuracy: Optional[float]
    task_completion_rate: float
    unsupported_claim_rate: float
    draft_acceptance_rate: Optional[float]
    mean_edit_distance: Optional[float]
    mean_time_to_ready_ms: Optional[float]
    mean_llm_calls: float
    mean_cost_usd: Optional[float]


def summarize(samples: list[EvaluationSample]) -> EvaluationSummary:
    if not samples:
        return EvaluationSummary(
            sample_count=0, intent_accuracy=None, task_completion_rate=0,
            unsupported_claim_rate=0, draft_acceptance_rate=None,
            mean_edit_distance=None, mean_time_to_ready_ms=None,
            mean_llm_calls=0, mean_cost_usd=None,
        )
    labeled = [s for s in samples if s.expected_intent is not None and s.predicted_intent is not None]
    acceptance = [s.accepted_without_edit for s in samples if s.accepted_without_edit is not None]
    edits = [s.edit_distance for s in samples if s.edit_distance is not None]
    times = [s.time_to_ready_ms for s in samples if s.time_to_ready_ms is not None]
    costs = [s.estimated_cost_usd for s in samples if s.estimated_cost_usd is not None]
    return EvaluationSummary(
        sample_count=len(samples),
        intent_accuracy=sum(s.expected_intent == s.predicted_intent for s in labeled) / len(labeled) if labeled else None,
        task_completion_rate=sum(s.completed for s in samples) / len(samples),
        unsupported_claim_rate=sum(s.unsupported_claims for s in samples) / len(samples),
        draft_acceptance_rate=sum(acceptance) / len(acceptance) if acceptance else None,
        mean_edit_distance=sum(edits) / len(edits) if edits else None,
        mean_time_to_ready_ms=sum(times) / len(times) if times else None,
        mean_llm_calls=sum(s.llm_calls for s in samples) / len(samples),
        mean_cost_usd=sum(costs) / len(costs) if costs else None,
    )

