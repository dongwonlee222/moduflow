import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "spec_kit_adapter.py"
ISSUE_ID = "098-speckit-selective-validation-adapter"
APPROVED_VERSION = "0.16.1"
APPROVED_SHA = "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"


def load_module(testcase):
    testcase.assertTrue(MODULE_PATH.exists(), "scripts/spec_kit_adapter.py must exist")
    spec = importlib.util.spec_from_file_location("spec_kit_adapter", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def opted_in_config(functions=("clarify", "analyze", "checklist", "converge")):
    return {
        "schema": "moduflow.capabilities.v1",
        "capabilities": {
            "spec-kit": {
                "enabled": True,
                "source_version": APPROVED_VERSION,
                "source_sha": APPROVED_SHA,
                "functions": list(functions),
            }
        },
    }


class SpecKitConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ska = load_module(cls)

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_config(self, payload):
        path = self.project / ".moduflow" / "capabilities.json"
        path.parent.mkdir()
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_missing_config_is_disabled_without_creating_a_file(self):
        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertEqual(result["outcome"], "disabled")
        self.assertFalse((self.project / ".moduflow" / "capabilities.json").exists())

    def test_explicit_korean_request_selects_one_function(self):
        self.assertEqual(
            self.ska.select_function("스펙킷으로 요구사항 체크리스트 만들어줘"),
            "checklist",
        )
        self.assertEqual(
            self.ska.select_function("스펙킷으로 남은 작업을 수렴해줘"), "converge"
        )

    def test_multiple_functions_do_not_fan_out(self):
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "ambiguous_function"):
            self.ska.select_function("스펙킷으로 분석하고 체크리스트도 만들어줘")

    def test_valid_opt_in_with_verified_assets_returns_one_ready_template(self):
        self.write_config(opted_in_config(("analyze",)))

        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertEqual(result["outcome"], "ready")
        self.assertEqual(result["function"], "analyze")
        self.assertEqual(
            result["source"]["template"],
            "vendor/spec-kit/0.16.1/commands/analyze.md",
        )
        self.assertEqual(
            result["source"]["template_sha256"],
            "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
        )
        self.assertEqual(result["permission"], "read")
        self.assertEqual(
            result["inputs"],
            ["spec.md", "plan.md", "tasks.md", "constitution.md"],
        )
        self.assertIsNone(result["fallback"])

    def test_unknown_config_field_is_blocked_without_exposing_a_template(self):
        payload = opted_in_config()
        payload["capabilities"]["spec-kit"]["unexpected"] = True
        self.write_config(payload)

        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["source"]["template"], None)
        self.assertTrue(result["fallback"])

    def test_output_path_escape_returns_a_blocked_handoff(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.project / "specs").symlink_to(outside, target_is_directory=True)

            result = self.ska.build_handoff(
                ROOT, self.project, ISSUE_ID, "analyze", host_available=True
            )

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["output_artifact"], None)
        self.assertEqual(result["source"]["template"], None)
        self.assertEqual(result["source"]["template_sha256"], None)
        self.assertTrue(result["fallback"])

    def test_handoff_has_only_the_public_contract_keys(self):
        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "not a spec kit request", host_available=True
        )

        self.assertEqual(result["outcome"], "unsupported")
        self.assertEqual(
            set(result),
            {
                "schema",
                "outcome",
                "function",
                "issue_id",
                "source",
                "permission",
                "inputs",
                "output_artifact",
                "limitations",
                "fallback",
            },
        )
