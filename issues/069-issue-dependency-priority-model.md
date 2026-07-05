# Issue: `069-issue-dependency-priority-model`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.

## Outcome

Issue files carry structured `blocked_by`/`blocks` dependency edges and a `priority` field (additive Markdown metadata, not a database), and a "ready work" query answers "what can I safely start now" — unblocked issues sorted by priority — instead of requiring a human to infer execution order from prose.

## Why

Benchmark (knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md): the flat `Status:`-only data model is the single biggest structural gap versus every compared tracker — dependency-aware ready queries are beads' entire thesis (`bd ready`, atomic claim), and Task Master ships `next`/`clusters`. Without edges, ModuFlow's parallel-worker story cannot scale past a handful of issues, and two workers can pick the same issue with no collision guard.

## Scope

### In

- Additive metadata on `issues/*.md` (e.g. structured lines alongside the canonical Status line): `blocked_by`, `blocks`, `priority: p0-p3`.
- A ready-work computation in the lifecycle/sync layer: backlog issues whose blockers are all done, priority-sorted.
- Surface in `product:status` dashboard (대기열 becomes dependency-aware) and, once `068` lands, as an MCP/JSON query.
- Validation: dependency cycles and dangling references become drift-gate errors.

### Out

- No estimates/complexity scoring in v1 (add later if PRD decomposition is pursued).
- No hash-based IDs or atomic claim primitive yet — single-operator reality today; revisit with multi-agent concurrency.

## Acceptance Criteria

- An issue blocked by a non-done issue is excluded from ready work; completing the blocker includes it.
- Cycle and dangling-reference detection fails validation with a clear message.
- Dashboard queue renders ready vs blocked distinctly.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `068-machine-query-surface`
- related: `048-artifact-lifecycle-sync` (same canonical-inline-metadata pattern)

## Workflow Tasks

- [x] spec → `specs/069-issue-dependency-priority-model/spec.md`
- [x] plan → `specs/069-issue-dependency-priority-model/plan.md`
- [x] execute → `scripts/project_lifecycle.py`, `scripts/mcp_server.py`, `templates/issues/issue.md`, `scripts/issue_generator.py`, `commands/product-issue.md`, `commands/product-status.md`, `tests/test_issue_dependencies.py`

## Sessions

- 2026-07-05: Registered from the competitive-gap benchmark (priority 2 of 5).
- 2026-07-05: Executed. Design fixed in spec: `Blocked-by` is the only stored edge (blocks derived — dual storage would drift), priority p0-p3 defaulting p2, inline bold lines per the 048 convention. Implementation subagent (TDD 9+2 cases) delivered parsers, `ready_issues` + `--ready` CLI, `moduflow_ready` MCP tool, dependency drift gates (dangling refs, cycles scoped to open issues), the `templates/issues/issue.md` pre-048-schema latent-defect repair, and p1/p2 backfill on 070-073. Independent verification: SPEC pass / QUALITY fail with 4 findings — prose quoting the metadata syntax parsed as real metadata (fixed: parsing scoped to the pre-section header region, line-anchored), RecursionError on ~2500-node dependency chains (fixed: iterative DFS), orphaned `issue_generator.py` still emitting the pre-048 schema (fixed: canonical Status/Priority output; its stale test updated), and active-issues-with-unmet-blockers having zero signal anywhere (fixed as a recorded scope addition: new drift entry + tests). Final: 15 dependency tests, 265 full suite, drift `[]`, release_check valid. Implementer self-reported one no-sub-delegation violation, self-caught, conclusions independently re-derived — no output contamination.

## Links

- Benchmark: `knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md`

## Next Command

`/product:status`
