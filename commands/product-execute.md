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
6. Recommend and record an execution backend before starting substantial implementation.

## Execution Backend

`product:execute` should act as an orchestrator, not always as the executor. Before implementation, recommend one backend and record the choice in `workspace/loop-state.json` under `git_binding.execution_backend`.

Default backend rules:

- high-risk work -> `manual`
- docs, spec, and planning work -> `codex`
- code work with GitHub available -> `copilot-cloud-agent` may be recommended
- code work with host subagents available -> `host-subagent`
- code work without GitHub available -> `codex`

Remote backends require explicit user approval before starting GitHub writes, cloud agent runs, or cross-repo mutation.

## Parallel Workers

Use parallel workers only when `specs/<issue>/worker-plan.md` marks the issue `parallel-eligible`. The worker plan must show non-overlapping expected files, no shared-state risk, and a merge order. If the plan falls back to `sequential`, execute tasks in the listed merge order.

## Subagent Dispatch (host-subagent)

When using `host-subagent` backend, `product:execute` will generate a subagent configuration card for each ready task:

```text
╭─ 🚀 ModuFlow Subagent Dispatch ────────────────────────╮
│ Task: T01 (implementation-worker)                       │
│ Type: self                                              │
│ Cognitive Demand: balanced                              │
│   → Use your standard production model for this task.  │
│ Workspace: share                                        │
│ Command: Please call invoke_subagent for T01            │
╰────────────────────────────────────────────────────────╯
```
The host agent should invoke the subagent tool using the parameters listed in the task's `subagent` config block in `worker-plan.json`.
The `CognitiveDemand` field is a hint — the host agent selects the actual model itself based on what is currently available on its platform.

## Next

- `/product:review` after implementation
- `/product:pr` after review passes
