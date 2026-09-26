# Evaluation-led Routing Iterations

These are real deterministic runs captured while improving the same 80-case suite. They measure workflow contracts, not human-perceived email quality.

| Version | Planner change | Intent accuracy | Task completion | Hard-case completion |
| --- | --- | ---: | ---: | ---: |
| V0 | Original broad keyword rules | 52.5% | 52.5% | 41.0% |
| V1 | Weighted scenario signals, ambiguity gate, typed missing-document checks | 86.3% | 90.0% | 82.1% |
| V2 | Added uncovered job/school signals and explicit missing-goal handling | 100.0% | 100.0% | 100.0% |

## Product decision

- LOW: Writer only. Direct thank-you, acceptance and reschedule tasks do not pay the latency cost of additional agents.
- MEDIUM: Context and/or Research as required, then Writer + Reviewer when materials or external facts increase risk.
- HIGH: Context + Research + Writer + Reviewer, with bounded re-planning and ASK_USER when evidence or identity is missing.
- LIVE follow-up: cap Reviewer re-planning at one targeted retry. The 12-case Qwen3 run showed repeated loops reaching 7 calls and ~91 seconds mean latency without improving completion.

## Integrity note

V2 was optimized using this dataset and may overfit its language. It is valuable as a regression suite, not as a claim of general-world 100% accuracy. The separate LIVE Qwen3 run and future blinded human evaluation are required for external validity.
