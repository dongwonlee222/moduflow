import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import project_operation, project_pr, project_registry


MATCHING_IDENTITY = {
    "schema": "moduflow.repository-identity.v1",
    "status": "match",
    "expected": {"repository": "github.com/dongwonlee222/moduflow", "base_branch": "main"},
    "observed": {},
    "capabilities": {"read": True, "github_write": True, "release": True},
    "reasons": [],
}


class ProjectPrHandoffTests(unittest.TestCase):
    def test_purpose_first_packets_preserve_issue_rationale_before_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "060-purpose-first"
            (root / "issues").mkdir()
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue\n\n## Why Needed\n\nUsers need trustworthy installation checks.\n\n"
                "## Problem\n\nHealthy packages are diagnosed as broken.\n\n"
                "## Expected Benefits\n\nFewer unnecessary reinstalls (expected, not measured).\n",
                encoding="utf-8",
            )
            path = project_pr.write_pr_handoff(root, issue_id)
            for filename, headings, verification in (
                ("pr.md", ("## Why Needed", "## Problem", "## Expected Benefits"), "### Verification"),
                ("human-review.ko.md", ("## 왜 필요한지", "## 해결해야 할 문제", "## 기대 효과"), "## 검증 요약"),
            ):
                with self.subTest(filename=filename):
                    output = (path.parent / filename).read_text(encoding="utf-8")
                    self.assertTrue(all(heading in output for heading in headings))
                    positions = [output.index(heading) for heading in (*headings, verification)]
                    self.assertEqual(positions, sorted(positions))
                    for heading, evidence in zip(headings, (
                        "Users need trustworthy installation checks.",
                        "Healthy packages are diagnosed as broken.",
                        "Fewer unnecessary reinstalls (expected, not measured).",
                    )):
                        content = output.split(heading + "\n", 1)[1].split("\n## ", 1)[0]
                        self.assertIn(evidence, content)

    def test_korean_issue_rationale_overrides_spec_per_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "060-korean-purpose"
            (root / "issues").mkdir()
            spec_dir = root / "specs" / issue_id
            spec_dir.mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue\n\n## 왜 필요한지\n\n이슈에서 확정한 필요성.\n\n"
                "## 기대 효과\n\n재작업 감소 예상, 아직 미측정.\n", encoding="utf-8",
            )
            (spec_dir / "spec.md").write_text(
                "# Spec\n\n## Why Needed\n\nSuperseded rationale.\n\n"
                "## Problem\n\n검사 대상 혼동.\n", encoding="utf-8",
            )
            for builder in (project_pr.build_pr_handoff, project_pr.build_human_review_packet_ko):
                with self.subTest(builder=builder.__name__):
                    output = builder(root, issue_id)
                    self.assertIn("이슈에서 확정한 필요성.", output)
                    self.assertIn("검사 대상 혼동.", output)
                    self.assertIn("재작업 감소 예상, 아직 미측정.", output)
                    self.assertNotIn("Superseded rationale.", output)

    def test_purpose_first_uses_configured_spec_without_cross_project_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "060-configured-purpose"
            (root / ".moduflow").mkdir()
            (root / ".moduflow/config.json").write_text(json.dumps({"paths": {
                "issues": "product/issues", "specs": "product/specs",
            }}), encoding="utf-8")
            for location, text in (
                (root / "product/specs" / issue_id / "spec.md",
                 "# Spec\n\n## Why Needed\n\nSelected project need.\n\n"
                 "## Problem\n\nSelected project problem.\n\n"
                 "## Expected Benefits\n\nSelected project benefit.\n"),
                (root / "issues" / f"{issue_id}.md",
                 "# Issue\n\n## Why Needed\n\nWRONG_PROJECT_CANARY\n"),
            ):
                location.parent.mkdir(parents=True, exist_ok=True)
                location.write_text(text, encoding="utf-8")
            for builder in (project_pr.build_pr_handoff, project_pr.build_human_review_packet_ko):
                with self.subTest(builder=builder.__name__):
                    output = builder(root, issue_id)
                    self.assertIn("Selected project need.", output)
                    self.assertIn("Selected project problem.", output)
                    self.assertIn("Selected project benefit.", output)
                    self.assertNotIn("WRONG_PROJECT_CANARY", output)

    def test_missing_purpose_is_unknown_not_inferred_from_summary_or_test_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "060-missing-purpose"
            (root / "issues").mkdir()
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue\n\n## Summary\n\nChanged 9 files; 100 tests passed.\n",
                encoding="utf-8",
            )
            for builder, headings, missing in (
                (project_pr.build_pr_handoff, ("## Why Needed", "## Problem", "## Expected Benefits"), "Not recorded"),
                (project_pr.build_human_review_packet_ko, ("## 왜 필요한지", "## 해결해야 할 문제", "## 기대 효과"), "미기록"),
            ):
                with self.subTest(builder=builder.__name__):
                    output = builder(root, issue_id)
                    for heading in headings:
                        self.assertIn(heading, output)
                        content = output.split(heading + "\n", 1)[1].split("\n## ", 1)[0]
                        self.assertIn(missing, content)
                        self.assertNotIn("100 tests passed", content)

    def test_archived_project_denies_pr_handoff_before_build_or_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = project_registry.project_context_for_root(root)
            context.update(project_operation.compute_project_policy("archived", "internal"))

            with mock.patch.object(
                project_pr,
                "build_pr_handoff",
                side_effect=AssertionError("build before authorization"),
            ) as build:
                with self.assertRaisesRegex(Exception, "Archived projects are read-only"):
                    project_pr.write_pr_handoff(
                        root,
                        "110-denied",
                        project_context=context,
                    )

            build.assert_not_called()
            self.assertFalse((root / "specs").exists())

    def test_pr_and_korean_packet_use_configured_specs_issues_workspace_and_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "102-configured-pr"
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "paths": {
                            "issues": "product/issues",
                            "specs": "product/specs",
                            "workspace": "product/workspace",
                            "memory": "product/memory",
                        }
                    }
                ),
                encoding="utf-8",
            )
            issue_dir = root / "product" / "issues"
            spec_dir = root / "product" / "specs" / issue_id
            workspace_dir = root / "product" / "workspace"
            issue_dir.mkdir(parents=True)
            spec_dir.mkdir(parents=True)
            workspace_dir.mkdir(parents=True)
            (issue_dir / f"{issue_id}.md").write_text(
                "# Issue: Configured PR\n", encoding="utf-8"
            )
            (workspace_dir / "issue-descriptions.ko.json").write_text(
                json.dumps({issue_id: "설정 경로의 한글 설명"}, ensure_ascii=False),
                encoding="utf-8",
            )

            path = project_pr.write_pr_handoff(root, issue_id)
            packet = (spec_dir / "human-review.ko.md").read_text(encoding="utf-8")
            handoff = path.read_text(encoding="utf-8")

            self.assertEqual(path, (spec_dir / "pr.md").resolve())
            self.assertIn("설정 경로의 한글 설명", packet)
            self.assertIn("product/memory/dashboard.html", handoff)
            self.assertFalse((root / "specs" / issue_id).exists())

    def test_github_pr_preflight_falls_back_when_api_unreachable(self):
        calls = []

        def runner(args, cwd):
            calls.append(tuple(args))
            if args == ["gh", "auth", "status"]:
                return project_pr.CommandResult(0, "logged in", "")
            if args == ["gh", "api", "rate_limit"]:
                return project_pr.CommandResult(1, "", "error connecting to api.github.com")
            return project_pr.CommandResult(1, "", "unexpected")

        result = project_pr.github_pr_preflight(
            Path("."), runner=runner, identity_result=MATCHING_IDENTITY
        )

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

        result = project_pr.github_pr_preflight(
            Path("."), runner=runner, identity_result=MATCHING_IDENTITY
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "github-draft-pr")
        self.assertIn("Draft PR creation may proceed", result["recommendations"][0])

    def test_github_pr_preflight_stops_before_auth_on_identity_mismatch(self):
        calls = []

        def runner(args, cwd):
            calls.append(tuple(args))
            return project_pr.CommandResult(0, "", "")

        identity = {
            "schema": "moduflow.repository-identity.v1",
            "status": "mismatch",
            "expected": {"repository": "github.com/owner/repo"},
            "observed": {"push_repositories": ["github.com/other/repo"]},
            "capabilities": {"read": True, "github_write": False},
            "reasons": [{"code": "push_remote_mismatch", "message": "wrong push repo"}],
        }

        result = project_pr.github_pr_preflight(
            Path("."), runner=runner, identity_result=identity
        )

        self.assertFalse(result["ok"])
        self.assertEqual(calls, [])
        self.assertEqual(result["repository_identity"]["reasons"][0]["code"], "push_remote_mismatch")

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
        self.assertIn("project_repository_identity.py <project-path> --operation release", command_doc)
        self.assertIn("before tag, release, deploy, or publish", command_doc)


if __name__ == "__main__":
    unittest.main()
