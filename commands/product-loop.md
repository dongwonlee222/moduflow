---
description: Read goal and issue state, then recommend or run the next safe ModuFlow step.
argument-hint: "[--step|--until blocked]"
---

# /product:loop

Advance a goal by routing through existing ModuFlow commands.

## Do

1. Read `workspace/goal.md` and `workspace/loop-state.json` when present.
2. Inspect the linked issue, spec, plan, tasks, status, release, and update artifacts.
3. Recommend the next existing ModuFlow command.
4. Write state only when the user asks for mutation or when running `--step`.
5. Stop as soon as the goal is `done`, `blocked`, or `needs_decision`.

## Recommendation Mode

Default `product:loop` is read-first and recommendation-oriented.

Expected output:

```text
Current goal: <goal>
Linked issue: <issue>
Observed state: <artifact summary>
Recommended next command: <product command>
Reason: <short reason>
```

## One-Step Mode

`product:loop --step` may run at most one safe next action and then stop.

Safe one-step actions include:

- creating or updating goal, issue, spec, plan, tasks, status, reflection, dashboard, issue index, and roadmap artifacts
- running local validation commands
- recommending review, release, PR, or update commands

Unsafe actions require explicit user approval:

- package publishing
- GitHub writes
- cross-repo mutation
- destructive file or Git operations
- long-running unattended execution

## Stop States

- `done`: completion criteria are satisfied and verification is recorded
- `blocked`: the next action cannot proceed without external change
- `needs_decision`: a human decision is required before mutation
- `active`: safe to continue with the recommended next command

## State Updates

When mutating, update `workspace/loop-state.json` with:

- current goal
- linked issue
- phase
- mode
- next command
- attempts
- status
- blocker
- last action
- last verification
- updated timestamp

Record repeated failures or uncertainty in `specs/<issue>/reflection.md`.

## Next

- `/product:status` to inspect the current state
- `/product:review` after implementation steps complete
