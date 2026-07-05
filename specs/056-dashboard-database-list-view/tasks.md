# Tasks: Dashboard Database/List View

Issue: `056-dashboard-database-list-view`
Plan: `specs/056-dashboard-database-list-view/plan.md`

## Stream A — Data Collection

- [x] Add `_collect_issue_table(root)` to `scripts/project_memory.py`.
- [x] Add issue number extraction helper.
- [x] Add `## Next Command` parser.
- [x] Add artifact coverage helper using file-existence checks.
- [x] Add phase inference from artifact coverage.
- [x] Add attention flag helper.
- [x] Add relationship count from issue graph edges.
- [x] Add updated-date fallback.

## Stream B — Dashboard UI

- [x] Embed `ISSUE_ROWS` JSON in `render_project_view(root)`.
- [x] Add `이슈 DB` tab to `PROJECT_VIEW_TEMPLATE`.
- [x] Make `이슈 DB` the default tab and support `#issue-db`.
- [x] Preserve `#issues` and `#memory`.
- [x] Add compact toolbar: search, view chips, group select, sort select.
- [x] Add table renderer with default columns.
- [x] Add status/attention filters.
- [x] Add sort behavior.
- [x] Add row link to `issue-<id>.html`.
- [x] Ensure graph resize/fit runs only for graph tabs.

## Stream C — Tests

- [x] Test `_collect_issue_table` row count and deterministic order.
- [x] Test status/title/next command parsing.
- [x] Test artifact coverage including Korean sidecars.
- [x] Test attention flags for missing spec/plan/review/PR/KO/next.
- [x] Test linked memory count.
- [x] Test `render_project_view` includes `이슈 DB`, `ISSUE_ROWS`, toolbar controls, and row links.
- [x] Re-run existing project memory tests.

## Stream D — Verification

- [x] Run `python3 -m unittest tests.test_project_memory`.
- [x] Run `python3 scripts/project_memory.py . --dashboard`.
- [x] Open `memory/dashboard.html` for human visual review.
- [x] Run `python3 scripts/validate_project_artifacts.py .`.
- [x] Run `python3 scripts/validate_moduflow.py .`.
- [x] Run `python3 scripts/release_check.py .`.

## Stream E — Handoff

- [x] Update issue session log with implementation summary.
- [x] Update `workspace/roadmap.md` and `workspace/loop-state.json`.
- [x] Prepare review artifacts after execute.
- [x] Next command after implementation: `product:review 056-dashboard-database-list-view`.
