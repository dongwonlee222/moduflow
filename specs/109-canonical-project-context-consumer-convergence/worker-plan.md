# Worker Plan: 109-canonical-project-context-consumer-convergence

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `qa-reviewer` | `sequential` | ready | - | - | **A1** Add strict context/root validation, canonical child paths, and canonical project-relative paths with RED/GREEN registry tests. | Files: scripts/project_registry.py, tests/test_project_registry.py |
| T02 | `qa-reviewer` | `sequential` | ready | - | - | **A2** Add the machine-readable canonical path-literal classifier, reviewed exceptions, distribution checks, and RED/GREEN guard tests. | Files: scripts/canonical_path_guard.py, config/canonical-path-literals.json, tests/test_canonical_path_guard.py, scripts/validate_moduflow.py, scripts/release_check.py | Depends: A1 |
| T03 | `qa-reviewer` | `group-1` | ready | - | - | **B1** Converge knowledge, workflow, and project validation on one context with nested/poisoned-default contract tests. | Files: scripts/project_knowledge.py, tests/test_project_knowledge.py, scripts/project_workflow.py, tests/test_project_workflow.py, scripts/validate_project_artifacts.py, tests/test_validation_distribution.py, tests/project_context_fixture.py | Depends: A1 |
| T04 | `qa-reviewer` | `group-1` | ready | - | - | **B2** Converge review, converge, worker orchestration, spec consistency, and reference backlog paths and generated links. | Files: scripts/project_review.py, tests/test_project_review.py, scripts/project_converge.py, tests/test_project_converge.py, scripts/worker_orchestrator.py, tests/test_worker_orchestrator.py, scripts/spec_consistency.py, tests/test_spec_consistency.py, scripts/project_reference_backlog.py, tests/test_project_reference_backlog.py | Depends: A1,B1 |
| T05 | `qa-reviewer` | `group-1` | ready | - | - | **C1** Converge memory dashboards/drill-down and Spec Kit inputs/outputs while preserving stricter no-follow behavior. | Files: scripts/project_memory.py, tests/test_project_memory.py, scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py | Depends: A1,B1 |
| T06 | `qa-reviewer` | `sequential` | ready | - | - | **C2** Scope sync and commit attribution Git commands to the canonical configured issue prefix with FakeRunner tests. | Files: scripts/project_sync.py, tests/test_project_sync.py, scripts/commit_resolution.py, tests/test_commit_resolution.py, tests/test_commit_resolution_parity.py | Depends: A1 |
| T07 | `pm-strategist` | `sequential` | ready | - | - | **D1** Run the guard, focused/full suites, validation, drift, review handoff, acceptance review, release check, lifecycle updates, and publish the completed branch/PR. | Files: issues/109-canonical-project-context-consumer-convergence.md, specs/109-canonical-project-context-consumer-convergence/status.md, specs/109-canonical-project-context-consumer-convergence/review.md, specs/109-canonical-project-context-consumer-convergence/review-handoff.md, workspace/dashboard.md, workspace/roadmap.md, .moduflow/state.json, workspace/loop-state.json | Depends: A2,B2,C1,C2 |
| T08 | `qa-reviewer` | `group-1` | ready | - | - | All twelve specification acceptance criteria have direct test or review evidence. |
| T09 | `implementation-worker` | `group-3` | ready | - | - | Project B honors all eight nested canonical roles and poisoned default folders remain byte-identical. |
| T10 | `implementation-worker` | `group-3` | ready | - | - | Invalid, unresolved, ambiguous, malformed, and cross-project contexts perform zero target-project I/O. |
| T11 | `implementation-worker` | `group-3` | ready | - | - | The canonical path guard has zero unclassified hits and zero stale/unjustified classifications. |
| T12 | `qa-reviewer` | `group-1` | ready | - | - | Issue 102 and Issue 093 regression suites remain green. |
| T13 | `spec-architect` | `group-4` | ready | - | - | Spec consistency has zero errors; project validation is valid; lifecycle drift is `[]`. |
| T14 | `qa-reviewer` | `group-1` | ready | - | - | Full test discovery and `python3 scripts/release_check.py .` pass. |
| T15 | `qa-reviewer` | `group-1` | ready | - | - | GitHub publication happens only after review evidence and final verification are committed. |

## Isolation

- T01: `codex/109-canonical-project-context-consumer-convergence-t01`
- T02: `codex/109-canonical-project-context-consumer-convergence-t02`
- T03: `codex/109-canonical-project-context-consumer-convergence-t03`
- T04: `codex/109-canonical-project-context-consumer-convergence-t04`
- T05: `codex/109-canonical-project-context-consumer-convergence-t05`
- T06: `codex/109-canonical-project-context-consumer-convergence-t06`
- T07: `codex/109-canonical-project-context-consumer-convergence-t07`
- T08: `codex/109-canonical-project-context-consumer-convergence-t08`
- T09: `codex/109-canonical-project-context-consumer-convergence-t09`
- T10: `codex/109-canonical-project-context-consumer-convergence-t10`
- T11: `codex/109-canonical-project-context-consumer-convergence-t11`
- T12: `codex/109-canonical-project-context-consumer-convergence-t12`
- T13: `codex/109-canonical-project-context-consumer-convergence-t13`
- T14: `codex/109-canonical-project-context-consumer-convergence-t14`
- T15: `codex/109-canonical-project-context-consumer-convergence-t15`

## Merge Order

- T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09 → T10 → T11 → T12 → T13 → T14 → T15

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 1 touches shared state: **A1** Add strict context/root validation, canonical child paths, and canonical project-relative paths with RED/GREEN registry tests. | Files: scripts/project_registry.py, tests/test_project_registry.py
- Task 2 touches shared state: **A2** Add the machine-readable canonical path-literal classifier, reviewed exceptions, distribution checks, and RED/GREEN guard tests. | Files: scripts/canonical_path_guard.py, config/canonical-path-literals.json, tests/test_canonical_path_guard.py, scripts/validate_moduflow.py, scripts/release_check.py | Depends: A1
- Task 6 touches shared state: **C2** Scope sync and commit attribution Git commands to the canonical configured issue prefix with FakeRunner tests. | Files: scripts/project_sync.py, tests/test_project_sync.py, scripts/commit_resolution.py, tests/test_commit_resolution.py, tests/test_commit_resolution_parity.py | Depends: A1
- Task 7 touches shared state: **D1** Run the guard, focused/full suites, validation, drift, review handoff, acceptance review, release check, lifecycle updates, and publish the completed branch/PR. | Files: issues/109-canonical-project-context-consumer-convergence.md, specs/109-canonical-project-context-consumer-convergence/status.md, specs/109-canonical-project-context-consumer-convergence/review.md, specs/109-canonical-project-context-consumer-convergence/review-handoff.md, workspace/dashboard.md, workspace/roadmap.md, .moduflow/state.json, workspace/loop-state.json | Depends: A2,B2,C1,C2

## Next Command

`product:execute 109-canonical-project-context-consumer-convergence`
