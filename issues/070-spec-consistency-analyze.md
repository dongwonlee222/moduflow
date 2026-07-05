# Issue: `070-spec-consistency-analyze`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.
**Priority: p1**

## Outcome

A read-only `product:analyze`-style pass validates that an issue's spec.md, plan.md, and tasks.md agree with each other BEFORE execution starts: requirement-to-task coverage, duplicated/contradicting statements, ambiguous terms, terminology drift — reported as a severity-graded table.

## Why

Benchmark (knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md): ModuFlow's review checks the work against the spec, but nothing checks the planning artifacts against each other — the class of rework spec-kit's `/speckit.analyze` and Kiro's requirements analysis were purpose-built to prevent. Heuristic first; Kiro's SMT-based formal analysis explicitly deferred.

## Scope

### In

- A checker (script + command doc) over `specs/<id>/{spec,plan,tasks}.md`: every spec requirement/AC maps to ≥1 plan stream or task; flag vague quantifiers ("fast", "secure", "intuitive") lacking measurable criteria; flag plan streams with no tasks and tasks tracing to nothing.
- Wire as a recommended step in `product:plan`'s Next and a soft pre-execute check.

### Out

- No SMT/formal logic; no auto-rewriting of artifacts (report only).
- No EARS migration of existing specs (new-artifacts-forward if adopted at all).

## Acceptance Criteria

- Fixture with an uncovered requirement → reported with severity; fully-covered fixture → clean.
- Runs read-only; never mutates artifacts.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `071-spec-code-converge-check` (post-implementation counterpart)
- related: `046-planning-artifact-templates`

## Workflow Tasks

- [x] spec → `specs/070-spec-consistency-analyze/spec.md`
- [x] plan → `specs/070-spec-consistency-analyze/plan.md`
- [x] execute → `scripts/spec_consistency.py`, `tests/test_spec_consistency.py`, `commands/product-plan.md`, `commands/product-execute.md`

## Sessions

- 2026-07-05: Registered from the competitive-gap benchmark (priority 3 of 5, pre-execution half).
- 2026-07-05: Executed. Deterministic heuristic v1 per spec: coverage (AC-bullet token overlap vs plan+tasks, "possibly uncovered" warns), vague-term lint (no-digit bullets only, word-boundary), structural tracing (stream mismatch both directions, missing AC section, empty tasks), artifact-presence info findings — report-only, read-only, exit 0 with findings. Fence content excluded from scanning (069's prose-collision lesson applied). Implementation subagent additionally fixed a real pre-existing gate false positive it hit (validate_project_artifacts treating the placeholder `specs/<id>/{...}.md` in this issue's own scope text as a real link — guard skips <>{}-containing matches; verified non-masking) and honestly reported both that and diagnostic-only git stash/worktree use. Independent verification: SPEC pass / QUALITY pass — the out-of-plan gate fix triple-verified sound; 3 non-blocking findings, 2 fixed (coverage-threshold boundary test added; zero-token bullets no longer inflate coverage_checked), 1 accepted (vague terms inside inline backticks still linted — spec silent, revisit if noisy). Dogfood: specs/069 analyzed clean (7 AC checked, 0 flagged). Final: 14 module tests, 279 full suite, release_check valid.

## Links

- Benchmark: `knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md`

## Next Command

`/product:status`
