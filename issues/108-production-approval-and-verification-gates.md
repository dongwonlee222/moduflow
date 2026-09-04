# Issue 108: Production Approval and Verification Gates

**Status: backlog** — created 2026-08-19.
**Priority: p1**
**Blocked-by: `104-project-aware-natural-language-request-orchestrator`**

## Summary

Initialize production approver readiness and select deliverable-specific verification adapters so evidence is required before a production artifact can become final, approved, published, or upload-ready.

## Source

- Type: user multi-project orchestration improvement request
- Link: local Codex attachment `pasted-text.txt`, 2026-08-19
- Owner / decision maker: Dongwon Lee
- Current phase: blocked

## Opportunity

Issue 085 validates record structure and playbook promotion, Issue 094 defines an optional risk-based review adapter pattern, and Issue 101 improves schema discoverability. Production workflows still lack early approver setup and artifact-specific verification for dimensions, copy, file integrity, packages, and HTML links.

## Scope

### In

- Detect missing `.moduflow/humans.json` during lightweight start/production initialization or before the first approval attempt.
- Offer explicit approver setup from a confirmed project owner or central user profile without auto-authorizing an arbitrary identity.
- Select verification checks from Production Record `deliverable_type`, `channel`, and `variant`.
- Initially cover image/banner, splash, event-page/HTML, ZIP/handoff, document, and message-copy deliverables.
- Emit `moduflow.production-verification.v1` with issue/record/artifact identity, checks, evidence, verifier, timestamp, and result.
- Block `final`, `approved`, `published`, and `upload-ready` transitions when required evidence is missing or failed.
- Integrate verification results with Issue 104 routing and Issue 103 lifecycle transactions.

### Out

- Claiming that generic automated checks replace human brand, legal, or release approval.
- Auto-registering an approver without confirmation.
- Building every media validator inside ModuFlow when a replaceable adapter can supply evidence.
- Running all validators for every artifact type.

## Acceptance Criteria

- A lightweight project receives approver setup guidance before the first promotion/approval attempt fails.
- An owner candidate is never authorized without explicit confirmation and recorded identity evidence.
- Each supported deliverable type selects only its relevant checks and records skipped/N/A rationale.
- Image checks cover dimensions, aspect ratio, format, size, and openability when required.
- HTML/ZIP checks cover link/package integrity and required artifact counts when required.
- Copy checks cover required terms, spacing, dates, prices, and brand names using project-approved rules.
- Missing or failed required evidence prevents final/approved/published/upload-ready state with an actionable reason.
- Successful verification is linked to the issue and Production Record and applied atomically with lifecycle state.
- Project A/B fixtures prove that verification rules and brand terms remain project-scoped.

## Verification

- Approver-missing, owner-confirmation, pass/fail/needs-review, N/A, and unavailable-adapter fixtures.
- Representative image, splash, HTML, ZIP, document, and Korean message-copy artifacts.
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_production.py`
- `scripts/project_review.py`
- `commands/product-production.md`
- `.moduflow/humans.json`
- `templates/production/`
- `adapters/`

## Scope Fence

Do not auto-approve users, claim universal quality coverage, or let optional checks block unrelated artifact types.

## Workflow Tasks

- [ ] spec → `specs/108-production-approval-and-verification-gates/spec.md`
- [ ] plan → `specs/108-production-approval-and-verification-gates/plan.md`
- [ ] execute → approver readiness, verification contract/adapters, lifecycle gate, and tests
- [ ] review → `specs/108-production-approval-and-verification-gates/review.md`

## Related Issues

- blocks:
- blocked_by: `104-project-aware-natural-language-request-orchestrator`
- duplicates:
- follows_up: `085-project-production-records-and-playbooks`, `094-risk-based-security-and-quality-review-gate`
- supersedes:
- related: `075-issue-less-context-capture`, `101-production-record-schema-friction`, `115-playbook-process-and-checklist-extension`

## Playbook Extension Note — 2026-09-03

[Issue 115](115-playbook-process-and-checklist-extension.md) adds an external `process_ref` and a numbered `Required Checks` checklist to `moduflow.playbook.v1`. This issue was written before they existed. `Required Checks` is a reviewer assertion recorded on the playbook, not evidence. Deciding whether a final-state gate requires those items to be confirmed, and with what evidence, is this issue's call. Issue 115 stores the list and enforces nothing.

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Source audit: `specs/102-project-registry-and-resolver/source-audit.md`

## Next Command

After Issue 104 is done: `product:spec 108-production-approval-and-verification-gates`.
