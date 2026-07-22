import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "issue-schema"


def codes(issue):
    return {diagnostic["code"] for diagnostic in issue["diagnostics"]}


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
            "BIZ-033": ("active", "in_progress", "ready", [], set()),
            "BIZ-038": (
                "backlog",
                "ready",
                "ready",
                ["BIZ-033"],
                {"ISSUE_AUX_STATUS_INVALID"},
            ),
            "BIZ-039": (
                "backlog",
                "ready",
                "ready",
                ["BIZ-033"],
                {"ISSUE_AUX_STATUS_INVALID"},
            ),
            "BIZ-040": (
                "backlog",
                "ready",
                "draft",
                [],
                {"ISSUE_AUX_STATUS_INVALID"},
            ),
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
                        codes(issue),
                    ),
                    contract,
                )

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


class ProjectIssueSchemaAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_module(
            "project_issue_schema_adapters", "scripts/project_issue_schema.py"
        )

    def write_issue(self, root, name, content):
        path = root / name
        path.write_text(content, encoding="utf-8")
        return self.schema.parse_issue(path, root)

    def test_dispatches_all_compatibility_rows_conservatively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markdown = self.write_issue(
                root,
                "markdown.md",
                "# Issue: `markdown` Markdown\n\n**Status: backlog**\n",
            )
            versioned = self.write_issue(
                root,
                "BIZ-201.md",
                """---
schema_version: 0.1.0
issue_id: BIZ-201
canonical_state: active
status: in_progress
priority: p1
definition_readiness: ready
gate_state: pending
phase: implementation
depends_on: []
next_command: product:status
custom_flag: true
---
# Issue: `BIZ-201` Versioned

**Status: active**
""",
            )
            unversioned = self.write_issue(
                root,
                "BIZ-202.md",
                """---
issue_id: BIZ-202-OVERRIDE
canonical_state: active
status: in_progress
priority: p0
definition_readiness: ready
gate_state: passed
phase: implementation
depends_on: [BIZ-200]
next_command: product:execute BIZ-202
custom_flag: true
---
# Issue: `BIZ-202` Unversioned

**Status: backlog**
**Priority: p3**
**Blocked-by: `BIZ-199`**
""",
            )
            unsupported = self.write_issue(
                root,
                "BIZ-203.md",
                """---
schema_version: 9.9.9
issue_id: BIZ-203
canonical_state: done
status: done
priority: p0
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:execute BIZ-203
---
# Issue: `BIZ-203` Unsupported

**Status: done**
""",
            )

        self.assertEqual(markdown["source_format"], "markdown")
        self.assertEqual(versioned["source_format"], "frontmatter-0.1.0")
        self.assertEqual(versioned["lifecycle_state"], "active")
        self.assertEqual(versioned["declared_phase"], "implementation")
        self.assertEqual(versioned["extensions"], {"custom_flag": True})

        self.assertEqual(unversioned["source_format"], "frontmatter-unversioned")
        self.assertEqual(unversioned["lifecycle_state"], "backlog")
        self.assertEqual(unversioned["priority"], "p3")
        self.assertEqual(unversioned["blocked_by"], ["BIZ-199"])
        self.assertEqual(unversioned["advisory_blocked_by"], ["BIZ-200"])
        self.assertIsNone(unversioned["definition_readiness"])
        self.assertIsNone(unversioned["declared_next_command"])
        self.assertEqual(unversioned["extensions"], {"custom_flag": True})
        self.assertIn("ISSUE_FRONTMATTER_UNVERSIONED", codes(unversioned))

        self.assertEqual(unsupported["source_format"], "frontmatter-unsupported")
        self.assertEqual(unsupported["lifecycle_state"], "backlog")
        self.assertEqual(unsupported["readiness"], "blocked")
        self.assertIsNone(unsupported["declared_next_command"])
        self.assertIn("ISSUE_SCHEMA_UNSUPPORTED", codes(unsupported))

        for issue, code in (
            (unversioned, "ISSUE_FRONTMATTER_UNVERSIONED"),
            (unsupported, "ISSUE_SCHEMA_UNSUPPORTED"),
        ):
            diagnostic = next(
                item for item in issue["diagnostics"] if item["code"] == code
            )
            self.assertGreaterEqual(
                diagnostic.keys(),
                {
                    "code",
                    "severity",
                    "issue_id",
                    "source_path",
                    "field",
                    "current",
                    "expected",
                    "message",
                    "recommendation",
                },
            )

    def test_versioned_markdown_status_must_match_canonical_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue = self.write_issue(
                Path(tmp),
                "BIZ-204.md",
                """---
schema_version: 0.1.0
issue_id: BIZ-204
canonical_state: active
status: in_progress
depends_on: []
---
# Issue: `BIZ-204` State drift

**Status: backlog**
""",
            )

        self.assertEqual(issue["lifecycle_state"], "active")
        self.assertIn("ISSUE_STATE_PROJECTION_MISMATCH", codes(issue))

    def test_versioned_ready_auxiliary_status_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue = self.write_issue(
                Path(tmp),
                "BIZ-205.md",
                """---
schema_version: 0.1.0
issue_id: BIZ-205
canonical_state: backlog
status: ready
depends_on: []
---
# Issue: `BIZ-205` Invalid auxiliary status

**Status: backlog**
""",
            )

        self.assertIn("ISSUE_AUX_STATUS_INVALID", codes(issue))

    def test_versioned_dependency_projection_must_match_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue = self.write_issue(
                Path(tmp),
                "BIZ-206.md",
                """---
schema_version: 0.1.0
issue_id: BIZ-206
canonical_state: backlog
status: backlog
depends_on: [BIZ-200, BIZ-201]
---
# Issue: `BIZ-206` Dependency drift

**Status: backlog**
**Blocked-by: `BIZ-200`, `BIZ-202`**
""",
            )

        self.assertEqual(issue["blocked_by"], ["BIZ-200", "BIZ-201"])
        self.assertIn("ISSUE_DEPENDENCY_PROJECTION_MISMATCH", codes(issue))


if __name__ == "__main__":
    unittest.main()
