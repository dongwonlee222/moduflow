import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


project_doctor = load_module("project_doctor", "scripts/project_doctor.py")


class ProjectMigrationTests(unittest.TestCase):
    def test_doctor_discovers_existing_project_artifact_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "planning").mkdir()
            (root / "reports").mkdir()
            (root / "research").mkdir()

            candidates = project_doctor.discover_candidate_paths(root)

            self.assertEqual(candidates["specs"], ["docs/specs"])
            self.assertEqual(candidates["workspace"], ["planning"])
            self.assertEqual(candidates["reports"], ["reports"])
            self.assertEqual(candidates["research"], ["research"])

    def test_doctor_recommends_mapped_migration_when_candidates_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "planning").mkdir()

            result = project_doctor.inspect_project(root)

            self.assertFalse(result["moduflow"]["initialized"])
            self.assertEqual(result["migration"]["recommended_mode"], "mapped")
            self.assertIn("product:migrate --mode mapped", " ".join(result["recommendation"]))

    def test_migration_dry_run_builds_plan_without_writing_files(self):
        project_migrate = load_module("project_migrate", "scripts/project_migrate.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "planning").mkdir()

            plan = project_migrate.build_migration_plan(root, mode="mapped")

            self.assertTrue(plan["dry_run"])
            self.assertEqual(plan["mode"], "mapped")
            self.assertEqual(plan["config"]["paths"]["specs"], "docs/specs")
            self.assertEqual(plan["config"]["paths"]["workspace"], "planning")
            self.assertFalse((root / ".moduflow" / "config.json").exists())

    def test_migration_write_creates_metadata_without_overwriting_existing_files(self):
        project_migrate = load_module("project_migrate", "scripts/project_migrate.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "planning").mkdir()
            existing_dashboard = root / "planning" / "dashboard.md"
            existing_dashboard.write_text("# Existing Dashboard\n", encoding="utf-8")

            plan = project_migrate.build_migration_plan(root, mode="mapped", dry_run=False)
            project_migrate.apply_migration_plan(plan)

            config = json.loads((root / ".moduflow" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["paths"]["specs"], "docs/specs")
            self.assertEqual(config["paths"]["workspace"], "planning")
            self.assertEqual(existing_dashboard.read_text(encoding="utf-8"), "# Existing Dashboard\n")
            self.assertTrue((root / ".moduflow" / "state.json").exists())

    def test_migration_plan_lists_only_missing_files_as_writes(self):
        project_migrate = load_module("project_migrate", "scripts/project_migrate.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text("{}\n", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}\n", encoding="utf-8")
            (root / "workspace").mkdir()
            (root / "workspace" / "dashboard.md").write_text("# Existing\n", encoding="utf-8")

            plan = project_migrate.build_migration_plan(root, mode="overlay")

            self.assertNotIn(".moduflow/config.json", plan["writes"])
            self.assertNotIn(".moduflow/state.json", plan["writes"])
            self.assertNotIn("workspace/dashboard.md", plan["writes"])
            self.assertIn("workspace/inbox.md", plan["writes"])


if __name__ == "__main__":
    unittest.main()
