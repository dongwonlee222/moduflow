# Issue 117: Plan Execution Readiness Surfacing

**Status: backlog** — created 2026-09-04.
**Priority: p1**
**Blocked-by:**

## Summary

Report, without being asked, when an issue has a plan that no execution tool can read: a completed plan with no `specs/<issue>/tasks.md`, a `tasks.md` whose tasks declare no expected files, or a `tasks.md` with no generated worker plan.

## Source

- Type: observed failure during the Issue 086 planning session
- Owner / decision maker: Dongwon Lee
- Observed: 2026-09-04. Plans for Issues 091 and 086 were written as prose streams with no `tasks.md`, so `scripts/worker_orchestrator.py` had no input and parallel eligibility was judged by hand instead. Issues 090, 103 and 111 have a `tasks.md` and have still never produced a worker plan. No worker plan existed anywhere in the repository.

## Opportunity

The machinery is already built and already correct. `worker_orchestrator.py` computes file overlap, shared-state risk, worker grouping, dependency-aware merge order and a `parallel-eligible` verdict from `[files:]`, `[depends:]` and `[shared_state:]` metadata. Issue 112 will consume the same input and return `needs_plan` when the boundaries are unusable. `project_issue_schema.py` already indexes which artifacts each issue has.

What is missing is that nothing says any of this until a human invokes it. On 2026-09-04 the owner had to ask three times before the tooling was run at all, and the hand analysis it replaced had already missed two dispatchable lanes and one file collision.

Documentation and agent memory were both tried for this class of problem earlier the same day and both failed. A check is what works.

## Scope

### In

- Detect an issue whose `plan` workflow task is checked while `specs/<issue>/tasks.md` is absent.
- Detect a `tasks.md` whose unchecked tasks declare no `[files:]` or `[globs:]`, since Issue 112 cannot route those.
- Detect a `tasks.md` with no `worker-plan.json`, or one older than the `tasks.md` that produced it.
- Report issue id, which of the three conditions holds, and the next command; surface it where lifecycle findings already surface.
- Reuse `worker_orchestrator.parse_tasks` and `parse_task_metadata` for reading; reuse the existing artifact index for presence.

### Out

- Generating `tasks.md` or a worker plan automatically. The author writes the boundaries; a machine guessing them is worse than an empty result.
- Blocking execute, review, merge or release on this signal.
- Judging whether the declared file boundaries are correct, only whether they exist.
- A second task parser, a second artifact index, or a second lifecycle truth.
- Requiring a worker plan for issues that are legitimately inline; a `sequential` verdict is a normal and complete result.

## Acceptance Criteria

- An issue with a checked `plan` task and no `tasks.md` is reported with that reason and a next command.
- A `tasks.md` whose unchecked tasks carry no file or glob boundary is reported as unroutable by Issue 112's contract.
- A `tasks.md` newer than its `worker-plan.json` is reported as stale; equal or missing plans are distinguished from stale ones.
- An issue whose worker plan says `sequential` is silent. Sequential is an answer, not a defect.
- Nothing is generated, and nothing is blocked.
- Task reading goes through `worker_orchestrator`'s existing parser; no second parser is added.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest tests.test_worker_orchestration tests.test_project_doctor -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/worker_orchestrator.py`
- `scripts/project_doctor.py`
- `scripts/project_issue_schema.py`
- `tests/test_worker_orchestration.py`

## Scope Fence

This reports that a plan cannot be executed by the tooling that exists. It does not write plans, does not choose file boundaries, and does not gate any transition.

## Workflow Tasks

- [ ] spec → `specs/117-plan-execution-readiness-surfacing/spec.md`
- [ ] plan → `specs/117-plan-execution-readiness-surfacing/plan.md` + `tasks.md` with declared file boundaries
- [ ] execute → detection, reporting and focused tests
- [ ] review → `specs/117-plan-execution-readiness-surfacing/review.md`

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `023-worker-routing-and-isolation`
- supersedes:
- related: `112-execution-planner-and-backend-boundary`, `116-merged-issue-completion-parity`, `093-frontmatter-issue-schema-readiness-gate`, `105-schema-migration-and-doctor-triage`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Observed during: `specs/086-project-aware-production-library-dashboard/worker-plan.md`

## Next Command

`product:spec 117-plan-execution-readiness-surfacing`.
