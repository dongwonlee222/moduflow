import tempfile
import unittest
from pathlib import Path

from scripts import project_execution


class ProjectExecutionHandoffTests(unittest.TestCase):
    def test_build_review_handoff_includes_subagents_verification_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "051-autonomous-execute-review-visual-handoff"
            (root / "issues").mkdir()
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue: `051-autonomous-execute-review-visual-handoff`\n\n"
                "## Acceptance Criteria\n\n"
                "- Handoff includes subagent review.\n",
                encoding="utf-8",
            )
            (root / "specs" / issue_id / "spec.md").write_text(
                "# Spec\n\n## Acceptance Criteria\n\n- Review handoff includes HTML output.\n",
                encoding="utf-8",
            )
            (root / "specs" / issue_id / "tasks.md").write_text(
                "# Tasks\n\n"
                "- [x] Implementation: add helper [files: scripts/project_execution.py]\n"
                "- [ ] QA: verify helper [files: tests/test_project_execution.py]\n",
                encoding="utf-8",
            )
            (root / "specs" / issue_id / "status.md").write_text(
                "# Status\n\n## Done\n\n- Helper drafted.\n",
                encoding="utf-8",
            )

            handoff = project_execution.build_review_handoff(root, issue_id)

            self.assertIn("implementation-worker", handoff)
            self.assertIn("qa-reviewer", handoff)
            self.assertIn("pm-strategist", handoff)
            self.assertIn("spec-architect", handoff)
            self.assertIn("python3 -m unittest discover -s tests -v", handoff)
            self.assertIn("python3 scripts/release_check.py .", handoff)
            self.assertIn("python3 scripts/project_memory.py . --dashboard", handoff)
            self.assertIn("python3 scripts/project_memory.py . --issue 051-autonomous-execute-review-visual-handoff", handoff)
            self.assertIn("memory/dashboard.html", handoff)
            self.assertIn("memory/issue-051-autonomous-execute-review-visual-handoff.html", handoff)
            self.assertNotIn("- - [", handoff)

    def test_write_review_handoff_creates_issue_local_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "051-autonomous-execute-review-visual-handoff"
            (root / "issues").mkdir()
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text("# Issue\n", encoding="utf-8")
            (root / "specs" / issue_id / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (root / "specs" / issue_id / "tasks.md").write_text("- [ ] Code: implement\n", encoding="utf-8")
            (root / "specs" / issue_id / "status.md").write_text("# Status\n", encoding="utf-8")

            path = project_execution.write_review_handoff(root, issue_id)

            self.assertEqual(path, (root / "specs" / issue_id / "review-handoff.md").resolve())
            self.assertTrue(path.exists())
            self.assertIn("Review Handoff", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
