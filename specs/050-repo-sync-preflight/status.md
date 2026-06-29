# Status: Repo Sync Preflight

Issue: `050-repo-sync-preflight`

## State

- Created: 2026-06-29
- Phase: execute
- Owner: Codex

## Done

- Issue created.
- Spec created.
- Plan created.
- `tests/test_project_sync.py` added with gone upstream, behind default branch, and remote-only issue visibility tests.
- Review added no-upstream dirty branch coverage so a local work branch is not reported as clean.
- `scripts/project_sync.py` added with an injectable Git runner and JSON output.
- `commands/product-sync.md` now runs repo preflight before vendor/Antigravity sync.
- `commands/product-status.md` now calls out stale branches, remote-only issue files, and `git-files` mode.
- `python3 -m unittest tests.test_project_sync -v` passed (4 tests).
- `python3 scripts/release_check.py .` passed.

## Pending

- None.

## Next Command

`product:status`
