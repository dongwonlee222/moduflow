# Issue: `053-vendor-freshness-gate`

**Status: done** — created 2026-07-03, started 2026-07-05, done 2026-07-05.

## Outcome

ModuFlow detects drift between `vendor.lock.json` pinned upstream sources and actual upstream activity, and surfaces it as a gate — the same pattern Issue 048 applied to internal planning artifacts, extended to external vendored sources.

## Why

`vendor.lock.json` pins four GitHub sources (`anthropic-skills`, `anthropic-knowledge-work-plugins`, `github-spec-kit`, `superpowers`) to `"main"` with no recorded sync marker. The file was last touched 2026-06-12; all four upstream repos had commits within the last 1-2 days as of 2026-07-02, including a `superpowers` minor release (v6.1.0) and four `spec-kit` patch releases. `product:sync` can refresh vendor sources with approval, but nothing currently detects that drift has accumulated — a user has to manually check GitHub to notice.

## Scope

### In

- A freshness check (script) that reads `vendor.lock.json`, fetches each `type: github` source's latest commit/release via the GitHub API, and compares against a recorded `last_synced` marker per source.
- Add a `last_synced` (commit sha + date) field to `vendor.lock.json`, written when a source is reviewed/refreshed.
- Surface drift count and per-source staleness in `product:sync` and/or `product:doctor` output.
- Tests covering: no drift, drift detected, missing/unreachable source handled gracefully.

### Out

- No automatic pulling or merging of upstream content into `overlays/`/`adapters/`.
- No change to the two `local-plugin` sources (`codex-product-design`, `codex-data-analytics`) — those are pinned by version string, not commit sha, and are out of scope for this GitHub-based check.
- No blocking gate that prevents work — informational surface only, same posture as 048's soft signals before the drift gate was added.

## Acceptance Criteria

- Freshness check script reports last-known vs. latest for each `type: github` vendor source.
- `vendor.lock.json` gains a `last_synced` field per source, updated on explicit review.
- `product:sync` (or `product:doctor`) output includes a vendor freshness summary.
- New unit tests pass; `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `048-artifact-lifecycle-sync` (drift-gate pattern this extends to vendor sources)
- related: `050-repo-sync-preflight` (repo-freshness precedent for `product:sync`)

## Workflow Tasks

- [x] spec → `specs/053-vendor-freshness-gate/spec.md`
- [x] plan → `specs/053-vendor-freshness-gate/plan.md`
- [x] execute → `scripts/vendor_freshness.py`, `tests/test_vendor_freshness.py`, `commands/product-sync.md`

## Sessions

- 2026-07-03: User asked what to improve next; review of `vendor.lock.json` found no drift-detection mechanism despite ~3 weeks of unreviewed upstream activity across all four GitHub sources. Registered as backlog issue only, per user's choice — implementation deferred.
- 2026-07-05: User asked to implement, then use it to refresh `vendor.lock.json`'s `last_synced` markers. Confirmed via AskUserQuestion: scope is the freshness check + lock-file bookkeeping only — not vendoring actual upstream code into `vendor/` (no code copy exists in this repo today) and not updating installed Claude Code plugins (a separate, out-of-repo concern).
- 2026-07-05: Implemented `scripts/vendor_freshness.py` (`gh api` via the same injectable-runner DI pattern as `project_sync.py`), 6 new tests, `product:sync` docs updated. Ran for real against the live `vendor.lock.json`: all four GitHub sources had never been reviewed — `--sync` recorded their current commit SHAs as the baseline. Also fixed a lifecycle conflict found along the way: issue `058` was left `active` from the earlier merge while unstarted (still at plan phase) — moved back to `backlog` since work shifted here. Full suite (189 tests) and `release_check.py` pass. Done.

## Links

- Roadmap: `workspace/roadmap.md`
- Spec: `specs/053-vendor-freshness-gate/spec.md`
- Plan: `specs/053-vendor-freshness-gate/plan.md`

## Next Command

`/product:status`
