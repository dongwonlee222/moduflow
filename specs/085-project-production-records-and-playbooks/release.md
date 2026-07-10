# Release: 085-project-production-records-and-playbooks

Issue: `085-project-production-records-and-playbooks`
Version: 0.3.23
Merged: PR https://github.com/dongwonlee222/moduflow/pull/17 -> `main` (`0356b75`), 2026-07-10
Approval: Dongwon Lee explicitly approved proceeding after reviewing the Korean-first PR surface, dashboard/issue detail, verification result, and release readiness in the Codex session on 2026-07-10.

## Shipped

- Project-local Production Records for artifacts, source inputs, decisions, failed attempts, reusable patterns, `Do Not Repeat`, and playbook updates.
- Human-approved project-local Playbooks with source-record linkage and audited approve/reject/defer decisions.
- External/customer-facing copy and internal-reporting copy separation across banner, PR, proposal, Alimtalk, SMS, Push, and related recurring deliverables.
- Duplicate-safe capture, search/retrieval, validation, templates, command routing, package checks, and dogfood fixtures.

## Human Review Evidence

- Korean packet: `specs/085-project-production-records-and-playbooks/human-review.ko.md`
- Canonical PR artifact: `specs/085-project-production-records-and-playbooks/pr.md`
- Dashboard: `memory/dashboard.html#issue-db`
- Issue detail: `memory/issue-085-project-production-records-and-playbooks.html`
- GitHub PR body and review findings were presented in Korean before approval.

## Verification at Release

- Focused production suite: 24 passed.
- Full repository suite: 483 passed.
- Spec consistency: 0 findings.
- Package, project, release, lint, security, and GitHub CI gates passed before merge.
- Independent review findings were fixed and covered by regression tests.

## Deploy

- Target: ModuFlow plugin/package source on `main` at version 0.3.23.
- No database migration or hosted runtime deployment is required.

## Rollback

Revert merge commit `0356b75`. The production-record files and command surfaces are additive; existing project memory remains canonical and readable.

## Post-release Checks

- Run `python3 scripts/validate_project_artifacts.py .` against a project that registers production records.
- Run `python3 scripts/release_check.py .` before the next package publication.
- Continue with `product:design 086-project-aware-production-library-dashboard` for the project-scoped dashboard view.
