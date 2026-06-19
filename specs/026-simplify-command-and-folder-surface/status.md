# Status: Simplify Command And Folder Surface

## Issue

`026-simplify-command-and-folder-surface`

## Phase

complete

## Summary

Created the spec and execution plan for simplifying ModuFlow's first user experience. Before implementation, benchmarked GitHub, CLI/developer-tool, and plugin/agent ecosystems to confirm the design rule: ModuFlow tooling should remain central, while target projects keep only PM artifacts, project state, and intentionally selected integration files.

## Completed

- Created `specs/026-simplify-command-and-folder-surface/spec.md`.
- Created `specs/026-simplify-command-and-folder-surface/plan.md`.
- Created `specs/026-simplify-command-and-folder-surface/benchmark.md`.
- Defined the compact command set and 18-folder grouping.
- Defined user-facing copy for `lightweight`, `dogfooding`, and `heavy`.
- Confirmed benchmark evidence from GitHub Actions, GitHub Apps, ESLint, Prettier, Husky, create-next-app, Terraform, VS Code extensions, and agent/plugin ecosystems.
- Updated Codex cache installation so source-repo planning and verification artifacts (`issues/`, `specs/`, `tests/`, `sessions/`) are excluded from runtime plugin cache bundles.
- Updated project migration so normal target projects get only the minimal PM structure and do not receive tool/runtime folders.
- Updated README and `/product:start` guidance with the default target-project footprint and opt-in integration surfaces.
- Added doctor mode guidance so raw `lightweight`, `dogfooding`, and `heavy` values stay in JSON while user-facing output shows plain Korean guidance.
- Clarified that every completed ModuFlow action must include a structured Korean-first handoff based on the active goal/loop state: next work, reason, concrete next actions, follow-on priority, and exact command when useful.
- Created `specs/026-simplify-command-and-folder-surface/review.md` and approved the issue for completion.

## Verification

- `python3 -m unittest tests.test_codex_personal_install -v` passed.
- `python3 -m unittest tests.test_project_migration -v` passed.
- `python3 -m unittest tests.test_validation_distribution.ValidationDistributionTests.test_project_doctor_keeps_raw_mode_and_adds_user_guidance -v` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Blockers

- None.

## Next Command

`/product:spec 027-reduce-approval-popup-friction`
