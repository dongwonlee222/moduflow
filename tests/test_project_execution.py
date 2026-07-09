import tempfile
import unittest
import json
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

    def test_build_implementation_readiness_returns_ready_for_explicit_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "077-implementation-readiness-gate"
            (root / "issues").mkdir()
            spec_dir = root / "specs" / issue_id
            spec_dir.mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue\n\nBuild an API-backed frontend screen with admin role access.\n",
                encoding="utf-8",
            )
            (spec_dir / "spec.md").write_text(
                "# Spec\n\nUI frontend uses API endpoint and admin permission model.\n",
                encoding="utf-8",
            )
            (spec_dir / "plan.md").write_text(
                "# Plan\n\n"
                "API contract mapping: GET /api/widgets response { items: [] }, 404 error state.\n"
                "Test strategy: unit tests for parser and integration tests for readiness.\n"
                "Storybook required states: loading, empty, error, success.\n"
                "MSW fixture baseline: widgetsSuccess, widgetsEmpty, widgetsError.\n"
                "Playwright smoke matrix: /widgets, create widget, assert success on desktop.\n"
                "Permission/role model: admin allowed, viewer denied.\n"
                "Release/rollback verification: run release_check and disable widget route on rollback.\n",
                encoding="utf-8",
            )
            (spec_dir / "tasks.md").write_text("- [ ] Code: implement\n", encoding="utf-8")
            (spec_dir / "status.md").write_text("# Status\n", encoding="utf-8")

            readiness = project_execution.build_implementation_readiness(root, issue_id)

            self.assertEqual(readiness["schema"], "moduflow.implementation-readiness.v1")
            self.assertEqual(readiness["status"], "ready")
            self.assertEqual(readiness["next_command"], f"product:execute {issue_id}")
            checks = {check["id"]: check for check in readiness["checks"]}
            self.assertEqual(checks["api_contract"]["state"], "pass")
            self.assertEqual(checks["storybook_states"]["state"], "pass")
            self.assertEqual(checks["permission_model"]["state"], "pass")

    def test_build_implementation_readiness_reports_not_ready_for_missing_high_severity_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "077-implementation-readiness-gate"
            (root / "issues").mkdir()
            spec_dir = root / "specs" / issue_id
            spec_dir.mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue\n\nBuild an API-backed frontend UI for admin users.\n",
                encoding="utf-8",
            )
            (spec_dir / "spec.md").write_text(
                "# Spec\n\nThe browser screen calls an API and uses role-based access.\n",
                encoding="utf-8",
            )
            (spec_dir / "plan.md").write_text("# Plan\n\nImplement UI.\n", encoding="utf-8")
            (spec_dir / "tasks.md").write_text("- [ ] Code: implement\n", encoding="utf-8")
            (spec_dir / "status.md").write_text("# Status\n", encoding="utf-8")

            readiness = project_execution.build_implementation_readiness(root, issue_id)

            self.assertEqual(readiness["status"], "not_ready")
            self.assertEqual(readiness["next_command"], f"product:plan {issue_id}")
            failed = {check["id"]: check for check in readiness["checks"] if check["state"] == "fail"}
            self.assertIn("api_contract", failed)
            self.assertIn("test_strategy", failed)
            self.assertEqual(failed["api_contract"]["severity"], "high")
            self.assertIn("API contract mapping", failed["api_contract"]["gap"])

    def test_build_implementation_readiness_marks_frontend_checks_not_applicable_for_docs_only_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "077-implementation-readiness-gate"
            (root / "issues").mkdir()
            spec_dir = root / "specs" / issue_id
            spec_dir.mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue\n\nUpdate command documentation only.\n",
                encoding="utf-8",
            )
            (spec_dir / "spec.md").write_text("# Spec\n\nDocs-only command guidance.\n", encoding="utf-8")
            (spec_dir / "plan.md").write_text(
                "# Plan\n\nTest strategy: run validate_moduflow and release_check.\n"
                "Release/rollback verification: docs-only rollback is git revert.\n",
                encoding="utf-8",
            )
            (spec_dir / "tasks.md").write_text("- [ ] Docs: update commands\n", encoding="utf-8")
            (spec_dir / "status.md").write_text("# Status\n", encoding="utf-8")

            readiness = project_execution.build_implementation_readiness(root, issue_id)

            checks = {check["id"]: check for check in readiness["checks"]}
            self.assertEqual(checks["storybook_states"]["state"], "not_applicable")
            self.assertEqual(checks["msw_fixtures"]["state"], "not_applicable")
            self.assertEqual(checks["playwright_smoke"]["state"], "not_applicable")
            self.assertEqual(checks["permission_model"]["state"], "not_applicable")

    def test_write_implementation_readiness_creates_json_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "077-implementation-readiness-gate"
            (root / "issues").mkdir()
            spec_dir = root / "specs" / issue_id
            spec_dir.mkdir(parents=True)
            (root / "issues" / f"{issue_id}.md").write_text("# Issue\n\nDocs only.\n", encoding="utf-8")
            (spec_dir / "spec.md").write_text("# Spec\n\nDocs only.\n", encoding="utf-8")
            (spec_dir / "plan.md").write_text(
                "# Plan\n\nTest strategy: validate docs.\nRelease/rollback verification: git revert.\n",
                encoding="utf-8",
            )
            (spec_dir / "tasks.md").write_text("- [ ] Docs: update\n", encoding="utf-8")
            (spec_dir / "status.md").write_text("# Status\n", encoding="utf-8")

            path = project_execution.write_implementation_readiness(root, issue_id)
            data = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual(path, (spec_dir / "implementation-readiness.json").resolve())
            self.assertEqual(data["schema"], "moduflow.implementation-readiness.v1")
            self.assertEqual(data["issue_id"], issue_id)


if __name__ == "__main__":
    unittest.main()
