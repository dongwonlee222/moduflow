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


class ProjectWorkflowTests(unittest.TestCase):
    def test_workflow_dry_run_lists_missing_files_without_writing(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            plan = project_workflow.build_workflow_plan(root)

            self.assertTrue(plan["dry_run"])
            self.assertEqual(
                plan["writes"],
                [
                    "workflow/review-gates.md",
                    "workflow/approval-policy.md",
                    "workflow/release-policy.md",
                    "workflow/handoff.md",
                    "workflow/risks.md",
                ],
            )
            self.assertFalse((root / "workflow" / "review-gates.md").exists())

    def test_workflow_write_preserves_existing_handoff(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "workflow" / "handoff.md"
            handoff.parent.mkdir()
            handoff.write_text("# Existing Handoff\n", encoding="utf-8")

            plan = project_workflow.build_workflow_plan(root, dry_run=False)
            result = project_workflow.apply_workflow_plan(plan)

            self.assertNotIn("workflow/handoff.md", result["written"])
            self.assertEqual(handoff.read_text(encoding="utf-8"), "# Existing Handoff\n")
            self.assertTrue((root / "workflow" / "review-gates.md").exists())

    def test_create_workflow_record_includes_state_roles_and_blockers(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            record = project_workflow.create_workflow_record(
                root,
                issue_id="005-team-workflow",
                state="ready-for-review",
                owner="Dongwon Lee",
                reviewers=["QA", "PM"],
                approver="Mina",
                blocker="none",
                next_command="product:review 005-team-workflow",
            )

            content = (root / record["path"]).read_text(encoding="utf-8")
            self.assertIn("state: ready-for-review", content)
            self.assertIn("owner: Dongwon Lee", content)
            self.assertIn("reviewers: QA, PM", content)
            self.assertIn("approver: Mina", content)
            self.assertIn("blocker: none", content)
            self.assertIn("next_command: product:review 005-team-workflow", content)

    def test_doctor_reports_workflow_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = project_doctor.inspect_project(root)

            self.assertFalse(result["workflow"]["initialized"])
            self.assertIn("workflow/review-gates.md", result["workflow"]["missing"])
            self.assertIn("product:handoff", " ".join(result["recommendation"]))

    def test_doctor_reports_workflow_initialized(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = project_workflow.build_workflow_plan(root, dry_run=False)
            project_workflow.apply_workflow_plan(plan)

            missing = project_doctor.missing_workflow_paths(root)

            self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
