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

No contract failures in the current deterministic V2 run. This is a regression result on the iteration dataset, not evidence of perfect real-world performance.
