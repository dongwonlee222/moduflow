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


class ProjectProfileTests(unittest.TestCase):
    def test_profile_dry_run_lists_missing_profile_files_without_writing(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            plan = project_profile.build_profile_plan(root)

            self.assertTrue(plan["dry_run"])
            self.assertEqual(
                plan["writes"],
                [
                    ".moduflow/project-profile.md",
                    ".moduflow/environments.json",
                    ".moduflow/integrations.json",
                ],
            )
            self.assertFalse((root / ".moduflow" / "project-profile.md").exists())

    def test_profile_write_creates_missing_files_and_preserves_existing_content(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = root / ".moduflow" / "project-profile.md"
            profile_path.parent.mkdir()
            profile_path.write_text("# Existing Profile\n", encoding="utf-8")

            plan = project_profile.build_profile_plan(root, dry_run=False)
            result = project_profile.apply_profile_plan(plan)

            self.assertNotIn(".moduflow/project-profile.md", result["written"])
            self.assertEqual(profile_path.read_text(encoding="utf-8"), "# Existing Profile\n")
            self.assertTrue((root / ".moduflow" / "environments.json").exists())
            self.assertTrue((root / ".moduflow" / "integrations.json").exists())

    def test_doctor_reports_profile_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text("{}\n", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}\n", encoding="utf-8")
            (root / "issues").mkdir()
            (root / "specs").mkdir()
            (root / "workspace").mkdir()
            for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / filename).write_text("# Test\n", encoding="utf-8")

            result = project_doctor.inspect_project(root)

            self.assertFalse(result["profile"]["initialized"])
            self.assertEqual(
                result["profile"]["missing"],
                [
                    ".moduflow/project-profile.md",
                    ".moduflow/environments.json",
                    ".moduflow/integrations.json",
                ],
            )
            self.assertIn("product:profile", " ".join(result["recommendation"]))

    def test_doctor_reports_profile_initialized(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = project_profile.build_profile_plan(root, dry_run=False)
            project_profile.apply_profile_plan(plan)

            missing = project_doctor.missing_profile_paths(root)

            self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
