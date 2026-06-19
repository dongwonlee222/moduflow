# Release: Artifact Schema And Doctor Gates

## Issue

`024-artifact-schema-and-doctor-gates`

## Date

2026-06-19

## Changes

- Added active-loop schema gates to `validate_project_artifacts.py`.
- Added active issue linked artifact checks for spec/status/plan references.
- Added dashboard, roadmap, and `next_command` drift checks.
- Added `schema_gates` output and actionable schema-gate recommendation to `project_doctor.py`.

## User Impact

`product:doctor`, release checks, and project validation now catch stale or inconsistent ModuFlow state before release instead of only checking whether files exist.

## Verification

- `python3 -m unittest tests.test_validation_distribution -v` passed (13 tests).
- `python3 -m unittest discover -s tests -v` passed (65 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Rollback

Revert `scripts/validate_project_artifacts.py`, `scripts/project_doctor.py`, `tests/test_validation_distribution.py`, and 024 artifacts.

## Next Command

`product:status`
