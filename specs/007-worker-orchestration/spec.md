# Spec: Worker Orchestration

Issue: `007-worker-orchestration`

## Problem

Workers exist as role documents, and `product:execute` mentions parallel workers, but there is no repeatable artifact that decides worker ownership or records why work is parallel-safe.

## Goals

- Create a repeatable worker planning artifact per issue.
- Keep worker dispatch provider-neutral.
- Make parallel decisions explainable before implementation begins.
- Avoid parallelizing shared-state or same-file work by default.

## Non-Goals

- Running a hosted agent scheduler.
- Hiding user approval requirements.
- Replacing Codex, Superpowers, or future multi-agent tool capabilities.

## User Flow

1. User creates or selects an issue.
2. User runs `product:workers <issue-id>`.
3. ModuFlow reads `specs/<issue-id>/tasks.md`.
4. ModuFlow writes `worker-plan.json` and `worker-plan.md`.
5. `product:execute` uses the worker plan to decide sequential versus parallel execution.

## Acceptance Criteria

- Worker planning works without network access.
- Empty or missing task files fail with actionable errors.
- Generated plans include worker, task, status, risk, and parallel group data.
- Shared-state tasks are marked sequential.

## Next Command

`product:plan 007-worker-orchestration`
