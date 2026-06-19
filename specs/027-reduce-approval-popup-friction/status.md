# Status: Reduce Approval Popup Friction

## Issue

`027-reduce-approval-popup-friction`

## Phase

plan

## Summary

Created the spec and plan for reducing approval popup fatigue. The work focuses on distinguishing safe local validation from risky shell/Git/network/account/destructive operations, while preserving existing CLI scripts for compatibility.

## Completed

- Created `specs/027-reduce-approval-popup-friction/spec.md`.
- Created `specs/027-reduce-approval-popup-friction/plan.md`.
- Captured Antigravity feedback around shell-based validation prompts.
- Defined initial approval classes and importable validation engine direction.
- Created `specs/027-reduce-approval-popup-friction/approval-surface.md` mapping validation scripts, project mutation scripts, and Git/GitHub approval classes.
- Added `validate_moduflow(root)` as an importable package validation API while preserving CLI output compatibility.

## Verification

- `python3 -m unittest tests.test_validation_distribution.ValidationDistributionTests.test_validate_moduflow_exposes_importable_api tests.test_validation_distribution.ValidationDistributionTests.test_validate_moduflow_importable_api_reports_missing_files -v` passed.
- `python3 scripts/validate_moduflow.py .` passed.

## Blockers

- Antigravity host API details need verification before host-specific adapter implementation.

## Next Command

`/product:execute 027-reduce-approval-popup-friction`
