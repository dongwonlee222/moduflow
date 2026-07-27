# Tasks: 095-commit-issue-resolution-parity

Issue: `095-commit-issue-resolution-parity`
Plan: `specs/095-commit-issue-resolution-parity/plan.md`

## Stream A — Shared Resolver

- [x] A1 Create `scripts/commit_resolution.py` owning trailer, branch, and merge-subject rules behind three fixed signatures, porting existing behavior verbatim.
- [x] A2 Replace per-commit `git branch --contains` with one batched branch-membership build, and assert subprocess count does not scale with history length.

## Stream B — Consumer Migration

- [x] B1 Make `linkage_check.resolve_issue_for_commit()` a wrapper over the shared resolver and gain the merge-subject source it lacked.
- [x] B2 Make `project_converge.resolve_commits()` delegate, gain the branch fallback, and add `unmatched_count`, `examined_count`, and per-commit `source` to the evidence payload.

## Stream C — Surface and Documentation

- [x] C1 Surface the unmatched count wherever converge evidence reaches a human reviewer, without changing review verdict logic.

## Stream D — Regression Coverage

- [x] D1 Extend `tests/git_repo_builder.py` (created in stream A) and cover trailer-only, branch-only, mixed, merge-subject with branch deleted, detached HEAD, no-issue commits, and parity.

## Stream E — Parity Proof and Completion

- [x] E1 Add the cross-module parity test, then confirm converge on issue 093's history collects the full commit set including `scripts/project_issue_schema.py`.
- [x] E2 Pass full unittest, lifecycle drift, and release check before moving to review.

## Corrective Completion — 2026-07-27

- [ ] F1 Fail closed on historical issue discovery and Git graph errors.
- [ ] F2 Remove R9-1 through R9-4 expected-failure masking and fix global attribution.
- [ ] F3 Reconcile the canonical issue, refined spec, lifecycle state, PR handoff, and Korean packet.
- [ ] F4 Pass focused/full verification with zero expected failures and complete independent review.

Plan: `docs/superpowers/plans/2026-07-27-095-corrective-completion.md`
