# Release: 095-commit-issue-resolution-parity

Issue: `095-commit-issue-resolution-parity`
Version: 0.3.41 source manifest
Merged: PR #33 as merge commit `f4029f37934002066ab02a4c5475e3fef81421da` to `main` on 2026-08-03.
Approval: Dongwon Lee authorized completion by replying `진행해줘` in the Korean Codex review flow after receiving the Korean packet link and the release-check, CI, and merge-readiness summary.

## Shipped

- One immutable Git graph snapshot and one evidence-backed attribution policy now serve commit-to-issue and issue-to-commit consumers.
- Per-issue fork points, stacked topic deltas, deleted refs, detached HEAD, complex merges, and caller-scoped diagnostics have explicit behavior.
- Ambiguous or malformed evidence fails closed instead of silently under-collecting commits.
- `FH-001`–`FH-040` remain in the append-only failure corpus and map to executable invariants.

## Human Review Evidence

- Korean packet: `specs/095-commit-issue-resolution-parity/human-review.ko.md`
- Canonical PR artifact: `specs/095-commit-issue-resolution-parity/pr.md`
- Dashboard: `memory/dashboard.html#issue-db`
- Issue detail: `memory/issue-095-commit-issue-resolution-parity.html`
- PR approval record: `https://github.com/dongwonlee222/moduflow/pull/33#issuecomment-5161987654`
- Human merge approval: Dongwon Lee, Korean Codex task, 2026-08-03.
- Technical review: Codex verified the dashboard entry, issue detail, PR change scope, failure corpus, fresh release check, GitHub CI, and merge state. The app cannot observe whether the human opened each linked file, so this record does not claim unobservable click-through activity.

## Verification At Release

- Canonical repository release decision: allowed; expected and observed repository match `github.com/dongwonlee222/moduflow`.
- Pre-merge PR: CI `test` passed; merge state `CLEAN` and `MERGEABLE`.
- Post-merge `python3 scripts/release_check.py .` at `f4029f3`: `valid: true`, `errors: []`; validation, artifact, linkage, lint, security, version, tests, doctor, and documentation gates all passed.
- Final whole-branch review: Critical/Important/Minor `0/0/0`; full controller discovery `1035/1035 PASS`.

## Deploy

- Target: ModuFlow repository source on `main` at `f4029f3`.
- No hosted runtime, database migration, GitHub tag/release, installed plugin/cache update, or marketplace publish is part of this release.
- Plugin publication remains held until the separate Issue 096 evidence-write and path-safety scope is completed.

## Rollback

- Create a dedicated rollback branch from current `main`, run `git revert -m 1 f4029f37934002066ab02a4c5475e3fef81421da`, and open a reviewed PR.
- Rerun `python3 scripts/release_check.py .` before merging the rollback.
- Preserve `failure-history.md` and review records even if behavior is reverted.

## Post-release Checks

- Confirm PR #33 is `MERGED` with merge commit `f4029f3`.
- Confirm post-merge release check is `valid: true` with `errors: []`.
- Continue with `product:spec 094-risk-based-security-and-quality-review-gate`.

