---
description: Initialize ModuFlow in the current project.
argument-hint: "[project name or path]"
---

# /product:start

Initialize ModuFlow project state.

## Do

1. Confirm the project root and local rules.
2. Run Git preflight:
   - `git rev-parse --show-toplevel`
   - `git remote get-url origin`
   - `gh auth status` when GitHub issue/PR sync is needed
3. If the target is not a Git repo, ask whether to run `git init` or switch to an existing repo.
4. If Git exists but no `origin` exists, ask whether local Git-only mode is enough or a GitHub remote should be added.
5. If GitHub CLI is missing or unauthenticated, continue in file-backed mode unless the user wants GitHub issue/PR sync.
6. Create `.moduflow/config.json` and `.moduflow/state.json` if missing.
7. Create `issues/`, `specs/`, `workspace/inbox.md`, `workspace/opportunities.md`, `workspace/roadmap.md`, and `workspace/dashboard.md` if missing.
8. Report the current state and next recommended command.

## Modes

- `git-files`: Git-tracked files are the source of truth. GitHub sync is off.
- `github-sync`: Git files remain the source of truth, and GitHub issues/PRs/releases are synced through `gh`.

## Output

- Project root
- Git repo status
- GitHub remote/auth status
- Created or reused files
- Next command, usually `product:inbox` or `product:status`
