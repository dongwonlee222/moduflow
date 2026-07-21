# Issue 092: Project Home Dashboard

**Status: backlog** — created 2026-07-16.
**Priority: p2**
**Blocked-by: `086-project-aware-production-library-dashboard`, `090-project-knowledge-and-artifact-registry`, `091-reproducible-analysis-runs-and-template-pack`**

## Summary

Add a project-home dashboard that shows current issues, recent analyses/reports, key Google Sheets, final conclusions, next actions, and last-updated dates in one project-scoped view.

## Source

- Type: user product direction
- Link: local Codex session and approved priority visualization, 2026-07-16
- Owner / decision maker: Dongwon Lee
- Current phase: backlog

## Problem

The existing dashboard exposes issues, graphs, and production records, but users still need to open several files to answer: what is active, what was recently analyzed, which Sheet is canonical, what did we conclude, and what happens next.

## Product Decision

- Extend the existing project-aware dashboard rather than creating a separate application.
- The home view is derived from canonical issue/state, knowledge, artifact, analysis-run, and decision records.
- Project selection from Issue 086 scopes every home element; no cross-project mixing is allowed.
- The home view summarizes decisions but does not replace `product:decision` records.

## Scope

### In

- A project-home tab or landing view showing current issues, blockers, recent analyses/reports, key Google Sheets, final conclusions, next actions, owners, and last-updated dates.
- Links from summaries to canonical issue, artifact, knowledge, report, Sheet, analysis-run, and decision records.
- Empty, stale, missing-link, and no-final-conclusion states.
- Project-scoped rendering and shareable URL state aligned with Issue 086.
- Responsive desktop/mobile review and Korean-first labels for the current user context.

### Out

- Browser-side editing or Git writes.
- Manually duplicating conclusions or next actions in dashboard-only storage.
- KPI calculation or analysis execution inside the dashboard.
- Cross-project detail views without explicit project selection.

## Acceptance Criteria

- One project-scoped screen shows all seven requested information groups.
- Every displayed conclusion, Sheet, report, and next action links to its canonical source.
- Last-updated values are source-derived and stale records are visibly marked.
- Switching projects cannot leave mixed-project issues, links, conclusions, or actions.
- Missing knowledge/artifact/run data produces actionable empty states.
- Existing Issue DB, graph, production records, and playbook views remain available.
- Desktop and mobile visual verification shows no clipped or overlapping content.
- Existing dashboard tests and `python3 scripts/release_check.py .` pass.

## Verification

- `python3 -m unittest tests.test_project_memory -v`
- `python3 scripts/project_memory.py . --dashboard`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`
- Playwright desktop/mobile screenshots for populated, empty, and stale project-home states

## Entry Points

- `scripts/project_memory.py`
- `commands/product-dashboard.md`
- `workspace/dashboard.md`
- `templates/portfolio/`
- `tests/test_project_memory.py`
- `specs/086-project-aware-production-library-dashboard/`

## Scope Fence

Do not add dashboard-only source data or browser-side writes. The home view is a read model over canonical project artifacts.

## Workflow Tasks

- [ ] spec → `specs/092-project-home-dashboard/spec.md`
- [ ] design → `specs/092-project-home-dashboard/design.md`
- [ ] prototype → `specs/092-project-home-dashboard/prototype.md`
- [ ] plan → `specs/092-project-home-dashboard/plan.md`
- [ ] execute → home read model, UI, links, empty/stale states, and tests
- [ ] review → `specs/092-project-home-dashboard/review.md`

## Related Issues

- follows_up: `036-portfolio-team-dashboard`, `044-product-dashboard-command`, `056-dashboard-database-list-view`, `086-project-aware-production-library-dashboard`, `090-project-knowledge-and-artifact-registry`, `091-reproducible-analysis-runs-and-template-pack`
- related: `085-project-production-records-and-playbooks`, `087-korean-github-pr-review-surface`
- blocks:
- blocked_by: `086-project-aware-production-library-dashboard`, `090-project-knowledge-and-artifact-registry`, `091-reproducible-analysis-runs-and-template-pack`

## Reference Implementations

- Renovate Dependency Dashboard as an issue-backed operational overview: `https://docs.renovatebot.com/key-concepts/dashboard/`
- Backstage project identity and project-scoped integrations: `https://backstage.io/docs/features/software-catalog/well-known-annotations/`

## Sessions

- 2026-07-16: User approved the project-home dashboard after repository safety and project knowledge foundations.

## Links

- Roadmap: `workspace/roadmap.md`
- Goal: `workspace/goal.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/22

## Next Command

`product:spec 092-project-home-dashboard`
