import json
import tempfile
import unittest
from pathlib import Path

from scripts import project_operation_audit


SCHEMA = "moduflow.project-operation-entrypoints.v1"


class ProjectOperationAuditTests(unittest.TestCase):
    def project(self, source, entries=()):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "scripts").mkdir()
        (root / "config").mkdir()
        (root / "scripts" / "consumer.py").write_text(source, encoding="utf-8")
        (root / "config" / "project-operation-entrypoints.json").write_text(
            json.dumps({"schema": SCHEMA, "entries": list(entries)}),
            encoding="utf-8",
        )
        self.addCleanup(temporary.cleanup)
        return root

    def entry(
        self,
        function,
        *,
        mode="write",
        scope="target-project",
        operation="write",
        classification="guarded_boundary",
        guard_owner=None,
    ):
        return {
            "module": "scripts/consumer.py",
            "function": function,
            "mode": mode,
            "scope": scope,
            "operation": operation,
            "classification": classification,
            "guard_owner": guard_owner if guard_owner is not None else function,
            "rationale": "Controlled fixture mutation boundary.",
        }

    def test_unclassified_file_mutation_fails(self):
        root = self.project(
            "def write_record(path):\n    path.write_text('x', encoding='utf-8')\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertEqual(result["unclassified"][0]["function"], "write_record")
        self.assertIn("write_text", result["unclassified"][0]["mutation_kinds"])

    def test_github_create_runner_call_is_discovered_as_external_mutation(self):
        root = self.project(
            "def publish(runner, root):\n"
            "    return runner(['gh', 'issue', 'create', '--title', 'x'], root)\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertIn("gh:issue:create", result["unclassified"][0]["mutation_kinds"])

    def test_external_command_prefix_is_discovered_when_tail_contains_variables(self):
        root = self.project(
            "def publish(runner, root, title):\n"
            "    args = ['gh', 'issue', 'create', '--title', title]\n"
            "    return runner(args, root)\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertIn("gh:issue:create", result["unclassified"][0]["mutation_kinds"])

    def test_missing_function_entry_is_stale(self):
        root = self.project(
            "def inspect():\n    return {}\n",
            [self.entry("removed_writer")],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["stale"], 1)
        self.assertEqual(result["stale_entries"][0]["function"], "removed_writer")

    def test_duplicate_exact_entry_fails(self):
        entry = self.entry("write_record")
        root = self.project(
            "def write_record(path):\n    path.write_text('x', encoding='utf-8')\n",
            [entry, dict(entry)],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["duplicates"], 1)

    def test_target_mutator_without_central_guard_fails(self):
        root = self.project(
            "def write_record(path):\n    path.write_text('x', encoding='utf-8')\n",
            [self.entry("write_record")],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unguarded"], 1)
        self.assertEqual(result["unguarded"][0]["guard_owner"], "write_record")

    def test_internal_helper_passes_when_concrete_owner_uses_guard(self):
        root = self.project(
            "def _write(path):\n"
            "    path.write_text('x', encoding='utf-8')\n\n"
            "def create(path, context):\n"
            "    project_operation.require_project_capability(context, 'write')\n"
            "    _write(path)\n",
            [
                self.entry(
                    "_write",
                    classification="internal_guarded_helper",
                    guard_owner="create",
                )
            ],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertTrue(result["valid"], result)
        self.assertEqual(result["counts"]["classified"], 1)
        self.assertEqual(result["counts"]["unguarded"], 0)

    def test_invalid_scope_and_operation_fail_closed(self):
        root = self.project(
            "def write_record(path, context):\n"
            "    project_operation.require_project_capability(context, 'write')\n"
            "    path.write_text('x', encoding='utf-8')\n",
            [
                self.entry(
                    "write_record",
                    scope="mystery",
                    operation="delete-everything",
                )
            ],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["configuration_errors"], 2)


if __name__ == "__main__":
    unittest.main()
