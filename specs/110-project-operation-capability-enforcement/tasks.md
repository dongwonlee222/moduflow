# Tasks: Project Operation Capability Enforcement

Issue: `110-project-operation-capability-enforcement`
Plan: `specs/110-project-operation-capability-enforcement/plan.md`
Status: review-ready — Streams A–C and all local D1 gates complete; non-draft PR publication pending

## Stream A — Policy, Resolver, and Audit

- [x] **A1** Add the side-effect-free capability matrix, authorization decision, typed enforcing guard, denial serializer, fixtures, and RED/GREEN tests. | Files: scripts/project_operation.py, tests/test_project_operation.py, tests/project_operation_fixture.py
- [x] **A2** Attach additive policy fields to every resolver route and surface them in Doctor/portfolio reads. | Files: scripts/project_registry.py, tests/test_project_registry.py, scripts/project_doctor.py, tests/test_project_doctor.py, scripts/project_portfolio.py, tests/test_project_portfolio.py | Depends: A1
- [x] **A3** Add the AST-backed mutator inventory audit and distribution presence checks. | Files: scripts/project_operation_audit.py, config/project-operation-entrypoints.json, tests/test_project_operation_audit.py, scripts/validate_moduflow.py, tests/test_validation_distribution.py | Depends: A1

## Stream B — Target-Project Enforcement

- [x] **B1** Guard core intake, knowledge, memory, workflow, lifecycle, and loop-state mutations; make candidate listing a pure read. | Depends: A1,A2,A3
- [x] **B2** Guard execution, review, convergence, worker-plan, and simulation report mutation modes. | Depends: A1,A2,A3
- [x] **B3** Guard production, profile, migration, promotion, reference, retention, issue-generation, Antigravity, and Spec Kit mutations. | Depends: A1,A2,A3

## Stream C — Git/External and Portfolio Boundaries

- [x] **C1** Guard dynamic Git/network/publication modes before runners while preserving repository identity and human gates. | Depends: B1,B2,B3
- [x] **C2** Authorize portfolio-control writes separately and close all mutator-audit gaps. | Depends: C1

## Stream D — Completion

- [ ] **D1** Update distribution/docs, run focused/full/release gates, produce review evidence, and publish a review-ready PR. | Depends: C2

## Required Gates

- [x] All status × trust × operation cases and fixed denial precedence pass.
- [x] Every resolver route exposes the complete additive policy shape.
- [x] Denied boundaries perform zero file/temp/Git/subprocess/network/external side effects.
- [x] The mutation inventory has zero unclassified, unguarded, duplicate, prohibited, and stale entries.
- [x] Portfolio-control authorization cannot be reused for a target-project mutation.
- [x] Publish eligibility cannot bypass repository identity, review, release, CI/status, or human approval.
- [x] Existing positional callers and active/internal behavior remain compatible.
- [x] Project validation is valid, spec consistency has zero errors, lifecycle drift is `[]`, full discovery passes, and release check is valid.

## Next Command

`product:pr 110-project-operation-capability-enforcement` — publish the verified branch as a non-draft PR.
