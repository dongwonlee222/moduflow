# Spec: Worker Routing And Isolation

## Issue

`023-worker-routing-and-isolation`

## Source Request

Dongwon Lee asked to continue the next ModuFlow issue after 022, making worker execution safer before the final schema/doctor gate issue.

## Owner

Dongwon Lee

## Phase

release

## Problem

Worker plans were based mainly on keyword routing and worker-domain count. That made ambiguous tasks such as acceptance verification route unpredictably, and it allowed parallel recommendations even when tasks expected to touch the same file or shared state.

## Goals

- Route tasks to workers deterministically, including ambiguous acceptance-related tasks.
- Parse task metadata for expected files, globs, dependencies, and explicit shared-state risk.
- Mark parallel execution unsafe when expected files overlap or shared state is involved.
- Include per-task worktree isolation and dependency-aware merge order in worker plans.
- Report worker files that have no routing rule so dead workers are visible.

## Non-Goals

- Fully autonomous worker dispatch.
- Cross-repo worker execution.
- GitHub issue, PR, or release synchronization.

## Design

`scripts/worker_orchestrator.py` remains the single worker planning engine. It reads checkbox tasks from `specs/<issue>/tasks.md` and supports inline task metadata:

```text
[files: path/a.py, path/b.md] [globs: docs/*.md] [depends: T02] [shared_state: true]
```

The planner strips metadata from task text, assigns a worker, calculates shared-state and file-overlap risks, then emits `worker-plan.json` and `worker-plan.md`. Parallel execution is eligible only when there are at least two worker domains and no risk. Unsafe plans explicitly fall back to sequential mode.

## Acceptance Criteria

- `acceptance verification` routes to `qa-reviewer`, while explicit `PM:` tasks still route to `pm-strategist`.
- Duplicate expected files force sequential mode.
- Plans include `expected_files`, `expected_globs`, `dependencies`, `isolation.worktree`, and `parallel.merge_order`.
- Worker inventory reports worker markdown files that are not covered by routing rules.
- ~~Existing worker plan output remains backward-compatible with schema
  `moduflow.worker-plan.v1`.~~ **Superseded 2026-09-06 by issue 112.** That
  issue changed the plan's shape on purpose — `isolation` became a host-adapter
  record, `deferred_to` was dropped because Gate 1 filters those lines, and
  host/backend/routing_reason/gaps/divergences were added — so the output is
  now `moduflow.worker-plan.v2`. This criterion was written assuming the shape
  would hold; it did not. Recorded here rather than left as two specs
  disagreeing in silence. The eleven committed v1 files are untouched and are
  distinguishable by their version, which is the point of the bump.

## Verification

- `python3 -m unittest tests.test_worker_orchestration -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`

## Next Command

`product:status`
