# Issue: `050-repo-sync-preflight`

**Status: done** — created 2026-06-29, started 2026-06-29, done 2026-06-29. Follows the 040/049 visibility incident where GitHub `main` had newer Git-file issues but the local workspace stayed on a deleted stale branch.

## Outcome

`product:sync` and status-adjacent flows detect stale local Git state before reading Git-file artifacts, so users do not mistake an old local branch for missing GitHub work.

## Why

ModuFlow uses `git-files` mode by default: issues live in `issues/*.md`, not necessarily GitHub Issues. When the local checkout is on a deleted branch or behind `origin/main`, local file reads can hide already-pushed issues. The previous `product:sync` documentation focused on vendors and Antigravity artifact checkbox sync, so it did not catch stale repo state.

## Scope

### In

- Add a repo sync preflight helper that reports current branch, upstream, gone upstream, ahead/behind counts, default branch status, and issue-file visibility.
- Update `product:sync` to run/recommend repo preflight before vendor sync.
- Update `product:status` guidance so stale branches and git-files mode are visible before artifact summaries.
- Add tests for gone upstream, behind default branch, and missing-local issue files that exist on `origin/main`.

### Out

- Automatic destructive cleanup of stale branches.
- Forcing GitHub Issue object creation.
- Changing the canonical issue storage model from `git-files` to `github-sync`.

## Acceptance Criteria

- `product:sync` documents repo sync preflight before vendor/Antigravity sync.
- A script/helper can be tested without a real network by injecting Git command output.
- The helper reports `upstream_gone` when the current upstream no longer exists.
- The helper reports when `origin/main` is ahead of local `main`.
- The helper reports issue IDs present on `origin/main` but missing locally.
- Status docs explain that GitHub Issues tab can be empty in `git-files` mode while repo files are canonical.
- `python3 -m unittest tests.test_project_sync -v` passes.
- `python3 scripts/release_check.py .` passes.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/050-repo-sync-preflight/spec.md`
- [x] plan → `specs/050-repo-sync-preflight/plan.md`
- [x] execute → `scripts/project_sync.py`, `tests/test_project_sync.py`, command docs
- [x] review → `specs/050-repo-sync-preflight/review.md`
- [x] test gone upstream detection
- [x] test default branch ahead detection
- [x] test remote-only issue visibility warning
- [x] test no-upstream dirty branch warning
- [x] document `product:sync` repo preflight
- [x] document `product:status` stale branch and `git-files` guidance

## Related Issues

- follows_up: `040-automatic-memory-candidate-capture`, `048-artifact-lifecycle-sync`, `049-bilingual-artifact-view`
- related: `021-git-binding-and-execution-backend`, `024-artifact-schema-and-doctor-gates`, `035-team-issue-branch-pr-workflow`

## Sessions

- 2026-06-29: User reported that work through 040 was on GitHub but not visible locally. Root cause: local checkout stayed on deleted `codex/034-memory-capture-sync` while `origin/main` had advanced to 049.

## Links

- Spec: `specs/050-repo-sync-preflight/spec.md`
- Status: `specs/050-repo-sync-preflight/status.md`
- Sessions: `sessions/050-repo-sync-preflight/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
