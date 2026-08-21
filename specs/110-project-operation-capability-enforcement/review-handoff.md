# Review Handoff: 110-project-operation-capability-enforcement

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/110-project-operation-capability-enforcement.md`
  - `specs/110-project-operation-capability-enforcement/spec.md`
  - `specs/110-project-operation-capability-enforcement/tasks.md`

### Implementation Tasks

- [x] **A1** Add the side-effect-free capability matrix, authorization decision, typed enforcing guard, denial serializer, fixtures, and RED/GREEN tests. | Files: scripts/project_operation.py, tests/test_project_operation.py, tests/project_operation_fixture.py
- [x] **A2** Attach additive policy fields to every resolver route and surface them in Doctor/portfolio reads. | Files: scripts/project_registry.py, tests/test_project_registry.py, scripts/project_doctor.py, tests/test_project_doctor.py, scripts/project_portfolio.py, tests/test_project_portfolio.py | Depends: A1
- [x] **A3** Add the AST-backed mutator inventory audit and distribution presence checks. | Files: scripts/project_operation_audit.py, config/project-operation-entrypoints.json, tests/test_project_operation_audit.py, scripts/validate_moduflow.py, tests/test_validation_distribution.py | Depends: A1
- [x] **B1** Guard core intake, knowledge, memory, workflow, lifecycle, and loop-state mutations; make candidate listing a pure read. | Depends: A1,A2,A3
- [x] **B2** Guard execution, review, convergence, worker-plan, and simulation report mutation modes. | Depends: A1,A2,A3
- [x] **B3** Guard production, profile, migration, promotion, reference, retention, issue-generation, Antigravity, and Spec Kit mutations. | Depends: A1,A2,A3
- [x] **C1** Guard dynamic Git/network/publication modes before runners while preserving repository identity and human gates. | Depends: B1,B2,B3
- [x] **C2** Authorize portfolio-control writes separately and close all mutator-audit gaps. | Depends: C1

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
python3 scripts/project_memory.py . --issue 110-project-operation-capability-enforcement
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-110-project-operation-capability-enforcement.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-110-project-operation-capability-enforcement.html`.

## Source Snapshot

- Issue bytes: 5177
- Spec bytes: 17086
- Status bytes: 3440
