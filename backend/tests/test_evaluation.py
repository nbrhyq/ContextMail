from app.evaluation.metrics import EvaluationSample, summarize


def test_evaluation_summary_only_uses_supplied_observations():
    summary = summarize([
        EvaluationSample(task_id="1", expected_intent="OTHER", predicted_intent="OTHER", completed=True, llm_calls=2),
        EvaluationSample(task_id="2", expected_intent="OTHER", predicted_intent="UNCERTAIN", completed=False, llm_calls=1),
    ])

    assert summary.intent_accuracy == 0.5
    assert summary.task_completion_rate == 0.5
    assert summary.mean_llm_calls == 1.5
    assert summary.mean_cost_usd is None
