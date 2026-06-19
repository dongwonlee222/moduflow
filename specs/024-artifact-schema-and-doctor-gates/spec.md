# Spec: Artifact Schema And Doctor Gates

## Issue

`024-artifact-schema-and-doctor-gates`

## Source Request

Dongwon Lee asked to continue the final core ModuFlow issue after worker routing and isolation.

## Owner

Dongwon Lee

## Phase

execute

## Problem

ModuFlow validation currently catches required files and some loop-state errors, but it does not consistently catch broken relationships between active issues, linked artifacts, dashboard state, roadmap state, and next commands.

## Goals

- Validate active issue artifact links.
- Validate active issue and next command drift across loop-state, dashboard, and roadmap.
- Validate whether `next_command` matches the inferred active issue phase.
- Surface schema gate findings through `product:doctor`.
- Keep release_check wired to the strengthened validation path.

## Non-Goals

- Auto-fixing every finding.
- Remote GitHub writes.
- Requiring every backlog issue to have complete specs before it is active.

## Design

`scripts/validate_project_artifacts.py` remains the main schema gate. The new checks are active-loop scoped: they validate the active issue and active views instead of forcing every backlog issue to be complete. `scripts/project_doctor.py` surfaces the same schema gate result and adds a repair recommendation when errors are present.

## Acceptance Criteria

- Missing active issue linked spec/status/plan artifacts are reported.
- Dashboard active issue drift is reported.
- Invalid `next_command` for the inferred phase is reported.
- Doctor output includes `schema_gates` and an actionable recommendation.
- Release check keeps using `validate_project_artifacts.py`.

## Next Command

`product:plan 024-artifact-schema-and-doctor-gates`
