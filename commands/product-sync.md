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

In approval-sensitive hosts where Python subprocesses cannot write Git remote refs
(for example `.git/FETCH_HEAD` is blocked), run a top-level fetch first and then
skip the internal fetch:

```bash
git fetch
python3 scripts/project_sync.py <project-path> --no-fetch
```

2. Read `repository_identity` from the same preflight. Report the configured canonical repository/base/lifecycle and observed fetch/push/provider evidence before freshness. A remote name is only a hint; URL identity decides whether it is the intended repository.
3. If the current upstream is gone, or the configured canonical base ref is ahead, report that local files may be stale before summarizing issues/specs.
4. If the worktree is clean and the user approves, fast-forward the local checkout to the canonical base ref. Do not auto-pull with local changes or an identity mismatch.
5. Explain source mode plainly: in `git-files` mode, ModuFlow issues live in repo files such as `issues/*.md`; the GitHub Issues tab may be empty unless `github-sync` is explicitly enabled.
6. Read `vendor.lock.json`. Check freshness for `type: github` sources against their actual latest commit:

```bash
python3 scripts/vendor_freshness.py vendor.lock.json
```

Report drifted sources (never reviewed, or moved since `last_synced`) before showing pins. Informational only — this does not block anything or pull code. `local-plugin` sources are not checked (pinned by version string, not a git ref).

7. Show current pins and available local vendor folders.
8. Pull or refresh upstream vendor sources only with user approval. After an explicit review, record the reviewed commit as the new baseline:

```bash
python3 scripts/vendor_freshness.py vendor.lock.json --sync
```
9. Keep local customizations in `overlays/` and `adapters/`.
10. Run `scripts/release_check.py .` after sync-sensitive changes.
11. Run `python3 scripts/antigravity_sync.py --host <host task.md> --git <git tasks.md>` to sync checkboxes between Antigravity and ModuFlow.
12. If this sync needs to write locally (fast-forward, vendor `--sync` bookkeeping), run `python3 scripts/project_git_handoff.py <project-path>` first. A canonical identity mismatch blocks the write before commit/push/API fallback selection.

## Repo Sync Preflight

`project_sync.py` catches the stale-checkout class of bug:

- current branch's upstream is deleted (`[gone]`)
- current branch has no upstream, so local status cannot be trusted as a remote mirror
- local branch is behind `origin/main`
- `origin/main` contains issue files that are missing locally
- worktree is dirty, so fast-forward needs human review first
- the remote fetch itself failed (offline/timeout/auth) — reported via `fetched`/`fetch_warning`, so a stale-cache read is visible instead of silently treated as current
- another remote branch (not the current one, not `origin/main`) has a `Status: done` issue that isn't `done` on `origin/main` — reported via `unmerged_branch_work`, so finished work on a forgotten branch (e.g. from another tool/session) isn't invisible. Detection only — merging that branch is a separate, explicitly-confirmed decision.

Recommended recovery path when clean:

```bash
git switch main
git merge --ff-only origin/main
```

Use a normal merge/rebase workflow instead when local commits or uncommitted changes are present.

## Vendor Freshness

`vendor_freshness.py` extends the same drift-detection pattern (`048`, `062`) to external vendored sources: for each `type: github` entry in `vendor.lock.json`, it compares the recorded `last_synced.sha` against the actual latest commit on the pinned ref (via `gh api`). A source with no `last_synced` is reported drifted — never reviewed. `local-plugin` sources (pinned by version string, not a git ref) are skipped.

```bash
python3 scripts/vendor_freshness.py vendor.lock.json
```

This is informational only — it never pulls or merges upstream code (this repo has no vendored checkouts, only pattern-reference pins). After reviewing drifted sources, record the new baseline explicitly:

```bash
python3 scripts/vendor_freshness.py vendor.lock.json --sync
```

**Stamp rule (issue `067`)**: `--sync` may only be run after an actual content review of what changed upstream in the paths ModuFlow borrows — `last_synced` means "reviewed against this SHA", not "SHA recorded". A review updates the matching adapter's `reviewed:` block in `adapters/*.yaml` (what changed, what was absorbed, what was intentionally skipped) in the same commit as the stamp. Stamping without an adapter review note hides drift instead of tracking it — that is how the 2026-06-12→07-05 adapter staleness went unnoticed.

## Antigravity Artifact Sync

To keep host-native planning artifacts (like `task.md` in Antigravity) synced with Git-native spec tracking (like `tasks.md` in ModuFlow):
```bash
python3 scripts/antigravity_sync.py --host /path/to/host/task.md --git /path/to/moduflow/specs/<issue>/tasks.md
```
This command performs a bidirectional status merge of checked (`[x]`), in-progress (`[/]`), and uncompleted (`[ ]`) checkboxes.

## Next

- `/product:doctor` after sync
- `/product:status` to resume work
