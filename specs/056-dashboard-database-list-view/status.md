# Status: Dashboard Database/List View

Issue: `056-dashboard-database-list-view`
Phase: execute complete; review next
Updated: 2026-07-03
Next: `product:review 056-dashboard-database-list-view`

## Implemented

- Added `_collect_issue_table(root)` to derive issue DB rows from Git-native issue, spec, and memory artifacts.
- Added issue number extraction, next command parsing, artifact coverage detection, phase inference, attention flags, relationship count, linked memory count, and updated-date fallback.
- Added `ISSUE_ROWS` to `render_project_view(root)`.
- Added the `이슈 DB` default tab to `memory/dashboard.html`.
- Added compact search/filter/sort/group controls.
- Added table rows with ID, Issue, Status, Phase, Next, Artifacts, Flags, and Memory columns.
- Preserved `이슈 그래프`, `지식 그래프`, existing graph behavior, and pre-generated issue/memory panels.

## Verification

- `python3 -m unittest tests.test_project_memory`
- `python3 -m unittest discover -s tests`
- `python3 scripts/project_memory.py . --dashboard`
- `python3 -m py_compile scripts/project_memory.py`
- generated HTML contains `이슈 DB`, `ISSUE_ROWS`, search controls, missing filter, and 056 issue row link
- generated dashboard script parses with Node `new Function`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`

## Notes

- Playwright browser automation could not run because the local Playwright browser binary was missing and the installed Chrome channel exited under sandbox constraints.
- The generated `memory/dashboard.html` was opened locally for human visual review.
