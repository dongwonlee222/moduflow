# Issue 113: Review Lifecycle and Exception Fix Approval

**Status: backlog** — created 2026-09-01.
**Priority: p1**
**Blocked-by: `103-atomic-lifecycle-state-transaction`, `112-execution-planner-and-backend-boundary`**

## Summary

Separate implementation completion, review, remediation, approval, and merge states, and require an explicit user-approved exception record before execution exceeds the normal SDD fix-round limit.

## Source

- Type: user-requested execution architecture audit follow-up
- Owner / decision maker: Dongwon Lee
- Approved decomposition: 2026-09-01
- Trend evidence: `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`

## Opportunity

Current issue, team, and review artifacts can collapse code completion and final approval into a single advanced state. Review findings then appear after the workflow has already moved ahead, and an extra remediation round has no durable user-approval record.

## Scope

### In

- Define the ordered review lifecycle `implementation_done → review_pending → fixes_required → approved → merged`.
- Record transition actor, source event, evidence links, fix-round count, and next command.
- Make reviewer findings move work to `fixes_required` without changing canonical acceptance criteria or silently dismissing findings.
- Return to `review_pending` only after a remediation round has fresh verification evidence.
- Introduce `exception_fix_approved` with approver, reason, allowed round, scope, timestamp, and linked findings when the normal SDD fix-round limit is exhausted.
- Apply review-state changes through Issue 103's transaction boundary and project capability checks.
- Project the state consistently to status, loop, dashboard, PR handoff, and team workflow views.

### Out

- Automatic human approval or automatic merge.
- Replacing GitHub review, CI, or branch protection.
- Production artifact approval, which remains owned by Issue 108.
- Changing Superpowers' internal review algorithm or fix-round policy.

## Acceptance Criteria

- `implementation_done` never renders as human-approved or merged.
- An open required finding produces `fixes_required`; a successful fix produces `review_pending`, not `approved`.
- `approved` requires explicit reviewer/approver evidence and `merged` requires verified merge evidence.
- A remediation attempt beyond the configured normal limit is blocked unless a matching `exception_fix_approved` record exists.
- Exception approval is single-purpose, round-bounded, actor-attributed, and cannot approve unrelated findings.
- Failed or concurrent state projection leaves every review/lifecycle view unchanged through Issue 103 rollback.
- Legacy review artifacts remain readable and receive an explicit compatibility mapping.

## Verification

- State-transition table tests including invalid skips, concurrent findings, remediation success/failure, exhausted rounds, scoped exception approval, and merge proof.
- Projection and rollback tests across issue/status/loop/dashboard/PR/team views.
- Existing review, workflow, loop, transaction, and release suites.

## Entry Points

- `scripts/project_workflow.py`
- `scripts/project_review.py`
- `scripts/project_execution.py`
- `scripts/project_loop.py`
- `commands/product-review.md`
- `templates/workflow/review-gates.md`

## Scope Fence

Do not infer approval from passing tests, a completed implementation task, or an agent verdict. Human-required approval remains explicit.

## Workflow Tasks

- [x] benchmark → `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`
- [x] design/scope → `docs/superpowers/specs/2026-09-01-execution-governance-scope-design.md`
- [ ] spec → `specs/113-review-lifecycle-and-exception-fix-approval/spec.md`
- [ ] plan → `specs/113-review-lifecycle-and-exception-fix-approval/plan.md` + `tasks.md`
- [ ] execute → state machine, exception approval evidence, projections, and tests
- [ ] review → `specs/113-review-lifecycle-and-exception-fix-approval/review.md`

## Related Issues

- blocks:
- blocked_by: `103-atomic-lifecycle-state-transaction`, `112-execution-planner-and-backend-boundary`
- duplicates:
- follows_up: `051-autonomous-execute-review-visual-handoff`, `052-draft-pr-review-handoff`, `089-verified-code-review-intake-and-remediation-routing`
- supersedes:
- related: `057-korean-human-review-packet`, `071-spec-code-converge-check`, `108-production-approval-and-verification-gates`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Benchmark: `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`

## Next Command

After Issues 103 and 112: `product:spec 113-review-lifecycle-and-exception-fix-approval`.
