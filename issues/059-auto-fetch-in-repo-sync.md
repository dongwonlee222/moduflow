# Issue: `059-auto-fetch-in-repo-sync`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.

## Outcome

ModuFlow automatically performs a safe `git fetch` in the background when running sync checks (`product:sync` and status preflights), ensuring that it compares local artifact states against the actual up-to-date remote state on GitHub without requiring manual terminal fetch commands.

## Why

Git is offline-first. Without running `git fetch` or `git pull`, the local Git database is completely unaware of new commits or branches pushed to the remote repository. Currently, `project_sync.py` only compares local files against local tracking branches (like `origin/main`), meaning that updates pushed by other collaborators or from other machines are completely invisible to the status tool until a human manually runs `git fetch`.

## Scope

### In

- Integrate a safe, automated `git fetch` (or `git remote update`) step at the beginning of `inspect_repo_sync()` in `scripts/project_sync.py`.
- Run the fetch command with a reasonable timeout (e.g., 5 seconds) to avoid hanging if the network is slow.
- Gracefully handle offline mode, network timeouts, or missing authentication credentials, logging a warning but continuing the sync check using the local tracking cache.
- Incorporate this check into `product:sync` and `product:status` workflow preflights.

### Out

- No automatic merging (`git pull`), rebasing, or hard checkouts of remote code.
- No modifying of local working files during the fetch phase.

## Acceptance Criteria

- Running `product:sync` automatically fetches remote tracking references.
- Sync diagnostics accurately detect remote-only commits or branches even if the user has not manually executed `git fetch` in the terminal.
- Test suite verifies that network failures/offline modes are handled gracefully without raising exceptions.
- `python3 scripts/release_check.py .` passes.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/059-auto-fetch-in-repo-sync/spec.md`
- [x] plan → `specs/059-auto-fetch-in-repo-sync/plan.md`, `specs/059-auto-fetch-in-repo-sync/tasks.md`
- [x] execute → `scripts/project_sync.py`, `tests/test_project_sync.py`, `commands/product-sync.md`, `commands/product-status.md`

## Related Issues

- related: `050-repo-sync-preflight`
- related: `053-vendor-freshness-gate`

## Sessions

- 2026-07-05: User pointed out that new remote branches (up to 058) were not visible to ModuFlow status/sync because there was no automatic background fetch.
- 2026-07-05: User confirmed the draft (originally authored via Antigravity) should be continued in Claude Code. Issue moved to active; spec drafting started.
- 2026-07-05: Wrote plan.md/tasks.md — RED-tests-first TDD plan for the fetch step, timeout handling, and doc updates.
- 2026-07-05: Implemented — `inspect_repo_sync()` now fetches (`git fetch --quiet`, 5s timeout, `GIT_TERMINAL_PROMPT=0`) before comparing refs; adds `fetched`/`fetch_warning` fields and a stale-cache recommendation on failure. 4 new tests (success/failure/timeout/`run_command` timeout conversion) + 4 existing tests updated with a passing fetch fixture. Full suite (169 tests) and `release_check.py` pass. `product:sync`/`product:status` docs updated to describe fetch as automatic. Done.

## Links

- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
