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
6. Create the lightweight project footprint only:
   - `.moduflow/config.json`
   - `.moduflow/state.json`
   - `issues/`
   - `specs/`
   - `knowledge/`
   - `workflow/`
   - `workspace/inbox.md`
   - `workspace/opportunities.md`
   - `workspace/roadmap.md`
   - `workspace/dashboard.md`
   - `workspace/loop-state.json`
   - `workspace/goal.md`
7. Do not create or copy tool/runtime folders into a normal target project: `commands/`, `scripts/`, `skills/`, `templates/`, `workers/`, `adapters/`, `vendor/`, `assets/`, `overlays/`, or `tests/`.
8. Seed the loop. Loop state MUST exist after `product:start` — a project without `loop-state.json` is an incomplete init. Set `next_command` to `product:goal` (or `product:inbox` when no goal is known yet).
9. Report the current state and next recommended command, always routing through the loop.

## Modes

- `git-files`: Git-tracked files are the source of truth. GitHub sync is off.
- `github-sync`: Git files remain the source of truth, and GitHub issues/PRs/releases are synced through `gh`.

## Output

- Project root
- Git repo status
- GitHub remote/auth status
- Created or reused lightweight project files (must include `workspace/loop-state.json`)
- Confirmation that ModuFlow tooling remains in the plugin/source package
- Next command: `product:goal` to set the active goal, then `product:loop` to keep advancing. Never end `product:start` without the loop seeded.
