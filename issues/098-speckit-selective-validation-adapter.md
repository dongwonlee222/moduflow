# Issue 098: Spec Kit Selective Validation Adapter

**Status: done** — created and specified 2026-08-10, implemented and verified 2026-08-12, merged via PR #37 as `513e08f`, and installed locally as ModuFlow `0.3.48` on 2026-08-13.
**Priority: p2**
**Blocked-by:**

## Summary

Offer selected Spec Kit validation capabilities through ModuFlow on demand—`clarify`,
`analyze`, `checklist`, and `converge`—without handing Spec Kit ownership of implementation,
Git, issue state, memory, review, or release.

## Source

- Type: user product direction
- Link: local Codex session
- Date: 2026-08-10

## Opportunity

ModuFlow currently reviews Spec Kit as an upstream reference, but the `specify` CLI and skills
are not installed as an active runtime. Users therefore do not receive Spec Kit 0.16.1's
specialized clarification, cross-artifact analysis, requirements checklist, or convergence
workflow. A project-scoped, opt-in adapter can expose those specific capabilities only when a
request benefits from them while ModuFlow remains the source of truth.

## Scope

### In

- Detect whether the approved Spec Kit runtime is available before routing.
- Provide project-scoped opt-in activation for `clarify`, `analyze`, `checklist`, and
  `converge` only.
- Normalize findings into the owning ModuFlow issue/spec as advisory evidence with source,
  version, limitations, and next action.
- Define a safe fallback to native ModuFlow spec checks when Spec Kit is unavailable.
- Evaluate the four selected functions against representative ModuFlow specs before wider use.

### Out

- Making Spec Kit mandatory or globally active for every project.
- Delegating `implement`, Git/commit behavior, issues, status, roadmap, memory, PR, review, or
  release to Spec Kit.
- Installing community extensions in the initial pilot.
- Allowing Spec Kit artifacts to become a second source of truth.

## Acceptance Criteria

- Projects without Spec Kit continue to work unchanged and receive a truthful fallback result.
- Opted-in projects can request each selected capability through ModuFlow without memorizing a
  Spec Kit command.
- Every result links to the owning issue and canonical spec and identifies the Spec Kit version.
- The adapter never routes implementation, lifecycle, Git, review, or release work to Spec Kit.
- Pilot evidence compares value, latency/context cost, false positives, and overlap with native
  ModuFlow checks before the capability is recommended by default.
- `python3 scripts/release_check.py .` passes.

## Verification

- Representative fixture evaluation for all four selected capabilities
- Fallback tests with no `specify` runtime available
- `python3 -m unittest discover -s tests`
- `python3 scripts/release_check.py .`

## Entry Points

- `adapters/spec-kit.yaml`
- `commands/product-spec.md`
- `commands/product-plan.md`
- `commands/product-review.md`
- `scripts/spec_consistency.py`
- `scripts/project_converge.py`

## Scope Fence

Do not make Spec Kit mandatory, create a competing `.specify` lifecycle, install community
extensions, or route build/release ownership away from ModuFlow and Superpowers.

## Workflow Tasks

- [x] spec → `specs/098-speckit-selective-validation-adapter/spec.md`; Korean sidecar → `specs/098-speckit-selective-validation-adapter/spec.ko.md`
- [x] benchmark → compare selected Spec Kit functions against native ModuFlow checks
- [x] plan → `specs/098-speckit-selective-validation-adapter/plan.md`; tasks → `specs/098-speckit-selective-validation-adapter/tasks.md`
- [x] execute → implementation and deterministic request-driven pilot commits
- [ ] review → review notes

## Related Issues

- blocks:
- blocked_by: `097-single-entry-capability-routing-contract`
- duplicates:
- follows_up: `067-upstream-adapter-absorption`
- supersedes:
- related: `070-spec-consistency-analyze`, `071-spec-code-converge-check`, `079-plan-discipline-skill-matrix`

## Sessions

- 2026-08-10: User requested access to useful new Spec Kit capabilities without making
  ModuFlow heavy. Split from issue 097 so capability activation remains optional.
- 2026-08-10: User approved the recommended selective-template adapter. Official upstream at
  `684b3d8e` confirms the four capabilities are command templates rather than standalone CLI
  subcommands. The design pins only those templates and forbids upstream scripts/hooks/Git.
- 2026-08-11: User approved proceeding. The implementation plan defines five sequential TDD
  streams, exact upstream hashes, append-only result persistence, and a human pilot-decision gate.
- 2026-08-11: Plan consistency passed with zero findings and the report-only implementation
  readiness gate is `ready` across all seven checks.
- 2026-08-11: The selective adapter, pinned templates, safety overlay, bridge, and initial
  offline pilot are prepared for review. Safety counters are zero; the human value/activation
  decision remains pending and wider/default activation is prohibited.
- 2026-08-11: Task 5 verification passed 131/131 focused tests and 1,133/1,133 full tests;
  spec consistency is 0/0/0, lifecycle drift is empty, package/project validation is valid,
  and the release check is green.
- 2026-08-11: Whole-branch remediation replaced shape-only persistence with current-handoff
  revalidation and locked atomic append, enforced no-follow config/input/output containment,
  derived canonical input/context evidence through the real router/adapter pilot, and kept the
  human activation decision pending with default availability false. The first remediation-pass focused
  matrix passed 146/146 in 62.199 seconds, fresh full discovery passed 1,145/1,145 in 308.012
  seconds, and package validation checked 174 required files.
- 2026-08-12: Conservative intent-boundary review removed the open-ended ownership parser and
  replaced it with an auditable finite English/Korean request grammar. The release pilot is now a
  fixed 24-case matrix: eight canonical successes, four availability fallbacks, and twelve grammar
  fallbacks. Noncanonical candidates return a canonical retry before loading config, templates,
  project inputs, or outputs; default activation and the human decision remain unchanged.
- 2026-08-12: Final verification passed the 24/24 deterministic pilot twice with identical evidence
  hashes, 167/167 focused tests, 1,168/1,168 full tests, 18/18 spec coverage, empty lifecycle drift,
  174-file package validation, and the complete release gate at version 0.3.48.
- 2026-08-13: Dongwon Lee approved the selective, on-demand model and asked to finish integration.
  PR #37 passed GitHub CI and merged as `513e08f`; local `main` was synchronized and the Codex
  personal plugin cache was refreshed to `0.3.48+codex.20260810222010`. Wider/default activation
  remains prohibited; project opt-in is still explicit.

## Links

- Spec: `specs/098-speckit-selective-validation-adapter/spec.md`
- Plan: `specs/098-speckit-selective-validation-adapter/plan.md`
- Tasks: `specs/098-speckit-selective-validation-adapter/tasks.md`
- Readiness: `specs/098-speckit-selective-validation-adapter/implementation-readiness.json`
- Pilot: `specs/098-speckit-selective-validation-adapter/pilot-report.md`
- Status: `specs/098-speckit-selective-validation-adapter/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:status`
