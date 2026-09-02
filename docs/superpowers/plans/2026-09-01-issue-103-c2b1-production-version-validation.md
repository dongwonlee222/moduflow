# Issue 103 C2b1 Production Version Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development inline. Do not use subagents.

**Goal:** Make canonical and projected project validation reject duplicate versioned Production Record semantic identities while leaving legacy unversioned records unchanged.

**Architecture:** Define one pure version identity `(issue_id, deliverable_type, channel, variant, version)` in `project_production.py`. Reuse the existing deterministic duplicate collector only for records with a non-empty version. The transaction projected validator already calls project validation, so no transaction-engine mutation is needed in this slice.

**Tech Stack:** Existing Production Record parser/validator and `unittest`.

## Constraints

- Record `id`, title, owner, and path are not part of semantic version identity.
- Unversioned legacy records do not participate in version uniqueness and are not migrated.
- Duplicate messages remain path-bounded and deterministic.
- Same-lock recheck and public no-op/conflict mapping remain C2b2/C2c.
- Do not run full discovery or release gates before D2.

### Task 1: RED Validation Tests

- [x] Add two different record IDs with the same version identity and assert one deterministic validation error.
- [x] Change one identity field and assert no version-identity error.
- [x] Keep two unversioned legacy records outside the version-identity rule.

### Task 2: Minimal Identity Validation

- [x] Add a private pure `_production_version_key(record)` helper.
- [x] Filter to non-empty versions and feed the key into the existing duplicate collector.
- [x] Preserve all existing capture-key and ID uniqueness checks.

### Task 3: Verification and Completion

- [x] Run named RED/GREEN tests and the full production suite (29 tests passed).
- [x] Run the projected-validation production case, compilation, and `git diff --check`.
- [x] Commit as `feat(103): validate production version uniqueness` (`93f6d80`).
- [x] Mark C2b1 complete and activate C2b2.

## Completion Gate

- [x] Canonical/projected validation rejects duplicate version identities.
- [x] Legacy unversioned compatibility is unchanged.
- [x] No lock, apply, or public writer behavior changes in C2b1.
