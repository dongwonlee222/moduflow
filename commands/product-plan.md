---
description: Create execution plan and task list for a spec.
argument-hint: "<issue id>"
---

# /product:plan

Prepare implementation.

## Do

1. Create or update `specs/<issue>/plan.md`.
2. Create or update `specs/<issue>/tasks.md`.
3. Split tasks by independent work streams for possible parallel workers.
4. Define test, review, deploy, and rollback gates.

## Next

- `/product:execute` when ready to build
- `/product:review` if the plan needs challenge

