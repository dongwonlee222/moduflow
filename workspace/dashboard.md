# ModuFlow Dashboard

## Current Phase

Post-merge UX cleanup: Issue 026 is complete; Issue 027 is planned and ready for execution.

## Active Goal

- `lightweight-moduflow-ux`: make ModuFlow feel lightweight and predictable in real projects while preserving Git-native PM artifacts and the central plugin/tooling model.

## Active Issue

- `027-reduce-approval-popup-friction`: reduce approval fatigue by making prompts predictable and moving routine validation toward importable/tool-call paths.

## Recently Completed

- `026-simplify-command-and-folder-surface`: completed lightweight project footprint, plugin cache packaging, user-facing mode guidance, and goal-loop completion handoff.
- `025-lightweight-project-adoption`: project doctor can now detect dogfooding, heavy, and lightweight layouts; remaining start/migrate write behavior is tracked separately.
- `0.2.11-goal-loop`: merged to `main` and pushed to GitHub.
- `024-artifact-schema-and-doctor-gates`: active-loop linked artifact, dashboard, roadmap, and `next_command` validation.
- `023-worker-routing-and-isolation`: deterministic worker routing, file-aware parallel safety, merge order, and dead-worker detection.

## Queue

- `028-real-subagent-execution-backend`
- `029-antigravity-artifact-sync-connector`

## Blockers

- None.

## Verification

- ModuFlow plugin version: `0.2.11+codex.20260619033058`.
- `python3 -m unittest tests.test_validation_distribution -v` passed (16 tests).
- `python3 -m unittest discover -s tests -v` passed (68 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Next Command

`product:execute 027-reduce-approval-popup-friction`
