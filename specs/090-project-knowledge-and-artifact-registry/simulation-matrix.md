# Simulation Matrix: Project Knowledge and Artifact Registry

Issue: `090-project-knowledge-and-artifact-registry` · Owner: Dongwon Lee
Phase: S01–S14 and temporary packaged smoke observed passing on 2026-09-03; release-policy completion remains integration-owned.
Source: 2026-09-02 delegated request and `8229170:workspace/roadmap.md` cross-phase simulation contract.
Prev: [spec](spec.md) / [plan](plan.md) · Next: integration-owner review with [implementation evidence](status.md).

## Fixture Boundary

Use only generated synthetic files under a TemporaryDirectory. Project A and B have distinct registry-v2 IDs, owners, issue IDs and canary strings. Give both an artifact with the same UUID to prove `(project_id, artifact_id)` scoping. At least B uses non-default workspace/knowledge/memory paths with poisoned default folders. An empty project has no knowledge/catalog; a legacy project has existing unstructured documents whose byte hashes are saved.

Project A includes synthetic `001-synthetic-a`, a population definition, a dated draft report, a superseded report, an approval evidence file and an optional restricted reference. B contains `SYNTHETIC_B_PRIVATE_MARKER`, never real private data. Fixed evaluation date: 2026-09-02. `review_after=2026-09-01` is stale; 2026-09-02 is current. Dates indicate synthetic content scope, not real business measurements.

Git-backed cases use a disposable local repository, commits and a separate detached worktree; never the active source repository, default checkout or integration task's worktree. All subprocess calls flow through the injected runner. No remotes/network/real external connectors. Cleanup is restricted to exact fixture paths; never broad workspace deletion. Fake Git failures and read spies supplement, not replace, real tree/worktree behavior.

## Offline Scenario Matrix

Implemented module: `tests/test_project_knowledge_registry_simulation.py`. All named tests were executed; detailed assertions and observed evidence are recorded in the dated section below.

| ID / proposed test | Input / action | Expected result and proof | Observed |
| --- | --- | --- | --- |
| S01 `test_empty_project_initialization_is_non_destructive` | Inspect empty project, preview init, apply twice | Preview creates nothing; missing-only init creates both workspace files and legacy knowledge structure; second run changes zero bytes; all six wiki sections present | Pass — observed below |
| S02 `test_legacy_migration_preserves_sources` | Existing unstructured wiki/catalog, memory/decision with IDs and relationships; request migration preview | No overwrite/copy/move/ID reassignment; precise manual merge proposal and missing metadata guidance; source hashes unchanged | Pass — observed below |
| S03 `test_project_a_b_switch_keeps_metadata_scoped` | Read A, then B with same artifact UUID and matching query | Distinct project_id and source locator; B nested paths honored; no A/B canary leakage in opposite envelope or traces; no poisoned default read | Pass — observed below |
| S04 `test_required_link_missing_and_local_broken_differ` | Required record with no locators; another with missing local path; valid issue links | REQUIRED_LINK_MISSING vs LOCAL_LINK_BROKEN; no source-ready claim; null external URL alone is not an error | Pass — observed below |
| S05 `test_optional_private_absence_is_metadata_only` | Optional restricted alias unavailable; another optional record has no locator and explained absence | Metadata valid, OPTIONAL_SOURCE_UNAVAILABLE info, unavailable/metadata_only; no body read, upload, network or alternate folder search | Pass — observed below |
| S06 `test_required_private_and_external_are_not_assumed_accessible` | Required private alias absent; required stable external URL not checked; source with available committed local plus external URL | Required private work remains blocked; external accessibility unchecked; available local may satisfy source read without requiring external access | Pass — observed below |
| S07 `test_staleness_and_supersession_preserve_state` | Review-after boundary/null, approved evidence, superseded ID, missing target/cycle; rename a source while keeping ID | Stale/current/unknown independent of draft/approved/superseded; no auto-approval or title substitution; invalid chains error; rename preserves material ID | Pass — observed below |
| S08 `test_fresh_reader_opens_only_selected_original` | New reader with no prior cache; ask for A population definition, inspect wiki/index then select its ID | Home/search content trace contains only wiki/catalog; source trace adds exactly selected definition; report/other source bodies not read; request rationale match reported | Pass — observed below |
| S09 `test_committed_worktree_resume_ignores_author_only_files` | Commit safe wiki/catalog/issue/selected source; add required author-only source locally and catalog it in a later commit; resume in separate worktree at each OID | Original snapshot resumes from committed files; later catalog with absent source reports uncommitted/broken shared source; author worktree's file cannot rescue second worktree; same OID used for all reads | Pass — observed below |
| S10 `test_dirty_staged_ignored_and_missing_evidence_do_not_rescue` | Source modified, staged-only source, ignored file, committed catalog with uncommitted issue or approval evidence | Shared reads use committed bytes; SOURCE_DIRTY/SOURCE_UNCOMMITTED or missing-link diagnostics; no false ready result; local staged index is not a committed source | Pass — observed below |
| S11 `test_registration_failure_and_retry_are_atomic` | New knowledge output plus catalog/backlink; injected failure before/after each replacement, validation failure, retry and conflicting edit | Each failure is no write or verified rollback/recovery_required; no orphan new output; retry has one stable ID/backlink; conflict preserves concurrent edits; lifecycle/projection hashes unchanged | Pass — observed below |
| S12 `test_denial_and_initialization_failure_are_truthful` | Archived/read-only project; partial-init write failure; unsupported uninitialized transaction prerequisites | Authorized read succeeds; denial before lock/staging writes; partial init lists exact paths and retry preserves them; output registration blocks with prerequisites, never creates state/issue automatically | Pass — observed below |
| S13 `test_limits_identity_and_consumer_references_are_explicit` | 25 matches, limit 20, long wiki, unknown identity and unknown artifact ID; 091-style reference uses A ID against B context | total=25/returned=20/omitted=5/truncated=true; bounded home omission visible; unknown identity and mismatch rejected for cross-project references; no fallback to matching title | Pass — observed below |
| S14 `test_unsafe_paths_and_git_failures_never_fallback` | Traversal, absolute/private path, root-escaping symlink, committed symlink/submodule, credential URL, invalid ref, Git runner error | Explicit sanitized diagnostics; no source body/private value echo, shell expansion, arbitrary read, local fallback or guessed commit | Pass — observed below |

## Observable Evidence Format

For each executed scenario append: ID, source commit, command/test name, fixture identity (synthetic ID only), input OID if applicable, expected assertions, observed diagnostics/read trace summary, before/after byte-hash comparison, pass/fail, and remediation if failed. Do not store private temporary absolute paths or source bodies in durable evidence. Expected cells above are never replaced by a claim of observation without a run.

Shared resume requires inspecting both catalog/tree membership and selected-source bytes. Merely checking `git ls-files`, filesystem `exists()`, or a source file count is insufficient. A fresh reader test is a reproducible simulation; actual new-host task loading is a separate observation.

## Observed Results — 2026-09-03

Source snapshot: `e812104` plus the bounded D2 changes in the final implementation diff. Initial explicit run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_knowledge_registry_simulation -v` — 15 tests, 2.892s, exit 0. The complete focused suite reruns these scenarios after review fixes; its final counts are in status.md. Only synthetic project IDs and logical paths are recorded here, never temporary absolute roots or original bodies.

| Scenario | Actual observation / proof | Result |
| --- | --- | --- |
| S01 | Empty read reports REGISTRY_NOT_INITIALIZED; preview hashes remain empty. Both templates and six wiki sections created; second initialization writes nothing and preserves all file hashes. | Pass |
| S02 | Unstructured wiki/catalog and memory record retain their original hashes and IDs/relationships. Catalog reports REGISTRY_SCHEMA_UNSUPPORTED; missing-only initialization does not migrate it. | Pass |
| S03 | The same artifact UUID is scoped separately to synthetic-a and synthetic-b. B uses product/workspace and product/knowledge; poisoned defaults are ignored. Metadata envelopes contain neither original canary; B's explicit selected read returns only B. | Pass |
| S04 | No-locator required metadata reports REQUIRED_LINK_MISSING; missing declared local original reports LOCAL_LINK_BROKEN. Null external URL is preserved; no source-ready claim. | Pass |
| S05 | Optional private and explained no-locator records remain metadata-valid, unavailable and metadata_only at a commit. OPTIONAL_SOURCE_UNAVAILABLE is informational; no source-content reads. | Pass |
| S06 | Required private remains unavailable/metadata_only; required external remains unchecked. A committed local original plus an unchecked external URL is readable/ready through local content only. | Pass |
| S07 | Approved/stale, draft/current at the exact boundary, and superseded/unknown remain independent. Cyclic supersession is rejected. Explicit source rename/amend preserves the stable ID and selected content. | Pass |
| S08 | A real content-read spy observed only wiki/catalog for search, then exactly the selected population source for explicit read. No unrelated report body read; match reasons and logical read trace present. | Pass |
| S09 | Separate detached worktree read the first committed original. Later committed catalog pointing to an author-only file reports LOCAL_LINK_BROKEN in the reader; the author's file cannot rescue it. Every ls-tree call uses the chosen OID. | Pass |
| S10 | Dirty source uses committed content; staged-only and ignored sources report SOURCE_UNCOMMITTED. Uncommitted issue/approval links report their missing-link errors; none of their local bodies are substituted. | Pass |
| S11 | Post-apply validation fault rolls back generated output/catalog/backlink and retains lifecycle bytes. Retry applies once and then noops. C1's eight before/after replacement faults, interrupted recovery and concurrent-source/metadata cases provide the broader fault proof. | Pass |
| S12 | Partial initialization reports the created wiki and failure accurately; retry preserves those hashes. Unsupported prerequisites create neither state nor issue. Archived reads work and writes are denied before transaction directories. | Pass |
| S13 | 25 total / 20 returned / 5 omitted, visible long-home omissions; unbound ID remains explicit. Mismatched root/context is rejected and unknown artifact ID never substitutes a similarly named record. | Pass |
| S14 | Traversal, absolute private paths, credential/token URLs, working/committed symlinks and committed gitlinks are rejected. Invalid refs and runner errors report GIT_SNAPSHOT_UNAVAILABLE with no local fallback or private marker echo. | Pass |
| Packaged smoke | Temporary distribution includes runtime parser/templates; a subprocess outside the source checkout initializes a synthetic target, inspects metadata and reads exactly one selected original through the bundled CLI. No installed cache changed. | Pass |

S09 initial observed OIDs: original/reader checkout `030fa03b6e88a543271da308237e989bb93fff58`; later catalog `4fce2627617563c21e08674723fec8ccd3abdbbf`. These identify disposable synthetic snapshots from that run, not the plugin source. Later reruns create new equivalent fixture OIDs.

S08 observed operations: metadata-content `workspace/knowledge.md`, metadata-content `workspace/artifacts.md`, link-stat `knowledge/references/population.md`, link-stat `issues/001-synthetic-a.md`, source-content `knowledge/references/population.md`. The independent content-read spy also verified that no other original was opened.

## Evidence Layers and Completion

| Layer | Planned command / method | Pass condition | Current observation |
| --- | --- | --- | --- |
| Existing baseline only | `python3 -m unittest tests.test_project_knowledge tests.test_project_memory -q` | Existing behavior remains a usable reference | 2026-09-02: 66 tests passed, exit 0; does not test new 090 behavior |
| New focused/transaction tests | Plan verification commands | All named new behaviors and failure paths pass | Implemented; passing evidence in status.md |
| Synthetic scenario execution | `python3 -m unittest tests.test_project_knowledge_registry_simulation -v` | S01–S14 assertions and observations recorded | 14 scenarios passed; observed table above |
| Package smoke | Temporary package and synthetic target; inspect/select source through bundled command | Parser/templates included, expected read contract, no real cache write | Passed as the 15th simulation test |
| Actual project / fresh host | Separately approved selected project and new task | Short home leads to requested source, access limitations reported | Not authorized / not run |
| Remote merge / publication / installed runtime | Parent/release workflow, separate verification | Evidence for each layer individually | Outside this task's authorized implementation scope |

The 모두의충전 pattern is only a motivating example. No `data-context.md`, `data-manifest.json`, company records or calculations from the actual project are required by these fixtures. A file-based handoff test does not establish automatic chat context loading.
