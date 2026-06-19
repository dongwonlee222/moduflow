# Release: Worker Routing And Isolation

## Issue

`023-worker-routing-and-isolation`

## Date

2026-06-19

## Changes

- Worker plans now parse inline task metadata for expected files, globs, dependencies, and shared-state flags.
- Ambiguous acceptance verification routes to QA, while explicit PM acceptance criteria still route to PM.
- Parallel eligibility now requires disjoint expected files and no shared-state risk.
- Worker plans include per-task isolation worktree names and merge order.
- Worker inventory reports unrouted worker files.

## User Impact

`product:workers <issue>` is safer: it recommends parallel work only when the split is file/dependency-safe, and otherwise falls back to sequential execution with a clear risk explanation.

## Verification

- `python3 -m unittest tests.test_worker_orchestration -v` passed (7 tests).
- `python3 -m unittest discover -s tests -v` passed (61 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Rollback

Revert `scripts/worker_orchestrator.py`, `tests/test_worker_orchestration.py`, and the 023 documentation updates.

## Next Command

`product:status`
