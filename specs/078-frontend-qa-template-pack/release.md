# Release: 078-frontend-qa-template-pack

Issue: `078-frontend-qa-template-pack`
Version: 0.3.21
Merged: PR https://github.com/dongwonlee222/moduflow/pull/15 -> `main` (`7d673c8`), 2026-07-09
Approval: Dongwon Lee approved sequential lifecycle reconciliation on 2026-07-21 after the merged PR, Korean review packet, recorded review result, CI result, and fresh repository verification were checked.

## Shipped

- Framework-agnostic frontend QA templates for API contracts, Storybook states, MSW fixtures, Playwright smoke coverage, and QA evidence.
- Required/optional/not-applicable guidance for frontend planning and review.
- Distribution validation that ensures the template pack ships with ModuFlow.
- Command and design-bridge guidance connecting the templates to planning, design, prototype, and review work.

## Human Review Evidence

- Korean packet: `specs/078-frontend-qa-template-pack/human-review.ko.md`
- Canonical PR artifact: `specs/078-frontend-qa-template-pack/pr.md`
- Review: `specs/078-frontend-qa-template-pack/review.md`
- Dashboard: `memory/dashboard.html#issue-db`
- Issue detail: `memory/issue-078-frontend-qa-template-pack.html`
- GitHub PR #15 merged with successful CI.

## Verification at Reconciliation

- PR #15 CI check `test` concluded `SUCCESS` before merge.
- `python3 scripts/release_check.py .` passed on 2026-07-21 after Issue 077 reconciliation; this includes the full test suite, validators, lint, security, linkage, doctor, and release checks.
- Focused distribution tests, spec consistency, package validation, and project validation were recorded as passing in `status.md` and `review.md` before merge.

## Deploy

- Target: ModuFlow plugin/package source on `main` at version 0.3.21.
- No target-project dependency installation, database migration, or hosted runtime deployment was required.

## Rollback

Revert merge commit `7d673c8bcf1e058c41da6c2122e6e7ebdd276721`. The template files and documentation links are additive and can be removed without migrating project data.

## Post-release Checks

- Confirm `templates/frontend-qa/` remains in package validation.
- Dogfood the templates on the next frontend implementation and adjust only from observed evidence.
- Continue lifecycle reconciliation with `079-plan-discipline-skill-matrix`.
