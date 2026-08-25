# Issue 103 B1d Redacted Evidence Rendering Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Source request:** 2026-08-25 execution continuation after B1c3 — keep Issue 103 in short, independently reviewable slices before canonical apply.
- **Owner / decision maker:** Dongwon Lee
- **Phase:** plan
- **Next command:** write the B1d implementation plan after human review

## Decision

Implement only a pure redacted evidence serializer and deterministic byte renderer. B1d accepts one already complete `moduflow.lifecycle-transaction.v1` result candidate, validates it through the existing strict result contract, removes environment-specific and self-referential fields, and returns detached evidence data or exact UTF-8 JSON bytes.

B1d performs no filesystem I/O. It does not change the A2 planner's current provisional evidence target, acquire a lock, persist a journal, stage or replace a canonical file, decide transaction outcomes, or recover an incomplete transaction. B2 will own the point at which a result candidate becomes final evidence and is bound back to the evidence target.

## Purpose

The Issue 103 specification requires Git-tracked transaction evidence containing enough redacted information to explain a local lifecycle mutation. The current A2 planner creates only a provisional evidence document containing the transaction ID and ordinary target metadata. That provisional form cannot represent validation results, terminal status, rollback outcome, actor/source, or timestamps.

Moving directly into B2 without a fixed evidence contract would mix result-shape decisions with canonical replacement and rollback code. B1d succeeds when:

> Given one strict transaction result candidate, ModuFlow deterministically renders complete redacted evidence without reading or writing any file and without embedding the evidence file's own target record.

## Selected Architecture

### Schema

The schema name remains:

```python
EVIDENCE_SCHEMA = "moduflow.lifecycle-transaction-evidence.v1"
```

Every serialized evidence dictionary has exactly these keys:

```text
schema
transaction_id
idempotency_key
status
project_id
issue_id
action
target_lifecycle
targets
projected_validation
post_apply_validation
failed_stage
error_code
rollback_status
verified_target_count
next_command
actor
source_event
created_at
started_at
completed_at
```

The output deliberately excludes `canonical_root`. A Git-tracked evidence file must not capture a machine-specific absolute project path.

### Pure Interfaces

Add these interfaces to `scripts/project_lifecycle_transaction.py`:

```python
def serialize_transaction_evidence(result: dict) -> dict:
    """Return detached redacted evidence from one strict result candidate."""


def render_transaction_evidence(result: dict) -> bytes:
    """Return deterministic UTF-8 evidence JSON with one trailing newline."""
```

`serialize_transaction_evidence()` first calls `serialize_transaction_result(result)`. It does not maintain a second permissive validator or accept evidence-specific aliases. Result-schema failures continue to use the existing bounded `TypeError` or `ValueError` behavior.

After result validation, the serializer requires exactly one `evidence` target, requires it to be the final target, and rejects an `evidence` role anywhere else. A layout failure raises `ValueError("Transaction evidence target layout invalid")`; the message never includes a path, hash, payload, or caller value.

The returned `targets` list contains every ordered non-evidence target and excludes the final evidence target entirely.

### Self-Reference Boundary

The evidence target is excluded because its `after_sha256` and `after_bytes` depend on the serialized evidence bytes. Embedding that record would create an unsatisfiable self-reference.

The public transaction result and private journal remain the authorities for the complete target list, including the evidence target's final hash and byte count. Durable evidence records the transaction's ordinary affected targets and outcome, not its own serialized metadata.

B1d proves this boundary by rendering two otherwise identical results whose final evidence-target metadata differs. The rendered evidence bytes must be identical.

### Deterministic Bytes

`render_transaction_evidence()` serializes only the detached result of `serialize_transaction_evidence()` using:

```python
json.dumps(
    evidence,
    ensure_ascii=False,
    sort_keys=True,
    indent=2,
).encode("utf-8") + b"\n"
```

This produces stable, reviewable Git JSON with alphabetically sorted keys, two-space indentation, UTF-8 text, and exactly one trailing newline. It never uses `default=str` or another coercion that could admit unsupported values.

## Data Ownership and Timing

B1d validates and copies values; it does not decide them.

- B2 supplies the terminal `status`, validation summaries, rollback status, verified-target count, next command, actor/source, and timestamps.
- B1d preserves those validated scalar and summary values exactly.
- B1d does not inspect the canonical filesystem to recompute a status or count.
- The caller may mutate its original result and nested lists after serialization without changing the detached evidence result or previously rendered bytes.
- B2 must render and bind the final evidence bytes before evidence-target replacement. Resolving that orchestration and any provisional-plan rebinding remains a separate B2 design decision.

## Privacy and Error Contract

Evidence may contain only strict result fields and redacted target records. It never contains:

- `_before_bytes` or `_after_bytes`;
- recovery manifest entries, preimage or staging names, journal bytes, lock metadata, or owner tokens;
- an absolute canonical root or temporary path;
- exception text, validator diagnostics, artifact content, credentials, or caller-defined extension fields;
- the evidence target's own path, before/after hash, byte count, validation rules, or apply/rollback order.

The existing result serializer already enforces exact envelope keys, strict target metadata, bounded validation summaries, terminal status values, and non-success failure fields. B1d adds only the exact final evidence-target layout check and never echoes rejected values.

## Test Contract

B1d adds focused pure tests in `tests/test_project_lifecycle_transaction.py`:

1. Serialize a complete `applied` result and assert the exact evidence dictionary, including every ordinary target and every required outcome field but excluding `canonical_root` and the final evidence target.
2. Render exact sorted, indented UTF-8 JSON bytes with one trailing newline and assert round-trip equality with the evidence dictionary.
3. Vary only the final evidence target's self-metadata and assert identical evidence bytes.
4. Reject missing, duplicate, non-final, or misplaced evidence targets with the one bounded layout error and no caller values in the message.
5. Exercise all six existing result statuses and prove B1d adds no independent status semantics.
6. Mutate caller-owned targets and validation lists after serialization and prove the returned evidence remains detached.
7. Patch filesystem mutation boundaries (`os.open`, `os.mkdir`, `os.fsync`, and `os.replace`) and prove zero calls.
8. Scan rendered data for private plan fields, recovery/staging names, absolute canonical paths, artifact bytes, and exception details.

The implementation modifies only `scripts/project_lifecycle_transaction.py` and `tests/test_project_lifecycle_transaction.py`. Focused contract tests and Python compilation are sufficient for this pure slice; full discovery, distribution validation, and release checks remain deferred to D2.

## Alternatives Considered

1. **Derive evidence from the existing strict result contract — selected.** This keeps one outcome vocabulary and one target/validation sanitizer while adding only the evidence-specific redaction boundary.
2. **Create a separate evidence input schema — rejected.** It would duplicate result status, target, validation, error, and timestamp validation and make later changes prone to drift.
3. **Keep the current provisional A2 evidence as the final contract — rejected.** It lacks status, validation, failure, rollback, actor/source, and timing information required to explain a completed transaction.
4. **Embed the final evidence target but omit only its hash — rejected.** A partial target record would introduce a second target schema and still leave byte-count and self-metadata ambiguity.
5. **Write evidence during B1d — rejected.** File replacement and rollback ordering belong to B2; introducing them here would recreate the oversized, long-running implementation boundary.

## Out of Scope

- changing the A2 provisional evidence target or its planned hash;
- deciding when projected or post-apply validation becomes final;
- resolving provisional-plan rebinding before B1c staging;
- write authorization, locks, journal persistence, private staging, or manifest updates;
- optimistic canonical hash comparison or canonical target replacement;
- post-apply validation, evidence-target finalization, cleanup, rollback, or crash recovery;
- idempotent replay, public lifecycle/production adapters, Doctor diagnostics, operation inventory, distribution, or release gates;
- Prefect, another runner, a plugin, service, database, background process, Git operation, network call, or external dependency.

## Compatibility and Product Weight

- A1 intent/result schemas, A2 immutable planning, A3 projected validation, and B1a/B1b/B1c behavior remain unchanged.
- The existing public result schema remains the complete caller-facing record and still contains `canonical_root` plus the final evidence target.
- The existing A2 provisional evidence bytes remain unchanged until B2 explicitly closes the planning/finalization timing boundary.
- B1d adds two pure functions, one schema constant, and focused tests in existing files. It adds no module, command, configuration, startup work, resident state, or dependency.
- B2 remains split into separately approved conflict-check, apply/rollback, finalization, and crash-recovery slices.
