---
kind: benchmark
title: Version Bump Automation Benchmark
issue_id: 063-version-bump-on-done
spec:
decision_supported: Bump .claude-plugin/plugin.json (and synced .codex-plugin/plugin.json) automatically from the Conventional-Commit-style prefix already used in this repo's commit messages, as part of the 061 auto-commit-push-on-done flow
date: 2026-07-05
confidence: high
sources:
  - https://www.conventionalcommits.org/en/v1.0.0/
  - https://github.com/semantic-release/commit-analyzer
  - https://devopsil.com/articles/2026-03-21-semantic-versioning-automated-releases
  - https://www.pkgpulse.com/guides/semantic-release-vs-changesets-vs-release-it-release-2026
---

# Version Bump Automation Benchmark

## Question

How should ModuFlow decide when and how much to bump `.claude-plugin/plugin.json`'s version, given 061 now auto-commits+pushes on every completed issue and today's session shipped 7 issues (059-062, 056/057/058 merge, 053) with zero version bumps?

## Current Gap

`docs/release-checklist.md` step 2 says "update version metadata when releasing a new plugin version" but never defines what counts as "a release" — so it gets skipped by default. `.claude-plugin/plugin.json` was last bumped (to `0.2.15`) at commit `b775a25`; 57 commits and 7 completed issues later, still `0.2.15`. Separately, the actually-*installed* Claude Code plugin reports `0.2.6` — a different problem (marketplace cache staleness, deferred by the user this session), not addressed here.

`.codex-plugin/plugin.json` already has a solved sibling problem: issue `010-codex-version-sync-fix` (confirmed done this session, was mis-marked backlog from a legacy schema) made `.claude-plugin/plugin.json` the canonical base version and `register_codex_personal_marketplace.py` sync the Codex manifest's base + preserve its `+codex.<timestamp>` build suffix. Any new automation must write through `.claude-plugin/plugin.json` and let that existing sync mechanism propagate, not duplicate it.

## External Pattern: Conventional Commits → semver

The standard mapping (semantic-release, release-please, and equivalents) is:

- `feat:` → **minor** bump
- `fix:` → **patch** bump
- `refactor:`/`style:`/`perf:`/`docs:`/`test:`/`chore:` → **no bump** (no release-worthy change)
- `BREAKING CHANGE:` footer or `!` after the type → **major** bump

This repo's own git history already follows this convention closely without anyone imposing it: 35 `feat:`, 33 `docs:`, 11 `fix:`, 6 `chore:` commits, occasionally scoped (`fix(049):`, `feat(032):`). No `BREAKING CHANGE`/`!` commits have appeared yet — first-class support for major bumps is cheap to add but untested against real history.

**semantic-release** (fully automated, CI-driven, commit-analyzer plugin computes the bump) is the closest fit in spirit but assumes a CI pipeline; this repo has none — issues get committed/pushed by an agent session directly, not through CI. **changesets** (PR-based, humans describe changes in separate files) doesn't fit either — adds authoring overhead this workflow doesn't have (an issue's own `Status: done` commit already carries the same information a changeset file would). The useful part to borrow is only the **classification algorithm** (commit type → bump level), not the CI/PR machinery around it.

## Recommended ModuFlow Shape

- A script, run as part of the `061` auto-commit-push-on-done flow, that:
  1. Looks at the commit message about to be made for the completed issue (already conventional-commit-prefixed in practice, per the tally above).
  2. Classifies it: `feat` → minor, `fix` → patch, anything else (`docs`/`chore`/`refactor`/etc.) → no bump, `!`/`BREAKING CHANGE` → major.
  3. Bumps `.claude-plugin/plugin.json`'s version accordingly (semver: `major.minor.patch`).
  4. Includes the version bump in the same commit as the issue's completion — one commit, not a separate "chore: bump version" follow-up (avoids the two-commits-per-release churn changesets-style PRs have).
- `.codex-plugin/plugin.json` is left to the existing `010` sync mechanism (`register_codex_personal_marketplace.py`) — not duplicated here.
- No CI/PR layer — this repo's "CI" is the pre-push `release_check` hook already gating every push.

## Decision

Scope `063-version-bump-on-done` as: classify-and-bump `.claude-plugin/plugin.json` from the issue's own commit-message prefix, wired into the existing `061` auto-push step. Reuse the semver level mapping verified across the industry (semantic-release's commit-analyzer) rather than inventing a new one.

## Next Action

`product:spec 063-version-bump-on-done`
