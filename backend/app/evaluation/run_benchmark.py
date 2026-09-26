from __future__ import annotations

import argparse
import asyncio
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from app.evaluation.benchmark import evaluate_case, summarize_results
from app.evaluation.dataset import load_dataset
from app.services.llm_service import create_llm


async def run(live: bool, limit: int | None = None, representative: bool = False) -> tuple[list[dict], dict]:
    all_cases = load_dataset()
    if representative:
        groups = [[case for case in all_cases if case.case_id.startswith(prefix)] for prefix in ("job-", "phd-", "school-", "ambiguous-")]
        per_group = max(1, (limit or 12) // 4)
        cases = [case for group in groups for case in group[:per_group]]
    else:
        cases = all_cases[:limit]
    llm = create_llm() if live else None
    rows = [await evaluate_case(case, llm=llm, use_llm=live) for case in cases]
    return rows, summarize_results(rows)


def _bad_cases(rows: list[dict]) -> str:
    taxonomy = [
        "Intent Error", "Wrong Agent Routing", "Missing Context", "Research Failure",
        "Unsupported Claim", "Reviewer Miss", "Over-research", "Unnecessary Agent Calls",
        "Excessive Latency", "Poor Personalization",
    ]
    sections = [
        "# ContextMail Bad Case Analysis", "", "Generated from benchmark failures.", "",
        "## Failure taxonomy", "", *[f"- {item}" for item in taxonomy], "",
        "## Historical representative bad cases", "",
        "### Ambiguous professor request was drafted", "",
        "- Case: `Email Professor Smith for me.`", "- Expected: `UNCERTAIN / ASK_USER`",
        "- Actual (V0): `OTHER / READY_FOR_APPROVAL`", "- Root cause: any email-like phrase was treated as enough intent.",
        "- Product / Agent issue: Intent Error and unsafe action readiness.",
        "- Product decision: add an ambiguity gate before scenario classification.", "",
        "### Wrong document satisfied missing context", "",
        "- Case: a job request referenced both CV and JD, but supplied only the JD.", "- Expected: ask for the CV.",
        "- Actual (V0): drafted because any uploaded document satisfied the material check.",
        "- Root cause: document presence was checked, not document type.",
        "- Product / Agent issue: Missing Context and Poor Personalization risk.",
        "- Product decision: match requested material types against filenames.", "",
        "### CV signal overrode explicit PhD goal", "",
        "- Case: `Use my CV and proposal, research Professor Chen, and draft a PhD enquiry.`",
        "- Expected: `PHD_OUTREACH` with full workflow.", "- Actual (V0): tie/uncertain or job routing.",
        "- Root cause: all lexical signals had equal weight.",
        "- Product / Agent issue: Intent Error and Wrong Agent Routing.",
        "- Product decision: weight explicit scenario terms above material names.", "",
        "## Current-run failures", "",
    ]
    failures = [row for row in rows if not row["contextmail"]["completed"] or not row["contextmail"]["intent_correct"]]
    for row in failures[:20]:
        if row["contextmail"]["status"] == "FAILED" and row["contextmail"]["llm_calls"] >= 7:
            issue = "Reviewer Miss / Excessive Latency"
        elif not row["contextmail"]["intent_correct"]:
            issue = "Intent Error"
        elif any("Research search failed" in error for error in row["contextmail"]["errors"]):
            issue = "Research Failure"
        else:
            issue = "Missing Context / Wrong Agent Routing"
        sections.extend([
            f"## {row['case_id']} — {issue}", "",
            f"- Expected: {row['expected_behavior']}",
            f"- Actual: {row['contextmail']['status']} / {row['contextmail']['predicted_intent']}",
            f"- Root cause: {'review/re-plan exhausted the iteration budget without reaching PASS' if row['contextmail']['status'] == 'FAILED' else 'routing or missing-context behavior did not match the case contract'}.",
            f"- Product / Agent issue: {issue}",
            "- Proposed improvement: refine Planner signals or ask a narrower clarification before drafting.", "",
        ])
    if not failures:
        sections.extend(["No contract failures in the current deterministic V2 run. This is a regression result on the iteration dataset, not evidence of perfect real-world performance.", ""])
    return "\n".join(sections)


def _report(summary: dict, live: bool) -> str:
    b, c = summary["baseline"], summary["contextmail"]
    if c["task_completion_rate"] > b["task_completion_rate"]:
        tradeoff = "ContextMail improved contract completion, with additional latency and calls concentrated in higher-risk tasks."
    else:
        tradeoff = (
            "This run did not justify the full agent workflow: the baseline completed more tasks, while ContextMail used "
            "more calls, tokens and latency. Reviewer/re-plan loops and missing LIVE evidence are the main optimization targets."
        )
    return f"""# ContextMail Evaluation

## Objective

Test when an adaptive agent workflow is worth its added calls and latency versus a fair single-generation baseline.

## Dataset

{summary['sample_count']} curated cases: {summary['distribution']}. Cases cover easy, medium, hard, missing context, ambiguity, research need, and unsupported-claim risk.

## Baseline

One {'Ollama model call' if live else 'deterministic smoke generator'} receives the request and available-material labels and returns an email draft. It has no Planner, Research, Reviewer, or re-planning.

## ContextMail

Planner-led adaptive routing through Context, Research, Writer, Reviewer, and bounded re-planning. Benchmark mode: {'LIVE Ollama' if live else 'deterministic CI-safe smoke'}.

## Results

| Metric | Single baseline | ContextMail |
| --- | ---: | ---: |
| Task completion | {b['task_completion_rate']:.1%} | {c['task_completion_rate']:.1%} |
| Unsupported claims / case | {b['unsupported_claim_rate']:.3f} | {c['unsupported_claim_rate']:.3f} |
| Automated rubric quality | {b['mean_quality_score']:.1%} | {c['mean_quality_score']:.1%} |
| Mean time-to-ready | {b['mean_time_to_ready_ms']:.2f} ms | {c['mean_time_to_ready_ms']:.2f} ms |
| Mean LLM calls | {b['mean_llm_calls']:.2f} | {c['mean_llm_calls']:.2f} |
| Input / output tokens | {b['input_tokens']} / {b['output_tokens']} | {c['input_tokens']} / {c['output_tokens']} |
| Estimated cost | unavailable | unavailable |

ContextMail intent accuracy: {summary['contextmail_intent_accuracy']:.1%}.

## Simple vs Complex Tasks

{json.dumps(summary['by_complexity'], indent=2)}

## Quality / Latency / Cost Trade-off

The baseline is faster and sufficient for many direct drafting tasks. {tradeoff} Monetary cost is unavailable because the configured model is local and no defensible electricity/hosting price was supplied.

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
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Use configured Ollama and LIVE providers")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--representative", action="store_true", help="Stratify limited run across all scenarios")
    parser.add_argument("--report-only", action="store_true", help="Regenerate Markdown from existing JSON results")
    args = parser.parse_args()
    root = Path("evaluation/results")
    root.mkdir(parents=True, exist_ok=True)
    stem = "live_results" if args.live else "results"
    if args.report_only:
        payload = json.loads((root / f"{stem}.json").read_text(encoding="utf-8"))
        rows, summary = payload["cases"], payload["summary"]
    else:
        rows, summary = asyncio.run(run(args.live, args.limit, args.representative))
        payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "live": args.live, "summary": summary, "cases": rows}
    (root / f"{stem}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (root / f"{stem}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["case_id", "complexity", "baseline_completed", "contextmail_completed", "intent_correct"])
        for row in rows:
            writer.writerow([row["case_id"], row["complexity"], row["baseline"]["completed"], row["contextmail"]["completed"], row["contextmail"]["intent_correct"]])
    (root / ("live_report.md" if args.live else "report.md")).write_text(_report(summary, args.live), encoding="utf-8")
    (root / ("live_bad_cases.md" if args.live else "bad_cases.md")).write_text(_bad_cases(rows), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
