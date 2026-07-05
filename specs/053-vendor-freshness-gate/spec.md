# Spec: Vendor Freshness Gate

Issue: `053-vendor-freshness-gate`
Prev: `048-artifact-lifecycle-sync`, `062-detect-unmerged-branch-work` · Next: `product:execute 053`

## Problem

`vendor.lock.json` pins four `type: github` sources to `"main"` with no recorded sync marker. Nothing detects when upstream has moved since the pin was last reviewed — a user has to manually check GitHub. This is the same class of blind spot `048` fixed for internal issue/dashboard state and `062` fixed for unmerged branch work, applied to external vendored sources instead.

## Users

- The user, periodically wanting to know "did any of the design-pattern sources I copied conventions from move since I last looked."
- `product:sync`, which already has a "pull or refresh upstream vendor sources only with user approval" step but nothing to trigger that approval prompt with actual evidence.

## Goals

- Report, per `type: github` vendor source, the last-known commit (from `vendor.lock.json`) vs. the current commit on the pinned ref.
- Record a `last_synced` marker (commit sha + date) per source once reviewed, so the next check has a baseline.
- Surface a summary in `product:sync` output.
- Handle network/API failures (rate limit, no `gh` auth, unreachable) without crashing — same soft-fail posture as `059`'s fetch handling.

## Non-Goals

- No cloning/copying upstream repo content into `vendor/<id>/` — this repo has no such checkouts today (`vendor/` contains only a README describing the *pattern*, per its own text). That would be new infrastructure, not freshness detection.
- No change to `local-plugin` sources (`codex-product-design`, `codex-data-analytics`) — pinned by version string, not a git ref; a GitHub commit-based check doesn't apply.
- No blocking gate — informational only, matching the issue's explicit scope.
- No updating installed Claude Code plugins/marketplaces on the user's machine — out of this repo entirely.

## Requirements

1. `scripts/vendor_freshness.py` exposes `check_vendor_freshness(lock_path, runner=None)`:
   - Read `vendor.lock.json`.
   - For each source with `type == "github"`: parse `owner/repo` from `url`, run `gh api repos/{owner}/{repo}/commits/{pin}` (via an injectable `runner`, same DI pattern as `project_sync.py`) to get the latest commit sha + date on the pinned ref.
   - Compare against `source.last_synced.sha` (absent → treat as drifted, never reviewed).
   - Skip `type != "github"` sources entirely (Non-Goals).
   - Return a per-source result: `{id, drifted: bool, last_synced_sha, latest_sha, latest_date, error}` (`error` set instead of raising on API failure).
2. `scripts/vendor_freshness.py --sync` writes `last_synced: {sha, date}` into `vendor.lock.json` for every successfully-checked source (explicit review action, not automatic).
3. `product:sync` docs call this check and print a one-line-per-source summary before the existing vendor pin/pull steps.
4. Reuse `gh api` via the CLI (already authenticated in this environment) rather than embedding a token — same reasoning as `git` being shelled out to elsewhere in this codebase.

## Alternatives Considered

- **Use `requests`/raw GitHub REST API with a token**: rejected — `gh api` is already authenticated in this environment and used nowhere else in this codebase needing extra dependency/token management; shelling out matches the existing `git`-via-subprocess convention in `project_sync.py`.
- **Vendor the actual upstream code now**: rejected — bigger scope than "detect drift," no current consumer reads from `vendor/<id>/` (adapters point at external filesystem paths, e.g. `local_path` in `adapters/superpowers.yaml`), and the issue's own Non-Goals exclude it.

## Acceptance Criteria

- Fixture: source with no `last_synced` → reported as drifted (never reviewed).
- Fixture: source with `last_synced.sha` matching the (fake) latest → not drifted.
- Fixture: source with `last_synced.sha` differing from latest → drifted, both shas/dates in the result.
- Fixture: `gh api` call fails (non-zero exit) → `error` set on that source, no exception, other sources still checked.
- `--sync` updates `last_synced` in `vendor.lock.json` for checked sources.
- `python3 -m unittest tests.test_vendor_freshness -v` passes.
- `python3 scripts/release_check.py .` passes.

## Risks

- `gh api` rate limits on unauthenticated or heavily-used tokens — surfaced via the same `error` field as any other failure, not a special case.
- Parsing `owner/repo` from `url` assumes a `https://github.com/{owner}/{repo}` shape, matching all four current `type: github` entries; a different URL shape degrades to an `error` entry rather than crashing.

## Open Questions

- None.

## Next Command

`/product:execute 053-vendor-freshness-gate`
