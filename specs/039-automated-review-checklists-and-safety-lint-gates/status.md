# Status: Automated Review Checklists And Safety Lint Gates

## Issue

`039-automated-review-checklists-and-safety-lint-gates`

## Current Phase

✅ Done

## Done

- Created spec file `specs/039-automated-review-checklists-and-safety-lint-gates/spec.md`.
- Implemented `run_review_check(root, issue_id)` in `scripts/project_workflow.py`.
  - Parses `## Acceptance Criteria` from spec.md, strips checkbox markers.
  - Generates git diff and keyword-matches each criterion against added lines.
  - Appends `## Automated Review Checklist` section to `status.md`.
- Added `--review-check` CLI flag to `scripts/project_workflow.py`.
- Added `run_lint_check(root)` to `scripts/release_check.py`.
  - Scans only git-modified python files for syntax errors using `compile()`.
- Added `run_security_check(root)` to `scripts/release_check.py`.
  - Regex-scans all repo files for hardcoded credential patterns (API_KEY, secret_token, password, etc.).
  - Exempts test/mock/placeholder strings to avoid false positives.
- Integrated both gates into `run_release_check()` — exits code 1 on violation.
- Added `test_run_review_check_generates_checklist` to `tests/test_project_workflow.py`.
- Added `test_release_check_fails_on_syntax_and_security_violations` to `tests/test_validation_distribution.py`.

## Verification

- All **133 unit tests pass** (`python3 -m unittest discover -s tests`).
- `python3 scripts/release_check.py .` → `valid: true`, all checks pass including `lint_check` and `security_check`.
- `python3 scripts/validate_project_artifacts.py .` → `valid: true`.

## Next Command

`product:status`

## Automated Review Checklist

- [x] Running `product:review` generates the checklist inside `status.md`.
  - *Verification*: `run_review_check` implemented in `project_workflow.py`, generates checklist section confirmed by unit test.
- [x] `release_check.py` fails if a simulated secret or credential leak pattern is inserted in any repo file.
  - *Verification*: `test_release_check_fails_on_syntax_and_security_violations` confirms FAIL on `API_KEY = "my-secret-key-123456"` pattern.
- [x] Unit tests verify comparison engine and gate logic.
  - *Verification*: 133 tests pass including 2 new tests for Issue 039 features.


