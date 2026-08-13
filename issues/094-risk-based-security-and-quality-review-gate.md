# Issue 094: Optional Risk-Based External Review Adapter Gate

**Status: backlog** — created 2026-07-16, scope reduced 2026-08-13.
**Priority: p2**
**Blocked-by: `089-verified-code-review-intake-and-remediation-routing`**

## Summary

Keep routine ModuFlow work light while optionally selecting replaceable external security and quality adapters for risk-sensitive review or release, normalizing their evidence, and requiring human approval before verified findings become reusable project guardrails.

## Source

- Type: user-approved follow-up from external code-review dogfood
- Link: ModuPay Biz CSV formula-injection finding, local Codex session 2026-07-16
- Owner / decision maker: Dongwon Lee
- Current phase: backlog

## Problem

Generic lint, tests, and security checks did not detect spreadsheet formula injection in a CSV export. The issue was found by an external reviewer and then fixed with a negative regression test. ModuFlow needs a small risk-aware orchestration layer, but it should not become a security scanner, load every plugin on every command, or make routine product work carry security-process overhead.

## Product Decision

- The gate is project opt-in and inactive during routine commands.
- ModuFlow owns risk-signal selection, adapter routing, evidence normalization, human approval, and release policy; external plugins own scanning and specialist analysis.
- Risk signals come from issue scope, changed paths, artifact types, data flows, and declared project rules, and are evaluated only at `product:review` or `product:release`.
- GitHub/CodeQL or SARIF, Codex Security, Sentry, and project-specific deployment adapters remain replaceable upstream capabilities; none is a mandatory dependency.
- A missing optional adapter degrades truthfully to an advisory. A project-declared required adapter or missing high-risk evidence blocks release with an actionable reason.
- Security findings use judgment-class review and cannot be auto-dismissed by a low-cost worker.
- Verified findings from Issue 089 may become reusable checks only after explicit human approval.
- Project-specific profiles extend a small ModuFlow baseline through adapters and overlays; they do not modify generated or vendored upstream code.
- The gate reports scoped coverage and residual risk, never “fully secure.”

## Initial Risk Profiles

- Export/download: spreadsheet formula injection, encoding, content type, filename, sensitive data.
- Authentication/authorization: role bypass, IDOR, token/session, 401/403, privileged actions.
- Payment/PII: masking, logging, transport, persistence, least privilege.

External input/rendering, file upload, destructive/write operations, API adapters, and shared-boundary refactors remain extension candidates. They are not required in the first version without project evidence that justifies them.

## Scope

### In

- A small versioned adapter/evidence contract and project opt-in configuration.
- Deterministic risk-signal collection from issue/spec/plan and changed files at review or release time only.
- Lazy routing to only the matching available adapter, using `vendor.lock.json`, `adapters/`, and `overlays/` without editing upstream sources.
- `product:review`/`product:release` evidence records with adapter identity, evidence paths, owner, result, N/A rationale, and residual risk.
- Negative-test recommendations and hard holds only for project-declared or high-risk required evidence.
- Initial export/download rule seeded from the CSV formula-injection dogfood.
- Human-approved promotion from verified review history to reusable checks.
- Focused tests for opt-in behavior, lazy adapter selection, unavailable-adapter fallback, evidence normalization, promotion approval, and release blocking.

### Out

- Claiming complete vulnerability coverage.
- Implementing a scanner, vulnerability database, runtime monitor, or deployment analyzer inside ModuFlow.
- Automatically installing or enabling plugins, paid scanners, or external source-code transmission.
- Running security/review adapters on routine issue, spec, plan, status, or execute commands.
- Treating all projects and changes as the same risk level.
- Promoting an unverified reviewer suggestion into policy.
- Replacing specialist security review for high-risk releases.

## Acceptance Criteria

- A project without opt-in produces no adapter invocation and no additional routine workflow artifact.
- An opted-in export/download change selects the spreadsheet-injection and sensitive-data adapter checks at review or release time.
- Opted-in authentication/authorization and payment/PII changes select only their matching adapter checks.
- Every invocation records the adapter ID, trigger, availability, permission, source version, and invoked/skipped reason.
- An unavailable optional adapter reports a truthful advisory fallback; an unavailable project-required adapter blocks release.
- Required checks record test/file or external-tool evidence, or block review/release with an actionable reason.
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

- `commands/product-review.md`
- `commands/product-release.md`
- `scripts/project_review.py`
- `scripts/release_check.py`
- `adapters/`
- `overlays/`
- `vendor.lock.json`
- `templates/workflow/`
- `tests/`

## Scope Fence

Do not build specialist scanners, load every adapter by default, or auto-promote policy from reviewer prose. Only a verified finding with evidence and explicit human approval can become a reusable gate.

## Workflow Tasks

- [ ] spec → `specs/094-risk-based-security-and-quality-review-gate/spec.md`
- [ ] plan → `specs/094-risk-based-security-and-quality-review-gate/plan.md`
- [ ] execute → opt-in trigger, adapter routing, normalized evidence gate, promotion workflow, and tests
- [ ] review → `specs/094-risk-based-security-and-quality-review-gate/review.md`

## Related Issues

- follows_up: `039-automated-review-checklists-and-safety-lint-gates`, `077-implementation-readiness-gate`, `089-verified-code-review-intake-and-remediation-routing`
- related: `071-spec-code-converge-check`, `088-canonical-repository-remote-identity-gate`, `093-frontmatter-issue-schema-readiness-gate`
- blocks:
- blocked_by: `089-verified-code-review-intake-and-remediation-routing`

## Sessions

- 2026-07-16: User approved turning verified external-review findings into a durable review history and future preventive security checks.
- 2026-08-13: User approved reducing 094 from a mandatory P1 security implementation to a P2/Later opt-in orchestration gate. External plugins perform specialist checks; ModuFlow stays responsible only for selective routing, normalized evidence, human approval, and release policy.

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/24

## Next Command

`product:spec 094-risk-based-security-and-quality-review-gate`
