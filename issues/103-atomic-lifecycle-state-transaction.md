# Issue 103: Atomic Lifecycle State Transaction

**Status: backlog** — created 2026-08-19.
**Priority: p0**
**Blocked-by:**

## Summary

Replace best-effort lifecycle propagation with a validated application-level transaction that updates the owning issue, state, loop, dashboard, issue index, roadmap when applicable, and Production Record when applicable with staged writes, recovery evidence, and byte-for-byte rollback.

## Source

- Type: user multi-project orchestration improvement request
- Link: local Codex attachment `pasted-text.txt`, 2026-08-19
- Owner / decision maker: Dongwon Lee
- Current phase: backlog

## Opportunity

Issue 048 made the issue status canonical and added drift detection plus a single propagation point for `.moduflow/state.json` and the dashboard. It explicitly did not unify all state consumers or guarantee rollback. Real project use still produced mismatched active issues across issue, state, loop, dashboard, issue index, and roadmap files.

## Scope

### In

- Define a change plan that lists every affected canonical and derived artifact before writes.
- Render changes to temporary results, validate the complete projected state, then apply all changes together.
- Restore the original byte content when any validation or write step fails.
- Define the guarantee precisely as application-level all-or-nothing behavior; portable filesystems do not provide one kernel-atomic rename across multiple files.
- Cover owning issue, `.moduflow/state.json`, `workspace/loop-state.json`, dashboard, optional issue index, conditional roadmap, and conditional Production Record.
- Make retries idempotent and record the applied change set plus next command.
- Add injected-failure and drift regression fixtures.

### Out

- Replacing issue Markdown as lifecycle truth.
- Changing the issue schema or project resolution contract.
- Distributed transactions across remote GitHub objects or external SaaS systems.

## Acceptance Criteria

- A failure after any staged update leaves every tracked target byte-identical to its pre-transaction state.
- A successful lifecycle mutation produces no lifecycle drift across all configured state views.
- Repeating the same transaction returns `noop` and does not duplicate Production Record versions.
- Optional files that are absent remain absent unless the owning workflow explicitly requires them.
- Priority changes include roadmap projection; non-priority changes do not rewrite roadmap prose.
- Transaction evidence records affected paths, validation result, applied/noop/rolled_back status, and next command.
- Existing Issue 048 drift checks continue to pass and detect any bypassed manual mutation.

## Verification

- Failure injection at each stage of plan, render, validate, and apply.
- Idempotence tests for start, update, pause, resume, complete, and production-version flows.
- Drift checks across issue, state, loop, dashboard, issue index, and roadmap fixtures.
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_lifecycle.py`
- `scripts/project_loop.py`
- `scripts/validate_project_artifacts.py`
- `scripts/project_production.py`
- `.moduflow/state.json`
- `workspace/loop-state.json`

## Scope Fence

Do not change project resolution, migrate legacy schemas, or make remote GitHub writes transactional in this issue.

## Workflow Tasks

- [ ] spec → `specs/103-atomic-lifecycle-state-transaction/spec.md`
- [ ] plan → `specs/103-atomic-lifecycle-state-transaction/plan.md`
- [ ] execute → transaction planner, staged validation, rollback, evidence, and tests
- [ ] review → `specs/103-atomic-lifecycle-state-transaction/review.md`

## Related Issues

- blocks: `104-project-aware-natural-language-request-orchestrator`, `105-schema-migration-and-doctor-triage`
- blocked_by:
- duplicates:
- follows_up: `019-loop-kernel-and-state-model`, `048-artifact-lifecycle-sync`
- supersedes:
- related: `024-artifact-schema-and-doctor-gates`, `072-lifecycle-hooks-automation`, `093-frontmatter-issue-schema-readiness-gate`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Source audit: `specs/102-project-registry-and-resolver/source-audit.md`

## Next Command

`product:spec 103-atomic-lifecycle-state-transaction`
