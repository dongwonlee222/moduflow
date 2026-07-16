# Status: Verified Code-Review Intake and Remediation Routing

Issue: `089-verified-code-review-intake-and-remediation-routing`

## Phase

Implementation complete and verified; staged product review is next.

## Progress

- Added immutable `moduflow.review-intake.v1` packets with source retention, SHA-256 provenance, target identity, stable finding fingerprints, and append-only decision history.
- Added manual, GitHub review-thread, CodeQL alert, and SARIF adapters with lazy trigger selection.
- Added Router proposals, independent Verifier requirements, deterministic security/release policy, and `accept` / `partial_accept` / `defer` / `reject` decisions.
- Added security, pre-release, and post-release-refactor candidates with priority, dependencies, CognitiveDemand, exact deduplication, overlap hints, and bidirectional trace.
- Added preview-first CLI, explicit local `--write`, atomic persistence, Korean summaries, candidate queues, templates, adapter registry, and `product:review --intake` routing.
- Bumped the plugin package from `0.3.24` to `0.3.25` for the feature release gate.

## Evidence

- TDD implementation commits: `f3804b9`, `962cae3`, `d539f22`, `c794028`, `e7f84c4`, `4bad53d`.
- Synthetic manual intake returned `action: preview`, schema `moduflow.review-intake.v1`, a reference SHA-256, invoked only manual/Superpowers adapters, and skipped GitHub/security/Spec Kit.
- Dry-run left `workspace/reviews` absent; the user's external review source was neither read nor copied during dogfood.
- Source-adapter verification: 5 tests passed.
- Review-intake focused verification: 44 tests passed.
- Full `unittest` discovery passed with zero failures.
- Spec consistency: 0 errors, 0 warnings, 0 info findings.
- `validate_moduflow.py`: passed, 145 required files checked.
- `validate_project_artifacts.py`: passed; only pre-existing non-blocking optional/link-role warnings remain.
- `release_check.py`: passed all package, artifact, linkage, lint, security, version, test, doctor, and documentation gates.

## Changed Surfaces

- Domain and CLI: `scripts/review_intake.py`, `scripts/project_review.py`
- Adapters and policy: `adapters/github-review.yaml`, `adapters/security-review.yaml`, `adapters/superpowers.yaml`, `overlays/review-policy.yaml`, `vendor.lock.json`
- Commands and routing: `commands/product-review.md`, `skills/index/SKILL.md`
- Templates: `templates/reviews/review-intake.json`, `templates/reviews/review-summary.ko.md`, `templates/reviews/review-candidates.md`
- Verification: `tests/test_review_intake.py`, `tests/test_project_review.py`, `tests/test_validation_distribution.py`

## Known Limitations

- Intake does not reply to or resolve GitHub threads, publish GitHub issues, implement findings, or bypass release gates; each remains a separate explicit workflow.
- The dogfood used synthetic structured findings and made no live GitHub or security-service call.
- Issue 094 owns enforcement of risk-based security and release checks beyond this intake/routing layer.
- Independent review execution is the next staged-review concern; no subagent was used during inline implementation.

## Blockers

- None for implementation. Issue 094 remains downstream of this issue.

## Next Command

`product:review 089-verified-code-review-intake-and-remediation-routing`
