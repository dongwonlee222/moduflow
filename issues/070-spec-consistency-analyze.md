# Issue: `070-spec-consistency-analyze`

**Status: backlog** — created 2026-07-05.

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

## Sessions

- 2026-07-05: Registered from the competitive-gap benchmark (priority 3 of 5, pre-execution half).

## Links

- Benchmark: `knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md`

## Next Command

`/product:status`
