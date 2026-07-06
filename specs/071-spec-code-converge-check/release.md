# Release: 071-spec-code-converge-check

Issue: `071-spec-code-converge-check`
Version: 0.3.14 (from 0.3.13)
Merged: PR https://github.com/dongwonlee222/moduflow/pull/9 → `main` (`a0453f7`), 2026-07-06
Approval: explicit human merge approval in session ("병합 진행해", 2026-07-06) after dashboard + drill-down + Korean packet review.

## Shipped

- `scripts/project_converge.py` — hybrid converge engine: `--evidence` (deterministic bundle: linkage-based commit resolution, capped current-file contents, single-parsed AC/GC) + `--apply-judgment` (dated converge.md run sections, CV append with source-ref dedup, regression re-append, byte-for-byte no-op, exit contract).
- `templates/converge-judgment-prompt.md` — independent-judge instruction with fixed verdict vocabulary (`converged|missing|partial|contradicting|unverifiable`) + `unrequested` + `bundle_gaps`.
- `commands/product-converge.md` (new command, outside the default mental model) + converge as `product:review`'s final non-blocking evidence step.
- Mechanism benchmark of spec-kit converge / OpenSpec verify (`memory/evidence/2026-07-06-converge-mechanism-benchmark.md`).

## Verification at release

- 393 tests OK (47 converge-focused); `release_check` valid; linkage gate green on the issue branch.
- Self-application ×2, both catching real issues: 075 dogfood (missing `retrieval_trigger` on two decision records — fixed) and 071 self-converge (plan GC#6 source-ref grammar drift — resolved via dated plan amendment).

## Rollback

Revert merge commit `a0453f7`; new files additive; the product-review.md auto-run step is a doc-level revert.

## Post-release checks

- Follow-up candidate (review.md finding 3): evidence bundle should prioritize code/tests over docs when capping — tight caps inflated `unverifiable` on the first 075 run.
- Inbox item captured: dashboard issue-DB should render the `active` status group first (user could not find active 071 under default sort).
- 075's CV-2..4 remain open as bundle-cap artifacts on its tasks.md.
