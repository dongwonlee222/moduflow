import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "capability_routing.py"
SPEC_KIT_MODULE_PATH = ROOT / "scripts" / "spec_kit_adapter.py"
SPEC_KIT_ISSUE_ID = "098-speckit-selective-validation-adapter"
HOST_AVAILABLE = {
    "data-analytics": True,
    "product-design": True,
    "superpowers": True,
    "documents": True,
    "spec-kit": False,
}
LIFECYCLE_ACTIONS = (
    "start", "begin", "pause", "stop", "resume", "continue", "finish", "complete", "close"
)
KOREAN_LIFECYCLE_ACTIONS = (
    "시작", "착수", "일시정지", "멈춰", "중지", "재개", "계속", "이어", "마무리", "끝내", "완료", "닫아", "종료"
)
LIFECYCLE_RESOURCES = ("status", "issue", "goal", "roadmap", "memory")
KOREAN_LIFECYCLE_RESOURCES = ("상태", "이슈", "목표", "로드맵", "메모리", "기억")
GIT_OPERATIONS = (
    "add", "stage", "stash", "fetch", "pull", "push", "merge", "rebase", "reset",
    "restore", "checkout", "switch", "branch", "tag", "cherry-pick", "revert", "clone", "commit",
)
KOREAN_GIT_OPERATIONS = (
    "깃 추가", "스테이징", "스태시", "페치", "풀", "푸시", "병합", "리베이스", "리셋",
    "복원", "체크아웃", "스위치", "브랜치", "태그", "체리픽", "리버트", "클론", "커밋",
)
KOREAN_INTRINSIC_GIT_OPERATIONS = {
    "스테이징", "스태시", "페치", "푸시", "병합", "리베이스", "리셋",
    "체크아웃", "체리픽", "리버트", "클론", "커밋",
}
ORDINARY_VALIDATION_REQUESTS = (
    ("Spec Kit clarify which acceptance criteria to add", "clarify"),
    ("Spec Kit analyze the stages in the plan", "analyze"),
    ("Spec Kit checklist where to start validation", "checklist"),
    ("Spec Kit converge candidates to restore requirement coverage", "converge"),
    ("스펙킷으로 분석해서 요구사항을 계속 명확히 해줘", "analyze"),
    ("스펙킷으로 체크리스트에 태그 요구사항을 추가해줘", "checklist"),
    ("Spec Kit clarify which changes to add to the requirements", "clarify"),
    ("Spec Kit analyze which stages changed in the spec files", "analyze"),
)
ADJACENT_OWNERSHIP_REQUESTS = (
    "Spec Kit analyze then add files to the index",
    "Spec Kit checklist then stage changed files",
    "Spec Kit clarify then restore files from the working tree",
    "Spec Kit analyze then start work on the issue",
    "Spec Kit checklist because the issue should be started",
    "스펙킷으로 분석한 뒤 이슈를 다시 시작해줘",
    "스펙킷으로 체크리스트 만든 뒤 이슈를 잠시 멈춰줘",
    "Spec Kit converge then switch to the current branch",
    "Spec Kit analyze then tag the modified commit",
    "Spec Kit checklist then branch the repo",
    "Spec Kit clarify then add tracked hunks to the index",
    "Spec Kit analyze then restore staged changes in the working tree",
    "Spec Kit checklist then stage untracked files",
    "Spec Kit checklist then continue work on the roadmap",
    "Spec Kit clarify because the project must be paused",
    "Spec Kit analyze because this work item can be completed",
    "스펙킷으로 분석한 뒤 프로젝트를 이제 재개해줘",
    "스펙킷으로 체크리스트 만든 뒤 로드맵을 바로 완료해줘",
    "스펙킷으로 분석한 뒤 이슈를 계속 이어줘",
)
METAMORPHIC_OWNERSHIP_REQUESTS = (
    "Spec Kit checklist then stage the recently changed files",
    "Spec Kit analyze then add all changed files to the index",
    "Spec Kit clarify then restore selected files from the working tree",
    "Spec Kit checklist because the issue should really be paused",
    "Spec Kit analyze then start working on the issue",
    "스펙킷으로 분석한 뒤 이슈를 잠깐 다시 시작해줘",
    "스펙킷으로 체크리스트 만든 뒤 프로젝트를 먼저 천천히 완료해줘",
    "Spec Kit checklist then stage the very recently modified files",
    "Spec Kit clarify then add every carefully reviewed changed hunk to the index",
    "Spec Kit analyze then restore only those selected archived files from the working tree",
    "Spec Kit checklist because the roadmap should eventually be carefully resumed",
    "Spec Kit analyze then carefully start seriously working on the current issue",
    "스펙킷으로 분석한 뒤 이슈를 아주 잠깐 먼저 멈춰줘",
    "스펙킷으로 체크리스트 만든 뒤 로드맵을 먼저 천천히 다시 재개해줘",
)
DOMAIN_TARGET_POSITIVE_REQUESTS = (
    ("Spec Kit clarify how to add changes to requirements", "clarify"),
    ("Spec Kit analyze which files to add to spec inputs", "analyze"),
    ("Spec Kit converge where to restore changes to requirement coverage", "converge"),
    ("Spec Kit checklist where to start validation for this issue", "checklist"),
    ("Spec Kit analyze which requirements to continue in the issue spec", "analyze"),
    ("스펙킷으로 스테이징된 요구사항 파일을 분석해줘", "analyze"),
)


def semantic_role_requests():
    negatives = [
        "Spec Kit checklist then stage, please, changed files",
        "Spec Kit checklist because the issue should, really, be paused",
        "스펙킷으로 분석한 뒤 이슈를, 잠깐, 먼저 멈춰줘",
        "Spec Kit analyze then stage files while preserving requirements",
        "Spec Kit clarify then add tracked files and update requirements",
    ]
    positives = [
        ("Spec Kit checklist which issue to start validation with", "checklist"),
        ("Spec Kit checklist issue to begin validation with", "checklist"),
        ("스펙킷으로 이슈별 시작 검증 기준을 체크리스트해줘", "checklist"),
        ("Spec Kit analyze committed requirements", "analyze"),
    ]
    for punctuation in (", {modifier},", " ({modifier}) ", " -- {modifier} -- "):
        for modifier in ("politely", "very carefully", "without any unnecessary delay"):
            insertion = punctuation.format(modifier=modifier)
            negatives.append(f"Spec Kit checklist then stage{insertion}changed files")
            negatives.append(
                f"Spec Kit checklist because the issue should{insertion}be paused"
            )
            positives.append(
                (f"Spec Kit checklist which issue to start{insertion}validation with", "checklist")
            )
    for modifier in (", 잠깐, 먼저 ", " (조심스럽게) 아주 잠깐 ", " 우선 천천히 "):
        negatives.append(f"스펙킷으로 분석한 뒤 이슈를{modifier}멈춰줘")
        positives.append(
            (f"스펙킷으로 이슈별 시작{modifier}검증 기준을 체크리스트해줘", "checklist")
        )
    return tuple(negatives), tuple(positives)


def load_module(testcase):
    testcase.assertTrue(MODULE_PATH.exists(), "scripts/capability_routing.py must exist")
    spec = importlib.util.spec_from_file_location("capability_routing", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_spec_kit_module(testcase):
    testcase.assertTrue(
        SPEC_KIT_MODULE_PATH.exists(), "scripts/spec_kit_adapter.py must exist"
    )
    spec = importlib.util.spec_from_file_location(
        "spec_kit_adapter_for_routing", SPEC_KIT_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_spec_kit_opt_in(project_root):
    config = project_root / ".moduflow" / "capabilities.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps(
            {
                "schema": "moduflow.capabilities.v1",
                "capabilities": {
                    "spec-kit": {
                        "enabled": True,
                        "source_version": "0.16.1",
                        "source_sha": "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5",
                        "functions": ["clarify", "analyze", "checklist", "converge"],
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    canonical = {
        Path("issues") / f"{SPEC_KIT_ISSUE_ID}.md": "# Canonical issue\n",
        Path("specs") / SPEC_KIT_ISSUE_ID / "spec.md": "# Canonical spec\n",
        Path("specs") / SPEC_KIT_ISSUE_ID / "plan.md": "# Canonical plan\n",
        Path("specs") / SPEC_KIT_ISSUE_ID / "tasks.md": "# Canonical tasks\n",
        Path("workspace") / "constitution.md": "# Canonical constitution\n",
    }
    for relative, content in canonical.items():
        path = project_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def valid_registry(root):
    adapter = root / "adapters" / "data-analytics.yaml"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_text("id: data-analytics\n", encoding="utf-8")
    return {
        "schema": "moduflow.capability-registry.v1",
        "lifecycle_triggers": ["issue status"],
        "sequence_markers": ["then"],
        "external_write_triggers": ["publish to posthog"],
        "capabilities": [
            {
                "id": "data-analytics",
                "adapter_path": "adapters/data-analytics.yaml",
                "purpose": "product and business data analysis",
                "triggers": ["analytics", "분석"],
                "explicit_triggers": ["data analytics", "데이터 분석"],
                "exclusions": ["issue status"],
                "default_available": False,
                "permission": "read",
                "output_artifact": "specs/{issue_id}/analysis.md",
                "setup_recommendation": "Enable Data Analytics in the current host.",
            }
        ],
    }


class CapabilityRegistryTests(unittest.TestCase):
    def test_real_registry_is_valid_and_spec_kit_is_inactive(self):
        capability_routing = load_module(self)

        registry = capability_routing.load_registry(ROOT)
        by_id = {item["id"]: item for item in registry["capabilities"]}

        self.assertEqual(len(by_id), 5)
        self.assertFalse(by_id["spec-kit"]["default_available"])
        self.assertEqual(
            set(by_id),
            {"data-analytics", "product-design", "superpowers", "documents", "spec-kit"},
        )

    def test_duplicate_ids_fail_closed(self):
        capability_routing = load_module(self)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = valid_registry(root)
            payload["capabilities"].append(dict(payload["capabilities"][0]))

            with self.assertRaisesRegex(capability_routing.RegistryError, "duplicate"):
                capability_routing.validate_registry(payload, root)

    def test_missing_adapter_file_fails_closed(self):
        capability_routing = load_module(self)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = valid_registry(root)
            payload["capabilities"][0]["adapter_path"] = "adapters/missing.yaml"

            with self.assertRaisesRegex(capability_routing.RegistryError, "adapter_path"):
                capability_routing.validate_registry(payload, root)

    def test_unknown_permission_fails_closed(self):
        capability_routing = load_module(self)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = valid_registry(root)
            payload["capabilities"][0]["permission"] = "admin"

            with self.assertRaisesRegex(capability_routing.RegistryError, "permission"):
                capability_routing.validate_registry(payload, root)

    def test_empty_triggers_fail_closed(self):
        capability_routing = load_module(self)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = valid_registry(root)
            payload["capabilities"][0]["triggers"] = []

            with self.assertRaisesRegex(capability_routing.RegistryError, "triggers"):
                capability_routing.validate_registry(payload, root)

    def test_invalid_json_is_reported_as_registry_error(self):
        capability_routing = load_module(self)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "adapters").mkdir()
            (root / "adapters" / "capability-routing.json").write_text(
                "{not-json", encoding="utf-8"
            )

            with self.assertRaisesRegex(capability_routing.RegistryError, "registry read failed"):
                capability_routing.load_registry(root)


class CapabilityRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routing = load_module(cls)
        cls.registry = cls.routing.load_registry(ROOT)

    def route(self, request, **kwargs):
        self.assertTrue(
            hasattr(self.routing, "route_request"),
            "route_request must implement the routing contract",
        )
        availability = kwargs.pop("availability", HOST_AVAILABLE)
        return self.routing.route_request(
            request,
            self.registry,
            issue_id="097-single-entry-capability-routing-contract",
            target_root=ROOT,
            availability=availability,
            **kwargs,
        )

    def test_lifecycle_request_routes_to_none(self):
        result = self.route("현재 이슈 상태 보여줘")

        self.assertEqual(result["outcome"], "none")
        self.assertEqual(result["stages"], [])
        self.assertIsNone(result["current_stage"])

    def test_direct_product_command_routes_to_none(self):
        result = self.route("product:status")

        self.assertEqual(result["outcome"], "none")

    def test_lifecycle_intent_beats_explicit_capability_names(self):
        requests = (
            "데이터 분석 프로젝트 현재 상태 보여줘",
            "제품 디자인 다음 단계 알려줘",
            "superpowers 이슈 상태 보여줘",
        )
        for request in requests:
            with self.subTest(request=request):
                result = self.route(request)
                self.assertEqual(result["outcome"], "none")
                self.assertEqual(result["stages"], [])

    def test_bounded_analytics_selects_exactly_one_adapter(self):
        result = self.route("전환율 하락 원인을 분석해줘")

        self.assertEqual(result["outcome"], "delegate")
        self.assertEqual(
            [stage["adapter_id"] for stage in result["stages"]],
            ["data-analytics"],
        )
        self.assertEqual(result["stages"][0]["permission"], "read")
        self.assertEqual(result["stages"][0]["permission_state"], "allowed")
        self.assertEqual(result["stages"][0]["availability"], "available")
        self.assertIn(result["issue_id"], result["stages"][0]["output_artifact"])

    def test_one_domain_with_repeated_triggers_stays_one_delegate(self):
        result = self.route("데이터 KPI 지표를 분석해줘")

        self.assertEqual(result["outcome"], "delegate")
        self.assertEqual(len(result["stages"]), 1)
        self.assertEqual(result["stages"][0]["adapter_id"], "data-analytics")

    def test_explicit_adapter_id_selects_that_adapter(self):
        result = self.route("data-analytics로 확인해줘")

        self.assertEqual(result["outcome"], "delegate")
        self.assertEqual(result["stages"][0]["adapter_id"], "data-analytics")
        self.assertEqual(result["stages"][0]["reason_code"], "explicit_adapter")

    def test_exclusion_beats_generic_trigger(self):
        result = self.route("API 구현 계획을 정리해줘")

        self.assertEqual(result["outcome"], "none")

    def test_overlap_without_order_asks_one_question(self):
        result = self.route("데이터 분석과 온보딩 디자인 개선안 부탁해")

        self.assertEqual(result["outcome"], "clarify")
        self.assertEqual(result["stages"], [])
        self.assertEqual(result["clarification"].count("?"), 1)

    def test_explicit_multistage_request_is_ordered_and_gated(self):
        result = self.route("전환율을 분석한 후 대시보드를 구현해줘")

        self.assertEqual(result["outcome"], "sequence")
        self.assertEqual(
            [stage["adapter_id"] for stage in result["stages"]],
            ["data-analytics", "superpowers"],
        )
        self.assertEqual(result["current_stage"], 0)
        self.assertEqual(
            result["stages"][0]["gate_after"],
            result["stages"][0]["output_artifact"],
        )
        self.assertIsNone(result["stages"][1]["gate_after"])

    def test_sequence_follows_request_order_not_registry_order(self):
        result = self.route("화면을 디자인하고 그다음 구현해줘")

        self.assertEqual(result["outcome"], "sequence")
        self.assertEqual(
            [stage["adapter_id"] for stage in result["stages"]],
            ["product-design", "superpowers"],
        )

    def test_unavailable_capability_reports_fallback_without_current_stage(self):
        result = self.route(
            "전환율을 분석해줘",
            availability={"data-analytics": False},
        )

        self.assertEqual(result["outcome"], "delegate")
        self.assertEqual(result["stages"][0]["availability"], "unavailable")
        self.assertIsNone(result["current_stage"])
        self.assertIn("Data Analytics", result["fallback"])

    def test_spec_kit_is_truthfully_unavailable_by_default(self):
        result = self.route("스펙킷으로 스펙을 검증해줘")

        self.assertEqual(result["outcome"], "delegate")
        self.assertEqual(result["stages"][0]["adapter_id"], "spec-kit")
        self.assertEqual(result["stages"][0]["availability"], "unavailable")
        self.assertIn("Spec Kit", result["fallback"])
        self.assertIn("opt in", result["fallback"])

    def test_explicit_spec_kit_intent_beats_generic_lifecycle_words(self):
        result = self.route("스펙킷으로 스펙을 검사해줘")

        self.assertEqual(result["outcome"], "delegate")
        self.assertEqual(result["stages"][0]["adapter_id"], "spec-kit")
        self.assertEqual(result["stages"][0]["reason_code"], "explicit_adapter")

    def test_available_spec_kit_routes_one_stage_then_adapter_selects_one_template(self):
        spec_kit = load_spec_kit_module(self)
        request = "스펙킷으로 요구사항 체크리스트 만들어줘"
        route = self.route(request, availability={"spec-kit": True})

        self.assertEqual(route["outcome"], "delegate")
        self.assertEqual([stage["adapter_id"] for stage in route["stages"]], ["spec-kit"])
        self.assertEqual(route["stages"][0]["permission"], "read")
        self.assertEqual(route["stages"][0]["permission_state"], "allowed")
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_spec_kit_opt_in(project)
            handoff = spec_kit.build_handoff(
                ROOT, project, SPEC_KIT_ISSUE_ID, route["request"], host_available=True
            )

            self.assertEqual(handoff["outcome"], "ready")
            self.assertEqual(handoff["function"], "checklist")
            self.assertEqual(
                handoff["source"]["template"],
                "vendor/spec-kit/0.16.1/commands/checklist.md",
            )
            self.assertFalse(
                (project / "specs" / SPEC_KIT_ISSUE_ID / "validation.md").exists()
            )

    def test_available_spec_kit_functions_each_route_only_spec_kit_with_all_capabilities(self):
        spec_kit = load_spec_kit_module(self)
        requests = {
            "clarify": "스펙킷으로 요구사항 명확화해줘",
            "analyze": "Spec Kit analyze the requirements",
            "checklist": "스펙킷으로 요구사항 체크리스트 만들어줘",
            "converge": "Spec Kit converge the remaining work",
        }

        for expected_function, request in requests.items():
            with self.subTest(function=expected_function):
                route = self.route(
                    request, availability={capability: True for capability in HOST_AVAILABLE}
                )

                self.assertEqual(route["outcome"], "delegate")
                self.assertEqual(
                    [stage["adapter_id"] for stage in route["stages"]],
                    ["spec-kit"],
                )
                self.assertEqual(spec_kit.select_function(route["request"]), expected_function)

    def test_ordinary_validation_words_route_one_spec_kit_stage(self):
        spec_kit = load_spec_kit_module(self)

        for request, expected_function in ORDINARY_VALIDATION_REQUESTS:
            with self.subTest(request=request):
                route = self.route(
                    request,
                    availability={capability: True for capability in HOST_AVAILABLE},
                )
                self.assertEqual(route["outcome"], "delegate")
                self.assertEqual(
                    [stage["adapter_id"] for stage in route["stages"]],
                    ["spec-kit"],
                )
                self.assertEqual(spec_kit.select_function(request), expected_function)

    def test_intrinsic_korean_git_action_crosses_router_but_not_adapter_boundary(self):
        spec_kit = load_spec_kit_module(self)
        request = "스펙킷으로 분석한 뒤 스테이징해줘"

        route = self.route(
            request,
            availability={capability: True for capability in HOST_AVAILABLE},
        )
        self.assertEqual(route["outcome"], "delegate")
        self.assertEqual(
            [stage["adapter_id"] for stage in route["stages"]], ["spec-kit"]
        )
        self.assertIsNone(spec_kit.select_function(request))
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_spec_kit_opt_in(project)
            handoff = spec_kit.build_handoff(
                ROOT, project, SPEC_KIT_ISSUE_ID, request, host_available=True
            )
            self.assertEqual(handoff["outcome"], "unsupported")
            self.assertIsNone(handoff["source"]["template"])
            self.assertFalse(
                (project / "specs" / SPEC_KIT_ISSUE_ID / "validation.md").exists()
            )

    def test_adjacent_ownership_phrase_families_cross_router_not_adapter(self):
        spec_kit = load_spec_kit_module(self)
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_spec_kit_opt_in(project)
            for request in ADJACENT_OWNERSHIP_REQUESTS:
                with self.subTest(request=request):
                    route = self.route(
                        request,
                        availability={capability: True for capability in HOST_AVAILABLE},
                    )
                    self.assertEqual(route["outcome"], "delegate")
                    self.assertEqual(
                        [stage["adapter_id"] for stage in route["stages"]],
                        ["spec-kit"],
                    )
                    self.assertIsNone(spec_kit.select_function(request))
                    handoff = spec_kit.build_handoff(
                        ROOT, project, SPEC_KIT_ISSUE_ID, request, host_available=True
                    )
                    self.assertEqual(handoff["outcome"], "unsupported")
                    self.assertIsNone(handoff["source"]["template"])
            self.assertFalse(
                (project / "specs" / SPEC_KIT_ISSUE_ID / "validation.md").exists()
            )

    def test_clause_token_ownership_and_domain_overrides_cross_real_router(self):
        spec_kit = load_spec_kit_module(self)
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_spec_kit_opt_in(project)
            for request in METAMORPHIC_OWNERSHIP_REQUESTS:
                with self.subTest(kind="ownership", request=request):
                    route = self.route(
                        request,
                        availability={capability: True for capability in HOST_AVAILABLE},
                    )
                    self.assertEqual(route["outcome"], "delegate")
                    self.assertEqual(
                        [stage["adapter_id"] for stage in route["stages"]], ["spec-kit"]
                    )
                    self.assertIsNone(spec_kit.select_function(request))
                    handoff = spec_kit.build_handoff(
                        ROOT, project, SPEC_KIT_ISSUE_ID, request, host_available=True
                    )
                    self.assertEqual(handoff["outcome"], "unsupported")
            for request, function in DOMAIN_TARGET_POSITIVE_REQUESTS:
                with self.subTest(kind="domain", request=request):
                    route = self.route(
                        request,
                        availability={capability: True for capability in HOST_AVAILABLE},
                    )
                    self.assertEqual(route["outcome"], "delegate")
                    self.assertEqual(
                        [stage["adapter_id"] for stage in route["stages"]], ["spec-kit"]
                    )
                    self.assertEqual(spec_kit.select_function(request), function)
                    handoff = spec_kit.build_handoff(
                        ROOT, project, SPEC_KIT_ISSUE_ID, request, host_available=True
                    )
                    self.assertEqual(handoff["outcome"], "ready")
                    self.assertEqual(handoff["function"], function)
            self.assertFalse(
                (project / "specs" / SPEC_KIT_ISSUE_ID / "validation.md").exists()
            )

    def test_strong_clause_role_requests_cross_real_router_and_adapter(self):
        spec_kit = load_spec_kit_module(self)
        negatives, positives = semantic_role_requests()
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_spec_kit_opt_in(project)
            for request in negatives:
                with self.subTest(kind="ownership", request=request):
                    route = self.route(
                        request,
                        availability={capability: True for capability in HOST_AVAILABLE},
                    )
                    self.assertEqual(route["outcome"], "delegate")
                    self.assertEqual(
                        [stage["adapter_id"] for stage in route["stages"]], ["spec-kit"]
                    )
                    self.assertIsNone(spec_kit.select_function(request))
                    handoff = spec_kit.build_handoff(
                        ROOT, project, SPEC_KIT_ISSUE_ID, request, host_available=True
                    )
                    self.assertEqual(handoff["outcome"], "unsupported")
            for request, function in positives:
                with self.subTest(kind="advisory", request=request):
                    route = self.route(
                        request,
                        availability={capability: True for capability in HOST_AVAILABLE},
                    )
                    self.assertEqual(route["outcome"], "delegate")
                    self.assertEqual(
                        [stage["adapter_id"] for stage in route["stages"]], ["spec-kit"]
                    )
                    self.assertEqual(spec_kit.select_function(request), function)
                    handoff = spec_kit.build_handoff(
                        ROOT, project, SPEC_KIT_ISSUE_ID, request, host_available=True
                    )
                    self.assertEqual(handoff["outcome"], "ready")
                    self.assertEqual(handoff["function"], function)
            self.assertFalse(
                (project / "specs" / SPEC_KIT_ISSUE_ID / "validation.md").exists()
            )

    def test_explicit_spec_kit_beats_every_general_capability_trigger_for_each_function(self):
        spec_kit = load_spec_kit_module(self)
        capability_subjects = {
            "data-analytics": "KPI requirements",
            "product-design": "UI requirements",
            "superpowers": "API requirements",
            "documents": "PPTX requirements",
        }
        function_requests = {
            "clarify": "Spec Kit clarify the {subject}",
            "analyze": "Spec Kit analyze the {subject}",
            "checklist": "Spec Kit checklist for {subject}",
            "converge": "Spec Kit converge the {subject}",
        }

        for capability, subject in capability_subjects.items():
            for expected_function, request_template in function_requests.items():
                with self.subTest(capability=capability, function=expected_function):
                    request = request_template.format(subject=subject)
                    route = self.route(
                        request,
                        availability={key: True for key in HOST_AVAILABLE},
                    )

                    self.assertEqual(route["outcome"], "delegate")
                    self.assertEqual(
                        [stage["adapter_id"] for stage in route["stages"]],
                        ["spec-kit"],
                    )
                    self.assertEqual(
                        spec_kit.select_function(route["request"]), expected_function
                    )

    def test_ordinary_general_capability_requests_keep_their_native_routes(self):
        requests = {
            "KPI를 분석해줘": "data-analytics",
            "UI 화면을 디자인해줘": "product-design",
            "API를 구현해줘": "superpowers",
            "PPTX 발표자료를 만들어줘": "documents",
        }

        for request, expected_adapter in requests.items():
            with self.subTest(adapter=expected_adapter):
                route = self.route(request)
                self.assertEqual(route["outcome"], "delegate")
                self.assertEqual(
                    [stage["adapter_id"] for stage in route["stages"]],
                    [expected_adapter],
                )

    def test_ownership_language_overrides_spec_kit_function_selection(self):
        spec_kit = load_spec_kit_module(self)
        requests = (
            "스펙킷으로 코드를 분석해줘",
            "Spec Kit analyze the Git changes",
            "스펙킷으로 PR 리뷰를 분석해줘",
        )

        for request in requests:
            with self.subTest(request=request):
                route = self.route(
                    request, availability={capability: True for capability in HOST_AVAILABLE}
                )

                self.assertEqual(route["outcome"], "delegate")
                self.assertEqual(
                    [stage["adapter_id"] for stage in route["stages"]],
                    ["spec-kit"],
                )
                self.assertIsNone(spec_kit.select_function(route["request"]))

    def test_complete_lifecycle_and_git_mutations_win_before_spec_kit_selection(self):
        spec_kit = load_spec_kit_module(self)
        requests = (
            "Spec Kit analyze this then mark issue done",
            "Spec Kit checklist then update roadmap status",
            "Spec Kit clarify then update the goal and memory",
            "Spec Kit analyze then merge, push, pull, and rebase the branch",
            "Spec Kit converge then tag and cherry-pick the release branch",
            "Spec Kit checklist then reset and checkout the branch",
            "스펙킷으로 분석한 다음 이슈 상태를 완료로 변경해줘",
            "스펙킷으로 체크리스트 만든 뒤 로드맵과 목표를 수정해줘",
            "스펙킷으로 수렴한 뒤 브랜치를 병합하고 푸시해줘",
            "스펙킷으로 명확화한 다음 리베이스하고 태그해줘",
        )
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_spec_kit_opt_in(project)
            for request in requests:
                with self.subTest(request=request):
                    route = self.route(
                        request,
                        availability={capability: True for capability in HOST_AVAILABLE},
                    )
                    self.assertIn(route["outcome"], {"none", "delegate"})
                    self.assertIsNone(spec_kit.select_function(request))
                    handoff = spec_kit.build_handoff(
                        ROOT,
                        project,
                        SPEC_KIT_ISSUE_ID,
                        request,
                        host_available=True,
                    )
                    self.assertEqual(handoff["outcome"], "unsupported")
                    self.assertIsNone(handoff["source"]["template"])
            self.assertFalse(
                (project / "specs" / SPEC_KIT_ISSUE_ID / "validation.md").exists()
            )

    def test_every_canonical_ownership_alias_crosses_router_but_not_adapter_boundary(self):
        spec_kit = load_spec_kit_module(self)
        self.assertEqual(set(spec_kit.LIFECYCLE_ACTION_ALIASES), set(LIFECYCLE_ACTIONS))
        self.assertEqual(
            set(spec_kit.KOREAN_LIFECYCLE_ACTION_ALIASES),
            set(KOREAN_LIFECYCLE_ACTIONS),
        )
        self.assertEqual(set(spec_kit.GIT_OPERATION_ALIASES), set(GIT_OPERATIONS))
        self.assertEqual(
            set(spec_kit.KOREAN_GIT_OPERATION_ALIASES), set(KOREAN_GIT_OPERATIONS)
        )
        requests = [
            *(f"Spec Kit analyze then {alias} the issue" for alias in LIFECYCLE_ACTIONS),
            *(f"Spec Kit checklist then update {resource}" for resource in LIFECYCLE_RESOURCES),
            *(f"스펙킷으로 분석한 다음 이슈를 {alias}" for alias in KOREAN_LIFECYCLE_ACTIONS),
            *(
                f"스펙킷으로 체크리스트 만든 뒤 {resource}를 수정해줘"
                for resource in KOREAN_LIFECYCLE_RESOURCES
            ),
            *(f"Spec Kit converge then {operation} repository changes" for operation in GIT_OPERATIONS),
            *(
                (
                    f"스펙킷으로 분석한 뒤 {operation}해줘"
                    if operation in KOREAN_INTRINSIC_GIT_OPERATIONS
                    else f"스펙킷으로 명확화한 뒤 저장소에 {operation}해줘"
                )
                for operation in KOREAN_GIT_OPERATIONS
            ),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_spec_kit_opt_in(project)
            for request in requests:
                with self.subTest(request=request):
                    route = self.route(
                        request,
                        availability={capability: True for capability in HOST_AVAILABLE},
                    )
                    self.assertIn(route["outcome"], {"none", "delegate"})
                    self.assertIsNone(spec_kit.select_function(route["request"]))
                    handoff = spec_kit.build_handoff(
                        ROOT, project, SPEC_KIT_ISSUE_ID, request, True
                    )
                    self.assertEqual(handoff["outcome"], "unsupported")
                    self.assertIsNone(handoff["source"]["template"])
            self.assertFalse(
                (project / "specs" / SPEC_KIT_ISSUE_ID / "validation.md").exists()
            )

    def test_implementation_language_cannot_select_a_spec_kit_function(self):
        spec_kit = load_spec_kit_module(self)
        requests = (
            "스펙킷으로 구현해줘",
            "스펙킷으로 코드를 작성해줘",
            "스펙킷으로 Git 작업해줘",
            "스펙킷으로 commit 해줘",
            "스펙킷으로 review 해줘",
            "스펙킷으로 PR 만들어줘",
            "스펙킷으로 release 해줘",
            "스펙킷으로 deployment 해줘",
        )
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_spec_kit_opt_in(project)
            for request in requests:
                with self.subTest(request=request):
                    route = self.route(
                        request, availability={**HOST_AVAILABLE, "spec-kit": True}
                    )

                    self.assertEqual(route["outcome"], "delegate")
                    self.assertEqual(
                        [stage["adapter_id"] for stage in route["stages"]],
                        ["spec-kit"],
                    )
                    self.assertIsNone(spec_kit.select_function(route["request"]))
                    handoff = spec_kit.build_handoff(
                        ROOT,
                        project,
                        SPEC_KIT_ISSUE_ID,
                        route["request"],
                        host_available=True,
                    )

                    self.assertEqual(handoff["outcome"], "unsupported")
                    self.assertIsNotNone(handoff["fallback"])
            self.assertFalse(
                (project / "specs" / SPEC_KIT_ISSUE_ID / "validation.md").exists()
            )

    def test_product_commands_stay_local_and_ordinary_implementation_uses_superpowers(self):
        for request in ("product:spec", "product:review", "product:pr", "product:release"):
            with self.subTest(request=request):
                result = self.route(request)
                self.assertEqual(result["outcome"], "none")
                self.assertEqual(result["stages"], [])

        implementation = self.route("API를 구현하고 테스트해줘")
        self.assertEqual(implementation["outcome"], "delegate")
        self.assertEqual(
            [stage["adapter_id"] for stage in implementation["stages"]],
            ["superpowers"],
        )

    def test_availability_defaults_fail_closed_without_host_confirmation(self):
        result = self.route("전환율을 분석해줘", availability={})

        self.assertEqual(result["stages"][0]["availability"], "unavailable")
        self.assertIsNone(result["current_stage"])

    def test_unknown_or_non_boolean_availability_is_rejected(self):
        with self.assertRaisesRegex(self.routing.RegistryError, "unknown capability"):
            self.route("전환율을 분석해줘", availability={"ghost": True})
        with self.assertRaisesRegex(self.routing.RegistryError, "boolean"):
            self.route("전환율을 분석해줘", availability={"data-analytics": "yes"})

    def test_external_write_requires_explicit_approval(self):
        result = self.route("분석 결과를 posthog에 반영해줘")

        self.assertEqual(result["stages"][0]["permission"], "write-external")
        self.assertEqual(
            result["stages"][0]["permission_state"],
            "requires_approval",
        )
        self.assertIsNone(result["current_stage"])

    def test_external_write_is_eligible_after_explicit_approval(self):
        result = self.route(
            "Analyze conversion and publish to PostHog",
            approved_permissions={"write-external"},
        )

        self.assertEqual(result["stages"][0]["permission"], "write-external")
        self.assertEqual(result["stages"][0]["permission_state"], "allowed")
        self.assertEqual(result["current_stage"], 0)

    def test_case_and_whitespace_are_normalized(self):
        result = self.route("  ANALYZE   conversion  ")

        self.assertEqual(result["outcome"], "delegate")
        self.assertEqual(result["stages"][0]["adapter_id"], "data-analytics")

    def test_sequence_advances_only_after_predecessor_artifact(self):
        initial = self.route("전환율을 분석한 후 대시보드를 구현해줘")
        first_artifact = initial["stages"][0]["output_artifact"]
        advanced = self.route(
            "전환율을 분석한 후 대시보드를 구현해줘",
            completed_artifacts={first_artifact},
        )
        completed = self.route(
            "전환율을 분석한 후 대시보드를 구현해줘",
            completed_artifacts={stage["output_artifact"] for stage in initial["stages"]},
        )

        self.assertEqual(initial["sequence_state"], "ready")
        self.assertEqual(initial["current_stage"], 0)
        self.assertEqual(advanced["sequence_state"], "ready")
        self.assertEqual(advanced["current_stage"], 1)
        self.assertEqual(completed["sequence_state"], "complete")
        self.assertIsNone(completed["current_stage"])

    def test_sequence_reports_blocked_when_next_stage_is_not_eligible(self):
        initial = self.route("전환율을 분석한 후 대시보드를 구현해줘")
        result = self.route(
            "전환율을 분석한 후 대시보드를 구현해줘",
            availability={**HOST_AVAILABLE, "superpowers": False},
            completed_artifacts={initial["stages"][0]["output_artifact"]},
        )

        self.assertEqual(result["sequence_state"], "blocked")
        self.assertIsNone(result["current_stage"])

    def test_issue_id_cannot_escape_target_specs_directory(self):
        for issue_id in ("../../outside", "bad/name", ".."):
            with self.subTest(issue_id=issue_id):
                with self.assertRaisesRegex(self.routing.RegistryError, "issue_id"):
                    self.routing.route_request(
                        "전환율을 분석해줘",
                        self.registry,
                        issue_id=issue_id,
                        target_root=ROOT,
                        availability=HOST_AVAILABLE,
                    )

    def test_output_template_cannot_escape_target_specs_directory(self):
        registry = json.loads(json.dumps(self.registry))
        registry["capabilities"][0]["output_artifact"] = "../outside/{issue_id}.md"

        with self.assertRaisesRegex(self.routing.RegistryError, "output_artifact"):
            self.routing.route_request(
                "전환율을 분석해줘",
                registry,
                issue_id="001-conversion",
                target_root=ROOT,
                availability=HOST_AVAILABLE,
            )

    def test_cli_prints_read_only_routing_json(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "전환율을 분석해줘",
                str(ROOT),
                "--issue-id",
                "097-single-entry-capability-routing-contract",
                "--available",
                "data-analytics",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(completed.stdout.strip(), "CLI must print routing JSON")
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["outcome"], "delegate")
        self.assertEqual(payload["stages"][0]["adapter_id"], "data-analytics")

    def test_cli_uses_bundled_registry_for_lightweight_target_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "전환율을 분석해줘",
                    str(target),
                    "--issue-id",
                    "001-conversion",
                    "--available",
                    "data-analytics",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["stages"][0]["output_artifact"], "specs/001-conversion/analysis.md")

    def test_cli_reports_structured_errors_without_traceback(self):
        completed = subprocess.run(
            [sys.executable, str(MODULE_PATH), "분석해줘", str(ROOT), "--available", "ghost"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertNotIn("Traceback", completed.stderr)
        payload = json.loads(completed.stderr)
        self.assertEqual(payload["schema"], "moduflow.capability-routing-error.v1")


if __name__ == "__main__":
    unittest.main()
