# Issue 103 C2b2 Locked Production Version Recheck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans, superpowers:test-driven-development, and superpowers:systematic-debugging inline. Do not use subagents.

**Goal:** Classify an existing Production Record version as absent, identical, or conflicting, and recheck it under the lifecycle lock before any journal, staging, or canonical replacement.

**Architecture:** Share the C2b1 semantic identity normalizer with the transaction module. A no-follow, configured-root scan compares the proposed production target against every versioned record. After projected validation, an already-identical target returns `noop` and a conflicting match returns `conflict`. The same scan runs again after acquiring the lifecycle lock; any newly appeared match returns preflight conflict so the caller can re-plan and receive the stable `noop`/`conflict` classification on retry.

**Tech Stack:** Existing transaction planner/apply lock, Production Record frontmatter parser, no-follow readers, `unittest`, fault injection.

## Constraints

- Identity is exactly `(issue_id, deliverable_type, channel, variant, version)`.
- Only the same canonical record path with byte-identical content is an initial semantic retry `noop`.
- A matching key at another path or with different bytes is `conflict`.
- A match that appears after projected validation is a pre-journal conflict; the operation does not guess whether other preimages are still valid.
- Scans use the resolved `production_records` root, reject symlinks/unsafe reads, and expose only stable error codes.
- Do not change the public production writer/CLI until C2c or run full release gates before D2.

### Task 1: RED Classification and Race Tests

- [x] Add a valid versioned proposal fixture whose exact existing target returns `noop` after the recovery barrier with no lifecycle apply workspace, journal, staging, or evidence write.
- [x] Add same-key/different-bytes and same-key/different-path cases returning deterministic `conflict`.
- [x] Inject a matching record after projected validation and prove the same-lock recheck returns preflight conflict before transaction workspace creation.
- [x] Add nested configured-root and poisoned default-root coverage.

### Task 2: Safe Semantic Classifier

- [x] Promote the C2b1 identity helper to a shared pure `production_version_identity(record)` function.
- [x] Parse only frontmatter from proposed/canonical bytes, validate the intent version binding, and scan configured `*.md` files with existing no-follow reads.
- [x] Return only `absent`, `identical`, or `conflict`; convert malformed, symlinked, or unreadable scan state to a stable conflict code.

### Task 3: Apply and Lock Integration

- [x] After the recovery barrier, classify once; return a truthful semantic `noop` only after projected validation and return preflight conflict immediately for unsafe/conflicting state.
- [x] Inside `_private_prepared_workspace()`, run the classifier after lock acquisition and recovery-inventory proof but before canonical preimage verification or workspace creation.
- [x] Treat any non-absent locked classification as preflight conflict; preserve retry-based re-planning.

### Task 4: Verification and Completion

- [x] Run named RED/GREEN tests plus production and transaction focused suites (248 combined lifecycle/loop/production/transaction tests passed).
- [x] Run compilation and `git diff --check`.
- [x] Commit as `feat(103): recheck production versions under lock` (`99c050b`).
- [x] Mark C2b/C2b2 complete and activate C2c; leave C2/D1/D2 open.

## Completion Gate

- [x] Existing identical versions return `noop` without lifecycle apply/journal/staging/evidence side effects.
- [x] Conflicting and racing versions never reach journal, staging, or replacement.
- [x] Nested canonical roots are authoritative and decoy defaults remain untouched.
