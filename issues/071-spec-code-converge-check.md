# Issue: `071-spec-code-converge-check`

**Status: active** — created 2026-07-05, spec 2026-07-06, plan 2026-07-06, started 2026-07-06.
**Priority: p1**

## Outcome

After implementation (and any time later), a converge pass assesses the actual code against an issue's spec/plan/tasks and reports divergence — missing, partial, contradicting, or unrequested behavior — optionally appending follow-up tasks, so "the code still matches the spec" stays checkable after the done commit.

## Why

Benchmark (knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md): both major spec-driven comparators grew this — spec-kit `/speckit.converge` (append-only gap tasks, severity-classified) and OpenSpec `/opsx:verify` (optional quality report; archive blocking is a separate deterministic validator — corrected 2026-07-06 by mechanism benchmark). ModuFlow's drift gate covers lifecycle state, not artifact-vs-code. The spec-kit adapter's reviewed note already flagged converge as watched-but-unabsorbed.

## Scope

### In

- A converge flow (likely subagent-driven, per the model-tier convention) comparing implementation reality against `specs/<id>/` artifacts for a given issue; severity-graded findings; optional append of follow-up tasks to tasks.md.
- Position in the pipeline: recommended after `product:review`, runnable standalone anytime.

### Out

- Not a hard release gate in v1 (review already gates); promote later if divergence recurs.
- No whole-repo continuous scanning — per-issue, on demand.

## Acceptance Criteria

- Fixture where code omits a spec AC → reported missing; where code adds unspecified behavior → reported unrequested.
- Findings append-only; never edits spec/plan retroactively.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `070-spec-consistency-analyze`
- related: `067-upstream-adapter-absorption` (where converge was first flagged as a watch item)

## Sessions

- 2026-07-05: Registered from the competitive-gap benchmark (priority 3 of 5, post-implementation half).

## Workflow Tasks

- [x] spec → `specs/071-spec-code-converge-check/spec.md` (+ `spec.ko.md`)
- [x] plan → `specs/071-spec-code-converge-check/plan.md` (+ tasks.md, spec_consistency clean)
- [x] execute → commits `8a62d24` (wave 1), `87ea20a` (wave 2), D1 dogfood
- [x] review → specs/071-spec-code-converge-check/review.md (pass; self-converge caught+resolved 1 high)

## Links

- Benchmark (existence): `knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md`
- Benchmark (mechanism): `memory/evidence/2026-07-06-converge-mechanism-benchmark.md`
- Spec: `specs/071-spec-code-converge-check/spec.md`

## Next Command

`/product:execute 071-spec-code-converge-check`
