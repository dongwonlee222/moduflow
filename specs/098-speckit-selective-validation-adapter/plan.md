# Spec Kit Selective Validation Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose Spec Kit 0.16.1 `clarify`, `analyze`, `checklist`, and `converge` as opt-in, advisory ModuFlow validation functions without installing `.specify`, executing upstream commands, or transferring lifecycle ownership.

**Architecture:** Add one stdlib-only adapter module that validates project opt-in, target containment, function selection, host availability, and pinned asset integrity before emitting a read-only handoff. Four exact upstream Markdown templates and one JSON manifest are vendored at the approved SHA; a ModuFlow safety overlay and bridge skill load exactly one template per accepted request. Host results are schema-checked and appended idempotently to canonical `validation.md`, while Issue 097's router remains the single natural-language entry point.

**Tech Stack:** Python 3 standard library, JSON, Markdown, SHA-256, `unittest`, existing ModuFlow capability router and Git-native artifacts; no PyYAML, Spec Kit CLI, database, hook, or new mandatory runtime.

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

1. `scripts/spec_kit_adapter.py` is the single parser and policy owner for project capability config, manifest, function selection, handoff metadata, host-result validation, and `validation.md` persistence.
2. The executable source contract is `vendor/spec-kit/0.16.1/manifest.json`; `adapters/spec-kit.yaml` remains human-reviewable metadata and must not introduce a YAML runtime dependency.
3. The only approved upstream source is `github/spec-kit` version `0.16.1` at SHA `684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5`.
4. Only `clarify.md`, `analyze.md`, `checklist.md`, and `converge.md` may be vendored or loaded. Every request loads exactly one template after both host availability and project opt-in pass.
5. Missing/invalid config, unknown fields, unsafe paths, unapproved functions, missing assets, version/SHA/hash drift, or absent host capability fails closed and returns a truthful native fallback without loading a template.
6. Upstream frontmatter scripts, prerequisite helpers, extension hooks, handoffs, Git operations, shell/PowerShell/Python helpers, and implementation commands are inert text and are never executed.
7. All Spec Kit output is advisory. No adapter or bridge path may modify `spec.md`, `plan.md`, `tasks.md`, code, Git, issue state, roadmap, review, PR, release, or deployment state.
8. Accepted validation evidence is append-only. Duplicate source/input/function/result hashes are byte-stable no-ops; failures and dry runs create no empty headings or files.
9. All paths are resolved beneath an explicit target project. Inputs must remain under the issue/spec scope and output must remain under `specs/<issue-id>/validation.md`.
10. Config files contain no credentials, executable paths, shell commands, host secrets, or implicit global enablement. Configuration writes require explicit `--configure --write`.
11. Offline tests never fetch upstream or invoke a model. The sync command is separate, exact-SHA, hash-gated, and writes only after explicit `--write`.
12. No function becomes automatic in Issue 098. Broader exposure requires a future issue after zero boundary violations and reviewer-confirmed value beyond native checks.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — config and handoff contract | Superpowers TDD + `moduflow:source-adapter-policy` | Fail-closed config, paths, availability, and version checks are behavior and trust boundaries. |
| B — pinned upstream assets | Superpowers TDD + source-adapter policy | Exact files and SHA-256 values must be reproducible without importing the full upstream runtime. |
| C — persistence and safety overlay | Superpowers TDD + `moduflow:git-native-artifact-model` | Advisory results must remain append-only, idempotent, and tied to canonical issue artifacts. |
| D — entrypoint and bridge | `moduflow:pm-execution-router` + review | Natural-language routing must select one function while preserving ModuFlow lifecycle ownership. |
| E — pilot and release | deterministic fixtures + review + verification-before-completion | Value, overlap, context cost, and boundary safety need evidence before any wider recommendation. |

The matrix is guidance and does not replace the Issue 077 implementation-readiness report.

## File Structure

### Create

| Path | Responsibility |
| --- | --- |
| `scripts/spec_kit_adapter.py` | Config/manifest parsing, function selection, containment, handoff/result validation, deterministic rendering, append-only persistence, and CLI |
| `scripts/sync_spec_kit_templates.py` | Exact-SHA upstream retrieval, allowlist enforcement, SHA-256 verification, dry-run, and atomic explicit writes |
| `tests/test_spec_kit_adapter.py` | Config, function, availability, path, handoff, result, persistence, CLI, and negative ownership tests |
| `tests/test_spec_kit_vendor_assets.py` | Manifest schema, exact hashes, allowlist, sync dry-run/write, and drift tests |
| `tests/test_spec_kit_pilot.py` | Fixture completeness, metric math, boundary-zero gate, report determinism, and CLI tests |
| `tests/fixtures/spec-kit-selective-validation/cases.json` | Successful, disabled/unavailable, and ownership-boundary cases for all four functions |
| `tests/fixtures/spec-kit-selective-validation/results/` | Structured advisory result fixtures with reviewer disposition and native-overlap labels |
| `vendor/spec-kit/0.16.1/manifest.json` | Machine-readable approved source, file hashes, permissions, inputs, and fallbacks |
| `vendor/spec-kit/0.16.1/commands/clarify.md` | Exact upstream command template snapshot |
| `vendor/spec-kit/0.16.1/commands/analyze.md` | Exact upstream command template snapshot |
| `vendor/spec-kit/0.16.1/commands/checklist.md` | Exact upstream command template snapshot |
| `vendor/spec-kit/0.16.1/commands/converge.md` | Exact upstream command template snapshot |
| `overlays/spec-kit/selective-validation-policy.md` | Higher-priority ModuFlow read/write, execution, ownership, and output policy |
| `skills/spec-kit-validation-bridge/SKILL.md` | Load one approved template plus overlay and return a structured advisory result |
| `scripts/spec_kit_pilot.py` | Offline fixture evaluation, value/overlap/cost/safety metrics, and deterministic report generation |
| `templates/moduflow-capabilities.json` | Explicit disabled-by-default project config example with approved source metadata |
| `specs/098-speckit-selective-validation-adapter/pilot-report.md` | Generated comparison and reviewer-decision surface |
| `specs/098-speckit-selective-validation-adapter/status.md` | RED/GREEN commits, pilot evidence, validation commands, and review state |
| `specs/098-speckit-selective-validation-adapter/implementation-readiness.json` | Issue 077 report-only gate evidence; currently `ready` before execution |

### Modify

| Path | Responsibility |
| --- | --- |
| `adapters/spec-kit.yaml` | Describe selective role, manifest pointer, function/fallback summary, and ownership exclusions |
| `adapters/capability-routing.json` | Replace Issue 098 setup-only copy with the explicit project opt-in recommendation while keeping fail-closed availability |
| `commands/moduflow.md` | Consume ready/disabled/unavailable/unsupported/blocked adapter outcomes without bypassing lifecycle aliases |
| `skills/index/SKILL.md` | Route explicit Spec Kit validation requests to the bridge and preserve native fallbacks |
| `skills/pm-execution-router/SKILL.md` | Document second-stage Spec Kit function selection after Issue 097 chooses the adapter |
| `scripts/validate_moduflow.py` | Require the adapter, sync tool, manifest, four templates, overlay, bridge, pilot, fixtures, and config template in packaged ModuFlow |
| `tests/test_validation_distribution.py` | Prove the full selective adapter surface is shipped and guidance contains the safety contract |
| `vendor/README.md` | Document exact-SHA selective vendoring and no-edit/no-runtime policy |
| `.claude-plugin/plugin.json` | Apply the repository's required patch version bump for behavior-affecting plugin files |
| `.codex-plugin/plugin.json` | Keep the Codex plugin projection version aligned with the canonical plugin version |
| `issues/098-speckit-selective-validation-adapter.md` | Track plan, execution, pilot, review, and acceptance evidence |
| `.moduflow/state.json` | Advance Issue 098 through execute/review only when artifacts and gates exist |
| `workspace/goal.md` | Keep the active goal's next command aligned |
| `workspace/loop-state.json` | Record readiness, backend, latest verification, and next step |
| `workspace/dashboard.md` | Show the current Issue 098 phase and bounded activation outcome |
| `workspace/roadmap.md` | Keep Issue 098 in Now until pilot/review completes |

## Stable Interfaces

### Approved manifest

`load_manifest(package_root: Path) -> dict` reads this JSON shape and rejects additional templates or mismatched hashes:

```json
{
  "schema": "moduflow.spec-kit-manifest.v1",
  "source": {
    "repository": "github/spec-kit",
    "version": "0.16.1",
    "sha": "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"
  },
  "functions": {
    "clarify": {
      "template": "commands/clarify.md",
      "sha256": "9fce9b3dfe037b67f52486df112f89377ff6c0c598698131cde65cec610b5bba",
      "fallback": "moduflow_short_clarification"
    },
    "analyze": {
      "template": "commands/analyze.md",
      "sha256": "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
      "fallback": "scripts/spec_consistency.py"
    },
    "checklist": {
      "template": "commands/checklist.md",
      "sha256": "0a862264b9b358138d6049590d42b392ee4dadb69d32811d460620f077924d4e",
      "fallback": "moduflow_acceptance_readiness"
    },
    "converge": {
      "template": "commands/converge.md",
      "sha256": "aafba511dea42334373c7ffb9f58e2fb6d82889ea94ec86c1367dbb6a531ca36",
      "fallback": "scripts/project_converge.py --report-only"
    }
  }
}
```

The manifest file location is `vendor/spec-kit/0.16.1/manifest.json`. Template paths resolve relative to that directory and must remain within `commands/`.

### Project config

`load_project_config(project_root: Path) -> dict` accepts exactly:

```json
{
  "schema": "moduflow.capabilities.v1",
  "capabilities": {
    "spec-kit": {
      "enabled": true,
      "source_version": "0.16.1",
      "source_sha": "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5",
      "functions": ["clarify", "analyze", "checklist", "converge"]
    }
  }
}
```

Missing `.moduflow/capabilities.json` normalizes to disabled. Unknown keys, duplicate/non-string functions, or version/SHA mismatches raise `SpecKitAdapterError` with a stable code and no secret-bearing content.

### Python API

The public call signatures are:

- `SpecKitAdapterError(code: str, message: str)` stores stable `code` and safe `message` fields.
- `select_function(request: str) -> str | None` returns one approved function, `None`, or raises `ambiguous_function`.
- `load_project_config(project_root: Path) -> dict` returns a validated or normalized-disabled config.
- `load_manifest(package_root: Path) -> dict` returns the exact approved manifest.
- `verify_assets(package_root: Path, manifest: dict) -> list[dict]` returns four integrity records.
- `build_handoff(package_root: Path, project_root: Path, issue_id: str, function: str, *, host_available: bool) -> dict` returns the stable handoff envelope.
- `validate_result_shape(payload: dict) -> dict` returns a deep-copied canonical result shape.
- `validate_host_result(payload: dict, handoff: dict) -> dict` additionally proves the result matches its ready handoff.
- `persist_validation(project_root: Path, result: dict, *, write: bool = False) -> dict` previews or appends one validated run.

`verify_assets` returns one record per approved function with `function`, `path`, `expected_sha256`, `actual_sha256`, and `valid`; it raises on containment or manifest-schema errors. `build_handoff` never invokes a model or writes a file.

### Handoff result

Ready and fallback handoffs use one stable envelope:

```json
{
  "schema": "moduflow.spec-kit-handoff.v1",
  "outcome": "ready",
  "function": "analyze",
  "issue_id": "098-speckit-selective-validation-adapter",
  "source": {
    "version": "0.16.1",
    "sha": "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5",
    "template": "vendor/spec-kit/0.16.1/commands/analyze.md",
    "template_sha256": "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6"
  },
  "permission": "read",
  "inputs": ["spec.md", "plan.md", "tasks.md", "constitution.md"],
  "output_artifact": "specs/098-speckit-selective-validation-adapter/validation.md",
  "limitations": ["advisory-only", "no upstream scripts or hooks"],
  "fallback": null
}
```

Allowed outcomes are `ready`, `disabled`, `unavailable`, `unsupported`, and `blocked`. Every non-ready result has `source.template: null`, `fallback` set, and no eligible template path.

### Accepted host result

The bridge returns, and `validate_host_result` validates, this shape:

```json
{
  "schema": "moduflow.spec-kit-result.v1",
  "run_id": "sha256:64-lowercase-hex",
  "input_hash": "sha256:64-lowercase-hex",
  "issue_id": "098-speckit-selective-validation-adapter",
  "function": "analyze",
  "source_version": "0.16.1",
  "source_sha": "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5",
  "template_sha256": "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
  "permission": "read",
  "findings": [],
  "limitations": ["advisory-only", "no upstream scripts or hooks"],
  "native_overlap": [],
  "elapsed_ms": 1200,
  "loaded_context_chars": 18400,
  "user_decision": "pending",
  "next_command": "product:plan 098-speckit-selective-validation-adapter"
}
```

`run_id` is derived from source SHA, template hash, function, issue ID, input hash, and canonicalized findings. Persistence uses `<!-- moduflow-spec-kit-run:sha256:{digest} -->` as the duplicate marker.

### CLI

```text
python3 scripts/spec_kit_adapter.py PROJECT_ROOT --issue-id ISSUE_ID --request "스펙킷으로 분석해줘" [--host-available]
python3 scripts/spec_kit_adapter.py PROJECT_ROOT --configure --functions clarify,analyze,checklist,converge --write
python3 scripts/spec_kit_adapter.py PROJECT_ROOT --issue-id ISSUE_ID --accept-result RESULT_JSON [--write]
python3 scripts/sync_spec_kit_templates.py . [--write]
python3 scripts/spec_kit_pilot.py . --fixtures tests/fixtures/spec-kit-selective-validation/cases.json [--write]
```

All commands print JSON to stdout. Failures use `moduflow.spec-kit-error.v1`, never a traceback. Configuration, sync, result acceptance, and pilot report writes occur only with `--write`.

## Implementation Readiness Inputs

- **API contract mapping:** No network service is introduced. The manifest, project config, handoff, host result, Python functions, and CLI shapes above are binding contracts.
- **Test strategy:** Focused `unittest` RED/GREEN slices cover config, selection, path containment, version/hash drift, availability, result validation, append-only persistence, sync behavior, routing guidance, fixture metrics, CLI exit codes, and package distribution. Full discovery protects existing capability routing and lifecycle behavior.
- **Storybook required states:** not applicable; no frontend UI.
- **MSW fixture baseline:** not applicable; no HTTP API or API-backed UI.
- **Playwright smoke matrix:** not applicable; no browser-visible flow.
- **Permission/role model:** handoff is read-only; `--configure --write`, sync `--write`, and accepted-result `--write` are explicit local mutations. No role permits upstream scripts, Git, implementation, review, release, or external writes.
- **Release/rollback verification:** Release requires focused tests, full discovery, zero pilot boundary violations, package/project validation, spec consistency, lifecycle drift `[]`, and `release_check.py` pass. Rollback reverts Issue 098 commits and version bump; target projects with an opt-in file safely fall back because missing package assets make the adapter unavailable, and existing `validation.md` history remains readable.

---

### Stream A — Config and Handoff Contract

#### Task 1 (A1): Fail-Closed Config, Function Selection, and Handoff Skeleton

**Files:**
- Create: `scripts/spec_kit_adapter.py`
- Create: `tests/test_spec_kit_adapter.py`
- Create: `templates/moduflow-capabilities.json`

**Interfaces:**
- Consumes: explicit package root, target root, issue ID, request/function, and host availability.
- Produces: `SpecKitAdapterError`, `select_function`, `load_project_config`, `load_manifest`, `verify_assets`, and `build_handoff` for Tasks B1–D1.

- [ ] **Step 1: Write failing config and selection tests**

```python
class SpecKitConfigTests(unittest.TestCase):
    def test_missing_config_is_disabled_without_creating_a_file(self):
        result = ska.build_handoff(ROOT, self.project, "098-speckit-selective-validation-adapter", "analyze", host_available=True)
        self.assertEqual(result["outcome"], "disabled")
        self.assertFalse((self.project / ".moduflow" / "capabilities.json").exists())

    def test_explicit_korean_request_selects_one_function(self):
        self.assertEqual(ska.select_function("스펙킷으로 요구사항 체크리스트 만들어줘"), "checklist")
        self.assertEqual(ska.select_function("스펙킷으로 남은 작업을 수렴해줘"), "converge")

    def test_multiple_functions_do_not_fan_out(self):
        with self.assertRaisesRegex(ska.SpecKitAdapterError, "ambiguous_function"):
            ska.select_function("스펙킷으로 분석하고 체크리스트도 만들어줘")
```

- [ ] **Step 2: Run the RED tests**

Run: `python3 -m unittest tests.test_spec_kit_adapter.SpecKitConfigTests -v`

Expected: FAIL because `scripts/spec_kit_adapter.py` and its interfaces do not exist.

- [ ] **Step 3: Implement strict config and function parsing**

```python
CONFIG_SCHEMA = "moduflow.capabilities.v1"
HANDOFF_SCHEMA = "moduflow.spec-kit-handoff.v1"
FUNCTIONS = ("clarify", "analyze", "checklist", "converge")
FUNCTION_PHRASES = {
    "clarify": ("clarify", "clarification", "명확화", "핵심 질문"),
    "analyze": ("analyze", "analysis", "분석", "정합성"),
    "checklist": ("checklist", "체크리스트", "요구사항 점검"),
    "converge": ("converge", "convergence", "수렴", "남은 작업"),
}

def select_function(request):
    text = " ".join(str(request or "").lower().split())
    matches = [name for name, phrases in FUNCTION_PHRASES.items() if any(phrase in text for phrase in phrases)]
    if len(matches) > 1:
        raise SpecKitAdapterError("ambiguous_function", "request selects more than one Spec Kit function")
    return matches[0] if matches else None
```

Implement exact-key validation, missing-config normalization, contained issue/output paths, disabled/unavailable/unsupported/blocked envelopes, and an explicit configure dry-run/write path. Until Task B1 installs a valid manifest, ready requests must report `unavailable` rather than claim execution.

- [ ] **Step 4: Run focused config tests**

Run: `python3 -m unittest tests.test_spec_kit_adapter.SpecKitConfigTests -v`

Expected: all config/selection tests PASS and temporary projects receive no implicit writes.

- [ ] **Step 5: Commit Task A1**

```bash
git add scripts/spec_kit_adapter.py tests/test_spec_kit_adapter.py templates/moduflow-capabilities.json
git commit -m "feat(098): add fail-closed Spec Kit adapter contract" -m "Issue: 098-speckit-selective-validation-adapter"
```

### Stream B — Pinned Upstream Assets

#### Task 2 (B1): Pin and Verify the Four Official Templates

**Files:**
- Create: `scripts/sync_spec_kit_templates.py`
- Create: `tests/test_spec_kit_vendor_assets.py`
- Create: `vendor/spec-kit/0.16.1/manifest.json`
- Create: `vendor/spec-kit/0.16.1/commands/clarify.md`
- Create: `vendor/spec-kit/0.16.1/commands/analyze.md`
- Create: `vendor/spec-kit/0.16.1/commands/checklist.md`
- Create: `vendor/spec-kit/0.16.1/commands/converge.md`
- Modify: `adapters/spec-kit.yaml`
- Modify: `vendor/README.md`

**Interfaces:**
- Consumes: Task A1's `load_manifest` and `verify_assets` contract.
- Produces: an exact four-file snapshot and verified manifest that makes a fully opted-in Task A1 handoff eligible for `ready`.

- [ ] **Step 1: Write failing manifest and asset tests**

```python
EXPECTED = {
    "clarify": "9fce9b3dfe037b67f52486df112f89377ff6c0c598698131cde65cec610b5bba",
    "analyze": "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
    "checklist": "0a862264b9b358138d6049590d42b392ee4dadb69d32811d460620f077924d4e",
    "converge": "aafba511dea42334373c7ffb9f58e2fb6d82889ea94ec86c1367dbb6a531ca36",
}

def test_manifest_allows_exactly_four_verified_templates(self):
    manifest = ska.load_manifest(ROOT)
    self.assertEqual(set(manifest["functions"]), set(EXPECTED))
    self.assertEqual({r["function"]: r["actual_sha256"] for r in ska.verify_assets(ROOT, manifest)}, EXPECTED)
```

Also test an extra template, symlink/path escape, one-byte drift, wrong source SHA, network error, dry-run, and explicit sync write with an injected downloader.

- [ ] **Step 2: Run the RED asset tests**

Run: `python3 -m unittest tests.test_spec_kit_vendor_assets -v`

Expected: FAIL because the manifest, templates, and sync module do not exist.

- [ ] **Step 3: Add the manifest, snapshots, and atomic sync implementation**

```python
APPROVED_SHA = "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"
ALLOWED_PATHS = {
    "clarify": "templates/commands/clarify.md",
    "analyze": "templates/commands/analyze.md",
    "checklist": "templates/commands/checklist.md",
    "converge": "templates/commands/converge.md",
}

def fetch_snapshot(downloader, function):
    source_path = ALLOWED_PATHS[function]
    url = f"https://raw.githubusercontent.com/github/spec-kit/{APPROVED_SHA}/{source_path}"
    return downloader(url)
```

The sync path downloads all four files into a temporary directory, checks every expected hash, rejects missing/extra files, and only then atomically replaces the four destinations when `write=True`. It never runs downloaded content. Expand `adapters/spec-kit.yaml` with the manifest pointer, allowed functions, native fallbacks, read-only permission, and explicit ownership exclusions.

- [ ] **Step 4: Run asset and ready-handoff tests**

Run:

```bash
python3 -m unittest tests.test_spec_kit_vendor_assets -v
python3 -m unittest tests.test_spec_kit_adapter.SpecKitConfigTests -v
```

Expected: exact asset/hash tests PASS; a valid config plus `host_available=True` produces `outcome: ready` and one template path.

- [ ] **Step 5: Commit Task B1**

```bash
git add adapters/spec-kit.yaml vendor/README.md vendor/spec-kit/0.16.1 scripts/sync_spec_kit_templates.py tests/test_spec_kit_vendor_assets.py tests/test_spec_kit_adapter.py
git commit -m "feat(098): pin selective Spec Kit templates" -m "Issue: 098-speckit-selective-validation-adapter"
```

### Stream C — Safety and Persistence

#### Task 3 (C1): Add the Safety Overlay and Append-Only Result Persistence

**Files:**
- Create: `overlays/spec-kit/selective-validation-policy.md`
- Modify: `scripts/spec_kit_adapter.py`
- Modify: `tests/test_spec_kit_adapter.py`

**Interfaces:**
- Consumes: Task B1's verified manifest and one ready handoff.
- Produces: `validate_host_result`, deterministic run IDs, Markdown rendering, and `persist_validation` for the bridge and pilot.

- [ ] **Step 1: Write failing safety and persistence tests**

```python
def test_duplicate_accepted_result_is_byte_stable(self):
    handoff = self.ready_handoff("analyze")
    result = self.valid_result(handoff)
    first = ska.persist_validation(self.project, result, write=True)
    before = first["path"].read_bytes()
    second = ska.persist_validation(self.project, result, write=True)
    self.assertFalse(second["changed"])
    self.assertEqual(second["path"].read_bytes(), before)

def test_result_cannot_claim_write_or_wrong_source(self):
    handoff = self.ready_handoff("converge")
    result = self.valid_result(handoff)
    result["permission"] = "write-local"
    with self.assertRaisesRegex(ska.SpecKitAdapterError, "permission_mismatch"):
        ska.validate_host_result(result, handoff)
```

Add tests for malformed results, wrong issue/function/SHA/hash, output escape, upstream-command claims, failed runs, dry-run byte stability, no empty file, one-question-at-a-time `clarify`, and `converge` candidates without task/code mutation.

- [ ] **Step 2: Run the RED persistence tests**

Run: `python3 -m unittest tests.test_spec_kit_adapter.SpecKitPersistenceTests -v`

Expected: FAIL because result validation and persistence are not implemented.

- [ ] **Step 3: Implement strict result validation and append-only rendering**

```python
RESULT_SCHEMA = "moduflow.spec-kit-result.v1"
RUN_MARKER = "<!-- moduflow-spec-kit-run:{run_id} -->"

def persist_validation(project_root, result, *, write=False):
    validated = validate_result_shape(result)
    target = contained_validation_path(project_root, validated["issue_id"])
    marker = RUN_MARKER.format(run_id=validated["run_id"])
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    if marker in existing:
        return {"changed": False, "path": target, "run_id": validated["run_id"]}
    rendered = render_validation_entry(validated)
    if write:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8", newline="") as handle:
            handle.write(rendered)
    return {"changed": bool(write), "path": target, "run_id": validated["run_id"], "preview": rendered}
```

The overlay must explicitly override upstream frontmatter/scripts/hooks/handoffs/mutations, restrict inputs/output, prohibit fan-out and false execution claims, and require the exact result schema. Rendering preserves findings, limitations, native overlap, timing/context metrics, user disposition, and next command.

- [ ] **Step 4: Run focused adapter tests**

Run: `python3 -m unittest tests.test_spec_kit_adapter -v`

Expected: all config, handoff, safety, CLI, and append-only tests PASS; unauthorized mutations remain zero in the fixture assertions.

- [ ] **Step 5: Commit Task C1**

```bash
git add overlays/spec-kit/selective-validation-policy.md scripts/spec_kit_adapter.py tests/test_spec_kit_adapter.py
git commit -m "feat(098): enforce advisory Spec Kit result safety" -m "Issue: 098-speckit-selective-validation-adapter"
```

### Stream D — Entrypoint and Bridge

#### Task 4 (D1): Connect One-Function Bridge to the Existing ModuFlow Router

**Files:**
- Create: `skills/spec-kit-validation-bridge/SKILL.md`
- Modify: `adapters/capability-routing.json`
- Modify: `commands/moduflow.md`
- Modify: `skills/index/SKILL.md`
- Modify: `skills/pm-execution-router/SKILL.md`
- Modify: `tests/test_capability_routing.py`
- Modify: `tests/test_validation_distribution.py`

**Interfaces:**
- Consumes: Issue 097's `delegate` result for adapter ID `spec-kit` and Task A1's adapter CLI/handoff.
- Produces: one lazy bridge invocation, explicit native fallback, and no automatic lifecycle or mutation transition.

- [ ] **Step 1: Write failing routing and bridge-contract tests**

```python
def test_available_spec_kit_routes_one_stage_then_adapter_selects_one_template(self):
    request = "스펙킷으로 요구사항 체크리스트 만들어줘"
    route = self.route(request, availability={"spec-kit": True})
    self.assertEqual(route["outcome"], "delegate")
    self.assertEqual([s["adapter_id"] for s in route["stages"]], ["spec-kit"])
    function = ska.select_function(request)
    handoff = ska.build_handoff(ROOT, self.opted_in_project, self.issue_id, function, host_available=True)
    self.assertEqual(handoff["outcome"], "ready")
    self.assertEqual(handoff["function"], "checklist")
    self.assertTrue(handoff["source"]["template"].endswith("/commands/checklist.md"))
    self.assertFalse((self.opted_in_project / "specs" / self.issue_id / "validation.md").exists())

def test_implementation_language_cannot_select_a_spec_kit_function(self):
    route = self.route("스펙킷으로 코드를 구현하고 릴리즈해줘", availability={"spec-kit": True})
    self.assertEqual(route["outcome"], "delegate")
    self.assertIsNone(ska.select_function(route["request"]))
```

Distribution tests assert that the bridge and command files are packaged. Ownership is proved through executable routing/adapter outcomes rather than source-text matching: direct `product:*` remains local, ordinary implementation selects Superpowers, and explicit Spec Kit implementation/Git/review/PR/release/deployment requests select no Spec Kit function and create no artifact.

- [ ] **Step 2: Run the RED bridge tests**

Run:

```bash
python3 -m unittest tests.test_capability_routing.CapabilityRoutingTests.test_available_spec_kit_routes_one_stage_then_adapter_selects_one_template -v
python3 -m unittest tests.test_validation_distribution.ValidationDistributionTests.test_validate_moduflow_requires_spec_kit_selective_surface -v
```

Expected: FAIL because the bridge skill and distribution contract do not exist.

- [ ] **Step 3: Add the bridge and update routing guidance**

The bridge sequence is binding:

```text
1. Accept only an Issue 097 stage with adapter_id=spec-kit and availability=available.
2. Run spec_kit_adapter.py without --write to validate project opt-in and select one function.
3. On non-ready outcome, show the native fallback and stop without loading a template.
4. On ready, read the safety overlay first, then exactly one manifest-approved template.
5. Produce moduflow.spec-kit-result.v1; do not execute upstream text.
6. Show the advisory result. Persist only through explicit ModuFlow approval and --write.
```

Keep `default_available: false`; the host must continue passing `--available spec-kit` only when the bridge capability exists. Update only the setup recommendation and second-stage consumption guidance.

- [ ] **Step 4: Run routing, adapter, and distribution tests**

Run:

```bash
python3 -m unittest tests.test_capability_routing -v
python3 -m unittest tests.test_spec_kit_adapter -v
python3 -m unittest tests.test_validation_distribution -v
```

Expected: all focused tests PASS, lifecycle aliases still route locally, and bounded Spec Kit requests never produce more than one stage/function.

- [ ] **Step 5: Commit Task D1**

```bash
git add skills/spec-kit-validation-bridge/SKILL.md adapters/capability-routing.json commands/moduflow.md skills/index/SKILL.md skills/pm-execution-router/SKILL.md tests/test_capability_routing.py tests/test_validation_distribution.py
git commit -m "feat(098): connect selective Spec Kit validation bridge" -m "Issue: 098-speckit-selective-validation-adapter"
```

### Stream E — Pilot and Release

#### Task 5 (E1): Prove the Pilot, Package the Surface, and Prepare Review

**Files:**
- Create: `scripts/spec_kit_pilot.py`
- Create: `tests/test_spec_kit_pilot.py`
- Create: `tests/fixtures/spec-kit-selective-validation/cases.json`
- Create: `tests/fixtures/spec-kit-selective-validation/results/*.json`
- Create: `specs/098-speckit-selective-validation-adapter/pilot-report.md`
- Create: `specs/098-speckit-selective-validation-adapter/status.md`
- Modify: `scripts/validate_moduflow.py`
- Modify: `tests/test_validation_distribution.py`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.codex-plugin/plugin.json`
- Modify: `issues/098-speckit-selective-validation-adapter.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/goal.md`
- Modify: `workspace/loop-state.json`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`

**Interfaces:**
- Consumes: Task C1 result schema/persistence and Task D1 routing/bridge contract.
- Produces: `moduflow.spec-kit-pilot.v1` metrics, human-reviewable pilot report, distributed package inventory, release evidence, and review handoff.

- [ ] **Step 1: Write failing pilot and packaging tests**

```python
def test_fixture_matrix_covers_functions_fallbacks_and_ownership_boundaries(self):
    payload = pilot.load_cases(ROOT / "tests/fixtures/spec-kit-selective-validation/cases.json")
    functions = {case["function"] for case in payload["cases"] if case["class"] == "success"}
    self.assertEqual(functions, {"clarify", "analyze", "checklist", "converge"})
    self.assertGreaterEqual(sum(case["class"] in {"disabled", "unavailable"} for case in payload["cases"]), 4)
    self.assertEqual({"implementation", "lifecycle", "git", "review", "release"} - {c["boundary"] for c in payload["cases"] if c["class"] == "ownership"}, set())

def test_pilot_fails_when_any_boundary_metric_is_nonzero(self):
    case = {
        "id": "ownership-git-negative",
        "class": "ownership",
        "function": None,
        "passed": False,
        "findings": [],
        "boundary_violation": True,
        "unauthorized_write": True,
        "fanout": 1,
        "false_execution_claim": False
    }
    report = pilot.evaluate_cases([case])
    self.assertEqual(report["metrics"]["boundary_violations"], 1)
    self.assertFalse(report["passed"])
```

Add tests for at least 13 cases (4 success, 4 disabled/unavailable, 5 ownership), metric denominators, zero-result division, false positives, native overlap, loaded context, elapsed time, deterministic report order, dry-run, explicit write, and non-zero CLI exit on safety failure.

- [ ] **Step 2: Run the RED pilot tests**

Run: `python3 -m unittest tests.test_spec_kit_pilot -v`

Expected: FAIL because the pilot evaluator and fixtures do not exist.

- [ ] **Step 3: Implement deterministic metrics and package registration**

```python
PILOT_SCHEMA = "moduflow.spec-kit-pilot.v1"

def safe_ratio(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else 0.0

def evaluate_cases(cases):
    findings = [finding for case in cases for finding in case.get("findings", [])]
    total = len(findings)
    return {
        "schema": PILOT_SCHEMA,
        "total_cases": len(cases),
        "passed_cases": sum(case["passed"] for case in cases),
        "metrics": {
            "actionable_value": sum(f["reviewer_disposition"] == "useful_unique" for f in findings),
            "false_positive_rate": safe_ratio(sum(f["reviewer_disposition"] == "rejected_invalid" for f in findings), total),
            "native_overlap_rate": safe_ratio(sum(f.get("native_overlap", False) for f in findings), total),
            "boundary_violations": sum(case.get("boundary_violation", False) for case in cases),
            "unauthorized_writes": sum(case.get("unauthorized_write", False) for case in cases),
            "unwanted_fanout": sum(case.get("fanout", 1) > 1 for case in cases),
            "false_execution_claims": sum(case.get("false_execution_claim", False) for case in cases),
        },
    }
```

`pilot-report.md` must distinguish deterministic test evidence from reviewer disposition. It may name Dongwon Lee as human approver only after explicit approval; until then, `Human decision: pending` remains visible and wider activation stays prohibited. Register every new runtime/asset in `validate_moduflow.py`, bump both plugin projections by the repository patch policy, and keep benchmark evidence linked from the issue.

- [ ] **Step 4: Run full verification and generate review artifacts**

Run:

```bash
python3 -m unittest tests.test_spec_kit_adapter tests.test_spec_kit_vendor_assets tests.test_spec_kit_pilot tests.test_capability_routing tests.test_validation_distribution -v
python3 scripts/spec_kit_pilot.py . --fixtures tests/fixtures/spec-kit-selective-validation/cases.json --write
python3 -m unittest discover -s tests
python3 scripts/spec_consistency.py . --issue-id 098-speckit-selective-validation-adapter
python3 scripts/project_lifecycle.py . --drift
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
git diff --check
```

Expected: focused/full tests PASS; pilot boundary violations, unauthorized writes, unwanted fan-out, and false execution claims are all `0`; spec consistency has zero errors; lifecycle drift is `[]`; both validators and release check pass.

- [ ] **Step 5: Commit Task E1 and generate the review handoff**

```bash
git add scripts/spec_kit_pilot.py tests/test_spec_kit_pilot.py tests/fixtures/spec-kit-selective-validation scripts/validate_moduflow.py tests/test_validation_distribution.py .claude-plugin/plugin.json .codex-plugin/plugin.json specs/098-speckit-selective-validation-adapter issues/098-speckit-selective-validation-adapter.md .moduflow/state.json workspace/goal.md workspace/loop-state.json workspace/dashboard.md workspace/roadmap.md
git commit -m "feat(098): validate selective Spec Kit pilot" -m "Issue: 098-speckit-selective-validation-adapter"
python3 scripts/project_execution.py . --issue-id 098-speckit-selective-validation-adapter --review-handoff --write
```

Commit the generated review handoff separately after verifying its paths and commands. Continue directly to `product:review 098-speckit-selective-validation-adapter`; do not claim broader activation before the human pilot decision.

## Execution Order and Parallelism

Tasks A1–E1 are sequential because each consumes contracts or files from the prior task, Tasks A1/C1 share `scripts/spec_kit_adapter.py`, and Tasks D1/E1 share distribution tests. Mechanical upstream snapshot verification inside Task B1 may be delegated, but its manifest and hash results require main-loop review. Worker orchestration should therefore mark this issue `sequential`.

## Next Command

`product:execute 098-speckit-selective-validation-adapter`
