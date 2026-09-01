# Issue 103 C2c Public Production Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development inline. Do not use subagents.

**Goal:** Replace the remaining public Production Record canonical write with one explicit-version `production-version` transaction while preserving useful compatibility result keys.

**Architecture:** Add a lazy transaction loader and a full-result `create_production_version()` entry. `create_production_record()` becomes a compatibility wrapper that renders deterministic versioned content, calls the transaction entry, and maps terminal status to its existing `action/id/path` envelope with additive `transaction` evidence. `--new-record` requires `--version` and uses the same wrapper. Existing init/search/retrieve/validation/playbook-decision paths remain unchanged.

**Tech Stack:** Existing Production Record renderer, lifecycle transaction API, `argparse`, `unittest`, nested project fixtures.

## Constraints

- New creation requires a real owning `issue_id` and an explicit semantic version; source-context-only and unversioned creation fail before engine dispatch.
- Legacy unversioned records remain readable/searchable and are never migrated.
- The public creation path does not call `apply_production_plan()`, `mkdir()`, `write_text()`, or collision-suffix loops; initialized canonical parents must already exist.
- Deterministic record ID and bytes make an identical retry `noop`; same semantic version with different bytes/path maps to `update_required` plus transaction conflict evidence.
- Capability denial, recovery barrier, locking, journal, validation, replacement, rollback, and evidence remain transaction-owned.
- Do not modify production init, search, retrieve, validation, or playbook approval behavior.
- Do not run full release gates before D2.

### Task 1: RED Public Adapter Tests

- [ ] Add an exact-intent unit test proving versioned content, actor/source event, idempotency input, context, clock, and fault injector reach one `production-version` transaction call.
- [ ] Assert missing/invalid version and missing `issue_id` reject before engine dispatch and create no directories/files.
- [ ] Assert compatibility mapping: `applied → created`, `noop → noop`, `conflict → update_required`, with stable `id/path` and additive full transaction result.
- [ ] Assert the adapter owns no direct canonical write or lazy initialization.

### Task 2: RED Integration and CLI Tests

- [ ] Apply a real versioned record only to a nested configured production root; issue/state/loop/dashboard/evidence participate and poisoned default roots remain byte-identical.
- [ ] Repeat identical creation and assert `noop`; change same semantic version content and assert `update_required` without overwrite.
- [ ] Require CLI `--version`, forward it through the wrapper, and return nonzero for non-success transaction statuses.
- [ ] Update existing creation fixtures to initialize required canonical workspace/production parents explicitly.

### Task 3: Minimal Public Routing

- [ ] Add lazy `_load_lifecycle_transaction_module()` and `create_production_version()`.
- [ ] Add `version`, actor/source-event/idempotency/hash/clock/fault inputs to `create_production_record()`; render one deterministic record ID/content and remove all direct-write/dedup/collision code.
- [ ] Map the transaction status into compatibility keys without hiding the complete transaction result.
- [ ] Add `--version` to the CLI required-field contract and status exit-code mapping.

### Task 4: Verification and Completion

- [ ] Run RED/GREEN named tests plus production, transaction, lifecycle, and loop focused suites.
- [ ] Run compilation, direct-writer inventory checks, and `git diff --check`.
- [ ] Commit as `feat(103): transact production record creation`.
- [ ] Mark C2/C2c and original C2 Steps 1–6 complete; activate D1 and leave D2 open.

## Completion Gate

- [ ] Every public new-record path crosses the transaction boundary exactly once.
- [ ] Identical retries are no-op and conflicts never overwrite canonical Production Records.
- [ ] No Production Record creation bypass remains outside transaction persistence.
