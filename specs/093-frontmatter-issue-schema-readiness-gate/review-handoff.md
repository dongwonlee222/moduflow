# Review Handoff: 093-frontmatter-issue-schema-readiness-gate

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/093-frontmatter-issue-schema-readiness-gate.md`
  - `specs/093-frontmatter-issue-schema-readiness-gate/spec.md`
  - `specs/093-frontmatter-issue-schema-readiness-gate/tasks.md`

### Implementation Tasks

- [x] A1 Lock legacy Markdown parity, sanitized BIZ fixtures, and the safe top-level YAML subset.
- [x] A2 Normalize versioned `0.1.0`, unversioned, unsupported, and projection-conflict inputs to `moduflow.issue.v2`.
- [x] B1 Enforce schema, state projection, dependency, definition-readiness, artifact, gate, and next-command precedence.
- [x] B2 Add `moduflow.issue-migration-report.v1` report-only CLI with before/after routing impact and zero writes.
- [x] C1 Move lifecycle state, priority, `depends_on`/`Blocked-by`, ready queue, dangling, cycle, and active-unmet drift to the shared normalizer.
- [x] C2 Put the structural gate before Issue 077 in loop routing, validation, and doctor recommendations.
- [x] C3 Move MCP and the current dashboard graph/Issue DB data model to normalized state, readiness, diagnostics, and recommended command.
- [x] D1 Keep generated/template issues canonical Markdown, ship the new module/fixtures, and prevent independent consumer parsers from returning.
- [x] E1 Prove cross-consumer parity for legacy Markdown and BIZ-033/038/039/040, then record focused-test and migration-report evidence.
- [x] E2 Pass spec consistency, full unittest, project validation, lifecycle drift, and release check before moving to review.

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
python3 scripts/project_memory.py . --issue 093-frontmatter-issue-schema-readiness-gate
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-093-frontmatter-issue-schema-readiness-gate.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-093-frontmatter-issue-schema-readiness-gate.html`.

## Source Snapshot

- Issue bytes: 6121
- Spec bytes: 16875
- Status bytes: 5075
