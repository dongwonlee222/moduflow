# Review: 075-issue-less-context-capture

Issue: `075-issue-less-context-capture`
Date: 2026-07-06
Verdict: pass (spec compliance: pass · quality: pass) — with one recorded limitation

> Subagent limitation (per product:review contract): host subagent dispatch hit session limits during execution waves 2-3, so QA and spec-compliance review concerns were performed inline by the coordinating agent instead of independent reviewer subagents. Findings below are reported unfiltered; the adversarial re-check of the v1 HIGH findings was done against the actual v2 code, not the workers' claims.

## Scope Reviewed

- `scripts/linkage_check.py`, `scripts/release_check.py`, `scripts/project_promote.py`, `scripts/project_retention.py`, `scripts/project_pr.py`
- `commands/product-promote.md`, `product-release.md`, `product-status.md`, four capture command docs
- `templates/issues/issue.md`, `.moduflow/humans.json`, `releases/no-issue-declarations.md`, `.github/workflows/ci.yml`
- Issue/spec/plan/tasks artifacts

## Adversarial HIGH-findings closure check (v1 → v2)

- **HIGH-1 (didn't solve own problem)**: closed at the release boundary — gate triggers on worktree diff + linkage, not capture records; in-session detection explicitly scoped to 072 with the linkage checker importable for it. Verified: `linkage_check.find_unlinked_behavior_commits` is module-level and release_check imports it.
- **HIGH-2 (self-approval loop)**: closed structurally — declarations validate via `git blame` against `.moduflow/humans.json`; agent cannot mint one. **Recorded limitation**: on this shared-identity machine, local blame attributes agent commits to the human; the GitHub PR-approval channel is the effective strong gate. Not hidden — documented in humans.json, spec Risks, status.md, and PR body.
- **HIGH-3 (path heuristic + silent holes)**: closed — branch/trailer convention is the primary signal; both `except Exception: pass` holes removed (verified by grep and by tests `test_git_failure_*`); merge-base explicit with shallow-fetch recovery; CI fetch-depth 0.

## Verification

- Full suite: **346 tests OK** (29 linkage + 12 release_check-new + 19 promote + 6 retention added).
- Self-application gate: branch passes its own linkage gate; `release_check.py .` → `valid: true` at every wave commit.
- Promote dry-run on a real record auto-numbers 076 and prefills sections; write-path covered by tmpdir tests including byte-identical record preservation.
- Retention live run: 12 unpromoted, 8 archive candidates surfaced without mutation.
- `spec_consistency` 0/0/0; `validate_project_artifacts` 0 errors.
- Declaration parser hardening verified: prose (headings/blockquotes/backticks) cannot parse as declarations — coordinator caught and fixed a real gap between A2's parser and the declarations file format during integration.

## Findings

1. (resolved during review) Declarations-file prose could have parsed as valid declarations under the shared-identity blame — parser now only accepts bare lines; packet renderer aligned.
2. (limitation, carried) Shared git identity weakens local blame validation — strong channel is GitHub PR approval; candidate follow-up when 072 lands hooks.
3. (minor, accepted) `version_bump_gate` requires a bump per feat-classified HEAD commit, which produced 0.3.12→0.3.13 across waves of one issue; harmless but slightly version-noisy for multi-wave issues.

## Visual Evidence

- Dashboard: `memory/dashboard.html` (76 issue panels, 13 memory panels)
- Issue drill-down: `memory/issue-075-issue-less-context-capture.html`

## Next

`product:pr 075-issue-less-context-capture` — Draft PR #8 exists; refresh packet and hand to human review.
