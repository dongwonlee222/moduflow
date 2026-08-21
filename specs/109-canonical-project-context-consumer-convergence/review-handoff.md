# Review Handoff: 109-canonical-project-context-consumer-convergence

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/109-canonical-project-context-consumer-convergence.md`
  - `specs/109-canonical-project-context-consumer-convergence/spec.md`
  - `specs/109-canonical-project-context-consumer-convergence/tasks.md`

### Implementation Tasks

- [x] **A1** Add strict context/root validation, canonical child paths, and canonical project-relative paths with RED/GREEN registry tests. | Files: scripts/project_registry.py, tests/test_project_registry.py
- [x] **A2** Add the machine-readable canonical path-literal classifier, reviewed exceptions, distribution checks, and RED/GREEN guard tests. | Files: scripts/canonical_path_guard.py, config/canonical-path-literals.json, tests/test_canonical_path_guard.py, scripts/validate_moduflow.py, scripts/release_check.py | Depends: A1
- [x] **B1** Converge knowledge, workflow, and project validation on one context with nested/poisoned-default contract tests. | Files: scripts/project_knowledge.py, tests/test_project_knowledge.py, scripts/project_workflow.py, tests/test_project_workflow.py, scripts/validate_project_artifacts.py, tests/test_validation_distribution.py | Depends: A1
- [x] **B2** Converge review, converge, worker orchestration, spec consistency, and reference backlog paths and generated links. | Files: scripts/project_review.py, tests/test_project_review.py, scripts/project_converge.py, tests/test_project_converge.py, scripts/worker_orchestrator.py, tests/test_worker_orchestration.py, scripts/spec_consistency.py, tests/test_spec_consistency.py, scripts/project_reference_backlog.py, tests/test_project_reference_backlog.py | Depends: A1,B1
- [x] **C1** Converge memory dashboards/drill-down and Spec Kit inputs/outputs while preserving stricter no-follow behavior. | Files: scripts/project_memory.py, tests/test_project_memory.py, scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py | Depends: A1,B1
- [x] **C2** Scope sync and commit attribution Git commands to the canonical configured issue prefix with FakeRunner tests. | Files: scripts/project_sync.py, tests/test_project_sync.py, scripts/commit_resolution.py, tests/test_commit_resolution.py, tests/test_commit_resolution_parity.py | Depends: A1
- [x] Full test discovery and `python3 scripts/release_check.py .` pass.

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
python3 scripts/project_memory.py . --issue 109-canonical-project-context-consumer-convergence
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-109-canonical-project-context-consumer-convergence.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-109-canonical-project-context-consumer-convergence.html`.

## Source Snapshot

- Issue bytes: 4800
- Spec bytes: 17186
- Status bytes: 3066
