import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "project-registry"


def load_module():
    path = ROOT / "scripts" / "project_registry.py"
    spec = importlib.util.spec_from_file_location("project_registry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectRegistryParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_module()

    def write_registry(self, root, payload):
        path = Path(root) / "projects.json"
        path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def valid_project(self, root="project-a"):
        return {
            "id": "project-a",
            "name": "Project A",
            "root": root,
            "aliases": ["Project A"],
            "paths": dict(self.registry.CANONICAL_PATH_DEFAULTS),
            "trust_scope": "internal",
            "status": "active",
            "owner": "Mina",
        }

    def diagnostic_codes(self, result):
        return [item["code"] for item in result["diagnostics"]]

    def test_valid_v2_registry_normalizes_projects_and_nested_paths(self):
        result = self.registry.load_project_registry(FIXTURES / "projects-v2.json")

        self.assertTrue(result["valid"])
        self.assertEqual(result["schema"], "moduflow.project-registry-read.v1")
        self.assertEqual(result["source_schema"], "moduflow.projects.v2")
        self.assertEqual(result["projects"][1]["id"], "modu-charge")
        self.assertEqual(
            result["projects"][1]["relative_paths"]["issues"],
            "projects/modu-charge/issues",
        )
        self.assertTrue(
            result["projects"][1]["paths"]["issues"].endswith(
                "/projects/modu-charge/issues"
            )
        )
        self.assertEqual(result["projects"][1]["aliases"], [
            "modu-charge",
            "모두의충전",
            "모두충전",
        ])

    def test_relative_root_is_resolved_from_registry_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = self.write_registry(
                tmp,
                {
                    "schema": "moduflow.projects.v2",
                    "projects": [self.valid_project("projects/a")],
                },
            )

            result = self.registry.load_project_registry(registry_path)

            self.assertEqual(
                result["projects"][0]["root"],
                str((Path(tmp) / "projects" / "a").resolve()),
            )

    def test_label_normalization_uses_nfkc_casefold_and_token_spacing(self):
        self.assertEqual(
            self.registry.normalize_project_label("  ＭＯＤＵ－Charge!! 모두의충전  "),
            "modu-charge 모두의충전",
        )

    def test_malformed_json_returns_diagnostic_instead_of_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "projects.json"
            path.write_text("{not-json", encoding="utf-8")

            result = self.registry.load_project_registry(path)

            self.assertFalse(result["valid"])
            self.assertIn("PROJECT_REGISTRY_MALFORMED", self.diagnostic_codes(result))

    def test_missing_and_unknown_schema_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, payload, expected in [
                ("missing", {"projects": []}, "PROJECT_REGISTRY_SCHEMA_MISSING"),
                (
                    "unknown",
                    {"schema": "moduflow.projects.v9", "projects": []},
                    "PROJECT_REGISTRY_SCHEMA_UNSUPPORTED",
                ),
            ]:
                with self.subTest(name=name):
                    result = self.registry.load_project_registry(
                        self.write_registry(tmp, payload)
                    )
                    self.assertFalse(result["valid"])
                    self.assertIn(expected, self.diagnostic_codes(result))

    def test_projects_must_be_a_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.registry.load_project_registry(
                self.write_registry(
                    tmp,
                    {"schema": "moduflow.projects.v2", "projects": {}},
                )
            )
            self.assertIn("PROJECTS_NOT_LIST", self.diagnostic_codes(result))

    def test_duplicate_ids_are_rejected_without_order_based_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = self.valid_project("a")
            second = self.valid_project("b")
            second["name"] = "Other"
            result = self.registry.load_project_registry(
                self.write_registry(
                    tmp,
                    {"schema": "moduflow.projects.v2", "projects": [first, second]},
                )
            )
            self.assertFalse(result["valid"])
            self.assertIn("PROJECT_ID_DUPLICATE", self.diagnostic_codes(result))

    def test_required_scalar_fields_reject_empty_or_invalid_values(self):
        cases = [
            ("id", "", "PROJECT_ID_INVALID"),
            ("name", "", "PROJECT_NAME_INVALID"),
            ("trust_scope", "", "PROJECT_TRUST_SCOPE_INVALID"),
            ("trust_scope", "Internal Team", "PROJECT_TRUST_SCOPE_INVALID"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for field, value, expected in cases:
                with self.subTest(field=field, value=value):
                    project = self.valid_project()
                    project[field] = value
                    result = self.registry.load_project_registry(
                        self.write_registry(
                            tmp,
                            {"schema": "moduflow.projects.v2", "projects": [project]},
                        )
                    )
                    self.assertFalse(result["valid"])
                    self.assertIn(expected, self.diagnostic_codes(result))

    def test_v2_paths_require_exact_canonical_key_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = self.valid_project()
            del missing["paths"]["workflow"]
            unknown = self.valid_project()
            unknown["paths"]["assets"] = "assets"
            for project, expected in [
                (missing, "PROJECT_PATH_MISSING"),
                (unknown, "PROJECT_PATH_UNKNOWN"),
            ]:
                with self.subTest(expected=expected):
                    result = self.registry.load_project_registry(
                        self.write_registry(
                            tmp,
                            {"schema": "moduflow.projects.v2", "projects": [project]},
                        )
                    )
                    self.assertFalse(result["valid"])
                    self.assertIn(expected, self.diagnostic_codes(result))

    def test_absolute_and_parent_escape_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for value in ["/tmp/outside/issues", "../outside/issues"]:
                with self.subTest(value=value):
                    project = self.valid_project()
                    project["paths"]["issues"] = value
                    result = self.registry.load_project_registry(
                        self.write_registry(
                            tmp,
                            {"schema": "moduflow.projects.v2", "projects": [project]},
                        )
                    )
                    self.assertFalse(result["valid"])
                    self.assertIn("PROJECT_PATH_OUTSIDE_ROOT", self.diagnostic_codes(result))

    def test_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_root = root / "project"
            outside = root / "outside"
            project_root.mkdir()
            outside.mkdir()
            (project_root / "linked").symlink_to(outside, target_is_directory=True)
            project = self.valid_project(str(project_root))
            project["paths"]["issues"] = "linked/issues"

            result = self.registry.load_project_registry(
                self.write_registry(
                    root,
                    {"schema": "moduflow.projects.v2", "projects": [project]},
                )
            )

            self.assertFalse(result["valid"])
            self.assertIn("PROJECT_PATH_OUTSIDE_ROOT", self.diagnostic_codes(result))


if __name__ == "__main__":
    unittest.main()
