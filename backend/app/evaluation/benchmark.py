from __future__ import annotations

import time
from collections import Counter
from typing import Any

from app.evaluation.baseline import SingleLLMBaseline
from app.evaluation.dataset import EvaluationCase
from app.graph.state import WorkflowState
from app.graph.workflow import ContextMailWorkflow
from app.models.domain import Recipient, UploadedDocument
from app.services.llm_service import StructuredLLM


def _recipient(case: EvaluationCase) -> Recipient | None:
    if case.expected_behavior == "ASK_USER" and "identity" in case.risk_notes.lower():
        return None
    if case.expected_intent.value == "PHD_OUTREACH" and case.expected_behavior == "DRAFT":
        return Recipient(name="Professor named in request")
    return None


def _unsupported(draft_body: str) -> list[str]:
    markers = ("[unsupported]", "guaranteed", "confirmed that", "your newest paper")
    return [marker for marker in markers if marker in draft_body.lower()]


async def evaluate_case(
    case: EvaluationCase, *, llm: StructuredLLM | None, use_llm: bool
) -> dict[str, Any]:
    baseline = SingleLLMBaseline(llm if use_llm else None)
    baseline_input_before = getattr(llm, "total_input_tokens", 0)
    baseline_output_before = getattr(llm, "total_output_tokens", 0)
    started = time.perf_counter()
    baseline_draft = await baseline.generate(case.user_request, case.supplied_context)
    baseline_ms = round((time.perf_counter() - started) * 1000, 2)
    baseline_unsupported = _unsupported(baseline_draft.body)
    baseline_completed = case.expected_behavior == "DRAFT" and bool(baseline_draft.body.strip())
    baseline_input = getattr(llm, "total_input_tokens", 0) - baseline_input_before if use_llm else None
    baseline_output = getattr(llm, "total_output_tokens", 0) - baseline_output_before if use_llm else None

    documents = [UploadedDocument(filename=name) for name in case.supplied_context]
    state = WorkflowState(user_request=case.user_request, recipient=_recipient(case), uploaded_documents=documents)
    context_input_before = getattr(llm, "total_input_tokens", 0)
    context_output_before = getattr(llm, "total_output_tokens", 0)
    started = time.perf_counter()
    result = await ContextMailWorkflow(use_llm=use_llm, llm=llm).run(state)
    context_ms = round((time.perf_counter() - started) * 1000, 2)
    expected_ready = case.expected_behavior == "DRAFT"
    context_completed = (
        result.workflow_status == "READY_FOR_APPROVAL" if expected_ready
        else result.workflow_status == "NEEDS_INPUT"
    )
    context_body = result.draft.body if result.draft else ""
    return {
        "case_id": case.case_id,
        "complexity": case.complexity,
        "expected_behavior": case.expected_behavior,
        "baseline": {
            "completed": baseline_completed,
            "unsupported_claims": len(baseline_unsupported),
            "time_to_ready_ms": baseline_ms,
            "llm_calls": 1 if use_llm else 0,
            "input_tokens": baseline_input,
            "output_tokens": baseline_output,
            "estimated_cost_usd": None,
            "quality_score": 1.0 if baseline_completed and not baseline_unsupported else 0.0,
        },
        "contextmail": {
            "predicted_intent": result.intent.value,
            "intent_correct": result.intent == case.expected_intent,
            "completed": context_completed,
            "unsupported_claims": len(_unsupported(context_body)),
            "time_to_ready_ms": context_ms,
            "llm_calls": result.llm_call_count,
            "input_tokens": getattr(llm, "total_input_tokens", 0) - context_input_before if use_llm else None,
            "output_tokens": getattr(llm, "total_output_tokens", 0) - context_output_before if use_llm else None,
            "estimated_cost_usd": None,
            "quality_score": 1.0 if context_completed and not _unsupported(context_body) else 0.0,
            "selected_agents": result.selected_agents,
            "status": result.workflow_status,
            "errors": result.errors,
        },
    }


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def variant(name: str) -> dict[str, Any]:
        data = [row[name] for row in rows]
        return {
            "task_completion_rate": round(sum(item["completed"] for item in data) / len(data), 4),
            "unsupported_claim_rate": round(sum(item["unsupported_claims"] for item in data) / len(data), 4),
            "mean_quality_score": round(sum(item["quality_score"] for item in data) / len(data), 4),
            "mean_time_to_ready_ms": round(sum(item["time_to_ready_ms"] for item in data) / len(data), 2),
            "mean_llm_calls": round(sum(item["llm_calls"] for item in data) / len(data), 2),
            "input_tokens": sum(item["input_tokens"] or 0 for item in data) if any(item["input_tokens"] is not None for item in data) else "unavailable",
            "output_tokens": sum(item["output_tokens"] or 0 for item in data) if any(item["output_tokens"] is not None for item in data) else "unavailable",
            "estimated_cost_usd": "unavailable",
        }
    intent = sum(row["contextmail"]["intent_correct"] for row in rows) / len(rows)
    return {
        "sample_count": len(rows),
        "distribution": dict(Counter(row["case_id"].split("-")[0] for row in rows)),
        "contextmail_intent_accuracy": round(intent, 4),
        "baseline": variant("baseline"),
        "contextmail": variant("contextmail"),
        "by_complexity": {
            level: {
                name: round(sum(row[name]["completed"] for row in rows if row["complexity"] == level) /
                            sum(row["complexity"] == level for row in rows), 4)
                for name in ("baseline", "contextmail")
            } for level in ("easy", "medium", "hard")
        },
    }
