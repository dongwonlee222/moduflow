# Spec Kit Conservative Intent Boundary Design

**Status: approved** — Dongwon Lee approved the recommended conservative approach on 2026-08-12.

## Problem

Issue 098 already proves the difficult safety boundaries around project opt-in, pinned assets,
canonical inputs, result provenance, append-only persistence, package distribution, and pilot
evidence. The remaining unstable surface is free-form request classification.

Trying to infer whether words such as `add`, `stage`, `start`, `changes`, or `files` describe a
requirements-validation subject or a Git/lifecycle mutation creates an open-ended natural-language
parsing problem. Repeatedly expanding regular expressions introduces alternating false allows and
false blocks. That complexity is not justified for an optional, advisory adapter.

## Decision

Spec Kit exposes only four explicit validation intents through a small canonical grammar. Any
request outside that grammar falls back to native ModuFlow with a safe normalized retry example.

This is intentionally conservative:

- a false allow could hand an ownership request to the wrong capability;
- a fallback costs one rephrasing but performs no unsafe action;
- ModuFlow and Superpowers retain all implementation, lifecycle, Git, review, and release work.

## Canonical Request Grammar

The selector accepts exactly one approved function and an optional approved validation target.

```text
English: <spec-kit-prefix> <function> [<validation-target>]
Korean:  <spec-kit-prefix> [<validation-target>] <function>
```

Approved prefixes:

- English: `spec kit`, `speckit`
- Korean: `스펙킷`, `스펙 킷`

Approved functions and synonyms:

| Function | English | Korean |
| --- | --- | --- |
| `clarify` | `clarify`, `clarification` | `명확화`, `핵심 질문` |
| `analyze` | `analyze`, `analysis` | `분석`, `정합성` |
| `checklist` | `checklist` | `체크리스트`, `요구사항 점검` |
| `converge` | `converge`, `convergence` | `수렴`, `남은 작업` |

Approved targets are bounded domain nouns such as requirements, spec, plan, tasks, acceptance
criteria, consistency, validation coverage, and their Korean equivalents. Harmless particles and
determiners are normalized. Punctuation or extra action clauses are not interpreted.

Guaranteed examples:

```text
Spec Kit analyze requirements
Spec Kit checklist acceptance criteria
스펙킷 요구사항 분석
스펙킷 요구사항 체크리스트
```

Requests with multiple functions, unknown content, action clauses, Git/lifecycle terms, or an
otherwise ambiguous shape return fallback. For example, `Spec Kit analyze then stage files` and
`Spec Kit clarify which changes to add to requirements` both fall back rather than being parsed.

## Interface

Add one structured classifier:

```python
classify_request(request) -> {
    "outcome": "selected" | "fallback",
    "function": "clarify" | "analyze" | "checklist" | "converge" | None,
    "reason_code": "explicit_validation" | "ambiguous_request" | "multiple_functions" | "unsupported_request",
    "retry": str | None,
}
```

`select_function()` remains a compatibility wrapper: it returns a function only for
`outcome=selected`, otherwise `None`. `build_handoff()` consumes the structured result and never
loads a template for fallback outcomes.

Fallback output includes:

- the truthful reason code;
- native ModuFlow validation guidance;
- one canonical retry, for example `Spec Kit analyze requirements`.

The adapter does not ask an LLM to classify ownership, install another parser, or maintain a large
verb/inflection list.

## Data Flow

1. ModuFlow resolves direct `product:*` and lifecycle aliases locally.
2. The capability router sees an explicit Spec Kit prefix and selects at most one Spec Kit stage.
3. The conservative classifier validates the complete request against the canonical grammar.
4. A noncanonical request returns fallback without reading an overlay, template, or project input.
5. A canonical request continues through the existing current-handoff checks: project opt-in,
   host availability, contained canonical inputs, pinned asset hashes, read permission, and exact
   output path.
6. Result validation and persistence retain the existing current-state provenance, locking,
   append-only, and explicit-write gates.

## Error and Safety Behavior

- Ambiguity is a normal fallback, not an exception or execution claim.
- Invalid CLI/JSON/UTF-8 remains a structured `moduflow.spec-kit-error.v1` failure.
- Fallback creates no config, template load, validation file, lifecycle transition, or command
  execution.
- Default availability remains `false`; the human activation decision remains pending.

## Testing

The test strategy proves a finite grammar rather than attempting exhaustive natural language.

1. Canonical success table: all four functions in English and Korean select exactly one function.
2. Target table: every approved validation target is accepted with harmless determiners/particles.
3. Fallback metamorphic tests: insert any unapproved token, second function, sequence marker,
   punctuation clause, Git/lifecycle action, or arbitrary modifier into a canonical request; the
   result must be fallback with no template or artifact.
4. Compatibility: `select_function()` returns `None` for every fallback classification.
5. End-to-end pilot: canonical requests succeed; disabled/unavailable and noncanonical ownership
   cases use real router/adapter fallback; all safety counters remain zero.
6. Provenance release gate remains mandatory and fails on canonical-input or snapshot drift.
7. Full suite, lifecycle drift, package validation, project validation, and release gate must pass.

## Migration and Documentation

- Replace the open-ended ownership classifier and its expanding phrase lists with the canonical
  grammar.
- Rewrite the previous positive-language fixtures as either canonical success cases or explicit
  safe-fallback cases.
- Update the bridge, Issue 098 spec/plan/status, pilot report, and user guidance with guaranteed
  request examples and the conservative fallback rule.
- Implement the approved simplification in a new reviewed fix commit and apply the repository's
  patch-version policy to both plugin projections. Do not publish a release or enable the
  capability by default.

## Non-Goals

- General English/Korean semantic parsing.
- Perfect interpretation of arbitrary mixed-intent sentences.
- Executing Spec Kit scripts, hooks, Git, implementation, or lifecycle actions.
- Making Spec Kit automatic or mandatory.
