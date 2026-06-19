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
- Updated `release_check.py` so package validation and project artifact validation use importable functions instead of shelling out.
- Split `project_doctor.inspect_project()` into default full preflight and local-only `include_preflight=False` mode.
- Added `scripts/project_doctor.py --no-preflight` for approval-sensitive local validation.

## Verification

- `python3 -m unittest tests.test_validation_distribution.ValidationDistributionTests.test_validate_moduflow_exposes_importable_api tests.test_validation_distribution.ValidationDistributionTests.test_validate_moduflow_importable_api_reports_missing_files -v` passed.
- `python3 -m unittest tests.test_validation_distribution.ValidationDistributionTests.test_release_check_uses_importable_validation_for_safe_checks -v` passed.
- `python3 -m unittest tests.test_validation_distribution.ValidationDistributionTests.test_project_doctor_can_skip_git_and_github_preflight tests.test_validation_distribution.ValidationDistributionTests.test_project_doctor_preflight_enabled_by_default -v` passed.
- `python3 scripts/project_doctor.py . --no-preflight` passed.
- `python3 -m unittest tests.test_validation_distribution.ValidationDistributionTests.test_project_doctor_can_skip_git_and_github_preflight tests.test_validation_distribution.ValidationDistributionTests.test_project_doctor_preflight_enabled_by_default tests.test_validation_distribution.ValidationDistributionTests.test_project_doctor_local_only_detects_project_root_from_subdirectory -v` passed.
- `python3 scripts/project_doctor.py workspace --no-preflight` passed.
- `python3 -m unittest tests.test_validation_distribution -v` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Blockers

- Antigravity host API details need verification before host-specific adapter implementation.

## Next Command

`/product:execute 027-reduce-approval-popup-friction`
