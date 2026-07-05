# Issue: `063-version-bump-on-done`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.

## Outcome

`.claude-plugin/plugin.json`'s version bumps automatically as part of the `061` auto-commit-push-on-done flow, classified from the completing commit's Conventional-Commit-style prefix (`feat`→minor, `fix`→patch, `!`/`BREAKING CHANGE`→major, everything else→no bump) — so shipping issues stops silently leaving the version stale.

Benchmark: `knowledge/benchmarks/2026-07-05-version-bump-automation-benchmark.md`.

## Why

`docs/release-checklist.md` already says to "update version metadata when releasing a new plugin version," but never defines what counts as a release, so it's been skipped: `.claude-plugin/plugin.json` was last bumped (to `0.2.15`) at commit `b775a25`, and 57 commits / 7 completed issues later (this session alone: `059`, `060`, `061`, `062`, the `056`/`057`/`058` merge, `053`) it's still `0.2.15`. 061 already made commit+push automatic on `done` — version bumping belongs in that same automatic step, or it will keep getting skipped the same way.

## Scope

### In

- A script/function that classifies a commit message's Conventional-Commit-style prefix into a semver bump level (`feat`→minor, `fix`→patch, `!`/`BREAKING CHANGE`→major, `docs`/`chore`/`refactor`/other→none), per the benchmark's industry-standard mapping (semantic-release's commit-analyzer).
- Bump `.claude-plugin/plugin.json`'s `version` field accordingly, included in the same commit as the issue's `Status: done` commit (not a separate follow-up commit).
- Wire into the `061` auto-commit-push-on-done flow: when about to commit a done issue, classify and bump before committing.
- Tests covering each classification case and a no-bump case.

### Out

- `.codex-plugin/plugin.json` sync — already solved by `010-codex-version-sync-fix`'s `register_codex_personal_marketplace.py`, which reads the canonical base from `.claude-plugin/plugin.json`. This issue writes the canonical file; `010`'s mechanism propagates it. Not duplicating that here.
- No CI/CD pipeline, changelog generation, or GitHub Release creation — this repo has no CI; the pre-push `release_check` hook is the only gate.
- No retroactive version bump for the 7 issues already shipped without one this session — could be done as a one-time manual catch-up, but not automated as part of this issue's scope.
- Not addressing the separately-deferred marketplace/installed-plugin staleness (`claude plugin list` showing `0.2.6` vs repo's `0.2.15`) — unrelated mechanism, user chose to hold off on that this session.

## Acceptance Criteria

- Given a `feat:` commit message, the classifier returns `minor`.
- Given a `fix:` commit message, `patch`.
- Given a `feat!:` or a message containing a `BREAKING CHANGE:` footer, `major`.
- Given a `docs:`/`chore:`/`refactor:` commit message, `none` (no version change).
- Bumping `0.2.15` with `minor` → `0.3.0`; with `patch` → `0.2.16`; with `major` → `1.0.0`.
- `python3 -m unittest tests.test_version_bump -v` passes.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- follows_up: `061-auto-commit-push-on-issue-done`
- related: `010-codex-version-sync-fix` (the sibling mechanism this issue does not duplicate)

## Workflow Tasks

- [x] spec → `specs/063-version-bump-on-done/spec.md`
- [x] plan → `specs/063-version-bump-on-done/plan.md`
- [x] execute → `scripts/version_bump.py`, `tests/test_version_bump.py`, `docs/host-adapter-guidance.md`

## Sessions

- 2026-07-05: User noticed the plugin version looked stale after a run of completed issues with no version bump. Confirmed the gap (0.2.15 unbumped across 57 commits/7 issues) and asked to research external conventions before designing the fix.
- 2026-07-05: Researched Conventional-Commits-to-semver mapping (semantic-release's commit-analyzer as the industry reference); this repo's own commit history already followed the same prefixes without anyone imposing it. Implemented `classify_bump`/`bump_version`/`apply_bump` in `scripts/version_bump.py`, wired into `061`'s auto-commit-push step via `docs/host-adapter-guidance.md`. 14 new tests, full suite (203 tests) and `release_check.py` pass. Also fixed issue `010`'s stale legacy status line (was already done, no inline `Status:` line — same class of drift as `029`). This commit is the first to dogfood the new flow. Done.

## Links

- Roadmap: `workspace/roadmap.md`
- Benchmark: `knowledge/benchmarks/2026-07-05-version-bump-automation-benchmark.md`
- Spec: `specs/063-version-bump-on-done/spec.md`
- Plan: `specs/063-version-bump-on-done/plan.md`

## Next Command

`/product:status`
