# Review Handoff: 098-speckit-selective-validation-adapter

## Purpose

Continue through implementation review without asking the user to manually decide each next step.
The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.

## Implementation Subagent

- Worker: `implementation-worker`
- Goal: review the completed implementation tasks and identify missing code/doc changes before review.
- Input artifacts:
  - `issues/098-speckit-selective-validation-adapter.md`
  - `specs/098-speckit-selective-validation-adapter/spec.md`
  - `specs/098-speckit-selective-validation-adapter/tasks.md`

### Implementation Tasks

- [x] A1 Implement strict project opt-in, deterministic function selection, path containment, host availability, configuration dry-run/write, and stable handoff outcomes. [files: scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py, templates/moduflow-capabilities.json] [shared_state: true]
- [x] B1 Pin the four official 0.16.1 templates at SHA `684b3d8e`, add the exact-hash manifest and atomic sync tool, complete manifest/hash handoff verification, and document the selective adapter policy. [files: scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py, scripts/sync_spec_kit_templates.py, tests/test_spec_kit_vendor_assets.py, vendor/spec-kit/0.16.1/manifest.json, vendor/spec-kit/0.16.1/commands/clarify.md, vendor/spec-kit/0.16.1/commands/analyze.md, vendor/spec-kit/0.16.1/commands/checklist.md, vendor/spec-kit/0.16.1/commands/converge.md, adapters/spec-kit.yaml, vendor/README.md] [depends: A1] [shared_state: true]
- [x] C1 Add the higher-priority safety overlay, strict host-result schema, deterministic run IDs, advisory Markdown rendering, and append-only duplicate-safe `validation.md` persistence. [files: overlays/spec-kit/selective-validation-policy.md, scripts/spec_kit_adapter.py, tests/test_spec_kit_adapter.py] [depends: B1] [shared_state: true]
- [x] D1 Connect one-function bridge consumption to Issue 097 routing while preserving lifecycle aliases, native fallbacks, default-unavailable behavior, and all implementation/Git/review/release ownership boundaries. [files: skills/spec-kit-validation-bridge/SKILL.md, adapters/capability-routing.json, commands/moduflow.md, skills/index/SKILL.md, skills/pm-execution-router/SKILL.md, scripts/spec_kit_adapter.py, tests/test_capability_routing.py, tests/test_spec_kit_adapter.py, tests/test_validation_distribution.py] [depends: C1] [shared_state: true]
- [ ] E1 Add at least 13 successful/fallback/ownership fixtures, deterministic value/cost/overlap/safety metrics, the pilot report, package inventory, patch version bump, full verification, lifecycle evidence, and review handoff. [files: scripts/spec_kit_pilot.py, tests/test_spec_kit_pilot.py, tests/fixtures/spec-kit-selective-validation/cases.json, tests/fixtures/spec-kit-selective-validation/results, scripts/validate_moduflow.py, tests/test_validation_distribution.py, .claude-plugin/plugin.json, .codex-plugin/plugin.json, specs/098-speckit-selective-validation-adapter/implementation-readiness.json, specs/098-speckit-selective-validation-adapter/pilot-report.md, specs/098-speckit-selective-validation-adapter/status.md, specs/098-speckit-selective-validation-adapter/review-handoff.md, issues/098-speckit-selective-validation-adapter.md, .moduflow/state.json, workspace/goal.md, workspace/loop-state.json, workspace/dashboard.md, workspace/roadmap.md] [depends: D1] [shared_state: true]

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
python3 scripts/project_memory.py . --issue 098-speckit-selective-validation-adapter
```

- Dashboard output: `memory/dashboard.html`
- Issue drill-down output: `memory/issue-098-speckit-selective-validation-adapter.html`
- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.

## Final Report Contract

- Summarize implementation changes.
- Summarize implementation-worker findings.
- Summarize QA reviewer findings.
- Summarize PM/spec reviewer findings.
- Include verification command results.
- Include dashboard HTML path: `memory/dashboard.html`.
- Include issue drill-down path: `memory/issue-098-speckit-selective-validation-adapter.html`.

## Source Snapshot

- Issue bytes: 5632
- Spec bytes: 15102
- Status bytes: 1486
