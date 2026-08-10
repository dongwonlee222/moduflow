import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "capability_routing.py"


def load_module(testcase):
    testcase.assertTrue(MODULE_PATH.exists(), "scripts/capability_routing.py must exist")
    spec = importlib.util.spec_from_file_location("capability_routing", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
                "exclusions": ["issue status"],
                "default_available": True,
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
        return self.routing.route_request(
            request,
            self.registry,
            issue_id="097-single-entry-capability-routing-contract",
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
        self.assertIn("098-speckit", result["fallback"])

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

    def test_cli_prints_read_only_routing_json(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "전환율을 분석해줘",
                str(ROOT),
                "--issue-id",
                "097-single-entry-capability-routing-contract",
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


if __name__ == "__main__":
    unittest.main()
