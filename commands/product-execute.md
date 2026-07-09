---
description: Execute approved plan using Superpowers-style workers.
argument-hint: "<issue id>"
---

# /product:execute

Run implementation from an approved plan.

## Do

1. Verify issue, spec, plan, and tasks exist.
   - Soft pre-check: run `python3 scripts/spec_consistency.py . --issue-id <id>` and report the findings. Proceed on warn/info findings; stop and fix on structure errors unless the user says otherwise — this is agent judgment, not a hard gate.
2. Run implementation-readiness before worker dispatch:

```bash
python3 scripts/project_execution.py . --issue-id <id> --readiness --write
```

   - `ready`: proceed.
   - `warning`: proceed only after reporting concrete gaps and risk.
   - `not_ready`: recommend `product:plan <id>` and ask for explicit user approval before continuing. This is report-only in v1, not an automatic hard block.
3. Run `scripts/worker_orchestrator.py <issue> --write` if `specs/<issue>/worker-plan.md` is missing.
4. Use Superpowers process: plan, TDD when applicable, workers for independent tasks, review, verification.
5. Update `specs/<issue>/status.md` as work progresses.
6. Keep Git branch and commits tied to issue ID.
7. Recommend and record an execution backend before starting substantial implementation.
8. Before entering review, ensure early PR state exists: when GitHub sync is available and the workflow/user has allowed GitHub writes, open a Draft PR after the first meaningful commit. If GitHub writes are unavailable, record a local PR-ready marker through `product:pr` instead of waiting until review is finished.
9. At implementation completion, generate the review handoff before asking the user what to do next:

```bash
python3 scripts/project_execution.py <project-path> --issue-id <issue id> --review-handoff --write
```

This writes `specs/<issue>/review-handoff.md`, including implementation-worker, review-worker, verification, and dashboard plus issue drill-down handoff instructions.

10. Continue directly into `product:review <issue id>` unless a blocker, failing test, dirty Git conflict, missing artifact, or explicit user stop prevents review. Do not ask the user whether to review after implementation; review is part of the implementation completion contract.

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

## Model Tier Policy

The main-loop model (the most capable/expensive tier the user is running) is for **orchestration and judgment**, not for everything (absorbed from Superpowers v6's explicit-model-per-dispatch rule, issue `067`; adopted as a working convention 2026-07-05):

- **Main loop keeps**: scope decisions, spec/plan authorship, absorb-or-skip judgments, final synthesis and verification of subagent output, user communication, git commit/push.
- **Dispatch to subagents** (explicitly on a cheaper tier when the host allows model selection): upstream/external research sweeps, codebase exploration, mechanical implementation streams from an approved plan, and independent review/verification passes (QA, spec-compliance).
- Every dispatch states its model tier explicitly when the host supports it — an unnamed dispatch silently inherits the most expensive tier, which wastes exactly the capacity the main loop should be reserving for judgment.
- Verification stays independent: the subagent that implemented a task is never the one that verifies it.

## Next

- `/product:review` immediately after implementation handoff exists
- `/product:pr` early for Draft PR / PR-ready state, then refresh after review passes
