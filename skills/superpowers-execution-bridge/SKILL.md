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
