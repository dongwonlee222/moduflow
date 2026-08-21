# Tasks: Atomic Lifecycle State Transaction

Issue: `103-atomic-lifecycle-state-transaction`
Plan: `specs/103-atomic-lifecycle-state-transaction/plan.md`
Status: ready — specification approved, dependencies complete, and implementation readiness gate passed

## Stream A — Contract, Planning, and Projected Validation

- [ ] **A1** Define `LifecycleIntent`, deterministic transaction/idempotency identity, plan/result envelopes, hashes, and reusable fixtures with RED/GREEN contract tests. | Files: scripts/project_lifecycle_transaction.py, tests/lifecycle_transaction_fixture.py, tests/test_project_lifecycle_transaction.py
- [ ] **A2** Add canonical target selection, pure renderers, nested/decoy coverage, and complete private projected-root validation. | Files: scripts/project_lifecycle_transaction.py, scripts/project_lifecycle.py, scripts/project_loop.py, scripts/validate_project_artifacts.py, focused tests | Depends: A1

## Stream B — Durable Apply, Rollback, and Recovery

- [ ] **B1** Add secure exclusive locking, same-filesystem staging, fsynced journal state machine, private preimages, cleanup, and redacted evidence. | Files: scripts/project_lifecycle_transaction.py, tests/test_project_lifecycle_transaction.py | Depends: A2
- [ ] **B2** Add deterministic apply, optimistic hash conflict handling, exact reverse rollback, idempotency, and crash recovery at every durable boundary. | Files: scripts/project_lifecycle_transaction.py, tests/test_project_lifecycle_transaction.py | Depends: B1

## Stream C — Public Mutation Adapters

- [ ] **C1** Route lifecycle, loop, dashboard, optional index, and conditional roadmap writes through the transaction while preserving public compatibility. | Files: scripts/project_lifecycle.py, scripts/project_loop.py, scripts/project_lifecycle_transaction.py, focused tests | Depends: B2
- [ ] **C2** Add compatible versioned Production Records and route creation/deduplication through the transaction. | Files: scripts/project_production.py, scripts/project_lifecycle_transaction.py, focused tests | Depends: B2

## Stream D — Recovery Diagnostics, Audit, and Completion

- [ ] **D1** Add read-only Doctor recovery diagnostics, close direct-writer audit gaps, require distribution files, and integrate focused release gates/docs. | Files: scripts/project_doctor.py, scripts/project_operation_audit.py, config/project-operation-entrypoints.json, scripts/validate_moduflow.py, scripts/release_check.py, docs/commands/tests | Depends: C1,C2
- [ ] **D2** Run focused/full/release validation, generate review evidence and visual handoff, update lifecycle artifacts, and publish one non-draft PR. | Files: Issue 103 status/review/handoff and project state views | Depends: D1

## Required Gates

- [ ] Write denial occurs before every lock, journal, staging, temporary, evidence, or canonical side effect.
- [ ] Every planned target is canonical, contained, no-follow, fully hashed, deterministically ordered, and validated in the projected state.
- [ ] Failure/crash injection at every journal boundary and target position proves unchanged state, exact rollback, or explicit `recovery_required`.
- [ ] Concurrent edits are never overwritten; identical retries return `noop`; key/intent collisions return deterministic conflict.
- [ ] Optional physical issue index stays absent unless selected; roadmap prose is untouched unless a roadmap-owned field changes.
- [ ] Production semantic versions cannot duplicate, and legacy unversioned records remain readable without migration.
- [ ] Existing public mutation entry points route through the central transaction and the operation audit reports zero gaps.
- [ ] Doctor reports incomplete recovery safely for read-only projects and emits the exact recovery command.
- [ ] Project validation is valid, spec consistency is clean, lifecycle drift is `[]`, full discovery passes, and source release check is valid.

## Next Command

`product:review 103-atomic-lifecycle-state-transaction` for plan PR #43; implementation remains approval-gated.
