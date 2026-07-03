# Release: Dashboard Database/List View

Issue: `056-dashboard-database-list-view`
Date: 2026-07-03
Release status: released locally; GitHub PR creation deferred by `gh` preflight

## Summary

Issue 056 is released in the Git-native workflow after human approval.

This release adds a Notion/Jira/Linear-inspired issue database view to the ModuFlow dashboard and improves the review surface so Korean-speaking reviewers can inspect the work without reading every English canonical artifact.

## Scope Released

- Dashboard `이슈 DB` tab.
- Static issue table with search, status filters, grouping, and sort controls.
- Date sorting by created/updated date.
- Artifact coverage and attention flags.
- Issue detail return link back to `dashboard.html#issue-db`.
- Korean issue descriptions in the DB list.
- Korean overview in every issue detail page.
- Korean human-review packet generation for PR/review gates.
- GitHub PR preflight before attempting `gh pr create`.

## Release Evidence

- Branch: `codex/056-dashboard-db-list-view-spec`
- Base: `main` at `771f8b8`
- Release branch range: `771f8b8..HEAD` on `codex/056-dashboard-db-list-view-spec`
- Local PR-ready marker: `local:056-dashboard-db-list-view-spec:review-ready`
- Human approval record: `workflow/records/2026-07-03-056-dashboard-database-list-view-approved.md`
- Korean review packet: `specs/056-dashboard-database-list-view/human-review.ko.md`

GitHub Draft PR creation was intentionally deferred because `python3 scripts/project_pr.py . --github-preflight` reports invalid `gh` tokens in the current Codex environment. Local release evidence remains canonical until GitHub API access is fixed.

## Verification

- `python3 scripts/project_memory.py . --dashboard` passed.
- `python3 -m unittest discover -s tests` passed, 175 tests.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Human Review

- Approver: Dongwon.
- Approval date: 2026-07-03.
- Review surface:
  - `memory/dashboard.html#issue-db`
  - `memory/issue-056-dashboard-database-list-view.html`
  - `specs/056-dashboard-database-list-view/human-review.ko.md`

## Rollback

If this release needs to be reverted before merge to `main`, abandon or reset the feature branch.

If this release has already been merged, revert the merge commit or revert the release branch range:

```bash
git revert 771f8b8..HEAD
python3 scripts/release_check.py .
```

## Post-Release Follow-Ups

- `057-korean-human-review-packet`: continue hardening Korean review packets beyond PR handoff.
- Future dashboard v2: saved filters, column visibility, kanban/timeline views, and side peek panel.

## Next

`product:status`
