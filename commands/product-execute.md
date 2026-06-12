---
description: Execute approved plan using Superpowers-style workers.
argument-hint: "<issue id>"
---

# /product:execute

Run implementation from an approved plan.

## Do

1. Verify issue, spec, plan, and tasks exist.
2. Run `scripts/worker_orchestrator.py <issue> --write` if `specs/<issue>/worker-plan.md` is missing.
3. Use Superpowers process: plan, TDD when applicable, workers for independent tasks, review, verification.
4. Update `specs/<issue>/status.md` as work progresses.
5. Keep Git branch and commits tied to issue ID.

## Parallel Workers

Use parallel workers only when `specs/<issue>/worker-plan.md` marks the issue `parallel-eligible`.

## Next

- `/product:review` after implementation
- `/product:pr` after review passes
