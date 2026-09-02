# Review Handoff: 103-atomic-lifecycle-state-transaction

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/103-atomic-lifecycle-state-transaction.md`
  - `specs/103-atomic-lifecycle-state-transaction/spec.md`
  - `specs/103-atomic-lifecycle-state-transaction/tasks.md`

### Implementation Tasks

- [x] **A1** Define `LifecycleIntent`, deterministic transaction/idempotency identity, plan/result envelopes, hashes, and reusable fixtures with RED/GREEN contract tests. | Files: scripts/project_lifecycle_transaction.py, tests/lifecycle_transaction_fixture.py, tests/test_project_lifecycle_transaction.py
- [x] **A2** Add canonical target selection, pure renderers, nested/decoy coverage, and complete private projected-root validation. | Files: scripts/project_lifecycle_transaction.py, scripts/project_lifecycle.py, scripts/project_loop.py, scripts/validate_project_artifacts.py, focused tests | Depends: A1
- [x] **B1** Add secure exclusive locking, same-filesystem staging, fsynced journal state machine, private preimages, cleanup, and redacted evidence. | Files: scripts/project_lifecycle_transaction.py, tests/test_project_lifecycle_transaction.py | Depends: A2
- [x] **B2** Add deterministic apply, optimistic hash conflict handling, exact reverse rollback, idempotency, and crash recovery at every durable boundary. | Files: scripts/project_lifecycle_transaction.py, tests/test_project_lifecycle_transaction.py | Depends: B1
- [x] **C1a** Add the transaction-backed lifecycle transition adapter plus transition/recovery CLI modes. | Files: scripts/project_lifecycle.py, tests/test_project_lifecycle.py, tests/test_project_lifecycle_transaction.py | Depends: B2 | Commits: e8530cd,5001ada
- [x] **C1b** Route compatibility `sync_lifecycle()` reconcile, state, dashboard, optional index, and shared projected routing through one transaction. | Files: scripts/project_lifecycle.py, scripts/project_lifecycle_transaction.py, focused tests | Depends: C1a | Commit: 7b53a00 | Plan: docs/superpowers/plans/2026-09-01-issue-103-c1b-sync-reconcile-adapter.md
- [x] **C1c** Route public loop-state mutation through the transaction and close the remaining C1 direct-write bypass. | Files: scripts/project_loop.py, scripts/project_lifecycle_transaction.py, focused tests | Depends: C1b | Commit: a770e75 | Plan: docs/superpowers/plans/2026-09-01-issue-103-c1c-loop-mutation-adapter.md
- [x] **C1d** Derive transition and loop-update state/dashboard/route projections from one shared projected issue evaluation without weakening canonical no-follow reads. | Files: scripts/project_lifecycle_transaction.py, scripts/project_loop.py, focused tests | Depends: C1c | Commit: 8ada787 | Plan: docs/superpowers/plans/2026-09-01-issue-103-c1d-projected-transition-routing.md
- [x] **C1e** Connect public transition `--priority` to conditional roadmap projection without changing no-priority target selection. | Files: scripts/project_lifecycle.py, tests/test_project_lifecycle.py, transaction integration tests | Depends: C1d | Commit: c71a543 | Plan: docs/superpowers/plans/2026-09-01-issue-103-c1e-priority-roadmap-cli.md
- [x] **C2a** Add legacy-safe Production Record version parsing and opt-in pure rendering. | Files: scripts/project_production.py, tests/test_project_production.py | Depends: B2 | Commit: 3361e33 | Plan: docs/superpowers/plans/2026-09-01-issue-103-c2a-production-version-metadata.md
- [x] **C2b1** Reject duplicate semantic versions in canonical/projected Production Record validation. | Files: scripts/project_production.py, tests/test_project_production.py | Depends: C2a | Commit: 93f6d80 | Plan: docs/superpowers/plans/2026-09-01-issue-103-c2b1-production-version-validation.md
- [x] **C2b2** Recheck Production Record semantic uniqueness under the transaction lock before any durable side effect. | Files: scripts/project_lifecycle_transaction.py, tests/test_project_lifecycle_transaction.py | Depends: C2b1 | Commit: 99c050b | Plan: docs/superpowers/plans/2026-09-01-issue-103-c2b2-locked-production-version-recheck.md
- [x] **C2b** Add projected semantic-version uniqueness and same-lock recheck. | Files: scripts/project_lifecycle_transaction.py, tests/test_project_lifecycle_transaction.py | Depends: C2a | Commits: 93f6d80,99c050b
- [x] **C2c** Route public Production Record creation and CLI through the transaction. | Files: scripts/project_production.py, scripts/project_lifecycle_transaction.py, focused tests | Depends: C2b | Commit: ec0ed17 | Plan: docs/superpowers/plans/2026-09-01-issue-103-c2c-public-production-adapter.md
- [x] **C2** Add compatible versioned Production Records and route creation/deduplication through the transaction. | Files: scripts/project_production.py, scripts/project_lifecycle_transaction.py, focused tests | Depends: B2 | Commits: 3361e33,93f6d80,99c050b,ec0ed17
- [x] **D1a** Add read-only lifecycle transaction diagnostics to Doctor with exact recovery commands and nonzero incomplete/unsafe status. | Files: scripts/project_lifecycle_transaction.py, scripts/project_doctor.py, commands/product-doctor.md, focused tests | Depends: C1,C2 | Commits: 4feb071,7607e7d | Plan: docs/superpowers/plans/2026-09-01-issue-103-d1a-doctor-recovery-diagnostics.md
- [x] **D1b** Close transaction/public-writer audit gaps and require a zero-gap operation inventory. | Files: scripts/project_operation_audit.py, config/project-operation-entrypoints.json, config/canonical-path-literals.json, tests/test_project_operation_audit.py | Depends: D1a | Commit: 294487a | Plan: docs/superpowers/plans/2026-09-02-issue-103-d1b-mutator-bypass-audit.md
- [x] **D1c** Require transaction files and focused suites in distribution/release gates and document local/remote guarantees. | Files: scripts/validate_moduflow.py, scripts/release_check.py, tests/test_validation_distribution.py, docs/architecture.md, docs/workflow.md | Depends: D1b | Commit: 99e0605 | Plan: docs/superpowers/plans/2026-09-02-issue-103-d1c-distribution-release-guarantees.md
- [x] **D1** Add read-only Doctor recovery diagnostics, close direct-writer audit gaps, require distribution files, and integrate focused release gates/docs. | Files: scripts/project_doctor.py, scripts/project_operation_audit.py, config/project-operation-entrypoints.json, scripts/validate_moduflow.py, scripts/release_check.py, docs/commands/tests | Depends: C1,C2 | Commits: 4feb071,7607e7d,294487a,99e0605

## Review Subagents

### QA Review

- Worker: `qa-reviewer`
- Goal: run verification, check acceptance criteria, and report regressions.
- Required commands:
  - `python3 -m unittest discover -s tests -v`
  - `python3 scripts/release_check.py .`

### PM / Spec Review

- Worker: `pm-strategist`
- Worker: `spec-architect`
- Goal: compare implementation against problem, goals, non-goals, and acceptance criteria.
- Constitution check (issue 073): verify against `workspace/constitution.md` and record the compliance line in review.md — `Constitution: v<X.Y> checked — no violations` or the violation list.

## Visual Handoff

Regenerate the ModuFlow dashboard and its issue drill-down before reporting completion.
The issue HTML is not a separate source artifact; it is a derived L2 view linked from the dashboard system.

```bash
python3 scripts/project_memory.py . --dashboard
```

```bash
python3 scripts/project_memory.py . --issue 103-atomic-lifecycle-state-transaction
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-103-atomic-lifecycle-state-transaction.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-103-atomic-lifecycle-state-transaction.html`.

## Source Snapshot

- Issue bytes: 5599
- Spec bytes: 14441
- Status bytes: 2593
