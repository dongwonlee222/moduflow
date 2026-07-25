# Issue 093: Frontmatter Issue Schema and Readiness/Dependency Gate

**Status: active** — created 2026-07-16, started 2026-07-22, planned 2026-07-22, implementation verified 2026-07-25.
**Priority: p1**

## Summary

Normalize YAML-frontmatter and Markdown issue formats through one parser, then block ready/execute routing when dependencies, definition readiness, lifecycle state, body status, or next command contradict one another.

## Source

- Type: verified external-review workflow dogfood
- Link: ModuPay Biz BIZ-038–040 audit, local Codex session 2026-07-16
- Owner / decision maker: Dongwon Lee
- Current phase: execute verified; review next

## Problem

ModuFlow’s current lifecycle parser recognizes canonical Markdown `Status`, `Priority`, and `Blocked-by` fields but does not normalize project issue schemas that use YAML frontmatter such as `canonical_state`, `status`, `definition_readiness`, `gate_state`, and `depends_on`. In the ModuPay Biz dogfood project, validation returned valid with zero lifecycle drift even though issues could declare an unfinished dependency, `status: ready`, and an execute command at the same time.

## Product Decision

- A single issue parser supports canonical Markdown and versioned frontmatter adapters.
- When `schema_version` frontmatter exists, `canonical_state` is lifecycle truth; the Markdown status line is its human projection and must agree.
- When frontmatter has no `schema_version`, Markdown remains canonical; known frontmatter fields produce migration warnings and may conservatively block execution, but cannot advance readiness.
- `depends_on` normalizes to the same dependency graph as `Blocked-by`.
- `definition_readiness`, `gate_state`, lifecycle state, dependencies, and artifact phase are separate fields with explicit allowed transitions.
- `next_command` is derived and validated; it cannot skip unmet dependencies, required spec/plan work, or a blocked gate.
- Migration reports proposed fixes and never silently rewrites project issues.

## Scope

### In

- Versioned adapters for canonical Markdown and YAML-frontmatter issue schemas.
- A normalized `moduflow.issue.v2` read model consumed by lifecycle, ready queue, doctor, dashboard, MCP, and validation.
- Drift checks for frontmatter/body status, duplicate fields, unsupported values, and contradictory readiness.
- Dependency and next-command enforcement for active/ready/execute transitions.
- Migration/report mode for existing projects with mixed schemas.
- Regression fixtures from BIZ-033/BIZ-038/BIZ-039/BIZ-040.

### Out

- Automatically rewriting all legacy issue files.
- Treating `status`, `gate_state`, and `definition_readiness` as synonyms.
- Replacing project-specific issue namespaces or GitHub projection.

## Acceptance Criteria

- Frontmatter `depends_on` appears in ready/blocked queries and cycle/dangling-reference validation.
- An issue with an unfinished dependency cannot be ready, active, or routed to execute.
- `definition_readiness: draft` cannot route past `product:spec` unless the issue type explicitly declares a documented exception.
- Frontmatter lifecycle and Markdown `Status` disagreement is reported as drift.
- Contradictory `canonical_state`, `status`, `gate_state`, and `next_command` values produce actionable errors.
- BIZ-038/039 are reported blocked by active BIZ-033; BIZ-040 is routed to spec.
- Every consumer uses the shared normalized parser.
- Focused tests and `python3 scripts/release_check.py .` pass.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*issue*schema*.py' -v`
- `python3 -m unittest tests.test_issue_dependencies tests.test_project_loop -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_lifecycle.py`
- `scripts/project_loop.py`
- `scripts/validate_project_artifacts.py`
- `scripts/issue_generator.py`
- `scripts/mcp_server.py`
- `templates/issues/`
- `tests/`

## Scope Fence

Do not introduce separate parsers in lifecycle, dashboard, or MCP consumers. Schema adaptation and normalization belong in one shared parser.

## Workflow Tasks

- [x] spec → `specs/093-frontmatter-issue-schema-readiness-gate/spec.md` + `spec.ko.md`
- [x] plan → `specs/093-frontmatter-issue-schema-readiness-gate/plan.md` + `tasks.md`
- [x] execute → implementation/evidence commits `0354c7b`–`ab682e3`; verification in `specs/093-frontmatter-issue-schema-readiness-gate/status.md`
- [ ] review → `specs/<issue-id>/review.md` (replace with the concrete link when created)

## Related Issues

- follows_up: `048-artifact-lifecycle-sync`, `069-issue-dependency-priority-model`, `075-issue-less-context-capture`, `077-implementation-readiness-gate`
- related: `089-verified-code-review-intake-and-remediation-routing`
- blocks:
- blocked_by:

## Sessions

- 2026-07-16: ModuPay Biz review dogfood proved that the current validator ignores frontmatter dependencies/readiness and can report contradictory issues as valid.
- 2026-07-22: Dongwon Lee approved a shared-normalizer design. Unversioned frontmatter keeps Markdown canonical, emits migration guidance, and cannot advance an issue to ready/execute.
- 2026-07-22: Implementation plan split the work into parser/model, structural gate/report, consumer convergence, authoring compatibility, and full verification streams.
- 2026-07-25: E2 passed spec consistency, 732 full tests, project validation, lifecycle drift, release check, and diff hygiene; implementation remains active for independent review.

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Spec: `specs/093-frontmatter-issue-schema-readiness-gate/spec.md`
- Korean Spec: `specs/093-frontmatter-issue-schema-readiness-gate/spec.ko.md`
- Plan: `specs/093-frontmatter-issue-schema-readiness-gate/plan.md`
- Tasks: `specs/093-frontmatter-issue-schema-readiness-gate/tasks.md`
- Status: `specs/093-frontmatter-issue-schema-readiness-gate/status.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/23

## Next Command

`product:review 093-frontmatter-issue-schema-readiness-gate`
