# Plan: Spec Consistency Analyze

Issue: `070-spec-consistency-analyze`
Spec: `specs/070-spec-consistency-analyze/spec.md`
Next: `product:execute 070-spec-consistency-analyze`

## Global Constraints

- Stdlib only; read-only (no writes, no subprocess); deterministic — same inputs, same findings, stable ordering.
- Findings always carry `severity` ∈ {error, warn, info}, `check` ∈ {coverage, vague-term, structure, artifacts}, `message`.
- Never exit nonzero because of findings — only for usage errors (missing `specs/<id>/` directory).
- Section extraction reuses the house approach (`_section_body`-style regex on `^## ` boundaries); code-fence content is excluded from bullet scanning (069's prose-collision lesson).

## Streams

### Stream A — Checker (`scripts/spec_consistency.py`)

Interfaces (produced): `analyze(root, issue_id) -> dict` (Req 1 shape); CLI wrapper.
- `_bullets(section_text)`: top-level `- ` bullets, fence-aware.
- `_tokens(text)`: lowercase alphanumeric ≥3 chars minus stopwords (small English set + {the, and, for, that, with, must, should, when, given, then}).
- Coverage per spec Req 2; vague list per Req 3 as a module constant; structure per Req 4; artifact presence per Req 5.

### Stream B — Docs

- `commands/product-plan.md` Next + `commands/product-execute.md` soft pre-check note.

### Stream C — Tests (`tests/test_spec_consistency.py`)

Fixture builder writing spec/plan/tasks trios into a tempdir. Cases per AC: uncovered bullet flagged / covered clean; vague terms with-and-without digits; stream mismatch both directions; missing AC section; missing plan.md info + still-runs; empty tasks error; JSON schema shape; ordering stability (two runs equal); fence-quoted bullet text not scanned.
Plus `scripts/release_check.py` module-list addition.

## Task right-sizing

A core, C alongside (TDD), B last. One reviewable diff.

## Gates

RED→GREEN; full discover; release_check; dogfood smoke on `specs/069-issue-dependency-priority-model` (capture output — findings allowed).

## Rollback

Fully additive: revert the script, tests, and two doc notes.
