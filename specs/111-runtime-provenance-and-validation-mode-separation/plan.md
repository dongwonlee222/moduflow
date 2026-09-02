# Runtime Provenance and Validation Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. The user requires inline execution without subagents. Steps use checkbox syntax for tracking.

**Goal:** Distinguish source/package/project validation and report evidenced package/process identity without building a runtime manager.

**Architecture:** One read-only provenance module serves existing validator, Doctor and MCP consumers. The explicit installer creates an atomic package receipt; persistent processes retain a startup snapshot rather than rereading a mutable installation on every request.

**Tech Stack:** Existing Python standard library, unittest, JSON, filesystem staging, existing stdio MCP and Markdown commands. No new service or dependency.

Issue: `111-runtime-provenance-and-validation-mode-separation` · Owner: Dongwon Lee.
Source: `spec.md`, its linked F-003/F-004 findings, and the 2026-09-02 planning/simulation request.
Phase: approved for inline implementation by Dongwon Lee on 2026-09-02; proceed through A–D without per-edit approval. Real installation/publication remains separately gated.
Prev: `spec.md` · Checklist: `tasks.md` · Next: `product:review 111-runtime-provenance-and-validation-mode-separation` (implementation review; source evidence in `status.md`).

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- Work only in `/Users/dongwon.lee/.config/superpowers/worktrees/moduflow/110-project-operation-capability-enforcement`; do not change the default checkout or installed caches during implementation/testing.
- Preserve the existing 25 untracked Issue 103 plan files and the roadmap/goal changes. Never stage them through a wildcard.
- Planning used `codex/103-atomic-lifecycle-state-transaction`; implementation uses `codex/111-runtime-provenance-and-validation-mode-separation` in this same worktree with the required Issue trailer. Do not reset/recreate the worktree.
- No subagents. Four reviewable streams, one active implementation stream at a time; do not create a new approval round for each test/edit.
- Source mode retains all existing gates. Installed mode excludes only source-development requirements, not shipped runtime safety fixtures/evidence.
- `loaded_at` means the observed startup of the reported `runtime_kind`, never install time, file mtime, request time, or a guessed host reload.
- Runtime consumers never amend the receipt. Unknown evidence is null with a reason; a local receipt is not a signed attestation.
- Simulations use temporary roots, fake homes and injected runners. No real host update, network, deployment, outbound message or paid execution.
- `spec.md`, `plan.md` and `tasks.md` are the canonical planning chain; do not independently duplicate this plan under Superpowers docs.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
|---|---|---|
| A — contract and explicit modes | Superpowers TDD; ModuFlow Git-native artifact model | Preserve existing gates and prove missing/invalid evidence behavior. |
| B — package receipt | Superpowers TDD; systematic-debugging only on a failure | Fault injection must establish atomic metadata and old-cache preservation. |
| C — consumers | Superpowers TDD | Doctor and persistent MCP must agree without inventing host load evidence. |
| D — verification | verification-before-completion; direct inline review | Separate assertions, simulation results, process smoke and real-host observations. |

## File Structure

| Action | Files | Responsibility |
|---|---|---|
| Create | `scripts/runtime_provenance.py` | Single receipt/manifest reader, role inspection, runtime snapshot and read-only JSON CLI |
| Create | `tests/runtime_provenance_fixture.py`, `tests/test_runtime_provenance.py`, `tests/test_runtime_provenance_simulation.py` | Synthetic fixtures, unit/error cases and offline scenarios |
| Modify | `scripts/validate_moduflow.py`, `scripts/release_check.py` | Explicit validation modes, strict source role and distribution requirements |
| Modify | `scripts/register_codex_personal_marketplace.py` | Prepared cache/receipt publication and conflict preservation |
| Modify | `scripts/project_doctor.py`, `scripts/mcp_server.py` | Early target-role guard, additive evidence and stable process snapshot |
| Modify | `tests/test_validation_distribution.py`, `tests/test_release_check.py`, `tests/test_codex_personal_install.py`, `tests/test_project_doctor.py`, `tests/test_installed_plugin_staleness.py`, `tests/test_mcp_server.py` | Existing interface regressions and focused additions |
| Modify | `config/project-operation-entrypoints.json` | Classify new installer write helpers as package-maintenance, not target-project authorization |
| Modify | `commands/product-status.md`, `commands/product-doctor.md`, `docs/release-checklist.md`, `docs/upgrade-guide.md` | Explicit modes, unknown/runtime wording and actual-host evidence |
| Later evidence | This spec directory's `status.md`, `review.md`, `release.md`; release manifests | Record actual results/version only when those actions occur |

There is no `scripts/project_status.py`; do not create it. Use the shared reader CLI and existing MCP status implementation. No frontend changes: Storybook, MSW and browser smoke are not applicable to 111. The new data-home UI retains its own later tests.

## Stable Interfaces

Signatures below are implementation contracts, not existing APIs:

```python
# scripts/runtime_provenance.py
inspect_package(package_root: Path) -> dict
inspect_validation_target(path: Path, *, requested_role: str) -> dict
capture_runtime(package_root: Path, *, runtime_kind: str,
                observed_at: str | None = None,
                host: str | None = None,
                session_id: str | None = None) -> dict
package_payload_sha256(package_root: Path) -> str

# scripts/validate_moduflow.py; keep old positional callers
validate_moduflow(path, *, mode="auto") -> dict

# scripts/register_codex_personal_marketplace.py
build_package_provenance(source: Path, payload_root: Path, *, version: str,
                         installed_at: str, runner) -> dict
write_package_provenance(staging_root: Path, receipt: dict) -> None
copy_plugin_cache(source: Path, home: Path, version: str, *,
                  runner=None, installed_at=None) -> Path

# scripts/project_doctor.py / scripts/mcp_server.py
inspect_project(path, include_preflight=True, *, project_context=None,
                runtime_snapshot=None) -> dict
handle_request(req, root, *, project_context=None,
               runtime_snapshot=None) -> dict | None
```

`inspect_package` returns `schema="moduflow.package-evidence.v1"`, `package_version`, `package_path`, `source_commit`, `source_dirty`, `installed_at`, `payload_sha256`, `receipt_state` (`valid|missing|invalid`), `provenance_source`, `unavailable_reasons`, `error_codes` and `warnings`. Missing manifests are invalid evidence, not a successful empty object. `inspect_validation_target` returns `requested_role`, `validation_role`, `role_source`, `valid`, `error_codes` and `recommendation`.

`capture_runtime` returns exactly the `moduflow.runtime-provenance.v1` object in the spec. When passed no observed time it returns `loaded_at=null` with reason `startup_not_observed`. CLI/MCP entry points supply an explicit UTC startup observation once. Do not add runtime writers to this module.

Fixture contract: `make_package(root: Path, *, version="0.0.1", receipt=None) -> Path` creates a synthetic manifest and optional receipt for reader tests; it is not a complete installable distribution. Full distribution tests use a staged copy of the source's declared runtime files and never weaken validation to accept the small reader fixture.

## Implementation Sequence

### Stream A — Shared Evidence and Explicit Validation Modes

**Files:** create the provenance module/fixture/unit tests; modify validator, release check and their tests. Consumes `spec.md`; produces the stable read-only APIs and explicit `source|installed|auto` modes for B/C.

- [x] Add this RED contract test in `tests/test_runtime_provenance.py`; create only the described test fixture, not the runtime implementation.

```python
def test_legacy_package_does_not_invent_install_or_load_time(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = make_package(Path(tmp), version="0.0.1")
        result = capture_runtime(root, runtime_kind="cli_process")
        self.assertEqual(result["package_version"], "0.0.1")
        self.assertIsNone(result["installed_at"])
        self.assertIsNone(result["loaded_at"])
        self.assertEqual(result["unavailable_reasons"]["loaded_at"],
                         "startup_not_observed")
        self.assertIsNone(result["host"])
        self.assertIsNone(result["session_id"])
```

- [x] Run `python3 -m unittest tests.test_runtime_provenance -v`; expect missing API failure, not an unrelated import/environment failure.
- [x] Implement the one evidence reader: validate object/schema/value types, timezone-aware timestamps, manifest agreement and null reasons. Read the exact package, never the requested project or newest cache. Implement receipt hash verification in installed self-check, not on every status request. Preserve legacy missing-receipt warnings separately from invalid-receipt errors.

```python
# Validation requirement selection; common checks below remain unchanged.
if mode not in {"source", "installed", "auto"}:
    raise ValueError("unsupported validation mode")
selected = mode
if selected == "auto":
    selected = "source" if (root / ".git").exists() else "installed"
required_files = [name for name in REQUIRED_FILES
                  if selected == "source"
                  or name not in SOURCE_ONLY_REQUIRED_FILES]
```

- [x] Add explicit CLI `--mode source|installed|auto` and `--json`; keep default human output and old import calls. Add `scripts/runtime_provenance.py` to runtime requirements; classify its new unit tests as source-only. Have `run_release_check` inspect the source target before any source-only subprocess and call `validate_moduflow(..., mode="source")` explicitly.
- [x] Add mode tests for full source, source without required test file, valid installed layout, missing runtime asset, invalid mode, source role on a cache, malformed receipt and manifest mismatch. Keep existing runtime fixtures and selective Spec Kit evidence requirements.
- [x] Test host-aware version agreement: Codex's exact published version may carry a `+codex` suffix while its base matches the canonical Claude version. Reject actual base/receipt mismatch, not a valid build suffix.
- [x] Run `python3 -m unittest tests.test_runtime_provenance tests.test_validation_distribution tests.test_release_check -v`; all must pass before committing `feat(111): separate validation roles and package evidence` with an Issue trailer.

### Stream B — Package Receipt and Cache Preservation

**Files:** installer, installer tests, package-maintenance classification. Consumes A's reader/digest/installed validation; produces prepared packages with `.moduflow-package.json`. Writes belong only to explicit package installation.

- [x] Add RED tests with a fake home and injected runner. The following helper test proves metadata atomicity; additional cases in `simulation-matrix.md` prove existing-cache preservation.

```python
def test_receipt_replace_failure_preserves_existing_bytes(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        destination = root / ".moduflow-package.json"
        old = b'{"previous":"evidence"}\n'
        destination.write_bytes(old)
        with mock.patch.object(installer.os, "replace",
                               side_effect=OSError("injected rename failure")):
            with self.assertRaises(OSError):
                installer.write_package_provenance(root, {"schema": "test"})
        self.assertEqual(destination.read_bytes(), old)
```

- [x] Run `python3 -m unittest tests.test_codex_personal_install -v`; confirm the new behavior fails before modifying the installer.
- [x] Implement `build_package_provenance`: use the injected command-runner convention for `git rev-parse HEAD` and source dirty state; retain explicit unknown reasons for non-Git fixture/archive sources. Compute digest from the prepared payload, after distribution manifest normalization and before receipt creation. Invalid runner results are diagnostics, not invented revisions.
- [x] Implement `write_package_provenance` with same-directory `tempfile.mkstemp`, UTF-8 sorted JSON plus newline, file flush/fsync, `os.replace`, then directory fsync where supported. Surface real I/O failures and clean only the exact temporary file created by this call. Use this ordering:

```python
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    json.dump(receipt, stream, ensure_ascii=False, sort_keys=True)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
os.replace(temp_path, staging_root / ".moduflow-package.json")
```

- [x] Replace delete-before-copy in `copy_plugin_cache` with prepare → receipt → explicit installed validation → publish. A cache path must be a concrete child of the fake/authorized cache root; reject symlink destinations. Identical validated content reuses the original receipt/install timestamp; different or invalid same-version content returns `PACKAGE_DESTINATION_CONFLICT`. Never delete a prior usable package on copy, validation, write or rename failure. Normalize distribution manifests in the prepared payload; keep source manifest changes within the existing explicit release/version workflow, not diagnostic reads.
- [x] Prepare/validate the cache before installer activation changes. Do not claim full atomicity across marketplace/config/link files; report activation failure separately and preserve the previous cache for explicit restoration. Update installer fixtures to contain declared runtime files where full package validation is expected.
- [x] Register any newly discovered write helper under `scope=package-maintenance`, `classification=package_maintenance`, `operation=none` with its exact function name and rationale. No target-project capability may authorize global installation.
- [x] Run `python3 -m unittest tests.test_codex_personal_install tests.test_runtime_provenance tests.test_project_operation_audit -v`; commit `feat(111): record package provenance without replacing conflicting caches` with an Issue trailer after GREEN.

### Stream C — Doctor, Status and Persistent MCP

**Files:** Doctor, MCP, corresponding tests, staleness tests and command docs. Consumes A's evidence/role APIs and B's receipts; produces additive process-scoped runtime evidence on every status/Doctor response, including errors.

- [x] Add a RED snapshot test plus early-role-guard tests. Build two independent fixture project roots from existing MCP test setup; do not copy private project content.

```python
def test_runtime_snapshot_survives_manifest_change(self):
    with tempfile.TemporaryDirectory() as tmp:
        package = make_package(Path(tmp), version="0.0.1")
        old = capture_runtime(package, runtime_kind="mcp_process",
                              observed_at="2026-09-02T00:00:00Z")
        manifest = package / ".claude-plugin" / "plugin.json"
        manifest.write_text(json.dumps({"name": "moduflow", "version": "0.0.2"}))
        self.assertEqual(old["package_version"], "0.0.1")
        new = capture_runtime(package, runtime_kind="mcp_process",
                              observed_at="2026-09-02T01:00:00Z")
        self.assertEqual(new["package_version"], "0.0.2")
        self.assertNotEqual(old["loaded_at"], new["loaded_at"])
```

- [x] Run `python3 -m unittest tests.test_mcp_server tests.test_project_doctor tests.test_installed_plugin_staleness -v`; prove the missing snapshot/role behavior fails.
- [x] In Doctor, inspect the requested target before `git_root`, `local_project_root`, registry resolution, transaction inspection or schema validation. A wrong-role result preserves `moduflow`, `schema_gates`, `lifecycle`, `recovery` keys for existing callers, returns nonzero CLI status, reports `TARGET_ROLE_MISMATCH`/`TARGET_ROLE_AMBIGUOUS`, and recommends explicit installed validation. Do not report guessed missing project files for a cache. Existing project capability/recovery reads remain intact.
- [x] Thread `runtime_snapshot` as a keyword-only optional parameter through `handle_request`, `_handle_line`, status and Doctor handlers. Check target role before MCP project-context creation too. Capture the exact module package once in `main`, not from `MODUFLOW_ROOT` (which selects the project). Keep the handler deterministic by injecting its observation rather than calling a clock in request dispatch.

```python
snapshot = capture_runtime(
    Path(__file__).resolve().parent.parent,
    runtime_kind="mcp_process",
    observed_at=datetime.now(timezone.utc).isoformat(),
)
# Each line forwards the same snapshot to the handler.
response = handle_request(req, root, runtime_snapshot=snapshot)
```

- [x] Initialize `serverInfo.version` from this same snapshot, retaining a protocol-compatible fallback only when version evidence is invalid and exposing its reason in diagnostics. Add the same nested provenance object to success and error status/Doctor results without changing `moduflow.mcp.v1` or `state_schema`.
- [x] Reuse the shared package reader in 065 staleness detection for actual located package paths. Preserve `checked/stale/recommendations`; label registration-only versions as inventory, report parse failures, and never select the newest cache as the active process. Add exact assertions that project A/B selection changes only project results, not executing package identity.
- [x] Update command docs: status runs the shared read-only provenance CLI or uses MCP output; Doctor explicitly selects installed self-check for the executing package and project checks for the target. State that CLI/MCP process evidence does not prove conversational skill reload.
- [x] Run `python3 -m unittest tests.test_mcp_server tests.test_project_doctor tests.test_installed_plugin_staleness tests.test_runtime_provenance -v`; commit `feat(111): expose process-scoped provenance in diagnostics` with an Issue trailer after GREEN.

### Stream D — Simulations, Review and Release Evidence

**Files:** simulation tests, existing packaging tests, release docs and this directory's evidence. Consumes A/B/C; proves AC1–AC8. No new runtime subsystem.

- [x] Encode S01–S12 from `simulation-matrix.md` in `tests/test_runtime_provenance_simulation.py`. Use `TemporaryDirectory` fixtures and injected subprocess/network sentinels. Execute only offline tests; all test inputs, expected decisions and observed fields are retained in the result log.

```python
# Hash only files before/after; directories are recorded separately in the fixture.
def file_snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts}

before = file_snapshot(project)
with mock.patch("subprocess.run", side_effect=AssertionError("unexpected process")), \
     mock.patch("socket.create_connection", side_effect=AssertionError("unexpected network")):
    result = doctor.inspect_project(project, include_preflight=False,
                                    runtime_snapshot=snapshot)
self.assertEqual(file_snapshot(project), before)
self.assertEqual(result["runtime_provenance"], snapshot)
```

- [x] Run `python3 -m unittest tests.test_runtime_provenance_simulation -v`. Any mismatch stays failed; never relabel an unavailable host as a passing simulation.
- [x] Add a packaged subprocess smoke: start CLI and MCP from a temporary cache with the development source import path unavailable; initialize MCP, call status and Doctor, then repeat within the same process. Set `PYTHONDONTWRITEBYTECODE=1`; use a 10-second subprocess timeout and no shell/network. Verify the loaded module/package path stays inside the temporary cache and required imports succeed without full source tests.
- [x] Run focused tests once, then `python3 -m unittest discover -s tests -v`, `python3 scripts/validate_project_artifacts.py .`, `python3 scripts/project_lifecycle.py . --drift`, `python3 scripts/release_check.py .`, and `git diff --check`. Record actual commands, exit codes, counts, failures, source commit and package digest in `status.md`; no prefilled pass counts.
- [x] Review AC1–AC8 against the actual diff and evidence in `review.md`. Check invalid metadata, source gates, snapshot stability, caller compatibility, permission inventory and no diagnostic side effects. Any required fix returns to its owning stream.
- [x] Update release/upgrade instructions and prepare `release.md` distinguishing implementation, local tests, simulations, packaged smoke, remote merge, publication, installed receipt, actual host observations and rollback. Select the release version from then-current source history; planning does not bump versions or publish.
- [ ] After separately authorized publication, record R01/R02 observations in a fresh Codex/Claude task. If the host cannot expose skill-load evidence, record that field as unavailable and retain process-scoped proof only. Do not claim whole-host reload from a successful CLI invocation. Commit the verification evidence after actual checks; do not mark Issue 111 complete merely because this plan exists.

## Simulation and Acceptance Mapping

| Acceptance | Stream | Evidence |
|---|---|---|
| AC1 explicit modes and runtime requirements | A, D | S01–S03, existing release/distribution regressions |
| AC2 wrong-target guard and project diagnostics | C, D | S04, S05; sentinels prove no parent resolution or project mutation |
| AC3 consistent provenance and null reasons | A, C, D | S06, S07, S11; response parity including error paths |
| AC4 atomic receipt, cache preservation and conflicts | B, D | S08, S09; injected failure snapshots |
| AC5 persistent startup vs new process vs host session | C, D | S10, packaged process smoke, R01/R02 |
| AC6 inventory is not active-runtime proof | C, D | S11 and existing 065 tests |
| AC7 offline simulation coverage | D | S01–S12 with synthetic fixtures and no-network/no-write assertions |
| AC8 truthful release and host evidence | D | Evidence columns in release record, no unobserved pass claims |

## Review, Deployment and Rollback Gates

Spec/plan approval precedes behavior changes. Each stream completes its RED/GREEN/review checkpoint without repeated product-scope questioning. Pause only for a material scope/permission decision or a safety failure that cannot be handled inside this plan.

Deployment still needs all source gates, review and explicit human publication approval. Do not replace a real user cache during testing. Preserve the prior approved package and registration values for an explicit rollback; reactivation/reload and its verification are separate release actions. Never restore by editing the prior immutable receipt. Source rollback uses an explicit revert of Issue 111 commits, not a hard reset or removal of existing user changes.

## Plan Self-Review

The four streams cover all eight acceptance criteria. The small fixture is explicitly not installable; full package checks use real declared distribution assets. Existing result keys, 065 hints and source gates are retained. No UI/automation/company-standard work is hidden inside 111. Execution is inline in the existing worktree. Detailed simulation cases are a test reference, not extra independent implementation plans.
