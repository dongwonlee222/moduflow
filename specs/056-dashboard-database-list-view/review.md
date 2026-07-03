# Review: Dashboard Database/List View

Issue: `056-dashboard-database-list-view`
Reviewed: 2026-07-03
Result: passed; ready for PR
Next: `product:pr 056-dashboard-database-list-view`

## Scope Reviewed

- `scripts/project_memory.py`
- `tests/test_project_memory.py`
- `commands/product-dashboard.md`
- `specs/056-dashboard-database-list-view/*`
- Generated review surfaces:
  - `memory/dashboard.html`
  - `memory/issue-056-dashboard-database-list-view.html`

## Findings

No blocking or important issues found.

## Checks

### Implementation Review

- `_collect_issue_table(root)` deterministically lists issue files.
- Rows include issue id, number, title, status, goal, phase, next command, artifact coverage, linked memory count, relationship count, attention flags, updated date, and issue-panel href.
- Artifact coverage uses file-existence checks and treats Korean sidecars as signals.
- `render_project_view(root)` embeds `ISSUE_ROWS` and keeps existing issue/memory graph payloads.
- `이슈 DB` is the default tab, with `#issue-db`, `#issues`, and `#memory` hash routing.
- Issue detail panels now include `← 이슈 DB로 돌아가기`, linking to `dashboard.html#issue-db`.

### Spec / PM Review

- Matches the approved spec and design: Notion/Jira/Linear/GitHub-inspired list/database view over canonical Git files.
- Preserves zero-backend behavior.
- Does not introduce write-back editing, external sync, or a new database.
- Keeps existing graph and drill-down behavior intact.

### QA Review

- New tests cover issue table row extraction, artifact sidecars, attention flags, rendered controls, row links, and issue-panel DB return link.
- Existing project memory tests still pass.
- Full test suite passes.

## Verification

- `python3 -m unittest tests.test_project_memory` — passed.
- `python3 -m unittest discover -s tests` — passed, 167 tests.
- `python3 scripts/project_memory.py . --dashboard` — passed.
- `python3 scripts/project_memory.py . --issue 056-dashboard-database-list-view` — passed.
- `python3 -m py_compile scripts/project_memory.py` — passed.
- Generated HTML contains `이슈 DB`, `ISSUE_ROWS`, search controls, missing filter, 056 issue row link, and issue-panel DB return link.
- `python3 scripts/validate_project_artifacts.py .` — passed.
- `python3 scripts/validate_moduflow.py .` — passed.
- `python3 scripts/release_check.py .` — passed.

## Known Limitations

- Browser automation could not run in this environment: Playwright browser binary was missing and installed Chrome exited under sandbox constraints.
- The generated dashboard and issue drill-down were opened locally for human visual review instead.
- The `리뷰필요` filter currently includes rows with missing review or PR handoff; this is intentionally broad for v1 triage.

## Recommendation

Proceed to `product:pr 056-dashboard-database-list-view`.
