# Issue 097: Single-Entry Capability Routing Contract

**Status: backlog** — created 2026-08-10.
**Priority: p2**
**Blocked-by:**

## Summary

Turn ModuFlow's existing single entry point and on-demand guidance into an executable,
regression-tested capability routing contract that selects no specialist by default and at
most one specialist for a bounded request unless an ordered multi-stage handoff is justified.

## Source

- Type: user product direction
- Link: local Codex session
- Date: 2026-08-10

## Opportunity

`/moduflow`, the fast-path shaping router, and adapter bridges already give users one entry
point and keep specialist commands on demand. The remaining behavior is distributed across
prompt documents and coordinator judgment. Equivalent requests can therefore select different
specialists across sessions, overlapping plugins can both activate, and upstream prompt changes
can alter routing without a failing test.

A thin routing contract can make the current product promise enforceable without turning
ModuFlow into a monolithic super-plugin: the user talks to ModuFlow, specialists remain
replaceable, and every delegated result returns to the canonical issue and artifact chain.

## Scope

### In

- Define a capability descriptor for each supported specialist: trigger conditions,
  exclusions, availability, read/write permission class, and expected artifact handoff.
- Define a routing result with `none`, `delegate`, or ordered `sequence` outcomes, including
  the selected adapter, reason, permission class, and destination issue/artifact.
- Enforce the default rule: zero specialists for ordinary ModuFlow lifecycle work and at most
  one specialist for a bounded request.
- Allow an ordered sequence only for explicitly multi-stage work; never load or run every
  potentially relevant specialist at once.
- Add representative positive, negative, ambiguous, unavailable-capability, and permission
  regression cases.
- Keep `/moduflow` and natural-language aliases as the user-facing entry point while preserving
  direct `product:*` commands as a power-user escape hatch.

### Out

- Installing Spec Kit, PostHog, Sentry, Supabase, Vercel, or any other external plugin.
- Copying specialist implementations into ModuFlow.
- Replacing issues, specs, lifecycle state, roadmap, review, PR, release, or Git as source of
  truth.
- Automatically granting write access or performing external mutations without the existing
  approval boundary.
- Building a database-backed plugin registry or a general-purpose workflow engine.

## Acceptance Criteria

- Status, issue, roadmap, and other ordinary ModuFlow lifecycle requests route to `none`.
- A bounded analytics, design, or implementation request selects exactly one matching
  specialist when it is available.
- A multi-stage request returns an ordered sequence with explicit handoff artifacts instead of
  activating all matching specialists simultaneously.
- Every non-`none` decision records why the capability was selected, the required permission
  class, and where its result returns in the ModuFlow artifact chain.
- An unavailable specialist produces a safe fallback or a clear setup recommendation; it never
  silently pretends the capability ran.
- Equivalent representative requests produce stable routing results in automated tests.
- No new runtime, database, or mandatory external plugin is added.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest discover -s tests`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `commands/moduflow.md`
- `skills/index/SKILL.md`
- `skills/pm-execution-router/SKILL.md`
- `adapters/*.yaml`
- `scripts/project_intake.py`
- `tests/`

## Scope Fence

Do not install or execute a new specialist, change the canonical lifecycle model, copy upstream
runtime code, or broaden external write permissions in this issue.

## Workflow Tasks

Every artifact-producing step is tracked here.

- [x] spec → `specs/097-single-entry-capability-routing-contract/spec.md`
- [ ] plan → `specs/097-single-entry-capability-routing-contract/plan.md`
- [ ] execute → PR / commits
- [ ] review → review notes

## Related Issues

- blocks: `098-speckit-selective-validation-adapter`
- blocked_by:
- duplicates:
- follows_up: `026-simplify-command-and-folder-surface`, `055-command-surface-onboarding`, `067-upstream-adapter-absorption`, `076-product-context-interview-and-readiness-loop`, `079-plan-discipline-skill-matrix`
- supersedes:
- related: `082-cross-host-model-capability-routing`, `084-worker-prompt-context-budget`

## Sessions

- 2026-08-10: User chose a single ModuFlow entry point with replaceable specialist engines,
  default on-demand use, and minimal context/permission overhead. Approved the thin routing
  contract before any specialist activation work.

## Links

- Spec: `specs/097-single-entry-capability-routing-contract/spec.md`
- Korean spec: `specs/097-single-entry-capability-routing-contract/spec.ko.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:plan 097-single-entry-capability-routing-contract`
