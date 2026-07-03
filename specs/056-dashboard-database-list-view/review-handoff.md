# Review Handoff: 056-dashboard-database-list-view

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/056-dashboard-database-list-view.md`
  - `specs/056-dashboard-database-list-view/spec.md`
  - `specs/056-dashboard-database-list-view/tasks.md`

### Implementation Tasks

- [x] Add `_collect_issue_table(root)` to `scripts/project_memory.py`.
- [x] Add issue number extraction helper.
- [x] Add artifact coverage helper using file-existence checks.
- [x] Add attention flag helper.
- [x] Run `python3 scripts/project_memory.py . --dashboard`.
- [x] Run `python3 scripts/validate_project_artifacts.py .`.
- [x] Run `python3 scripts/validate_moduflow.py .`.
- [x] Run `python3 scripts/release_check.py .`.
- [x] Update issue session log with implementation summary.
- [x] Next command after implementation: `product:review 056-dashboard-database-list-view`.

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

## Visual Handoff

Regenerate the ModuFlow dashboard and its issue drill-down before reporting completion.
The issue HTML is not a separate source artifact; it is a derived L2 view linked from the dashboard system.

```bash
python3 scripts/project_memory.py . --dashboard
```

```bash
python3 scripts/project_memory.py . --issue 056-dashboard-database-list-view
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-056-dashboard-database-list-view.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-056-dashboard-database-list-view.html`.

## Source Snapshot

- Issue bytes: 5419
- Spec bytes: 8506
- Status bytes: 1670
