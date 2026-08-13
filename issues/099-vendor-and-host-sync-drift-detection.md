# Issue 099: Vendor and Host Sync Drift Is Detectable but Never Surfaced

**Status: backlog** — created 2026-08-08.
**Priority: p1**
**Blocked-by:**

## Summary

`vendor_freshness.py` and `project_doctor.py` already detect vendor drift and stale host installs, but nothing routes that signal into the normal workflow. All four GitHub vendor sources have been drifted for 26–37 days and the Codex host is 24 versions behind, with no surface reporting it.

## Source

- Type: finding from a dogfood audit of a downstream project (2026-08-08)
- Context: user was auditing whether ModuFlow covers their working-environment requirements; vendor freshness came up as an unverified assumption

## Problem

The vendoring model's premise is "compose verified external tools." That premise fails silently when the vendored copies age out.

**Measured 2026-08-08** (`python3 scripts/vendor_freshness.py vendor.lock.json`):

| source | last_synced | upstream | drift |
| --- | --- | --- | --- |
| `anthropic-skills` | 2026-07-01 | 2026-08-07 | 37일 |
| `anthropic-knowledge-work-plugins` | 2026-07-04 | drifted | ~35일 |
| `github-spec-kit` | 2026-07-02 | 2026-08-07 | 36일 |
| `superpowers` | 2026-07-02 | 2026-07-28 | 26일 |

**All four report `drifted`.** The tool works. Nothing calls it.

Three separate gaps produce this:

1. **`product:sync` does not check vendors.** Its description says "Update or inspect upstream source references," but `project_sync.py` never reads `vendor.lock.json` (0 occurrences). It only compares git remotes. A user running `product:sync` gets `"Repo sync preflight is clean."` while four sources are a month stale.

2. **`codex-*` sources carry no `last_synced` at all.** Four entries are `type: local-plugin` with only a `pin`; `vendor_freshness.py` skips them, so drift is structurally undetectable for half the source list. One is `pin: unpinned`.

3. **Host install drift is reported but not routed.** `project_doctor.py` does surface it:
   ```json
   "stale": [{"host": "codex", "installed": "0.3.17+codex.20260626145655", "repo": "0.3.41"}]
   ```
   The Claude Code host is on 0.3.41 while Codex is on 0.3.17 — the same plugin, two hosts, 24 versions apart. This defeats the cross-host parity the adapters exist to provide.

## Scope

- `scripts/project_sync.py` — include vendor freshness in the preflight result
- `vendor.lock.json` — record sync markers for `local-plugin` sources
- `scripts/vendor_freshness.py` — handle `local-plugin` type instead of skipping
- `commands/product-sync.md` — document what is and is not checked

## Do NOT touch

- The vendoring model itself (pin strategy, vendor/ layout)
- Auto-updating vendors — detection and reporting only; updates stay explicit
- `sync-vendors.sh` behavior

## Workflow Tasks

- [ ] spec → `specs/<issue-id>/spec.md`
- [ ] plan → `specs/<issue-id>/plan.md`
- [ ] execute → PR / commits
- [ ] review → review notes

## Acceptance Criteria

1. `python3 scripts/project_sync.py <path>` output includes a vendor freshness section listing every source in `vendor.lock.json` with its drift state.
2. A drifted vendor produces a recommendation string; a clean run says so explicitly rather than omitting the section.
3. `local-plugin` sources report a drift state or an explicit `unverifiable` reason — never silently absent.
4. `product:sync` documentation states which source types are checked and which are not.
5. Host install drift (`installed_plugin.stale`) appears in `product:sync` output, not only in `doctor`.

## Global Constraints

- Detection only. No automatic vendor updates.
- `unverifiable` is a valid reported state — do not round it up to clean.
- Offline runs must degrade to a warning, matching the existing `fetched: false` convention.

## Links

- Spec: `specs/<issue-id>/spec.md`
- Status: `specs/<issue-id>/status.md`
- Roadmap: `workspace/roadmap.md`
