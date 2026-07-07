# Review Handoff: 072-lifecycle-hooks-automation

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/072-lifecycle-hooks-automation.md`
  - `specs/072-lifecycle-hooks-automation/spec.md`
  - `specs/072-lifecycle-hooks-automation/tasks.md`

### Implementation Tasks

- [ ] V1. Hook schema verification: official Claude Code plugin-hooks docs + superpowers shipped hooks → `specs/072-lifecycle-hooks-automation/hook-schema-notes.md` (hooks.json shape, SessionStart matchers, Stop payload, context-injection channel, timeout semantics, plugin-cache CWD behavior; doc URLs cited) — depends: none. **No hook code before this lands.**

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
python3 scripts/project_memory.py . --issue 072-lifecycle-hooks-automation
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-072-lifecycle-hooks-automation.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-072-lifecycle-hooks-automation.html`.

## Source Snapshot

- Issue bytes: 2714
- Spec bytes: 10212
- Status bytes: 2177
