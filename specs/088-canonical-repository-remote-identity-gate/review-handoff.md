# Review Handoff: 088-canonical-repository-remote-identity-gate

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/088-canonical-repository-remote-identity-gate.md`
  - `specs/088-canonical-repository-remote-identity-gate/spec.md`
  - `specs/088-canonical-repository-remote-identity-gate/tasks.md`

### Implementation Tasks

- [x] A4 — Implement versioned evidence, reason codes, capabilities, and operation decisions.

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
python3 scripts/project_memory.py . --issue 088-canonical-repository-remote-identity-gate
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-088-canonical-repository-remote-identity-gate.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-088-canonical-repository-remote-identity-gate.html`.

## Source Snapshot

- Issue bytes: 6155
- Spec bytes: 17591
- Status bytes: 2278
