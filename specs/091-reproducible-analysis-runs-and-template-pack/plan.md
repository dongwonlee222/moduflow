# Reproducible Analysis Runs and Template Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL after explicit implementation approval: `superpowers:executing-plans`; execute inline, task-by-task. Do not dispatch subagents or additional tasks for this assignment. Checkboxes below describe future work, not completed implementation.

**Goal:** Stop re-explaining a recurring request. A playbook carries the deliverable's contract, and an append-only run record carries the provenance that makes its result reproducible.

**Architecture:** One canonical Markdown run file with fenced JSON, one parser, one read facade, one bounded append intent inside the existing 103 transaction owner. The deliverable contract lives in the existing `moduflow.playbook.v1`, extended by two additive fields. Sources reopen through the delivered 090 facades; outputs register through 090's existing boundary. No calculator, scheduler, second registry or second template system.

**Tech Stack:** Existing Python 3 standard library, Markdown, JSON, `unittest`, injected Git runner, injected UUID factory and date, and the existing 103 lock/journal/recovery. No new dependencies.

Issue: `091-reproducible-analysis-runs-and-template-pack` · Owner: Dongwon Lee
Phase: draft plan, revision 2 of 2026-09-03. Implementation requires separate explicit approval; nothing below is executable yet.
Source / Prev: [spec](spec.md), [existing issue](../../issues/091-reproducible-analysis-runs-and-template-pack.md), `workspace/roadmap.md` 2026-09-02 scope reconciliation, [the 2026-09-03 benchmark](../../knowledge/benchmarks/2026-09-03-deliverable-playbook-and-analysis-run-benchmark.md), and the delivered [090 contract](../090-project-knowledge-and-artifact-registry/spec.md).
Next: decide the Ownership Boundary follow-up issue, then `product:execute 091-reproducible-analysis-runs-and-template-pack` inline after a recorded readiness check.

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- No new dependencies, database, crawler, vector store, upload, scheduler, queue, timer, lineage engine, analysis calculator, document generator, approval flow or UI code.
- One resolved project context per operation; no sibling-project traversal and no cross-project payload.
- No company data, metric values, cost amounts, KPI definitions, credentials, private absolute paths or full source text in the plugin or in a shared record.
- Default paths are `workspace/analysis-runs.md` and `templates/analysis-playbooks/`, resolved through canonical roles; non-default registered paths must work.
- Lifecycle state, goal, loop, roadmap and dashboard bytes must not change during a run append or amendment.
- 091 implements no registry parser, no second registration path, no second transaction engine and no second template system; it calls 090, 103 and the playbook format.
- `scripts/project_artifact_registry.py` is read-only for this issue.
- All git/subprocess access flows through the injected runner (C1); no gate swallows an exception (C2); every behavior change lands with focused tests (C3); appends never rewrite existing records (C5); one parser per artifact (C8); every bound reports itself (C11).
- **Stream B moved to [Issue 115](../../issues/115-playbook-process-and-checklist-extension.md)**, registered 2026-09-03 as an Issue 085 follow-up owning the two additive playbook fields. Issue 091 is blocked by it, consumes the fields, and does not modify `scripts/project_production.py` or `templates/production/playbook.md`. Stream B below is retained as the consumed contract, not as work performed here.
- This issue is not a gate on the held plugin release; Issue 111 keeps that gate.
- Current authoring writes remain confined to `specs/091-reproducible-analysis-runs-and-template-pack/` and `knowledge/benchmarks/`. The file map below is future implementation scope, not permission to edit it now.

## Contract and Dependencies

The [spec](spec.md) is authoritative for `moduflow.analysis-runs.v1`, `moduflow.analysis-run-read.v1`, R1–R8 and AC1–AC10. Function names below are proposed additions; existing functions are explicitly labeled.

| Interface | Consumes | Produces |
| --- | --- | --- |
| `parse_analysis_runs(text: str) -> dict` | One run-file Markdown string | `{schema, entries, diagnostics, metadata_valid}`; one parser, no I/O |
| `validate_run(entry: dict, *, today, playbook=None) -> list` | One R2 record and its resolved playbook | Ordered diagnostics for R2 shape, R4 code checks, R5 states and amendment boundary, R6 follow-up, R3 playbook binding; pure |
| `render_run_entry(entry: dict) -> str` | Valid R2 record | Deterministic `## run-<uuid>` heading plus one fenced JSON block; no whole-file rewrite |
| `resolve_playbook(root, name, *, project_context) -> dict` | A deliverable/playbook name | The project playbook when present, else the read-only default, with the resolution reason; `PLAYBOOK_UNRESOLVED` when neither exists |
| `prefill_run(playbook: dict) -> dict` | A resolved playbook | Claim class, measure unit, checks skeleton, default caveats and structure reference for a new run; pure |
| `read_analysis_runs(root, *, project_context, view="working", ref="HEAD", query="", run_ids=(), issue_id=None, limit=20, runner=None, today=None) -> dict` | One context and request filters | R8 envelope with explicit `total`/`returned`/`omitted`/`truncated` and read trace |
| `resolve_run_sources(root, run_id, *, project_context, runner=None) -> dict` | A stored run's `sources[]` | Delegated `read_artifact_registry` / `read_artifact_sources` results at each stored `snapshot_commit`; no local parser |
| `plan_analysis_run_append(root, entry, *, project_context, runner=None) -> object` | One record and its resolved context | Existing `LifecycleTransactionPlan` carrying a bounded `analysis-run-append` intent; no writes |
| `plan_run_amendment(root, run_id, changes, *, reason, evidence_ref=None, project_context, runner=None) -> object` | An existing run and a change limited to the six mutable fields | The same bounded intent with one appended `state_history` entry; rejects any other field |
| `apply_analysis_run_append(root, plan, *, project_context, runner=None) -> dict` | Immutable plan and same context | Existing transaction terminal result plus `run_id` and `appended` flag; no direct file writer |

Existing delivered functions reused unchanged: `project_artifact_registry.read_artifact_registry`, `read_artifact_sources`, `plan_artifact_registration`, `apply_artifact_registration`; `project_registry.context_for_operation` and canonical path helpers; `project_operation` capability checks; `project_lifecycle_transaction` planning, lock, journal, rollback, recovery and its six terminal outcomes; `project_production` playbook and record readers. `runner(args, cwd, timeout=None) -> CommandResult` follows the existing `project_sync.run_command` shape.

Prerequisites: 090 is delivered at `3585e84` and is the only source of registry parsing; 085's playbook and production record formats exist; 102/109 context, 110 capability enforcement and 103 transactions exist at this baseline. 111 is not a prerequisite and must not be cherry-picked.

## File Map

| File(s) | Responsibility / change after approval |
| --- | --- |
| New `scripts/project_analysis_run.py` | Sole run parser, validator, renderer, playbook resolver, prefill, read facade, source resolver and bounded append/amend adapter |
| New `templates/workspace/analysis-runs.md` | Empty canonical run file with `moduflow.analysis-runs.v1` frontmatter and the exact record format |
| New `templates/analysis-playbooks/weekly-usage.md` | Thin-slice default playbook proving the two new fields end to end |
| New `templates/analysis-playbooks/monthly-trend.md`, `cpo-change.md`, `amount-band.md`, `charging-speed.md`, `policy-impact.md` | The five accepted analyses as default playbooks |
| New `templates/analysis-playbooks/README.md` | Resolution order, the two new fields, and the rule that a default may not name an undefined check ID |
| Existing `templates/production/playbook.md`, `scripts/project_production.py` | **Issue 115 owns these. Not modified by Issue 091.** Additive `process_ref` field and `Required Checks` section land there and are consumed here |
| Existing `scripts/project_lifecycle_transaction.py` | Bounded `analysis-run-append` intent covering append and six-field amendment, with a no-lifecycle-change path |
| Existing `scripts/project_lifecycle_transaction_storage.py` | Reuse unchanged unless a demonstrated recovery requirement needs a focused, tested addition; no second lock or journal |
| Existing `scripts/project_knowledge.py` | Missing-only initialization gains the run file; existing behavior preserved |
| Existing `scripts/validate_project_artifacts.py`, `scripts/project_doctor.py` | Call the single run validation/read facade; actionable diagnostics; no competing validator |
| Existing `config/project-operation-entrypoints.json`, `scripts/validate_moduflow.py`, `scripts/release_check.py` | Exact mutation ownership, new source/package assets and focused suite registration |
| Existing `commands/product-analyze.md` | Playbook selection over resolved names, preview-before-apply, claim class, four separate states |
| Existing `skills/data-analysis-bridge/SKILL.md` | Required-field list extended to the R2 fields, including non-applicability and unknown-cost wording |
| New `tests/analysis_run_fixture.py` | Synthetic-only run/playbook/context/temporary Git fixture builders; no company assets |
| New `tests/test_project_analysis_run.py`, `tests/test_project_analysis_run_transaction.py`, `tests/test_project_analysis_run_simulation.py` | Schema/validation/read, append/amend/failure/retry, and end-to-end scenario proof |
| New `tests/test_analysis_playbooks.py` | Default playbook shape, resolution order, and check-ID agreement |
| Existing `tests/test_project_knowledge.py`, `tests/test_project_doctor.py`, `tests/test_project_lifecycle_transaction.py`, `tests/test_project_production.py`, `tests/test_project_operation_audit.py`, `tests/test_validation_distribution.py`, `tests/test_release_check.py` | Backward compatibility and integration gates |

**Known collision set for this issue**, to be re-checked against the latest integration base before execution: `scripts/project_production.py`, `templates/production/playbook.md`, `scripts/project_lifecycle_transaction.py`, `scripts/validate_moduflow.py`, `scripts/release_check.py`, `config/project-operation-entrypoints.json`. The first two are also on the path of Issues 107 and 108.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — run schema | writing-plans + TDD + git-native-artifact-model | The record contract and its diagnostics must be stable before any consumer exists |
| B — playbook fields | TDD + focused 085 compatibility review | An additive change to a delivered format needs proof that existing playbooks still parse |
| C — reads and bindings | TDD + verification-before-completion | Assert read traces, project isolation, pinned-commit reopening and explicit bounds |
| D — append transaction | executing-plans inline + TDD + focused transaction review | Shared lock and planner changes are dependent work, never parallel writes |
| E — default playbooks | writing-plans + TDD | The pack is a validated contract, not free-form prose |
| F — integration/evidence | verification-before-completion + PM/privacy self-review | Keep observed simulations distinct from expected outcomes |

---

## Stream A — Run Record Foundation

### Task A1: One parser, exact record schema, amendment boundary, initialization

- [ ] Add `scripts/project_analysis_run.py` with `SCHEMA = "moduflow.analysis-runs.v1"`, the `run-` UUIDv4 pattern, `parse_analysis_runs`, `render_run_entry` and the R2 field/type validation, mirroring the delivered `project_artifact_registry` structure so the two stay reviewable side by side.
- [ ] Reject duplicate JSON keys, duplicate run IDs, header/object ID disagreement, a second metadata block in one record section, and an unsupported schema; preserve prose outside record sections byte-for-byte.
- [ ] Implement the R5 amendment boundary: only the six mutable fields change in place, each amendment appends one `state_history` entry with a nonempty reason, the newest entry per field equals that field's current value, existing entries are immutable, and anything else returns `RUN_AMENDMENT_FORBIDDEN`.
- [ ] Implement R5 state independence, `RUN_UNASSIGNED_NOT_FINAL`, and R6 `FOLLOW_UP_NOT_SCHEDULABLE`.
- [ ] Add `templates/workspace/analysis-runs.md` and extend `project_knowledge.py` missing-only initialization to create it without touching existing files; a second run changes zero bytes.
- [ ] Allocate the run ID once through an injectable UUID factory and reuse it on retry.
- [ ] Tests in `tests/test_project_analysis_run.py`: every required field missing, each nullable-with-reason pair, malformed dates, oversized single-line fields, duplicate IDs, prose preservation, idempotent initialization, an amendment of each mutable and each forbidden field, a missing or edited history entry, a history/current mismatch, and an approved `unassigned` run.

**Verify:** `python3 -m unittest tests.test_project_analysis_run -v`

### Task A2: The three code checks and the cost rule

- [ ] Enforce `population-defined` for every claim class, `denominator-stated` for `profitability` and `causal`, and `cost-applicability-explicit` for `profitability`; a missing required check returns `CHECK_MISSING`, never a pass.
- [ ] Require a nonempty reason on `not_applicable` (`CHECK_UNEXPLAINED`) and on `fail`; any `fail` from either layer blocks `validation_state=passed`.
- [ ] Require an existing `evidence_ref` on every `pass` in a `profitability` or `causal` run.
- [ ] Enforce `COST_UNKNOWN_NOT_ZERO`: a nonempty `unknown_items` cannot accompany a settled profitability conclusion, and no output renders, sums or defaults an unknown cost as `0`.
- [ ] Enforce exactly one claim per run; do not grade or rewrite prose.
- [ ] Tests: each claim class's minimum set, explained and unexplained non-applicability, a `pass` without evidence on a causal run, unknown cost items against a settled conclusion, and a `costs.applicable=false` run with and without a reason.

**Verify:** `python3 -m unittest tests.test_project_analysis_run -v`

---

## Stream B — Playbook Fields (delivered by Issue 115) and Resolution

### Task B1: Two additive fields on `moduflow.playbook.v1` — Issue 115

> This task is **not executed by Issue 091.** It is the contract Issue 091 consumes, restated here so the dependency is reviewable. Track and verify it in Issue 115.

- [ ] Add `process_ref` as `{kind, ref, version, missing_evidence}`; a null `ref` is valid only with a nonempty `missing_evidence`. Store the reference only — no ordered steps, no process format, no assumption that the referenced procedure is installed.
- [ ] Add a numbered `Required Checks` section (`CHK001`, …) with stable IDs; changing an item's meaning requires a new ID. A checked item is a reviewer assertion, never proof of a passing run.
- [ ] Keep every existing playbook section, field and behavior unchanged; an existing playbook without the two new fields must still parse and validate.
- [ ] Tests in `tests/test_project_production.py`: an existing playbook parses unchanged, the new fields round-trip, a null `ref` without `missing_evidence` fails, and a duplicate or renumbered check ID is rejected.

**Verify:** `python3 -m unittest tests.test_project_production -v`

### Task B2: Resolution order and prefill

- [ ] Implement `resolve_playbook`: a project playbook of the same name wins over a read-only default; a new project name is added; defaults are never edited in place; neither present returns `PLAYBOOK_UNRESOLVED` with no silent fallback.
- [ ] Implement `prefill_run`: claim class, measure unit, checks skeleton, default caveats and structure reference come from the resolved playbook.
- [ ] Record `{playbook_id, version, deliverable_type}` on the run and emit `PLAYBOOK_VERSION_CHANGED` as info when the current project version differs from the pinned one.
- [ ] Tests: project override, project-only name, default-only name, neither present, two projects with different playbooks of the same name, and prefill output for each default claim class.

**Verify:** `python3 -m unittest tests.test_analysis_playbooks -v`

---

## Stream C — Read Contract and Bindings

### Task C1: Read envelope, state separation, explicit bounds

- [ ] Implement `read_analysis_runs` with a capability read check before any project content, `working`/`shared` views, shell-free ref resolution and committed-tree-only shared reads.
- [ ] Return the R8 envelope with the four states kept separate, `run_anchor`, `match_reasons` and R3–R6 diagnostics; default limit 20 with `total`/`returned`/`omitted`/`truncated` always populated (C11).
- [ ] Emit `FOLLOW_UP_INTENT_ONLY` for every run with a follow-up and `FOLLOW_UP_DUE` when the injected date has passed `due_on`; neither changes state nor re-runs anything.
- [ ] Reject cross-project references when `identity_status=unbound`; exclude source bodies, absolute roots and other projects' payloads from every envelope and trace.
- [ ] Tests: A/B isolation with a shared run UUID, non-default workspace paths, limit overflow, unbound identity, each diagnostic, and a read that collapses no two states into one.

**Verify:** `python3 -m unittest tests.test_project_analysis_run -v`

### Task C2: Pinned sources and playbook binding

- [ ] Implement `resolve_run_sources` by calling `read_artifact_registry` and `read_artifact_sources` with each stored `snapshot_commit` as `ref`; implement no registry parsing here.
- [ ] Return explicit diagnostics for `project_id` mismatch, unknown `artifact_id`, unknown schema and superseded input; never substitute a similarly titled record and never switch snapshot.
- [ ] Treat a pinned `recorded_state` of `approved` as pin-time material state only.
- [ ] Emit `PLAYBOOK_MISMATCH` when a run's output has a `production_record_ref` whose `playbook_refs` names a different playbook.
- [ ] Tests with a disposable local Git fixture: rename-with-same-ID reopening, mismatched project ID, superseded pinned artifact, missing artifact ID, optional absent private source, injected Git failure, and a production record naming a different playbook.

**Verify:** `python3 -m unittest tests.test_project_analysis_run -v`

---

## Stream D — Append Transaction and Output Registration

### Task D1: Bounded `analysis-run-append` intent

- [ ] Add the intent to the existing 103 transaction owner, covering both a new append and a six-field amendment, changing only the run file and, for a real `issue_id`, one append-only `Analysis Runs` backlink to the stable run anchor.
- [ ] Build and validate projected targets, recheck preimages under the existing lock, and reuse the existing journal, rollback, recovery and six terminal outcomes; add no second lock, journal or storage owner.
- [ ] Assert unchanged issue lifecycle, state, goal, loop, roadmap and dashboard bytes by comparing hashes before and after.
- [ ] Default to a read-only preview; make retry byte-identical; block on uninitialized prerequisites with explicit guidance instead of creating state; expose no general file-transaction API.
- [ ] Reject every forbidden-field amendment before staging; a one-time `issue_id` promotion out of `unassigned` also appends the backlink exactly once.
- [ ] Tests in `tests/test_project_analysis_run_transaction.py`: injected failure before and after each replacement, validation failure, retry, concurrent edit, an archived/read-only project denied before any staging write, unchanged projection hashes, a rejected forbidden amendment, and a double promotion.

**Verify:** `python3 -m unittest tests.test_project_analysis_run_transaction -v`

### Task D2: Output registration and routing

- [ ] Register run outputs through `plan_artifact_registration` / `apply_artifact_registration` and store the returned artifact IDs; add no second registration path.
- [ ] Store `production_record_ref` when the output is a production deliverable; report a failed registration as `unregistered` without claiming the run is shared or complete.
- [ ] Update `commands/product-analyze.md` with playbook selection over resolved names, preview-before-apply, required claim class, and the four states reported separately.
- [ ] Update `skills/data-analysis-bridge/SKILL.md` required fields to the R2 set, including non-applicability and unknown-cost wording.
- [ ] Tests: successful registration stores IDs; a failed registration stays explicit; documented command guidance matches the implemented resolution order.

**Verify:** `python3 -m unittest tests.test_project_analysis_run_transaction -v`

---

## Stream E — Default Analysis Playbooks

### Task E1: Origination paths and the weekly thin slice

- [ ] Add `templates/analysis-playbooks/weekly-usage.md` as one default playbook with a declared claim class, a numbered `Required Checks` checklist and a `process_ref` whose null `ref` is explained.
- [ ] Add `templates/analysis-playbooks/README.md` describing resolution order, the check-ID rule and the two origination paths.
- [ ] Implement scaffolding: copy a read-only default into the project as `version: 0.1`, `status: candidate`, preview first, leaving the default untouched and refusing to silently overwrite an existing project playbook.
- [ ] Implement run promotion: project a completed run's `claim_class`, `measure.unit`, `checks[]` IDs, `caveats` and output structure into a new project playbook or a proposed update, always `status: candidate`, never setting `approved_by`/`approved_at` and never inventing approved copy. Never automatic.
- [ ] Reuse the existing playbook write path in `scripts/project_production.py`; add no second writer. If creating a new project playbook file needs a writer that does not exist, keep it inside that module and preview-first.
- [ ] Prove the full loop on synthetic fixtures: scaffold a project playbook, run once with every field, run again supplying only the time window, and assert the prefilled fields came from the playbook.
- [ ] Prove promotion: run an ad-hoc analysis with no playbook, promote it, and assert the resulting candidate playbook drives the next run's prefill.

**Verify:** `python3 -m unittest tests.test_analysis_playbooks -v`

### Task E2: The five accepted analyses

- [ ] Add `monthly-trend.md`, `cpo-change.md`, `amount-band.md`, `charging-speed.md`, `policy-impact.md` in the same shape, each vendor-neutral with inputs stated as Sheet/CSV/XLSX/SQL-extract/local-file shapes.
- [ ] Add `tests/test_analysis_playbooks.py` assertions: all five exist, carry the required sections, declare a valid claim class, and name only check IDs that are code checks or defined in their own checklist; an undefined ID fails the build for a default and only warns for a project playbook.
- [ ] Assert no default playbook file contains a numeric threshold or currency amount, so the pack cannot drift into company logic.

**Verify:** `python3 -m unittest tests.test_analysis_playbooks -v`

---

## Stream F — Integration, Diagnostics and Evidence

### Task F1: Validator, Doctor, entrypoints and distribution

- [ ] Make `scripts/validate_project_artifacts.py` and `scripts/project_doctor.py` consume the single run validation/read facade with actionable diagnostics; add no competing validator.
- [ ] Register exact mutation ownership in `config/project-operation-entrypoints.json`, the new assets in `scripts/validate_moduflow.py`, and the new focused suites in `scripts/release_check.py`.
- [ ] Confirm `scripts/project_artifact_registry.py` is unmodified by this issue.
- [ ] Re-run the existing compatibility suites in the file map.

**Verify:** `python3 scripts/validate_project_artifacts.py .` and `python3 scripts/release_check.py .`

### Task F2: Simulations and the acceptance demonstration

- [ ] Implement `tests/test_project_analysis_run_simulation.py` covering S01–S12 of the [simulation matrix](simulation-matrix.md) on synthetic fixtures only.
- [ ] Perform and record the spec's five-step Acceptance Demonstration, including the second-run observation that no field was restated.
- [ ] Record each scenario's observed diagnostics, read-trace summary and before/after byte hashes in `status.md`; never replace an expected cell with an unrun claim.
- [ ] Refresh `spec.ko.md` for Korean review before requesting approval (C9).
- [ ] Report implementation, tests, remote merge, plugin publication, installed package and actual-session application as separate evidence.

**Verify:** `python3 -m unittest tests.test_project_analysis_run_simulation -v`

---

## Verification Commands and Gates

| Gate | Command | Passing condition |
| --- | --- | --- |
| Focused issue suites | `python3 -m unittest discover -s tests -p 'test_*analysis*.py' -v` | All new run and playbook tests pass |
| Compatibility | `python3 -m unittest tests.test_project_knowledge tests.test_project_doctor tests.test_project_lifecycle_transaction tests.test_project_production tests.test_project_operation_audit tests.test_validation_distribution tests.test_release_check -v` | No regression, including existing playbooks parsing unchanged |
| Full suite | `python3 -m unittest discover -s tests -v` | No failure; the existing suite is the regression floor (C3) |
| Project artifacts | `python3 scripts/validate_project_artifacts.py .` | No error diagnostics |
| Release policy | `python3 scripts/release_check.py .` | All checks pass, including commit↔issue linkage (C10) |
| Simulation | `python3 -m unittest tests.test_project_analysis_run_simulation -v` | S01–S12 observed, recorded in `status.md` |
| Acceptance demonstration | Recorded observation, not a test | Step 3 removes the re-explanation; if it does not, the issue is not done |

An expected result is not a passing test. Unit tests, simulated execution, packaged smoke and actual project/host observation remain separate evidence.

## Implementation Readiness Inputs

Before execution begins, record in `implementation-readiness.json`:

- Confirmation that Issue 115 has landed the two playbook fields, or that execution is starting with the deferred order below.
- The exact integration base commit and a re-check of the file map and collision set against it; worktree isolation alone is insufficient.
- Confirmation that no other active task is writing any file in the collision set.
- Explicit human implementation approval (C6). This plan is not that approval.

## Coverage and Execution Order

| Requirement | Stream / Task |
| --- | --- |
| R1 canonical file, one parser, append-only | A1 |
| R2 record schema | A1, A2, C2 |
| R3 playbook as the carrier | B1, B2, C2 |
| R4 minimum code checks and cost rule | A2 |
| R5 four states, amendment, unassigned | A1, C1, D1 |
| R6 follow-up intent | A1, C1 |
| R7 default playbooks and resolution | B2, E1, E2 |
| R8 read contract, bindings, append, routing | C1, C2, D1, D2 |
| AC1–AC3, AC3b | A1, B2, E1, E2 |
| AC4–AC5 | C2 |
| AC6–AC7 | A2 |
| AC8–AC9 | A1, D1 |
| AC10 | C1, D2, F1, F2 |
| Acceptance Demonstration | E1, F2 |

**Order — thin slice first:** `A1 → [115 B1] → B2 → E1 → A2 → C1 → D1` gives one working end-to-end path with a single deliverable type, and the second-run observation can be made there. Then `C2 → D2 → E2 → F1 → F2` widens it to the five analyses and the full evidence set.

**Deferred order if Issue 115 has not landed:** run `A1 → A2 → C1 → D1` first and hold B2 and E1 until the playbook fields exist. D1 is the only task touching shared transaction files and has exactly one writer.

## Next Command

`product:spec 115-playbook-process-and-checklist-extension` first. Then `product:review 091-reproducible-analysis-runs-and-template-pack` to review this plan and the [spec](spec.md) and give or withhold explicit implementation approval.
