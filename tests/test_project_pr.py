import tempfile
import unittest
from pathlib import Path

from scripts import project_pr


class ProjectPrHandoffTests(unittest.TestCase):
    def test_github_pr_preflight_falls_back_when_api_unreachable(self):
        calls = []

        def runner(args, cwd):
            calls.append(tuple(args))
            if args == ["gh", "auth", "status"]:
                return project_pr.CommandResult(0, "logged in", "")
            if args == ["gh", "api", "rate_limit"]:
                return project_pr.CommandResult(1, "", "error connecting to api.github.com")
            return project_pr.CommandResult(1, "", "unexpected")

        result = project_pr.github_pr_preflight(Path("."), runner=runner)

        self.assertFalse(result["ok"])
        self.assertEqual(result["mode"], "local-pr-ready")
        self.assertIn(("gh", "auth", "status"), calls)
        self.assertIn(("gh", "api", "rate_limit"), calls)
        self.assertIn("api.github.com", result["errors"][0])
        self.assertIn("Do not run gh pr create", result["recommendations"][0])

    def test_github_pr_preflight_allows_draft_pr_when_api_reachable(self):
        def runner(args, cwd):
            if args == ["gh", "auth", "status"]:
                return project_pr.CommandResult(0, "logged in", "")
            if args == ["gh", "api", "rate_limit"]:
                return project_pr.CommandResult(0, '{"resources":{}}', "")
            return project_pr.CommandResult(1, "", "unexpected")

        result = project_pr.github_pr_preflight(Path("."), runner=runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "github-draft-pr")
        self.assertIn("Draft PR creation may proceed", result["recommendations"][0])

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
            self.assertIn("human-review.ko.md", handoff)
            self.assertIn("Required status checks", handoff)
            self.assertIn("Human approval", handoff)
            self.assertIn("GitHub Draft PR URL is not recorded yet", handoff)
            self.assertIn("- tests passed.", handoff)
            self.assertIn("- QA accepted the handoff evidence.", handoff)
            self.assertIn("Merge approver", handoff)

    def test_build_pr_handoff_records_github_api_commit_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "058-git-write-fallback-via-github-api"
            (root / "issues").mkdir()
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text("# Issue\n", encoding="utf-8")

            handoff = project_pr.build_pr_handoff(
                root,
                issue_id,
                commit_mode="github-api-commit",
                commit_reason="local .git write failed: index.lock permission denied",
            )

            self.assertIn("Commit mode: `github-api-commit`", handoff)
            self.assertIn("index.lock permission denied", handoff)

    def test_build_pr_handoff_defaults_commit_mode_to_local_git_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "052-draft-pr-review-handoff"
            (root / "issues").mkdir()
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text("# Issue\n", encoding="utf-8")

            handoff = project_pr.build_pr_handoff(root, issue_id)

            self.assertIn("Commit mode: `local-git-write`", handoff)

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
            human_packet = root / "specs" / issue_id / "human-review.ko.md"
            self.assertTrue(human_packet.exists())
            self.assertIn("한글 검토 패킷", human_packet.read_text(encoding="utf-8"))

    def test_build_human_review_packet_uses_korean_description_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "057-korean-human-review-packet"
            (root / "issues").mkdir()
            (root / "workspace").mkdir()
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue: `057-korean-human-review-packet`\n\n"
                "## Outcome\n\n"
                "English review packet outcome.\n",
                encoding="utf-8",
            )
            (root / "workspace" / "issue-descriptions.ko.json").write_text(
                '{"057-korean-human-review-packet": "PR 확인을 위한 한글 검토 패킷을 자동 생성합니다."}',
                encoding="utf-8",
            )
            (root / "specs" / issue_id / "status.md").write_text(
                "# Status\n\n## Verification\n\n- tests passed.\n",
                encoding="utf-8",
            )

            packet = project_pr.build_human_review_packet_ko(
                root,
                issue_id,
                branch="codex/057-korean-human-review-packet",
                pr="local:057-review",
                reviewer="Dongwon",
            )

            self.assertIn("PR 확인을 위한 한글 검토 패킷을 자동 생성합니다.", packet)
            self.assertIn("memory/issue-057-korean-human-review-packet.html", packet)
            self.assertIn("codex/057-korean-human-review-packet", packet)
            self.assertIn("- tests passed.", packet)
            self.assertIn("승인 체크리스트", packet)
            self.assertIn("release 대상이면 rollback/post-release check", packet)

    def test_product_release_requires_korean_human_review_gate(self):
        command_doc = Path("commands/product-release.md").read_text(encoding="utf-8")

        self.assertIn("human-review.ko.md", command_doc)
        self.assertIn("first human approval surface", command_doc)
        self.assertIn("Korean Human Review Gate", command_doc)
        self.assertIn("Do not treat the local marker as merge or release approval", command_doc)


if __name__ == "__main__":
    unittest.main()
