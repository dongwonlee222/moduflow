import contextlib
import hashlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "issue-schema"
REQUIRED_DIAGNOSTIC_KEYS = {
    "code",
    "severity",
    "issue_id",
    "source_path",
    "field",
    "current",
    "expected",
    "message",
    "recommendation",
}


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
            "backlog": ("backlog", None),
            "active": ("active", None),
            "done": ("done", None),
            "superseded-by-001-replacement": (
                "superseded",
                "001-replacement",
            ),
            "superseded-by-BIZ-107": ("superseded", "BIZ-107"),
            "superseded-by-": ("superseded", None),
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "legacy-status.md"
            for status, (expected, superseded_by) in cases.items():
                with self.subTest(status=status):
                    path.write_text(
                        f"# Issue: `legacy-status` Status parity\n\n"
                        f"**Status: {status}** — created 2026-07-22.\n",
                        encoding="utf-8",
                    )
                    issue = self.schema.parse_issue(path, root)
                    self.assertEqual(issue["source_format"], "markdown")
                    self.assertEqual(issue["lifecycle_state"], expected)
                    self.assertEqual(issue["superseded_by"], superseded_by)

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
        self.assertIsNone(issue["superseded_by"])

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

    def test_unreadable_issue_fails_closed_with_actionable_source_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "BIZ-UNREADABLE.md"
            path.write_bytes(b"\xff\xfe\x00\x80")

            issue = self.schema.parse_issue(path, root)

        self.assertIsNone(issue["lifecycle_state"])
        self.assertEqual(issue["readiness"], "blocked")
        diagnostic = next(
            item
            for item in issue["diagnostics"]
            if item["code"] == "ISSUE_SOURCE_UNREADABLE"
        )
        self.assertEqual(diagnostic["severity"], "error")
        self.assertIn("read", diagnostic["recommendation"].lower())
        self.assertIn("permission", diagnostic["recommendation"].lower())
        self.assertIn("UTF-8", diagnostic["recommendation"])
        self.assertNotIn("frontmatter", diagnostic["recommendation"].lower())

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
        self.assertIsNone(unsupported["lifecycle_state"])
        self.assertIsNone(unsupported["projection_status"])
        self.assertEqual(unsupported["blocked_by"], [])
        self.assertEqual(unsupported["advisory_blocked_by"], [])
        self.assertIsNone(unsupported["definition_readiness"])
        self.assertIsNone(unsupported["gate_state"])
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

    def test_versioned_markdown_status_requires_explicit_lifecycle_word(self):
        cases = {
            "missing": ("", None),
            "unknown": ("**Status: nonsense**\n", "nonsense"),
            "auxiliary": ("**Status: in_progress**\n", "in_progress"),
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label, (markdown_line, expected_current) in cases.items():
                with self.subTest(case=label):
                    issue = self.write_issue(
                        root,
                        f"BIZ-204-{label}.md",
                        f"""---
schema_version: 0.1.0
issue_id: BIZ-204-{label}
canonical_state: backlog
status: backlog
depends_on: []
---
# Issue: `BIZ-204-{label}` Raw status projection

{markdown_line}""",
                    )

                    diagnostic = next(
                        (
                            item
                            for item in issue["diagnostics"]
                            if item["code"] == "ISSUE_STATE_PROJECTION_MISMATCH"
                            and item["field"] == "markdown_status"
                        ),
                        None,
                    )
                    self.assertIsNotNone(diagnostic, issue["diagnostics"])
                    self.assertEqual(diagnostic["current"], expected_current)
                    self.assertEqual(diagnostic["expected"], "backlog")

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

    def test_invalid_depends_on_types_fail_closed_for_frontmatter_adapters(self):
        cases = {
            "scalar": ("BIZ-033", "BIZ-033"),
            "integer": ("2", 2),
            "mapping-like": ("{issue: BIZ-033}", "{issue: BIZ-033}"),
            "mixed-list": ("[BIZ-033, 2]", ["BIZ-033", 2]),
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source_format in ("versioned", "unversioned"):
                for label, (declared_value, expected_current) in cases.items():
                    with self.subTest(source_format=source_format, case=label):
                        schema_line = (
                            "schema_version: 0.1.0\n"
                            if source_format == "versioned"
                            else ""
                        )
                        issue = self.write_issue(
                            root,
                            f"BIZ-207-{source_format}-{label}.md",
                            f"""---
{schema_line}issue_id: BIZ-207-{source_format}-{label}
canonical_state: backlog
status: backlog
depends_on: {declared_value}
---
# Issue: `BIZ-207-{source_format}-{label}` Invalid dependency type

**Status: backlog**
**Blocked-by: `BIZ-099`**
""",
                        )

                        diagnostic = next(
                            (
                                item
                                for item in issue["diagnostics"]
                                if item["code"] == "ISSUE_SCHEMA_MALFORMED"
                                and item["field"] == "depends_on"
                            ),
                            None,
                        )
                        self.assertIsNotNone(diagnostic, issue["diagnostics"])
                        self.assertEqual(diagnostic["severity"], "error")
                        self.assertEqual(diagnostic["current"], expected_current)
                        self.assertTrue(diagnostic["expected"])
                        self.assertIn("top-level", diagnostic["recommendation"])
                        self.assertGreaterEqual(
                            diagnostic.keys(), REQUIRED_DIAGNOSTIC_KEYS
                        )

                        if source_format == "versioned":
                            self.assertEqual(issue["blocked_by"], [])
                        else:
                            self.assertEqual(issue["blocked_by"], ["BIZ-099"])
                            self.assertEqual(issue["advisory_blocked_by"], [])

    def test_list_typed_state_fields_are_diagnostics_not_exceptions(self):
        for field in ("canonical_state", "status"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                values = {
                    "canonical_state": "backlog",
                    "status": "backlog",
                }
                values[field] = "[backlog]"
                issue = self.write_issue(
                    Path(tmp),
                    f"BIZ-208-{field}.md",
                    f"""---
schema_version: 0.1.0
issue_id: BIZ-208-{field}
canonical_state: {values['canonical_state']}
status: {values['status']}
depends_on: []
---
# Issue: `BIZ-208-{field}` Invalid state type

**Status: backlog**
""",
                )

                diagnostic = next(
                    item
                    for item in issue["diagnostics"]
                    if item["code"] == "ISSUE_SCHEMA_MALFORMED"
                    and item["field"] == field
                )
                self.assertEqual(set(diagnostic), REQUIRED_DIAGNOSTIC_KEYS)
                self.assertEqual(diagnostic["severity"], "error")
                self.assertEqual(diagnostic["current"], ["backlog"])
                self.assertEqual(diagnostic["expected"], "string")
                self.assertEqual(
                    [
                        (item["code"], item["field"])
                        for item in issue["diagnostics"]
                    ],
                    [("ISSUE_SCHEMA_MALFORMED", field)],
                )

    def test_invalid_auxiliary_status_is_independent_of_canonical_validity(self):
        cases = {
            "list-ready": (
                "[backlog]",
                "ready",
                "ISSUE_SCHEMA_MALFORMED",
            ),
            "null-blocked": (
                "null",
                "blocked",
                "ISSUE_SCHEMA_MALFORMED",
            ),
            "unknown-nonsense": (
                "nonsense",
                "nonsense",
                "ISSUE_STATE_PROJECTION_MISMATCH",
            ),
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label, (canonical_state, status, primary_code) in cases.items():
                with self.subTest(case=label):
                    issue = self.write_issue(
                        root,
                        f"BIZ-211-{label}.md",
                        f"""---
schema_version: 0.1.0
issue_id: BIZ-211-{label}
canonical_state: {canonical_state}
status: {status}
depends_on: []
---
# Issue: `BIZ-211-{label}` Independent auxiliary validation

**Status: backlog**
""",
                    )

                    self.assertTrue(
                        any(
                            item["code"] == primary_code
                            and item["field"] == "canonical_state"
                            for item in issue["diagnostics"]
                        ),
                        issue["diagnostics"],
                    )
                    auxiliary = next(
                        (
                            item
                            for item in issue["diagnostics"]
                            if item["code"] == "ISSUE_AUX_STATUS_INVALID"
                        ),
                        None,
                    )
                    self.assertIsNotNone(auxiliary, issue["diagnostics"])
                    self.assertEqual(auxiliary["field"], "status")
                    self.assertEqual(auxiliary["current"], status)
                    self.assertEqual(
                        auxiliary["expected"],
                        "backlog, in_progress, or done",
                    )
                    self.assertFalse(
                        any(
                            item["code"] == "ISSUE_STATE_PROJECTION_MISMATCH"
                            and item["field"] == "status"
                            for item in issue["diagnostics"]
                        ),
                        issue["diagnostics"],
                    )

    def test_other_scalar_contract_fields_reject_list_values(self):
        scalar_fields = (
            "schema_version",
            "issue_id",
            "priority",
            "definition_readiness",
            "gate_state",
            "phase",
            "declared_phase",
            "next_command",
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for field in scalar_fields:
                with self.subTest(field=field):
                    values = {
                        "schema_version": "0.1.0",
                        "issue_id": f"BIZ-209-{field}",
                        "priority": "p2",
                        "definition_readiness": "ready",
                        "gate_state": "pending",
                        "phase": "implementation",
                        "next_command": "product:status",
                    }
                    if field == "declared_phase":
                        values.pop("phase")
                    values[field] = "[invalid]"
                    frontmatter = "\n".join(
                        f"{key}: {value}" for key, value in values.items()
                    )
                    issue = self.write_issue(
                        root,
                        f"BIZ-209-{field}.md",
                        f"""---
{frontmatter}
canonical_state: backlog
status: backlog
depends_on: []
---
# Issue: `BIZ-209-{field}` Invalid scalar contract field

**Status: backlog**
""",
                    )

                    diagnostic = next(
                        item
                        for item in issue["diagnostics"]
                        if item["code"] == "ISSUE_SCHEMA_MALFORMED"
                        and item["field"] == field
                    )
                    self.assertEqual(diagnostic["current"], ["invalid"])
                    self.assertEqual(diagnostic["expected"], "string")
                    self.assertEqual(diagnostic["severity"], "error")

    def test_equivalent_dependency_projection_ignores_order_and_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue = self.write_issue(
                Path(tmp),
                "BIZ-210.md",
                """---
schema_version: 0.1.0
issue_id: BIZ-210
canonical_state: backlog
status: backlog
depends_on: [BIZ-201, BIZ-200, BIZ-201]
---
# Issue: `BIZ-210` Equivalent dependencies

**Status: backlog**
**Blocked-by: `BIZ-200`, `BIZ-201`, `BIZ-200`**
""",
            )

        self.assertEqual(issue["blocked_by"], ["BIZ-201", "BIZ-200"])
        self.assertNotIn("ISSUE_DEPENDENCY_PROJECTION_MISMATCH", codes(issue))


class ProjectIssueSchemaEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_module(
            "project_issue_schema_evaluation", "scripts/project_issue_schema.py"
        )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "issues").mkdir()

    def write_versioned(
        self,
        issue_id,
        *,
        lifecycle="backlog",
        definition="ready",
        gate="passed",
        dependencies=(),
        next_command=None,
        status=None,
        markdown_status=None,
        phase=None,
    ):
        status = status or {
            "backlog": "backlog",
            "active": "in_progress",
            "done": "done",
        }[lifecycle]
        markdown_status = markdown_status or lifecycle
        next_command = next_command or f"product:execute {issue_id}"
        dependency_text = ", ".join(dependencies)
        definition_line = (
            f"definition_readiness: {definition}\n" if definition is not None else ""
        )
        gate_line = f"gate_state: {gate}\n" if gate is not None else ""
        phase_line = f"phase: {phase}\n" if phase is not None else ""
        path = self.root / "issues" / f"{issue_id}.md"
        path.write_text(
            f"""---
schema_version: 0.1.0
issue_id: {issue_id}
canonical_state: {lifecycle}
status: {status}
priority: p2
{definition_line}{gate_line}{phase_line}depends_on: [{dependency_text}]
next_command: {next_command}
---
# Issue: `{issue_id}` Evaluator fixture

**Status: {markdown_status}** — created 2026-07-22.
""",
            encoding="utf-8",
        )
        return path

    def write_markdown(self, issue_id, status="backlog", dependencies=()):
        blocked = (
            f"\n**Blocked-by: {', '.join(dependencies)}**" if dependencies else ""
        )
        path = self.root / "issues" / f"{issue_id}.md"
        path.write_text(
            f"# Issue: `{issue_id}` Markdown fixture\n\n"
            f"**Status: {status}** — created 2026-07-22.{blocked}\n",
            encoding="utf-8",
        )
        return path

    def add_artifacts(self, issue_id, *names):
        artifact_root = self.root / "specs" / issue_id
        artifact_root.mkdir(parents=True, exist_ok=True)
        for name in names:
            (artifact_root / f"{name}.md").write_text(
                f"# {name.title()}\n", encoding="utf-8"
            )

    def evaluated_by_id(self):
        return {
            issue["issue_id"]: issue
            for issue in self.schema.evaluate_project(self.root)["issues"]
        }

    def test_evaluate_project_respects_configured_issue_and_spec_paths(self):
        (self.root / ".moduflow").mkdir()
        (self.root / ".moduflow" / "config.json").write_text(
            json.dumps(
                {
                    "schema": "moduflow.config.v1",
                    "paths": {
                        "issues": "projects/billing/issues",
                        "specs": "projects/billing/specs",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        custom_issues = self.root / "projects" / "billing" / "issues"
        custom_issues.mkdir(parents=True)
        (custom_issues / "BIZ-CUSTOM.md").write_text(
            """---
schema_version: 0.1.0
issue_id: BIZ-CUSTOM
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:execute BIZ-CUSTOM
---
# Custom issue

**Status: backlog** — created 2026-07-25.
""",
            encoding="utf-8",
        )
        artifact_root = (
            self.root / "projects" / "billing" / "specs" / "BIZ-CUSTOM"
        )
        artifact_root.mkdir(parents=True)
        for name in ("spec", "plan", "tasks"):
            (artifact_root / f"{name}.md").write_text(
                f"# {name}\n", encoding="utf-8"
            )

        project = self.schema.evaluate_project(self.root)

        self.assertEqual(len(project["issues"]), 1)
        issue = project["issues"][0]
        self.assertEqual(issue["issue_id"], "BIZ-CUSTOM")
        self.assertEqual(
            issue["source_path"],
            "projects/billing/issues/BIZ-CUSTOM.md",
        )
        self.assertEqual(issue["artifact_phase"], "tasks")
        self.assertEqual(issue["readiness"], "ready")
        self.assertEqual(
            issue["recommended_next_command"],
            "product:execute BIZ-CUSTOM",
        )

    def test_evaluate_project_reports_configured_paths_outside_root(self):
        base = self.root.parent
        outside_issues = base / f"{self.root.name}-outside-issues"
        outside_issues.mkdir(exist_ok=True)
        self.addCleanup(
            lambda: outside_issues.rmdir()
            if outside_issues.exists() and not any(outside_issues.iterdir())
            else None
        )
        (outside_issues / "BIZ-OUTSIDE.md").write_text(
            "# Outside\n\n**Status: backlog** — created.\n",
            encoding="utf-8",
        )
        self.addCleanup(
            lambda: (outside_issues / "BIZ-OUTSIDE.md").unlink(missing_ok=True)
        )
        (self.root / ".moduflow").mkdir()
        (self.root / ".moduflow" / "config.json").write_text(
            json.dumps(
                {
                    "schema": "moduflow.config.v1",
                    "paths": {
                        "issues": f"../{outside_issues.name}",
                        "specs": "/tmp/outside-specs",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

        configured_paths = self.schema.configured_project_paths(self.root)
        project = self.schema.evaluate_project(self.root)

        self.assertEqual(configured_paths["issues"], "issues")
        self.assertEqual(configured_paths["specs"], "specs")
        self.assertEqual(len(project["issues"]), 1)
        issue = project["issues"][0]
        self.assertEqual(issue["issue_id"], "project-issues-root")
        self.assertIn("ISSUE_SOURCE_OUTSIDE_ROOT", codes(issue))
        self.assertEqual(issue["recommended_next_command"], "product:doctor")
        self.assertNotIn("Outside", json.dumps(project))

    def test_evaluate_project_reports_absolute_configured_issues_path(self):
        outside_issues = self.root.parent / f"{self.root.name}-absolute-issues"
        outside_issues.mkdir()
        self.addCleanup(lambda: shutil.rmtree(outside_issues))
        (outside_issues / "BIZ-ABSOLUTE.md").write_text(
            "# DO-NOT-EXPOSE-ABSOLUTE-ISSUE\n",
            encoding="utf-8",
        )
        (self.root / ".moduflow").mkdir()
        (self.root / ".moduflow" / "config.json").write_text(
            json.dumps(
                {
                    "schema": "moduflow.config.v1",
                    "paths": {"issues": str(outside_issues)},
                }
            )
            + "\n",
            encoding="utf-8",
        )

        project = self.schema.evaluate_project(self.root)
        issue = project["issues"][0]

        self.assertEqual(issue["issue_id"], "project-issues-root")
        self.assertIn("ISSUE_SOURCE_OUTSIDE_ROOT", codes(issue))
        self.assertNotIn("DO-NOT-EXPOSE", json.dumps(project))

    def test_evaluate_project_reports_external_issues_root_symlink(self):
        base = self.root.parent
        outside_issues = base / f"{self.root.name}-symlink-issues"
        outside_issues.mkdir()
        self.addCleanup(lambda: shutil.rmtree(outside_issues))
        (outside_issues / "BIZ-ROOT-LINK.md").write_text(
            "# DO-NOT-EXPOSE-ROOT-LINK\n",
            encoding="utf-8",
        )
        (self.root / "issues").rmdir()
        (self.root / "issues").symlink_to(
            outside_issues,
            target_is_directory=True,
        )

        project = self.schema.evaluate_project(self.root)
        issue = project["issues"][0]

        self.assertEqual(issue["issue_id"], "project-issues-root")
        self.assertEqual(issue["source_path"], "issues")
        self.assertIn("ISSUE_SOURCE_OUTSIDE_ROOT", codes(issue))
        self.assertEqual(issue["recommended_next_command"], "product:doctor")
        self.assertNotIn("DO-NOT-EXPOSE", json.dumps(project))

    def test_missing_or_empty_default_issues_root_remains_safe_and_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_root = Path(tmp) / "missing"
            missing_root.mkdir()
            missing = self.schema.evaluate_project(missing_root)

            empty_root = Path(tmp) / "empty"
            (empty_root / "issues").mkdir(parents=True)
            empty = self.schema.evaluate_project(empty_root)

        self.assertEqual(missing["issues"], [])
        self.assertEqual(empty["issues"], [])

    def test_sanitized_biz_fixtures_apply_project_level_routing(self):
        for issue_id in ("BIZ-033", "BIZ-038", "BIZ-039", "BIZ-040"):
            shutil.copy2(
                FIXTURES / f"{issue_id}.md",
                self.root / "issues" / f"{issue_id}.md",
            )

        by_id = self.evaluated_by_id()

        self.assertEqual(by_id["BIZ-033"]["lifecycle_state"], "active")
        self.assertEqual(by_id["BIZ-038"]["readiness"], "blocked")
        self.assertIn("ISSUE_AUX_STATUS_INVALID", codes(by_id["BIZ-038"]))
        self.assertIn("ISSUE_DEPENDENCY_UNMET", codes(by_id["BIZ-038"]))
        for issue_id in ("BIZ-038", "BIZ-039"):
            unmet = next(
                diagnostic
                for diagnostic in by_id[issue_id]["diagnostics"]
                if diagnostic["code"] == "ISSUE_DEPENDENCY_UNMET"
            )
            self.assertEqual(unmet["severity"], "error")
        self.assertEqual(
            by_id["BIZ-039"]["recommended_next_command"], "product:status"
        )
        self.assertEqual(
            by_id["BIZ-040"]["recommended_next_command"],
            "product:spec BIZ-040",
        )

    def test_invalid_auxiliary_status_routes_doctor_instead_of_execute(self):
        for label, status in (
            ("READY", "ready"),
            ("BLOCKED", "blocked"),
            ("UNKNOWN", "nonsense"),
        ):
            issue_id = f"BIZ-AUX-{label}"
            self.write_versioned(issue_id, status=status)
            self.add_artifacts(issue_id, "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        for issue_id in ("BIZ-AUX-READY", "BIZ-AUX-BLOCKED", "BIZ-AUX-UNKNOWN"):
            with self.subTest(issue_id=issue_id):
                issue = by_id[issue_id]
                self.assertIn("ISSUE_AUX_STATUS_INVALID", codes(issue))
                self.assertEqual(issue["readiness"], "blocked")
                self.assertEqual(
                    issue["recommended_next_command"], "product:doctor"
                )

    def test_dependency_route_precedes_invalid_auxiliary_status(self):
        self.write_versioned("BIZ-AUX-BLOCKER")
        self.write_versioned(
            "BIZ-AUX-DEPENDENCY",
            status="ready",
            dependencies=("BIZ-AUX-BLOCKER",),
        )
        self.add_artifacts("BIZ-AUX-DEPENDENCY", "spec", "plan", "tasks")

        issue = self.evaluated_by_id()["BIZ-AUX-DEPENDENCY"]

        self.assertIn("ISSUE_AUX_STATUS_INVALID", codes(issue))
        self.assertIn("ISSUE_DEPENDENCY_UNMET", codes(issue))
        self.assertEqual(issue["readiness"], "blocked")
        self.assertEqual(issue["recommended_next_command"], "product:status")

    def test_structural_recovery_routes_precede_invalid_auxiliary_status(self):
        self.write_versioned(
            "BIZ-AUX-DEFINITION", status="ready", definition="draft"
        )
        self.write_versioned("BIZ-AUX-ARTIFACT", status="ready")
        self.write_versioned(
            "BIZ-AUX-PHASE", status="ready", phase="release"
        )
        self.add_artifacts("BIZ-AUX-PHASE", "spec", "plan", "tasks")
        self.write_versioned(
            "BIZ-AUX-GATE", status="ready", gate="pending"
        )
        self.add_artifacts("BIZ-AUX-GATE", "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        expected = {
            "BIZ-AUX-DEFINITION": "product:spec BIZ-AUX-DEFINITION",
            "BIZ-AUX-ARTIFACT": "product:spec BIZ-AUX-ARTIFACT",
            "BIZ-AUX-PHASE": "product:doctor",
            "BIZ-AUX-GATE": "product:review BIZ-AUX-GATE",
        }
        for issue_id, command in expected.items():
            with self.subTest(issue_id=issue_id):
                self.assertIn("ISSUE_AUX_STATUS_INVALID", codes(by_id[issue_id]))
                self.assertEqual(
                    by_id[issue_id]["recommended_next_command"], command
                )

    def test_duplicate_issue_ids_are_isolated_and_route_doctor(self):
        first = self.write_versioned("BIZ-DUPLICATE")
        first.rename(self.root / "issues" / "first.md")
        second = self.write_versioned("BIZ-DUPLICATE")
        second.rename(self.root / "issues" / "second.md")
        self.add_artifacts("BIZ-DUPLICATE", "spec", "plan", "tasks")

        project = self.schema.evaluate_project(self.root)
        duplicates = [
            issue
            for issue in project["issues"]
            if issue["issue_id"] == "BIZ-DUPLICATE"
        ]

        self.assertEqual(len(duplicates), 2)
        self.assertEqual(project["dependency_diagnostics"], {})
        expected_paths = ["issues/first.md", "issues/second.md"]
        self.assertEqual(
            sorted(issue["source_path"] for issue in duplicates), expected_paths
        )
        for issue in duplicates:
            with self.subTest(source_path=issue["source_path"]):
                duplicate = next(
                    diagnostic
                    for diagnostic in issue["diagnostics"]
                    if diagnostic["code"] == "ISSUE_DUPLICATE_FIELD"
                )
                self.assertEqual(duplicate["field"], "issue_id")
                self.assertEqual(duplicate["current"], expected_paths)
                self.assertEqual(duplicate["expected"], "a unique issue id")
                self.assertEqual(duplicate["source_path"], issue["source_path"])
                self.assertTrue(
                    all(
                        diagnostic["source_path"] == issue["source_path"]
                        for diagnostic in issue["diagnostics"]
                    )
                )
                self.assertEqual(issue["readiness"], "blocked")
                self.assertEqual(
                    issue["recommended_next_command"], "product:doctor"
                )

    def test_dependency_on_duplicate_issue_id_reports_ambiguous_target(self):
        first = self.write_versioned("BIZ-AMBIGUOUS")
        first.rename(self.root / "issues" / "first.md")
        second = self.write_versioned("BIZ-AMBIGUOUS")
        second.rename(self.root / "issues" / "second.md")
        self.write_versioned(
            "BIZ-CONSUMER", dependencies=("BIZ-AMBIGUOUS",)
        )
        self.add_artifacts("BIZ-CONSUMER", "spec", "plan", "tasks")

        project = self.schema.evaluate_project(self.root)
        consumer = next(
            issue
            for issue in project["issues"]
            if issue["issue_id"] == "BIZ-CONSUMER"
        )
        ambiguities = [
            diagnostic
            for diagnostic in consumer["diagnostics"]
            if diagnostic["code"] == "ISSUE_DUPLICATE_FIELD"
            and diagnostic["field"] == "depends_on"
        ]

        self.assertEqual(len(ambiguities), 1)
        ambiguity = ambiguities[0]
        self.assertNotIn("ISSUE_DEPENDENCY_DANGLING", codes(consumer))
        self.assertFalse(
            any(
                "does not exist" in diagnostic["message"].lower()
                for diagnostic in consumer["diagnostics"]
            )
        )
        self.assertEqual(
            ambiguity["current"],
            {
                "issue_id": "BIZ-AMBIGUOUS",
                "source_paths": ["issues/first.md", "issues/second.md"],
            },
        )
        self.assertEqual(ambiguity["expected"], "one unique dependency target")
        self.assertIn("multiple issue definitions", ambiguity["message"])
        self.assertIn("unique issue_id", ambiguity["recommendation"])
        self.assertNotIn("create", ambiguity["recommendation"].lower())
        self.assertEqual(consumer["readiness"], "blocked")
        self.assertEqual(
            consumer["recommended_next_command"], "product:doctor"
        )

    def test_dangling_self_and_cycle_dependencies_are_hard_errors(self):
        self.write_versioned("BIZ-DANGLING", dependencies=("BIZ-MISSING",))
        self.write_versioned("BIZ-SELF", dependencies=("BIZ-SELF",))
        self.write_versioned("BIZ-CYCLE-A", dependencies=("BIZ-CYCLE-B",))
        self.write_versioned("BIZ-CYCLE-B", dependencies=("BIZ-CYCLE-C",))
        self.write_versioned("BIZ-CYCLE-C", dependencies=("BIZ-CYCLE-A",))

        by_id = self.evaluated_by_id()

        self.assertIn("ISSUE_DEPENDENCY_DANGLING", codes(by_id["BIZ-DANGLING"]))
        self.assertIn("ISSUE_DEPENDENCY_CYCLE", codes(by_id["BIZ-SELF"]))
        for issue_id in ("BIZ-CYCLE-A", "BIZ-CYCLE-B", "BIZ-CYCLE-C"):
            self.assertIn("ISSUE_DEPENDENCY_CYCLE", codes(by_id[issue_id]))
            self.assertEqual(by_id[issue_id]["readiness"], "blocked")
            self.assertEqual(
                by_id[issue_id]["recommended_next_command"], "product:status"
            )

    def test_independent_cycles_report_only_their_own_members(self):
        self.write_versioned("BIZ-A1", dependencies=("BIZ-A2",))
        self.write_versioned("BIZ-A2", dependencies=("BIZ-A1",))
        self.write_versioned("BIZ-B1", dependencies=("BIZ-B2",))
        self.write_versioned("BIZ-B2", dependencies=("BIZ-B1",))

        by_id = self.evaluated_by_id()
        current = {
            issue_id: next(
                diagnostic["current"]
                for diagnostic in by_id[issue_id]["diagnostics"]
                if diagnostic["code"] == "ISSUE_DEPENDENCY_CYCLE"
            )
            for issue_id in by_id
        }

        self.assertEqual(
            current["BIZ-A1"],
            {
                "issue_id": "BIZ-A1",
                "representative_issue_id": "BIZ-A1",
                "component_size": 2,
            },
        )
        self.assertEqual(
            current["BIZ-A2"],
            {
                "issue_id": "BIZ-A2",
                "representative_issue_id": "BIZ-A1",
                "component_size": 2,
            },
        )
        self.assertEqual(current["BIZ-B1"]["representative_issue_id"], "BIZ-B1")
        self.assertEqual(current["BIZ-B2"]["representative_issue_id"], "BIZ-B1")

    def test_cycle_diagnostics_include_complete_strongly_connected_component(self):
        issue_index = {
            "BIZ-A": {
                "issue_id": "BIZ-A",
                "source_path": "issues/BIZ-A.md",
                "lifecycle_state": "backlog",
                "blocked_by": ["BIZ-B", "BIZ-C"],
                "advisory_blocked_by": [],
            },
            "BIZ-B": {
                "issue_id": "BIZ-B",
                "source_path": "issues/BIZ-B.md",
                "lifecycle_state": "backlog",
                "blocked_by": ["BIZ-A"],
                "advisory_blocked_by": [],
            },
            "BIZ-C": {
                "issue_id": "BIZ-C",
                "source_path": "issues/BIZ-C.md",
                "lifecycle_state": "backlog",
                "blocked_by": ["BIZ-B"],
                "advisory_blocked_by": [],
            },
        }

        diagnostics = self.schema.dependency_diagnostics(issue_index)
        repeated = self.schema.dependency_diagnostics(issue_index)

        expected = {
            issue_id: [
                (
                    "ISSUE_DEPENDENCY_CYCLE",
                    {
                        "issue_id": issue_id,
                        "representative_issue_id": "BIZ-A",
                        "component_size": 3,
                    },
                )
            ]
            for issue_id in ("BIZ-A", "BIZ-B", "BIZ-C")
        }
        actual = {
            issue_id: [
                (diagnostic["code"], diagnostic["current"])
                for diagnostic in issue_diagnostics
                if diagnostic["code"] == "ISSUE_DEPENDENCY_CYCLE"
            ]
            for issue_id, issue_diagnostics in diagnostics.items()
        }
        self.assertEqual(actual, expected)
        self.assertEqual(repeated, diagnostics)

    def test_cycle_path_is_deterministic_and_contains_only_real_graph_edges(self):
        graph = {
            "001-a": ["003-c"],
            "002-b": ["001-a"],
            "003-c": ["002-b"],
        }
        issue_index = {
            issue_id: {
                "issue_id": issue_id,
                "source_path": f"issues/{issue_id}.md",
                "lifecycle_state": "backlog",
                "blocked_by": dependencies,
                "advisory_blocked_by": [],
            }
            for issue_id, dependencies in graph.items()
        }

        diagnostics = self.schema.dependency_diagnostics(issue_index)
        cycle_diagnostics = [
            diagnostic
            for issue_diagnostics in diagnostics.values()
            for diagnostic in issue_diagnostics
            if diagnostic["code"] == "ISSUE_DEPENDENCY_CYCLE"
        ]

        self.assertEqual(len(cycle_diagnostics), 3)
        for diagnostic in cycle_diagnostics:
            with self.subTest(issue_id=diagnostic["issue_id"]):
                self.assertEqual(diagnostic["current"]["component_size"], 3)
                if diagnostic["issue_id"] == "001-a":
                    self.assertEqual(
                        diagnostic["cycle_path"],
                        ["001-a", "003-c", "002-b", "001-a"],
                    )
                    self.assertEqual(
                        diagnostic["cycle_paths"],
                        [["001-a", "003-c", "002-b", "001-a"]],
                    )
                    self.assertEqual(
                        set(diagnostic),
                        REQUIRED_DIAGNOSTIC_KEYS
                        | {"cycle_path", "cycle_paths"},
                    )
                    self.assertTrue(
                        all(
                            target in graph[source]
                            for source, target in zip(
                                diagnostic["cycle_path"],
                                diagnostic["cycle_path"][1:],
                            )
                        )
                    )
                else:
                    self.assertNotIn("cycle_path", diagnostic)
                    self.assertNotIn("cycle_paths", diagnostic)
                    self.assertEqual(set(diagnostic), REQUIRED_DIAGNOSTIC_KEYS)

        self_cycle_index = {
            "004-self": {
                "issue_id": "004-self",
                "source_path": "issues/004-self.md",
                "lifecycle_state": "backlog",
                "blocked_by": ["004-self"],
                "advisory_blocked_by": [],
            }
        }
        self_cycle = self.schema.dependency_diagnostics(self_cycle_index)
        self.assertEqual(
            self_cycle["004-self"][-1]["cycle_path"],
            ["004-self", "004-self"],
        )
        self.assertEqual(
            self_cycle["004-self"][-1]["cycle_paths"],
            [["004-self", "004-self"]],
        )

        non_hamiltonian_graph = {
            "005-a": ["006-b", "007-c"],
            "006-b": ["005-a"],
            "007-c": ["006-b"],
        }
        non_hamiltonian_index = {
            issue_id: {
                "issue_id": issue_id,
                "source_path": f"issues/{issue_id}.md",
                "lifecycle_state": "backlog",
                "blocked_by": dependencies,
                "advisory_blocked_by": [],
            }
            for issue_id, dependencies in non_hamiltonian_graph.items()
        }
        non_hamiltonian = self.schema.dependency_diagnostics(
            non_hamiltonian_index
        )
        cycle_paths = non_hamiltonian["005-a"][-1]["cycle_paths"]
        self.assertEqual(
            cycle_paths,
            [
                ["005-a", "006-b", "005-a"],
                ["007-c", "006-b", "005-a", "007-c"],
            ],
        )
        self.assertEqual(
            {node for path in cycle_paths for node in path},
            set(non_hamiltonian_graph),
        )
        for cycle_path in cycle_paths:
            self.assertTrue(
                all(
                    target in non_hamiltonian_graph[source]
                    for source, target in zip(
                        cycle_path, cycle_path[1:]
                    )
                )
            )

    def test_cycle_paths_preserve_all_back_edges_and_dependency_order(self):
        cases = (
            (
                ["002-b", "003-c"],
                [
                    ["001-a", "002-b", "001-a"],
                    ["001-a", "003-c", "001-a"],
                ],
            ),
            (
                ["003-c", "002-b"],
                [
                    ["001-a", "003-c", "001-a"],
                    ["001-a", "002-b", "001-a"],
                ],
            ),
        )
        for dependencies, expected_paths in cases:
            with self.subTest(dependencies=dependencies):
                graph = {
                    "001-a": dependencies,
                    "002-b": ["001-a"],
                    "003-c": ["001-a"],
                }
                issue_index = {
                    issue_id: {
                        "issue_id": issue_id,
                        "source_path": f"issues/{issue_id}.md",
                        "lifecycle_state": "backlog",
                        "blocked_by": blocked_by,
                        "advisory_blocked_by": [],
                    }
                    for issue_id, blocked_by in graph.items()
                }

                diagnostics = self.schema.dependency_diagnostics(issue_index)
                cycle = diagnostics["001-a"][-1]

                self.assertEqual(cycle["cycle_path"], expected_paths[0])
                self.assertEqual(cycle["cycle_paths"], expected_paths)
                for path in cycle["cycle_paths"]:
                    self.assertTrue(
                        all(
                            target in graph[source]
                            for source, target in zip(path, path[1:])
                        )
                    )

    def test_unfinished_dependency_blocks_active_issue(self):
        self.write_versioned("BIZ-BLOCKER")
        self.write_versioned(
            "BIZ-ACTIVE", lifecycle="active", dependencies=("BIZ-BLOCKER",)
        )

        issue = self.evaluated_by_id()["BIZ-ACTIVE"]

        self.assertEqual(issue["readiness"], "blocked")
        self.assertEqual(issue["recommended_next_command"], "product:status")
        self.assertIn("ISSUE_DEPENDENCY_UNMET", codes(issue))
        diagnostic = next(
            item
            for item in issue["diagnostics"]
            if item["code"] == "ISSUE_DEPENDENCY_UNMET"
        )
        self.assertEqual(diagnostic["severity"], "error")

    def test_backlog_dependency_wait_is_warning_unless_execute_is_claimed(self):
        self.write_versioned("BIZ-BLOCKER")
        self.write_versioned(
            "BIZ-WAITING",
            dependencies=("BIZ-BLOCKER",),
            next_command="product:status",
        )
        self.write_versioned(
            "BIZ-EXECUTE-CLAIM",
            dependencies=("BIZ-BLOCKER",),
        )

        by_id = self.evaluated_by_id()

        waiting = next(
            item
            for item in by_id["BIZ-WAITING"]["diagnostics"]
            if item["code"] == "ISSUE_DEPENDENCY_UNMET"
        )
        execute_claim = next(
            item
            for item in by_id["BIZ-EXECUTE-CLAIM"]["diagnostics"]
            if item["code"] == "ISSUE_DEPENDENCY_UNMET"
        )
        self.assertEqual(waiting["severity"], "warning")
        self.assertEqual(execute_claim["severity"], "error")
        self.assertEqual(
            by_id["BIZ-WAITING"]["recommended_next_command"],
            "product:status",
        )

    def test_done_and_superseded_dependencies_are_satisfied(self):
        self.write_versioned("BIZ-DONE", lifecycle="done", next_command="product:status")
        self.write_markdown("BIZ-SUPERSEDED", status="superseded")
        self.write_versioned(
            "BIZ-WORK",
            dependencies=("BIZ-DONE", "BIZ-SUPERSEDED"),
        )
        self.add_artifacts("BIZ-WORK", "spec", "plan", "tasks")

        issue = self.evaluated_by_id()["BIZ-WORK"]

        self.assertNotIn("ISSUE_DEPENDENCY_UNMET", codes(issue))
        self.assertEqual(issue["readiness"], "ready")
        self.assertEqual(
            issue["recommended_next_command"], "product:execute BIZ-WORK"
        )

    def test_completed_issues_are_excluded_from_dependency_cycle_gates(self):
        self.write_versioned(
            "BIZ-OPEN",
            dependencies=("BIZ-DONE",),
        )
        self.write_versioned(
            "BIZ-DONE",
            lifecycle="done",
            dependencies=("BIZ-OPEN",),
            next_command="product:status",
        )

        project = self.schema.evaluate_project(self.root)
        by_id = {issue["issue_id"]: issue for issue in project["issues"]}

        self.assertNotIn("ISSUE_DEPENDENCY_UNMET", codes(by_id["BIZ-OPEN"]))
        self.assertNotIn("ISSUE_DEPENDENCY_CYCLE", codes(by_id["BIZ-OPEN"]))
        self.assertNotIn("ISSUE_DEPENDENCY_CYCLE", codes(by_id["BIZ-DONE"]))
        self.assertNotIn("BIZ-DONE", project["dependency_diagnostics"])

    def test_completed_cross_edges_do_not_suppress_real_open_cycle(self):
        issue_index = {
            "001-a": {
                "issue_id": "001-a",
                "source_path": "issues/001-a.md",
                "lifecycle_state": "backlog",
                "blocked_by": ["002-b"],
                "advisory_blocked_by": [],
            },
            "002-b": {
                "issue_id": "002-b",
                "source_path": "issues/002-b.md",
                "lifecycle_state": "backlog",
                "blocked_by": ["001-a", "003-done"],
                "advisory_blocked_by": [],
            },
            "003-done": {
                "issue_id": "003-done",
                "source_path": "issues/003-done.md",
                "lifecycle_state": "done",
                "blocked_by": ["001-a"],
                "advisory_blocked_by": [],
            },
        }

        diagnostics = self.schema.dependency_diagnostics(issue_index)

        self.assertEqual(
            diagnostics["001-a"][-1]["cycle_paths"],
            [["001-a", "002-b", "001-a"]],
        )
        self.assertNotIn("cycle_paths", diagnostics["002-b"][-1])
        self.assertNotIn("003-done", diagnostics)

    def test_high_fanout_cycle_payload_is_stored_once_and_memory_is_bounded(self):
        count = 600
        representative = "BIZ-0000"
        issue_index = {}
        member_ids = [f"BIZ-{index:04d}" for index in range(count)]
        for issue_id in member_ids:
            dependencies = (
                member_ids[1:]
                if issue_id == representative
                else [representative]
            )
            issue_index[issue_id] = {
                "issue_id": issue_id,
                "source_path": f"issues/{issue_id}.md",
                "lifecycle_state": "backlog",
                "blocked_by": dependencies,
                "advisory_blocked_by": [],
            }

        diagnostics = self.schema.dependency_diagnostics(issue_index)
        cycle_diagnostics = [
            diagnostic
            for issue_diagnostics in diagnostics.values()
            for diagnostic in issue_diagnostics
            if diagnostic["code"] == "ISSUE_DEPENDENCY_CYCLE"
        ]
        payload_owners = [
            diagnostic
            for diagnostic in cycle_diagnostics
            if "cycle_paths" in diagnostic
        ]
        serialized_size = len(
            json.dumps(diagnostics, separators=(",", ":")).encode("utf-8")
        )

        self.assertEqual(len(cycle_diagnostics), count)
        self.assertEqual(len(payload_owners), 1)
        self.assertEqual(payload_owners[0]["issue_id"], representative)
        self.assertEqual(len(payload_owners[0]["cycle_paths"]), count - 1)
        self.assertTrue(
            all(
                diagnostic["current"]["component_size"] == count
                for diagnostic in cycle_diagnostics
            )
        )
        self.assertLess(serialized_size, 2_000_000)

    def test_unversioned_advisory_dependency_only_blocks_conservatively(self):
        self.write_versioned("BIZ-BLOCKER")
        path = self.root / "issues" / "BIZ-ADVISORY.md"
        path.write_text(
            """---
depends_on: [BIZ-BLOCKER]
definition_readiness: ready
gate_state: passed
next_command: product:execute BIZ-ADVISORY
---
# Issue: `BIZ-ADVISORY` Advisory fixture

**Status: backlog** — created 2026-07-22.
""",
            encoding="utf-8",
        )
        self.add_artifacts("BIZ-ADVISORY", "spec", "plan", "tasks")

        issue = self.evaluated_by_id()["BIZ-ADVISORY"]

        self.assertEqual(issue["definition_readiness"], None)
        self.assertEqual(issue["readiness"], "blocked")
        self.assertIn("ISSUE_DEPENDENCY_UNMET", codes(issue))
        self.assertEqual(issue["recommended_next_command"], "product:status")
        unmet = next(
            item
            for item in issue["diagnostics"]
            if item["code"] == "ISSUE_DEPENDENCY_UNMET"
        )
        self.assertEqual(unmet["severity"], "warning")

    def test_dependency_analysis_is_iterative_for_deep_chain(self):
        count = 2000
        issue_index = {}
        for index in range(count):
            issue_id = f"BIZ-{index:04d}"
            dependency = [f"BIZ-{index + 1:04d}"] if index + 1 < count else []
            issue_index[issue_id] = {
                "issue_id": issue_id,
                "source_path": f"issues/{issue_id}.md",
                "lifecycle_state": "done",
                "blocked_by": dependency,
                "advisory_blocked_by": [],
            }

        diagnostics = self.schema.dependency_diagnostics(issue_index)

        self.assertEqual(diagnostics, {})

    def test_project_dependency_diagnostics_do_not_alias_issue_diagnostics(self):
        self.write_versioned("BIZ-ALIAS-BLOCKER")
        self.write_versioned(
            "BIZ-ALIAS-WORK", dependencies=("BIZ-ALIAS-BLOCKER",)
        )

        project = self.schema.evaluate_project(self.root)
        issue = next(
            item for item in project["issues"] if item["issue_id"] == "BIZ-ALIAS-WORK"
        )
        project_diagnostic = next(
            item
            for item in project["dependency_diagnostics"]["BIZ-ALIAS-WORK"]
            if item["code"] == "ISSUE_DEPENDENCY_UNMET"
        )
        issue_diagnostic = next(
            item
            for item in issue["diagnostics"]
            if item["code"] == "ISSUE_DEPENDENCY_UNMET"
        )
        original = issue_diagnostic["current"]

        project_diagnostic["current"] = "mutated"

        self.assertIsNot(project_diagnostic, issue_diagnostic)
        self.assertEqual(issue_diagnostic["current"], original)

    def test_artifact_index_exposes_coverage_and_ordered_phase(self):
        issue_ids = [f"BIZ-{name.upper()}" for name in (
            "issue", "spec", "plan", "tasks", "review", "release"
        )]
        phases = ("spec", "plan", "tasks", "review", "release")
        for index, issue_id in enumerate(issue_ids):
            self.add_artifacts(issue_id, *phases[:index])

        artifact_index = self.schema.build_artifact_index(self.root, issue_ids)

        for index, issue_id in enumerate(issue_ids):
            self.assertEqual(artifact_index[issue_id]["artifact_phase"], (
                "issue", "spec", "plan", "tasks", "review", "release"
            )[index])
            for phase_index, phase in enumerate(phases):
                self.assertEqual(artifact_index[issue_id][phase], phase_index < index)

    def test_route_precedence_schema_projection_and_dependency(self):
        malformed = self.root / "issues" / "BIZ-MALFORMED.md"
        malformed.write_text(
            "---\nschema_version: [0.1.0]\n---\n# Issue: `BIZ-MALFORMED` Bad\n",
            encoding="utf-8",
        )
        unsupported = self.root / "issues" / "BIZ-UNSUPPORTED.md"
        unsupported.write_text(
            "---\nschema_version: 9.9.9\n---\n# Issue: `BIZ-UNSUPPORTED` Bad\n",
            encoding="utf-8",
        )
        self.write_versioned("BIZ-PROJECTION", markdown_status="done")
        self.write_versioned("BIZ-DEPENDENCY", dependencies=("BIZ-GHOST",))
        for issue_id in (
            "BIZ-MALFORMED", "BIZ-UNSUPPORTED", "BIZ-PROJECTION", "BIZ-DEPENDENCY"
        ):
            self.add_artifacts(issue_id, "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        for issue_id in ("BIZ-MALFORMED", "BIZ-UNSUPPORTED", "BIZ-PROJECTION"):
            self.assertEqual(by_id[issue_id]["readiness"], "blocked")
            self.assertEqual(
                by_id[issue_id]["recommended_next_command"], "product:doctor"
            )
        self.assertEqual(
            by_id["BIZ-DEPENDENCY"]["recommended_next_command"], "product:status"
        )

    def test_definition_artifact_and_gate_routes_are_ordered(self):
        self.write_versioned("BIZ-DRAFT", definition="draft")
        self.write_versioned("BIZ-NO-SPEC")
        self.write_versioned("BIZ-NO-PLAN")
        self.add_artifacts("BIZ-NO-PLAN", "spec")
        self.write_versioned("BIZ-NO-TASKS")
        self.add_artifacts("BIZ-NO-TASKS", "spec", "plan")
        self.write_versioned("BIZ-PENDING", gate="pending")
        self.add_artifacts("BIZ-PENDING", "spec", "plan", "tasks")
        self.write_versioned("BIZ-BLOCKED", gate="blocked")
        self.add_artifacts("BIZ-BLOCKED", "spec", "plan", "tasks")
        self.write_versioned("BIZ-READY")
        self.add_artifacts("BIZ-READY", "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        expected = {
            "BIZ-DRAFT": ("blocked", "product:spec BIZ-DRAFT"),
            "BIZ-NO-SPEC": ("not_ready", "product:spec BIZ-NO-SPEC"),
            "BIZ-NO-PLAN": ("not_ready", "product:plan BIZ-NO-PLAN"),
            "BIZ-NO-TASKS": ("not_ready", "product:plan BIZ-NO-TASKS"),
            "BIZ-PENDING": ("blocked", "product:review BIZ-PENDING"),
            "BIZ-BLOCKED": ("blocked", "product:review BIZ-BLOCKED"),
            "BIZ-READY": ("ready", "product:execute BIZ-READY"),
        }
        for issue_id, (readiness, command) in expected.items():
            with self.subTest(issue_id=issue_id):
                self.assertEqual(by_id[issue_id]["readiness"], readiness)
                self.assertEqual(by_id[issue_id]["recommended_next_command"], command)

        self.assertIn("ISSUE_DEFINITION_NOT_READY", codes(by_id["BIZ-DRAFT"]))
        for issue_id in ("BIZ-PENDING", "BIZ-BLOCKED"):
            self.assertIn("ISSUE_GATE_BLOCKED", codes(by_id[issue_id]))

    def test_recognized_definition_state_fails_closed_but_legacy_none_does_not(self):
        self.write_versioned("BIZ-DEF-MISSING", definition=None)
        self.write_versioned("BIZ-DEF-UNKNOWN", definition="nonsense")
        for issue_id in ("BIZ-DEF-MISSING", "BIZ-DEF-UNKNOWN"):
            self.add_artifacts(issue_id, "spec", "plan", "tasks")
        self.write_markdown("legacy-definition-none")
        self.add_artifacts("legacy-definition-none", "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        for issue_id, current in (
            ("BIZ-DEF-MISSING", None),
            ("BIZ-DEF-UNKNOWN", "nonsense"),
        ):
            with self.subTest(issue_id=issue_id):
                issue = by_id[issue_id]
                self.assertEqual(issue["readiness"], "blocked")
                self.assertEqual(
                    issue["recommended_next_command"], f"product:spec {issue_id}"
                )
                diagnostic = next(
                    item
                    for item in issue["diagnostics"]
                    if item["code"] == "ISSUE_DEFINITION_NOT_READY"
                )
                self.assertEqual(diagnostic["current"], current)
                self.assertEqual(diagnostic["expected"], "draft or ready")
                self.assertEqual(set(diagnostic), REQUIRED_DIAGNOSTIC_KEYS)

        legacy = by_id["legacy-definition-none"]
        self.assertEqual(legacy["readiness"], "ready")
        self.assertEqual(
            legacy["recommended_next_command"],
            "product:execute legacy-definition-none",
        )

    def test_recognized_gate_state_fails_closed_after_artifact_gates(self):
        for issue_id, gate in (
            ("BIZ-GATE-MISSING", None),
            ("BIZ-GATE-UNKNOWN", "nonsense"),
            ("BIZ-GATE-IN-PROGRESS", "in_progress"),
        ):
            self.write_versioned(issue_id, gate=gate)
            self.add_artifacts(issue_id, "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        for issue_id, current, expected in (
            (
                "BIZ-GATE-MISSING",
                None,
                "pending, in_progress, blocked, or passed",
            ),
            (
                "BIZ-GATE-UNKNOWN",
                "nonsense",
                "pending, in_progress, blocked, or passed",
            ),
            ("BIZ-GATE-IN-PROGRESS", "in_progress", "passed"),
        ):
            with self.subTest(issue_id=issue_id):
                issue = by_id[issue_id]
                self.assertEqual(issue["readiness"], "blocked")
                self.assertEqual(
                    issue["recommended_next_command"], f"product:review {issue_id}"
                )
                diagnostic = next(
                    item
                    for item in issue["diagnostics"]
                    if item["code"] == "ISSUE_GATE_BLOCKED"
                )
                self.assertEqual(diagnostic["current"], current)
                self.assertEqual(diagnostic["expected"], expected)
                self.assertEqual(set(diagnostic), REQUIRED_DIAGNOSTIC_KEYS)

    def test_malformed_structural_fields_do_not_add_derived_diagnostics(self):
        self.write_versioned("BIZ-DEF-TYPE", definition=["ready"])
        self.write_versioned("BIZ-GATE-TYPE", gate=["passed"])
        for issue_id in ("BIZ-DEF-TYPE", "BIZ-GATE-TYPE"):
            self.add_artifacts(issue_id, "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        for issue_id, field, derived_code in (
            ("BIZ-DEF-TYPE", "definition_readiness", "ISSUE_DEFINITION_NOT_READY"),
            ("BIZ-GATE-TYPE", "gate_state", "ISSUE_GATE_BLOCKED"),
        ):
            with self.subTest(issue_id=issue_id):
                field_diagnostics = [
                    diagnostic
                    for diagnostic in by_id[issue_id]["diagnostics"]
                    if diagnostic["field"] == field
                ]
                self.assertEqual(
                    [diagnostic["code"] for diagnostic in field_diagnostics],
                    ["ISSUE_SCHEMA_MALFORMED"],
                )
                self.assertNotIn(derived_code, codes(by_id[issue_id]))

    def test_declared_phase_mapping_accepts_only_actual_artifact_phase(self):
        cases = {
            "BIZ-PHASE-ISSUE": ("issue", ()),
            "BIZ-PHASE-SPEC": ("spec", ("spec",)),
            "BIZ-PHASE-PLAN": ("plan", ("spec", "plan")),
            "BIZ-PHASE-IMPLEMENTATION": (
                "implementation",
                ("spec", "plan", "tasks"),
            ),
            "BIZ-PHASE-EXECUTE": ("execute", ("spec", "plan", "tasks")),
            "BIZ-PHASE-REVIEW": (
                "review",
                ("spec", "plan", "tasks", "review"),
            ),
            "BIZ-PHASE-RELEASE": (
                "release",
                ("spec", "plan", "tasks", "review", "release"),
            ),
        }
        for issue_id, (phase, artifacts) in cases.items():
            self.write_versioned(issue_id, phase=phase)
            self.add_artifacts(issue_id, *artifacts)

        by_id = self.evaluated_by_id()

        for issue_id in cases:
            with self.subTest(issue_id=issue_id):
                self.assertNotIn(
                    "ISSUE_STATE_PROJECTION_MISMATCH", codes(by_id[issue_id])
                )
                phase_errors = [
                    item
                    for item in by_id[issue_id]["diagnostics"]
                    if item["field"] == "phase"
                ]
                self.assertEqual(phase_errors, [])

    def test_declared_phase_drift_and_unsupported_value_route_doctor(self):
        self.write_versioned("BIZ-PHASE-DRIFT", phase="release")
        self.add_artifacts("BIZ-PHASE-DRIFT", "spec", "plan", "tasks")
        self.write_versioned("BIZ-PHASE-UNKNOWN", phase="design")
        self.add_artifacts("BIZ-PHASE-UNKNOWN", "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        drift = by_id["BIZ-PHASE-DRIFT"]
        self.assertEqual(drift["recommended_next_command"], "product:doctor")
        drift_diagnostic = next(
            item
            for item in drift["diagnostics"]
            if item["code"] == "ISSUE_STATE_PROJECTION_MISMATCH"
            and item["field"] == "phase"
        )
        self.assertEqual(drift_diagnostic["current"], "release")
        self.assertEqual(drift_diagnostic["expected"], "tasks")
        self.assertEqual(set(drift_diagnostic), REQUIRED_DIAGNOSTIC_KEYS)

        unsupported = by_id["BIZ-PHASE-UNKNOWN"]
        self.assertEqual(unsupported["recommended_next_command"], "product:doctor")
        unsupported_diagnostic = next(
            item
            for item in unsupported["diagnostics"]
            if item["code"] == "ISSUE_SCHEMA_MALFORMED"
            and item["field"] == "phase"
        )
        self.assertEqual(unsupported_diagnostic["current"], "design")
        self.assertIn("implementation", unsupported_diagnostic["expected"])
        self.assertEqual(unsupported_diagnostic["origin"], "evaluator")
        self.assertEqual(
            set(unsupported_diagnostic),
            REQUIRED_DIAGNOSTIC_KEYS | {"origin"},
        )

    def test_phase_drift_does_not_override_earlier_structural_gates(self):
        self.write_versioned("BIZ-PHASE-BLOCKER")
        self.write_versioned(
            "BIZ-PHASE-DEPENDENCY",
            dependencies=("BIZ-PHASE-BLOCKER",),
            phase="release",
        )
        self.add_artifacts("BIZ-PHASE-DEPENDENCY", "spec", "plan", "tasks")
        self.write_versioned(
            "BIZ-PHASE-DEFINITION",
            definition="draft",
            phase="release",
        )
        self.add_artifacts("BIZ-PHASE-DEFINITION", "spec", "plan", "tasks")
        self.write_versioned("BIZ-PHASE-MISSING-SPEC", phase="release")
        self.write_versioned("BIZ-PHASE-COMPLETE", phase="release")
        self.add_artifacts("BIZ-PHASE-COMPLETE", "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        expected = {
            "BIZ-PHASE-DEPENDENCY": "product:status",
            "BIZ-PHASE-DEFINITION": "product:spec BIZ-PHASE-DEFINITION",
            "BIZ-PHASE-MISSING-SPEC": "product:spec BIZ-PHASE-MISSING-SPEC",
            "BIZ-PHASE-COMPLETE": "product:doctor",
        }
        for issue_id, command in expected.items():
            with self.subTest(issue_id=issue_id):
                issue = by_id[issue_id]
                self.assertEqual(issue["recommended_next_command"], command)
                self.assertTrue(
                    any(
                        diagnostic["code"] == "ISSUE_STATE_PROJECTION_MISMATCH"
                        and diagnostic["field"] == "phase"
                        for diagnostic in issue["diagnostics"]
                    )
                )

    def test_aligned_phase_continues_to_gate_and_execute_idempotently(self):
        self.write_versioned(
            "BIZ-PHASE-GATE", phase="implementation", gate="pending"
        )
        self.add_artifacts("BIZ-PHASE-GATE", "spec", "plan", "tasks")
        self.write_versioned(
            "BIZ-PHASE-EXECUTE", phase="execute", gate="passed"
        )
        self.add_artifacts("BIZ-PHASE-EXECUTE", "spec", "plan", "tasks")

        by_id = self.evaluated_by_id()

        self.assertEqual(
            by_id["BIZ-PHASE-GATE"]["recommended_next_command"],
            "product:review BIZ-PHASE-GATE",
        )
        self.assertEqual(
            by_id["BIZ-PHASE-EXECUTE"]["recommended_next_command"],
            "product:execute BIZ-PHASE-EXECUTE",
        )

        first = by_id["BIZ-PHASE-EXECUTE"]
        artifact_index = self.schema.build_artifact_index(
            self.root, ["BIZ-PHASE-EXECUTE"]
        )
        second = self.schema.evaluate_issue(
            first, {"BIZ-PHASE-EXECUTE": first}, artifact_index
        )
        self.assertEqual(
            second["recommended_next_command"], first["recommended_next_command"]
        )
        self.assertEqual(second["diagnostics"], first["diagnostics"])

    def test_re_evaluation_removes_resolved_dependency_diagnostics(self):
        self.write_versioned("BIZ-REEVAL-BLOCKER")
        self.write_versioned(
            "BIZ-REEVAL-WORK", dependencies=("BIZ-REEVAL-BLOCKER",)
        )
        self.add_artifacts("BIZ-REEVAL-WORK", "spec", "plan", "tasks")
        project = self.schema.evaluate_project(self.root)
        by_id = {issue["issue_id"]: issue for issue in project["issues"]}
        first = by_id["BIZ-REEVAL-WORK"]
        by_id["BIZ-REEVAL-BLOCKER"] = dict(by_id["BIZ-REEVAL-BLOCKER"])
        by_id["BIZ-REEVAL-BLOCKER"]["lifecycle_state"] = "done"

        second = self.schema.evaluate_issue(
            first,
            by_id,
            self.schema.build_artifact_index(self.root, by_id),
        )

        self.assertNotIn("ISSUE_DEPENDENCY_UNMET", codes(second))
        self.assertNotIn("ISSUE_NEXT_COMMAND_INVALID", codes(second))
        self.assertEqual(second["readiness"], "ready")
        self.assertEqual(
            second["recommended_next_command"],
            "product:execute BIZ-REEVAL-WORK",
        )

    def test_re_evaluation_removes_aligned_phase_diagnostic(self):
        self.write_versioned("BIZ-REEVAL-PHASE", phase="release")
        self.add_artifacts("BIZ-REEVAL-PHASE", "spec", "plan", "tasks")
        first = self.evaluated_by_id()["BIZ-REEVAL-PHASE"]
        self.assertTrue(
            any(
                diagnostic["code"] == "ISSUE_STATE_PROJECTION_MISMATCH"
                and diagnostic["field"] == "phase"
                for diagnostic in first["diagnostics"]
            )
        )
        self.add_artifacts("BIZ-REEVAL-PHASE", "review", "release")

        second = self.schema.evaluate_issue(
            first,
            {"BIZ-REEVAL-PHASE": first},
            self.schema.build_artifact_index(self.root, ["BIZ-REEVAL-PHASE"]),
        )

        self.assertFalse(
            any(
                diagnostic["code"] == "ISSUE_STATE_PROJECTION_MISMATCH"
                and diagnostic["field"] == "phase"
                for diagnostic in second["diagnostics"]
            )
        )
        self.assertNotIn("ISSUE_NEXT_COMMAND_INVALID", codes(second))
        self.assertEqual(second["readiness"], "ready")
        self.assertEqual(
            second["recommended_next_command"],
            "product:execute BIZ-REEVAL-PHASE",
        )

    def test_re_evaluation_removes_corrected_unsupported_phase_diagnostic(self):
        self.write_versioned("BIZ-REEVAL-PHASE-UNKNOWN", phase="design")
        self.add_artifacts(
            "BIZ-REEVAL-PHASE-UNKNOWN", "spec", "plan", "tasks"
        )
        first = self.evaluated_by_id()["BIZ-REEVAL-PHASE-UNKNOWN"]
        unsupported = next(
            diagnostic
            for diagnostic in first["diagnostics"]
            if diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
            and diagnostic["field"] == "phase"
        )
        self.assertEqual(unsupported.get("origin"), "evaluator")
        corrected = dict(first)
        corrected["declared_phase"] = "release"
        self.add_artifacts("BIZ-REEVAL-PHASE-UNKNOWN", "review", "release")

        second = self.schema.evaluate_issue(
            corrected,
            {"BIZ-REEVAL-PHASE-UNKNOWN": corrected},
            self.schema.build_artifact_index(
                self.root, ["BIZ-REEVAL-PHASE-UNKNOWN"]
            ),
        )

        self.assertFalse(
            any(
                diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
                and diagnostic["field"] == "phase"
                for diagnostic in second["diagnostics"]
            )
        )
        self.assertNotIn("ISSUE_NEXT_COMMAND_INVALID", codes(second))
        self.assertEqual(second["readiness"], "ready")
        self.assertEqual(
            second["recommended_next_command"],
            "product:execute BIZ-REEVAL-PHASE-UNKNOWN",
        )

    def test_re_evaluation_preserves_parser_owned_phase_type_error(self):
        self.write_versioned("BIZ-REEVAL-PHASE-TYPE", phase=["release"])
        first = self.evaluated_by_id()["BIZ-REEVAL-PHASE-TYPE"]
        parser_error = next(
            diagnostic
            for diagnostic in first["diagnostics"]
            if diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
            and diagnostic["field"] == "phase"
        )
        self.assertNotIn("origin", parser_error)
        corrected = dict(first)
        corrected["declared_phase"] = "release"
        self.add_artifacts(
            "BIZ-REEVAL-PHASE-TYPE",
            "spec",
            "plan",
            "tasks",
            "review",
            "release",
        )

        second = self.schema.evaluate_issue(
            corrected,
            {"BIZ-REEVAL-PHASE-TYPE": corrected},
            self.schema.build_artifact_index(
                self.root, ["BIZ-REEVAL-PHASE-TYPE"]
            ),
        )

        self.assertIn(parser_error, second["diagnostics"])
        self.assertEqual(second["readiness"], "blocked")
        self.assertEqual(
            second["recommended_next_command"], "product:doctor"
        )

    def test_re_evaluation_preserves_parser_projection_diagnostics(self):
        self.write_versioned("BIZ-REEVAL-PARSER", markdown_status="done")
        self.add_artifacts("BIZ-REEVAL-PARSER", "spec", "plan", "tasks")
        first = self.evaluated_by_id()["BIZ-REEVAL-PARSER"]
        parser_diagnostic = next(
            diagnostic
            for diagnostic in first["diagnostics"]
            if diagnostic["code"] == "ISSUE_STATE_PROJECTION_MISMATCH"
            and diagnostic["field"] == "markdown_status"
        )

        second = self.schema.evaluate_issue(
            first,
            {"BIZ-REEVAL-PARSER": first},
            self.schema.build_artifact_index(self.root, ["BIZ-REEVAL-PARSER"]),
        )

        self.assertIn(parser_diagnostic, second["diagnostics"])
        self.assertEqual(
            second["recommended_next_command"], "product:doctor"
        )

    def test_re_evaluation_removes_resolved_duplicate_id_diagnostic(self):
        first_path = self.write_versioned("BIZ-REEVAL-DUP")
        first_path.rename(self.root / "issues" / "first.md")
        second_path = self.write_versioned("BIZ-REEVAL-DUP")
        second_path.rename(self.root / "issues" / "second.md")
        self.add_artifacts("BIZ-REEVAL-DUP", "spec", "plan", "tasks")
        duplicate = self.schema.evaluate_project(self.root)["issues"][0]
        self.assertIn("ISSUE_DUPLICATE_FIELD", codes(duplicate))

        reevaluated = self.schema.evaluate_issue(
            duplicate,
            {"BIZ-REEVAL-DUP": duplicate},
            self.schema.build_artifact_index(self.root, ["BIZ-REEVAL-DUP"]),
        )

        self.assertNotIn("ISSUE_DUPLICATE_FIELD", codes(reevaluated))
        self.assertNotIn("ISSUE_NEXT_COMMAND_INVALID", codes(reevaluated))
        self.assertEqual(reevaluated["readiness"], "ready")
        self.assertEqual(
            reevaluated["recommended_next_command"],
            "product:execute BIZ-REEVAL-DUP",
        )

    def test_declared_command_skip_is_diagnosed_without_overwriting_route(self):
        self.write_versioned(
            "BIZ-SKIP",
            definition="draft",
            next_command="product:execute BIZ-SKIP",
        )

        issue = self.evaluated_by_id()["BIZ-SKIP"]
        diagnostic = next(
            item
            for item in issue["diagnostics"]
            if item["code"] == "ISSUE_NEXT_COMMAND_INVALID"
        )

        self.assertEqual(issue["recommended_next_command"], "product:spec BIZ-SKIP")
        self.assertEqual(diagnostic["current"], "product:execute BIZ-SKIP")
        self.assertEqual(diagnostic["expected"], "product:spec BIZ-SKIP")
        self.assertEqual(set(diagnostic), REQUIRED_DIAGNOSTIC_KEYS)

    def test_completed_lifecycle_routes_status_and_exception_allowlist_is_empty(self):
        self.write_versioned("BIZ-DONE", lifecycle="done", next_command="product:status")
        self.add_artifacts("BIZ-DONE", "spec", "plan", "tasks", "review", "release")
        self.write_markdown("BIZ-SUPERSEDED", status="superseded")

        by_id = self.evaluated_by_id()

        for issue_id in ("BIZ-DONE", "BIZ-SUPERSEDED"):
            self.assertEqual(by_id[issue_id]["recommended_next_command"], "product:status")
            self.assertNotEqual(by_id[issue_id]["readiness"], "ready")
        self.assertEqual(self.schema.DEFINITION_READINESS_EXCEPTIONS, frozenset())


class ProjectIssueSchemaCrossConsumerParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_module(
            "project_issue_schema_cross_consumer",
            "scripts/project_issue_schema.py",
        )
        cls.lifecycle = load_module(
            "project_lifecycle_cross_consumer",
            "scripts/project_lifecycle.py",
        )
        cls.loop = load_module(
            "project_loop_cross_consumer",
            "scripts/project_loop.py",
        )
        cls.mcp = load_module(
            "mcp_server_cross_consumer",
            "scripts/mcp_server.py",
        )
        cls.memory = load_module(
            "project_memory_cross_consumer",
            "scripts/project_memory.py",
        )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "issues").mkdir()
        for issue_id in ("BIZ-033", "BIZ-038", "BIZ-039", "BIZ-040"):
            shutil.copy2(
                FIXTURES / f"{issue_id}.md",
                self.root / "issues" / f"{issue_id}.md",
            )
        shutil.copy2(
            FIXTURES / "legacy-markdown.md",
            self.root / "issues" / "legacy-markdown.md",
        )
        (self.root / "issues" / "001-dependency.md").write_text(
            "# Issue: `001-dependency` Completed dependency\n\n"
            "**Status: done** — created 2026-07-22, done 2026-07-22.\n",
            encoding="utf-8",
        )
        artifact_root = self.root / "specs" / "legacy-markdown"
        artifact_root.mkdir(parents=True)
        for name in ("spec", "plan", "tasks"):
            (artifact_root / f"{name}.md").write_text(
                f"# {name.title()}\n",
                encoding="utf-8",
            )
        (self.root / "workspace").mkdir()

    def loop_recommendation(self, issue_id):
        (self.root / "workspace" / "loop-state.json").write_text(
            json.dumps(
                {
                    "schema": "moduflow.loop-state.v2",
                    "loop_id": "issue-schema-parity",
                    "goal_id": "issue-schema-parity",
                    "issue_ids": [issue_id],
                    "active_issue_id": issue_id,
                    "phase": "execute",
                    "mode": "recommend",
                    "delegation_level": "full",
                    "status": "active",
                    "next_command": "product:loop",
                    "attempts": {
                        "command": "product:loop",
                        "count": 0,
                        "max": 10,
                        "last_changed_at": "2026-07-25",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return self.loop.recommend_loop(self.root)

    def test_legacy_and_biz_fixtures_have_cross_consumer_semantic_parity(self):
        expected = {
            "legacy-markdown": {
                "lifecycle_state": "backlog",
                "blocked_by": ["001-dependency"],
                "readiness": "ready",
                "recommended_next_command": "product:execute legacy-markdown",
                "diagnostic_codes": set(),
            },
            "BIZ-033": {
                "lifecycle_state": "active",
                "blocked_by": [],
                "readiness": "not_ready",
                "recommended_next_command": "product:spec BIZ-033",
                "diagnostic_codes": {
                    "ISSUE_GATE_BLOCKED",
                    "ISSUE_NEXT_COMMAND_INVALID",
                },
            },
            "BIZ-038": {
                "lifecycle_state": "backlog",
                "blocked_by": ["BIZ-033"],
                "readiness": "blocked",
                "recommended_next_command": "product:status",
                "diagnostic_codes": {
                    "ISSUE_AUX_STATUS_INVALID",
                    "ISSUE_DEPENDENCY_UNMET",
                    "ISSUE_GATE_BLOCKED",
                    "ISSUE_NEXT_COMMAND_INVALID",
                },
            },
            "BIZ-039": {
                "lifecycle_state": "backlog",
                "blocked_by": ["BIZ-033"],
                "readiness": "blocked",
                "recommended_next_command": "product:status",
                "diagnostic_codes": {
                    "ISSUE_AUX_STATUS_INVALID",
                    "ISSUE_DEPENDENCY_UNMET",
                    "ISSUE_GATE_BLOCKED",
                    "ISSUE_NEXT_COMMAND_INVALID",
                },
            },
            "BIZ-040": {
                "lifecycle_state": "backlog",
                "blocked_by": [],
                "readiness": "blocked",
                "recommended_next_command": "product:spec BIZ-040",
                "diagnostic_codes": {
                    "ISSUE_AUX_STATUS_INVALID",
                    "ISSUE_DEFINITION_NOT_READY",
                    "ISSUE_GATE_BLOCKED",
                    "ISSUE_NEXT_COMMAND_INVALID",
                },
            },
        }

        normalized = {
            issue["issue_id"]: issue
            for issue in self.schema.evaluate_project(self.root)["issues"]
        }
        lifecycle_items = {
            issue["id"]: issue for issue in self.lifecycle.list_issues(self.root)
        }
        ready_ids = {
            issue["id"] for issue in self.lifecycle.ready_issues(self.root)
        }
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 93,
            "method": "tools/call",
            "params": {"name": "moduflow_issues", "arguments": {}},
        }
        mcp_payload = json.loads(
            self.mcp.handle_request(mcp_request, self.root)["result"]["content"][0][
                "text"
            ]
        )
        mcp_items = {issue["id"]: issue for issue in mcp_payload["issues"]}
        issue_context = self.memory._evaluated_issue_context(self.root)
        graph_nodes, _edges = self.memory._collect_issue_graph(
            self.root,
            issue_context,
        )
        dashboard_rows = {
            row["id"]: row
            for row in self.memory._collect_issue_table(
                self.root,
                issue_context,
            )
        }

        self.assertIn("legacy-markdown", ready_ids)
        self.assertTrue(
            {"BIZ-033", "BIZ-038", "BIZ-039", "BIZ-040"}.isdisjoint(ready_ids)
        )
        for issue_id, contract in expected.items():
            with self.subTest(issue_id=issue_id):
                canonical = normalized[issue_id]
                lifecycle = lifecycle_items[issue_id]
                mcp = mcp_items[issue_id]
                graph = graph_nodes[issue_id]
                dashboard = dashboard_rows[issue_id]
                loop = self.loop_recommendation(issue_id)

                self.assertEqual(
                    canonical["lifecycle_state"],
                    contract["lifecycle_state"],
                )
                self.assertEqual(canonical["blocked_by"], contract["blocked_by"])
                self.assertEqual(canonical["readiness"], contract["readiness"])
                self.assertEqual(
                    canonical["recommended_next_command"],
                    contract["recommended_next_command"],
                )
                self.assertEqual(
                    codes(canonical),
                    contract["diagnostic_codes"],
                )

                for consumer in (lifecycle, mcp, graph, dashboard):
                    self.assertEqual(
                        consumer["status"],
                        canonical["lifecycle_state"],
                    )
                    self.assertEqual(
                        consumer["blocked_by"],
                        canonical["blocked_by"],
                    )
                for consumer in (mcp, graph, dashboard):
                    self.assertEqual(
                        consumer["readiness"],
                        canonical["readiness"],
                    )
                    self.assertEqual(
                        consumer["recommended_next_command"],
                        canonical["recommended_next_command"],
                    )
                    self.assertEqual(
                        set(consumer["diagnostic_codes"]),
                        codes(canonical),
                    )
                self.assertEqual(
                    dashboard["next_command"],
                    canonical["recommended_next_command"],
                )
                self.assertEqual(
                    loop["next_command"],
                    canonical["recommended_next_command"],
                )
                if canonical["readiness"] == "ready":
                    self.assertEqual(loop["status"], "active")
                    self.assertIsNone(loop["blocker"])
                else:
                    self.assertEqual(loop["status"], "needs_decision")
                    self.assertTrue(loop["blocker"])


class ProjectIssueMigrationReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_module(
            "project_issue_schema_migration", "scripts/project_issue_schema.py"
        )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "issues").mkdir()
        (self.root / "specs" / "BIZ-VERSIONED").mkdir(parents=True)
        for artifact in ("spec", "plan", "tasks"):
            (
                self.root
                / "specs"
                / "BIZ-VERSIONED"
                / f"{artifact}.md"
            ).write_text(f"# {artifact}\n", encoding="utf-8")

        self.write_issue(
            "BIZ-MARKDOWN.md",
            "# Issue: `BIZ-MARKDOWN` Compatible\n\n"
            "**Status: backlog** — created 2026-07-24.\n",
        )
        self.write_issue(
            "BIZ-VERSIONED.md",
            """---
schema_version: 0.1.0
issue_id: BIZ-VERSIONED
canonical_state: backlog
status: ready
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:execute BIZ-VERSIONED
---
# Issue: `BIZ-VERSIONED` Deterministic projection fixes

**Status: done**
**Blocked-by: `BIZ-OLD`**
""",
        )
        self.write_issue(
            "BIZ-UNVERSIONED.md",
            """---
depends_on: []
definition_readiness: ready
---
# Issue: `BIZ-UNVERSIONED` Missing canonical fields

**Status: backlog**
""",
        )
        self.write_issue(
            "BIZ-UNSUPPORTED.md",
            """---
schema_version: 9.9.9
issue_id: BIZ-UNSUPPORTED
custom_mode: future
---
# Issue: `BIZ-UNSUPPORTED` Unsupported

**Status: backlog**
""",
        )

    def write_issue(self, name, content):
        path = self.root / "issues" / name
        path.write_text(content, encoding="utf-8")
        return path

    def project_file_manifest(self):
        return {
            path.relative_to(self.root).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(self.root.rglob("*"))
            if path.is_file()
        }

    def by_id(self, report):
        return {issue["issue_id"]: issue for issue in report["issues"]}

    def test_build_report_has_deterministic_contract_and_is_read_only(self):
        before_hashes = self.project_file_manifest()

        report = self.schema.build_migration_report(self.root)
        repeated = self.schema.build_migration_report(self.root)

        self.assertEqual(report["schema"], "moduflow.issue-migration-report.v1")
        self.assertEqual(report["project_root"], str(self.root.resolve()))
        self.assertEqual(report["summary"]["issues_scanned"], 4)
        self.assertEqual(
            report["summary"]["source_formats"],
            {
                "frontmatter-0.1.0": 1,
                "frontmatter-unsupported": 1,
                "frontmatter-unversioned": 1,
                "markdown": 1,
            },
        )
        self.assertIn("safe_mappings", report["issues"][0])
        self.assertIn("human_decisions", report["issues"][0])
        self.assertIn("routing_before", report["issues"][0])
        self.assertIn("routing_after", report["issues"][0])
        self.assertEqual(
            [issue["source_path"] for issue in report["issues"]],
            sorted(issue["source_path"] for issue in report["issues"]),
        )
        self.assertEqual(report, repeated)
        self.assertEqual(before_hashes, self.project_file_manifest())

    def test_compatibility_policy_classifies_proposals_conservatively(self):
        report = self.schema.build_migration_report(self.root)
        by_id = self.by_id(report)

        markdown = by_id["BIZ-MARKDOWN"]
        self.assertFalse(markdown["migration_required"])
        self.assertEqual(markdown["proposed_changes"], {})
        self.assertEqual(markdown["human_decisions"], [])

        versioned = by_id["BIZ-VERSIONED"]
        self.assertEqual(
            versioned["proposed_changes"],
            {
                "align_dependency_projection": [],
                "align_frontmatter_status": "backlog",
                "align_markdown_status": "backlog",
            },
        )
        self.assertEqual(versioned["human_decisions"], [])
        self.assertEqual(
            versioned["routing_before"]["recommended_next_command"],
            "product:doctor",
        )
        self.assertEqual(
            versioned["routing_after"]["recommended_next_command"],
            "product:execute BIZ-VERSIONED",
        )

        unversioned = by_id["BIZ-UNVERSIONED"]
        self.assertNotIn("set_schema_version", unversioned["proposed_changes"])
        self.assertTrue(
            {"issue_id", "canonical_state", "status", "priority",
             "gate_state", "next_command"}
            <= {decision["field"] for decision in unversioned["human_decisions"]}
        )
        self.assertNotIn(
            "product:execute",
            unversioned["routing_after"]["recommended_next_command"],
        )

        unsupported = by_id["BIZ-UNSUPPORTED"]
        self.assertTrue(unsupported["migration_required"])
        self.assertIn(
            "schema_version",
            {decision["field"] for decision in unsupported["human_decisions"]},
        )
        self.assertEqual(unsupported["routing_after"]["readiness"], "blocked")
        self.assertEqual(
            unsupported["routing_after"]["recommended_next_command"],
            "product:doctor",
        )

    def test_complete_unversioned_contract_only_proposes_schema_when_unambiguous(self):
        path = self.root / "issues" / "BIZ-UNVERSIONED.md"
        path.write_text(
            """---
issue_id: BIZ-UNVERSIONED
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:spec BIZ-UNVERSIONED
---
# Issue: `BIZ-UNVERSIONED` Complete advisory contract

**Status: backlog**
""",
            encoding="utf-8",
        )

        issue = self.by_id(
            self.schema.build_migration_report(self.root)
        )["BIZ-UNVERSIONED"]

        self.assertEqual(
            issue["proposed_changes"]["set_schema_version"], "0.1.0"
        )
        self.assertEqual(issue["human_decisions"], [])
        self.assertNotEqual(
            issue["routing_after"]["recommended_next_command"],
            "product:execute BIZ-UNVERSIONED",
        )

    def test_invalid_canonical_state_is_not_used_as_safe_projection_truth(self):
        path = self.root / "issues" / "BIZ-VERSIONED.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "canonical_state: backlog", "canonical_state: unknown"
            ),
            encoding="utf-8",
        )

        issue = self.by_id(
            self.schema.build_migration_report(self.root)
        )["BIZ-VERSIONED"]

        self.assertNotIn(
            "align_frontmatter_status", issue["proposed_changes"]
        )
        self.assertIn(
            "canonical_state",
            {decision["field"] for decision in issue["human_decisions"]},
        )
        self.assertNotIn(
            "product:execute",
            issue["routing_after"]["recommended_next_command"],
        )

    def test_duplicate_unversioned_identity_proposals_require_human_decision(self):
        duplicate_paths = [
            "issues/BIZ-UNVERSIONED-2.md",
            "issues/BIZ-UNVERSIONED.md",
        ]
        content = """---
issue_id: DUP
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:spec DUP
---
# Issue: `DUP` Ambiguous advisory identity

**Status: backlog**
"""
        (self.root / duplicate_paths[1]).write_text(content, encoding="utf-8")
        self.write_issue("BIZ-UNVERSIONED-2.md", content)
        before_hashes = self.project_file_manifest()

        report = self.schema.build_migration_report(self.root)

        duplicates = [
            issue
            for issue in report["issues"]
            if issue["source_path"] in duplicate_paths
        ]
        self.assertEqual(len(duplicates), 2)
        for issue in duplicates:
            with self.subTest(source_path=issue["source_path"]):
                self.assertNotIn(
                    "set_schema_version", issue["proposed_changes"]
                )
                identity = next(
                    decision
                    for decision in issue["human_decisions"]
                    if decision["field"] == "issue_id"
                )
                self.assertEqual(
                    identity["current"],
                    {
                        "issue_id": "DUP",
                        "source_paths": duplicate_paths,
                    },
                )
                self.assertIn("duplicate", identity["reason"].lower())
                self.assertIn("unique", identity["recommendation"].lower())
                self.assertEqual(issue["routing_after"]["readiness"], "blocked")
                self.assertEqual(
                    issue["routing_after"]["recommended_next_command"],
                    "product:doctor",
                )
        self.assertEqual(before_hashes, self.project_file_manifest())

    def test_unversioned_identity_collision_with_versioned_record_is_ambiguous(self):
        versioned_path = self.root / "issues" / "BIZ-VERSIONED.md"
        versioned_path.write_text(
            versioned_path.read_text(encoding="utf-8").replace(
                "issue_id: BIZ-VERSIONED", "issue_id: SHARED"
            ),
            encoding="utf-8",
        )
        unversioned_path = self.root / "issues" / "BIZ-UNVERSIONED.md"
        unversioned_path.write_text(
            """---
issue_id: SHARED
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:spec SHARED
---
# Issue: `SHARED` Colliding advisory identity

**Status: backlog**
""",
            encoding="utf-8",
        )

        issue = next(
            item
            for item in self.schema.build_migration_report(self.root)["issues"]
            if item["source_path"] == "issues/BIZ-UNVERSIONED.md"
        )

        self.assertNotIn("set_schema_version", issue["proposed_changes"])
        identity = next(
            decision
            for decision in issue["human_decisions"]
            if decision["field"] == "issue_id"
        )
        self.assertEqual(
            identity["current"],
            {
                "issue_id": "SHARED",
                "source_paths": [
                    "issues/BIZ-UNVERSIONED.md",
                    "issues/BIZ-VERSIONED.md",
                ],
            },
        )
        self.assertEqual(issue["routing_after"]["readiness"], "blocked")
        self.assertEqual(
            issue["routing_after"]["recommended_next_command"],
            "product:doctor",
        )

    def test_complete_identity_collides_with_incomplete_advisory_proposal(self):
        complete = """---
issue_id: ADVISORY-DUP
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:spec ADVISORY-DUP
---
# Issue: `ADVISORY-DUP` Complete proposal

**Status: backlog**
"""
        incomplete = """---
issue_id: ADVISORY-DUP
depends_on: []
---
# Issue: `ADVISORY-DUP` Incomplete proposal

**Status: backlog**
"""
        (self.root / "issues" / "BIZ-UNVERSIONED.md").write_text(
            complete, encoding="utf-8"
        )
        self.write_issue("BIZ-UNVERSIONED-2.md", incomplete)
        source_paths = [
            "issues/BIZ-UNVERSIONED-2.md",
            "issues/BIZ-UNVERSIONED.md",
        ]

        report = self.schema.build_migration_report(self.root)
        by_path = {
            issue["source_path"]: issue for issue in report["issues"]
        }

        for source_path in source_paths:
            with self.subTest(source_path=source_path):
                issue = by_path[source_path]
                self.assertNotIn(
                    "set_schema_version", issue["proposed_changes"]
                )
                identity = next(
                    decision
                    for decision in issue["human_decisions"]
                    if decision["field"] == "issue_id"
                    and isinstance(decision["current"], dict)
                )
                self.assertEqual(
                    identity["current"],
                    {
                        "issue_id": "ADVISORY-DUP",
                        "source_paths": source_paths,
                    },
                )
                self.assertEqual(issue["routing_after"]["readiness"], "blocked")
                self.assertEqual(
                    issue["routing_after"]["recommended_next_command"],
                    "product:doctor",
                )

    def test_blank_dependency_ids_fail_closed_for_versioned_and_unversioned(self):
        self.write_issue(
            "BIZ-BLANK-VERSIONED.md",
            """---
schema_version: 0.1.0
issue_id: BIZ-BLANK-VERSIONED
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: [""]
next_command: product:spec BIZ-BLANK-VERSIONED
---
# Issue: `BIZ-BLANK-VERSIONED` Blank dependency

**Status: backlog**
""",
        )
        self.write_issue(
            "BIZ-BLANK-UNVERSIONED.md",
            """---
issue_id: BIZ-BLANK-UNVERSIONED
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: ["   "]
next_command: product:spec BIZ-BLANK-UNVERSIONED
---
# Issue: `BIZ-BLANK-UNVERSIONED` Whitespace dependency

**Status: backlog**
""",
        )

        report = self.schema.build_migration_report(self.root)
        by_path = {
            issue["source_path"]: issue for issue in report["issues"]
        }
        cases = {
            "issues/BIZ-BLANK-VERSIONED.md": [""],
            "issues/BIZ-BLANK-UNVERSIONED.md": ["   "],
        }
        for source_path, current in cases.items():
            with self.subTest(source_path=source_path):
                normalized = self.schema.parse_issue(
                    self.root / source_path, self.root
                )
                issue = by_path[source_path]
                malformed = next(
                    diagnostic
                    for diagnostic in issue["diagnostics"]
                    if diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
                    and diagnostic["field"] == "depends_on"
                )
                decision = next(
                    item
                    for item in issue["human_decisions"]
                    if item["field"] == "depends_on"
                )

                self.assertEqual(normalized["blocked_by"], [])
                self.assertEqual(normalized["advisory_blocked_by"], [])
                self.assertEqual(malformed["current"], current)
                self.assertEqual(
                    malformed["expected"],
                    "list of non-empty issue ID strings",
                )
                self.assertEqual(decision["current"], current)
                self.assertEqual(decision["expected"], malformed["expected"])
                self.assertIn("blank", decision["recommendation"].lower())
                self.assertNotIn(
                    "depends_on",
                    {mapping["field"] for mapping in issue["safe_mappings"]},
                )
                self.assertNotIn(
                    "set_schema_version", issue["proposed_changes"]
                )
                self.assertEqual(issue["routing_after"]["readiness"], "blocked")
                self.assertEqual(
                    issue["routing_after"]["recommended_next_command"],
                    "product:doctor",
                )

    def test_canonically_empty_backtick_dependencies_fail_closed(self):
        self.write_issue(
            "BIZ-BACKTICK-VERSIONED.md",
            """---
schema_version: 0.1.0
issue_id: BIZ-BACKTICK-VERSIONED
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: ["``"]
next_command: product:spec BIZ-BACKTICK-VERSIONED
---
# Issue: `BIZ-BACKTICK-VERSIONED` Empty backtick dependency

**Status: backlog**
""",
        )
        self.write_issue(
            "BIZ-BACKTICK-UNVERSIONED.md",
            """---
issue_id: BIZ-BACKTICK-UNVERSIONED
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: ["`   `"]
next_command: product:spec BIZ-BACKTICK-UNVERSIONED
---
# Issue: `BIZ-BACKTICK-UNVERSIONED` Whitespace backtick dependency

**Status: backlog**
""",
        )
        legitimate_path = self.write_issue(
            "BIZ-BACKTICK-VALID.md",
            """---
schema_version: 0.1.0
issue_id: BIZ-BACKTICK-VALID
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: ["`BIZ-DEPENDENCY`"]
next_command: product:status
---
# Issue: `BIZ-BACKTICK-VALID` Valid backtick dependency

**Status: backlog**
""",
        )

        report = self.schema.build_migration_report(self.root)
        by_path = {
            issue["source_path"]: issue for issue in report["issues"]
        }
        cases = {
            "issues/BIZ-BACKTICK-VERSIONED.md": ["``"],
            "issues/BIZ-BACKTICK-UNVERSIONED.md": ["`   `"],
        }
        for source_path, current in cases.items():
            with self.subTest(source_path=source_path):
                issue = by_path[source_path]
                decision = next(
                    item
                    for item in issue["human_decisions"]
                    if item["field"] == "depends_on"
                )
                self.assertEqual(decision["current"], current)
                self.assertNotIn(
                    "depends_on",
                    {mapping["field"] for mapping in issue["safe_mappings"]},
                )
                self.assertNotIn(
                    "set_schema_version", issue["proposed_changes"]
                )
                self.assertEqual(issue["routing_after"]["readiness"], "blocked")
                self.assertEqual(
                    issue["routing_after"]["recommended_next_command"],
                    "product:doctor",
                )

        legitimate = self.schema.parse_issue(legitimate_path, self.root)
        self.assertEqual(legitimate["blocked_by"], ["BIZ-DEPENDENCY"])
        self.assertFalse(
            any(
                diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
                and diagnostic["field"] == "depends_on"
                for diagnostic in legitimate["diagnostics"]
            )
        )

    def test_unsupported_tentative_identity_collides_with_versioned_canonical(self):
        versioned = self.root / "issues" / "BIZ-VERSIONED.md"
        versioned.write_text(
            versioned.read_text(encoding="utf-8").replace(
                "issue_id: BIZ-VERSIONED", "issue_id: FUTURE-ID"
            ),
            encoding="utf-8",
        )
        unsupported = self.root / "issues" / "BIZ-UNSUPPORTED.md"
        unsupported.write_text(
            unsupported.read_text(encoding="utf-8").replace(
                "issue_id: BIZ-UNSUPPORTED", "issue_id: FUTURE-ID"
            ),
            encoding="utf-8",
        )

        report = self.schema.build_migration_report(self.root)
        issue = next(
            item
            for item in report["issues"]
            if item["source_path"] == "issues/BIZ-UNSUPPORTED.md"
        )
        identity = next(
            decision
            for decision in issue["human_decisions"]
            if decision["field"] == "issue_id"
        )

        self.assertEqual(issue["issue_id"], "BIZ-UNSUPPORTED")
        self.assertEqual(issue["tentative_issue_id"], "FUTURE-ID")
        self.assertEqual(
            identity["current"],
            {
                "issue_id": "FUTURE-ID",
                "source_paths": [
                    "issues/BIZ-UNSUPPORTED.md",
                    "issues/BIZ-VERSIONED.md",
                ],
            },
        )
        self.assertEqual(issue["routing_after"]["readiness"], "blocked")
        self.assertEqual(
            issue["routing_after"]["recommended_next_command"],
            "product:doctor",
        )

    def test_unsupported_tentative_identity_collides_with_unversioned_proposal(self):
        unsupported = self.root / "issues" / "BIZ-UNSUPPORTED.md"
        unsupported.write_text(
            unsupported.read_text(encoding="utf-8").replace(
                "issue_id: BIZ-UNSUPPORTED", "issue_id: TENTATIVE-ID"
            ),
            encoding="utf-8",
        )
        unversioned = self.root / "issues" / "BIZ-UNVERSIONED.md"
        unversioned.write_text(
            """---
issue_id: TENTATIVE-ID
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:spec TENTATIVE-ID
---
# Issue: `TENTATIVE-ID` Colliding proposal

**Status: backlog**
""",
            encoding="utf-8",
        )
        source_paths = [
            "issues/BIZ-UNSUPPORTED.md",
            "issues/BIZ-UNVERSIONED.md",
        ]

        report = self.schema.build_migration_report(self.root)
        by_path = {
            issue["source_path"]: issue for issue in report["issues"]
        }
        for source_path in source_paths:
            with self.subTest(source_path=source_path):
                issue = by_path[source_path]
                identity = next(
                    decision
                    for decision in issue["human_decisions"]
                    if decision["field"] == "issue_id"
                )
                self.assertEqual(
                    identity["current"],
                    {
                        "issue_id": "TENTATIVE-ID",
                        "source_paths": source_paths,
                    },
                )
                self.assertNotIn(
                    "set_schema_version", issue["proposed_changes"]
                )
                self.assertEqual(issue["routing_after"]["readiness"], "blocked")
                self.assertEqual(
                    issue["routing_after"]["recommended_next_command"],
                    "product:doctor",
                )

    def test_malformed_input_preserves_hard_diagnostics_and_blocked_projection(self):
        self.write_issue(
            "BIZ-MALFORMED.md",
            "---\nschema_version: [9]\n---\n"
            "# Issue: `BIZ-MALFORMED` Malformed\n\n**Status: backlog**\n",
        )

        issue = self.by_id(
            self.schema.build_migration_report(self.root)
        )["BIZ-MALFORMED"]

        self.assertIn(
            "ISSUE_SCHEMA_MALFORMED",
            {diagnostic["code"] for diagnostic in issue["diagnostics"]},
        )
        decision = next(
            item
            for item in issue["human_decisions"]
            if item["field"] == "schema_version"
        )
        self.assertEqual(decision["current"], [9])
        self.assertEqual(decision["expected"], "string")
        self.assertIn("schema_version", decision["recommendation"])
        self.assertEqual(issue["routing_after"]["readiness"], "blocked")
        self.assertEqual(
            issue["routing_after"]["recommended_next_command"], "product:doctor"
        )

    def test_distinct_same_field_malformed_decisions_are_preserved(self):
        self.write_issue(
            "BIZ-MULTI-MALFORMED.md",
            """---
schema_version: [9]
schema_version: 9.9.9
---
# Issue: `BIZ-MULTI-MALFORMED` Multiple schema failures

**Status: backlog**
""",
        )

        issue = next(
            item
            for item in self.schema.build_migration_report(self.root)["issues"]
            if item["source_path"] == "issues/BIZ-MULTI-MALFORMED.md"
        )
        malformed_decisions = [
            decision
            for decision in issue["human_decisions"]
            if decision["field"] == "schema_version"
            and "expected" in decision
        ]

        self.assertEqual(len(malformed_decisions), 2)
        self.assertEqual(
            {repr(decision["current"]) for decision in malformed_decisions},
            {"None", "[9]"},
        )
        self.assertEqual(
            len(
                {
                    (
                        decision["field"],
                        repr(decision["current"]),
                        decision["reason"],
                        decision["recommendation"],
                    )
                    for decision in malformed_decisions
                }
            ),
            2,
        )

    def test_cli_prints_json_only_returns_zero_and_does_not_write(self):
        before_hashes = self.project_file_manifest()
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = self.schema.main([str(self.root), "--report"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema"], "moduflow.issue-migration-report.v1")
        self.assertEqual(before_hashes, self.project_file_manifest())

    def test_file_creation_order_does_not_change_report(self):
        logical_files = {
            "issues/A.md": (
                "# Issue: `A` Stable ordering\n\n"
                "**Status: backlog** — created 2026-07-24.\n"
            ),
            "issues/B.md": """---
schema_version: 9.9.9
issue_id: FUTURE-B
---
# Issue: `B` Unsupported

**Status: backlog**
""",
            "specs/A/spec.md": "# Spec\n",
        }

        reports = []
        roots = []
        for reverse in (False, True):
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            root = Path(temporary.name)
            roots.append(root)
            items = sorted(logical_files.items(), reverse=reverse)
            for relative_path, content in items:
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            report = self.schema.build_migration_report(root)
            report["project_root"] = "<project-root>"
            reports.append(report)

        self.assertNotEqual(str(roots[0]), str(roots[1]))
        self.assertEqual(reports[0], reports[1])

    def test_cli_rejects_write_and_returns_stable_json_for_invalid_root(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                self.schema.main([str(self.root), "--report", "--write"])

        stdout = io.StringIO()
        missing = self.root / "missing"
        with contextlib.redirect_stdout(stdout):
            exit_code = self.schema.main([str(missing), "--report"])

        payload = json.loads(stdout.getvalue())
        self.assertNotEqual(exit_code, 0)
        self.assertEqual(
            payload["schema"], "moduflow.issue-migration-report.error.v1"
        )
        self.assertEqual(payload["error"]["code"], "PROJECT_ROOT_INVALID")


class ProjectIssueIdBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_module(
            "project_issue_schema_issue_id_boundary",
            "scripts/project_issue_schema.py",
        )

    def write_versioned_issue(self, root, filename, issue_id, dependencies=()):
        (root / "issues").mkdir(parents=True, exist_ok=True)
        dependency_text = ", ".join(dependencies)
        (root / "issues" / filename).write_text(
            f"""---
schema_version: 0.1.0
issue_id: {issue_id}
canonical_state: active
status: in_progress
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: [{dependency_text}]
next_command: product:execute {issue_id}
---
# Issue: `{issue_id}` Boundary fixture

**Status: active** — created 2026-07-25.
""",
            encoding="utf-8",
        )

    def test_validate_issue_id_accepts_legal_filename_stems(self):
        for issue_id in (
            "0",
            "BIZ-033",
            "093-frontmatter-issue-schema-readiness-gate",
            "alpha_beta",
            "alpha.beta",
        ):
            with self.subTest(issue_id=issue_id):
                self.assertTrue(self.schema.validate_issue_id(issue_id))

    def test_validate_issue_id_rejects_path_tokens(self):
        for issue_id in (
            "",
            ".",
            "..",
            "../../outside",
            "/tmp/outside",
            "folder/issue",
            r"folder\issue",
            "-leading-hyphen",
        ):
            with self.subTest(issue_id=issue_id):
                self.assertFalse(self.schema.validate_issue_id(issue_id))

    def test_frontmatter_path_tokens_are_malformed_and_route_to_doctor(self):
        for malicious_id in (
            "../../outside",
            "/tmp/outside",
            "folder/issue",
            r"folder\issue",
            ".",
            "..",
        ):
            with self.subTest(issue_id=malicious_id), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.write_versioned_issue(root, "SAFE.md", malicious_id)

                issue = self.schema.evaluate_project(root)["issues"][0]

                self.assertEqual(issue["issue_id"], "SAFE")
                self.assertIn("ISSUE_SCHEMA_MALFORMED", codes(issue))
                self.assertTrue(
                    any(
                        diagnostic["field"] == "issue_id"
                        for diagnostic in issue["diagnostics"]
                    )
                )
                self.assertEqual(
                    issue["recommended_next_command"],
                    "product:doctor",
                )

    def test_dependency_path_injection_is_malformed_and_routes_to_doctor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_versioned_issue(
                root,
                "BIZ-WORK.md",
                "BIZ-WORK",
                dependencies=("../../outside",),
            )

            issue = self.schema.evaluate_project(root)["issues"][0]

        self.assertEqual(issue["blocked_by"], [])
        self.assertIn("ISSUE_SCHEMA_MALFORMED", codes(issue))
        self.assertTrue(
            any(
                diagnostic["field"] == "depends_on"
                for diagnostic in issue["diagnostics"]
            )
        )
        self.assertEqual(issue["recommended_next_command"], "product:doctor")

    def test_external_issue_symlink_is_blocked_before_content_is_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "project"
            outside = base / "outside-secret.md"
            root.mkdir()
            outside.write_text(
                """---
schema_version: 0.1.0
issue_id: BIZ-LINK
canonical_state: active
status: in_progress
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:execute BIZ-LINK
external_secret: DO-NOT-EXPOSE-ISSUE-SECRET
---
# Issue: `BIZ-LINK` DO-NOT-EXPOSE-ISSUE-TITLE

**Status: active**
""",
                encoding="utf-8",
            )
            (root / "issues").mkdir()
            (root / "issues" / "BIZ-LINK.md").symlink_to(outside)

            project = self.schema.evaluate_project(root)
            issue = project["issues"][0]
            serialized = json.dumps(project, ensure_ascii=False)

        self.assertEqual(issue["issue_id"], "BIZ-LINK")
        self.assertEqual(issue["source_path"], "issues/BIZ-LINK.md")
        self.assertEqual(issue["title"], "")
        self.assertEqual(issue["extensions"], {})
        self.assertNotIn("DO-NOT-EXPOSE", serialized)
        self.assertIn("ISSUE_SOURCE_OUTSIDE_ROOT", codes(issue))
        self.assertEqual(issue["recommended_next_command"], "product:doctor")

    def test_internal_issue_symlink_is_allowed_with_lexical_source_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_dir = root / "issues" / "targets"
            target_dir.mkdir(parents=True)
            self.write_versioned_issue(
                target_dir.parent.parent,
                "targets/BIZ-INTERNAL-SOURCE.md",
                "BIZ-INTERNAL",
            )
            (root / "issues" / "BIZ-INTERNAL.md").symlink_to(
                target_dir / "BIZ-INTERNAL-SOURCE.md"
            )

            issue = next(
                item
                for item in self.schema.evaluate_project(root)["issues"]
                if item["issue_id"] == "BIZ-INTERNAL"
            )

        self.assertEqual(issue["source_path"], "issues/BIZ-INTERNAL.md")
        self.assertNotIn("ISSUE_SOURCE_OUTSIDE_ROOT", codes(issue))
        self.assertIn("Boundary fixture", issue["title"])

    def test_external_spec_directory_is_a_per_issue_hard_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "project"
            outside = base / "outside-specs"
            root.mkdir()
            outside.mkdir()
            self.write_versioned_issue(root, "BIZ-SPEC-LINK.md", "BIZ-SPEC-LINK")
            for phase in ("spec", "plan", "tasks"):
                (outside / f"{phase}.md").write_text(
                    f"# DO-NOT-EXPOSE-{phase.upper()}-SECRET\n",
                    encoding="utf-8",
                )
            (root / "specs").mkdir()
            (root / "specs" / "BIZ-SPEC-LINK").symlink_to(
                outside,
                target_is_directory=True,
            )

            project = self.schema.evaluate_project(root)
            issue = project["issues"][0]
            serialized = json.dumps(project, ensure_ascii=False)

        self.assertNotIn("DO-NOT-EXPOSE", serialized)
        self.assertEqual(issue["artifact_phase"], "issue")
        self.assertIn("ISSUE_ARTIFACT_OUTSIDE_ROOT", codes(issue))
        self.assertEqual(issue["recommended_next_command"], "product:doctor")

    def test_external_artifact_file_symlinks_are_blocked_per_phase(self):
        for linked_phase in ("spec", "plan", "tasks"):
            with self.subTest(phase=linked_phase), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                root = base / "project"
                outside = base / f"outside-{linked_phase}.md"
                root.mkdir()
                self.write_versioned_issue(
                    root,
                    "BIZ-ARTIFACT-LINK.md",
                    "BIZ-ARTIFACT-LINK",
                )
                artifact_root = root / "specs" / "BIZ-ARTIFACT-LINK"
                artifact_root.mkdir(parents=True)
                outside.write_text(
                    f"# DO-NOT-EXPOSE-{linked_phase.upper()}-SECRET\n",
                    encoding="utf-8",
                )
                for phase in ("spec", "plan", "tasks"):
                    path = artifact_root / f"{phase}.md"
                    if phase == linked_phase:
                        path.symlink_to(outside)
                    else:
                        path.write_text(f"# {phase}\n", encoding="utf-8")

                project = self.schema.evaluate_project(root)
                issue = project["issues"][0]
                serialized = json.dumps(project, ensure_ascii=False)

                self.assertNotIn("DO-NOT-EXPOSE", serialized)
                self.assertIn("ISSUE_ARTIFACT_OUTSIDE_ROOT", codes(issue))
                self.assertTrue(
                    any(
                        diagnostic["current"]
                        == f"specs/BIZ-ARTIFACT-LINK/{linked_phase}.md"
                        for diagnostic in issue["diagnostics"]
                    )
                )
                self.assertEqual(
                    issue["recommended_next_command"],
                    "product:doctor",
                )

    def test_internal_artifact_file_symlinks_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_versioned_issue(
                root,
                "BIZ-INTERNAL-ARTIFACT.md",
                "BIZ-INTERNAL-ARTIFACT",
            )
            shared = root / "specs" / "shared"
            artifact_root = root / "specs" / "BIZ-INTERNAL-ARTIFACT"
            shared.mkdir(parents=True)
            artifact_root.mkdir()
            for phase in ("spec", "plan", "tasks"):
                target = shared / f"{phase}.md"
                target.write_text(f"# {phase}\n", encoding="utf-8")
                (artifact_root / f"{phase}.md").symlink_to(target)

            issue = self.schema.evaluate_project(root)["issues"][0]

        self.assertNotIn("ISSUE_ARTIFACT_OUTSIDE_ROOT", codes(issue))
        self.assertEqual(issue["recommended_next_command"], "product:execute BIZ-INTERNAL-ARTIFACT")

    def test_internal_spec_directory_symlink_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_versioned_issue(
                root,
                "BIZ-INTERNAL-SPEC-DIR.md",
                "BIZ-INTERNAL-SPEC-DIR",
            )
            shared = root / "specs" / "shared"
            shared.mkdir(parents=True)
            for phase in ("spec", "plan", "tasks"):
                (shared / f"{phase}.md").write_text(
                    f"# {phase}\n",
                    encoding="utf-8",
                )
            (root / "specs" / "BIZ-INTERNAL-SPEC-DIR").symlink_to(
                shared,
                target_is_directory=True,
            )

            issue = self.schema.evaluate_project(root)["issues"][0]

        self.assertNotIn("ISSUE_ARTIFACT_OUTSIDE_ROOT", codes(issue))
        self.assertEqual(
            issue["recommended_next_command"],
            "product:execute BIZ-INTERNAL-SPEC-DIR",
        )


if __name__ == "__main__":
    unittest.main()
