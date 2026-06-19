# ModuFlow Dashboard

## Current Phase

Core goal loop complete: issues 019 through 024 are released locally.

## Active Goal

- `goal-loop-orchestrator`: make ModuFlow a plugin-installed PM loop orchestrator that connects goal, issues, specs, tasks, workers, and Git progress while keeping the user surface simple.

## Active Issue

- `024-artifact-schema-and-doctor-gates`: completed artifact schema gates and doctor drift checks.

## Recently Completed

- `024-artifact-schema-and-doctor-gates`: active-loop linked artifact, dashboard, roadmap, and `next_command` validation.
- `023-worker-routing-and-isolation`: deterministic worker routing, file-aware parallel safety, merge order, and dead-worker detection.

## Queue

- None in the current core goal.

## Blockers

- None.

## Verification

- ModuFlow plugin version: `0.2.11+codex.20260619033058`.
- `python3 -m unittest tests.test_validation_distribution -v` passed (13 tests).
- `python3 -m unittest discover -s tests -v` passed (65 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Next Command

`product:status`
