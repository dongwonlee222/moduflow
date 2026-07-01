import tempfile
import unittest
from pathlib import Path

from scripts import project_pr


class ProjectPrHandoffTests(unittest.TestCase):
    def test_build_pr_handoff_includes_draft_pr_review_and_dashboard_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "052-draft-pr-review-handoff"
            (root / "issues").mkdir()
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue: `052-draft-pr-review-handoff`\n\n"
                "## Outcome\n\n"
                "Review happens around a draft PR.\n",
                encoding="utf-8",
            )
            (root / "specs" / issue_id / "spec.md").write_text(
                "# Spec\n\n## Acceptance Criteria\n\n- Draft PR receives review evidence.\n",
                encoding="utf-8",
            )
            (root / "specs" / issue_id / "status.md").write_text(
                "# Status\n\n## Verification\n\n- tests passed.\n",
                encoding="utf-8",
            )
            (root / "specs" / issue_id / "review.md").write_text(
                "# Review\n\n## Findings\n\n- QA accepted the handoff evidence.\n",
                encoding="utf-8",
            )

            handoff = project_pr.build_pr_handoff(
                root,
                issue_id,
                branch="codex/052-draft-pr-review-handoff",
                pr="local:052-draft-pr-ready",
                reviewer="Dongwon",
            )

            self.assertIn("Draft PR", handoff)
            self.assertIn("codex/052-draft-pr-review-handoff", handoff)
            self.assertIn("local:052-draft-pr-ready", handoff)
            self.assertIn("Dongwon", handoff)
            self.assertIn("product:review 052-draft-pr-review-handoff", handoff)
            self.assertIn("product:pr 052-draft-pr-review-handoff", handoff)
            self.assertIn("memory/dashboard.html", handoff)
            self.assertIn("memory/issue-052-draft-pr-review-handoff.html", handoff)
            self.assertIn("Required status checks", handoff)
            self.assertIn("Human approval", handoff)
            self.assertIn("GitHub Draft PR URL is not recorded yet", handoff)
            self.assertIn("- tests passed.", handoff)
            self.assertIn("- QA accepted the handoff evidence.", handoff)
            self.assertIn("Merge approver", handoff)

    def test_write_pr_handoff_creates_pr_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "052-draft-pr-review-handoff"
            (root / "issues").mkdir()
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text("# Issue\n", encoding="utf-8")
            (root / "specs" / issue_id / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (root / "specs" / issue_id / "status.md").write_text("# Status\n", encoding="utf-8")

            path = project_pr.write_pr_handoff(root, issue_id)

            self.assertEqual(path, (root / "specs" / issue_id / "pr.md").resolve())
            self.assertTrue(path.exists())
            self.assertIn("PR Handoff", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
