# Review Handoff: 085-project-production-records-and-playbooks

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/085-project-production-records-and-playbooks.md`
  - `specs/085-project-production-records-and-playbooks/spec.md`
  - `specs/085-project-production-records-and-playbooks/tasks.md`

### Implementation Tasks

- [x] **A1. Parser + templates** — create `scripts/project_production.py`, `templates/production/{record,playbook}.md`, and parser RED/GREEN tests; produces normalized record/playbook interfaces — depends: none.
- [x] `python3 scripts/spec_consistency.py . --issue-id 085-project-production-records-and-playbooks` — 0 findings.
- [x] `python3 scripts/validate_moduflow.py .` — 137 required files checked.
- [x] `python3 scripts/validate_project_artifacts.py .` — valid; one pre-existing optional-memory warning.
- [x] `python3 scripts/release_check.py .` — valid; all gates passed.

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
python3 scripts/project_memory.py . --issue 085-project-production-records-and-playbooks
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-085-project-production-records-and-playbooks.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-085-project-production-records-and-playbooks.html`.

## Source Snapshot

- Issue bytes: 6076
- Spec bytes: 17131
- Status bytes: 1241
