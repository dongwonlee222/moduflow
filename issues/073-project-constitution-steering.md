# Issue: `073-project-constitution-steering`

**Status: done** — created 2026-07-05, spec 2026-07-07, plan 2026-07-07, started 2026-07-07, done 2026-07-07.
**Priority: p2**

## Outcome

A standing, versioned project constitution (project-wide MUST/SHOULD principles: TDD, injectable-runner pattern, canonical-Markdown rule, model-tier policy, ask-first boundaries) that every spec/plan/review pass checks against — replacing per-plan re-authoring of Global Constraints with one governed source that plans reference and extend.

## Why

Benchmark (knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md): spec-kit versions a constitution consulted by every workflow command; Kiro's steering adds conditional (glob/semantic) loading. ModuFlow re-derives Global Constraints in each plan.md — this session alone re-stated the same house rules (runner injection, TDD order, no-live-calls-in-tests) in three separate task plans. A constitution also gives `070`'s analyzer a governance layer to check against.

## Scope

### In

- `workspace/constitution.md` (or `.moduflow/constitution.md`): numbered, semver-versioned principles with MUST/SHOULD force; amendment log.
- `product:spec`/`product:plan` templates reference it — plan Global Constraints become "constitution vX.Y plus these plan-specific additions".
- `product:review` verdicts include a constitution-compliance note.

### Out

- No Kiro-style conditional/glob auto-loading in v1 (single file, always applicable).
- No org/MDM multi-tier scoping.

## Acceptance Criteria

- Constitution exists with version + amendment history; plans reference it instead of restating shared rules.
- Review handoff template includes a constitution-check line.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `070-spec-consistency-analyze` (analyzer checks against it)
- related: `060-cross-agent-output-format-convention` (AGENTS.md governs output shape; constitution governs engineering principles)

## Sessions

- 2026-07-05: Registered from the competitive-gap benchmark (priority 5 of 5).

## Workflow Tasks

- [x] spec → `specs/073-project-constitution-steering/spec.md` (+ `spec.ko.md`; amendments human-gated, template+doc scope — user decisions 2026-07-07)
- [x] plan → `specs/073-project-constitution-steering/plan.md` (+ tasks.md; inline coordinator mode)
- [x] execute → constitution v1.0 draft + 5-surface wiring (inline)
- [x] review → specs/073-project-constitution-steering/review.md (pass; first constitution compliance line; converge 4/8 converged 0 violations)

## Links

- Benchmark: `knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md`
- Spec: `specs/073-project-constitution-steering/spec.md`

## Next Command

`product:status`
