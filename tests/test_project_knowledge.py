import importlib.util
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


class ProjectKnowledgeTests(unittest.TestCase):
    def test_knowledge_dry_run_lists_missing_structure_without_writing(self):
        project_knowledge = load_module("project_knowledge", "scripts/project_knowledge.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            plan = project_knowledge.build_knowledge_plan(root)

            self.assertTrue(plan["dry_run"])
            self.assertIn("knowledge/index.md", plan["writes"])
            self.assertIn("knowledge/decisions", plan["writes"])
            self.assertFalse((root / "knowledge" / "index.md").exists())

    def test_knowledge_write_creates_missing_structure_and_preserves_existing_index(self):
        project_knowledge = load_module("project_knowledge", "scripts/project_knowledge.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "knowledge" / "index.md"
            index.parent.mkdir()
            index.write_text("# Existing Knowledge\n", encoding="utf-8")

            plan = project_knowledge.build_knowledge_plan(root, dry_run=False)
            result = project_knowledge.apply_knowledge_plan(plan)

            self.assertNotIn("knowledge/index.md", result["written"])
            self.assertEqual(index.read_text(encoding="utf-8"), "# Existing Knowledge\n")
            self.assertTrue((root / "knowledge" / "decisions").is_dir())
            self.assertTrue((root / "knowledge" / "data-notes").is_dir())

    def test_create_knowledge_artifact_includes_issue_spec_and_decision_support(self):
        project_knowledge = load_module("project_knowledge", "scripts/project_knowledge.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            artifact = project_knowledge.create_knowledge_artifact(
                root,
                kind="decision",
                title="Payment priority",
                issue_id="003-payment",
                spec_path="specs/003-payment/spec.md",
                decision_supported="Prioritize card onboarding",
            )

            artifact_path = root / artifact["path"]
            content = artifact_path.read_text(encoding="utf-8")
            self.assertEqual(artifact["kind"], "decision")
            self.assertIn("issue_id: 003-payment", content)
            self.assertIn("spec: specs/003-payment/spec.md", content)
            self.assertIn("decision_supported: Prioritize card onboarding", content)

    def test_doctor_reports_knowledge_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = project_doctor.inspect_project(root)

            self.assertFalse(result["knowledge"]["initialized"])
            self.assertIn("knowledge/index.md", result["knowledge"]["missing"])
            self.assertIn("product:knowledge", " ".join(result["recommendation"]))

    def test_doctor_reports_knowledge_initialized(self):
        project_knowledge = load_module("project_knowledge", "scripts/project_knowledge.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = project_knowledge.build_knowledge_plan(root, dry_run=False)
            project_knowledge.apply_knowledge_plan(plan)

            missing = project_doctor.missing_knowledge_paths(root)

            self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
