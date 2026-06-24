# Market Entry Analysis Recipe

Create this package under `business/<slug>/`.

```text
brief.md
assumptions.md
source-list.md
calculation-model.md
market-entry/report.md
decision.md
validation.md
issue-candidates.md
exports/
```

## Report Structure

`market-entry/report.md` should use this structure:

```text
# <Market Entry Report Title>

## Executive Summary
## Decision Recommendation
## Market Context
## Customer And Demand
## Competitive Landscape
## Route To Market
## Revenue And Unit Economics
## Operating Requirements
## Risks And Unknowns
## Validation Plan
## Next Actions
```

## Required Checks

- Define market, geography, customer segment, and entry window.
- Separate facts, assumptions, estimates, and judgment.
- Show top 3-5 assumptions that can reverse the decision.
- Link each claim to `source-list.md` or label it as an assumption.
- Include at least one table for options, economics, or risks.
- End with a decision-ready recommendation: go, no-go, staged test, or defer.
- For Korean reports, apply `writing-style.md` before review.

## Review Gate

Before export, create `validation.md` with:

- source coverage
- calculation sanity check
- risk coverage
- tone check
- unresolved questions
- recommended next ModuFlow command
