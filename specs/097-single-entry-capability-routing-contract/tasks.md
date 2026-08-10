# Tasks: Single-Entry Capability Routing Contract

Issue: `097-single-entry-capability-routing-contract`
Plan: `specs/097-single-entry-capability-routing-contract/plan.md`

## Stream A

- [x] A1 Add `adapters/capability-routing.json`, fail-closed stdlib loading, descriptor validation, and focused registry tests. [files: adapters/capability-routing.json, scripts/capability_routing.py, tests/test_capability_routing.py] [shared_state: true]

## Stream B

- [x] B1 Implement deterministic `none | delegate | sequence | clarify` routing, one-specialist default, ordered artifact gates, availability fallback, permission projection, read-only CLI, and focused tests. [files: scripts/capability_routing.py, tests/test_capability_routing.py] [depends: A1] [shared_state: true]

## Stream C

- [x] C1 Add at least 24 golden fixtures across eight boundary classes, Korean/English semantic pairs, independent safety metrics, deterministic report/write behavior, non-zero failure exit, and mutation tests. [files: tests/fixtures/capability-routing/cases.json, scripts/capability_routing_simulation.py, tests/test_capability_routing_simulation.py] [depends: B1] [shared_state: true]

## Stream D

- [x] D1 Wire `/moduflow`, index, and PM router guidance to the executable result; register all new files in package validation and distribution tests. [files: commands/moduflow.md, skills/index/SKILL.md, skills/pm-execution-router/SKILL.md, scripts/validate_moduflow.py, tests/test_validation_distribution.py] [depends: B1,C1] [shared_state: true]
- [x] D2 Generate readiness and simulation reports; run focused/full/consistency/project/lifecycle/release gates; record status and complete staged review with no open Critical or Important findings. [files: specs/097-single-entry-capability-routing-contract/implementation-readiness.json, specs/097-single-entry-capability-routing-contract/simulation-report.json, specs/097-single-entry-capability-routing-contract/status.md, issues/097-single-entry-capability-routing-contract.md, .moduflow/state.json, workspace/goal.md, workspace/loop-state.json, workspace/dashboard.md, workspace/roadmap.md] [depends: D1] [shared_state: true]

## Acceptance Coverage

- Lifecycle requests route to `none` → B1, C1.
- Bounded analytics, design, and implementation select one available specialist → A1, B1, C1.
- Multi-stage work is ordered, current-stage-only, and artifact-gated → B1, C1, D1.
- Delegation records adapter, reason, permission, availability, issue, and artifact → B1, C1.
- Unavailable capability returns truthful fallback → A1, B1, C1.
- At least 24 Korean/English offline fixtures cover all eight classes → C1.
- Fan-out, permission, false-claim, and missing-field safety metrics equal zero → C1, D2.
- No specialist execution, external mutation, new runtime, database, or plugin → A1–D2.
- Direct commands and Git-native artifacts remain compatible → D1, D2.

## Next

`product:pr 097-single-entry-capability-routing-contract`
