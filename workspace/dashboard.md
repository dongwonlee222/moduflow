# ModuFlow Dashboard

## Current Phase

Post-merge UX cleanup: Issue 026 implementation is ready for review; new Antigravity feedback expanded the approval, real-subagent, and artifact-sync backlog.

## Active Goal

- `lightweight-moduflow-ux`: make ModuFlow feel lightweight and predictable in real projects while preserving Git-native PM artifacts and the central plugin/tooling model.

## Active Issue

- `026-simplify-command-and-folder-surface`: ready for review after simplifying default project footprint, plugin cache packaging, and user-facing mode guidance.

## Recently Completed

- `025-lightweight-project-adoption`: project doctor can now detect dogfooding, heavy, and lightweight layouts; remaining start/migrate write behavior is tracked separately.
- `0.2.11-goal-loop`: merged to `main` and pushed to GitHub.
- `024-artifact-schema-and-doctor-gates`: active-loop linked artifact, dashboard, roadmap, and `next_command` validation.
- `023-worker-routing-and-isolation`: deterministic worker routing, file-aware parallel safety, merge order, and dead-worker detection.

## Queue

- `027-reduce-approval-popup-friction`
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

`product:review 026-simplify-command-and-folder-surface`
