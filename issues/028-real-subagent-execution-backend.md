# Issue 028: Real Subagent Execution Backend

## Summary

Upgrade ModuFlow worker orchestration from static worker-plan simulation into an optional real subagent execution backend that can dispatch independent work to host-provided coding agents.

## Source

- Type: user feedback / Antigravity feedback
- Link: conversation, 2026-06-19
- Date: 2026-06-19

## Lifecycle

- Phase: backlog
- Created: 2026-06-19
- Started:
- Target End:
- Completed:
- Last Updated: 2026-06-19

## Opportunity

ModuFlow's current `worker_orchestrator.py` creates worker plans and simulates coordination through Git artifacts. That is useful for planning, but it does not fully use environments that can launch actual parallel coding agents. Antigravity feedback suggested integrating with a host subagent API such as `invoke_subagent` so independent tasks can be assigned to real workers and merged when complete.

## Scope

### In

- Define a provider-neutral subagent execution backend interface.
- Map worker-plan tasks to host subagent calls when the host supports them.
- Keep existing worker-plan JSON/Markdown as the durable audit trail.
- Add safety checks for file ownership, branch/worktree isolation, dependencies, and merge order before dispatch.
- Treat `invoke_subagent` as an Antigravity integration candidate that must be verified during spec/design.
- Record backend selection in `workspace/loop-state.json` or worker-plan metadata.

### Out

- Replacing the existing worker planner.
- Assuming every host supports real subagents.
- Automatically merging destructive or conflicting work without review.
- Hard-coding Antigravity-only APIs into the core planner.

## Acceptance Criteria

- ModuFlow can decide between `plan-only`, `manual`, and `host-subagent` execution backends.
- Worker plans identify which tasks are safe to dispatch concurrently.
- Host-specific subagent APIs are isolated behind an adapter.
- Real subagent execution produces a durable summary linked back to the issue/spec.
- Automatic merge is gated by clean verification and conflict checks.

## Workflow Tasks

Every artifact-producing step is a tracked task here - never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [ ] spec -> `specs/028-real-subagent-execution-backend/spec.md`
- [ ] plan -> `specs/028-real-subagent-execution-backend/plan.md`
- [ ] execute -> PR / commits
- [ ] review -> review notes
- [ ] verify Antigravity subagent API surface before implementation
- [ ] define provider-neutral execution backend interface
- [ ] add host-subagent adapter prototype
- [ ] preserve worker-plan audit trail and merge gates

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `007-worker-orchestration`, `023-worker-routing-and-isolation`, `026-simplify-command-and-folder-surface`
- supersedes:
- related: `027-reduce-approval-popup-friction`

## Sessions

- 2026-06-19: Antigravity feedback noted that virtual worker simulation misses the benefit of actual parallel intelligent agents.

## Links

- Spec: `specs/028-real-subagent-execution-backend/spec.md`
- Status: `specs/028-real-subagent-execution-backend/status.md`
- Sessions: `sessions/028-real-subagent-execution-backend/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:spec 028-real-subagent-execution-backend`
