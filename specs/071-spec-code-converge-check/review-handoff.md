# Review Handoff: 071-spec-code-converge-check

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/071-spec-code-converge-check.md`
  - `specs/071-spec-code-converge-check/spec.md`
  - `specs/071-spec-code-converge-check/tasks.md`

### Implementation Tasks

- [ ] A1. `scripts/project_converge.py --evidence`: commit resolution (trailer + merge-subject), current-file bundle with caps + explicit `truncated`, single-parse of AC (checkbox + prose) and plan Global Constraints, evidence JSON per schema, non-zero exit on git/bundle failure in both output modes + `tests/test_project_converge.py` (FakeRunner) — depends: none

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
python3 scripts/project_memory.py . --issue 071-spec-code-converge-check
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-071-spec-code-converge-check.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-071-spec-code-converge-check.html`.

## Source Snapshot

- Issue bytes: 2588
- Spec bytes: 12433
- Status bytes: 2109
