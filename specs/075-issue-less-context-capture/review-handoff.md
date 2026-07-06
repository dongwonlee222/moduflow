# Review Handoff: 075-issue-less-context-capture

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/075-issue-less-context-capture.md`
  - `specs/075-issue-less-context-capture/spec.md`
  - `specs/075-issue-less-context-capture/tasks.md`

### Implementation Tasks

- [ ] A1. `scripts/linkage_check.py` module (branch/trailer resolution, path classification, declaration blame validation) + `tests/test_linkage_check.py` (FakeRunner; error-path tests mandatory) — depends: none
- [ ] A3. `.moduflow/humans.json` + `releases/no-issue-declarations.md` + blame validation + declaration listing in `human-review.ko.md` via `scripts/project_pr.py` + tests — depends: A1, A2
- [ ] B2. `scripts/project_promote.py` (record→issue, `promoted_to` in place, `Promoted-from` on issue, AI-field prefill or `TODO(blocking-execution)`) + `commands/product-promote.md` + `tests/test_project_promote.py` covering all 4 record kinds — depends: B1, C1
- [ ] C2. `commands/product-status.md` unpromoted-record count/oldest surfacing + 2-release retention archive (frontmatter `archived:`, file stays, queryable list) in `scripts/project_memory.py` or `project_retention.py` + tests — depends: C1, A3
- [ ] D1. 074 case writeup against v2 mechanisms + docs sweep (no v1 capture-tier references remain; `commands/product-release.md` gate description updated) — depends: Stream A, Stream B

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
python3 scripts/project_memory.py . --issue 075-issue-less-context-capture
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-075-issue-less-context-capture.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-075-issue-less-context-capture.html`.

## Source Snapshot

- Issue bytes: 5789
- Spec bytes: 12386
- Status bytes: 2687
