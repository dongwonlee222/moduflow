# Issue: `056-dashboard-database-list-view`

**Status: backlog** — created 2026-07-03.

## Outcome

ModuFlow dashboard supports both the current node graph and a database/list-style issue view, so users can scan, filter, sort, and group work like a lightweight Notion/Jira/Linear table without losing relationship graph navigation.

## Why

The current dashboard is useful for seeing issue and memory relationships, but graph-only navigation becomes uncomfortable when the user needs to answer practical PM questions:

- What is active, blocked, review-ready, or backlog?
- Which issue should I touch next?
- Which items have missing Korean sidecars, stale review, no PR handoff, or no owner?
- Which issues belong to a goal or dependency chain?

Notion, Jira, and Linear all pair visual/board views with list or database views. ModuFlow should do the same: the graph remains a relationship lens, while a database/table lens becomes the scanning and triage surface.

## Benchmark Summary

See `knowledge/benchmarks/2026-07-03-dashboard-db-list-view-benchmark.md`.

Initial lessons:

- Notion: one database can expose multiple views; table/list/board/timeline/calendar/gallery/chart each serve different reading goals, with per-view filters, sorts, groups, property visibility, and side peek.
- Jira: PM tracking expects multiple views of the same work, including boards, lists, timeline, and calendars, plus dependency management and status/risk reporting.
- Linear: durable custom views save filtered issue/project/initiative lists, can be shared/favorited, and can be created from filtered boards or lists.
- ModuFlow implication: `memory/dashboard.html` should evolve from graph-first only into a workbench with persistent tabs: `이슈 그래프`, `이슈 DB`, `칸반`, `타임라인`, `지식 그래프`.

## Scope

### In

- Add a list/table issue view to `memory/dashboard.html`, derived from `issues/*.md`, `specs/*`, `.moduflow/state.json`, `workspace/roadmap.md`, and available memory links.
- Include PM-useful columns: issue id, title, status, phase, goal, next command, priority/confidence when available, linked memory count, artifact coverage, PR/review status, updated date.
- Add filter/sort/group controls for status, goal, issue range, text search, and missing-artifact signals.
- Add click-through from table rows to the existing issue drill-down HTML.
- Keep graph view as the relationship-first lens; do not remove existing graph behavior.
- Preserve zero-backend behavior: derived static HTML, no hosted DB required.

### Out

- No external database dependency.
- No Notion/Jira/Linear sync.
- No write-back editing inside the dashboard in v1.
- No replacement of Git Markdown as canonical source.

## Acceptance Criteria

- `product:dashboard` generates a dashboard with at least `이슈 그래프`, `이슈 DB`, and `지식 그래프` tabs.
- The DB/list view shows all issue files with status, title, next command, artifact coverage, and linked memory count.
- Users can filter by status and search by issue id/title from static HTML.
- Table rows link to `memory/issue-<id>.html` when the drill-down exists or can be generated.
- Tests cover issue table data extraction and rendered HTML controls.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- follows_up: `045-issue-graph-visualization`
- follows_up: `047-issue-artifact-drilldown`
- related: `044-product-dashboard-command`
- related: `049-bilingual-artifact-view`
- related: `055-command-surface-onboarding`

## Sessions

- 2026-07-03: User observed that the dashboard needs more than node structure; it also needs a list/database-style view inspired by Notion, Jira, and Linear. Registered as backlog issue after initial benchmarking.

## Links

- Benchmark: `knowledge/benchmarks/2026-07-03-dashboard-db-list-view-benchmark.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:spec 056-dashboard-database-list-view`
