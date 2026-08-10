# Single-Entry Capability Routing Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/moduflow` resolve specialist requests through a deterministic,
permission-aware `none | delegate | sequence | clarify` contract and prove the
contract against at least 24 offline routing simulations.

**Architecture:** Add one stdlib-only JSON capability registry whose IDs reference
the existing YAML adapters, one pure Python routing module, and one fixture-driven
simulation runner. Command and skill guidance consume the routing result but remain
responsible for execution; the router never imports, invokes, or installs a specialist.

**Tech Stack:** Python 3 standard library, JSON, `unittest`, existing ModuFlow
Markdown command/skill files, Git-native issue/spec/status artifacts.

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

1. `scripts/capability_routing.py` is the single parser and policy owner for
   `adapters/capability-routing.json` and `moduflow.capability-routing.v1` results.
2. The router is pure and offline: it never imports, invokes, installs, or mutates a
   specialist, external service, repository, issue, or artifact.
3. No YAML dependency is added. The JSON registry references existing adapter IDs;
   YAML adapter files remain descriptive source records.
4. Ordinary lifecycle work resolves to `none`. A bounded request resolves to at most
   one stage. Only explicit ordered language may produce `sequence`.
5. Every non-`none` stage carries adapter ID, reason code, permission class,
   permission state, availability, issue ID, and output artifact.
6. `write-external` never becomes `allowed` without explicit approval in the routing
   context. Unavailable capabilities never report a ready stage.
7. `spec-kit` remains unavailable by default in Issue 097. Issue 098 owns selective
   activation; 097 may only return a truthful setup recommendation.
8. Golden fixture changes require review. The simulation runner never rewrites
   expected values or silently accepts changed snapshots.
9. Safety metrics are hard gates: unwanted fan-out, permission violations, false
   capability claims, and missing handoff fields must all equal zero.
10. Existing `product:*` direct commands remain a power-user escape hatch and do not
    require specialist routing.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — registry contract | Superpowers TDD + `moduflow:source-adapter-policy` | Registry validation must fail closed without turning adapters into copied runtimes. |
| B — routing policy | Superpowers TDD + `moduflow:pm-execution-router` | `none`, one-specialist delegation, ordered sequences, permissions, and fallbacks are product behavior. |
| C — simulation | Superpowers TDD + data-backed regression fixtures | Representative Korean/English requests must measure stable routing and safety failures. |
| D — entrypoint and release | `moduflow:git-native-artifact-model` + review + verification-before-completion | User-facing routing guidance, packaged files, lifecycle state, and completion evidence must agree. |

The matrix guides execution and does not replace the Issue 077 readiness gate.

## File Structure

### Create

| Path | Responsibility |
| --- | --- |
| `adapters/capability-routing.json` | Versioned descriptors, trigger/exclusion phrases, default availability, permissions, output artifacts, and ordering metadata for supported specialist adapters |
| `scripts/capability_routing.py` | Registry validation, deterministic request routing, permission/availability projection, result schema, and read-only CLI |
| `scripts/capability_routing_simulation.py` | Golden-case evaluation, safety metrics, semantic-pair consistency, JSON report, and exit status |
| `tests/fixtures/capability-routing/cases.json` | At least 24 reviewed Korean/English lifecycle, specialist, overlap, availability, permission, and sequence cases |
| `tests/test_capability_routing.py` | Registry and routing unit tests |
| `tests/test_capability_routing_simulation.py` | Simulation metric, fixture, write, and CLI tests |
| `specs/097-single-entry-capability-routing-contract/status.md` | RED/GREEN commits, simulation totals, release evidence, and review verdict |

### Modify

| Path | Responsibility |
| --- | --- |
| `commands/moduflow.md` | Route natural-language specialist requests through the executable contract while preserving direct aliases |
| `skills/index/SKILL.md` | Define how agents consume `none`, `delegate`, `sequence`, and `clarify` outcomes |
| `skills/pm-execution-router/SKILL.md` | Keep lifecycle work local and specialist execution lazy and artifact-gated |
| `scripts/validate_moduflow.py` | Require the registry, router, simulation runner, and fixtures in distributed ModuFlow packages |
| `tests/test_validation_distribution.py` | Prove new routing files and contract guidance are packaged |
| `issues/097-single-entry-capability-routing-contract.md` | Track plan, execution, review, and verification evidence |
| `.moduflow/state.json` | Track Issue 097's active phase and next command |
| `workspace/goal.md` | Attach Issue 097 to the trustworthy-execution goal |
| `workspace/loop-state.json` | Keep Issue 097's durable next step and verification checkpoint |
| `workspace/dashboard.md` | Surface current Issue 097 phase and simulation gate |
| `workspace/roadmap.md` | Place Issue 097 before its blocked follow-up Issue 098 |

## Stable Interfaces

### Registry

`capability_routing.load_registry(root)` reads and validates exactly this shape:

```python
{
    "schema": "moduflow.capability-registry.v1",
    "lifecycle_triggers": ["status", "상태", "issue", "이슈"],
    "sequence_markers": ["then", "after", "그다음", "후", "하고"],
    "external_write_triggers": ["publish", "upload", "외부", "게시", "업로드"],
    "capabilities": [
        {
            "id": "data-analytics",
            "adapter_path": "adapters/data-analytics.yaml",
            "purpose": "product and business data analysis",
            "triggers": ["analytics", "metric", "kpi", "분석", "지표"],
            "explicit_triggers": ["data analytics", "데이터 분석"],
            "exclusions": ["issue status", "이슈 상태"],
            "default_available": False,
            "permission": "read",
            "output_artifact": "specs/{issue_id}/analysis.md",
            "setup_recommendation": "Enable the Data Analytics capability in the current host."
        }
    ]
}
```

The committed registry includes `data-analytics`, `product-design`, `superpowers`,
`documents`, and `spec-kit`. Every `default_available` is `false`; Spec Kit's setup
recommendation points to `098-speckit-selective-validation-adapter`.

Use these reviewed descriptor values; phrase lists may only change through a fixture-backed
review:

| ID | Triggers | Exclusions | Default | Permission | Output artifact |
| --- | --- | --- | --- | --- | --- |
| `data-analytics` | `analytics`, `analyze`, `metric`, `kpi`, `dashboard`, `data`, `분석`, `지표`, `데이터`, `대시보드` | `issue status`, `이슈 상태`, `status dashboard`, `상태 대시보드` | unavailable until host-confirmed | `read` | `specs/{issue_id}/analysis.md` |
| `product-design` | `design`, `ux`, `ui`, `prototype`, `wireframe`, `screen`, `onboarding`, `디자인`, `프로토타입`, `와이어프레임`, `화면`, `온보딩` | `design issue status`, `디자인 이슈 상태` | unavailable until host-confirmed | `write-local` | `specs/{issue_id}/design-brief.md` |
| `superpowers` | `implement`, `build`, `code`, `test`, `bug`, `api`, `구현`, `개발`, `코드`, `테스트`, `버그` | `implementation plan`, `구현 계획` | unavailable until host-confirmed | `write-local` | `specs/{issue_id}/status.md` |
| `documents` | `docx`, `pptx`, `xlsx`, `presentation`, `slides`, `발표자료`, `슬라이드`, `문서 파일` | `report metric`, `리포트 지표` | unavailable until host-confirmed | `write-local` | `specs/{issue_id}/deliverables.md` |
| `spec-kit` | `spec kit`, `speckit`, `스펙 킷`, `스펙킷` | `product:spec`, `스펙 상태` | unavailable | `read` | `specs/{issue_id}/validation.md` |

The registry-level lifecycle phrases are `product:`, `current status`, `issue status`,
`show issues`, `roadmap status`, `현재 상태`, `이슈 상태`, `이슈 목록`, `로드맵 보여`,
`현재 목표`, and `다음 단계`. The broad doctor alias `검사해줘` is resolved before this
router and is intentionally not a registry lifecycle phrase, so an explicit request such as
`스펙킷으로 스펙을 검사해줘` can still select Spec Kit. Sequence markers are `then`, `after`,
`and then`, `그다음`, `후`, `한 다음`, and `하고`; a marker counts only when it lies
between two different matched adapters. External-write phrases are `publish to posthog`,
`upload to google drive`, `posthog에 반영`, `google drive에 업로드`, `외부에 저장`,
and `게시해`.

### Routing call

```python
route_request(
    request: str,
    registry: dict,
    *,
    issue_id: str = "unassigned",
    target_root: Path = Path("."),
    availability: dict[str, bool] | None = None,
    approved_permissions: set[str] | None = None,
    completed_artifacts: set[str] | None = None,
) -> dict
```

The result shape is:

```python
{
    "schema": "moduflow.capability-routing.v1",
    "request": "전환율 하락 원인을 분석해줘",
    "issue_id": "097-single-entry-capability-routing-contract",
    "outcome": "delegate",
    "stages": [
        {
            "adapter_id": "data-analytics",
            "reason_code": "trigger_match",
            "permission": "read",
            "permission_state": "allowed",
            "availability": "available",
            "output_artifact": "specs/097-single-entry-capability-routing-contract/analysis.md",
            "gate_after": None
        }
    ],
    "current_stage": 0,
    "sequence_state": "not_applicable",
    "clarification": None,
    "fallback": None
}
```

Outcome invariants:

- `none`: `stages == []`, `current_stage is None`.
- `delegate`: exactly one stage.
- `sequence`: two or more ordered stages; only index `current_stage` is eligible
  and every earlier stage's `output_artifact` is the next-stage gate. Verified
  `completed_artifacts` advance the route and `sequence_state` reports `ready`, `blocked`, or
  `complete`.
- `clarify`: no stages and one concise `clarification`.
- unavailable delegation keeps the matching stage with
  `availability: unavailable`, `current_stage: null`, and a truthful `fallback`.
- `write-external` uses `permission_state: requires_approval` unless
  `write-external` appears in `approved_permissions`.

Review amendment: the CLI always resolves its registry from its installed/bundled package root,
while `project_path` is used only as the target artifact root. All capability defaults are
fail-closed; the host must pass confirmed availability explicitly. Canonical issue IDs and
resolved output paths are contained under target `specs/`, and CLI failures use a stable JSON
error envelope rather than a traceback.

### Simulation call

```python
simulate_cases(root: Path, cases: list[dict]) -> dict
```

It returns:

```python
{
    "schema": "moduflow.capability-routing-simulation.v1",
    "total": 24,
    "passed": 24,
    "failed": 0,
    "metrics": {
        "route_mismatches": 0,
        "adapter_mismatches": 0,
        "unwanted_fanout": 0,
        "permission_violations": 0,
        "false_capability_claims": 0,
        "missing_handoff_fields": 0,
        "semantic_pair_inconsistencies": 0
    },
    "cases": []
}
```

The CLI prints this JSON and exits `1` when any case fails or any safety metric
is non-zero. `--write` writes the same deterministic payload to
`specs/097-single-entry-capability-routing-contract/simulation-report.json`.

## Implementation Readiness Inputs

- **API contract mapping:** `load_registry`, `route_request`, and `simulate_cases`
  are the only new callable boundaries; command/skill files consume their JSON.
- **Test strategy:** focused unit tests prove registry failure, route precedence,
  permission and availability behavior; the fixture suite proves all eight product
  boundaries and Korean/English consistency; full discovery protects existing aliases.
- **Storybook required states:** not applicable; no frontend UI.
- **MSW fixture baseline:** not applicable; no HTTP API.
- **Playwright smoke matrix:** not applicable; no browser-visible flow.
- **Permission/role model:** `read`, `write-local`, and `write-external`; only the last
  requires explicit approval in routing context.
- **Release condition:** 24 or more simulations pass with every safety metric at zero,
  focused/full tests pass, spec consistency has zero errors, project validation is
  valid, release check is valid, and review has no Critical or Important findings.
- **Rollback condition:** revert entrypoint guidance before router code, then registry;
  no migration, external write, plugin installation, or persisted user data is involved.

---

### Stream A — Capability Registry and Validation

#### Task A1: Add the versioned registry and fail-closed loader

**Files:**

- Create: `adapters/capability-routing.json`
- Create: `scripts/capability_routing.py`
- Create: `tests/test_capability_routing.py`

**Interfaces:** Produces `load_registry(root)` and `validate_registry(payload, root)`.
Stream B consumes the validated descriptor list.

- [ ] **Step 1: Write RED registry tests**

Add tests that assert the real registry loads five unique IDs, all referenced adapter
paths exist, permissions belong to `read | write-local | write-external`, artifact
templates contain `{issue_id}`, and `spec-kit` defaults unavailable. Add temporary
registry tests for duplicate IDs, missing adapter files, empty triggers, and an unknown
permission; each must raise `RegistryError` with the failing field in its message.

```python
class CapabilityRegistryTests(unittest.TestCase):
    def test_real_registry_is_valid_and_spec_kit_is_inactive(self):
        registry = capability_routing.load_registry(ROOT)
        by_id = {item["id"]: item for item in registry["capabilities"]}
        self.assertEqual(len(by_id), 5)
        self.assertFalse(by_id["spec-kit"]["default_available"])
        self.assertEqual(
            set(by_id),
            {"data-analytics", "product-design", "superpowers", "documents", "spec-kit"},
        )

    def test_duplicate_ids_fail_closed(self):
        payload = valid_registry()
        payload["capabilities"].append(dict(payload["capabilities"][0]))
        with self.assertRaisesRegex(capability_routing.RegistryError, "duplicate"):
            capability_routing.validate_registry(payload, ROOT)
```

- [ ] **Step 2: Run the RED tests**

Run:

```bash
python3 -m unittest tests.test_capability_routing.CapabilityRegistryTests -v
```

Expected: FAIL because `capability_routing`, the registry, and `RegistryError` do
not exist.

- [ ] **Step 3: Implement the registry and loader**

Create the five descriptors and implement:

```python
REGISTRY_SCHEMA = "moduflow.capability-registry.v1"
PERMISSIONS = {"read", "write-local", "write-external"}

class RegistryError(ValueError):
    pass

def load_registry(root):
    root = Path(root).resolve()
    path = root / "adapters" / "capability-routing.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"registry read failed: {exc}") from exc
    validate_registry(payload, root)
    return payload
```

`validate_registry` checks the schema, list/object types, unique IDs, adapter path
containment under `root/adapters`, file existence, non-empty trigger lists, boolean
availability, permission values, output template, and setup recommendation. It returns
the input payload without normalization so committed ordering stays visible.

- [ ] **Step 4: Run the focused registry tests**

Run:

```bash
python3 -m unittest tests.test_capability_routing.CapabilityRegistryTests -v
```

Expected: all registry tests PASS.

- [ ] **Step 5: Commit Stream A**

```bash
git add adapters/capability-routing.json scripts/capability_routing.py tests/test_capability_routing.py
git commit -m "feat(097): add capability routing registry" -m "Issue: 097-single-entry-capability-routing-contract"
```

### Stream B — Deterministic Routing Contract

#### Task B1: Implement `none`, one-specialist delegation, clarification, and sequences

**Files:**

- Modify: `scripts/capability_routing.py`
- Modify: `tests/test_capability_routing.py`

**Interfaces:** Consumes the validated registry. Produces `route_request(...)` and
the `moduflow.capability-routing.v1` result consumed by Stream C and entrypoint docs.

- [ ] **Step 1: Write RED routing tests**

Add exact assertions for:

```python
def test_lifecycle_request_routes_to_none(self):
    result = route("현재 이슈 상태 보여줘")
    self.assertEqual(result["outcome"], "none")
    self.assertEqual(result["stages"], [])

def test_bounded_analytics_selects_exactly_one_adapter(self):
    result = route("전환율 하락 원인을 분석해줘")
    self.assertEqual(result["outcome"], "delegate")
    self.assertEqual([s["adapter_id"] for s in result["stages"]], ["data-analytics"])

def test_overlap_without_order_asks_one_question(self):
    result = route("데이터 분석과 온보딩 디자인 개선안 부탁해")
    self.assertEqual(result["outcome"], "clarify")
    self.assertEqual(result["stages"], [])
    self.assertEqual(result["clarification"].count("?"), 1)

def test_explicit_multistage_request_is_ordered_and_gated(self):
    result = route("전환율을 분석한 후 대시보드를 구현해줘")
    self.assertEqual(result["outcome"], "sequence")
    self.assertEqual(
        [s["adapter_id"] for s in result["stages"]],
        ["data-analytics", "superpowers"],
    )
    self.assertEqual(result["current_stage"], 0)
    self.assertEqual(result["stages"][0]["gate_after"], result["stages"][0]["output_artifact"])
```

Also cover one-domain repeated triggers, exclusions winning over generic triggers,
explicit adapter naming, whitespace/case normalization, and direct `product:*`
commands resolving to `none`.

- [ ] **Step 2: Run routing tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_capability_routing.CapabilityRoutingTests -v
```

Expected: FAIL because `route_request` is missing.

- [ ] **Step 3: Implement deterministic candidate scoring and outcome selection**

Implement phrase matching with normalized lowercase text and stable registry order:

```python
def matched_positions(text, phrases):
    matches = []
    for phrase in phrases:
        position = text.find(phrase.lower())
        if position >= 0:
            matches.append((position, phrase))
    return sorted(matches)

def candidate_score(text, descriptor):
    positive = matched_positions(text, descriptor["triggers"])
    negative = matched_positions(text, descriptor.get("exclusions", []))
    if negative:
        return 0, []
    return len(positive), positive
```

Routing precedence is direct `product:*` or lifecycle trigger → `none`; no
specialist candidate → `none`; one candidate → `delegate`; multiple candidates
with explicit sequence markers between their first matched positions → ordered
`sequence`; otherwise → `clarify`. Sequence order follows matched text position,
not registry order, and repeated matches for one adapter are deduplicated.

- [ ] **Step 4: Implement stage projection, availability, and permissions**

Resolve availability from the call override first and `default_available` second.
Upgrade effective permission to `write-external` when an external-write phrase is
present. Set `requires_approval` unless the approved permission set contains
`write-external`. An unavailable result has no current stage and carries its
descriptor's setup recommendation.

Required stage fields are created in one function:

```python
REQUIRED_HANDOFF_FIELDS = {
    "adapter_id", "reason_code", "permission", "permission_state",
    "availability", "output_artifact", "gate_after",
}

def build_stage(descriptor, issue_id, *, permission, permission_state, available):
    output = descriptor["output_artifact"].format(issue_id=issue_id)
    return {
        "adapter_id": descriptor["id"],
        "reason_code": "trigger_match",
        "permission": permission,
        "permission_state": permission_state,
        "availability": "available" if available else "unavailable",
        "output_artifact": output,
        "gate_after": None,
    }
```

- [ ] **Step 5: Add the read-only CLI and run GREEN tests**

The CLI accepts request, project root, issue ID, repeated unavailable IDs, and
repeated approved permission classes; it prints JSON and never writes:

```bash
python3 scripts/capability_routing.py "전환율을 분석해줘" . --issue-id 097-single-entry-capability-routing-contract
```

Run:

```bash
python3 -m unittest tests.test_capability_routing -v
```

Expected: all routing and registry tests PASS.

- [ ] **Step 6: Commit Stream B**

```bash
git add scripts/capability_routing.py tests/test_capability_routing.py
git commit -m "feat(097): enforce single-entry routing contract" -m "Issue: 097-single-entry-capability-routing-contract"
```

### Stream C — Offline Golden Simulation

#### Task C1: Add 24 boundary fixtures and the safety report

**Files:**

- Create: `tests/fixtures/capability-routing/cases.json`
- Create: `scripts/capability_routing_simulation.py`
- Create: `tests/test_capability_routing_simulation.py`

**Interfaces:** Consumes `route_request`. Produces
`moduflow.capability-routing-simulation.v1`, exit status, and optional
`simulation-report.json` for Stream D verification.

- [ ] **Step 1: Commit the exact fixture matrix**

Encode three cases in each class below. Each record includes `id`, `class`,
`request`, `locale`, `issue_id`, `availability`, `approved_permissions`,
`expected_outcome`, `expected_adapters`, `expected_permissions`,
`expected_availability`, `expected_artifacts`, and optional `semantic_pair_id`.

| Class / ID | Request | Context | Expected |
| --- | --- | --- | --- |
| lifecycle / `L01-ko-status` | `현재 이슈 상태 보여줘` | Korean, pair `lifecycle-status` | `none` |
| lifecycle / `L02-en-status` | `Show the current issue status` | English, pair `lifecycle-status` | `none` |
| lifecycle / `L03-ko-roadmap` | `로드맵 보여줘` | Korean | `none` |
| analytics / `A01-ko-conversion` | `전환율 하락 원인을 분석해줘` | Korean, pair `analytics-conversion` | `delegate: data-analytics`, `read`, available |
| analytics / `A02-en-conversion` | `Analyze why conversion declined` | English, pair `analytics-conversion` | `delegate: data-analytics`, `read`, available |
| analytics / `A03-ko-kpi` | `활성 사용자 KPI를 정의해줘` | Korean | `delegate: data-analytics`, `read`, available |
| design / `D01-ko-onboarding` | `온보딩 화면 디자인을 개선해줘` | Korean, pair `design-onboarding` | `delegate: product-design`, `write-local`, available |
| design / `D02-en-onboarding` | `Improve the onboarding screen design` | English, pair `design-onboarding` | `delegate: product-design`, `write-local`, available |
| design / `D03-ko-prototype` | `결제 프로토타입을 만들어줘` | Korean | `delegate: product-design`, `write-local`, available |
| implementation / `I01-ko-api` | `결제 API를 구현해줘` | Korean, pair `implementation-api` | `delegate: superpowers`, `write-local`, available |
| implementation / `I02-en-api` | `Implement the payment API` | English, pair `implementation-api` | `delegate: superpowers`, `write-local`, available |
| implementation / `I03-ko-login-test` | `로그인 버그 테스트를 추가해줘` | Korean | `delegate: superpowers`, `write-local`, available |
| overlap / `O01-ko-analysis-design` | `데이터 분석과 온보딩 디자인 개선안 부탁해` | Korean, pair `overlap-analysis-design` | `clarify` |
| overlap / `O02-en-analysis-design` | `Give me data analysis and onboarding design improvements` | English, pair `overlap-analysis-design` | `clarify` |
| overlap / `O03-ko-dashboard-report` | `지표 대시보드 분석 리포트를 만들어줘` | Korean | `delegate: data-analytics`; documents excluded by absent document-file trigger |
| unavailable / `U01-ko-speckit` | `스펙킷으로 스펙을 검증해줘` | default registry availability | `delegate: spec-kit`, unavailable, Issue 098 fallback |
| unavailable / `U02-en-analytics` | `Analyze conversion decline` | `availability.data-analytics=false` | `delegate: data-analytics`, unavailable, setup fallback |
| unavailable / `U03-ko-design` | `온보딩 화면을 디자인해줘` | `availability.product-design=false` | `delegate: product-design`, unavailable, setup fallback |
| external-write / `P01-ko-posthog` | `분석 결과를 posthog에 반영해줘` | no approval | `delegate: data-analytics`, `write-external`, `requires_approval` |
| external-write / `P02-en-posthog-approved` | `Analyze conversion and publish to PostHog` | `approved_permissions=[write-external]` | `delegate: data-analytics`, `write-external`, `allowed` |
| external-write / `P03-ko-drive-upload` | `발표자료를 만들어 google drive에 업로드해줘` | no approval | `delegate: documents`, `write-external`, `requires_approval` |
| multi-stage / `M01-ko-analysis-build` | `전환율을 분석한 후 대시보드를 구현해줘` | Korean, pair `sequence-analysis-build` | `sequence: data-analytics → superpowers` |
| multi-stage / `M02-en-analysis-build` | `Analyze conversion, then build the dashboard` | English, pair `sequence-analysis-build` | `sequence: data-analytics → superpowers` |
| multi-stage / `M03-ko-design-build` | `화면을 디자인하고 그다음 구현해줘` | Korean | `sequence: product-design → superpowers` |

Pair IDs connect L01/L02, A01/A02, D01/D02, I01/I02, O01/O02, and M01/M02.
Unavailable and approval pairs remain separate because their contexts intentionally differ.

- [ ] **Step 2: Write RED simulation tests**

```python
def test_committed_fixture_corpus_has_eight_classes_and_24_cases(self):
    cases = load_cases(ROOT)
    self.assertGreaterEqual(len(cases), 24)
    self.assertEqual(
        {case["class"] for case in cases},
        {"lifecycle", "analytics", "design", "implementation", "overlap",
         "unavailable", "external-write", "multi-stage"},
    )

def test_simulation_has_zero_safety_failures(self):
    report = simulation.simulate_cases(ROOT, load_cases(ROOT))
    self.assertEqual(report["failed"], 0)
    for key in (
        "unwanted_fanout", "permission_violations", "false_capability_claims",
        "missing_handoff_fields", "semantic_pair_inconsistencies",
    ):
        self.assertEqual(report["metrics"][key], 0)
```

Add mutation tests that alter one expected adapter, mark an unavailable stage ready,
remove a required handoff field, and create an unapproved external write. Each must
increment the matching metric and make `report["failed"]` non-zero.

- [ ] **Step 3: Run simulation tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_capability_routing_simulation -v
```

Expected: FAIL because the simulation module does not exist.

- [ ] **Step 4: Implement case comparison and safety metrics**

Compare each actual route against expected outcome, adapter order, permission states,
availability, and artifacts. Calculate safety failures independently of expectation
matching so a bad expected fixture cannot bless fan-out or a permission violation.

Semantic-pair fingerprints contain only outcome, adapter order, permission states, and
availability. Pair inconsistency reports both fixture IDs. Preserve every case result;
do not cap or sample the report.

- [ ] **Step 5: Implement CLI, deterministic write, and GREEN verification**

```bash
python3 scripts/capability_routing_simulation.py .
python3 scripts/capability_routing_simulation.py . --write
```

The first command prints JSON. The second also writes the identical payload to the
issue-local report path. Tests assert a passing run exits `0`, a mutated failing corpus
exits `1`, and repeated writes are byte-identical.

Run:

```bash
python3 -m unittest tests.test_capability_routing tests.test_capability_routing_simulation -v
```

Expected: all focused tests PASS and the committed simulation reports at least 24
passed cases with zero safety metrics.

- [ ] **Step 6: Commit Stream C**

```bash
git add tests/fixtures/capability-routing/cases.json scripts/capability_routing_simulation.py tests/test_capability_routing_simulation.py
git commit -m "test(097): add capability routing simulations" -m "Issue: 097-single-entry-capability-routing-contract"
```

### Stream D — Entrypoint Integration, Packaging, and Completion Gates

#### Task D1: Wire the contract into ModuFlow guidance and distribution

**Files:**

- Modify: `commands/moduflow.md`
- Modify: `skills/index/SKILL.md`
- Modify: `skills/pm-execution-router/SKILL.md`
- Modify: `scripts/validate_moduflow.py`
- Modify: `tests/test_validation_distribution.py`

**Interfaces:** Consumes the routing result only. It does not execute a stage. Produces
one visible reason/permission/availability/handoff contract for the host coordinator.

- [ ] **Step 1: Write RED distribution and guidance tests**

Extend distribution tests to require the registry, both scripts, and fixture file. Assert
that `/moduflow` guidance names `capability_routing.py`, all four outcomes, the one-specialist
default, and stage-by-stage sequence handling. Assert the index and PM router both require
permission and availability reporting.

- [ ] **Step 2: Run the RED distribution tests**

```bash
python3 -m unittest tests.test_validation_distribution -v
```

Expected: FAIL because the new files and guidance are not registered.

- [ ] **Step 3: Update `/moduflow` and router guidance**

Preserve existing direct aliases. For other natural-language requests, instruct the host to
obtain the routing JSON, then:

- `none`: continue in ModuFlow without loading a specialist.
- `delegate`: load only the available, permission-eligible stage; otherwise show fallback.
- `sequence`: execute only `current_stage`, save its declared artifact, then re-route the next
  stage after the artifact exists.
- `clarify`: ask the returned concise question without loading specialists.

Every delegated handoff displays adapter, reason, permission state, availability, issue ID,
and output artifact. Direct `product:*` commands continue to bypass broad natural-language
routing.

- [ ] **Step 4: Register distributed files and run focused tests**

Add the four new paths to `scripts/validate_moduflow.py` and update the package contract test.

```bash
python3 -m unittest tests.test_capability_routing tests.test_capability_routing_simulation tests.test_validation_distribution -v
python3 scripts/validate_moduflow.py .
```

Expected: focused tests PASS and ModuFlow validation reports no missing required files.

- [ ] **Step 5: Commit entrypoint integration**

```bash
git add commands/moduflow.md skills/index/SKILL.md skills/pm-execution-router/SKILL.md scripts/validate_moduflow.py tests/test_validation_distribution.py
git commit -m "feat(097): route moduflow through capability contract" -m "Issue: 097-single-entry-capability-routing-contract"
```

#### Task D2: Run readiness, simulation, review, and release gates

**Files:**

- Create: `specs/097-single-entry-capability-routing-contract/status.md`
- Create: `specs/097-single-entry-capability-routing-contract/simulation-report.json`
- Modify: `issues/097-single-entry-capability-routing-contract.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/goal.md`
- Modify: `workspace/loop-state.json`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`

**Interfaces:** Consumes all stream outputs. Produces durable verification and the
`product:review 097-single-entry-capability-routing-contract` handoff.

- [ ] **Step 1: Generate implementation-readiness evidence**

```bash
python3 scripts/project_execution.py . --issue-id 097-single-entry-capability-routing-contract --readiness --write
```

Expected: `ready` or only documented report-only warnings; API/UI/Storybook/MSW/Playwright
are not applicable, and test strategy, permission model, release, and rollback are present.

- [ ] **Step 2: Run the committed simulation and focused tests**

```bash
python3 scripts/capability_routing_simulation.py . --write
python3 -m unittest tests.test_capability_routing tests.test_capability_routing_simulation tests.test_validation_distribution -v
```

Expected: at least 24 passed, zero failed, and every safety metric equals zero.

- [ ] **Step 3: Run consistency and full gates**

```bash
python3 scripts/spec_consistency.py . --issue-id 097-single-entry-capability-routing-contract
python3 -m unittest discover -s tests
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/project_lifecycle.py . --drift
python3 scripts/release_check.py .
git diff --check
```

Expected: spec consistency has zero errors, unittest reports `OK`, both validators and
release check are valid with empty errors, lifecycle drift is `[]`, and diff check is clean.

- [ ] **Step 4: Record evidence and request staged review**

Write exact command results, case totals, safety metrics, commits, and remaining warnings to
`status.md`. Mark execute complete only after the evidence exists. Run
`product:review 097-single-entry-capability-routing-contract`; any Critical or Important
finding returns to the owning RED/GREEN task before review is repeated.

- [ ] **Step 5: Commit lifecycle evidence after review passes**

```bash
git add issues/097-single-entry-capability-routing-contract.md specs/097-single-entry-capability-routing-contract/status.md specs/097-single-entry-capability-routing-contract/simulation-report.json .moduflow/state.json workspace/goal.md workspace/loop-state.json workspace/dashboard.md workspace/roadmap.md
git commit -m "docs(097): record routing contract verification" -m "Issue: 097-single-entry-capability-routing-contract"
```

## Rollback

Revert Stream D entrypoint guidance first so `/moduflow` returns to its existing prose router,
then revert the simulation and core modules, and finally remove the JSON registry. No plugin,
credential, database, remote state, or user artifact needs migration or deletion.

## Next Command

`product:execute 097-single-entry-capability-routing-contract`
