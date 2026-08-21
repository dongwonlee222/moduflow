# Issue 110: Project Operation Capability Enforcement

**Status: active** — created 2026-08-21; design/specification/plan approved, Stream A and B1–B2 implemented 2026-08-21.
**Priority: p0**
**Blocked-by: `102-project-registry-and-resolver`**

## Summary

Separate project discovery from operation authorization by returning explicit project status and read/write/execute/publish capabilities, then enforcing those capabilities before every mutating workflow.

## Source

- Type: accepted external validation finding `F002` / `MF102-PROJECT-CAPABILITY-GAP`
- Review packet: `workspace/reviews/2026-08-21-issue-102-post-release-validation.json`
- Verified against: `010eee8eeec37edd6902f2dd008e7164f715e7b1`
- Owner / decision maker: Dongwon Lee
- Current phase: execution — Stream A and B1–B2 complete, B3 support/Spec Kit enforcement next

## Opportunity

The resolver currently reports archived and read-only projects as resolved without saying which operations are allowed. Callers can mistake “found” for “authorized” and mutate a project that policy intended to preserve.

## Scope

### In

- Add normalized `project_status` and `capabilities.read/write/execute/publish` with machine-readable denial reasons to every resolved context.
- Define a fail-closed policy: active internal projects may be eligible to read, write, and execute; archived or read-only projects may only read; unknown status or trust scope denies mutation.
- Treat `publish` as eligibility only. Repository identity, release, review, and human-approval gates remain independently mandatory.
- Enforce capabilities through one shared operation guard used by every project-mutating workflow.
- Classify portfolio-level selection/history writes separately from project-local writes and document that boundary.
- Return a deterministic denied result before mutation, temporary files, lifecycle journals, Git changes, or external actions.

### Out

- Canonical-path consumer migration; Issue 109 owns that audit.
- Atomic lifecycle transaction behavior; Issue 103 owns transaction semantics.
- Replacing the repository identity gate from Issue 088 or granting human approval implicitly.

## Acceptance Criteria

- Every resolved result includes normalized project status, all four capabilities, and a reason for each denied capability.
- Archived and `trust_scope=read-only` projects resolve for reads while write, execute, and publish are denied.
- Missing or unrecognized status/trust values fail closed for mutation and produce deterministic remediation guidance.
- Every project-mutating command calls the same guard before the first project-local or external side effect.
- Publish eligibility never bypasses Issue 088 repository identity, release, review, or human-approval gates.
- Denied operations leave project files, lifecycle state, Git state, and external systems unchanged.
- Contract tests enumerate the status × trust-scope × operation matrix and detect an unguarded mutating entry point.

## Verification

- Resolver capability-matrix tests.
- Mutating-workflow denial and no-write tests.
- Guard coverage test for all registered mutating entry points.
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_registry.py`
- `scripts/project_execution.py`
- `scripts/project_lifecycle.py`
- `scripts/project_production.py`
- `scripts/project_pr.py`
- `scripts/project_release.py`
- `scripts/project_sync.py`

## Scope Fence

Do not interpret resolver success as write approval, weaken downstream safety gates, or implement Issue 103's transaction engine here.

## Workflow Tasks

- [x] spec → `specs/110-project-operation-capability-enforcement/spec.md` + `spec.ko.md`
- [x] plan → `specs/110-project-operation-capability-enforcement/plan.md` + `tasks.md`
- [ ] execute → capability schema, central guard, workflow enforcement, and tests
- [ ] review

## Related Issues

- blocks: `103-atomic-lifecycle-state-transaction`
- blocked_by: `102-project-registry-and-resolver`
- duplicates:
- follows_up: `102-project-registry-and-resolver`
- supersedes:
- related: `088-canonical-repository-remote-identity-gate`, `097-single-entry-capability-routing-contract`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Review packet: `workspace/reviews/2026-08-21-issue-102-post-release-validation.md`
- Finding source: `specs/102-project-registry-and-resolver/external-review-2026-08-21.json`
- Spec: `specs/110-project-operation-capability-enforcement/spec.md`
- Korean spec: `specs/110-project-operation-capability-enforcement/spec.ko.md`
- Plan: `specs/110-project-operation-capability-enforcement/plan.md`
- Tasks: `specs/110-project-operation-capability-enforcement/tasks.md`
- Implementation readiness: `specs/110-project-operation-capability-enforcement/implementation-readiness.json`

## Next Command

`product:execute 110-project-operation-capability-enforcement` — continue B3 support/Spec Kit enforcement.
