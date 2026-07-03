# Tasks: Dashboard Database/List View

Issue: `056-dashboard-database-list-view`
Plan: `specs/056-dashboard-database-list-view/plan.md`

## Stream A — Data Collection

- [ ] Add `_collect_issue_table(root)` to `scripts/project_memory.py`.
- [ ] Add issue number extraction helper.
- [ ] Add `## Next Command` parser.
- [ ] Add artifact coverage helper using file-existence checks.
- [ ] Add phase inference from artifact coverage.
- [ ] Add attention flag helper.
- [ ] Add relationship count from issue graph edges.
- [ ] Add updated-date fallback.

## Stream B — Dashboard UI

- [ ] Embed `ISSUE_ROWS` JSON in `render_project_view(root)`.
- [ ] Add `이슈 DB` tab to `PROJECT_VIEW_TEMPLATE`.
- [ ] Make `이슈 DB` the default tab and support `#issue-db`.
- [ ] Preserve `#issues` and `#memory`.
- [ ] Add compact toolbar: search, view chips, group select, sort select.
- [ ] Add table renderer with default columns.
- [ ] Add status/attention filters.
- [ ] Add sort behavior.
- [ ] Add row link to `issue-<id>.html`.
- [ ] Ensure graph resize/fit runs only for graph tabs.

## Stream C — Tests

- [ ] Test `_collect_issue_table` row count and deterministic order.
- [ ] Test status/title/next command parsing.
- [ ] Test artifact coverage including Korean sidecars.
- [ ] Test attention flags for missing spec/plan/review/PR/KO/next.
- [ ] Test linked memory count.
- [ ] Test `render_project_view` includes `이슈 DB`, `ISSUE_ROWS`, toolbar controls, and row links.
- [ ] Re-run existing project memory tests.

## Stream D — Verification

- [ ] Run `python3 -m unittest tests.test_project_memory`.
- [ ] Run `python3 scripts/project_memory.py . --dashboard`.
- [ ] Visually confirm `memory/dashboard.html`.
- [ ] Run `python3 scripts/validate_project_artifacts.py .`.
- [ ] Run `python3 scripts/validate_moduflow.py .`.
- [ ] Run `python3 scripts/release_check.py .`.

## Stream E — Handoff

- [ ] Update issue session log with implementation summary.
- [ ] Update `workspace/roadmap.md` and `workspace/loop-state.json`.
- [ ] Prepare review artifacts after execute.
- [ ] Next command after implementation: `product:review 056-dashboard-database-list-view`.
