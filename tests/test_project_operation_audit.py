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

    def multi_module_project(self, sources, entries=()):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "scripts").mkdir()
        (root / "config").mkdir()
        for relative_path, source in sources.items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")
        (root / "config" / "project-operation-entrypoints.json").write_text(
            json.dumps({"schema": SCHEMA, "entries": list(entries)}),
            encoding="utf-8",
        )
        self.addCleanup(temporary.cleanup)
        return root

    def transaction_entry(self, function="persist", *, owners=None):
        return {
            "module": "scripts/storage.py",
            "function": function,
            "mode": "transaction-apply",
            "scope": "target-project",
            "operation": "write",
            "classification": "transaction_persistence",
            "guard_owners": owners
            if owners is not None
            else [{"module": "scripts/boundary.py", "function": "apply"}],
            "rationale": "Persists only under a guarded transaction boundary.",
        }

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

    def test_guard_after_mutation_fails(self):
        root = self.project(
            "def write_record(path, context):\n"
            "    path.write_text('x', encoding='utf-8')\n"
            "    project_operation.require_project_capability(context, 'write')\n",
            [self.entry("write_record")],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unguarded"], 1)

    def test_conditional_guard_does_not_cover_unconditional_mutation(self):
        root = self.project(
            "def write_record(path, context, allowed):\n"
            "    if allowed:\n"
            "        project_operation.require_project_capability(context, 'write')\n"
            "    path.write_text('x', encoding='utf-8')\n",
            [self.entry("write_record")],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unguarded"], 1)

    def test_wrong_guard_operation_fails(self):
        root = self.project(
            "def write_record(path, context):\n"
            "    project_operation.require_project_capability(context, 'read')\n"
            "    path.write_text('x', encoding='utf-8')\n",
            [self.entry("write_record", operation="write")],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unguarded"], 1)

    def test_internal_helper_owner_must_reach_helper_after_guard(self):
        root = self.project(
            "def _write(path):\n"
            "    path.write_text('x', encoding='utf-8')\n\n"
            "def unrelated(path, context):\n"
            "    project_operation.require_project_capability(context, 'write')\n",
            [
                self.entry(
                    "_write",
                    classification="internal_guarded_helper",
                    guard_owner="unrelated",
                )
            ],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unguarded"], 1)

    def test_transaction_persistence_accepts_qualified_owner_and_delegated_guard(self):
        root = self.multi_module_project(
            {
                "scripts/boundary.py": (
                    "from scripts import storage\n\n"
                    "def _authorize(context):\n"
                    "    project_operation.require_project_capability(context, 'write')\n\n"
                    "def apply(path, context):\n"
                    "    _authorize(context)\n"
                    "    storage.persist(path)\n"
                ),
                "scripts/storage.py": (
                    "def persist(path):\n"
                    "    path.write_text('x', encoding='utf-8')\n"
                ),
            },
            [self.transaction_entry()],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertTrue(result["valid"], result)
        self.assertEqual(result["counts"]["classified"], 1)
        self.assertEqual(result["counts"]["unguarded"], 0)

    def test_transaction_persistence_guard_must_precede_owner_path(self):
        root = self.multi_module_project(
            {
                "scripts/boundary.py": (
                    "from scripts import storage\n\n"
                    "def _authorize(context):\n"
                    "    project_operation.require_project_capability(context, 'write')\n\n"
                    "def apply(path, context):\n"
                    "    storage.persist(path)\n"
                    "    _authorize(context)\n"
                ),
                "scripts/storage.py": (
                    "def persist(path):\n"
                    "    path.write_text('x', encoding='utf-8')\n"
                ),
            },
            [self.transaction_entry()],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unguarded"], 1)

    def test_transaction_persistence_accepts_guarded_try_with_terminating_handler(self):
        root = self.multi_module_project(
            {
                "scripts/boundary.py": (
                    "from scripts import storage\n\n"
                    "def _authorize(context):\n"
                    "    project_operation.require_project_capability(context, 'write')\n\n"
                    "def apply(path, context):\n"
                    "    try:\n"
                    "        _authorize(context)\n"
                    "    except PermissionError:\n"
                    "        return {'status': 'denied'}\n"
                    "    storage.persist(path)\n"
                ),
                "scripts/storage.py": (
                    "def persist(path):\n"
                    "    path.write_text('x', encoding='utf-8')\n"
                ),
            },
            [self.transaction_entry()],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertTrue(result["valid"], result)

    def test_transaction_persistence_rejects_guarded_try_with_continuing_handler(self):
        root = self.multi_module_project(
            {
                "scripts/boundary.py": (
                    "from scripts import storage\n\n"
                    "def _authorize(context):\n"
                    "    project_operation.require_project_capability(context, 'write')\n\n"
                    "def apply(path, context):\n"
                    "    try:\n"
                    "        _authorize(context)\n"
                    "    except PermissionError:\n"
                    "        pass\n"
                    "    storage.persist(path)\n"
                ),
                "scripts/storage.py": (
                    "def persist(path):\n"
                    "    path.write_text('x', encoding='utf-8')\n"
                ),
            },
            [self.transaction_entry()],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unguarded"], 1)

    def test_transaction_persistence_delegated_guard_requires_declared_operation(self):
        root = self.multi_module_project(
            {
                "scripts/boundary.py": (
                    "from scripts import storage\n\n"
                    "def _authorize(context):\n"
                    "    project_operation.require_project_capability(context, 'read')\n\n"
                    "def apply(path, context):\n"
                    "    _authorize(context)\n"
                    "    storage.persist(path)\n"
                ),
                "scripts/storage.py": (
                    "def persist(path):\n"
                    "    path.write_text('x', encoding='utf-8')\n"
                ),
            },
            [self.transaction_entry()],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unguarded"], 1)

    def test_transaction_persistence_owner_must_reach_exact_mutator(self):
        root = self.multi_module_project(
            {
                "scripts/boundary.py": (
                    "def _authorize(context):\n"
                    "    project_operation.require_project_capability(context, 'write')\n\n"
                    "def apply(path, context):\n"
                    "    _authorize(context)\n"
                ),
                "scripts/storage.py": (
                    "def persist(path):\n"
                    "    path.write_text('x', encoding='utf-8')\n"
                ),
            },
            [self.transaction_entry()],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"]["unguarded"], 1)

    def test_transaction_persistence_requires_well_formed_owners(self):
        root = self.multi_module_project(
            {
                "scripts/storage.py": (
                    "def persist(path):\n"
                    "    path.write_text('x', encoding='utf-8')\n"
                ),
            },
            [self.transaction_entry(owners=[])],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertGreater(result["counts"]["configuration_errors"], 0)

    def test_legacy_adapter_direct_write_remains_unclassified(self):
        root = self.multi_module_project(
            {
                "scripts/boundary.py": (
                    "from scripts import storage\n\n"
                    "def _authorize(context):\n"
                    "    project_operation.require_project_capability(context, 'write')\n\n"
                    "def apply(path, context):\n"
                    "    _authorize(context)\n"
                    "    storage.persist(path)\n"
                ),
                "scripts/storage.py": (
                    "def persist(path):\n"
                    "    path.write_text('x', encoding='utf-8')\n"
                ),
                "scripts/legacy.py": (
                    "from scripts import boundary\n\n"
                    "def sync(path, context):\n"
                    "    boundary.apply(path, context)\n"
                    "    path.write_text('bypass', encoding='utf-8')\n"
                ),
            },
            [self.transaction_entry()],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any(
                item["module"] == "scripts/legacy.py"
                and item["function"] == "sync"
                for item in result["unclassified"]
            ),
            result,
        )

    def test_request_data_is_discovered_as_post(self):
        root = self.project(
            "import urllib.request\n\n"
            "def publish(url, payload):\n"
            "    return urllib.request.Request(url, data=payload)\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertIn("network:POST", result["unclassified"][0]["mutation_kinds"])

    def test_class_method_network_mutation_is_discovered(self):
        root = self.project(
            "import urllib.request\n\n"
            "class Client:\n"
            "    def publish(self, url, payload):\n"
            "        return urllib.request.Request(url, data=payload)\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertEqual(result["unclassified"][0]["function"], "Client.publish")
        self.assertIn("network:POST", result["unclassified"][0]["mutation_kinds"])

    def test_external_control_surface_requires_explicit_non_project_classification(self):
        entry = self.entry(
            "publish",
            scope="external-control",
            operation="publish",
            classification="external_control",
            guard_owner="",
        )
        entry["rationale"] = "Standalone transport has no selected target project."
        root = self.project(
            "import urllib.request\n\n"
            "def publish(url, payload):\n"
            "    return urllib.request.Request(url, data=payload)\n",
            [entry],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertTrue(result["valid"], result)
        self.assertEqual(result["counts"]["classified"], 1)

    def test_external_control_cannot_exempt_mixed_file_and_network_mutation(self):
        entry = self.entry(
            "publish",
            scope="external-control",
            operation="publish",
            classification="external_control",
            guard_owner="",
        )
        entry["rationale"] = "Standalone transport has no selected target project."
        root = self.project(
            "import urllib.request\n\n"
            "def publish(path, url, payload):\n"
            "    path.write_text('x', encoding='utf-8')\n"
            "    return urllib.request.Request(url, data=payload)\n",
            [entry],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any("network-only" in error for error in result["configuration_errors"]),
            result,
        )

    def test_open_write_modes_are_discovered(self):
        root = self.project(
            "def write_files(path):\n"
            "    open(path, 'w', encoding='utf-8')\n"
            "    path.open(mode='ab')\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        kinds = result["unclassified"][0]["mutation_kinds"]
        self.assertIn("open:w", kinds)
        self.assertIn("open:a", kinds)

    def test_os_open_create_flags_and_tempfile_creation_are_discovered(self):
        root = self.project(
            "import os\n"
            "import tempfile\n\n"
            "def create_files(path):\n"
            "    os.open(path, os.O_CREAT | os.O_WRONLY)\n"
            "    tempfile.mkstemp()\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        kinds = result["unclassified"][0]["mutation_kinds"]
        self.assertIn("os.open:create", kinds)
        self.assertIn("tempfile.mkstemp", kinds)

    def test_assigned_and_imported_os_open_flags_are_discovered(self):
        root = self.project(
            "from os import O_CREAT, O_WRONLY\n"
            "import os\n\n"
            "def create_file(path):\n"
            "    flags = O_CREAT | O_WRONLY\n"
            "    os.open(path, flags)\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertIn(
            "os.open:create",
            result["unclassified"][0]["mutation_kinds"],
        )

    def test_composed_read_only_os_open_flags_are_not_mutations(self):
        root = self.project(
            "import os\n\n"
            "def read_file(path):\n"
            "    read_flags = os.O_RDONLY | getattr(os, 'O_CLOEXEC', 0)\n"
            "    no_follow = getattr(os, 'O_NOFOLLOW', 0)\n"
            "    directory_flags = (\n"
            "        read_flags | no_follow | getattr(os, 'O_DIRECTORY', 0)\n"
            "    )\n"
            "    return os.open(path, directory_flags)\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertTrue(result["valid"], result)
        self.assertEqual(result["counts"]["findings"], 0)

    def test_assigned_literal_and_unresolved_open_modes_fail_closed(self):
        root = self.project(
            "def write_files(first, second, dynamic_mode):\n"
            "    append_mode = 'a'\n"
            "    open(first, append_mode)\n"
            "    second.open(dynamic_mode)\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        kinds = result["unclassified"][0]["mutation_kinds"]
        self.assertIn("open:a", kinds)
        self.assertIn("open:dynamic", kinds)

    def test_external_control_cannot_hide_assigned_flag_file_creation(self):
        entry = self.entry(
            "publish",
            scope="external-control",
            operation="publish",
            classification="external_control",
            guard_owner="",
        )
        entry["rationale"] = "Standalone transport has no selected target project."
        root = self.project(
            "import os\n"
            "import urllib.request\n\n"
            "def publish(path, url, payload):\n"
            "    flags = os.O_CREAT | os.O_WRONLY\n"
            "    os.open(path, flags)\n"
            "    return urllib.request.Request(url, data=payload)\n",
            [entry],
        )

        result = project_operation_audit.inspect_project(root)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any("network-only" in error for error in result["configuration_errors"]),
            result,
        )

    def test_assignments_after_open_call_cannot_rewrite_reaching_mode(self):
        root = self.project(
            "def write_file(path):\n"
            "    mode = 'w'\n"
            "    open(path, mode)\n"
            "    mode = 'r'\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertIn("open:w", result["unclassified"][0]["mutation_kinds"])

    def test_assignments_after_os_open_call_cannot_rewrite_reaching_flags(self):
        root = self.project(
            "import os\n\n"
            "def create_file(path):\n"
            "    flags = os.O_CREAT | os.O_WRONLY\n"
            "    os.open(path, flags)\n"
            "    flags = os.O_RDONLY\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertIn(
            "os.open:create",
            result["unclassified"][0]["mutation_kinds"],
        )

    def test_augmented_open_flags_fail_closed_as_dynamic(self):
        root = self.project(
            "import os\n\n"
            "def create_file(path):\n"
            "    flags = os.O_RDONLY\n"
            "    flags |= os.O_CREAT\n"
            "    os.open(path, flags)\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        self.assertIn(
            "os.open:dynamic",
            result["unclassified"][0]["mutation_kinds"],
        )

    def test_nested_local_assignment_cannot_contaminate_outer_open_mode(self):
        root = self.project(
            "mode = 'w'\n\n"
            "def outer(path):\n"
            "    def inner():\n"
            "        mode = 'r'\n"
            "        return mode\n"
            "    open(path, mode)\n"
        )

        result = project_operation_audit.inspect_project(root)

        outer = next(
            item for item in result["unclassified"] if item["function"] == "outer"
        )
        self.assertIn("open:dynamic", outer["mutation_kinds"])

    def test_nested_mutator_is_a_separate_audit_surface(self):
        root = self.project(
            "def outer(path):\n"
            "    def inner():\n"
            "        path.write_text('x', encoding='utf-8')\n"
            "    inner()\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertTrue(
            any(
                item["function"] == "outer.<locals>.inner"
                and "write_text" in item["mutation_kinds"]
                for item in result["unclassified"]
            ),
            result,
        )

    def test_invoked_lambda_mutation_is_attributed_to_outer_surface(self):
        root = self.project(
            "def outer(path):\n"
            "    (lambda: path.write_text('x', encoding='utf-8'))()\n"
        )

        result = project_operation_audit.inspect_project(root)

        outer = next(
            item for item in result["unclassified"] if item["function"] == "outer"
        )
        self.assertIn("write_text", outer["mutation_kinds"])

    def test_copy_move_and_symlink_surfaces_are_discovered(self):
        root = self.project(
            "import os\n"
            "import shutil\n\n"
            "def stage(source, target):\n"
            "    shutil.copy2(source, target)\n"
            "    shutil.move(source, target)\n"
            "    os.symlink(source, target)\n"
        )

        result = project_operation_audit.inspect_project(root)

        self.assertEqual(result["counts"]["unclassified"], 1)
        kinds = result["unclassified"][0]["mutation_kinds"]
        self.assertIn("shutil.copy2", kinds)
        self.assertIn("shutil.move", kinds)
        self.assertIn("os.symlink", kinds)

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

    def test_current_repository_has_zero_operation_audit_gaps(self):
        root = Path(__file__).resolve().parents[1]

        result = project_operation_audit.inspect_project(root)
        inventory = json.loads(
            (root / "config" / "project-operation-entrypoints.json").read_text(
                encoding="utf-8"
            )
        )["entries"]

        self.assertTrue(result["valid"], result)
        self.assertEqual(
            {
                key: result["counts"][key]
                for key in (
                    "unclassified",
                    "unguarded",
                    "stale",
                    "duplicates",
                    "configuration_errors",
                )
            },
            {
                "unclassified": 0,
                "unguarded": 0,
                "stale": 0,
                "duplicates": 0,
                "configuration_errors": 0,
            },
        )
        transaction_entries = [
            entry
            for entry in inventory
            if entry["classification"] == "transaction_persistence"
        ]
        self.assertTrue(transaction_entries)
        self.assertEqual(
            {
                (owner["module"], owner["function"])
                for entry in transaction_entries
                for owner in entry["guard_owners"]
            },
            {
                (
                    "scripts/project_lifecycle_transaction.py",
                    "apply_lifecycle_transaction",
                ),
                (
                    "scripts/project_lifecycle_transaction.py",
                    "recover_incomplete_transaction",
                ),
            },
        )
        self.assertTrue(
            all(
                entry["module"]
                in {
                    "scripts/project_lifecycle_transaction.py",
                    "scripts/project_lifecycle_transaction_storage.py",
                }
                for entry in transaction_entries
            )
        )
        self.assertTrue(
            {
                ("scripts/project_lifecycle.py", "sync_lifecycle"),
                ("scripts/project_loop.py", "write_loop_state"),
                ("scripts/project_production.py", "create_production_record"),
            }.isdisjoint(
                {(entry["module"], entry["function"]) for entry in inventory}
            )
        )


if __name__ == "__main__":
    unittest.main()
