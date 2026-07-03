# Plan: Dashboard Database/List View

Issue: `056-dashboard-database-list-view`
Spec: `specs/056-dashboard-database-list-view/spec.md` · Design: `specs/056-dashboard-database-list-view/design.md` · Next: `product:execute 056-dashboard-database-list-view`

## Implementation Shape

Add an issue-table data path to the existing project dashboard renderer. Keep the current graph collectors and panel generation intact.

1. **Issue row collector** (`scripts/project_memory.py`)
   - Add `_collect_issue_table(root)`.
   - Scan `issues/*.md` deterministically by filename.
   - Reuse `_collect_issue_graph(root)` for title, status bucket, goal, and relationship data where useful.
   - Reuse `_issue_linked_memory(root)` for linked memory counts.
   - Parse `## Next Command` with tolerant markdown regex.
   - Derive `number`, `href`, `phase`, `artifact_coverage`, `attention_flags`, `relationship_count`, and `updated`.

2. **Artifact coverage detector**
   - Prefer file-existence checks over full artifact reads for table rows.
   - Cover: issue, spec, spec_ko, plan, plan_ko, tasks, tasks_ko, status, review, pr, release, human_review_ko.
   - Treat sidecars as signals, not gates.

3. **Attention flag builder**
   - V1 flags:
     - `missing_spec`
     - `missing_plan`
     - `no_next`
     - `no_review`
     - `no_pr`
     - `no_ko`
     - `blocked`
   - Keep labels Korean in the UI while row JSON keeps stable English keys.

4. **Project view template**
   - Add `const ISSUE_ROWS = __ISSUE_ROWS__;`.
   - Add third tab `이슈 DB` and make it the default tab.
   - Keep `이슈 그래프` and `지식 그래프` tabs working.
   - Support hashes:
     - `#issue-db`
     - `#issues`
     - `#memory`

5. **Static table UI**
   - Add compact toolbar:
     - search input
     - view chips: `전체`, `진행중`, `리뷰필요`, `막힘`, `누락있음`, `완료`
     - group select: `상태별`, `Goal별`, `없음`
     - sort select: `최근 업데이트`, `이슈 번호`, `상태`, `메모리 수`
   - Render default columns:
     - ID, Issue, Status, Phase, Next, Artifacts, Flags, Memory
   - Row click or explicit link opens `issue-<id>.html`.

6. **Dashboard command behavior**
   - Keep `--dashboard` output path unchanged: `memory/dashboard.html`.
   - Keep pre-generating `memory/issue-<id>.html` and memory panels.
   - Do not add runtime dependencies.

## Task Streams

### Stream A — Data Collection

- Add `_collect_issue_table(root)`.
- Add helper functions for:
  - issue number extraction
  - next-command parsing
  - phase inference from artifact coverage
  - artifact coverage
  - attention flags
  - updated date fallback
- Unit-test row extraction with temporary issue/spec/memory files.

### Stream B — HTML/UI Rendering

- Extend `PROJECT_VIEW_TEMPLATE`.
- Add `ISSUE_ROWS` payload.
- Add tab/show logic for `issue-db`.
- Add table render, search, filters, grouping, and sorting.
- Keep graph resize/fit behavior scoped to graph tabs only.

### Stream C — Verification And Docs

- Add/adjust tests in `tests/test_project_memory.py`.
- Generate `memory/dashboard.html` manually for visual inspection.
- Update command docs only if the visible `product:dashboard` behavior description is now outdated.
- Run release gates.

## Tests

Add focused tests in `tests/test_project_memory.py`:

- `_collect_issue_table` lists every issue file.
- row includes status, title, next command, artifact coverage, linked memory count, and row href.
- missing fields do not crash and produce fallback values/flags.
- artifact coverage detects English and Korean sidecars.
- `render_project_view` contains:
  - `이슈 DB`
  - `ISSUE_ROWS`
  - search/filter/sort controls
  - row-link pattern `issue-`
- existing tests for memory dashboard, issue graph, panel sidecars, and linked memory still pass.

## Manual QA

After implementation:

1. Run `python3 scripts/project_memory.py . --dashboard`.
2. Open `memory/dashboard.html`.
3. Confirm default tab is `이슈 DB`.
4. Search for `056`.
5. Filter `누락있음`.
6. Sort by issue number and memory count.
7. Open the 056 row and confirm `memory/issue-056-dashboard-database-list-view.html` loads.
8. Switch to `이슈 그래프` and `지식 그래프`; confirm existing graph behavior still works.

## Gates

- `python3 -m unittest tests.test_project_memory`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`
- Human visual check of generated `memory/dashboard.html`.

## Rollback

This is additive. Rollback is a single revert of the implementation commit:

- remove `_collect_issue_table` and helpers
- remove `ISSUE_ROWS` payload
- remove `이슈 DB` tab/table UI
- keep existing graph and issue-panel code unchanged

No Git artifact schema or external data migration is required.

## Out Of Scope

- Write-back editing from the dashboard.
- External service sync.
- Kanban/timeline implementation.
- Saved user preferences beyond optional URL hash state.
- Right-side peek panel.
