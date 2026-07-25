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

issue_generator = load_module("issue_generator", "scripts/issue_generator.py")
project_issue_schema = load_module(
    "project_issue_schema_generator", "scripts/project_issue_schema.py"
)

class IssueGeneratorTests(unittest.TestCase):
    def test_get_next_issue_number_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            num = issue_generator.get_next_issue_number(Path(tmp) / "issues")
            self.assertEqual(num, 1)

    def test_get_next_issue_number_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues_dir = Path(tmp) / "issues"
            issues_dir.mkdir()
            (issues_dir / "001-some-test.md").write_text("# Test", encoding="utf-8")
            (issues_dir / "005-another-test.md").write_text("# Test", encoding="utf-8")
            
            num = issue_generator.get_next_issue_number(issues_dir)
            self.assertEqual(num, 6)

    def test_format_issue_filename(self):
        filename = issue_generator.format_issue_filename(42, "Setup DB & Auth Service!!")
        self.assertEqual(filename, "042-setup-db-auth-service.md")

    def test_generate_issues_from_goal(self):
        issues = issue_generator.generate_issues_from_goal("OAuth2 Integration", search_mock_data="OAuth2 RFC standards")
        self.assertEqual(len(issues), 3)
        self.assertIn("Setup database schema and auth scope for OAuth2 Integration", issues[0]["title"])
        self.assertIn("OAuth2 RFC standards", issues[0]["opportunity"])

    def test_write_issue_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_data = {
                "title": "OAuth2 Schema setup",
                "summary": "Setup OAuth2 Schema.",
                "opportunity": "Needed for security.",
                "scope_in": ["DB table creation"],
                "scope_out": ["Frontend UI"],
                "acceptance_criteria": ["Migrate exit code 0"],
                "tasks": ["Implement migration script"]
            }
            file_path = issue_generator.write_issue_file(root, 7, issue_data)
            self.assertTrue(file_path.exists())
            
            content = file_path.read_text(encoding="utf-8")
            self.assertIn("# Issue 007: OAuth2 Schema setup", content)
            self.assertIn(
                "**Status: backlog** — created "
                f"{issue_generator.date.today().isoformat()}.\n"
                "**Priority: p2**\n"
                "**Blocked-by:**",
                content,
            )
            self.assertNotIn("## Lifecycle", content)
            self.assertNotIn("specs/007-oauth2-schema-setup/spec.md", content)
            self.assertIn("`specs/<issue-id>/spec.md`", content)
            self.assertIn("`specs/<issue-id>/plan.md`", content)
            self.assertIn("- [ ] Implement migration script", content)

            parsed = project_issue_schema.parse_issue(file_path, root)
            self.assertEqual(parsed["source_format"], "markdown")
            self.assertEqual(parsed["lifecycle_state"], "backlog")
            self.assertEqual(parsed["priority"], "p2")
            self.assertEqual(parsed["diagnostics"], [])

    def test_write_issue_file_links_existing_workflow_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_slug = "007-oauth2-schema-setup"
            artifact_root = root / "specs" / issue_slug
            artifact_root.mkdir(parents=True)
            (artifact_root / "spec.md").write_text("# Spec\n", encoding="utf-8")
            issue_data = {
                "title": "OAuth2 Schema setup",
                "summary": "Setup OAuth2 Schema.",
                "opportunity": "Needed for security.",
                "scope_in": ["DB table creation"],
                "scope_out": ["Frontend UI"],
                "acceptance_criteria": ["Migrate exit code 0"],
                "tasks": ["Implement migration script"],
            }

            file_path = issue_generator.write_issue_file(root, 7, issue_data)
            content = file_path.read_text(encoding="utf-8")

            self.assertIn(f"`specs/{issue_slug}/spec.md`", content)
            self.assertIn("`specs/<issue-id>/plan.md`", content)
            self.assertNotIn(f"`specs/{issue_slug}/plan.md`", content)

    def test_issue_template_keeps_canonical_markdown_header(self):
        content = (ROOT / "templates" / "issues" / "issue.md").read_text(
            encoding="utf-8"
        )

        self.assertFalse(content.startswith("---\n"))
        self.assertIn(
            "**Status: backlog** — created {{created_date}}.\n"
            "**Priority: p2**\n"
            "**Blocked-by:**",
            content,
        )
        self.assertIn("`specs/<issue-id>/spec.md`", content)
        self.assertIn("`specs/<issue-id>/plan.md`", content)
        self.assertIn("- Status: `specs/<issue-id>/status.md`", content)
