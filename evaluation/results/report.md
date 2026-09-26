# ContextMail Evaluation

## Objective

Test when an adaptive agent workflow is worth its added calls and latency versus a fair single-generation baseline.

## Dataset

80 curated cases: {'job': 25, 'phd': 25, 'school': 20, 'ambiguous': 10}. Cases cover easy, medium, hard, missing context, ambiguity, research need, and unsupported-claim risk.

## Baseline

One deterministic smoke generator receives the request and available-material labels and returns an email draft. It has no Planner, Research, Reviewer, or re-planning.

## ContextMail

Planner-led adaptive routing through Context, Research, Writer, Reviewer, and bounded re-planning. Benchmark mode: deterministic CI-safe smoke.

## Results

| Metric | Single baseline | ContextMail |
| --- | ---: | ---: |
| Task completion | 72.5% | 100.0% |
| Unsupported claims / case | 0.000 | 0.000 |
| Automated rubric quality | 72.5% | 100.0% |
| Mean time-to-ready | 0.00 ms | 3.51 ms |
| Mean LLM calls | 0.00 | 0.00 |
| Input / output tokens | unavailable / unavailable | unavailable / unavailable |
| Estimated cost | unavailable | unavailable |

ContextMail intent accuracy: 100.0%.

## Simple vs Complex Tasks

{
  "easy": {
    "baseline": 1.0,
    "contextmail": 1.0
  },
  "medium": {
    "baseline": 0.84,
    "contextmail": 1.0
  },
  "hard": {
    "baseline": 0.5385,
    "contextmail": 1.0
  }
}

## Quality / Latency / Cost Trade-off

The baseline is faster and sufficient for many direct drafting tasks. ContextMail improved contract completion, with additional latency and calls concentrated in higher-risk tasks. Monetary cost is unavailable because the configured model is local and no defensible electricity/hosting price was supplied.

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
