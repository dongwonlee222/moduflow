# Issue 089: Verified Code-Review Intake and Remediation Routing

**Status: backlog** — created 2026-07-16.
**Priority: p1**

## Summary

Verify external code-review findings before disposition, record evidence and conflicts, route accepted remediation by release risk, and generate reviewable GitHub issue candidates plus CognitiveDemand metadata.

## Source

- Type: user product direction
- Link: local Codex session, 2026-07-16
- Owner / decision maker: Dongwon Lee
- Original requested ID: `082`; mapped to `089` because local issue `082` already exists.
- Current phase: backlog

## Problem

External review text can contain valid findings, incomplete suggestions, architectural conflicts, or unsupported “no-risk” claims. Treating review prose as truth creates unsafe fixes and noisy issues; ignoring it loses useful evidence. ModuFlow needs a verified intake state between review receipt and remediation work.

## Product Decision

- Every finding receives one disposition: `accept`, `partial_accept`, `defer`, or `reject`.
- Every review preserves source authorship and target provenance: provider, received date, repository, branch/commit, and a permitted source representation (`copy`, `reference`, or `hash_only`).
- Each finding receives a stable ID and separates observed facts, reviewer recommendations, and root-cause hypotheses.
- A disposition records source, affected files, reproduction evidence, tests, architectural/import-boundary conflicts, rationale, and reviewer confidence.
- “No risk” remains `unverified` until relevant tests and import boundaries are checked.
- Accepted work routes to `security`, `pre_release`, or `post_release_refactor` remediation lanes.
- Generated issues are candidates in canonical Git files first; GitHub issue creation remains opt-in.
- Each candidate includes CognitiveDemand and the evidence supporting that routing choice.
- A finding-to-issue trace matrix preserves which findings were grouped, split, deferred, or rejected; implementation plans remain owned by one issue or explicitly link child plans.

## Scope

### In

- A machine-readable review finding and disposition schema.
- A durable review-intake packet containing source ownership, retention mode, source path/link/hash, target repository and commit, received date, and verification timestamp.
- Intake from pasted external review, PR comments, review artifacts, or security findings.
- Evidence checks for referenced files, tests, architecture rules, and import boundaries.
- Partial-acceptance support that separates valid observations from unsuitable remedies.
- Remediation routing by security and release timing.
- Candidate issue generation with deduplication hints, dependencies, priority, and CognitiveDemand.
- Finding-to-issue traceability, including grouped findings and cross-issue program context without replacing per-issue plans.
- Human-reviewable summary before GitHub sync or implementation.

### Out

- Automatically implementing every accepted suggestion.
- Automatically creating remote GitHub issues without explicit opt-in.
- Treating reviewer authority or confidence as proof.
- Replacing `product:review` or security tooling.

## Acceptance Criteria

- Every imported finding has a source link or source description and an explicit verification state.
- Source ownership is retained, and the packet records `copy`, `reference`, or `hash_only` without silently copying sensitive or externally owned material.
- Every finding has a stable ID plus separate observation, recommendation, and root-cause-hypothesis fields.
- Accept, partial accept, defer, and reject decisions require recorded rationale.
- Missing files, failing reproduction, architecture conflicts, and import-boundary conflicts are visible evidence fields.
- “No risk” cannot become verified without relevant test and boundary evidence.
- Accepted findings route to security, pre-release, or post-release-refactor work.
- Candidate issues contain scope, evidence, priority, dependency hints, CognitiveDemand, and next command.
- Duplicate or overlapping candidates are linked to existing issues instead of blindly recreated.
- Every accepted/partial finding maps to one or more candidate issues, and every candidate lists its finding IDs.
- A shared remediation plan cannot make multiple child issues executable unless each issue links its own approved plan or an explicit child-plan section.
- GitHub synchronization is explicit and uses the canonical repository identity from Issue 088 when available.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*review*intake*.py' -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `commands/product-review.md`
- `commands/product-issue.md`
- `scripts/project_review.py`
- `scripts/project_intake.py`
- `scripts/issue_generator.py`
- `scripts/worker_orchestrator.py`
- `templates/`
- `templates/reviews/`
- `tests/`

## Scope Fence

Do not auto-apply review suggestions or publish GitHub issues. The v1 result is a verified, auditable routing decision and a human-reviewable candidate queue.

## Workflow Tasks

- [ ] spec → `specs/089-verified-code-review-intake-and-remediation-routing/spec.md`
- [ ] plan → `specs/089-verified-code-review-intake-and-remediation-routing/plan.md`
- [ ] execute → intake schema, verifier, remediation router, candidate generator, and tests
- [ ] review → `specs/089-verified-code-review-intake-and-remediation-routing/review.md`

## Related Issues

- follows_up: `030-worker-cognitive-demand-model-routing`, `031-goal-driven-autonomous-benchmarking-and-issue-generation`, `039-automated-review-checklists-and-safety-lint-gates`, `051-autonomous-execute-review-visual-handoff`, `052-draft-pr-review-handoff`
- related: `054-github-issue-sync`, `071-spec-code-converge-check`, `087-korean-github-pr-review-surface`, `088-canonical-repository-remote-identity-gate`
- blocks: `094-risk-based-security-and-quality-review-gate`
- blocked_by:

## Reference Implementations

- GitHub Code Scanning alert states, dismissal reasons, and audit comments: `https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-code-scanning-alerts/resolve-alerts`
- GitHub Code Scanning REST disposition fields: `https://docs.github.com/en/rest/code-scanning/code-scanning`
- Renovate Dependency Dashboard approval and candidate promotion: `https://docs.renovatebot.com/key-concepts/dashboard/`

## Sessions

- 2026-07-16: User approved verified review intake and remediation routing after reviewing the public implementation patterns.
- 2026-07-16: ModuPay Biz dogfood added source authorship/retention, finding IDs, fact-vs-hypothesis separation, and finding-to-issue trace requirements.

## Links

- Roadmap: `workspace/roadmap.md`
- Goal: `workspace/goal.md`
- Dogfood: `modu-biz/workspace/reviews/2026-07-16-external-code-review.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/19

## Next Command

`product:spec 089-verified-code-review-intake-and-remediation-routing`
