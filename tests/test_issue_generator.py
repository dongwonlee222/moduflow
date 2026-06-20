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
            self.assertIn("- Phase: issue", content)
            self.assertIn("specs/007-oauth2-schema-setup/spec.md", content)
            self.assertIn("- [ ] Implement migration script", content)
