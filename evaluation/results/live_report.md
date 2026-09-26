# ContextMail Evaluation

## Objective

Test when an adaptive agent workflow is worth its added calls and latency versus a fair single-generation baseline.

## Dataset

12 curated cases: {'job': 3, 'phd': 3, 'school': 3, 'ambiguous': 3}. Cases cover easy, medium, hard, missing context, ambiguity, research need, and unsupported-claim risk.

## Baseline

One Ollama model call receives the request and available-material labels and returns an email draft. It has no Planner, Research, Reviewer, or re-planning.

## ContextMail

Planner-led adaptive routing through Context, Research, Writer, Reviewer, and bounded re-planning. Benchmark mode: LIVE Ollama.

## Results

| Metric | Single baseline | ContextMail |
| --- | ---: | ---: |
| Task completion | 75.0% | 58.3% |
| Unsupported claims / case | 0.000 | 0.000 |
| Automated rubric quality | 75.0% | 58.3% |
| Mean time-to-ready | 16753.62 ms | 91020.76 ms |
| Mean LLM calls | 1.00 | 2.83 |
| Input / output tokens | 1028 / 3142 | 8351 / 16291 |
| Estimated cost | unavailable | unavailable |

ContextMail intent accuracy: 91.7%.

## Simple vs Complex Tasks

{
  "easy": {
    "baseline": 1.0,
    "contextmail": 1.0
  },
  "medium": {
    "baseline": 1.0,
    "contextmail": 0.5
  },
  "hard": {
    "baseline": 0.5714,
    "contextmail": 0.4286
  }
}

## Quality / Latency / Cost Trade-off

The baseline is faster and sufficient for many direct drafting tasks. This run did not justify the full agent workflow: the baseline completed more tasks, while ContextMail used more calls, tokens and latency. Reviewer/re-plan loops and missing LIVE evidence are the main optimization targets. Monetary cost is unavailable because the configured model is local and no defensible electricity/hosting price was supplied.

## Bad Cases

See `bad_cases.md` for failure → root cause → product decision analysis.

## Product Decisions

Keep LOW tasks on Writer-only routing; add Context + Reviewer for supplied materials or medium risk; reserve Research for explicit/current external facts and HIGH-risk work.

## Limitations

- Curated synthetic cases, not real-user acceptance data.
- Quality score is an automated rubric, not user adoption.
- Search is mocked unless LIVE credentials are configured.
- Edit distance is unavailable without human-edited reference drafts.
- Monetary cost remains unavailable rather than estimated from invented data.

## Next Validation

Run authenticated LIVE research and Ollama evaluation, then collect blinded human ratings and edited drafts from 5–10 target users.
