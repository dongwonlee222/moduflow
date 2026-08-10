import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
