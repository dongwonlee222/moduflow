import importlib.util
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

        self.assertEqual(current["BIZ-A1"], "BIZ-A1, BIZ-A2")
        self.assertEqual(current["BIZ-A2"], "BIZ-A1, BIZ-A2")
        self.assertEqual(current["BIZ-B1"], "BIZ-B1, BIZ-B2")
        self.assertEqual(current["BIZ-B2"], "BIZ-B1, BIZ-B2")

    def test_cycle_diagnostics_include_complete_strongly_connected_component(self):
        issue_index = {
            "BIZ-A": {
                "issue_id": "BIZ-A",
                "source_path": "issues/BIZ-A.md",
                "lifecycle_state": "done",
                "blocked_by": ["BIZ-B", "BIZ-C"],
                "advisory_blocked_by": [],
            },
            "BIZ-B": {
                "issue_id": "BIZ-B",
                "source_path": "issues/BIZ-B.md",
                "lifecycle_state": "done",
                "blocked_by": ["BIZ-A"],
                "advisory_blocked_by": [],
            },
            "BIZ-C": {
                "issue_id": "BIZ-C",
                "source_path": "issues/BIZ-C.md",
                "lifecycle_state": "done",
                "blocked_by": ["BIZ-B"],
                "advisory_blocked_by": [],
            },
        }

        diagnostics = self.schema.dependency_diagnostics(issue_index)
        repeated = self.schema.dependency_diagnostics(issue_index)

        expected = {
            issue_id: [("ISSUE_DEPENDENCY_CYCLE", "BIZ-A, BIZ-B, BIZ-C")]
            for issue_id in ("BIZ-A", "BIZ-B", "BIZ-C")
        }
        actual = {
            issue_id: [
                (diagnostic["code"], diagnostic["current"])
                for diagnostic in issue_diagnostics
            ]
            for issue_id, issue_diagnostics in diagnostics.items()
        }
        self.assertEqual(actual, expected)
        self.assertEqual(repeated, diagnostics)

    def test_unfinished_dependency_blocks_active_issue(self):
        self.write_versioned("BIZ-BLOCKER")
        self.write_versioned(
            "BIZ-ACTIVE", lifecycle="active", dependencies=("BIZ-BLOCKER",)
        )

        issue = self.evaluated_by_id()["BIZ-ACTIVE"]

        self.assertEqual(issue["readiness"], "blocked")
        self.assertEqual(issue["recommended_next_command"], "product:status")
        self.assertIn("ISSUE_DEPENDENCY_UNMET", codes(issue))

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


if __name__ == "__main__":
    unittest.main()
