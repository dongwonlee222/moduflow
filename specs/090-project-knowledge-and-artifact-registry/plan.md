# Project Knowledge and Artifact Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL after explicit implementation approval: `superpowers:executing-plans`; execute inline, task-by-task. Do not dispatch subagents or additional tasks for this assignment. Checkboxes below describe future work, not completed implementation.

**Goal:** Make project materials discoverable through a short wiki, one stable-ID registry, selective retrieval and verified issue-linked registration.

**Architecture:** Keep canonical metadata in two workspace Markdown files, with one parser/read facade. Extend existing knowledge initialization and the 103 transaction owner for an explicit issue-linked save; reuse project context and policy. No new persistence/runtime engine.

**Tech Stack:** Existing Python 3 standard library, Markdown, JSON, `unittest`, injected Git runner and existing 103 lock/journal/recovery. No new dependencies.

Issue: `090-project-knowledge-and-artifact-registry` · Owner: Dongwon Lee
Phase: spec/plan implementation approved by Dongwon Lee on 2026-09-02; see [implementation approval](implementation-approval.md). Earlier draft language below preserves the original planning boundary; the approved file map is now executable.
Source / Prev: [spec](spec.md), [existing issue](../../issues/090-project-knowledge-and-artifact-registry.md), 2026-09-02 delegated request and `8229170:workspace/roadmap.md`.
Next: `product:execute 090-project-knowledge-and-artifact-registry`, inline in the existing 090 task, after the recorded readiness check.

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- No new dependencies, database, crawler, vector store, upload, scheduler, analysis calculator, document editor, or UI code.
- Only one resolved project context per operation; no sibling-project traversal or cross-project source payload.
- No company data, metric values, credentials, private absolute paths, or full source text copied into the plugin or shared registry.
- Defaults are `workspace/knowledge.md` and `workspace/artifacts.md`, resolved through the canonical workspace role.
- Lifecycle state, goal, loop, roadmap and dashboard bytes must not change during artifact registration.
- Implementation needs separate explicit approval; the parent task owns 111 integration/release. This plan does not make 090 a release prerequisite for 111.
- Current authoring writes remain confined to `specs/090-project-knowledge-and-artifact-registry/` and the existing issue's requirements/links/checklist. The file map below is future implementation scope, not permission to edit it now.

## Contract and Dependencies

The [spec](spec.md) is the authoritative definition of `moduflow.artifacts.v1`, `moduflow.artifact-registry-read.v1`, R1–R7 and AC1–AC9. Function names below are proposed additions; existing functions are explicitly labeled.

| Interface | Consumes | Produces |
| --- | --- | --- |
| `parse_artifact_registry(text: str) -> dict` | One registry Markdown string | `{schema, entries, diagnostics, metadata_valid}`; one parser, no I/O |
| `render_artifact_entry(entry: dict) -> str` | Valid R2 record | Deterministic ID heading + fenced JSON block; no whole-file rewriting |
| `read_artifact_registry(root, *, project_context, view="working", ref="HEAD", query="", artifact_ids=(), limit=20, runner=None, today=None) -> dict` | One context and request filters | R6 envelope; only wiki/registry content reads, explicit limits and diagnostics |
| `read_artifact_sources(root, artifact_ids, *, project_context, view="working", ref="HEAD", runner=None) -> dict` | Explicit IDs and pinned OID from prior read | `{project_id, snapshot_commit, sources, diagnostics, read_trace}`; source item contains artifact_id, locator, availability, content (selected local only), and handoff |
| `plan_artifact_registration(root, entry: dict, *, issue_id: str, project_context, new_knowledge: dict | None = None, runner=None) -> object` | Record, actual owning issue, optional `{kind, title, spec_path, decision_supported}` | Existing `LifecycleTransactionPlan` with new bounded artifact-register intent; no writes |
| `apply_artifact_registration(root, plan, *, project_context, runner=None) -> dict` | Immutable plan and same context | Existing transaction terminal result plus artifact_id / registered flag; no direct file writer |

`runner(args: list[str], cwd: Path, timeout=None) -> CommandResult` follows existing `project_sync.run_command`; its result has `returncode`, `stdout`, and `stderr` attributes. Git blobs use UTF-8 text for the supported Markdown source slice; unsupported binary input returns an external/manual-open handoff without decoding or copying. Test time uses an injected `date`; UUID allocation occurs once in a registration preview and is retained for apply/retry. Consumers must reject null/unbound project IDs for cross-project run references.

Prerequisites: 102/109 canonical context, 110 capability enforcement and 103 transactions exist at this baseline. 111's source/package/project validation changes must be re-read after integration; do not cherry-pick 111 into this planning branch. No need to wait for 091 or UI code to implement this contract. No new hard dependency is added to the issue graph.

## File Map

| File(s) | Responsibility / change after approval |
| --- | --- |
| New `scripts/project_artifact_registry.py` | Sole registry parser/rendering/read facades and bounded registration adapter |
| Existing `scripts/project_knowledge.py` | Missing-only workspace initialization; opt-in registered knowledge creation using existing pure artifact_body |
| New `templates/workspace/knowledge.md`, `templates/workspace/artifacts.md` | Empty curated wiki and exact canonical metadata format |
| Existing `scripts/project_lifecycle_transaction.py` | Bounded artifact-register intent/planning, source preconditions, validation and no-lifecycle-change path |
| Existing `scripts/project_lifecycle_transaction_storage.py` | Reuse unchanged unless a demonstrated target/recovery schema requirement needs a focused, tested addition; no second lock/journal |
| Existing `scripts/validate_project_artifacts.py`, `scripts/project_doctor.py` | Call single registry validation/read facade; optional capability initialization and actionable diagnostics |
| Existing `commands/product-knowledge.md`, `commands/product-memory.md` | Preview/apply/selective-read/migration guidance and explicit register-after-save contract |
| Existing `config/project-operation-entrypoints.json`, `scripts/validate_moduflow.py`, `scripts/release_check.py` | Exact mutation ownership, source/package assets and focused suite registration |
| New `tests/knowledge_registry_fixture.py` | Synthetic-only record/context/temporary Git fixture builders; no company assets |
| New `tests/test_project_knowledge_registry.py`, `tests/test_project_knowledge_registry_transaction.py`, `tests/test_project_knowledge_registry_simulation.py` | Schema/read, save/failure, and end-to-end handoff proof |
| Existing `tests/test_project_knowledge.py`, `tests/test_project_doctor.py`, `tests/test_project_memory.py`, `tests/test_project_lifecycle_transaction.py`, `tests/test_project_operation_audit.py`, `tests/test_validation_distribution.py`, `tests/test_release_check.py` | Backward compatibility and integration gates |

Keep memory/decision formats and renderers unchanged. Existing records are linked by their exact path and retain their own IDs/relationships; registry search must not call the body-scanning memory search.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — schema/init | writing-plans + TDD + git-native-artifact-model | Stable format and legacy preservation before behavior changes |
| B — reads | TDD + verification-before-completion | Assert read traces, project isolation and committed-only truth |
| C — registration | executing-plans inline + TDD + focused transaction review | Shared lock/planner changes are dependent work, not parallel writes |
| D — integration/evidence | verification-before-completion + PM/spec and privacy self-review | Distinguish observed simulations from expected outcomes |

### Stream A — Canonical Schema and Initialization

#### Task A1: One parser, exact metadata and missing-only templates

Files: create registry module, workspace templates, fixture builder, `tests/test_project_knowledge_registry.py`; modify knowledge initialization and existing knowledge tests. Interfaces: produces parser/renderer and template bodies; consumes R1/R2/R7 and existing resolved paths.

- [ ] Write parser tests first. A valid fixture contains the exact spec R2 example; `make_entry(**overrides)` in the fixture builder returns a fresh copy, and `registry_text(entries)` wraps rendered records in `moduflow.artifacts.v1` frontmatter. Reject duplicate IDs/keys, heading mismatch, unknown schema, invalid UUID/state/date/period, missing read_when, empty owner, invalid link and supersession cycle. Example assertion:

```python
entry = make_entry(summary="A scoped source", read_when="Before A comparisons")
parsed = registry.parse_artifact_registry(registry_text([entry, entry]))
self.assertFalse(parsed["metadata_valid"])
self.assertIn("REGISTRY_DUPLICATE_ID", {d["code"] for d in parsed["diagnostics"]})
```

- [ ] Run `python3 -m unittest tests.test_project_knowledge_registry -v`; expect RED at missing module/API, then actual failing cases after stubs. Do not treat an import failure as sufficient behavioral coverage.
- [ ] Implement pure parsing/rendering and validation. Preserve non-record prose; explicit metadata amendments replace only the selected block after preimage checks. Use `json.loads(..., object_pairs_hook=...)` for duplicate-key rejection, ISO date parsing, UUID version checks and graph traversal for supersession cycles. Do not parse Markdown tables or external files.
- [ ] Extend existing build/apply initialization plans to include the two canonical workspace files. Existing files stay byte-identical even if unstructured. Record created/preserved paths and partial-init failure; dry-run writes nothing; retry creates remaining files. Include six required wiki sections and no sample company metrics.
- [ ] Run `python3 -m unittest tests.test_project_knowledge_registry tests.test_project_knowledge -v`; expect GREEN including nested workspace/knowledge roots, empty and legacy project fixtures, archived denial and no-overwrite behavior. Commit only this approved implementation slice as `feat(090): add canonical knowledge registry schema`.

### Stream B — Metadata Retrieval and Committed Handoff

#### Task B1: Read envelope and selected source access

Files: registry module, fixture builder, registry tests. Interfaces: consumes A1 parser and existing project context/policy; produces the exact R6 facades for 086/091/092.

- [ ] Add RED tests with `SyntheticProject(root, project_id, nested=False)` fixture builder, whose `.context` is one resolved registry-v2 context. `ReadSpy` records logical content reads; `FakeGitRunner` records argv and returns pinned-tree text without subprocess. Keep home/search tests distinct from explicit source reads:

```python
result = registry.read_artifact_registry(
    project_a.root, project_context=project_a.context, query="population", today=fixed_day
)
self.assertEqual(result["project_id"], "synthetic-a")
self.assertEqual(result["returned"], 1)
self.assertFalse(any(r["operation"] == "source-content" for r in result["read_trace"]))
self.assertNotIn("SYNTHETIC_B_PRIVATE_MARKER", repr(result))
```

- [ ] Run `python3 -m unittest tests.test_project_knowledge_registry -v`; expect failure for missing read facade or source reads outside the requested set.
- [ ] Implement metadata-only token filtering and selected-ID resolution. Normalize strings with existing `normalize_project_label`; match all requested tokens, report reasons, sort deterministically by ID, and paginate explicitly with total/omitted/truncated. Add section IDs for bounded home continuation. Resolve the workspace path through the caller's context and enforce read permission before content I/O.
- [ ] Implement working/shared access through one snapshot helper. In shared mode use injected runner to resolve commit OID once, inspect listed tree entries and read wiki/registry/selected UTF-8 Markdown blobs at that OID. Reject symlink/submodule tree modes, unsafe ref/path inputs and shell interpolation. Report working dirty/uncommitted status without using local bytes as fallback. Explicit source reads must receive the pinned OID from the envelope.
- [ ] Test every diagnostic in R4, including required source missing, optional private absent, external unchecked, stale vs unknown freshness, missing issue/approval at commit, invalid ref, runner failure, renamed source/unchanged ID, unknown schema, null project identity and A/B ID collision. Run GREEN focused suite; commit `feat(090): add project-scoped selective artifact reads`.

### Stream C — Issue-Linked Output Registration

#### Task C1: Bounded 103 extension with no lifecycle projection

Files: registry module, transaction module, transaction/registry fixture builders, new registry transaction tests and existing transaction tests. Interfaces: consumes A1 metadata validation and existing `LifecycleTransactionPlan`; produces preview/apply facades and an additive `LifecycleIntent.artifact_change` for `action="artifact-register"` only.

`artifact_change` is a frozen mapping with `entry`, `owning_issue_id`, optional `new_knowledge`, catalog/source expected hashes and preallocated artifact ID. It is not arbitrary path/byte input. Reject a target lifecycle, loop/roadmap/production change, missing issue, mismatch between owning issue and entry issue_ids, or unsafe source path. New knowledge target is derived solely from existing kind directory/title/date; renderer remains `artifact_body`.

- [ ] Add RED tests for preview/no-write, exact allowlisted targets, lifecycle byte preservation, replay/ID stability, catalog preimage conflict and same-ID/different-content conflict. Capture bytes of issue lifecycle line, state, goal, loop, roadmap, dashboard and unrelated records before planning. Assert only the issue backlink changes in the issue document.

```python
before = fixture.snapshot_shared_lifecycle()
plan = registry.plan_artifact_registration(
    fixture.root, entry, issue_id="001-synthetic-a", project_context=fixture.context
)
self.assertEqual(before, fixture.snapshot_shared_lifecycle())
result = registry.apply_artifact_registration(fixture.root, plan, project_context=fixture.context)
self.assertEqual(result["status"], "applied")
self.assertEqual(before, fixture.snapshot_shared_lifecycle())
self.assertEqual(fixture.artifact_backlink_count(entry["id"]), 1)
```

- [ ] Run `python3 -m unittest tests.test_project_knowledge_registry_transaction -v`; expect RED until the bounded action exists. Fixture builder uses the existing lifecycle transaction fixture conventions and supplies initialized prerequisites, not fabricated production data.
- [ ] Add action normalization, immutable identity/replay hashing and a separate target-planning branch that bypasses lifecycle projection. Logical targets are `artifact-registry`, `artifact-owning-issue`, optional `knowledge-output`; existing required control prerequisites are validated but never re-rendered. Validate IDs/issues/evidence against projected content, recheck existing source identity/hash under lock, and append one issue backlink.
- [ ] Reuse existing apply/journal/recovery; include the new action/role in strict serialization and recovery allowlists and projected/post-apply validation. Do not call private persistence from the registry adapter, introduce nested locks, or treat unsupported target plans as successful. An uninitialized project gets explicit missing-prerequisite diagnostics before writes, not implicit issue/state creation.
- [ ] Inject failure before and after each replacement, during projected validation, and after apply; prove verified rollback or honest recovery_required. Test interrupted recovery, concurrent change, archived/read-only denial before lock/staging, idempotent retry, source symlink swap, and 103 legacy intents unchanged. Run `python3 -m unittest tests.test_project_knowledge_registry_transaction tests.test_project_lifecycle_transaction tests.test_project_lifecycle_transaction_storage -v`; commit `feat(090): transact issue-linked artifact registration` only after GREEN.

#### Task C2: Integrate explicit knowledge saves and registration guidance

Files: knowledge module, commands/product-knowledge.md, commands/product-memory.md, knowledge/registry transaction tests. Interfaces: existing `create_knowledge_artifact(..., project_context=...)` adds optional `registry_entry=None`; non-null uses C1, not an initial direct write followed by registration.

- [ ] Add RED tests for opt-in creation: one fresh Markdown output plus catalog/backlink, duplicate retry, failed transaction leaves no new source, legacy creation retains old result fields and reports `registered=false`. Existing memory/decision registration must leave its source bytes/IDs/relationships unchanged.
- [ ] Implement the wrapper by calling `artifact_body` before planning, then C1. Proposed CLI additions: `--inspect`, `--query TEXT`, `--artifact-id ID` (repeatable), `--shared-ref REF`, `--register ENTRY_JSON`, and `--read-sources` (only with explicit artifact IDs). `--register` defaults to preview; `--write --register ... --issue-id ...` applies. No catalog mutations under `--inspect`, no implicit external retrieval, and no source-content reading from search alone. CLI explicit-root context reports unbound identity unless supplied by an already resolved host context; do not fabricate project IDs.
- [ ] Document save success separately from registered/share-ready success. Other writers use explicit register-existing after creating their original; failure reports unregistered and never deletes external/previous originals. Memory command guidance lists existing IDs and exact selected paths; no migration-wide body scan.
- [ ] Run `python3 -m unittest tests.test_project_knowledge tests.test_project_memory tests.test_project_knowledge_registry tests.test_project_knowledge_registry_transaction -v`; commit `feat(090): connect explicit knowledge saves to registry` after GREEN.

### Stream D — Diagnostics, Simulation and Handoff

#### Task D1: Validator, Doctor, operation/distribution integration

Files: validator/Doctor, operation inventory, validate_moduflow/release_check, associated tests from file map. Interfaces: consumes B1/C1; emits optional-capability guidance plus structured registry diagnostics without changing old memory validation.

- [ ] Add RED tests: missing both files is optional-capability guidance; malformed present registry is an error; optional private unavailable remains informational; stale is warning; metadata-only is not source-ready. Source/package asset requirements include the new module/templates/tests. Mutation audit must reject a direct registry writer outside the qualified transaction owner and detect stale ownership declarations.
- [ ] Implement delegation to the sole parser; expose diagnostics without performing network calls or selecting projects. Add exact audit ownership entries for implemented mutators, not blanket exemptions. Update source/package assets and focused release suites, reconciled with 111 validation modes after its integration.
- [ ] Run `python3 -m unittest tests.test_project_doctor tests.test_project_operation_audit tests.test_validation_distribution tests.test_release_check -v`, `python3 scripts/project_operation_audit.py .`, and `python3 scripts/canonical_path_guard.py .`; require no new errors. Commit `feat(090): integrate registry diagnostics and package gates` after GREEN.

#### Task D2: Offline simulations and review evidence

Files: new `tests/test_project_knowledge_registry_simulation.py`, fixture builder; update simulation matrix with actual observations only after execution; create future status/review evidence under this spec directory. No real company project, host installation or deployment mutation.

- [ ] Implement the [simulation matrix](simulation-matrix.md) as synthetic tests. Use TemporaryDirectory repositories for real committed-worktree behavior, injected runners for faults, and generated allowlisted fixture paths. No live remotes, credentials, networks or private datasets. Proposed tests have explicit names in the matrix.
- [ ] Run `python3 -m unittest tests.test_project_knowledge_registry_simulation -v`; require each scenario's assertion, read trace and mutation proof. A fresh-reader object/process has no previous cache; label it simulated fresh-task retrieval, not actual host autoload.
- [ ] Run all gates below, recording exact command, exit, counts, source commit and observations. Findings are appended, not replaced with guessed pass results. PM/spec, transaction safety, privacy and compatibility review must cover all ACs. Commit local evidence only after review; remote PR/merge/install/release are separately authorized later.

## Verification Commands and Gates

These are future implementation gates, not a claim that the new suites exist or passed during planning.

```bash
python3 -m unittest discover -s tests -p 'test_*knowledge*registry*.py' -v
python3 -m unittest tests.test_project_knowledge tests.test_project_memory tests.test_project_lifecycle_transaction tests.test_project_lifecycle_transaction_storage -v
python3 -m unittest discover -s tests -v
python3 scripts/spec_consistency.py . --issue-id 090-project-knowledge-and-artifact-registry
python3 scripts/validate_project_artifacts.py .
python3 scripts/project_operation_audit.py .
python3 scripts/canonical_path_guard.py .
python3 scripts/release_check.py .
git diff --check
```

Release check remains the original issue's criterion; use 111's source-mode equivalent if its integrated CLI changes this command. Record that exact equivalence, not a weakened gate. Packaged smoke uses a temporary package/target fixture, not the installed cache: inspect and select a source through the bundled entrypoint and prove templates/parser are included. Actual host/project observation is a separate authorized step, not required to claim an offline simulation passed and not silently omitted from a release report.

## Implementation Readiness Inputs

- API contract mapping: the Contract and Dependencies table maps each Python facade's request/response to spec R1–R7. R6 defines the project-scoped read envelope and explicit-ID source-read response; R4 defines safe diagnostics and error/unknown states; R5 defines registration/replay/failure results. There are no HTTP endpoints or live connectors.
- Test strategy: schema + path/policy unit tests, transaction failure injection, real temporary committed-worktree handoff, packaged smoke, and full regressions.
- Storybook required states: not applicable; 090 has no screen/component implementation. Empty, malformed, stale, denied and unavailable states are Python/JSON cases in S01–S14, not Storybook renders.
- MSW fixture baseline: not applicable; no HTTP client/server is introduced. Existing injected Git runners and local synthetic fixtures cover the actual interfaces.
- Playwright smoke matrix: not applicable; UI belongs to 086/092. S03/S08/S09 prove project isolation and fresh-reader/committed-worktree lookup without claiming browser or actual host execution.
- Permission: existing read/write project capabilities, no grant from a registry state or hidden tab; external retrieval remains host-authorized.
- Deployment: none in this planning task. Future release requires source/package evidence and independent publication/install/runtime reporting.
- Rollback: revert approved code commits in reverse dependency order; do not remove catalogs, material IDs, legacy records or recovery evidence. Older readers may report unsupported schema, never silently erase it. Recover unfinished transactions through existing 103 recovery before code downgrade; no manual journal cleanup.

## Coverage and Execution Order

| Acceptance | Task / proof |
| --- | --- |
| AC1 initialization/legacy/empty/partial failure | A1; S01/S02/S12 |
| AC2 metadata/wiki/stable identity/period/state | A1/B1; S03/S07 |
| AC3 required/broken/optional-private/external/stale diagnostics | A1/B1/D1; S04–S07 |
| AC4 metadata-first/limits/non-default/A-B isolation | B1; S03/S08/S13 |
| AC5 committed snapshot/no local rescue | B1/D2; S09/S10/S14 |
| AC6 atomic registration/noop/rollback/unchanged lifecycle | C1/C2; S11/S12 |
| AC7 migration/memory/decision/policy | A1/C2/D1; S02/S12 |
| AC8 shared consumers/unbound identity/supersession | B1; S03/S07/S13 |
| AC9 simulations, all gates and truthful evidence | D1/D2; all scenarios + packaged smoke |

Execution is inline and ordered A1 → B1 → C1 → C2 → D1 → D2. Shared parser/transaction files make parallel implementation inappropriate in this slice. Stop for a material contract/safety expansion, not for minor naming details. Spec/plan approval remains one combined human decision.

## Next Command

`product:execute 090-project-knowledge-and-artifact-registry` — approval and scope are recorded in implementation-approval.md; merge/publication remain separate.
