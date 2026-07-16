# Review Handoff: 089-verified-code-review-intake-and-remediation-routing

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/089-verified-code-review-intake-and-remediation-routing.md`
  - `specs/089-verified-code-review-intake-and-remediation-routing/spec.md`
  - `specs/089-verified-code-review-intake-and-remediation-routing/tasks.md`

### Implementation Tasks

- [x] implementation: T01 — add the immutable review packet, source retention/hash, finding identity, and validation core. [files: scripts/review_intake.py, tests/test_review_intake.py] [shared_state: true]
- [x] implementation: T02 — add manual, GitHub thread, CodeQL alert, SARIF, and trigger-based lazy source adapters. [files: scripts/project_review.py, tests/test_project_review.py] [depends: T01] [shared_state: true]
- [x] implementation: T03 — add Router/Verifier decision inputs and deterministic verification/disposition policy. [files: scripts/review_intake.py, tests/test_review_intake.py] [depends: T01,T02] [shared_state: true]
- [x] implementation: T04 — add remediation lanes, CognitiveDemand, exact deduplication, candidates, and bidirectional trace. [files: scripts/review_intake.py, tests/test_review_intake.py] [depends: T03] [shared_state: true]
- [x] implementation: T05 — add dry-run/write CLI, atomic packet persistence, Korean projection, candidate queue, and templates. [files: scripts/project_review.py, tests/test_project_review.py, templates/reviews/review-intake.json, templates/reviews/review-summary.ko.md, templates/reviews/review-candidates.md] [depends: T02,T04] [shared_state: true]
- [x] implementation: T06 — register GitHub/security/Superpowers adapters, policy overlay, distribution validation, and `product:review --intake` routing. [files: adapters/github-review.yaml, adapters/security-review.yaml, adapters/superpowers.yaml, overlays/review-policy.yaml, vendor.lock.json, scripts/validate_moduflow.py, tests/test_validation_distribution.py, commands/product-review.md, skills/index/SKILL.md] [depends: T05] [shared_state: true]
- [x] qa: T07 — run synthetic dry-run dogfood, focused/full verification, and record status without copying external review source text. [files: issues/089-verified-code-review-intake-and-remediation-routing.md, specs/089-verified-code-review-intake-and-remediation-routing/tasks.md, specs/089-verified-code-review-intake-and-remediation-routing/status.md] [depends: T06] [shared_state: true]

## Review Subagents

### QA Review

- Worker: `qa-reviewer`
- Goal: run verification, check acceptance criteria, and report regressions.
- Required commands:
  - `python3 -m unittest discover -s tests -v`
  - `python3 scripts/release_check.py .`

### PM / Spec Review

- Worker: `pm-strategist`
- Worker: `spec-architect`
- Goal: compare implementation against problem, goals, non-goals, and acceptance criteria.
- Constitution check (issue 073): verify against `workspace/constitution.md` and record the compliance line in review.md — `Constitution: v<X.Y> checked — no violations` or the violation list.

## Visual Handoff

Regenerate the ModuFlow dashboard and its issue drill-down before reporting completion.
The issue HTML is not a separate source artifact; it is a derived L2 view linked from the dashboard system.

```bash
python3 scripts/project_memory.py . --dashboard
```

```bash
python3 scripts/project_memory.py . --issue 089-verified-code-review-intake-and-remediation-routing
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-089-verified-code-review-intake-and-remediation-routing.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-089-verified-code-review-intake-and-remediation-routing.html`.

## Source Snapshot

- Issue bytes: 9982
- Spec bytes: 23607
- Status bytes: 3314
