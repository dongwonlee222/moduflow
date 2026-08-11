# Issue 098: Spec Kit Selective Validation Adapter

**Status: active** — created and specified 2026-08-10; planned 2026-08-11.
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
- 2026-08-11: The selective adapter, pinned templates, safety overlay, bridge, and 13-case
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
- 2026-08-11: Final re-review closed the remaining ownership-vocabulary, documented handoff CLI,
  pilot JSON error-boundary, and canonical-prerequisite fallback gaps with RED/GREEN coverage;
  13/13 pilot cases and 69/69 canonical ownership probes passed, the focused matrix passed
  152/152 in 67.582 seconds, and fresh full discovery passed 1,151/1,151 in 308.004 seconds.
  Phase remains review, default activation remains false, and the human decision remains pending.
- 2026-08-11: Final ownership re-review replaced global single-word blocking with lifecycle-resource
  and ambiguous-Git context while retaining unmistakable Git and explicit lifecycle ownership.
  Six ordinary English/Korean validation probes now cross adapter, router, and pilot paths without
  weakening the 69 canonical negative probes; activation and human decision remain unchanged.
- 2026-08-11: Phrase-level follow-up removed the remaining bag-of-words coupling: generic changes/
  files and plural stages no longer manufacture Git intent, while intrinsic Korean staging and
  other unmistakable operations remain context-free ownership boundaries. Eight positive probes
  and all 69 canonical negatives now execute through the real router/adapter pilot.
- 2026-08-11: Adjacent phrase-family follow-up extended the bounded classifier to direct Git
  files/changes/hunks/index/working-tree objects with optional state modifiers/prepositions and to
  lifecycle auxiliaries/adverbs/Korean modifiers. Nineteen table-driven adjacent negatives now run
  through adapter, router, and pilot while all eight positives and 69 canonical negatives remain
  protected; the focused matrix passed 161/161 and fresh full discovery passed 1,160/1,160.
- 2026-08-11: Clause/token follow-up replaced bounded filler/modifier enumeration with
  punctuation/sequence clause splitting and token-level Git operation/object plus lifecycle
  action/resource semantics. Metamorphic modifier insertion and domain-target advisory probes now
  protect the boundary, and release has a named canonical pilot-provenance gate that rejects stale
  input hashes, context costs, or run IDs.

## Links

- Spec: `specs/098-speckit-selective-validation-adapter/spec.md`
- Plan: `specs/098-speckit-selective-validation-adapter/plan.md`
- Tasks: `specs/098-speckit-selective-validation-adapter/tasks.md`
- Readiness: `specs/098-speckit-selective-validation-adapter/implementation-readiness.json`
- Pilot: `specs/098-speckit-selective-validation-adapter/pilot-report.md`
- Status: `specs/098-speckit-selective-validation-adapter/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:review 098-speckit-selective-validation-adapter`
