import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "issue-schema"


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectIssueSchemaParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_module(
            "project_issue_schema", "scripts/project_issue_schema.py"
        )

    def test_legacy_markdown_preserves_existing_parser_contract(self):
        issue = self.schema.parse_issue(
            FIXTURES / "legacy-markdown.md", FIXTURES
        )

        self.assertEqual(issue["schema"], "moduflow.issue.v2")
        self.assertEqual(issue["source_format"], "markdown")
        self.assertEqual(issue["lifecycle_state"], "backlog")
        self.assertEqual(issue["priority"], "p1")
        self.assertEqual(issue["blocked_by"], ["001-dependency"])

    def test_legacy_markdown_statuses_preserve_lifecycle_parity(self):
        cases = {
            "backlog": "backlog",
            "active": "active",
            "done": "done",
            "superseded-by-001-replacement": "superseded",
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "legacy-status.md"
            for status, expected in cases.items():
                with self.subTest(status=status):
                    path.write_text(
                        f"# Issue: `legacy-status` Status parity\n\n"
                        f"**Status: {status}** — created 2026-07-22.\n",
                        encoding="utf-8",
                    )
                    issue = self.schema.parse_issue(path, root)
                    self.assertEqual(issue["source_format"], "markdown")
                    self.assertEqual(issue["lifecycle_state"], expected)

    def test_versioned_canonical_state_does_not_inherit_legacy_superseded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "BIZ-106.md"
            path.write_text(
                """---
schema_version: 0.1.0
issue_id: BIZ-106
canonical_state: superseded
status: done
priority: p2
definition_readiness: ready
gate_state: pending
depends_on: []
next_command: product:status
---
# Issue: `BIZ-106` Versioned state boundary

**Status: superseded-by-BIZ-107**
""",
                encoding="utf-8",
            )

            issue = self.schema.parse_issue(path, root)

        self.assertEqual(issue["source_format"], "frontmatter-0.1.0")
        self.assertEqual(issue["lifecycle_state"], "backlog")

    def test_supported_frontmatter_fixture_parses_into_normalized_fields(self):
        issue = self.schema.parse_issue(FIXTURES / "BIZ-033.md", FIXTURES)

        self.assertEqual(issue["schema"], "moduflow.issue.v2")
        self.assertEqual(issue["source_format"], "frontmatter-0.1.0")
        self.assertEqual(issue["issue_id"], "BIZ-033")
        self.assertEqual(issue["lifecycle_state"], "active")
        self.assertEqual(issue["projection_status"], "in_progress")
        self.assertEqual(issue["blocked_by"], [])
        self.assertEqual(issue["diagnostics"], [])

    def test_versioned_contract_fixtures_are_sanitized_and_project_status(self):
        expected = {
            "BIZ-033": ("active", "in_progress", "ready", []),
            "BIZ-038": ("backlog", "ready", "ready", ["BIZ-033"]),
            "BIZ-039": ("backlog", "ready", "ready", ["BIZ-033"]),
            "BIZ-040": ("backlog", "ready", "draft", []),
        }

        for issue_id, contract in expected.items():
            with self.subTest(issue_id=issue_id):
                issue = self.schema.parse_issue(
                    FIXTURES / f"{issue_id}.md", FIXTURES
                )
                self.assertEqual(
                    (
                        issue["lifecycle_state"],
                        issue["projection_status"],
                        issue["definition_readiness"],
                        issue["blocked_by"],
                    ),
                    contract,
                )
                self.assertEqual(issue["diagnostics"], [])

    def test_frontmatter_subset_parses_supported_scalar_types_and_lists(self):
        fields, diagnostics = self.schema.parse_frontmatter_subset(
            """schema_version: \"0.1.0\"
plain: hello world
quoted: 'hello: world'
escaped_quote: 'it''s'
enabled: true
disabled: false
empty: null
count: 3
inline: [one, \"two words\", 3, false, null]
inline_escaped_quote: ['it''s', plain]
indented:
  - one
  - 'two words'
""",
            "BIZ-101",
            "issues/BIZ-101.md",
        )

        self.assertEqual(diagnostics, [])
        self.assertEqual(fields["plain"], "hello world")
        self.assertEqual(fields["quoted"], "hello: world")
        self.assertEqual(fields["escaped_quote"], "it's")
        self.assertIs(fields["enabled"], True)
        self.assertIs(fields["disabled"], False)
        self.assertIsNone(fields["empty"])
        self.assertEqual(fields["count"], 3)
        self.assertEqual(fields["inline"], ["one", "two words", 3, False, None])
        self.assertEqual(fields["inline_escaped_quote"], ["it's", "plain"])
        self.assertEqual(fields["indented"], ["one", "two words"])

    def test_malformed_frontmatter_is_reported_as_data(self):
        cases = {
            "duplicate keys": "schema_version: 0.1.0\npriority: p1\npriority: p2\n",
            "nested mappings": "schema_version: 0.1.0\nowner:\n  name: example\n",
            "anchors": "schema_version: 0.1.0\nowner: &owner example\n",
            "aliases": "schema_version: 0.1.0\nowner: *owner\n",
            "tags": "schema_version: 0.1.0\nowner: !person example\n",
            "second document": "schema_version: 0.1.0\n---\npriority: p1\n",
            "literal block scalar variant": "schema_version: 0.1.0\nnotes: |2-\n",
            "folded block scalar variant": "schema_version: 0.1.0\nnotes: >+2\n",
            "isolated single quote": "schema_version: 0.1.0\nnotes: 'a' 'b'\n",
        }

        for label, frontmatter in cases.items():
            with self.subTest(case=label):
                fields, diagnostics = self.schema.parse_frontmatter_subset(
                    frontmatter, "BIZ-102", "issues/BIZ-102.md"
                )
                self.assertIsInstance(fields, dict)
                self.assertTrue(
                    any(
                        diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
                        for diagnostic in diagnostics
                    ),
                    diagnostics,
                )

    def test_duplicate_key_cannot_replace_an_earlier_malformed_value(self):
        fields, diagnostics = self.schema.parse_frontmatter_subset(
            "schema_version: 0.1.0\npriority: [p1\npriority: p0\n",
            "BIZ-102",
            "issues/BIZ-102.md",
        )

        self.assertNotEqual(fields.get("priority"), "p0")
        self.assertTrue(
            any(
                diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
                and "duplicate key" in diagnostic["message"]
                for diagnostic in diagnostics
            )
        )

    def test_nested_list_structures_are_rejected_without_populating_field(self):
        cases = {
            "nested sequence": "  - - child\n",
            "terminal mapping colon": "  - name:\n",
            "child indentation": "  - parent\n    - child\n",
            "explicit mapping indicator": "  - ? name\n",
        }
        contract_prefix = """schema_version: 0.1.0
issue_id: BIZ-105
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: pending
depends_on:
"""
        contract_suffix = "next_command: product:execute BIZ-105\n"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "BIZ-105.md"
            for label, nested_value in cases.items():
                with self.subTest(case=label):
                    frontmatter = contract_prefix + nested_value + contract_suffix
                    fields, diagnostics = self.schema.parse_frontmatter_subset(
                        frontmatter, "BIZ-105", "BIZ-105.md"
                    )
                    self.assertNotIn("depends_on", fields)
                    self.assertTrue(
                        any(
                            diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
                            for diagnostic in diagnostics
                        ),
                        diagnostics,
                    )

                    path.write_text(
                        f"---\n{frontmatter}---\n"
                        "# Issue: `BIZ-105` Nested YAML\n\n**Status: backlog**\n",
                        encoding="utf-8",
                    )
                    issue = self.schema.parse_issue(path, root)
                    self.assertEqual(issue["blocked_by"], [])
                    self.assertTrue(
                        any(
                            diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
                            for diagnostic in issue["diagnostics"]
                        ),
                        issue["diagnostics"],
                    )

    def test_malformed_issue_file_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "BIZ-102.md"
            path.write_text(
                "---\nschema_version: 0.1.0\npriority: p1\npriority: p2\n---\n"
                "# Issue: `BIZ-102` Malformed\n\n**Status: backlog**\n",
                encoding="utf-8",
            )

            issue = self.schema.parse_issue(path, root)

        self.assertTrue(
            any(
                diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
                for diagnostic in issue["diagnostics"]
            )
        )

    def test_unknown_scalar_fields_are_isolated_in_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "BIZ-103.md"
            path.write_text(
                """---
schema_version: 0.1.0
issue_id: BIZ-103
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: pending
depends_on: []
next_command: product:execute BIZ-103
lifecycle_state: done
recommended_next_command: product:execute BIZ-999
custom_flag: true
---
# Issue: `BIZ-103` Extension isolation

**Status: backlog**
""",
                encoding="utf-8",
            )

            issue = self.schema.parse_issue(path, root)

        self.assertEqual(issue["lifecycle_state"], "backlog")
        self.assertNotEqual(
            issue.get("recommended_next_command"), "product:execute BIZ-999"
        )
        self.assertEqual(
            issue["extensions"],
            {
                "lifecycle_state": "done",
                "recommended_next_command": "product:execute BIZ-999",
                "custom_flag": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
