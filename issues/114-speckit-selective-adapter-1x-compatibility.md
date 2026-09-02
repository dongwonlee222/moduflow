# Issue 114: Spec Kit Selective Adapter 1.x Compatibility

**Status: backlog** — created 2026-09-01.
**Priority: p1**
**Blocked-by: `112-execution-planner-and-backend-boundary`**

## Summary

Revalidate the four read-only Spec Kit functions against the official 1.x line and update the exact version/SHA pin only after template compatibility, safety boundaries, fallbacks, and pilot behavior pass.

## Source

- Type: user-requested upstream compatibility follow-up
- Owner / decision maker: Dongwon Lee
- Current adapter: Spec Kit `0.16.1` at SHA `684b3d8e`
- Official milestone: Spec Kit `1.0.0` released 2026-08-21
- Trend evidence: `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`

## Opportunity

Issue 098 intentionally pinned exact snapshots of `clarify`, `analyze`, `checklist`, and `converge`. Spec Kit has since reached 1.x and expanded its integration, preset, extension, and workflow model. Updating without reviewing the four templates and ownership boundaries could silently introduce a second plan/task/implementation lifecycle.

## Scope

### In

- Select one exact official 1.x release and commit SHA during spec review; do not track `main` or an unpinned latest tag.
- Diff the four approved templates, their invocation forms, inputs, outputs, mutation behavior, and assumptions against the pinned 0.16.1 snapshots.
- Revalidate the safety overlay, manifest hashes, contained reads, zero-write contract, canonical request grammar, native fallbacks, and deterministic pilot.
- Keep `clarify`, `checklist`, `analyze`, and `converge` project-opt-in and advisory.
- Verify Claude Code, Codex, and other integration formats do not change the host-neutral ModuFlow handoff contract.
- Record absorbed, adapted, and intentionally skipped upstream changes before updating `approved_version`, SHA, manifest, or vendored snapshots.

### Out

- Installing `.specify` into ModuFlow projects.
- Enabling Spec Kit `specify`, `plan`, `tasks`, `implement`, workflows, extensions, presets, hooks, Git operations, or lifecycle mutation.
- Automatic vendor update or version-range execution.
- Treating upstream 1.x as backward-compatible without evidence.

## Acceptance Criteria

- The current 0.16.1 adapter remains active until an exact 1.x version/SHA passes the complete compatibility review.
- Each of the four template changes has a documented disposition and new expected hash.
- The adapter performs zero project writes and cannot route `implement` or another non-approved function.
- Existing native fallbacks remain valid when Spec Kit is disabled, unavailable, or rejected.
- The fixed English/Korean pilot passes with deterministic evidence and zero ownership/safety violations.
- Upgrade and rollback instructions preserve the prior manifest and snapshots.
- No ModuFlow canonical spec, plan, task, lifecycle, review, PR, or release ownership transfers to Spec Kit.

## Verification

- Template/hash manifest verification against the exact upstream tag/SHA.
- Existing Issue 098 routing, grammar, containment, no-write, pilot, and distribution suites.
- Added compatibility cases for 1.x integration/skill invocation changes.
- `python3 scripts/release_check.py .`

## Entry Points

- `adapters/spec-kit.yaml`
- `vendor/spec-kit/`
- `scripts/spec_kit_adapter.py`
- `scripts/sync_spec_kit_templates.py`
- `scripts/spec_kit_pilot.py`
- `skills/spec-kit-validation-bridge/SKILL.md`

## Scope Fence

This is a replaceable read-only adapter refresh, not adoption of Spec Kit's full SDD runtime.

## Workflow Tasks

- [x] benchmark → `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`
- [x] design/scope → `docs/superpowers/specs/2026-09-01-execution-governance-scope-design.md`
- [ ] spec → `specs/114-speckit-selective-adapter-1x-compatibility/spec.md`
- [ ] upstream comparison → exact selected 1.x release/SHA/template disposition
- [ ] plan → `specs/114-speckit-selective-adapter-1x-compatibility/plan.md` + `tasks.md`
- [ ] execute → reviewed snapshots, manifest/pin, pilot, docs, and tests
- [ ] review → `specs/114-speckit-selective-adapter-1x-compatibility/review.md`

## Related Issues

- blocks:
- blocked_by: `112-execution-planner-and-backend-boundary`
- duplicates:
- follows_up: `067-upstream-adapter-absorption`, `098-speckit-selective-validation-adapter`
- supersedes:
- related: `070-spec-consistency-analyze`, `071-spec-code-converge-check`, `099-vendor-and-host-sync-drift-detection`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Benchmark: `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`
- External reference (official history): `https://github.com/github/spec-kit/blob/main/docs/history.md`

## Next Command

After Issue 112: `product:spec 114-speckit-selective-adapter-1x-compatibility`.
