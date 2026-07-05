---
description: Update or inspect upstream source references.
argument-hint: "[source id]"
---

# /product:sync

Keep the local repo, upstream skills/plugins, and host-native planning artifacts easy to update.

## Do

1. Run repo sync preflight before reading local artifacts. `project_sync.py` fetches remote refs itself (5s timeout, non-interactive) before comparing — no manual `git fetch` needed:

```bash
python3 scripts/project_sync.py <project-path>
```

If the fetch could not reach the remote (offline, timeout, auth), the result includes `fetched: false` and a `fetch_warning`, and a recommendation flags that the freshness numbers reflect the last local fetch, not the current remote — report that caveat rather than treating the numbers as current.

2. If the current upstream is gone, or `origin/main` is ahead, report that local files may be stale before summarizing issues/specs.
3. If the worktree is clean and the user approves, fast-forward the local checkout to the default remote branch. Do not auto-pull with local changes.
4. Explain source mode plainly: in `git-files` mode, ModuFlow issues live in repo files such as `issues/*.md`; the GitHub Issues tab may be empty unless `github-sync` is explicitly enabled.
5. Read `vendor.lock.json`.
6. Show current pins and available local vendor folders.
7. Pull or refresh upstream vendor sources only with user approval.
8. Keep local customizations in `overlays/` and `adapters/`.
9. Run `scripts/release_check.py .` after sync-sensitive changes.
10. Run `python3 scripts/antigravity_sync.py --host <host task.md> --git <git tasks.md>` to sync checkboxes between Antigravity and ModuFlow.

## Repo Sync Preflight

`project_sync.py` catches the stale-checkout class of bug:

- current branch's upstream is deleted (`[gone]`)
- current branch has no upstream, so local status cannot be trusted as a remote mirror
- local branch is behind `origin/main`
- `origin/main` contains issue files that are missing locally
- worktree is dirty, so fast-forward needs human review first
- the remote fetch itself failed (offline/timeout/auth) — reported via `fetched`/`fetch_warning`, so a stale-cache read is visible instead of silently treated as current

Recommended recovery path when clean:

```bash
git switch main
git merge --ff-only origin/main
```

Use a normal merge/rebase workflow instead when local commits or uncommitted changes are present.

## Antigravity Artifact Sync

To keep host-native planning artifacts (like `task.md` in Antigravity) synced with Git-native spec tracking (like `tasks.md` in ModuFlow):
```bash
python3 scripts/antigravity_sync.py --host /path/to/host/task.md --git /path/to/moduflow/specs/<issue>/tasks.md
```
This command performs a bidirectional status merge of checked (`[x]`), in-progress (`[/]`), and uncompleted (`[ ]`) checkboxes.

## Next

- `/product:doctor` after sync
- `/product:status` to resume work
