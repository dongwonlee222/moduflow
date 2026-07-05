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
5. Structure the plan for handoff quality (absorbed from Superpowers v6 writing-plans, issue `067`):
   - **Global Constraints** block at the top: binding rules every task must honor verbatim (naming, dependency, compatibility constraints) — so per-task workers can't drift from them.
   - Per-task **Interfaces** notes where tasks hand data to each other: what each task consumes and produces, so parallel workers agree on contracts before building.
   - Right-size tasks: one reviewable outcome each — split a task whose diff a reviewer couldn't judge in one sitting; merge tasks too small to verify independently.

## Next

- Recommended: `python3 scripts/spec_consistency.py . --issue-id <id>` once plan.md and tasks.md exist, to catch coverage gaps, vague terms, and stream mismatches before execution.
- `/product:execute` when ready to build
- `/product:review` if the plan needs challenge

