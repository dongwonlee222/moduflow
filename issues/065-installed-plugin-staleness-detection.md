# Issue: `065-installed-plugin-staleness-detection`

**Status: backlog** — created 2026-07-05.

## Outcome

ModuFlow detects when the *installed* plugin copy (Claude Code marketplace cache / Codex personal cache) has fallen behind the repo's own `.claude-plugin/plugin.json` version, and surfaces that in `product:doctor`/`product:sync` output with the exact update commands — so a stale install is caught automatically instead of by the user noticing old behavior.

## Why

Found live on 2026-07-05: the repo was at `0.3.2` but the installed `moduflow@moduflow` Claude Code plugin was pinned at `0.2.6` (8 releases behind), and the marketplace clone at `0.2.15`. Nothing in the toolchain auto-updates these — `claude plugin marketplace update` + `claude plugin update` must be run by hand, and no ModuFlow check compares installed vs repo version. The same staleness class was already solved for *external* sources (`053-vendor-freshness-gate`) and *remote branches* (`062`), but not for ModuFlow's own installed copies — the tool that detects everyone else's drift couldn't see its own.

## Scope

### In

- A check (likely in `project_doctor.py`, reusing the injectable-runner pattern) that compares `.claude-plugin/plugin.json`'s version against:
  - `~/.claude/plugins/installed_plugins.json`'s `moduflow@moduflow` entry (when present on this machine)
  - `~/.codex/plugins/cache/personal/moduflow/<version>` (when present)
- Report staleness as a doctor warning (not a hard failure — the repo checkout is still valid) with the exact `claude plugin marketplace update moduflow && claude plugin update moduflow@moduflow` / `register_codex_personal_marketplace.py` recovery commands.
- Skip silently when the plugin isn't installed on this machine (contributor without an install).
- Tests using a fake home directory layout.

### Out

- No auto-running the update commands — installing/updating a plugin restarts-to-apply and mutates user-level state; recommend only.
- No general check for *other* installed plugins (telegram, warp, ...) — only ModuFlow's own copies.
- No CI-side check — this is a local-machine concern by nature.

## Acceptance Criteria

- With a fake `installed_plugins.json` pinning an older version, doctor output includes a staleness warning naming both versions and the update commands.
- With versions equal, no warning.
- With no install present, no warning and no error.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `053-vendor-freshness-gate` (same drift-detection pattern, external sources)
- related: `010-codex-version-sync-fix` (keeps the two manifests aligned; this issue covers the installed copies)
- related: `061-auto-commit-push-on-issue-done` (auto-push makes releases frequent, which makes silent install staleness worse)

## Sessions

- 2026-07-05: Registered during a plugin-side audit after finding the installed plugin 8 releases behind the repo (0.2.6 vs 0.3.2). Fixed the immediate staleness by hand (`marketplace update` + `plugin update`, both now 0.3.2); this issue automates the *detection* so it can't silently recur.

## Links

- Roadmap: `workspace/roadmap.md`
- Upgrade commands: `docs/upgrade-guide.md`

## Next Command

`/product:status`
