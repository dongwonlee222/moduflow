# Spec: Auto Fetch in Repo Sync

Issue: `059-auto-fetch-in-repo-sync`
Prev: `050-repo-sync-preflight` · Next: `product:execute 059`

## Problem

`inspect_repo_sync()` in `scripts/project_sync.py` (issue 050) compares `HEAD` against `@{u}` and `origin/main` using only refs already present in the local Git database. Git never updates those refs on its own — a human has to run `git fetch` first. Today's status check (2026-07-05) required a manual `git fetch` before the ahead/behind counts and `remote_only_issue_ids` could be trusted; without it, remote work (issues up to `058`) would have looked identical to "nothing new," reproducing the same class of blind spot issue 050 was built to catch.

## Users

- A PM running `product:status`/`product:sync` who expects the freshness numbers to reflect GitHub right now, not whatever was last fetched.
- A coding agent (this one) preparing a status dashboard without a human in the loop to remember `git fetch`.

## Goals

- Make `inspect_repo_sync()` fetch remote refs itself before computing ahead/behind and `remote_only_issue_ids`.
- Fail soft: offline, timeout, or auth errors degrade to the existing local-ref comparison plus a visible warning — never an exception, never a hang.
- Keep the fetch read-only: refs only, no merge/rebase/checkout.

## Non-Goals

- No automatic `git pull`, rebase, or fast-forward — issue 050's manual-approval boundary for applying changes is unchanged.
- No change to the manual-approval gate for actually updating the local branch.
- No polling/background daemon; the fetch runs once per `inspect_repo_sync()` call.

## Requirements

1. `inspect_repo_sync()` runs `git fetch --quiet` (via the existing `runner` injection point) as its first Git call, before reading `@{u}`/`origin/main` state, so ahead/behind and `remote_only_issue_ids` reflect the fetched refs.
2. The fetch uses a bounded timeout (5s default) via `subprocess.run(..., timeout=...)`; a `subprocess.TimeoutExpired` is caught and treated as a fetch failure, not raised.
3. Non-zero fetch return code (offline, auth failure, no remote) does not abort the function — it falls back to whatever refs are already cached locally and continues the rest of the existing comparison logic unchanged.
4. The result dict gains:
   - `fetched: bool` — true only when the fetch command exited 0.
   - `fetch_warning: str | null` — human-readable reason when `fetched` is false (e.g. `"git fetch timed out after 5s"`, `"git fetch failed: <stderr>"`).
5. `format_recommendations()` prepends a recommendation when `fetched` is false, so a stale-cache read is visible instead of silently treated as current.
6. `product:sync` and `product:status` skill docs describe the fetch as automatic (already covered by calling `inspect_repo_sync()`) rather than instructing a manual `git fetch` step first.
7. Tests inject a fake `runner` that simulates: successful fetch, non-zero fetch, and `TimeoutExpired` — all three must leave `inspect_repo_sync()` returning a well-formed result.

## Acceptance Criteria

- Calling `inspect_repo_sync()` with a runner that raises `TimeoutExpired` on the fetch call returns `fetched: false`, a non-null `fetch_warning`, and still returns valid `branch`/`upstream`/`default_remote` fields computed from local refs.
- Calling it with a runner that returns fetch exit code 0 returns `fetched: true`, `fetch_warning: null`, and ahead/behind counts computed after the (simulated) fetch.
- Calling it with a runner that returns fetch exit code 1 (e.g. no network) returns `fetched: false` with a `fetch_warning` derived from stderr, and does not raise.
- `python3 -m unittest tests.test_project_sync -v` passes, including three new cases for the fetch outcomes above.
- `python3 scripts/release_check.py .` passes.

## Risks

- A slow or hung `git fetch` could stall every `product:status`/`product:sync` call; mitigated by the bounded timeout (Requirement 2).
- Some environments have no configured remote or run fully offline (CI, air-gapped); the soft-fail path (Requirements 3–4) must be the default, not an edge case.
- Repos with credential prompts (HTTPS without a cached credential helper) could hang waiting for input; `git fetch` should be run non-interactively (`GIT_TERMINAL_PROMPT=0` or equivalent) so it fails fast instead of blocking.

## Open Questions

- Whether to fetch a specific remote (`origin`) explicitly vs. the default remote, for repos with multiple remotes configured. Default to `origin` to match the rest of `project_sync.py`'s `origin/*` assumptions; revisit if a multi-remote project surfaces.

## Next Command

`/product:execute 059-auto-fetch-in-repo-sync`
