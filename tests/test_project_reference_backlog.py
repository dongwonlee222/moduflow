import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


project_reference_backlog = load_module(
    "project_reference_backlog",
    "scripts/project_reference_backlog.py",
)


class ReferenceBacklogEntryTests(unittest.TestCase):
    def test_build_entry_adds_traceable_defaults(self):
        entry = project_reference_backlog.build_entry(
            title="Backoffice table filters need empty state",
            source="github:webn77/ai-native-backoffice-ui/components/table",
            gap="The reference table has filter states but no empty-result example.",
            recommendation="Add empty-result Storybook and fixture examples.",
            issue_id="080-reference-improvement-backlog",
            today="2026-07-09",
        )

        self.assertEqual(entry["status"], "candidate")
        self.assertEqual(entry["priority"], "p2")
        self.assertEqual(entry["title"], "Backoffice table filters need empty state")
        self.assertEqual(entry["source_reference"], "github:webn77/ai-native-backoffice-ui/components/table")
        self.assertEqual(entry["origin_issue"], "080-reference-improvement-backlog")
        self.assertEqual(entry["origin_spec"], "specs/080-reference-improvement-backlog/spec.md")
        self.assertEqual(entry["promotion_target"], "")
        self.assertTrue(entry["id"].startswith("ref-2026-07-09-backoffice-table-filters-need-empty-state"))

    def test_render_entry_markdown_uses_stable_fields(self):
        entry = project_reference_backlog.build_entry(
            title="Reference card needs loading example",
            source="template:frontend-qa/storybook-required-states",
            gap="Loading state guidance is too implicit.",
            recommendation="Add an explicit loading row to the template.",
            issue_id="080-reference-improvement-backlog",
            today="2026-07-09",
        )

        markdown = project_reference_backlog.render_entry_markdown(entry)

        self.assertIn("### Reference card needs loading example", markdown)
        self.assertIn("- ID: `ref-2026-07-09-reference-card-needs-loading-example`", markdown)
        self.assertIn("- Status: candidate", markdown)
        self.assertIn("- Source reference: `template:frontend-qa/storybook-required-states`", markdown)
        self.assertIn("- Origin spec: `specs/080-reference-improvement-backlog/spec.md`", markdown)
        self.assertIn("**Observed gap**: Loading state guidance is too implicit.", markdown)
        self.assertIn("**Suggested improvement**: Add an explicit loading row to the template.", markdown)


class ReferenceBacklogWriteTests(unittest.TestCase):
    def test_write_entry_creates_workspace_backlog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = project_reference_backlog.build_entry(
                title="Reference table needs permission examples",
                source="github:webn77/ai-native-backoffice-ui",
                gap="Permission-denied examples are missing.",
                recommendation="Add role-specific blocked states.",
                issue_id="080-reference-improvement-backlog",
                today="2026-07-09",
            )

            result = project_reference_backlog.write_entry(root, entry)

            backlog = root / "workspace" / "reference-improvements.md"
            self.assertTrue(result["written"])
            self.assertFalse(result["duplicate"])
            self.assertEqual(Path(result["path"]), backlog)
            text = backlog.read_text(encoding="utf-8")
            self.assertIn("# Reference Improvements", text)
            self.assertIn("### Reference table needs permission examples", text)
            self.assertIn("- Source reference: `github:webn77/ai-native-backoffice-ui`", text)

    def test_write_entry_skips_duplicate_title_and_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = project_reference_backlog.build_entry(
                title="Reference table needs permission examples",
                source="github:webn77/ai-native-backoffice-ui",
                gap="Permission-denied examples are missing.",
                recommendation="Add role-specific blocked states.",
                issue_id="080-reference-improvement-backlog",
                today="2026-07-09",
            )

            first = project_reference_backlog.write_entry(root, entry)
            second = project_reference_backlog.write_entry(root, entry)

            text = (root / "workspace" / "reference-improvements.md").read_text(encoding="utf-8")
            self.assertTrue(first["written"])
            self.assertFalse(first["duplicate"])
            self.assertFalse(second["written"])
            self.assertTrue(second["duplicate"])
            self.assertEqual(text.count("### Reference table needs permission examples"), 1)


class ReferenceBacklogCliTests(unittest.TestCase):
    def test_dry_run_cli_prints_json_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = io.StringIO()

            with contextlib.redirect_stdout(out):
                code = project_reference_backlog.main([
                    str(root),
                    "--title", "Reference filters need empty state",
                    "--source", "github:webn77/ai-native-backoffice-ui",
                    "--gap", "No empty-result example.",
                    "--recommendation", "Add empty-result story and fixture.",
                    "--issue-id", "080-reference-improvement-backlog",
                    "--date", "2026-07-09",
                ])

            payload = json.loads(out.getvalue())
            self.assertEqual(code, 0)
            self.assertFalse(payload["written"])
            self.assertFalse((root / "workspace" / "reference-improvements.md").exists())
            self.assertEqual(payload["entry"]["origin_issue"], "080-reference-improvement-backlog")

    def test_write_cli_appends_backlog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = io.StringIO()

            with contextlib.redirect_stdout(out):
                code = project_reference_backlog.main([
                    str(root),
                    "--title", "Reference filters need empty state",
                    "--source", "github:webn77/ai-native-backoffice-ui",
                    "--gap", "No empty-result example.",
                    "--recommendation", "Add empty-result story and fixture.",
                    "--issue-id", "080-reference-improvement-backlog",
                    "--date", "2026-07-09",
                    "--write",
                ])

            payload = json.loads(out.getvalue())
            self.assertEqual(code, 0)
            self.assertTrue(payload["written"])
            self.assertTrue((root / "workspace" / "reference-improvements.md").exists())
