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

    def test_start_issue_work_records_branch_lock_and_assignment(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            item = project_workflow.start_issue_work(
                root,
                issue_id="035-team-issue-branch-pr-workflow",
                assignee="Minsu",
                owner="PM",
                reviewer="Dongwon",
            )

            self.assertEqual(item["status"], "active")
            self.assertEqual(item["branch"], "codex/035-team-issue-branch-pr-workflow")
            self.assertEqual(item["lock_state"], "active")
            self.assertEqual(item["locked_by"], "Minsu")
            self.assertEqual(item["next_command"], "product:execute 035-team-issue-branch-pr-workflow")
            self.assertTrue((root / "workflow" / "team-state.json").exists())

    def test_record_pr_state_moves_item_to_review(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_workflow.start_issue_work(
                root,
                issue_id="035-team-issue-branch-pr-workflow",
                assignee="Minsu",
                reviewer="Dongwon",
            )

            item = project_workflow.record_pr_state(
                root,
                issue_id="035-team-issue-branch-pr-workflow",
                pr="https://github.com/example/repo/pull/35",
                reviewer="Dongwon",
            )

            self.assertEqual(item["status"], "review")
            self.assertEqual(item["pr"], "https://github.com/example/repo/pull/35")
            self.assertEqual(item["reviewer"], "Dongwon")
            self.assertEqual(item["next_command"], "product:review 035-team-issue-branch-pr-workflow")

    def test_record_pr_state_preserves_existing_reviewer_when_omitted(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_workflow.start_issue_work(
                root,
                issue_id="035-team-issue-branch-pr-workflow",
                assignee="Minsu",
                reviewer="Dongwon",
            )

            item = project_workflow.record_pr_state(
                root,
                issue_id="035-team-issue-branch-pr-workflow",
                pr="local:035-team-issue-branch-pr-workflow",
            )

            self.assertEqual(item["reviewer"], "Dongwon")

    def test_render_team_status_groups_work_for_pm_view(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_workflow.start_issue_work(
                root,
                issue_id="035-team-issue-branch-pr-workflow",
                assignee="Minsu",
                owner="PM",
            )

            status = project_workflow.render_team_status(root)

            self.assertIn("## Active", status)
            self.assertIn("035-team-issue-branch-pr-workflow", status)
            self.assertIn("Minsu", status)
            self.assertIn("codex/035-team-issue-branch-pr-workflow", status)

    def test_suggest_completion_memory_returns_candidate_inputs(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            candidate = project_workflow.suggest_completion_memory(
                root,
                issue_id="035-team-issue-branch-pr-workflow",
                title="Team workflow decision",
                summary="Small teams use local Git files as canonical issue and PR state.",
                source_artifacts=["issues/035-team-issue-branch-pr-workflow.md"],
            )

            self.assertEqual(candidate["source_event"], "issue_completed")
            self.assertEqual(candidate["source_artifacts"], ["issues/035-team-issue-branch-pr-workflow.md"])
            self.assertEqual(candidate["storage_policy"], "canonical_git")
            self.assertIn("team-workflow", candidate["tags"])

    def test_done_team_item_recommends_status(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")

        self.assertEqual(
            project_workflow.next_command_for_status("035-team-issue-branch-pr-workflow", "done"),
            "product:status",
        )

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

    def test_run_review_check_generates_checklist(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_dir = root / "specs" / "039-test-review"
            spec_dir.mkdir(parents=True)
            
            # Create a mock spec.md with Acceptance Criteria
            spec_content = """# Spec: Test Review
            
## Acceptance Criteria

- [ ] Verify that automated checklist is generated.
- [ ] Ensure credentials scanner detects hardcoded keys.
"""
            (spec_dir / "spec.md").write_text(spec_content, encoding="utf-8")
            (spec_dir / "status.md").write_text("# Status\n\n## Next Command\n\nproduct:status\n", encoding="utf-8")

            # Mock git diff using a monkeypatched subprocess.check_output in the test
            import subprocess
            orig_check_output = subprocess.check_output
            try:
                # Stub git diff to return a fake diff that matches the first criterion keyword (checklist)
                subprocess.check_output = lambda *args, **kwargs: "+ Add automated checklist implementation\n"
                result = project_workflow.run_review_check(root, "039-test-review")
            finally:
                subprocess.check_output = orig_check_output

            self.assertTrue(result["ok"])
            status_text = (spec_dir / "status.md").read_text(encoding="utf-8")
            self.assertIn("## Automated Review Checklist", status_text)
            self.assertIn("[x] Verify that automated checklist is generated.", status_text)
            self.assertIn("[ ] Ensure credentials scanner detects hardcoded keys.", status_text)


if __name__ == "__main__":
    unittest.main()
