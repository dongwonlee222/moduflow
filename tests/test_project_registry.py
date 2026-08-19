import importlib.util
import json
import tempfile
import unittest
from unittest import mock
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


class ProjectResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_module()

    def project(self, project_id, name, root, aliases=None, status="active"):
        relative_paths = dict(self.registry.CANONICAL_PATH_DEFAULTS)
        canonical_root = Path(root).resolve()
        return {
            "id": project_id,
            "name": name,
            "root": str(canonical_root),
            "aliases": sorted(
                {
                    self.registry.normalize_project_label(item)
                    for item in [project_id, name, *(aliases or [])]
                }
            ),
            "relative_paths": relative_paths,
            "paths": {
                key: str((canonical_root / value).resolve())
                for key, value in relative_paths.items()
            },
            "trust_scope": "internal",
            "status": status,
            "owner": "Owner",
            "source_schema": "moduflow.projects.v2",
        }

    def catalog(self, projects, valid=True):
        return {
            "schema": "moduflow.project-registry-read.v1",
            "valid": valid,
            "source_schema": "moduflow.projects.v2",
            "registry_path": "/portfolio/projects.json",
            "projects": projects,
            "diagnostics": [],
            "migration_proposal": None,
        }

    def test_explicit_id_wins_over_conflicting_cwd_and_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_a = root / "project-a"
            project_b = root / "project-b"
            project_a.mkdir()
            project_b.mkdir()
            catalog = self.catalog(
                [
                    self.project("project-a", "Project A", project_a),
                    self.project(
                        "project-b", "모두의충전", project_b, ["모두의충전"]
                    ),
                ]
            )

            result = self.registry.resolve_loaded_registry(
                catalog,
                explicit_project_id="project-a",
                cwd=project_b,
                request_text="모두의충전 배너 수정",
            )

            self.assertEqual(result["status"], "resolved")
            self.assertEqual(result["project_id"], "project-a")
            self.assertEqual(result["reason_code"], "explicit_id")
            self.assertIn("PROJECT_SIGNAL_CONFLICT", result["warnings"])

    def test_exactly_one_containing_cwd_root_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_a = root / "a"
            project_b = root / "b"
            cwd = project_b / "nested" / "feature"
            project_a.mkdir()
            cwd.mkdir(parents=True)

            result = self.registry.resolve_loaded_registry(
                self.catalog(
                    [
                        self.project("project-a", "Project A", project_a),
                        self.project("project-b", "Project B", project_b),
                    ]
                ),
                cwd=cwd,
            )

            self.assertEqual(result["project_id"], "project-b")
            self.assertEqual(result["reason_code"], "cwd_root")

    def test_korean_alias_matches_as_a_complete_normalized_phrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a"
            b = root / "b"
            a.mkdir()
            b.mkdir()
            result = self.registry.resolve_loaded_registry(
                self.catalog(
                    [
                        self.project("project-a", "Project A", a),
                        self.project("modu-charge", "모두의충전", b, ["모두충전"]),
                    ]
                ),
                request_text="모두충전 배너 수정",
            )

            self.assertEqual(result["project_id"], "modu-charge")
            self.assertEqual(result["reason_code"], "request_alias")

    def test_active_issue_project_precedes_recent_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a"
            b = root / "b"
            a.mkdir()
            b.mkdir()
            result = self.registry.resolve_loaded_registry(
                self.catalog(
                    [
                        self.project("project-a", "Project A", a),
                        self.project("project-b", "Project B", b),
                    ]
                ),
                active_project_id="project-a",
                recent_selection={"project_id": "project-b"},
            )

            self.assertEqual(result["project_id"], "project-a")
            self.assertEqual(result["reason_code"], "active_project")

    def test_recent_selection_is_last_successful_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a"
            b = root / "b"
            a.mkdir()
            b.mkdir()
            result = self.registry.resolve_loaded_registry(
                self.catalog(
                    [
                        self.project("project-a", "Project A", a),
                        self.project("project-b", "Project B", b),
                    ]
                ),
                recent_selection={"project_id": "project-b"},
            )

            self.assertEqual(result["project_id"], "project-b")
            self.assertEqual(result["reason_code"], "recent_selection")

    def test_duplicate_alias_is_ambiguous_and_redacts_project_paths(self):
        catalog = self.registry.load_project_registry(
            FIXTURES / "projects-v2-alias-collision.json"
        )

        result = self.registry.resolve_loaded_registry(
            catalog,
            request_text="이벤트 배너",
        )

        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(result["reason_code"], "request_alias_ambiguous")
        self.assertEqual(
            result["candidates"],
            [
                {"id": "project-a", "name": "Project A"},
                {"id": "project-b", "name": "Project B"},
            ],
        )
        self.assertEqual(result["canonical_root"], "")
        self.assertEqual(result["relative_paths"], {})
        self.assertEqual(result["paths"], {})
        self.assertEqual(result["trust_scope"], "")
        self.assertTrue(result["question"])

    def test_no_signal_with_multiple_projects_is_ambiguous(self):
        catalog = self.registry.load_project_registry(FIXTURES / "projects-v2.json")

        result = self.registry.resolve_loaded_registry(catalog)

        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(result["reason_code"], "multiple_projects")
        self.assertEqual(
            {item["id"] for item in result["candidates"]},
            {"project-a", "modu-charge"},
        )

    def test_invalid_registry_is_unresolved(self):
        result = self.registry.resolve_loaded_registry(self.catalog([], valid=False))

        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(result["reason_code"], "registry_invalid")
        self.assertIn("PROJECT_REGISTRY_INVALID", result["warnings"])

    def test_missing_selected_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            result = self.registry.resolve_loaded_registry(
                self.catalog([self.project("project-a", "Project A", missing)]),
                explicit_project_id="project-a",
            )

            self.assertEqual(result["status"], "unresolved")
            self.assertEqual(result["reason_code"], "project_root_missing")
            self.assertEqual(result["paths"], {})
            self.assertIn("PROJECT_ROOT_MISSING", result["warnings"])

    def test_unknown_explicit_id_does_not_fall_back_to_other_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "a"
            root.mkdir()
            result = self.registry.resolve_loaded_registry(
                self.catalog([self.project("project-a", "Project A", root)]),
                explicit_project_id="missing-project",
                cwd=root,
                request_text="Project A",
            )

            self.assertEqual(result["status"], "unresolved")
            self.assertEqual(result["reason_code"], "explicit_id_not_registered")
            self.assertIn("PROJECT_ID_NOT_REGISTERED", result["warnings"])

    def test_unregistered_sibling_is_never_added_as_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a"
            b = root / "b"
            sibling = root / "unregistered"
            a.mkdir()
            b.mkdir()
            sibling.mkdir()
            result = self.registry.resolve_loaded_registry(
                self.catalog(
                    [
                        self.project("project-a", "Project A", a),
                        self.project("project-b", "Project B", b),
                    ]
                ),
                cwd=sibling,
            )

            self.assertEqual(result["status"], "ambiguous")
            self.assertNotIn(
                str(sibling),
                json.dumps(result, ensure_ascii=False),
            )

    def test_ambiguous_resolution_performs_no_project_local_reads(self):
        catalog = self.registry.load_project_registry(
            FIXTURES / "projects-v2-alias-collision.json"
        )

        with mock.patch.object(
            Path, "read_text", side_effect=AssertionError("project read")
        ):
            result = self.registry.resolve_loaded_registry(
                catalog,
                request_text="이벤트 배너",
            )

        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(result["paths"], {})


class ProjectContextCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_module()

    def write_v1_registry(self, directory, projects):
        path = Path(directory) / "projects.json"
        path.write_text(
            json.dumps(
                {"schema": "moduflow.projects.v1", "projects": projects},
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def write_v2_registry(self, directory, projects):
        path = Path(directory) / "projects.json"
        payloads = []
        for project_id, name, root in projects:
            payloads.append(
                {
                    "id": project_id,
                    "name": name,
                    "root": str(root),
                    "aliases": [project_id, name],
                    "paths": dict(self.registry.CANONICAL_PATH_DEFAULTS),
                    "trust_scope": "internal",
                    "status": "active",
                    "owner": "Owner",
                }
            )
        path.write_text(
            json.dumps(
                {"schema": "moduflow.projects.v2", "projects": payloads},
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_v1_is_read_compatible_and_returns_migration_proposal_without_rewrite(self):
        path = FIXTURES / "projects-v1.json"
        before = path.read_bytes()

        result = self.registry.load_project_registry(path)

        self.assertTrue(result["valid"])
        self.assertEqual(result["source_schema"], "moduflow.projects.v1")
        self.assertEqual(
            result["migration_proposal"]["schema"],
            "moduflow.projects-migration-proposal.v1",
        )
        self.assertEqual(
            result["migration_proposal"]["to_schema"],
            "moduflow.projects.v2",
        )
        self.assertEqual(
            result["migration_proposal"]["projects"][0]["paths"],
            self.registry.CANONICAL_PATH_DEFAULTS,
        )
        self.assertEqual(path.read_bytes(), before)

    def test_only_selected_v1_project_reads_local_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_a = base / "a"
            project_b = base / "b"
            for root in (project_a, project_b):
                (root / ".moduflow").mkdir(parents=True)
            (project_a / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "paths": {
                            "issues": "product/issues",
                            "specs": "product/specs",
                            "workspace": "product/workspace",
                        }
                    }
                ),
                encoding="utf-8",
            )
            (project_b / ".moduflow" / "config.json").write_text(
                '{"paths": {"issues": "must-not-read"}}',
                encoding="utf-8",
            )
            registry_path = self.write_v1_registry(
                base,
                [
                    {"id": "project-a", "name": "A", "path": str(project_a)},
                    {"id": "project-b", "name": "B", "path": str(project_b)},
                ],
            )
            forbidden = (project_b / ".moduflow" / "config.json").resolve()
            original_read_text = Path.read_text

            def guarded_read_text(path, *args, **kwargs):
                if Path(path).resolve() == forbidden:
                    raise AssertionError("unselected project config read")
                return original_read_text(path, *args, **kwargs)

            with mock.patch.object(Path, "read_text", guarded_read_text):
                result = self.registry.resolve_project(
                    registry_path,
                    explicit_project_id="project-a",
                )

            self.assertEqual(result["status"], "resolved")
            self.assertEqual(result["project_id"], "project-a")
            self.assertEqual(result["relative_paths"]["issues"], "product/issues")
            self.assertEqual(result["relative_paths"]["specs"], "product/specs")
            self.assertEqual(
                result["relative_paths"]["workspace"], "product/workspace"
            )
            self.assertEqual(result["relative_paths"]["memory"], "memory")

    def test_explicit_root_context_matches_project_local_configured_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "paths": {
                            "issues": "product/issues",
                            "specs": "product/specs",
                            "workspace": "product/workspace",
                            "memory": "project-memory",
                        }
                    }
                ),
                encoding="utf-8",
            )

            context = self.registry.project_context_for_root(root)

            self.assertEqual(context["status"], "resolved")
            self.assertEqual(context["reason_code"], "explicit_root")
            self.assertEqual(context["relative_paths"]["issues"], "product/issues")
            self.assertEqual(context["relative_paths"]["memory"], "project-memory")
            self.assertEqual(
                self.registry.canonical_path(context, "issues"),
                (root / "product" / "issues").resolve(),
            )

    def test_unsafe_new_config_paths_fall_back_and_surface_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "paths": {
                            "memory": "../outside-memory",
                            "playbooks": "/tmp/outside-playbooks",
                        }
                    }
                ),
                encoding="utf-8",
            )

            context = self.registry.project_context_for_root(root)

            self.assertEqual(context["relative_paths"]["memory"], "memory")
            self.assertEqual(context["relative_paths"]["playbooks"], "playbooks")
            self.assertEqual(
                context["warnings"].count("PROJECT_CONFIG_PATH_OUTSIDE_ROOT"),
                2,
            )

    def test_canonical_path_rejects_unresolved_context_and_unknown_key(self):
        unresolved = {
            "status": "unresolved",
            "paths": {},
        }
        with self.assertRaises(ValueError):
            self.registry.canonical_path(unresolved, "issues")

        with tempfile.TemporaryDirectory() as tmp:
            context = self.registry.project_context_for_root(tmp)
            with self.assertRaises(KeyError):
                self.registry.canonical_path(context, "assets")

    def test_selection_write_is_atomic_minimal_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = base / "project-a"
            project.mkdir()
            registry_path = self.write_v2_registry(
                base, [("project-a", "Project A", project)]
            )
            selected_at = "2026-08-19T10:30:00+09:00"

            first = self.registry.record_recent_selection(
                registry_path, "project-a", selected_at
            )
            selection_path = base / "project-selection.json"
            before = selection_path.read_bytes()
            second = self.registry.record_recent_selection(
                registry_path, "project-a", selected_at
            )

            payload = json.loads(before)
            self.assertEqual(first["action"], "written")
            self.assertEqual(second["action"], "noop")
            self.assertEqual(
                set(payload), {"schema", "project_id", "selected_at"}
            )
            self.assertEqual(selection_path.read_bytes(), before)
            self.assertFalse((base / "project-selection.json.tmp").exists())

    def test_invalid_or_unregistered_selection_is_ignored_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = base / "project-a"
            project.mkdir()
            registry_path = self.write_v2_registry(
                base, [("project-a", "Project A", project)]
            )
            selection_path = base / "project-selection.json"
            cases = [
                ("{bad-json", "PROJECT_SELECTION_MALFORMED"),
                (
                    json.dumps(
                        {
                            "schema": "moduflow.project-selection.v1",
                            "project_id": "missing",
                            "selected_at": "2026-08-19T10:30:00+09:00",
                        }
                    ),
                    "PROJECT_SELECTION_NOT_REGISTERED",
                ),
                (
                    json.dumps(
                        {
                            "schema": "moduflow.project-selection.v1",
                            "project_id": "project-a",
                            "selected_at": "not-a-time",
                        }
                    ),
                    "PROJECT_SELECTION_TIME_INVALID",
                ),
            ]
            for payload, warning in cases:
                with self.subTest(warning=warning):
                    selection_path.write_text(payload, encoding="utf-8")
                    result = self.registry.load_recent_selection(registry_path)
                    self.assertEqual(result["project_id"], "")
                    self.assertIn(warning, result["warnings"])

    def test_recent_selection_is_loaded_by_resolve_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_a = base / "a"
            project_b = base / "b"
            project_a.mkdir()
            project_b.mkdir()
            registry_path = self.write_v2_registry(
                base,
                [
                    ("project-a", "Project A", project_a),
                    ("project-b", "Project B", project_b),
                ],
            )
            self.registry.record_recent_selection(
                registry_path,
                "project-b",
                "2026-08-19T10:30:00+09:00",
            )

            result = self.registry.resolve_project(registry_path)

            self.assertEqual(result["project_id"], "project-b")
            self.assertEqual(result["reason_code"], "recent_selection")

    def test_unknown_selection_write_is_rejected_without_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = base / "project-a"
            project.mkdir()
            registry_path = self.write_v2_registry(
                base, [("project-a", "Project A", project)]
            )

            with self.assertRaises(ValueError):
                self.registry.record_recent_selection(
                    registry_path,
                    "missing",
                    "2026-08-19T10:30:00+09:00",
                )

            self.assertFalse((base / "project-selection.json").exists())


if __name__ == "__main__":
    unittest.main()
