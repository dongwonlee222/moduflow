# Tasks: Spec Kit Selective Validation Adapter

Issue: `098-speckit-selective-validation-adapter`
Plan: `specs/098-speckit-selective-validation-adapter/plan.md`

## Stream A

- [x] A1 Implement strict project opt-in, deterministic function selection, path containment, host availability, mutually exclusive configure/read-only-handoff/accepted-result CLI modes, and stable handoff outcomes. [files: scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py, templates/moduflow-capabilities.json] [shared_state: true]

## Stream B

- [x] B1 Pin the four official 0.16.1 templates at SHA `684b3d8e`, add the exact-hash manifest and atomic sync tool, complete manifest/hash handoff verification, and document the selective adapter policy. [files: scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py, scripts/sync_spec_kit_templates.py, tests/test_spec_kit_vendor_assets.py, vendor/spec-kit/0.16.1/manifest.json, vendor/spec-kit/0.16.1/commands/clarify.md, vendor/spec-kit/0.16.1/commands/analyze.md, vendor/spec-kit/0.16.1/commands/checklist.md, vendor/spec-kit/0.16.1/commands/converge.md, adapters/spec-kit.yaml, vendor/README.md] [depends: A1] [shared_state: true]

## Stream C

- [x] C1 Add the higher-priority safety overlay, strict host-result schema, deterministic input/run IDs, current-handoff revalidation, advisory Markdown rendering, and locked atomic duplicate-safe `validation.md` persistence. [files: overlays/spec-kit/selective-validation-policy.md, scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py] [depends: B1] [shared_state: true]

## Stream D

- [x] D1 Connect one-function bridge consumption to Issue 097 routing while enumerating complete English/Korean lifecycle aliases and Git operations, applying clause splitting and token-level lifecycle action/resource plus Git operation/object semantics across arbitrary modifiers without a bounded filler regex, preserving domain-target advisory validation, exact prerequisite fallback, default-unavailable behavior, and all implementation/review/release ownership boundaries. [files: skills/spec-kit-validation-bridge/SKILL.md, adapters/capability-routing.json, commands/moduflow.md, skills/index/SKILL.md, skills/pm-execution-router/SKILL.md, scripts/spec_kit_adapter.py, tests/test_capability_routing.py, tests/test_spec_kit_adapter.py, tests/test_validation_distribution.py] [depends: C1] [shared_state: true]

## Stream E

- [x] E1 Execute at least 13 real-router/adapter success/fallback/ownership requests plus 69 canonical ownership, 19 adjacent phrase-family ownership, 14 metamorphic insertion ownership, and 14 ordinary/domain-validation probes; derive input/context/cost/safety metrics from current bytes; gate release on canonical pilot provenance; enforce shared pilot JSON errors; and refresh the pilot report, package inventory, patch version, lifecycle evidence, and review handoff. [files: scripts/spec_kit_pilot.py, scripts/release_check.py, tests/test_spec_kit_pilot.py, tests/test_release_check.py, tests/fixtures/spec-kit-selective-validation/cases.json, tests/fixtures/spec-kit-selective-validation/results, scripts/validate_moduflow.py, tests/test_validation_distribution.py, .claude-plugin/plugin.json, .codex-plugin/plugin.json, specs/098-speckit-selective-validation-adapter/implementation-readiness.json, specs/098-speckit-selective-validation-adapter/pilot-report.md, specs/098-speckit-selective-validation-adapter/status.md, specs/098-speckit-selective-validation-adapter/review-handoff.md, issues/098-speckit-selective-validation-adapter.md, .moduflow/state.json, workspace/goal.md, workspace/loop-state.json, workspace/dashboard.md, workspace/roadmap.md] [depends: D1] [shared_state: true]

## Acceptance Coverage

- Missing/disabled/mismatched config returns truthful fallback without loading a template → A1, B1.
- Only four exact templates at the approved version/SHA/hash are eligible → B1.
- One explicit request loads at most one function after host and project gates pass → A1, D1.
- Read-only handoff JSON is executable from the documented CLI without `--accept-result`; mode and argument errors remain structured → A1.
- Upstream scripts, hooks, Git, handoffs, implementation, review, and release operations remain inert/out of scope → C1, D1, E1.
- `clarify` questions, `analyze` findings, `checklist` candidates, and `converge` work candidates remain advisory → C1, D1.
- Accepted evidence is append-only and duplicate runs are byte-stable no-ops → C1.
- At least 13 fixtures cover four successes, four disabled/unavailable cases, and five ownership boundaries → E1.
- Complete canonical lifecycle/Git alias probes, 19 adjacent variants, and 14 arbitrary modifier-insertion metamorphic variants pass through adapter, routing integration, and the real pilot path → D1, E1.
- Fourteen exact ordinary/domain-target validation contexts remain ready through adapter, routing integration, and the real pilot path → D1, E1.
- Release re-evaluates canonical pilot provenance and fails on snapshot input hash, context cost, or run ID drift → E1.
- Pilot reports value, latency, context cost, false positives, native overlap, and zero safety violations → E1.
- Full tests, validators, lifecycle drift, spec consistency, version bump, and release check pass → E1.

## Next Command

`product:review 098-speckit-selective-validation-adapter`
