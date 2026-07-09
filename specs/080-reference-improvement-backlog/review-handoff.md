# Review Handoff: 080-reference-improvement-backlog

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/080-reference-improvement-backlog.md`
  - `specs/080-reference-improvement-backlog/spec.md`
  - `specs/080-reference-improvement-backlog/tasks.md`

### Implementation Tasks

- [x] T2: Implement `scripts/project_reference_backlog.py`.

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
python3 scripts/project_memory.py . --issue 080-reference-improvement-backlog
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-080-reference-improvement-backlog.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-080-reference-improvement-backlog.html`.

## Source Snapshot

- Issue bytes: 3871
- Spec bytes: 4848
- Status bytes: 944
