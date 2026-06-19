# Status: Artifact Schema And Doctor Gates

## Issue

`024-artifact-schema-and-doctor-gates`

## Phase

release

## Summary

Active-loop schema gates now validate linked artifacts, dashboard/roadmap drift, and phase-aware `next_command` consistency. Project doctor surfaces the same schema gate findings with a repair recommendation.

## Completed

- Added active issue linked artifact validation.
- Added dashboard and roadmap active issue drift checks.
- Added phase-aware `next_command` validation.
- Added project doctor `schema_gates` output and recommendation.
- Kept release_check wired through `validate_project_artifacts.py`.

## Verification

- `python3 -m unittest tests.test_validation_distribution -v` passed (13 tests).
- `python3 -m unittest discover -s tests -v` passed (65 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Blockers

- None.

## Next Command

`product:status`
