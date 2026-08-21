import json
import tempfile
import unittest
from pathlib import Path

from scripts import canonical_path_guard


CLASSIFICATION_SCHEMA = "moduflow.canonical-path-classifications.v1"


class CanonicalPathGuardTests(unittest.TestCase):
    def write_project(self, source, entries=()):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "scripts").mkdir()
        (root / "config").mkdir()
        (root / "scripts" / "consumer.py").write_text(source, encoding="utf-8")
        (root / "config" / "canonical-path-literals.json").write_text(
            json.dumps(
                {"schema": CLASSIFICATION_SCHEMA, "entries": list(entries)}
            ),
            encoding="utf-8",
        )
        return temporary, root

    def test_unclassified_direct_role_join_fails(self):
        temporary, root = self.write_project('target = root / "issues"\n')
        self.addCleanup(temporary.cleanup)

        result = canonical_path_guard.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertEqual(result["findings"][0]["pattern"], "join:issues")

    def test_unused_classification_is_stale(self):
        temporary, root = self.write_project(
            "value = 1\n",
            [
                {
                    "module": "scripts/consumer.py",
                    "pattern": "join:issues",
                    "classification": "test_fixture",
                    "rationale": "Temporary fixture layout.",
                }
            ],
        )
        self.addCleanup(temporary.cleanup)

        result = canonical_path_guard.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(len(result["stale_entries"]), 1)

    def test_missing_classification_file_fails_closed_without_raising(self):
        temporary, root = self.write_project("value = 1\n")
        self.addCleanup(temporary.cleanup)
        (root / "config" / "canonical-path-literals.json").unlink()

        result = canonical_path_guard.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any("classification file" in error for error in result["errors"]),
            result,
        )

    def test_reviewed_default_string_fragment_passes(self):
        temporary, root = self.write_project(
            'CANONICAL_PATH_DEFAULTS = {"issues": "issues/"}\n',
            [
                {
                    "module": "scripts/consumer.py",
                    "pattern": "fragment:issues/",
                    "classification": "canonical_default_declaration",
                    "rationale": "Declares the compatibility default only.",
                }
            ],
        )
        self.addCleanup(temporary.cleanup)

        result = canonical_path_guard.inspect_project(root)

        self.assertTrue(result["valid"])
        self.assertEqual(result["counts"]["classified"], 1)

    def test_runtime_role_join_cannot_hide_as_default_declaration(self):
        temporary, root = self.write_project(
            'target = root / "issues"\n',
            [
                {
                    "module": "scripts/consumer.py",
                    "pattern": "join:issues",
                    "classification": "canonical_default_declaration",
                    "rationale": "This is actually runtime target I/O.",
                }
            ],
        )
        self.addCleanup(temporary.cleanup)

        result = canonical_path_guard.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["prohibited"], 1)

    def test_current_repository_has_only_reviewed_findings(self):
        root = Path(__file__).resolve().parents[1]

        result = canonical_path_guard.inspect_project(root)

        self.assertTrue(result["valid"], result)


if __name__ == "__main__":
    unittest.main()
