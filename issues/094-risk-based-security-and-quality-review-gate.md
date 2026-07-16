# Issue 094: Risk-Based Security and Quality Review Gate

**Status: backlog** — created 2026-07-16.
**Priority: p1**
**Blocked-by: `089-verified-code-review-intake-and-remediation-routing`**

## Summary

Select security and quality checks from the changed feature’s risk profile, require evidence and negative tests before PR/release, and promote verified external-review findings into reusable project guardrails with human approval.

## Source

- Type: user-approved follow-up from external code-review dogfood
- Link: ModuPay Biz CSV formula-injection finding, local Codex session 2026-07-16
- Owner / decision maker: Dongwon Lee
- Current phase: backlog

## Problem

Generic lint, tests, and security checks did not detect spreadsheet formula injection in a CSV export. The issue was found by an external reviewer and then fixed with a negative regression test. ModuFlow needs a risk-aware review layer that asks the right questions before external review or release, without pretending that one universal checklist proves security.

## Product Decision

- Risk signals come from issue scope, changed paths, artifact types, data flows, and declared project rules.
- Applicable checks are explicit and evidence-backed; non-applicable checks require rationale.
- Security findings use judgment-class review and cannot be auto-dismissed by a low-cost worker.
- Verified findings from Issue 089 may become reusable checks only after human approval.
- Project-specific profiles extend a small ModuFlow baseline; they do not modify generated or vendor code.
- The gate reports coverage and residual risk, never “fully secure.”

## Risk Profiles

- Export/download: spreadsheet formula injection, encoding, content type, filename, sensitive data.
- Authentication/authorization: role bypass, IDOR, token/session, 401/403, privileged actions.
- External input/rendering: XSS, HTML/URL injection, unsafe redirects.
- File upload: MIME/extension, size, storage path, malware handoff.
- Destructive/write operations: confirmation, permission, idempotency, audit trail, rollback.
- Payment/PII: masking, logging, transport, persistence, least privilege.
- API adapters: field omission, trust boundary, raw error leakage, generated-client boundary.
- Shared-boundary refactors: import rules, role-specific behavior, accessibility, regression matrix.

## Scope

### In

- A versioned risk-profile schema and project extension file.
- Deterministic risk-signal collection from issue/spec/plan and changed files.
- `product:plan`/`product:review`/`product:release` check matrices with evidence paths, owner, result, N/A rationale, and residual risk.
- Negative-test recommendations and hard holds for required missing evidence.
- Initial export/download rule seeded from the CSV formula-injection dogfood.
- Human-approved promotion from verified review history to reusable checks.
- Focused tests for rule selection, N/A handling, promotion approval, and release blocking.

### Out

- Claiming complete vulnerability coverage.
- Automatically enabling paid scanners or sending source code externally.
- Treating all projects and changes as the same risk level.
- Promoting an unverified reviewer suggestion into policy.
- Replacing specialist security review for high-risk releases.

## Acceptance Criteria

- Export/download changes select spreadsheet-injection and sensitive-data checks automatically.
- Auth/permission, external input, upload, destructive action, payment/PII, adapter, and shared-refactor signals select their relevant checks.
- Required checks record test/file evidence or block review/release with an actionable reason.
- N/A and residual-risk decisions record owner and rationale.
- A verified Issue 089 finding can be proposed for promotion, but only explicit human approval updates the governed checklist.
- The ModuPay Biz CSV finding produces a reusable negative-test rule without copying project data.
- “No findings” is reported as scoped evidence, not a claim of zero risk.
- Focused tests and `python3 scripts/release_check.py .` pass.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*risk*review*.py' -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `commands/product-plan.md`
- `commands/product-review.md`
- `commands/product-release.md`
- `scripts/project_review.py`
- `scripts/release_check.py`
- `templates/workflow/`
- `tests/`

## Scope Fence

Do not auto-promote policy from reviewer prose. Only a verified finding with evidence and explicit human approval can become a reusable gate.

## Workflow Tasks

- [ ] spec → `specs/094-risk-based-security-and-quality-review-gate/spec.md`
- [ ] plan → `specs/094-risk-based-security-and-quality-review-gate/plan.md`
- [ ] execute → risk profiles, signal selector, evidence gate, promotion workflow, and tests
- [ ] review → `specs/094-risk-based-security-and-quality-review-gate/review.md`

## Related Issues

- follows_up: `039-automated-review-checklists-and-safety-lint-gates`, `077-implementation-readiness-gate`, `089-verified-code-review-intake-and-remediation-routing`
- related: `071-spec-code-converge-check`, `088-canonical-repository-remote-identity-gate`, `093-frontmatter-issue-schema-readiness-gate`
- blocks:
- blocked_by: `089-verified-code-review-intake-and-remediation-routing`

## Sessions

- 2026-07-16: User approved turning verified external-review findings into a durable review history and future preventive security checks.

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/24

## Next Command

`product:spec 094-risk-based-security-and-quality-review-gate`
