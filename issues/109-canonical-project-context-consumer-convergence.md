# Issue 109: Canonical Project Context Consumer Convergence

**Status: active** — created 2026-08-21; specification approved and implementation authorized 2026-08-21.
**Priority: p0**
**Blocked-by: `102-project-registry-and-resolver`**

## Summary

Complete the Issue 102 follow-up by auditing every project-aware path consumer and replacing direct `<root>/<default-folder>` assumptions with paths from one resolved project context.

## Source

- Type: accepted external validation finding `F001` / `MF102-CANONICAL-CONSUMER-GAP`
- Review packet: `workspace/reviews/2026-08-21-issue-102-post-release-validation.json`
- Verified against: `010eee8eeec37edd6902f2dd008e7164f715e7b1`
- Owner / decision maker: Dongwon Lee
- Current phase: implementation active; Tasks A1, B1, B2, and C1 complete

## Opportunity

Issue 102 introduced the canonical resolver, but several consumers still build default paths directly. A registered project with nested or renamed canonical folders can therefore resolve correctly and still be read from or written to through the wrong folder.

## Scope

### In

- Audit all project-aware path consumers, including `project_knowledge`, `project_workflow`, `validate_project_artifacts`, `project_review`, `project_converge`, `worker_orchestrator`, and `spec_consistency`.
- Route issue, spec, workspace, knowledge, memory, production-record, playbook, and workflow paths through the resolved project context and the registry canonical-path API.
- Define the explicit-root compatibility adapter as the only sanctioned boundary for legacy callers that have no registry context.
- Add non-default-path and decoy-default-folder contract tests for every migrated consumer.
- Guarantee that ambiguous or unresolved context performs no project-local I/O.

### Out

- Project status and operation permissions; Issue 110 owns those rules.
- Atomic multi-file lifecycle writes; Issue 103 owns transaction behavior.
- Moving project folders or changing registry schema ownership.

## Acceptance Criteria

- Every project-aware consumer obtains canonical paths from one resolved project context; no production consumer independently reconstructs a default project folder.
- The seven named consumers pass nested-path fixtures for every canonical path type they use.
- A decoy default folder containing conflicting artifacts is never read or mutated when the registry points elsewhere.
- Explicit-root compatibility is isolated behind one documented adapter and produces the same normalized context shape as registry resolution.
- Ambiguous and unresolved requests return before any project-local read or write.
- A repository-wide guard test detects new direct default-path construction outside approved compatibility and fixture code.
- Existing Issue 102 resolution, containment, and Project A/B isolation tests remain green.

## Verification

- Focused consumer contract tests with nested canonical paths and decoy defaults.
- Repository-wide direct-path guard test.
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_registry.py`
- `scripts/project_knowledge.py`
- `scripts/project_workflow.py`
- `scripts/validate_project_artifacts.py`
- `scripts/project_review.py`
- `scripts/project_converge.py`
- `scripts/worker_orchestrator.py`
- `scripts/spec_consistency.py`

## Scope Fence

Do not add operation capabilities, lifecycle transactions, remote writes, or folder migration in this issue.

## Workflow Tasks

- [x] spec → `specs/109-canonical-project-context-consumer-convergence/spec.md` + `spec.ko.md` (approved 2026-08-21)
- [x] plan → `specs/109-canonical-project-context-consumer-convergence/plan.md` + `tasks.md`
- [ ] execute → consumer migration, guardrails, and contract tests
- [ ] review → create after implementation verification

## Related Issues

- blocks: `103-atomic-lifecycle-state-transaction`
- blocked_by: `102-project-registry-and-resolver`
- duplicates:
- follows_up: `102-project-registry-and-resolver`
- supersedes:
- related: `093-frontmatter-issue-schema-readiness-gate`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Review packet: `workspace/reviews/2026-08-21-issue-102-post-release-validation.md`
- Finding source: `specs/102-project-registry-and-resolver/external-review-2026-08-21.json`
- Spec: `specs/109-canonical-project-context-consumer-convergence/spec.md`
- Korean spec: `specs/109-canonical-project-context-consumer-convergence/spec.ko.md`
- Plan: `specs/109-canonical-project-context-consumer-convergence/plan.md`
- Tasks: `specs/109-canonical-project-context-consumer-convergence/tasks.md`

## Next Command

`product:execute 109-canonical-project-context-consumer-convergence`.
