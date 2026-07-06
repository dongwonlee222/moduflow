# Issue 074: Sync Fetch Sandbox Handling

**Status: done** — created 2026-07-06, started 2026-07-06, done 2026-07-06.
**Priority: p1**

## Summary

`project_sync.py` should support approval-sensitive hosts where a top-level `git fetch` is allowed but a Python subprocess `git fetch --quiet` cannot write `.git/FETCH_HEAD`.

## Source

- Type: user-reported operational warning
- Link: local Codex session
- Date: 2026-07-06

## Opportunity

ModuFlow recently added automatic fetch in repo sync preflight, but Codex sandboxing can block the internal subprocess fetch even after a direct `git fetch` succeeds. The result is a noisy `fetch_warning` that makes a clean, current checkout look suspect.

## Scope

### In

- Add an explicit `--no-fetch` mode for hosts that already ran a top-level fetch.
- Preserve the default auto-fetch behavior for normal hosts.
- Document the Codex/approval-sensitive host workaround in `product:sync` and `product:status`.
- Cover the behavior with focused tests.

### Out

- Changing Codex sandbox policy.
- Removing automatic fetch from normal `project_sync.py` usage.
- Auto-escalating from inside Python.

## Acceptance Criteria

- `python3 scripts/project_sync.py . --no-fetch` skips internal fetch and does not emit the stale-fetch recommendation.
- Existing fetch failure and timeout warnings still work in default mode.
- Command docs explain the top-level `git fetch` + `--no-fetch` path.
- `python3 -m unittest tests.test_project_sync -v` passes.
- `python3 scripts/release_check.py .` passes.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec/plan → not required; scoped hotfix captured in this issue
- [x] execute → `scripts/project_sync.py`, `commands/product-sync.md`, `commands/product-status.md`
- [x] test → `tests/test_project_sync.py`
- [x] status → `specs/074-sync-fetch-sandbox-handling/status.md`
- [x] review → `specs/074-sync-fetch-sandbox-handling/review.md`

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `059-auto-fetch-in-repo-sync`, `050-repo-sync-preflight`
- supersedes:
- related: `058-git-write-fallback-via-github-api`

## Sessions

- 2026-07-06: User asked why `project_sync.py` warned after local `main` matched GitHub. Root cause: Codex allows top-level `git fetch` but blocks Python subprocess writes to `.git/FETCH_HEAD`.

## Links

- Status: `specs/074-sync-fetch-sandbox-handling/status.md`
- Review: `specs/074-sync-fetch-sandbox-handling/review.md`
- Release: `specs/074-sync-fetch-sandbox-handling/release.md`
- Human Review: `specs/074-sync-fetch-sandbox-handling/human-review.ko.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:spec 075-issue-less-context-capture`
