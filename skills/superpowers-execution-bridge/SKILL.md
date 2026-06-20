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
