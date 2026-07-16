# Release: 089-verified-code-review-intake-and-remediation-routing

Issue: `089-verified-code-review-intake-and-remediation-routing`
Version: 0.3.26 (from 0.3.23)
GitHub Release: `https://github.com/dongwonlee222/moduflow/releases/tag/v0.3.26`
Merged: PR #25 (`84f6350`), PR #26 (`cd073e9`), and issue-link reconciliation PR #29 (`2615212`) to `main`, 2026-07-16.
Approval: Dongwon Lee explicitly authorized Codex to complete the PRs and immediate operational release work in the active Codex task on 2026-07-16.

## Shipped

- Canonical repository/remote/base-branch identity with deterministic mismatch, archive, read-only, provider, and write-capability gates.
- Verified human/AI/GitHub/CodeQL/SARIF review intake with source retention and integrity evidence.
- Independent Verifier and deterministic policy boundaries for elevated-risk disposition decisions.
- Security, pre-release, and post-release remediation routing with CognitiveDemand, deduplication, overlap hints, candidate queues, and bidirectional trace.
- Preview-first local CLI, Korean review summaries, adapter registry, templates, `product:review --intake`, and package validation.
- Review fixes for source-reviewer self-verification, partial-accept remedy leakage, review-ID path traversal, and incomplete final-packet validation.
- Dedicated GitHub Issues #27 and #28 for Issues 086 and 087 so all prioritized remaining roadmap work has a remote tracking surface.

## Human Review Evidence

- Korean packet: `specs/089-verified-code-review-intake-and-remediation-routing/human-review.ko.md`
- Canonical PR artifact: `specs/089-verified-code-review-intake-and-remediation-routing/pr.md`
- Review findings: `specs/089-verified-code-review-intake-and-remediation-routing/review.md`
- Dashboard: `memory/dashboard.html#issue-db`
- Issue detail: `memory/issue-089-verified-code-review-intake-and-remediation-routing.html`
- Merge approvals are recorded in PR #25, PR #26, and their canonical issue/review artifacts.

## Verification At Release

- Canonical repository release decision: allowed; expected and observed repository match `github.com/dongwonlee222/moduflow`.
- Full release gate: package, artifact, linkage, lint, security, version, test, doctor, and documentation checks pass.
- GitHub CI passed for PR #25, PR #26, and PR #29 before merge.
- Lifecycle drift: 0 after PR #25 and PR #26 merged.
- GitHub Issue projections #18 and #19 are closed with `moduflow:done`.

## Deploy

- Target: ModuFlow plugin/package source on `main` at version 0.3.26.
- Publish GitHub tag/release `v0.3.26`, then register the same source in the Codex personal marketplace.
- No database migration or hosted runtime deployment is required.

## Rollback

- Return to pre-088 main commit `2bcd5e5` / plugin version 0.3.23, rerun `scripts/release_check.py`, and reinstall from that source.
- Do not rewrite project remotes or delete review packets during rollback; the new identity and review files are additive and remain auditable.

## Post-release Checks

- Confirm `gh release view v0.3.26 -R dongwonlee222/moduflow` resolves to the intended `main` commit.
- Run `python3 scripts/register_codex_personal_marketplace.py .` and confirm a 0.3.26 Codex cache path.
- Run `product:doctor`/`product:status` from a fresh Codex task and verify the installed plugin is no longer stale.
- Continue with `product:spec 093-frontmatter-issue-schema-readiness-gate`.
