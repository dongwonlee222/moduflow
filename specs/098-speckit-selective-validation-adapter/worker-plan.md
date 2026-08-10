# Worker Plan: 098-speckit-selective-validation-adapter

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `implementation-worker` | `sequential` | ready | scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py, templates/moduflow-capabilities.json | - | A1 Implement strict project opt-in, deterministic function selection, path containment, host availability, configuration dry-run/write, and stable handoff outcomes. |
| T02 | `implementation-worker` | `sequential` | ready | scripts/sync_spec_kit_templates.py, tests/test_spec_kit_vendor_assets.py, vendor/spec-kit/0.16.1/manifest.json, vendor/spec-kit/0.16.1/commands/clarify.md, vendor/spec-kit/0.16.1/commands/analyze.md, vendor/spec-kit/0.16.1/commands/checklist.md, vendor/spec-kit/0.16.1/commands/converge.md, adapters/spec-kit.yaml, vendor/README.md | A1 | B1 Pin the four official 0.16.1 templates at SHA `684b3d8e`, add the exact-hash manifest and atomic sync tool, and document the selective adapter policy. |
| T03 | `roadmap-planner` | `sequential` | ready | overlays/spec-kit/selective-validation-policy.md, scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py | B1 | C1 Add the higher-priority safety overlay, strict host-result schema, deterministic run IDs, advisory Markdown rendering, and append-only duplicate-safe `validation.md` persistence. |
| T04 | `release-manager` | `sequential` | ready | skills/spec-kit-validation-bridge/SKILL.md, adapters/capability-routing.json, commands/moduflow.md, skills/index/SKILL.md, skills/pm-execution-router/SKILL.md, tests/test_capability_routing.py, tests/test_validation_distribution.py | C1 | D1 Connect one-function bridge consumption to Issue 097 routing while preserving lifecycle aliases, native fallbacks, default-unavailable behavior, and all implementation/Git/review/release ownership boundaries. |
| T05 | `qa-reviewer` | `sequential` | ready | scripts/spec_kit_pilot.py, tests/test_spec_kit_pilot.py, tests/fixtures/spec-kit-selective-validation/cases.json, tests/fixtures/spec-kit-selective-validation/results, scripts/validate_moduflow.py, tests/test_validation_distribution.py, .claude-plugin/plugin.json, .codex-plugin/plugin.json, specs/098-speckit-selective-validation-adapter/implementation-readiness.json, specs/098-speckit-selective-validation-adapter/pilot-report.md, specs/098-speckit-selective-validation-adapter/status.md, issues/098-speckit-selective-validation-adapter.md, .moduflow/state.json, workspace/goal.md, workspace/loop-state.json, workspace/dashboard.md, workspace/roadmap.md | D1 | E1 Add at least 13 successful/fallback/ownership fixtures, deterministic value/cost/overlap/safety metrics, the pilot report, package inventory, patch version bump, full verification, lifecycle evidence, and review handoff. |

## Isolation

- T01: `codex/098-speckit-selective-validation-adapter-t01`
- T02: `codex/098-speckit-selective-validation-adapter-t02`
- T03: `codex/098-speckit-selective-validation-adapter-t03`
- T04: `codex/098-speckit-selective-validation-adapter-t04`
- T05: `codex/098-speckit-selective-validation-adapter-t05`

## Merge Order

- T01 → T02 → T03 → T04 → T05

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 1 touches shared state: A1 Implement strict project opt-in, deterministic function selection, path containment, host availability, configuration dry-run/write, and stable handoff outcomes.
- Task 2 touches shared state: B1 Pin the four official 0.16.1 templates at SHA `684b3d8e`, add the exact-hash manifest and atomic sync tool, and document the selective adapter policy.
- Task 3 touches shared state: C1 Add the higher-priority safety overlay, strict host-result schema, deterministic run IDs, advisory Markdown rendering, and append-only duplicate-safe `validation.md` persistence.
- Task 4 touches shared state: D1 Connect one-function bridge consumption to Issue 097 routing while preserving lifecycle aliases, native fallbacks, default-unavailable behavior, and all implementation/Git/review/release ownership boundaries.
- Task 5 touches shared state: E1 Add at least 13 successful/fallback/ownership fixtures, deterministic value/cost/overlap/safety metrics, the pilot report, package inventory, patch version bump, full verification, lifecycle evidence, and review handoff.
- scripts/spec_kit_adapter.py is expected by T01 and T03
- tests/test_spec_kit_adapter.py is expected by T01 and T03
- tests/test_validation_distribution.py is expected by T04 and T05

## Next Command

`product:execute 098-speckit-selective-validation-adapter`
