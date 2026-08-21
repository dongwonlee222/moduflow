# Tasks: Canonical Project Context Consumer Convergence

Issue: `109-canonical-project-context-consumer-convergence`
Plan: `specs/109-canonical-project-context-consumer-convergence/plan.md`
Status: active — implementation authorized 2026-08-21

## Stream A — Shared Boundary and Regression Guard

- [x] **A1** Add strict context/root validation, canonical child paths, and canonical project-relative paths with RED/GREEN registry tests. | Files: scripts/project_registry.py, tests/test_project_registry.py
- [ ] **A2** Add the machine-readable canonical path-literal classifier, reviewed exceptions, distribution checks, and RED/GREEN guard tests. | Files: scripts/canonical_path_guard.py, config/canonical-path-literals.json, tests/test_canonical_path_guard.py, scripts/validate_moduflow.py, scripts/release_check.py | Depends: A1

## Stream B — Filesystem Consumer Convergence

- [x] **B1** Converge knowledge, workflow, and project validation on one context with nested/poisoned-default contract tests. | Files: scripts/project_knowledge.py, tests/test_project_knowledge.py, scripts/project_workflow.py, tests/test_project_workflow.py, scripts/validate_project_artifacts.py, tests/test_validation_distribution.py | Depends: A1
- [x] **B2** Converge review, converge, worker orchestration, spec consistency, and reference backlog paths and generated links. | Files: scripts/project_review.py, tests/test_project_review.py, scripts/project_converge.py, tests/test_project_converge.py, scripts/worker_orchestrator.py, tests/test_worker_orchestration.py, scripts/spec_consistency.py, tests/test_spec_consistency.py, scripts/project_reference_backlog.py, tests/test_project_reference_backlog.py | Depends: A1,B1

## Stream C — Adapter and Git History Convergence

- [x] **C1** Converge memory dashboards/drill-down and Spec Kit inputs/outputs while preserving stricter no-follow behavior. | Files: scripts/project_memory.py, tests/test_project_memory.py, scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py | Depends: A1,B1
- [ ] **C2** Scope sync and commit attribution Git commands to the canonical configured issue prefix with FakeRunner tests. | Files: scripts/project_sync.py, tests/test_project_sync.py, scripts/commit_resolution.py, tests/test_commit_resolution.py, tests/test_commit_resolution_parity.py | Depends: A1

## Stream D — Verification and Publication

- [ ] **D1** Run the guard, focused/full suites, validation, drift, review handoff, acceptance review, release check, lifecycle updates, and publish the completed branch/PR. | Files: issues/109-canonical-project-context-consumer-convergence.md, specs/109-canonical-project-context-consumer-convergence/status.md, specs/109-canonical-project-context-consumer-convergence/review.md, specs/109-canonical-project-context-consumer-convergence/review-handoff.md, workspace/dashboard.md, workspace/roadmap.md, .moduflow/state.json, workspace/loop-state.json | Depends: A2,B2,C1,C2

## Required Gates

- [ ] All twelve specification acceptance criteria have direct test or review evidence.
- [ ] Project B honors all eight nested canonical roles and poisoned default folders remain byte-identical.
- [ ] Invalid, unresolved, ambiguous, malformed, and cross-project contexts perform zero target-project I/O.
- [ ] The canonical path guard has zero unclassified hits and zero stale/unjustified classifications.
- [ ] Issue 102 and Issue 093 regression suites remain green.
- [ ] Spec consistency has zero errors; project validation is valid; lifecycle drift is `[]`.
- [ ] Full test discovery and `python3 scripts/release_check.py .` pass.
- [ ] GitHub publication happens only after review evidence and final verification are committed.

## Next Command

`product:execute 109-canonical-project-context-consumer-convergence`
