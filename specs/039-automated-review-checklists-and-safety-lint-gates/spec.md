# Spec: Automated Review Checklists And Safety Lint Gates

## Issue

`039-automated-review-checklists-and-safety-lint-gates`

## Source Request

Reviewing code changes against specifications is manually intensive. ModuFlow should assist human review by automatically checking changes against the spec criteria and printing a checklist report.
Additionally, code style violations and credentials leakage must block final releases.

## Goals

- Extend `product:review` status output to automatically compare code diffs against spec acceptance criteria, outputting checklist findings directly into the issue's `status.md`.
- Extend `scripts/release_check.py` to run basic credentials scanning and code style sanity checks.
- Fail the release check (exit code 1) if critical style or security violations are present.

## Non-Goals

- Deprecating existing human code review. The automated checklist acts as a helper, not a replacement.
- Installing heavy external enterprise static-analysis backends.

## Proposed Changes & User Flows

### 1. Spec-to-Diff Review Engine
When `product:review` is run:
1. It reads the current issue's `spec.md` file and extracts the "Acceptance Criteria" lines.
2. It generates the git diff of changes made in the issue branch against `main` (or unstaged changes if no branch).
3. It maps each acceptance criterion to the diff and generates a status summary:
   - `[x] implemented`: implemented changes found in diff.
   - `[ ] pending/missing`: no evidence in diff.
4. It updates the `status.md` file under a new section `## Automated Review Checklist`.

### 2. Linting & Credentials Scan Gates
In `scripts/release_check.py`, we will add two new validation checks:
1. **Lint Check**: A sanity scanner that parses modified python files for basic syntax correctness, import order, or generic style violations.
2. **Security Gate**: Searches all repository files for potential hardcoded credentials (e.g. matching `API_KEY`, `secret_token`, `password = "..."` patterns).
3. If violations are found, `release_check.py` prints warning logs and exits with return code `1` (blocking final publication).

## Acceptance Criteria

- Running `product:review` generates the checklist inside `status.md`.
- `release_check.py` fails if a simulated secret or credential leak pattern is inserted in any repo file.
- Unit tests verify comparison engine and gate logic.
