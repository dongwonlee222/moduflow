# Status: Dashboard Database/List View

Issue: `056-dashboard-database-list-view`
Phase: released locally
Updated: 2026-07-03
Next: `product:status`

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

## Review

- Result: passed; human approved 2026-07-03.
- Review artifact: `specs/056-dashboard-database-list-view/review.md`.
- Review handoff: `specs/056-dashboard-database-list-view/review-handoff.md`.
- PR handoff: `specs/056-dashboard-database-list-view/pr.md`.
- Korean human-review packet: `specs/056-dashboard-database-list-view/human-review.ko.md`.
- No blocking or important review findings.

## Human Approval

- Approver: Dongwon.
- Approved: 2026-07-03.
- Approval record: `workflow/records/2026-07-03-056-dashboard-database-list-view-approved.md`.
- Next command: `product:status`.

## Release

- Release artifact: `specs/056-dashboard-database-list-view/release.md`.
- Release status: released locally after human approval.
- GitHub PR creation remains deferred by `gh` preflight failure in the current Codex environment.

## PR State

- Branch: `codex/056-dashboard-db-list-view-spec`.
- Local PR-ready marker: `local:056-dashboard-db-list-view-spec:review-ready`.
- GitHub PR creation attempted on 2026-07-03 with `gh pr create --draft`, but GitHub API access failed with `error connecting to api.github.com`.
- Follow-up prevention added: `python3 scripts/project_pr.py . --github-preflight` now checks `gh auth status` and `gh api rate_limit` before any Draft PR creation attempt.
- Current Codex environment preflight reports invalid `gh` tokens, so future `product:pr` runs should stay in local PR-ready mode until authentication/network access is fixed.
- Keep local PR-ready artifacts as the review source until GitHub API access is available.

## Notes

- Playwright browser automation could not run because the local Playwright browser binary was missing and the installed Chrome channel exited under sandbox constraints.
- The generated `memory/dashboard.html` was opened locally for human visual review.
