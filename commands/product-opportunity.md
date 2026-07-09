---
description: Convert inbox material into a product opportunity/problem statement.
argument-hint: "<inbox item id or summary>"
---

# /product:opportunity

Shape the problem before creating execution work.

## Do

1. Identify user, problem, current workaround, desired outcome, evidence, and risk.
2. Update `workspace/opportunities.md`.
3. Recommend create/update/merge/drop.

## Shaping Router

Use opportunity shaping when a request is ambiguous, broad, strategic, or high-risk enough that immediate issue creation would hide important product context. Keep the user-facing surface short:

- short shaping: ask 1-3 questions, then promote to issue/spec/goal
- panel shaping: use multiple perspectives internally, then show only the compressed 1-3 questions

Do not route clear implementation requests here by default.

## Next

- `/product:issue` when actionable
- `/product:analyze` when evidence is weak
- `/product:roadmap` when priority/timing changes
