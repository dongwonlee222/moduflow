# Spec 019: Loop Kernel And State Model

## Problem

ModuFlow has useful issue, spec, plan, task, worker, status, and roadmap artifacts, but the loop that connects them is still mostly command-level guidance. A plugin-installed user should not have to understand those internal commands to make progress. ModuFlow needs one durable loop kernel that can translate a simple request into a goal, issue graph, active issue, next action, Git-bound progress, and completion state.

## Goal

Make ModuFlow a user-simple goal-loop PM orchestrator. Internally it may manage a graph, cursor, phase ladder, attempts guard, and derived views. Externally the default user surface stays small: `상태`, `다음`, `이거 해줘`, `완료`.

## Non-Goals

- Full GitHub issue, PR, or Copilot Cloud Agent automation. That belongs to `021-git-binding-and-execution-backend`.
- Worker file isolation and parallel execution implementation. That belongs to `023-worker-routing-and-isolation`.
- Full natural-language intake classifier. That belongs to `022-intake-to-goal-graph`.
- Dashboard or UI redesign beyond the state fields needed to prevent drift.

## Relationship Model

Default relationships:

- Project `1:N` Goal
- Roadmap `1:N` Goal as a prioritized view
- Goal `1:N` Issue
- Goal `1:1` active Issue cursor
- Issue `1:1` Spec by default
- Issue `1:1` Plan by default
- Issue `1:N` Task
- Task `N:1` Worker Type
- Issue `1:N` Commit
- Issue `0:1` Pull Request
- Goal `1:N` Pull Request or Release

Issues may exist before a goal is finalized, but the loop should prefer attaching every active issue to a goal. A standalone issue is allowed only as an intake or triage state, not as the long-term operating model.

## State Model

Git files remain canonical. For v1 implementation, preserve existing files and add only the minimum state needed for the loop.

### Project State

`.moduflow/state.json` stays the project-level pointer:

```json
{
  "schema": "moduflow.state.v1",
  "phase": "loop-active",
  "active_goal": "goal-loop-orchestrator",
  "active_issue": "019-loop-kernel-and-state-model",
  "last_command": "product:spec 019-loop-kernel-and-state-model",
  "next_command": "product:plan 019-loop-kernel-and-state-model",
  "blockers": [],
  "updated_at": "2026-06-17"
}
```

### Loop State

`workspace/loop-state.json` becomes the active goal loop state. It must be backward compatible with the existing single `issue_id` shape while adding `issue_ids` and an active cursor.

```json
{
  "schema": "moduflow.loop-state.v2",
  "loop_id": "goal-loop-orchestrator-20260617",
  "goal_id": "goal-loop-orchestrator",
  "objective": "Make ModuFlow a plugin-installed PM loop orchestrator that connects goal, issues, specs, tasks, workers, and Git progress.",
  "issue_ids": [
    "019-loop-kernel-and-state-model",
    "020-user-facing-simple-loop-ux",
    "021-git-binding-and-execution-backend",
    "022-intake-to-goal-graph",
    "023-worker-routing-and-isolation",
    "024-artifact-schema-and-doctor-gates"
  ],
  "active_issue_id": "019-loop-kernel-and-state-model",
  "phase": "spec",
  "mode": "recommend",
  "status": "active",
  "next_command": "product:plan 019-loop-kernel-and-state-model",
  "attempts": {
    "command": "product:plan 019-loop-kernel-and-state-model",
    "count": 1,
    "max": 3,
    "last_changed_at": "2026-06-17"
  },
  "blocker": null,
  "last_action": "spec drafted",
  "last_verification": null,
  "updated_at": "2026-06-17"
}
```

Future multi-goal storage may move each goal loop into `.moduflow/goals/<goal_id>.json`, but this issue should not force a migration unless needed. The v1 rule is: project state points to the active loop; loop state owns active goal and active issue; markdown roadmap/dashboard are views.

## Loop Algorithm

1. Load project config, `.moduflow/state.json`, `workspace/loop-state.json`, roadmap, issues, specs, status files, and Git summary.
2. Reconcile active goal and active issue. If an active issue is missing or closed, select the next unblocked issue from the goal issue list.
3. Infer the active issue phase from artifacts and its `## Workflow Tasks` checklist.
4. Select the next command from the phase ladder: `issue -> spec -> plan -> execute -> review -> release -> update/status`.
5. Compare selected command with the previous command. If the same command repeats more than the configured max without artifact, verification, or state change, set `status: needs_decision`.
6. In recommend mode, report the next action without mutation. In step mode, perform one safe artifact or state update.
7. Persist state and update derived views only after the safe step succeeds.

## User-Facing Behavior

The user should not need to say `product:spec`, `product:plan`, or `product:workers` unless they want precision.

- `상태`: show active goal, active issue, current phase, blocker, next action, and recent verification.
- `다음`: recommend the next safe action.
- `이거 해줘`: route the request into the active goal or create an intake issue when no safe target exists.
- `완료`: close the current step or issue only after required artifacts and verification are present.

When ambiguity remains, ask at most one concise question. Prefer a useful default over exposing internal schema choices.

## Acceptance Criteria

- A goal can supervise multiple issues while preserving one active issue and one next command.
- Existing single-issue loop state remains readable.
- `product:loop` can recommend the next command from files without requiring GitHub connectivity.
- Repeated identical next actions trip `needs_decision` instead of looping indefinitely.
- Dashboard, roadmap, and state drift can be detected by doctor or validation in a follow-up gate.
- The first implementation can run fully in `git-files` mode after plugin installation.

## Risks

- Internal graph complexity leaking into the user surface. Mitigation: keep simple commands as the default UX and push details into diagnostics.
- State migration breaking existing projects. Mitigation: read old `issue_id` and write v2 only after successful validation.
- Premature backend coupling. Mitigation: model Git/backend binding in 021 after the loop kernel is stable.

## Open Questions

- Should multi-goal canonical storage stay in `workspace/loop-state.json` for v1 or move immediately to `.moduflow/goals/<goal_id>.json`?
- Should roadmap allow standalone issues, or only goals with nested issues after intake?
- What exact mutation boundary should `product:loop --step` have for status-only updates?

## Next Command

`product:plan 019-loop-kernel-and-state-model`
