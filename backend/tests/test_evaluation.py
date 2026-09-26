from app.evaluation.metrics import EvaluationSample, summarize
from app.evaluation.dataset import load_dataset
from app.evaluation.run_benchmark import run
import pytest


def test_evaluation_summary_only_uses_supplied_observations():
    summary = summarize([
        EvaluationSample(task_id="1", expected_intent="OTHER", predicted_intent="OTHER", completed=True, llm_calls=2),
        EvaluationSample(task_id="2", expected_intent="OTHER", predicted_intent="UNCERTAIN", completed=False, llm_calls=1),
    ])

    assert summary.intent_accuracy == 0.5
    assert summary.task_completion_rate == 0.5
    assert summary.mean_llm_calls == 1.5
    assert summary.mean_cost_usd is None


def test_evaluation_dataset_has_80_diverse_cases():
    cases = load_dataset()
    assert len(cases) == 80
    assert len({case.user_request for case in cases}) == 80
    assert {case.expected_intent.value for case in cases} == {
        "JOB_APPLICATION", "PHD_OUTREACH", "SCHOOL_AFFAIRS", "UNCERTAIN"
    }


@pytest.mark.asyncio
async def test_deterministic_benchmark_runner():
    rows, summary = await run(live=False, limit=3)
    assert len(rows) == 3
    assert summary["sample_count"] == 3
