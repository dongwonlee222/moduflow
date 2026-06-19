# ModuFlow Dashboard

## Current Phase

Post-merge UX cleanup: new issues opened for lightweight project adoption, simpler folder/command surface, and lower approval-popup friction.

## Active Goal

- `lightweight-moduflow-ux`: make ModuFlow feel lightweight and predictable in real projects while preserving Git-native PM artifacts and the central plugin/tooling model.

## Active Issue

- `025-lightweight-project-adoption`: define light mode so target projects keep only state and PM artifacts, not ModuFlow tooling folders.

## Recently Completed

- `0.2.11-goal-loop`: merged to `main` and pushed to GitHub.
- `024-artifact-schema-and-doctor-gates`: active-loop linked artifact, dashboard, roadmap, and `next_command` validation.
- `023-worker-routing-and-isolation`: deterministic worker routing, file-aware parallel safety, merge order, and dead-worker detection.

## Queue

- `026-simplify-command-and-folder-surface`
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

`product:review 025-lightweight-project-adoption`
