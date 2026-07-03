# Issue 024: Artifact Schema And Doctor Gates

**Status: done** — complete.

## Summary

Strengthen validation from file-existence checks to artifact relationship checks so ModuFlow can detect broken goal, issue, spec, task, worker, Git, dashboard, and roadmap links.

## Source

- Type: product direction
- Link: user discussion, 2026-06-17
- Date: 2026-06-17

## Lifecycle

- Phase: complete
- Created: 2026-06-17
- Started: 2026-06-19
- Target End:
- Completed: 2026-06-19
- Last Updated: 2026-06-19

## Opportunity

As ModuFlow becomes a loop orchestrator, missing or drifting links are more dangerous than missing files. Doctor should explain what is stale, inconsistent, or unsafe and recommend the next repair.

## Scope

### In

- Validate issue required fields and workflow task artifact links.
- Validate goal issue list against actual issue files.
- Validate active issue, next command, dashboard, roadmap, and loop state consistency.
- Validate branch/active issue mismatch when Git is available.
- Produce actionable doctor recommendations.

### Out

- Auto-fixing all doctor findings without approval.
- Remote GitHub writes.

## Acceptance Criteria

- Doctor catches state/dashboard drift.
- Doctor catches missing linked spec/plan/tasks/status files.
- Doctor catches invalid next_command for current phase.
- Doctor catches Git branch mismatch when active issue is set.
- Release check includes the new schema gates where safe.

## Workflow Tasks

- [x] spec → `specs/024-artifact-schema-and-doctor-gates/spec.md`
- [x] plan → `specs/024-artifact-schema-and-doctor-gates/plan.md`
- [x] execute → schema validator + doctor gates
- [x] review → fixture-based drift/missing-link tests

## Related Issues

- blocks:
- blocked_by: `019-loop-kernel-and-state-model`, `021-git-binding-and-execution-backend`
- duplicates:
- follows_up: `013-project-doctor-gate`
- supersedes:
- related: `012-ci-pipeline`

## Sessions

- 2026-06-19: Completed artifact schema gates, doctor drift checks, and release validation wiring.
- 2026-06-17: Identified schema validation as the safety net for a richer loop model.

## Links

- Spec: `specs/024-artifact-schema-and-doctor-gates/spec.md`
- Status: `specs/024-artifact-schema-and-doctor-gates/status.md`
- Sessions: `sessions/024-artifact-schema-and-doctor-gates/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:status`
