# Spec: Spec Consistency Analyze

Issue: `070-spec-consistency-analyze`

## Problem

Nothing validates that an issue's spec.md, plan.md, and tasks.md agree with each other before execution starts. Review checks the *work* against the spec; the planning artifacts themselves can contradict, omit, or stay vague — the rework class spec-kit's `/speckit.analyze` and Kiro's requirements analysis were built to prevent.

## Goals

- A read-only, deterministic checker over `specs/<id>/{spec,plan,tasks}.md` producing a severity-graded findings report (JSON + human list).
- Three heuristic check families in v1: acceptance-criteria coverage, vague-term lint, structural tracing.
- Recommended (not gating) position in the pipeline: after `product:plan`, before `product:execute`.

## Non-Goals

- No LLM calls, no SMT/formal logic (Kiro-style analysis explicitly deferred per the benchmark).
- No auto-rewriting of artifacts — report only.
- No hard gate in release_check v1 (promote later if signal proves reliable).
- No EARS migration of existing specs.

## Requirements

1. **CLI**: `python3 scripts/spec_consistency.py <root> --issue-id <id>` prints JSON: `{schema: "moduflow.spec-consistency.v1", issue_id, findings: [{severity, check, message}], summary: {error, warn, info, coverage_checked, coverage_flagged}}`. Exit 0 always when artifacts exist; exit 1 only for usage errors (missing spec dir).
2. **Coverage check** (`check: "coverage"`, severity `warn`): for each bullet in spec.md's `## Acceptance Criteria` section, tokenize (lowercase, alphanumeric words ≥3 chars, minus a small stopword set); compare against the combined token set of plan.md + tasks.md. A bullet sharing fewer than 2 significant tokens (or <30% of its tokens, whichever is stricter) is flagged "possibly uncovered". Heuristic by design — the message says "possibly".
3. **Vague-term lint** (`check: "vague-term"`, severity `warn`): bullets in spec.md's `## Requirements` and `## Acceptance Criteria` sections containing a vague quantifier (fast, quick, slow, easy, simple, secure, intuitive, scalable, robust, efficient, user-friendly, seamless, performant) with NO digit anywhere in the same bullet are flagged: requirement lacks a measurable criterion. Word-boundary matching; case-insensitive.
4. **Structural tracing** (`check: "structure"`): plan.md `### Stream X — <name>` headings with no corresponding `## Stream X` section in tasks.md → severity `error`; tasks.md `## Stream` sections tracing to no plan stream → `warn`; missing `## Acceptance Criteria` section in spec.md entirely → `error`; empty tasks.md (zero checkboxes) → `error`.
5. Missing plan.md or tasks.md (spec-only issues are legitimate early states): report as `info` findings, run the checks that are possible, exit 0.
6. **Docs**: `commands/product-plan.md` Next section recommends running the checker; `commands/product-execute.md` step 1 area gains a soft pre-execute note (run it, report findings, proceed unless errors are severe — agent judgment, not a hard stop).
7. Pure stdlib; read-only; no subprocess.

## Acceptance Criteria

- Fixture with an AC bullet whose tokens appear nowhere in plan/tasks → one `coverage` warn naming the bullet; fully-covered fixture → zero coverage findings.
- Fixture bullet "The system must be fast and secure" (no digits) → vague-term warns for both terms; "responds within 200 ms" → no vague-term finding.
- Plan stream `### Stream B — X` with no tasks `## Stream B` section → structure error; matching sections → clean.
- Spec missing `## Acceptance Criteria` → structure error.
- Missing plan.md → info finding, coverage still runs against tasks.md alone.
- JSON shape per Req 1; `python3 -m unittest tests.test_spec_consistency -v` passes; full suite; `release_check.py .` passes.
- Dogfood smoke: running against `specs/069-issue-dependency-priority-model` completes and reports (findings allowed — informational).

## Risks

- Token-overlap coverage will have false positives/negatives — mitigated by "possibly" wording, warn severity, and no gating in v1.

## Alternatives Considered

- LLM-judged coverage: rejected for v1 (nondeterministic, costs tokens in a gate path).
- Hard gate now: rejected — collect signal first.
- Extending `product:analyze`: rejected — that command is metrics/data analysis; overloading it would confuse the surface (055's grouping).

## Next Command

`product:plan 070-spec-consistency-analyze`
