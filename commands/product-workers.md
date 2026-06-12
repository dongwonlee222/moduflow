---
description: Generate a worker plan and parallel execution decision for an issue.
argument-hint: "<issue id>"
---

# /product:workers

Create an issue-local worker plan.

## Do

1. Verify `specs/<issue>/tasks.md` exists.
2. Run `scripts/worker_orchestrator.py <issue> --write`.
3. Review `specs/<issue>/worker-plan.md`.
4. Use parallel workers only when the plan is `parallel-eligible`.
5. Keep shared-state, migration, schema, and config work sequential unless explicitly approved.

## Output

- `specs/<issue>/worker-plan.json`
- `specs/<issue>/worker-plan.md`

## Next

- `/product:execute <issue>` when the worker plan is accepted.
- `/product:plan <issue>` if the tasks need to be split more clearly.
