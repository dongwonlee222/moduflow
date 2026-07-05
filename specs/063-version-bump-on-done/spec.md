# Spec: Version Bump On Done

Issue: `063-version-bump-on-done`
Prev: `061-auto-commit-push-on-issue-done` · Next: `product:execute 063`

## Problem

`.claude-plugin/plugin.json`'s version has not moved (`0.2.15`) across 57 commits and 7 completed issues in this session alone. `docs/release-checklist.md` says to bump it "when releasing a new plugin version" but never defines what counts as a release, so it's skipped by default — the same class of gap `061` closed for git push (a manual step that quietly never happens without an explicit trigger).

## Users

- The user, who expects the plugin version to reflect what actually shipped, without having to remember to ask for a bump after every issue.
- Anything reading `.claude-plugin/plugin.json`'s version as a signal of what's installed (`claude plugin list`, the Codex manifest sync in `010`) — a stale version misrepresents how much has actually changed.

## Goals

- Classify the commit message for a completing issue into a semver bump level, using the Conventional-Commit-style prefixes already used throughout this repo's history (`feat`/`fix`/`docs`/`chore`/etc.).
- Bump `.claude-plugin/plugin.json`'s version accordingly, in the same commit as the issue's completion (per `061`'s auto-commit-push flow) — not a separate follow-up commit.
- Match the industry-standard mapping (semantic-release's commit-analyzer): `feat`→minor, `fix`→patch, `!`/`BREAKING CHANGE`→major, everything else→no bump.

## Non-Goals

- `.codex-plugin/plugin.json` sync — already solved by `010-codex-version-sync-fix`. This issue only writes the canonical `.claude-plugin/plugin.json`; `010`'s `register_codex_personal_marketplace.py` propagates from there. Do not duplicate that sync logic here.
- CI/CD, changelog generation, or GitHub Releases — no CI exists in this repo; `release_check` (already a pre-push hook) is the only gate.
- Retroactively bumping for the 7 issues already shipped without a version change this session.
- The separately-deferred installed-plugin/marketplace staleness (`claude plugin list` showing an older version than the repo) — a different mechanism (marketplace cache refresh), out of scope here.

## Requirements

1. `scripts/version_bump.py` exposes `classify_bump(commit_message)`:
   - Returns `"major"` if the message contains `BREAKING CHANGE:` or has `!` immediately before the `:` in the type/scope prefix (e.g. `feat!:`, `feat(scope)!:`).
   - Returns `"minor"` if the message starts with `feat` (optionally scoped, e.g. `feat(053):`).
   - Returns `"patch"` if the message starts with `fix` (optionally scoped).
   - Returns `"none"` for any other recognized or unrecognized prefix (`docs`, `chore`, `refactor`, `test`, `style`, `perf`, or no prefix at all).
2. `bump_version(version_str, level)`: pure semver arithmetic — `"none"` returns the input unchanged; `"patch"`/`"minor"`/`"major"` increment the corresponding component and zero out the components to its right (standard semver rule).
3. `apply_bump(plugin_json_path, commit_message)`: reads the version, classifies, bumps, writes back if changed; returns the new version (or the unchanged one for `"none"`).
4. Wire into the `061` auto-commit-push-on-done step in `docs/host-adapter-guidance.md`: before making the completion commit, run `apply_bump` against the commit message being used, and stage the resulting `.claude-plugin/plugin.json` change into that same commit.

## Alternatives Considered

- **Bump based on the issue's Scope section content instead of the commit message**: rejected — the commit message is already conventionally prefixed by house habit (confirmed: 35 `feat:`, 33 `docs:`, 11 `fix:`, 6 `chore:` in history) and is the thing actually being written at the moment of the `061` auto-commit anyway; parsing free-form issue prose would be less reliable and duplicate information already present in the commit type.
- **Full semantic-release/CI pipeline**: rejected per benchmark — this repo has no CI; the classification algorithm is the useful part, not the automated-publish machinery around it.

## Acceptance Criteria

- `classify_bump("feat: implement issue 059 — auto fetch in repo sync")` → `"minor"`.
- `classify_bump("fix: correct issue 029 stale status")` → `"patch"`.
- `classify_bump("feat!: remove legacy loop-state gate")` → `"major"`.
- `classify_bump("docs: release issue 034 memory workflow")` → `"none"`.
- `bump_version("0.2.15", "minor")` → `"0.3.0"`; `bump_version("0.2.15", "patch")` → `"0.2.16"`; `bump_version("0.2.15", "major")` → `"1.0.0"`; `bump_version("0.2.15", "none")` → `"0.2.15"`.
- `apply_bump` on a fixture plugin.json + a `feat:` message updates the file's version and returns the new value; with a `docs:` message, the file is untouched.
- `python3 -m unittest tests.test_version_bump -v` passes.
- `python3 scripts/release_check.py .` passes.

## Risks

- Scoped prefixes (`feat(053):`) must still classify as `feat` — a naive `message.startswith("feat:")` check would miss them; match on the type token before `(` or `:`, not the full literal prefix.
- A message with no recognized prefix (e.g. a merge commit like `merge: bring in issues 056/057/058...`) must safely fall through to `"none"`, not error — matches this session's own `merge:`-prefixed commit.

## Open Questions

- None.

## Next Command

`/product:execute 063-version-bump-on-done`
