# Issue: `066-legacy-issue-status-migration`

**Status: backlog** — created 2026-07-05.

## Outcome

Every issue file in `issues/` carries the canonical `**Status: ...**` inline line (issue `048` schema), so `project_lifecycle.py` and issue listings report accurate states for the whole backlog — not just post-048 issues.

## Why

10 pre-048 issue files have no `Status:` line at all (`012`–`018`, `030`, `033`, `040`), so the lifecycle parser defaults them to `backlog` even though several are demonstrably shipped (`012`/`013` say "Shipped as 0.2.6 ✅" in their own body; `040` sits in the dashboard's Recently Completed list; `030` uses the old `Phase: done` block). This same drift class already caused real miscounts twice this session (`029`, `010` were fixed opportunistically when discovered). A one-time migration ends the recurring surprises.

## Scope

### In

- Read each of the 10 legacy files, determine the true state from body evidence (`Shipped as ...`, old `Phase:` blocks, dashboard/git history), and add the canonical `**Status: <state>**` line.
- Where the true state is genuinely unclear, mark `backlog` and note the ambiguity in a session line rather than guessing `done`.
- Re-run `project_lifecycle.py --drift` and `release_check.py` after migration.

### Out

- No rewriting of legacy issue bodies beyond the status line (history stays as written).
- No automated migration script — 10 files, human-judgment-per-file is cheaper and safer than codifying heuristics.

## Acceptance Criteria

- `grep -L "Status:" issues/*.md` returns empty.
- Issue counts in `product:issues`/`product:status` match dashboard reality.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `048-artifact-lifecycle-sync` (defined the canonical schema this migrates to)
- related: `060-cross-agent-output-format-convention` (scoped this out with "track separately if wanted" — this is that track)

## Sessions

- 2026-07-05: Registered during a full-repo audit; parser mis-reports 10 legacy files as backlog, of which at least 4 (`012`, `013`, `030`, `040`) are provably done.

## Links

- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
