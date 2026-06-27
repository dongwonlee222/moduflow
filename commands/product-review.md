---
description: Review issue/spec/work across PM, UX, data, QA, and release gates.
argument-hint: "<issue id>"
---

# /product:review

Run staged verification.

## Do

1. Assign review concerns to workers where useful.
2. Check acceptance criteria, tests, UX, metrics, release risk, and docs.
3. Save results to `specs/<issue>/status.md`.

## Subagent Review

When the host-subagent execution backend is supported, `product:review` should dispatch specialized review tasks directly to subagents:
- `qa-reviewer` to run all test suites (`discover`), project doctor checks, and verify acceptance criteria.
- `pm-strategist` / `spec-architect` to review file changes against the spec design.

The host agent must call `invoke_subagent` to execute these reviews, and document the subagents' findings in `specs/<issue>/status.md` before concluding the review phase.

## Next

- `/product:plan` if gaps require more work
- `/product:pr` if review passes
