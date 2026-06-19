# ModuFlow Dashboard

## Current Phase

Post-merge UX cleanup: Issue 028 is in execute phase.

## Active Goal

- `lightweight-moduflow-ux`: make ModuFlow feel lightweight and predictable in real projects while preserving Git-native PM artifacts and the central plugin/tooling model.

## Active Issue

- `028-real-subagent-execution-backend`: define host-subagent execution backend adapter for Antigravity integration.

## Recently Completed

- `027-reduce-approval-popup-friction`: completed approval surface mapping, importable validation paths, local-only doctor mode, host adapter guidance, and resume banner contract.
- `026-simplify-command-and-folder-surface`: completed lightweight project footprint, plugin cache packaging, user-facing mode guidance, and goal-loop completion handoff.
- `025-lightweight-project-adoption`: project doctor can now detect dogfooding, heavy, and lightweight layouts; remaining start/migrate write behavior is tracked separately.
- `0.2.11-goal-loop`: merged to `main` and pushed to GitHub.
- `024-artifact-schema-and-doctor-gates`: active-loop linked artifact, dashboard, roadmap, and `next_command` validation.
- `023-worker-routing-and-isolation`: deterministic worker routing, file-aware parallel safety, merge order, and dead-worker detection.

## Queue

- `029-antigravity-artifact-sync-connector`

## Blockers

- None.

## Verification

- ModuFlow plugin version: `0.2.11+codex.20260619033058`.
- `python3 -m unittest tests.test_validation_distribution -v` passed (23 tests).
- `python3 -m unittest discover -s tests -v` passed (68 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Next Command

`product:execute 028-real-subagent-execution-backend`
