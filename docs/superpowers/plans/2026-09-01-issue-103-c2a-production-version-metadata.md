# Issue 103 C2a Production Version Metadata Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development inline. Do not use subagents.

**Goal:** Add the backward-compatible Production Record version metadata contract needed before transaction uniqueness and public adapter work.

**Architecture:** Keep legacy record parsing valid by returning `version=""` when frontmatter omits the field. Extend the pure record renderer with an optional version input and emit `version:` only for versioned records. Do not change the current public writer, CLI, transaction planning, or lock behavior in this slice.

**Tech Stack:** Python string rendering and frontmatter parsing, `unittest`.

## Constraints

- Legacy unversioned records remain byte-compatible and parse without migration.
- A versioned record exposes the exact normalized frontmatter value.
- The pure renderer is the only production code changed in this slice.
- Do not route public writes or implement uniqueness/lock rechecks until C2b/C2c.
- Do not run full discovery or release gates before D2.

### Task 1: RED Metadata Tests

- [x] Assert a legacy record parses with `version == ""`.
- [x] Assert a versioned record parses with its explicit semantic version.
- [x] Assert the pure renderer includes exactly one `version:` field when supplied and none when omitted.
- [x] Run the named tests and confirm the missing return/renderer argument fails.

### Task 2: Minimal Parser and Renderer Change

- [x] Return `metadata.get("version", "")` from `parse_production_record()`.
- [x] Add optional `version=""` to `_record_content()` and conditionally render one frontmatter line.
- [x] Keep every existing `create_production_record()` caller and rendered legacy byte sequence unchanged.

### Task 3: Verification and Completion

- [x] Run production parser/mutation tests and the full production module suite (27 tests passed).
- [x] Run compilation and `git diff --check`.
- [x] Commit as `feat(103): parse production record versions` (`3361e33`).
- [x] Mark C2a complete and activate C2b; leave C2/C2c/D1/D2 open.

## Completion Gate

- [x] Legacy and versioned records both parse deterministically.
- [x] Version metadata emission is opt-in and pure.
- [x] No public mutation or transaction semantics changed in C2a.
