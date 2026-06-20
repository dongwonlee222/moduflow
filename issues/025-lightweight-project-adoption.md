# Issue 025: Lightweight Project Adoption

## Summary

Reduce ModuFlow's footprint in target projects so project adoption keeps only durable state and PM artifacts in the project, while commands, scripts, skills, and templates stay in the central ModuFlow plugin/tooling repo.

## Source

- Type: user feedback
- Link: conversation, 2026-06-19
- Date: 2026-06-19

## Lifecycle

- Phase: done
- Created: 2026-06-19
- Started: 2026-06-19
- Target End: 2026-06-20
- Completed: 2026-06-20
- Last Updated: 2026-06-20

## Opportunity

The current repo is intentionally heavy because ModuFlow dogfoods itself, but the same shape feels too invasive for normal projects. Users should be able to adopt ModuFlow without feeling that every project now owns the tool's command surface, scripts, and templates.

## Scope

### In

- Define a light project layout for real project adoption.
- Keep project-local files limited to `.moduflow/`, `workspace/`, selected `issues/`, `specs/`, and `knowledge/` artifacts.
- Ensure `commands/`, `skills/`, `scripts/`, and `templates/` remain central plugin assets by default.
- Add migration/doctor guidance that distinguishes "tool repo dogfooding mode" from "target project light mode".
- Document what ModuFlow writes before it writes anything.

### Out

- Removing dogfooding artifacts from this ModuFlow repo.
- Forcing existing projects to migrate immediately.
- Changing the Git-native artifact principle.

## Acceptance Criteria

- A new project can start ModuFlow in light mode without copying command, skill, script, or template folders into the project.
- `product:start` or equivalent preflight shows the exact folders/files that will be created.
- Doctor reports whether a project is in light mode, dogfooding mode, or legacy/heavy mode.
- Migration guidance can convert a heavy project layout toward light mode without deleting user artifacts automatically.

## Workflow Tasks

Every artifact-producing step is a tracked task here - never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec -> `specs/025-lightweight-project-adoption/spec.md`
- [x] plan -> `specs/025-lightweight-project-adoption/plan.md`
- [x] execute -> PR / commits
- [x] review -> review notes
- [x] define light-mode project layout
- [x] update doctor behavior
- [x] update start/migrate lightweight write behavior
- [x] add tests for light-mode adoption

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `001-project-migration`, `002-project-profile`, `020-user-facing-simple-loop-ux`
- supersedes:
- related: `024-artifact-schema-and-doctor-gates`

## Sessions

- 2026-06-19: User flagged ModuFlow as too heavy when project adoption appears to include templates, scripts, commands, and many folders.

## Links

- Spec: `specs/025-lightweight-project-adoption/spec.md`
- Status: `specs/025-lightweight-project-adoption/status.md`
- Sessions: `sessions/025-lightweight-project-adoption/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:review 025-lightweight-project-adoption`
