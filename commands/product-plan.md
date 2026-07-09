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
   - **Global Constraints** block at the top (issue 073): open with the constitution reference — `Constitution v<X.Y> applies (workspace/constitution.md). Plan-specific additions:` — then author ONLY the additions this issue needs. Never restate constitution principles; a per-issue *tightening* of a principle is an addition, not an amendment (no constitution log entry needed). Additions remain binding rules every task must honor verbatim, so per-task workers can't drift from them.
   - **Recommended Discipline** block (issue 079): include a visible matrix that names the Superpowers disciplines and ModuFlow adapter skills recommended for each stream or task. Use columns `Stream`, `Discipline / Adapter`, and `Reason`.
   - Per-task **Interfaces** notes where tasks hand data to each other: what each task consumes and produces, so parallel workers agree on contracts before building.
   - Right-size tasks: one reviewable outcome each — split a task whose diff a reviewer couldn't judge in one sitting; merge tasks too small to verify independently.

Recommended Discipline example:

```markdown
## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — behavior change | Superpowers TDD + focused tests | Routing, parser, command, or validator behavior must prove RED/GREEN. |
| B — UX flow | product-design + review | User-facing workflows need design rationale and review evidence. |
| C — verification | verification-before-completion | Completion claims need fresh evidence. |
```

The matrix is guidance, not an execution gate. Do not block `product:execute` from this section alone; issue 077 owns implementation-readiness gates.

## Implementation Readiness Inputs

Before recommending `/product:execute`, plans should state the applicable
contracts that issue 077 checks:

- API contract mapping, or explicit `not applicable`.
- Test strategy and what each test proves.
- Storybook required states when frontend UI is in scope.
- MSW fixture baseline when API-backed UI is in scope.
- Playwright smoke matrix when browser-visible user flows are in scope.
- Permission/role model when access control is in scope.
- Release/rollback verification condition.

Do not paste the full frontend QA template pack here; issue 078 owns reusable
template details. The plan only needs enough evidence for the readiness check
to route correctly.

## Next

- Recommended: `python3 scripts/spec_consistency.py . --issue-id <id>` once plan.md and tasks.md exist, to catch coverage gaps, vague terms, and stream mismatches before execution.
- `/product:execute` when ready to build
- `/product:review` if the plan needs challenge
