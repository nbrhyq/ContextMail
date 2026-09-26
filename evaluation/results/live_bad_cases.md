# ContextMail Bad Case Analysis

Generated from benchmark failures.

## Failure taxonomy

- Intent Error
- Wrong Agent Routing
- Missing Context
- Research Failure
- Unsupported Claim
- Reviewer Miss
- Over-research
- Unnecessary Agent Calls
- Excessive Latency
- Poor Personalization

## Historical representative bad cases

### Ambiguous professor request was drafted

- Case: `Email Professor Smith for me.`
- Expected: `UNCERTAIN / ASK_USER`
- Actual (V0): `OTHER / READY_FOR_APPROVAL`
- Root cause: any email-like phrase was treated as enough intent.
- Product / Agent issue: Intent Error and unsafe action readiness.
- Product decision: add an ambiguity gate before scenario classification.

### Wrong document satisfied missing context

- Case: a job request referenced both CV and JD, but supplied only the JD.
- Expected: ask for the CV.
- Actual (V0): drafted because any uploaded document satisfied the material check.
- Root cause: document presence was checked, not document type.
- Product / Agent issue: Missing Context and Poor Personalization risk.
- Product decision: match requested material types against filenames.

### CV signal overrode explicit PhD goal

- Case: `Use my CV and proposal, research Professor Chen, and draft a PhD enquiry.`
- Expected: `PHD_OUTREACH` with full workflow.
- Actual (V0): tie/uncertain or job routing.
- Root cause: all lexical signals had equal weight.
- Product / Agent issue: Intent Error and Wrong Agent Routing.
- Product decision: weight explicit scenario terms above material names.

## Current-run failures

## job-002 — Reviewer Miss / Excessive Latency

- Expected: DRAFT
- Actual: FAILED / JOB_APPLICATION
- Root cause: review/re-plan exhausted the iteration budget without reaching PASS.
- Product / Agent issue: Reviewer Miss / Excessive Latency
- Proposed improvement: refine Planner signals or ask a narrower clarification before drafting.

## job-003 — Intent Error

- Expected: DRAFT
- Actual: NEEDS_INPUT / UNCERTAIN
- Root cause: routing or missing-context behavior did not match the case contract.
- Product / Agent issue: Intent Error
- Proposed improvement: refine Planner signals or ask a narrower clarification before drafting.

## phd-001 — Reviewer Miss / Excessive Latency

- Expected: DRAFT
- Actual: FAILED / PHD_OUTREACH
- Root cause: review/re-plan exhausted the iteration budget without reaching PASS.
- Product / Agent issue: Reviewer Miss / Excessive Latency
- Proposed improvement: refine Planner signals or ask a narrower clarification before drafting.

## phd-003 — Reviewer Miss / Excessive Latency

- Expected: DRAFT
- Actual: FAILED / PHD_OUTREACH
- Root cause: review/re-plan exhausted the iteration budget without reaching PASS.
- Product / Agent issue: Reviewer Miss / Excessive Latency
- Proposed improvement: refine Planner signals or ask a narrower clarification before drafting.

## school-002 — Missing Context / Wrong Agent Routing

- Expected: DRAFT
- Actual: NEEDS_INPUT / SCHOOL_AFFAIRS
- Root cause: routing or missing-context behavior did not match the case contract.
- Product / Agent issue: Missing Context / Wrong Agent Routing
- Proposed improvement: refine Planner signals or ask a narrower clarification before drafting.
