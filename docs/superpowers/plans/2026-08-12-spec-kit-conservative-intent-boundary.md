# Spec Kit Conservative Intent Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the open-ended Spec Kit ownership parser with a finite English/Korean request grammar that selects only `clarify`, `analyze`, `checklist`, or `converge` and safely falls back for every noncanonical request.

**Architecture:** `scripts/spec_kit_adapter.py` owns one deterministic `classify_request()` boundary and keeps `select_function()` as a compatibility wrapper. The capability router continues to recognize an explicit Spec Kit prefix, while the adapter validates the entire request before config, asset, template, or project-input access. Existing handoff provenance, result validation, locking, append-only persistence, package validation, and default-disabled behavior remain unchanged.

**Tech Stack:** Python 3 standard library (`re`, `unicodedata`, `unittest`), JSON, Markdown, existing ModuFlow capability router, Spec Kit pilot and release gates; no LLM classifier, parser dependency, Spec Kit CLI runtime, hook, or automatic activation.

## Global Constraints

1. Accept only the approved prefixes `spec kit`, `speckit`, `스펙킷`, and `스펙 킷`.
2. English canonical order is prefix → function → optional target; Korean canonical order is prefix → optional target → function.
3. Accept exactly one of the four approved functions and only the bounded target vocabulary documented in the approved design.
4. Unknown tokens, multiple functions, punctuation clauses, Git/lifecycle/implementation/review/release language, and mixed intent always return fallback without reading overlays, templates, project inputs, or output files.
5. Fallback is a normal structured outcome and includes a canonical retry; it never claims execution or performs a mutation.
6. Keep current project opt-in, host availability, containment, asset hash, input provenance, locking, append-only persistence, and structured JSON error boundaries unchanged.
7. Keep Spec Kit source version `0.16.1`, default availability `false`, and the human activation decision `pending`.
8. Apply the repository patch-version policy to both plugin projections when the implementation is committed; the expected next base version is `0.3.48`.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `scripts/spec_kit_adapter.py` | Canonical grammar tables, `classify_request()`, compatibility selection, and fallback handoff |
| `tests/test_spec_kit_adapter.py` | Unit contract for the finite classifier, no-load fallback, and compatibility wrapper |
| `tests/test_capability_routing.py` | Router-to-adapter integration and single-stage/fallback behavior |
| `skills/spec-kit-validation-bridge/SKILL.md` | User-facing canonical requests and conservative boundary guidance |
| `scripts/spec_kit_pilot.py` | Request-driven pilot execution and classifier evidence aggregation |
| `tests/test_spec_kit_pilot.py` | Deterministic canonical/fallback pilot and provenance regression tests |
| `tests/fixtures/spec-kit-selective-validation/cases.json` | Canonical success and representative fallback pilot cases |
| `tests/fixtures/spec-kit-selective-validation/results/*.json` | Current-input result snapshots for the four selected functions |
| `specs/098-speckit-selective-validation-adapter/{spec.md,spec.ko.md,plan.md,tasks.md,status.md,pilot-report.md,review-handoff.md}` | Canonical contract, evidence, and review projection |
| `issues/098-speckit-selective-validation-adapter.md` | Issue acceptance and latest review evidence |
| `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` | Synchronized patch release projections |

---

### Task 1: Replace the Open-Ended Parser with a Finite Classifier

**Files:**
- Modify: `scripts/spec_kit_adapter.py`
- Modify: `tests/test_spec_kit_adapter.py`

**Interfaces:**
- Consumes: `FUNCTIONS`, existing `_handoff()`, `load_project_config()`, `load_manifest()`, `verify_assets()`, and `read_canonical_inputs()`.
- Produces: `classify_request(request: object) -> dict[str, str | None]` and compatibility `select_function(request: object) -> str | None`.

- [ ] **Step 1: Replace experimental grammar fixtures with the finite success/fallback table**

```python
CANONICAL_REQUESTS = {
    "Spec Kit clarify requirements": "clarify",
    "Spec Kit analyze acceptance criteria": "analyze",
    "Spec Kit checklist spec": "checklist",
    "Spec Kit converge tasks": "converge",
    "스펙킷 요구사항 명확화": "clarify",
    "스펙킷 승인 기준 분석": "analyze",
    "스펙킷 요구사항 체크리스트": "checklist",
    "스펙킷 남은 작업 수렴": "converge",
}

FALLBACK_REQUESTS = (
    "Spec Kit analyze then stage files",
    "Spec Kit clarify which changes to add to requirements",
    "Spec Kit analyze checklist requirements",
    "Spec Kit analyze requirements, then continue issue",
    "스펙킷 요구사항 분석하고 이슈를 완료해줘",
    "Spec Kit analyze unknown target",
)
```

Assert each canonical request returns `outcome == "selected"`, the exact function, `reason_code == "explicit_validation"`, and `retry is None`. Assert every fallback returns `function is None`, a non-empty canonical retry, and one of `ambiguous_request`, `multiple_functions`, or `unsupported_request`.

- [ ] **Step 2: Run the focused tests and confirm RED against the current parser**

Run:

```bash
python3 -m unittest tests.test_spec_kit_adapter.SpecKitAdapterContractTests.test_canonical_request_grammar tests.test_spec_kit_adapter.SpecKitAdapterContractTests.test_noncanonical_requests_return_structured_fallback -v
```

Expected: FAIL because `classify_request()` does not exist and the current parser still accepts free-form phrases or raises `ambiguous_function`.

- [ ] **Step 3: Implement exact normalization and grammar tables**

Use NFKC normalization, case folding, whitespace collapsing, and a bounded optional terminal punctuation trim. Define immutable prefix, function synonym, target phrase, determiner, and Korean-particle tables. Parse only the two approved shapes:

```python
def _normalize_request(request):
    if not isinstance(request, str):
        return ""
    text = unicodedata.normalize("NFKC", request).casefold()
    return " ".join(text.split()).rstrip(".?!")

def classify_request(request):
    text = _normalize_request(request)
    # 1. consume exactly one approved prefix
    # 2. match exactly one complete English or Korean canonical phrase
    # 3. reject every remaining token or clause separator
    # 4. return a fresh dict with outcome/function/reason_code/retry
```

Build the accepted strings from explicit synonym × target tables rather than interpreting verbs, roles, clauses, or token distance. Preserve the guaranteed Korean target-before-function examples and allow only documented particles/determiners inside enumerated phrases.

- [ ] **Step 4: Keep `select_function()` as a zero-side-effect wrapper**

```python
def select_function(request):
    classification = classify_request(request)
    return classification["function"] if classification["outcome"] == "selected" else None
```

Do not retain `NON_GIT_OWNERSHIP_PATTERN`, role inference helpers, modifier parsing, or verb/inflection ownership lists once no live path references them.

- [ ] **Step 5: Make fallback stop before any prerequisite read**

In `build_handoff()`, call `classify_request()` once. For fallback, immediately return `_handoff(..., function=None, outcome="unsupported", ...)` with a fallback override containing the reason and canonical retry. Add a mock-based test proving `load_project_config`, `load_manifest`, `verify_assets`, and `read_canonical_inputs` are never called for a noncanonical request.

- [ ] **Step 6: Run adapter tests and commit the classifier**

Run:

```bash
python3 -m unittest tests.test_spec_kit_adapter -v
git diff --check
```

Expected: all adapter tests PASS; canonical cases select one function, all old free-form positives become fallback, and no fallback loads a template or project input.

Commit:

```bash
git add scripts/spec_kit_adapter.py tests/test_spec_kit_adapter.py
git commit -m "fix(098): bound Spec Kit request classification" -m "Issue: 098-speckit-selective-validation-adapter"
```

---

### Task 2: Align Routing and Bridge Guidance

**Files:**
- Modify: `tests/test_capability_routing.py`
- Modify: `skills/spec-kit-validation-bridge/SKILL.md`
- Modify: `skills/index/SKILL.md`
- Modify: `skills/pm-execution-router/SKILL.md`

**Interfaces:**
- Consumes: Task 1 `classify_request()` and `select_function()`.
- Produces: one Spec Kit router stage only for explicit-prefix candidates; adapter fallback for every candidate outside the canonical grammar.

- [ ] **Step 1: Write router RED tests for selected and fallback outcomes**

```python
def test_canonical_spec_kit_request_routes_exactly_one_function(self):
    route = self.route("Spec Kit analyze requirements", spec_kit_available=True)
    self.assertEqual([stage["adapter_id"] for stage in route["stages"]], ["spec-kit"])
    self.assertEqual(spec_kit.select_function(route["request"]), "analyze")

def test_noncanonical_spec_kit_candidate_falls_back_without_function(self):
    route = self.route("Spec Kit analyze then stage files", spec_kit_available=True)
    self.assertIsNone(spec_kit.select_function(route["request"]))
    handoff = spec_kit.build_handoff(ROOT, self.project, ISSUE_ID, route["request"], True)
    self.assertNotEqual(handoff["outcome"], "ready")
    self.assertIsNone(handoff["function"])
```

Cover all four functions, both languages, disabled/unavailable hosts, all-capability routing, and direct `product:*` aliases.

- [ ] **Step 2: Run the routing tests and confirm RED**

Run:

```bash
python3 -m unittest tests.test_capability_routing -v
```

Expected: FAIL until old phrase-level positive fixtures and ownership-parser assumptions are replaced.

- [ ] **Step 3: Update routing documentation to the finite contract**

Replace claims of natural-language ownership parsing with these guaranteed forms:

```text
Spec Kit clarify requirements
Spec Kit analyze requirements
Spec Kit checklist acceptance criteria
Spec Kit converge tasks
스펙킷 요구사항 명확화
스펙킷 요구사항 분석
스펙킷 승인 기준 체크리스트
스펙킷 남은 작업 수렴
```

Document that explicit-prefix but noncanonical requests receive a native fallback plus retry and load no overlay/template/input. Do not promise arbitrary English/Korean natural-language interpretation.

- [ ] **Step 4: Run bridge/routing/distribution tests and commit**

Run:

```bash
python3 -m unittest tests.test_capability_routing tests.test_spec_kit_adapter tests.test_validation_distribution -v
git diff --check
```

Expected: all tests PASS and distribution still includes the bridge and adapter.

Commit:

```bash
git add tests/test_capability_routing.py skills/spec-kit-validation-bridge/SKILL.md skills/index/SKILL.md skills/pm-execution-router/SKILL.md
git commit -m "docs(098): expose canonical Spec Kit requests" -m "Issue: 098-speckit-selective-validation-adapter"
```

---

### Task 3: Rebuild the Pilot Around the Finite Grammar

**Files:**
- Modify: `scripts/spec_kit_pilot.py`
- Modify: `tests/test_spec_kit_pilot.py`
- Modify: `tests/fixtures/spec-kit-selective-validation/cases.json`
- Modify: `tests/fixtures/spec-kit-selective-validation/results/clarify.json`
- Modify: `tests/fixtures/spec-kit-selective-validation/results/analyze.json`
- Modify: `tests/fixtures/spec-kit-selective-validation/results/checklist.json`
- Modify: `tests/fixtures/spec-kit-selective-validation/results/converge.json`
- Modify: `specs/098-speckit-selective-validation-adapter/pilot-report.md`

**Interfaces:**
- Consumes: Task 1 classifier and current provenance functions `canonical_input_hash()`, `validate_host_result()`, and `persist_validation()`.
- Produces: deterministic evidence for canonical selection, conservative fallback, zero unauthorized effects, and current-input result provenance.

- [ ] **Step 1: Replace open-ended language probes with a finite evidence matrix**

The committed pilot must contain at least:

```python
EXPECTED_COUNTS = {
    "canonical_success": 8,      # four functions × English/Korean
    "availability_fallback": 4, # disabled/unavailable
    "grammar_fallback": 12,     # unknown token, mixed function, clause, Git/lifecycle, punctuation
}
```

Every case derives its observed route, selected function, handoff outcome, loaded template count, and output bytes from the real router/adapter. Fixture-declared `passed` booleans remain forbidden.

- [ ] **Step 2: Add RED tests for deterministic classifier evidence and zero-load fallback**

Assert that two pilot runs produce byte-identical cases, snapshots, and report; all eight canonical cases select exactly one expected function; every grammar fallback has zero function/template fan-out and no output artifact; safety violations equal zero.

Run:

```bash
python3 -m unittest tests.test_spec_kit_pilot -v
```

Expected: FAIL while the pilot still expects ownership phrase-family and metamorphic NLP counters.

- [ ] **Step 3: Update the pilot generator without weakening provenance**

Retain current result-file containment, UTF-8/JSON structured errors, exact input hashes, loaded-context byte accounting, deterministic ordering, and canonical-input provenance release gate. Replace ownership-parser metrics with:

```json
{
  "canonical_success_count": 8,
  "availability_fallback_count": 4,
  "grammar_fallback_count": 12,
  "template_fanout_violations": 0,
  "unauthorized_write_count": 0,
  "ownership_escape_count": 0
}
```

- [ ] **Step 4: Regenerate snapshots and report only after canonical inputs are final**

Run the repository-supported pilot command discovered from `scripts/spec_kit_pilot.py --help`, twice against isolated temporary output roots. Compare SHA-256 hashes of `cases.json`, all four result snapshots, and `pilot-report.md`; then update the tracked canonical copies once.

- [ ] **Step 5: Run pilot, provenance, and release-check tests and commit**

Run:

```bash
python3 -m unittest tests.test_spec_kit_pilot tests.test_release_check -v
python3 scripts/release_check.py .
git diff --check
```

Expected: pilot and release tests PASS; `release_check` reports `valid: true`; changing any canonical input or snapshot makes the provenance subcheck fail.

Commit:

```bash
git add scripts/spec_kit_pilot.py tests/test_spec_kit_pilot.py tests/fixtures/spec-kit-selective-validation specs/098-speckit-selective-validation-adapter/pilot-report.md
git commit -m "test(098): validate conservative Spec Kit pilot" -m "Issue: 098-speckit-selective-validation-adapter"
```

---

### Task 4: Project the Contract, Bump the Patch Version, and Gate Completion

**Files:**
- Modify: `specs/098-speckit-selective-validation-adapter/spec.md`
- Modify: `specs/098-speckit-selective-validation-adapter/spec.ko.md`
- Modify: `specs/098-speckit-selective-validation-adapter/plan.md`
- Modify: `specs/098-speckit-selective-validation-adapter/tasks.md`
- Modify: `specs/098-speckit-selective-validation-adapter/status.md`
- Modify: `specs/098-speckit-selective-validation-adapter/review-handoff.md`
- Modify: `issues/098-speckit-selective-validation-adapter.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.codex-plugin/plugin.json`
- Modify if generated by repository commands: `.moduflow/state.json`, `workspace/goal.md`, `workspace/loop-state.json`, `workspace/dashboard.md`, `workspace/roadmap.md`

**Interfaces:**
- Consumes: Tasks 1–3 implementation and fresh verification counts.
- Produces: one reviewable Issue 098 handoff whose documentation, plugin versions, package inventory, pilot provenance, and tests describe the same finite contract.

- [ ] **Step 1: Replace stale parser claims in canonical Issue 098 artifacts**

Delete claims about clause splitting, nearest verb targets, arbitrary modifiers, and exhaustive English/Korean ownership vocabularies. Add the exact canonical grammar, supported examples, structured fallback fields, zero-load guarantee, and explicit non-goals from the approved design.

- [ ] **Step 2: Update task and review evidence without stale counts**

Add a final completed remediation item referencing the conservative classifier. Record only counts produced by the fresh commands in Step 4; do not copy the previous `167/167` or `1168/1168` values.

- [ ] **Step 3: Bump both plugin projections together**

Set:

```json
// .claude-plugin/plugin.json
"version": "0.3.48"

// .codex-plugin/plugin.json
"version": "0.3.48+codex.20260810222010"
```

Preserve every other manifest field and keep default Spec Kit availability `false`.

- [ ] **Step 4: Run the complete verification matrix**

Run:

```bash
python3 -m unittest tests.test_spec_kit_adapter tests.test_spec_kit_vendor_assets tests.test_spec_kit_pilot tests.test_capability_routing tests.test_validation_distribution tests.test_codex_install_cache -v
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/spec_consistency.py . --issue-id 098-speckit-selective-validation-adapter
python3 scripts/project_lifecycle.py . --check
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
git diff --check
```

Expected: every unittest and gate PASS; lifecycle drift is empty; package inventory is valid; release output has `valid: true` and no errors; tracked worktree contains only intended Issue 098 changes.

- [ ] **Step 5: Perform completion self-review**

Verify directly that:

```text
canonical request -> one selected function -> one template
noncanonical request -> fallback -> zero template/input/output access
accepted result -> current handoff + current input hash -> append-only write
default activation -> false
human decision -> pending
```

Search for stale parser terminology and old evidence counts:

```bash
rg -n "nearest|clause-local|arbitrary modifier|ownership probe|167/167|1168/1168" scripts skills issues/098-speckit-selective-validation-adapter.md specs/098-speckit-selective-validation-adapter tests
```

Any match must be either removed or explicitly historical.

- [ ] **Step 6: Commit the synchronized projection**

```bash
git add .claude-plugin/plugin.json .codex-plugin/plugin.json issues/098-speckit-selective-validation-adapter.md specs/098-speckit-selective-validation-adapter .moduflow/state.json workspace/goal.md workspace/loop-state.json workspace/dashboard.md workspace/roadmap.md
git commit -m "fix(098): finalize conservative Spec Kit boundary" -m "Issue: 098-speckit-selective-validation-adapter"
python3 scripts/release_check.py .
git status --short
```

Expected: the post-commit release gate remains valid and the tracked worktree is clean. Do not push, merge, publish, or enable the capability until the final review is accepted.

---

## Execution Order and Review Gates

1. Task 1 reviewer checks the finite grammar and proves fallback has no reads or writes.
2. Task 2 reviewer checks router ownership and public guidance against Task 1.
3. Task 3 reviewer independently verifies pilot determinism and provenance failure behavior.
4. Task 4 reviewer reads the whole branch diff and reruns the focused and release gates before merge authorization.

The current uncommitted parser/test changes are experimental agent-created work. During Task 1, preserve them only long enough to extract useful failing examples, then remove the open-ended parsing implementation and replace its expectations with the finite contract. Do not stage those four files before Task 1's RED/GREEN cycle is complete.
