# ModuFlow Dashboard

## Current Phase

Post-merge UX cleanup: Issue 025 is in review, and Issue 026 is now planned to simplify the visible command/folder surface.

## Active Goal

- `lightweight-moduflow-ux`: make ModuFlow feel lightweight and predictable in real projects while preserving Git-native PM artifacts and the central plugin/tooling model.

## Active Issue

- `026-simplify-command-and-folder-surface`: make the first user experience smaller by grouping folders, reducing default commands, and translating internal mode labels into plain guidance.

## Recently Completed

- `025-lightweight-project-adoption`: project doctor can now detect dogfooding, heavy, and lightweight layouts; remaining start/migrate write behavior is tracked separately.
- `0.2.11-goal-loop`: merged to `main` and pushed to GitHub.
- `024-artifact-schema-and-doctor-gates`: active-loop linked artifact, dashboard, roadmap, and `next_command` validation.
- `023-worker-routing-and-isolation`: deterministic worker routing, file-aware parallel safety, merge order, and dead-worker detection.

## Queue

- `027-reduce-approval-popup-friction`

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

`product:execute 026-simplify-command-and-folder-surface`
