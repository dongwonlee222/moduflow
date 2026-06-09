---
description: Execute approved plan using Superpowers-style workers.
argument-hint: "<issue id>"
---

# /product:execute

Run implementation from an approved plan.

## Do

1. Verify issue, spec, plan, and tasks exist.
2. Use Superpowers process: plan, TDD when applicable, workers for independent tasks, review, verification.
3. Update `specs/<issue>/status.md` as work progresses.
4. Keep Git branch and commits tied to issue ID.

## Parallel Workers

Use parallel workers only for independent tasks with low file/state overlap.

## Next

- `/product:review` after implementation
- `/product:pr` after review passes

