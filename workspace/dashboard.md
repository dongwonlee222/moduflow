# ModuFlow Dashboard

## Current Phase

Core goal loop complete: issues 025 through 029 are released locally.

## Active Goal

- `lightweight-moduflow-ux`: make ModuFlow feel lightweight and predictable in real projects while preserving Git-native PM artifacts and the central plugin/tooling model.

## Active Issue

- `031-goal-driven-autonomous-benchmarking-and-issue-generation`

## Recently Completed

- `029-antigravity-artifact-sync-connector`: completed sync connector script, bidirectional task merging, and drift checks.
- `028-real-subagent-execution-backend`: completed host-subagent execution backend adapter for Antigravity integration.
- `027-reduce-approval-popup-friction`: completed approval surface mapping, importable validation paths, local-only doctor mode, host adapter guidance, and resume banner contract.
- `026-simplify-command-and-folder-surface`: completed lightweight project footprint, plugin cache packaging, user-facing mode guidance, and goal-loop completion handoff.
- `025-lightweight-project-adoption`: project doctor can now detect dogfooding, heavy, and lightweight layouts; remaining start/migrate write behavior is tracked separately.
- `0.2.11-goal-loop`: merged to `main` and pushed to GitHub.

## Queue

- None.

## Blockers

- None.

## Verification

- ModuFlow plugin version: `0.2.11+codex.20260619033058`.
- `python3 -m unittest tests.test_validation_distribution -v` passed (23 tests).
- `python3 -m unittest discover -s tests -v` passed (80 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Next Command

`product:status`
