# Release: 074-sync-fetch-sandbox-handling

Issue: `074-sync-fetch-sandbox-handling`
Date: 2026-07-06
Version: `0.3.11`

## Summary

Released a scoped sync preflight hotfix for approval-sensitive hosts. `project_sync.py` now supports `--no-fetch`, allowing agents to run a top-level `git fetch` first and then inspect fresh local refs without triggering a blocked Python subprocess fetch.

## Changes

- Added `fetch` parameter to `inspect_repo_sync`.
- Added CLI flag `--no-fetch`.
- Added `fetch_mode: skipped` output for explicit skip mode.
- Suppressed stale-fetch recommendations when fetch was intentionally skipped.
- Documented the workaround in `product:sync` and `product:status`.
- Added regression coverage.
- Created Issue 075 and a decision record for issue-less context capture.

## Verification

- `python3 -m unittest tests.test_project_sync -v` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Review Artifacts

- Korean human-review packet: `specs/074-sync-fetch-sandbox-handling/human-review.ko.md`
- PR handoff: `specs/074-sync-fetch-sandbox-handling/pr.md`
- Review notes: `specs/074-sync-fetch-sandbox-handling/review.md`
- Dashboard: `memory/dashboard.html`
- Issue drill-down: `memory/issue-074-sync-fetch-sandbox-handling.html`

## Rollback

Revert the commit for Issue 074. Normal auto-fetch behavior in `project_sync.py` will remain available in the prior version, but approval-sensitive hosts will again see the internal fetch warning.

## Next

`product:spec 075-issue-less-context-capture`
