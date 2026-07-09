---
name: superpowers-execution-bridge
description: Use when ModuFlow executes plans, splits independent work into workers, requests review, verifies completion, or decides whether parallel subagents are appropriate.
---

# Superpowers Execution Bridge

Use Superpowers as the execution discipline.

## Sequence

1. Brainstorm and clarify when intent is still blurry.
2. Write a plan before non-trivial implementation.
3. Use TDD where behavior changes.
4. Generate a ModuFlow worker plan for non-trivial issue execution.
5. Dispatch parallel workers only for independent tasks.
6. Request review after implementation.
7. Verify before completion.

## Recommended Discipline Catalog

When `product:plan` creates a plan, include a visible `Recommended Discipline`
matrix that names the discipline or adapter each stream should use and why.
Keep recommendations selective: name only the disciplines that match the issue's
files, artifacts, risk, or evidence needs.

- **writing-plans**: multi-step implementation, cross-file changes, worker handoff, or work that needs clear interfaces before execution.
- **TDD**: behavior changes, bug fixes, routing logic, parsers, validators, command behavior, or release gates.
- **product-design**: UX flows, screen decisions, IA, prototypes, visual review, screenshot-to-code, or image-to-code work.
- **data-analysis**: KPI design, metric diagnostics, dashboard/report work, market sizing, or evidence-backed product decisions.
- **Storybook/MSW**: frontend component states, API fixture contracts, mocked edge cases, or repeatable UI QA.
- **Playwright/QA**: browser-visible workflows, smoke tests, regression paths, or release evidence.
- **review**: non-trivial implementation, behavior-affecting docs, commands, templates, or any work that changes product-facing behavior.
- **verification-before-completion**: every completion claim, PR handoff, release, or done-state transition.

These are recommendations, not readiness gates. Issue 077 owns any future
implementation-readiness blocking behavior.

## Implementation Readiness Handoff

Before `product:execute` dispatches workers, run the ModuFlow implementation
readiness check. It turns the planning discipline into a concrete execution
handoff:

- API contract mapping
- test strategy
- Storybook required states when frontend UI is in scope
- MSW fixture baseline when API-backed UI is in scope
- Playwright smoke matrix when browser-visible flows are in scope
- permission/role model when access control is in scope
- release/rollback verification

The v1 gate is report-only. `not_ready` should route back to `product:plan`
unless the user explicitly approves continuing with the recorded risk.

When tuning recommendations, use data-backed examples: collect representative
requests/issues, encode executable cases as regression tests when the logic
becomes code, then update the guidance.

## Parallel Criteria

Parallel work is allowed when tasks have:

- separate files or domains
- independent acceptance checks
- low shared state risk
- clear merge order
- `specs/<issue>/worker-plan.md` marks the issue `parallel-eligible`

Parallel work is avoided for:

- same-file edits
- ordered migrations
- unresolved product decisions
- shared design system changes

## Model Self-Selection for Subagents

When dispatching a subagent, read its `CognitiveDemand` field and choose the
best currently available model on your platform yourself. Do NOT hardcode model
names — pick based on the demand level:

- `deep`     → Use your **most capable reasoning model**.
               Prioritize quality and depth over speed.
               (e.g., the highest-tier model available to you right now)
- `balanced` → Use your **standard production model**.
               Optimize for the best quality-speed tradeoff.
               (e.g., your default mid-tier model)
- `fast`     → Use your **lightest, fastest model**.
               Speed and cost efficiency are the priority.
               (e.g., your smallest or flash-class model)

This keeps the system version-agnostic: new model releases are automatically
used without any changes to worker files or orchestrator config.
