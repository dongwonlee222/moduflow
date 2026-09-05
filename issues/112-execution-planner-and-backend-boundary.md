# Issue 112: Execution Planner and Backend Boundary

**Status: backlog** — created 2026-09-01.
**Priority: p0**
**Blocked-by: `103-atomic-lifecycle-state-transaction`**

## Summary

Make ModuFlow plan only executable implementation work and select exactly one execution path—inline or Superpowers SDD—while leaving actual agent dispatch to the active host runtime.

## Source

- Type: user-requested execution architecture audit follow-up
- Owner / decision maker: Dongwon Lee
- Approved decomposition: 2026-09-01
- Trend evidence: `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`
- Scope design: `docs/superpowers/specs/2026-09-01-execution-governance-scope-design.md`

## Opportunity

The current worker planner converts every checkbox into a worker task, including decisions, completion conditions, and Hard Gates. It can emit tasks with no expected files or dependencies, records stale absolute project roots, and produces a second execution ceremony even when Superpowers SDD or the host already owns dispatch. This creates misleading readiness and unnecessary product weight.

## Scope

### In

- Select only unchecked, executable implementation tasks from canonical `specs/<issue>/tasks.md`.
- Exclude decisions, approval conditions, acceptance criteria, verification gates, release gates, and documentation-only completion evidence unless they are explicitly declared as an implementation deliverable.
- Require concrete expected files or globs plus valid dependency references before generating a worker task.
- Return a clear `not_applicable` or `needs_plan` result instead of writing a worker plan when no executable task or usable file boundary exists.
- Emit one execution-routing decision: `inline` for small/shared-context work or `superpowers-sdd` for bounded multi-task implementation and review.
- Keep ModuFlow `spec.md`, `plan.md`, and `tasks.md` canonical; link Superpowers design/plan documents as execution detail rather than a second lifecycle truth.
- Keep host capabilities and agent APIs behind an adapter boundary so Claude Code, Codex, Copilot, or later hosts can execute the same routing result.
- Record routing reason, selected backend, task IDs, file boundaries, dependencies, approval requirement, and next command without claiming dispatch occurred.

### Out

- Building a ModuFlow subagent runtime, scheduler, queue, or worktree manager.
- Reimplementing Superpowers SDD inside ModuFlow.
- Using Spec Kit `implement` or letting Spec Kit own lifecycle, Git, review, or release.
- Forcing workers for simple, sequential, single-file, or shared-state changes.

## Acceptance Criteria

- Decision text, Hard Gates, acceptance criteria, and already-completed tasks never become worker tasks.
- Every generated implementation task has at least one concrete file/glob boundary and all dependencies resolve to generated executable task IDs.
- Missing executable boundaries produces no `worker-plan.md` or `worker-plan.json` write and recommends `product:plan`.
- One request selects exactly one of `inline` or `superpowers-sdd`; ModuFlow never runs a competing dispatch loop.
- A host adapter can map the same routing result to Claude Code, Codex, or Copilot without changing canonical project artifacts.
- Canonical ModuFlow artifacts and linked Superpowers execution details cannot independently claim conflicting task completion.
- Existing implementation-readiness, capability, repository identity, and Issue 103 transaction gates remain authoritative.

## Verification

- Fixtures containing implementation tasks, decisions, Hard Gates, approval conditions, missing files, dangling dependencies, same-file work, and independent workstreams.
- Cross-host routing fixtures that prove the plan is host-neutral and dispatch claims remain truthful.
- Existing worker, execution, loop, lifecycle, and distribution tests.
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/worker_orchestrator.py`
- `scripts/project_execution.py`
- `commands/product-workers.md`
- `commands/product-execute.md`
- `skills/superpowers-execution-bridge/SKILL.md`
- `specs/*/tasks.md`

## Scope Fence

Do not add another execution engine. ModuFlow owns selection, state, evidence, and policy; the selected host/Superpowers path owns implementation execution.

## Workflow Tasks

- [x] benchmark → `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`
- [x] design/scope → `docs/superpowers/specs/2026-09-01-execution-governance-scope-design.md`
- [x] spec → `specs/112-execution-planner-and-backend-boundary/spec.md` (한글: `spec.ko.md`)
- [x] plan → `specs/112-execution-planner-and-backend-boundary/plan.md` + `tasks.md`
- [ ] execute → planner filtering, backend decision contract, artifact ownership, and tests
- [ ] review → `specs/112-execution-planner-and-backend-boundary/review.md`

## Related Issues

- blocks: `104-project-aware-natural-language-request-orchestrator`, `113-review-lifecycle-and-exception-fix-approval`
- blocked_by: `103-atomic-lifecycle-state-transaction`
- duplicates:
- follows_up: `051-autonomous-execute-review-visual-handoff`, `077-implementation-readiness-gate`, `079-plan-discipline-skill-matrix`
- supersedes:
- related: `023-worker-routing-and-isolation`, `028-real-subagent-execution-backend`, `084-worker-prompt-context-budget`, `098-speckit-selective-validation-adapter`


## Landed Early — 2026-09-04

One piece of this issue shipped before the issue itself was specced, and is recorded here so the spec does not plan it again.

`scripts/worker_orchestrator.py` gained `dispatchable_now(planned_tasks)`, and `worker-plan.md` gained a `Dispatchable Now` section naming the tasks whose dependencies are met and whose declared files do not overlap. Commit `ba1269a`.

The reason it could not wait: the plan's only parallel outputs were a whole-plan verdict and a linear `merge_order`, so eligibility appeared fixed at planning time. It is not — it changes every time a task completes and unblocks its dependents. On 2026-09-04 that window opened three times during Issue 086 and a human had to notice it each time.

What this does **not** cover, and what this issue still owns: the execution-routing decision itself (`inline` versus `superpowers-sdd`), the `not_applicable` / `needs_plan` results, the host-neutral adapter boundary, and recording the routing reason without claiming dispatch occurred. Only the "what can start together right now" question is answered.

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Benchmark: `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`
- Scope design: `docs/superpowers/specs/2026-09-01-execution-governance-scope-design.md`

## Next Command

Issue 103 is done. Spec, plan and tasks are written and pass
`spec_consistency` with zero findings. `tasks.md` declares a boundary on every
task and passes this issue's own prototype gates (`ok`, `inline`), so the spec
satisfies the contract it defines.

Blocked on the four human review decisions in
`specs/112-execution-planner-and-backend-boundary/spec.md` §15 — chiefly
fail-closed refusal and its effect on 19 live specs. After that,
`product:execute`, starting with the Stream C interface review.
