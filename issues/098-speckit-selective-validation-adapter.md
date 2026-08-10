# Issue 098: Spec Kit Selective Validation Adapter

**Status: active** — created and specified 2026-08-10.
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
- [ ] benchmark → compare selected Spec Kit functions against native ModuFlow checks
- [ ] plan → pending user approval of the written spec
- [ ] execute → PR / commits
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

## Links

- Spec: `specs/098-speckit-selective-validation-adapter/spec.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:plan 098-speckit-selective-validation-adapter`
