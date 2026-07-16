# Tasks: Verified Code-Review Intake and Remediation Routing

Issue: `089-verified-code-review-intake-and-remediation-routing`
Plan: `specs/089-verified-code-review-intake-and-remediation-routing/plan.md`

## Ready

- [x] implementation: T01 — add the immutable review packet, source retention/hash, finding identity, and validation core. [files: scripts/review_intake.py, tests/test_review_intake.py] [shared_state: true]
- [x] implementation: T02 — add manual, GitHub thread, CodeQL alert, SARIF, and trigger-based lazy source adapters. [files: scripts/project_review.py, tests/test_project_review.py] [depends: T01] [shared_state: true]
- [x] implementation: T03 — add Router/Verifier decision inputs and deterministic verification/disposition policy. [files: scripts/review_intake.py, tests/test_review_intake.py] [depends: T01,T02] [shared_state: true]
- [x] implementation: T04 — add remediation lanes, CognitiveDemand, exact deduplication, candidates, and bidirectional trace. [files: scripts/review_intake.py, tests/test_review_intake.py] [depends: T03] [shared_state: true]
- [x] implementation: T05 — add dry-run/write CLI, atomic packet persistence, Korean projection, candidate queue, and templates. [files: scripts/project_review.py, tests/test_project_review.py, templates/reviews/review-intake.json, templates/reviews/review-summary.ko.md, templates/reviews/review-candidates.md] [depends: T02,T04] [shared_state: true]
- [x] implementation: T06 — register GitHub/security/Superpowers adapters, policy overlay, distribution validation, and `product:review --intake` routing. [files: adapters/github-review.yaml, adapters/security-review.yaml, adapters/superpowers.yaml, overlays/review-policy.yaml, vendor.lock.json, scripts/validate_moduflow.py, tests/test_validation_distribution.py, commands/product-review.md, skills/index/SKILL.md] [depends: T05] [shared_state: true]
- [x] qa: T07 — run synthetic dry-run dogfood, focused/full verification, and record status without copying external review source text. [files: issues/089-verified-code-review-intake-and-remediation-routing.md, specs/089-verified-code-review-intake-and-remediation-routing/tasks.md, specs/089-verified-code-review-intake-and-remediation-routing/status.md] [depends: T06] [shared_state: true]

## In Progress

- None.

## Done

- Approved adapter-first design and benchmark basis.
- English and Korean spec written and committed.
- TDD implementation plan and task dependency graph written.
- T01–T07 implemented and verified; staged product review remains.

## Blocked

- None. Issue 094 remains blocked by completion of Issue 089, not vice versa.

## Acceptance Coverage

- AC1–AC4 → T01, T03, T05
- AC5–AC6 → T03
- AC7–AC10 → T02, T03, T06
- AC11–AC12 → T06
- AC13–AC16 → T04
- AC17–AC18 → T05, T06, T07
- AC19–AC20 → T01–T07

## Next

`product:review 089-verified-code-review-intake-and-remediation-routing`
