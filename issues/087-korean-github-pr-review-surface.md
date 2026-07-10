# Issue 087: Korean GitHub PR Review Surface

**Status: backlog** — created 2026-07-10.
**Priority: p1**

## Summary

Make Korean the default human-facing language when ModuFlow creates or updates GitHub PR bodies, review comments, and approval summaries for a Korean reviewer, while keeping English Git artifacts canonical.

## Source

- Type: user workflow correction
- Link: PR #17 review session, 2026-07-10
- Owner / decision maker: Dongwon Lee
- Date: 2026-07-10

## Problem

Issue 057 generates `human-review.ko.md`, but the GitHub upload step can still use the English `pr.md` as the PR body. This means ModuFlow creates a Korean packet locally while asking the human to review an English-first surface in GitHub. The prior agreement is documented but not enforced at the point where review content is published.

## Product Decision

English `pr.md` remains the canonical machine-oriented handoff. For Korean reviewers, GitHub PR bodies, review comments, check summaries, and approval requests must be generated from the Korean review packet or an equivalent Korean-first projection. Agents must not upload `pr.md` directly as the human review body when a Korean packet exists.

## Scope

### In

- Define the Korean-first GitHub review publication rule in `product:pr` and `product:review`.
- Make PR creation and refresh use `human-review.ko.md` as the GitHub body for Korean reviewers.
- Make review findings and CI/check summaries posted to GitHub Korean-first.
- Preserve English `pr.md` as canonical and link it only as supporting detail.
- Expose the selected GitHub body path deterministically from `project_pr.py` so agents do not improvise.
- Add regression tests that fail when command guidance uploads English `pr.md` despite an available Korean packet.
- Document an explicit fallback when no Korean packet exists; the missing packet must be visible, not silently replaced by English.

### Out

- Replacing English canonical artifacts with Korean.
- Runtime translation APIs.
- Translating third-party CI log output.
- Automatic PR approval or merge.

## Acceptance Criteria

- `product:pr` creates and updates Korean-reviewer PR bodies from `human-review.ko.md`, not `pr.md`.
- `product:review` posts review findings and check summaries in Korean when the reviewer language is Korean.
- `project_pr.py` returns or records the exact human-facing GitHub body path.
- English `pr.md` remains canonical and is linked as supporting evidence.
- Missing Korean review content produces a visible hold/fallback state.
- Tests cover PR create, PR refresh, review comment, and missing-packet behavior.
- PR #17 remains a verified dogfood example with a Korean GitHub body.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- follows_up: `057-korean-human-review-packet`
- related: `049-bilingual-artifact-view`, `052-draft-pr-review-handoff`, `085-project-production-records-and-playbooks`
- blocks:
- blocked_by:
- duplicates:
- supersedes:

## Sessions

- 2026-07-10: User reiterated that reviews posted for human approval must be Korean and identified PR #17's English body as a repeated workflow failure.
- 2026-07-10: PR #17 was immediately corrected to use the Korean review packet as its GitHub body.

## Links

- Dogfood PR: `https://github.com/dongwonlee222/moduflow/pull/17`
- Prior issue: `issues/057-korean-human-review-packet.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 087-korean-github-pr-review-surface`
