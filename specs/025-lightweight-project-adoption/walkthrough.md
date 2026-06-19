# Walkthrough: Lightweight Project Adoption

## Summary

Issue 025 is the first cleanup slice for making ModuFlow feel lighter in real target projects. The current implementation does not move folders yet; it makes the system able to recognize and report the project layout mode.

## What Changed

- Added project mode detection in `scripts/project_doctor.py`.
- Added `dogfooding`, `heavy`, and `lightweight` layout labels.
- Updated `/product:doctor` documentation to show `프로젝트 모드 <lightweight|dogfooding|heavy>`.
- Added tests for the three mode-detection cases in `tests/test_validation_distribution.py`.
- Updated active goal, dashboard, roadmap, and issue state to track the lightweight UX goal.

## Mode Definitions

- `dogfooding`: the target root is the ModuFlow tool repo itself.
- `heavy`: a target project contains tool folders such as `commands`, `skills`, `scripts`, or `templates`.
- `lightweight`: a target project keeps PM artifacts and state without local tool folders.

## Verification

- `python3 -m pytest` passed with 68 tests.
- `python3 scripts/release_check.py .` passed.
- `python3 scripts/project_doctor.py .` reports this repo as `dogfooding`.

## Review Notes

This was the right slice to do first because it gives ModuFlow language and diagnostics for the problem before moving files or changing write behavior. The remaining 025 work is to make start/migrate/intake flows actually enforce lightweight writes by default.

The raw mode labels should remain primarily internal. A normal user should not have to learn `lightweight`, `dogfooding`, and `heavy`; user-facing status should translate them into direct guidance like "clean project setup", "ModuFlow tool repo", or "cleanup recommended".

## Next Command

`product:review 025-lightweight-project-adoption`
