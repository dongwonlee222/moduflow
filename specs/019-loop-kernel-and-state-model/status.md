# Loop Kernel And State Model Status

## Phase

Released; 020 user-facing loop UX is next.

## Completed

- Completed review gate for loop-state drift validation and attempts guard coverage.
- Released 019 and refreshed the Codex plugin cache for the updated loop kernel.
- Created issue 019 as the parent for loop attempts guard, Goal 1:N Issue, and state single-source work.
- Drafted `spec.md` with relationship model, state model, loop algorithm, user-facing behavior, risks, and acceptance criteria.
- Preserved the product direction that ModuFlow remains a plugin with simple user commands while internal complexity stays hidden.
- Updated project state, active loop state, dashboard, and roadmap pointers to 019.
- Drafted `plan.md` and `tasks.md` for loop kernel implementation.
- Implemented `scripts/project_loop.py` loop state loader, normalizer, phase inference, recommendation, write mode, and attempts guard.
- Added `tests/test_project_loop.py` coverage for v1/v2 state, phase routing, attempts guard, recommendation/write mode, and validation.
- Connected loop-state validation to `scripts/validate_project_artifacts.py` and loop health to `scripts/project_doctor.py`.
- Updated `product-loop`, `product-status`, and workspace/project state templates for loop-state v2.

## In Progress

- Released and handed off to issue 020.

## Blockers

- None.

## Follow-Ups

- Decide v1 canonical multi-goal storage path during planning.
- Coordinate Git/backend binding with issue 021 after issue 020 simplifies the user surface.

## Verification

- `python3 -m unittest tests.test_project_loop -v` passed (9 tests).
- `python3 -m unittest tests.test_validation_distribution -v` passed (9 tests).
- `python3 -m unittest discover -s tests -v` passed (46 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Next Command

`product:spec 020-user-facing-simple-loop-ux`
