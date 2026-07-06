# Issue 039: Automated Review Checklists And Safety Lint Gates

**Status: done** — implemented in commit 4e1c74b; all workflow tasks checked, status.md records 133 tests passing. Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

Enhance the `product:review` status output with automated spec-diff checklist comparisons and add code linting and security vulnerability gates to the release checker.

## Source

- Type: user feedback / product direction
- Link: conversation, 2026-06-27
- Date: 2026-06-27

## Lifecycle

- Phase: roadmap
- Created: 2026-06-27
- Started:
- Target End:
- Completed:
- Last Updated: 2026-06-27

## Opportunity

Reviewing code changes against specifications is manually intensive. ModuFlow should assist human review by automatically checking changes against the spec criteria and printing a checklist report.
Additionally, to ensure diligence, `release_check.py` needs to block release check validation if styling (lint) or security rules (credentials leakage, unsafe APIs) are violated.

## Scope

### In

- Update the review loop (`product:review`) to compare code diffs against spec acceptance criteria, outputting findings directly into the issue's `status.md`.
- Extend `scripts/release_check.py` to run code linter (e.g. `flake8` or `black`) and simple security/credentials check.
- Block the release check output if code style or security checks fail.

### Out

- Creating redundant new review files (re-use existing `status.md` instead).

## Acceptance Criteria

- `product:review` runs spec-to-diff analysis and updates the issue's `status.md` with checklist findings.
- `release_check.py` runs linting checks and security checks.
- `release_check.py` fails if critical code style or security violations are present.
- Unit tests verify new validation and review routines.

## Workflow Tasks

- [x] spec -> define criteria comparison rules
- [x] plan -> implementation plan for review and safety gates
- [x] execute -> code review and release check extensions
- [x] review -> validation and tests
- [x] release -> release checks

## Related Issues

- follows_up: `038-worker-context-memory-path-injection`

## Sessions

- 2026-06-27: User requested setting up downstream issues for the remaining phases.

## Links

- Status: `specs/039-automated-review-checklists-and-safety-lint-gates/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
