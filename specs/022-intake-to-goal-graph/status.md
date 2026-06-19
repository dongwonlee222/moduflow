# Status 022: Intake To Goal Graph

## State

- Phase: released
- Owner: Dongwon Lee
- Updated: 2026-06-18
- Blockers: none

## Shipped

- `scripts/project_intake.py` routes loose requests into active issue attachments, new issue candidates, or goal-linked issue graphs.
- `tests/test_project_intake.py` covers classification, duplicate/related detection, active issue attach, large request splitting, and inbox write mode.
- Command and skill docs now describe the deterministic `이거 해줘` routing behavior.

## Verification

- Focused intake tests passed.
- Full repository tests and validation gates are recorded in `specs/022-intake-to-goal-graph/release.md`.

## Next

`product:spec 023-worker-routing-and-isolation`
