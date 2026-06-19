# Issue 021: Git Binding And Execution Backend

## Summary

Define how ModuFlow connects issues and loop steps to Git branch, commit, PR, release, and optional external execution backends such as Copilot Cloud Agent, Codex, Claude Code, OpenHands, or manual execution.

## Source

- Type: product direction
- Link: user discussion, 2026-06-17
- Date: 2026-06-17

## Lifecycle

- Phase: completed
- Created: 2026-06-17
- Started: 2026-06-18
- Target End:
- Completed: 2026-06-18
- Last Updated: 2026-06-18

## Opportunity

Copilot Cloud Agent overlaps with the implementation segment. ModuFlow should not compete as another executor; it should choose and supervise execution backends while keeping Git as durable evidence.

## Scope

### In

- Define branch naming rules tied to issue IDs.
- Define commit/PR/release references back to issue/spec/status artifacts.
- Add execution backend model: local Codex, Copilot Cloud Agent, Claude Code, OpenHands, manual.
- Define backend selection criteria by task type, repo scope, risk, and available credentials.
- Record backend choice and result in status/loop state.

### Out

- Implementing Copilot Cloud Agent API integration end-to-end.
- Mandating GitHub sync for all users.

## Acceptance Criteria

- Git-files mode works without GitHub/Copilot setup.
- GitHub sync and Copilot Cloud Agent are optional upgrades, not requirements.
- `product:execute` can recommend a backend instead of always acting as executor.
- Doctor can flag branch/active issue mismatch.
- PR/release artifacts can be traced to the goal and issue that produced them.

## Workflow Tasks

- [x] spec → `specs/021-git-binding-and-execution-backend/spec.md`
- [x] plan → `specs/021-git-binding-and-execution-backend/plan.md`
- [x] execute → git binding schema + backend routing docs/scripts
- [x] review → branch/issue mismatch and backend selection tests

## Related Issues

- blocks: `023-worker-routing-and-isolation`, `024-artifact-schema-and-doctor-gates`
- blocked_by: `019-loop-kernel-and-state-model`
- duplicates:
- follows_up: `007-worker-orchestration`
- supersedes:
- related: `012-ci-pipeline`, `013-project-doctor-gate`

## Sessions

- 2026-06-17: Clarified ModuFlow as orchestrator, not competitor to Copilot Cloud Agent.
- 2026-06-18: Released Git binding helpers, backend recommendation rules, doctor branch output, and loop-state git_binding metadata.

## Links

- Spec: `specs/021-git-binding-and-execution-backend/spec.md`
- Status: `specs/021-git-binding-and-execution-backend/status.md`
- Sessions: `sessions/021-git-binding-and-execution-backend/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 022-intake-to-goal-graph`
