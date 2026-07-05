# Spec: Detect Unmerged Branch Work

Issue: `062-detect-unmerged-branch-work`
Prev: `059-auto-fetch-in-repo-sync` · Next: `product:execute 062`

## Problem

`inspect_repo_sync()` (059) only answers "is my current branch stale vs `origin/main`." It has no visibility into other remote branches. This session hit exactly that gap: `issues/056-dashboard-database-list-view.md` and `issues/057-korean-human-review-packet.md` were `Status: done` with 22 commits and release evidence on `origin/codex/058-git-write-fallback-via-github-api`, and `project_sync.py` reported "clean" because that branch was never compared against anything.

## Users

- The user, working across sessions/machines/tools (Antigravity, Codex, Claude Code) that each may push their own branch — needs to know "is there finished work sitting on a branch I forgot about" without remembering branch names.
- `product:sync`/`product:status`, which should surface this alongside the existing freshness checks rather than requiring a separate manual `git branch -r` + `git log` investigation (what this session did by hand).

## Goals

- After fetching, scan remote branches other than the default remote for ones ahead of it.
- For branches that are ahead, check whether they contain an issue file with `Status: done` that is not `done` (or missing entirely) on the default branch — that is the actionable signal, not raw commit count.
- Reuse the existing status parser (`project_lifecycle._issue_status`) rather than writing a second regex — avoids recreating the exact multi-parser drift problem `060`/`062` exist because of.
- Surface findings as a new recommendation, same shape as `059`'s `fetched`/`fetch_warning` pattern.

## Non-Goals

- No automatic merge, checkout, or branch switch. Detection and reporting only.
- No content diff beyond the `Status:` line. If the user wants to merge, that's a separate, explicitly-confirmed action (as it was for `058` in this session).
- No continuous/background scanning — this runs once per `inspect_repo_sync()` call, same as every other check in that function.
- No special-casing branch naming conventions (e.g. `codex/*`) — scan all remote branches uniformly.

## Requirements

1. Add `find_unmerged_branch_work(runner, cwd, default_remote)` to `scripts/project_sync.py`:
   - List remote branches via `git for-each-ref --format=%(refname:short) refs/remotes`, excluding `<remote>/HEAD` and `default_remote` itself.
   - For each branch, get ahead count via `git rev-list --left-right --count {default_remote}...{branch}`; skip branches with `ahead == 0`.
   - For branches with `ahead > 0`, list issue ids on that branch (`git ls-tree -r --name-only {branch} issues`) and, for each, read `Status:` via `git show {ref}:issues/{id}.md` on both the branch and `default_remote`, using `project_lifecycle._issue_status` to parse.
   - Collect issue ids where the branch's status is `done` and the default remote's status is not `done` (including "issue file doesn't exist on default_remote at all").
   - Return `[{"branch": ..., "ahead": N, "done_issue_ids": [...]}, ...]`, omitting branches with no such issues.
2. `inspect_repo_sync()` calls this after the existing checks and adds `"unmerged_branch_work": [...]` to its result dict.
3. `format_recommendations()` adds one recommendation per finding: `"<branch> is N commits ahead of <default_remote> and has done issue(s) not done there: <ids>."`
4. No behavior change when there are no remote branches ahead of the default (the common case) — no extra recommendation, no extra noise.

## Alternatives Considered

- **Compare every file in the branch, not just `issues/*.md`**: rejected — status drift in an issue file is the specific, actionable signal; a branch could differ in many files (specs, tests) without representing "finished work I don't know about."
- **Only check branches matching a `codex/*`/`agent/*` naming pattern**: rejected — scoping by naming convention is brittle and this repo already has non-`codex/*` remote branches; scan all remote branches uniformly instead.

## Acceptance Criteria

- Fixture: two branches, one with `Status: done` for an issue that's `backlog`/absent on `default_remote` → reported with correct branch name and issue id.
- Fixture: a branch ahead of default but with no status-differing issues → not reported.
- Fixture: no other branches, or no branches ahead → `unmerged_branch_work` is `[]`, no extra recommendation.
- `python3 -m unittest tests.test_project_sync -v` passes, including new cases above.
- `python3 scripts/release_check.py .` passes.

## Risks

- Cost scales with (branches ahead of default) × (issues on that branch) `git show` calls. Acceptable for an occasional human-triggered check; not run in a hot loop. If this becomes slow on a repo with many stale branches, a future issue can add caching or a `--skip-branch-scan` flag — out of scope here.
- A branch's `issues/<id>.md` may not exist at the same path historically (renamed issue). Treated as "not found on that ref," which degrades to "status differs" rather than crashing — acceptable false-positive vs. a crash.

## Open Questions

- None — scope is deliberately narrow (detect + report only) per the Non-Goals above.

## Next Command

`/product:execute 062-detect-unmerged-branch-work`
