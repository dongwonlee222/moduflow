# Spec: Repo Sync Preflight

Issue: `050-repo-sync-preflight`
Prev: `040-automatic-memory-candidate-capture`, `049-bilingual-artifact-view` · Next: `product:execute 050`

## Problem

ModuFlow reads Git-file artifacts from the current checkout. If the checkout is on a stale branch, deleted upstream branch, or a local `main` behind `origin/main`, the local files can make completed work look missing. In the 2026-06-29 incident, `origin/main` contained issues `037` through `049`, including `040`, but the current workspace was on `codex/034-memory-capture-sync` with an upstream marked gone.

`product:sync` did not catch this because its documented scope was vendor pins and Antigravity checkbox sync, not repo freshness.

## Users

- A PM asking "why is the issue missing on GitHub?" while actually looking at a stale local Git checkout.
- A maintainer running `product:sync` expecting local artifact state to match the remote repo.
- A coding agent preparing status from `issues/*.md`.

## Goals

- Make repo freshness visible before ModuFlow reads local artifact files.
- Keep sync safe: detect and recommend first; fast-forward only when explicitly approved by the host/user.
- Explain `git-files` mode clearly: GitHub repo files are canonical, GitHub Issues objects are optional mirrors.

## Non-Goals

- No automatic branch deletion.
- No forced `git pull` when the worktree is dirty.
- No GitHub Issue object sync.
- No migration away from Git-file artifacts.

## Requirements

1. Provide an importable helper, `scripts/project_sync.py`, that can inspect repo sync state from Git command output.
2. The helper reports:
   - current branch
   - upstream branch when configured
   - whether the upstream is gone
   - ahead/behind counts for current upstream
   - default remote branch, usually `origin/main`
   - local HEAD versus default remote ahead/behind counts
   - issue IDs present on default remote but missing in local checkout
   - worktree dirty state
   - human-readable recommendations
3. `product:sync` docs run repo preflight first, then vendor and Antigravity sync.
4. `product:status` docs show stale branch and `git-files` guidance before summarizing issues.
5. Tests cover the 2026-06-29 failure mode.

## Acceptance Criteria

- On a branch whose upstream is gone, the helper returns `upstream_gone: true` and recommends switching to the default branch or choosing an active work branch.
- When local `main` is behind `origin/main`, the helper reports the behind count and recommends fast-forwarding if the worktree is clean.
- When `origin/main` has `issues/040-...md` and local checkout does not, the helper reports `remote_only_issue_ids: ["040-..."]`.
- Docs clarify that an empty GitHub Issues tab is not a missing ModuFlow issue in `git-files` mode.
- Release checks pass.

## Risks

- Git commands may fail in non-Git folders. The helper should return a structured warning, not crash.
- Some repos use `master` or a custom default branch. The helper should prefer `origin/HEAD`, then fall back to `origin/main`.
- Worktrees may be dirty. The helper should avoid recommending automatic fast-forward when local changes exist.

## Open Questions

- Whether a future `product:sync --apply` should perform the fast-forward itself. For this issue, the command only documents approval-gated application.

## Next Command

`/product:execute 050-repo-sync-preflight`
