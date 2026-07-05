# Issue: `062-detect-unmerged-branch-work`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.

## Outcome

`product:sync`/`product:status` also detect completed (or in-progress) issue work sitting on remote branches other than the current one, not just freshness of the current branch against `origin/main` — so a user is told "issue 056 is `done` on `origin/codex/058-...`, not merged to main" instead of discovering it only by remembering the branch name themselves.

## Why

This session's `059-auto-fetch-in-repo-sync` fixed "is my current branch stale vs `origin/main`" but that's a different question from "does some other remote branch already contain finished work for an issue I think is still backlog." Both happened in the same session: after 059 shipped, the user asked to re-check sync, `project_sync.py` reported "clean" (correctly, for what it checks), but `issues/056-dashboard-database-list-view.md` and `issues/057-korean-human-review-packet.md` were actually `Status: done` on `origin/codex/058-git-write-fallback-via-github-api` — 22 commits, including release commits, invisible to any tool that only compares the current branch to `origin/main`.

## Scope

### In

- Extend `scripts/project_sync.py` (or add a sibling function) to list remote branches (`git branch -r` / `git for-each-ref refs/remotes`) and, for each branch that has commits not in `origin/main`, report:
  - branch name
  - ahead-of-`origin/main` commit count
  - which `issues/*.md` files differ in `Status:` between that branch and `origin/main` (the actionable signal — a branch merely having commits isn't itself interesting; a branch with a `Status: done` issue that's `backlog`/missing on `main` is)
- Surface this as a `recommendations` entry, same pattern as `059`'s `fetched`/`fetch_warning`: e.g. `"origin/codex/058-... has issue(s) done that are backlog on origin/main: 056, 057"`.
- Wire into `product:sync`/`product:status` docs alongside the existing repo-freshness checks.

### Out

- No automatic merge, checkout, or branch switch — detection and reporting only. Merge decisions stay explicit-confirmation, same as any other hard-to-reverse Git action.
- No deep content diff of the issue files beyond the `Status:` line — full diff review happens if/when the user decides to merge.
- Not scanning every branch unconditionally in perpetuity — cap to branches with commits ahead of `origin/main` (already-merged/stale branches aren't worth reporting).

## Acceptance Criteria

- Given a fixture with two branches where a feature branch has `Status: done` for an issue that's `backlog`/absent on the default branch, the check reports that branch + issue id.
- Given no such branches, the check reports nothing extra (no noise on the common case).
- Tests cover: no other branches, a branch with irrelevant commits only, a branch with a genuinely done-but-unmerged issue.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- follows_up: `059-auto-fetch-in-repo-sync`
- related: `050-repo-sync-preflight`
- caused-by: session incident, 2026-07-05 — `056`/`057` were fully implemented and released on `origin/codex/058-git-write-fallback-via-github-api` (22 commits) with zero visibility from `main`.

## Workflow Tasks

- [x] spec → `specs/062-detect-unmerged-branch-work/spec.md`
- [x] plan → `specs/062-detect-unmerged-branch-work/plan.md`
- [x] execute → `scripts/project_sync.py`, `tests/test_project_sync.py`, `commands/product-sync.md`, `commands/product-status.md`

## Sessions

- 2026-07-05: User asked to re-check sync after being told (via Antigravity, on another session) that 056/057 were already done on a branch. `project_sync.py` reported clean because it only compares against `origin/main`. Manual `git branch -r` + `git log origin/main..<branch>` found the real state. User asked that 059's sync capability extend to cover this.
- 2026-07-05: Meanwhile, `origin/codex/058-git-write-fallback-via-github-api` (containing 056/057/058) was merged into `main` directly (separate action). Implemented `find_unmerged_branch_work()` in `project_sync.py`: scans remote branches ahead of `origin/main`, reads `Status:` via `project_lifecycle._issue_status` (reused, not re-parsed) on both refs, reports branches with a `done` issue not `done` on `origin/main`. 3 new tests + full suite (183 tests) pass. Fixed a direct-CLI-invocation import bug (`python3 scripts/project_sync.py` vs `from scripts import project_sync`) found while smoke-testing. Docs updated. Done.

## Links

- Roadmap: `workspace/roadmap.md`
- Spec: `specs/062-detect-unmerged-branch-work/spec.md`
- Plan: `specs/062-detect-unmerged-branch-work/plan.md`

## Next Command

`/product:status`
