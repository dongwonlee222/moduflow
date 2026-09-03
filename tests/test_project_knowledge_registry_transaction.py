import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from scripts import project_artifact_registry as registry, project_operation
from scripts import project_knowledge
from tests.knowledge_registry_fixture import ARTIFACT_A, make_entry, transaction_project, shared_lifecycle_bytes


class RegistryTransactionTests(unittest.TestCase):
    def plan(self, project, entry=None, **kwargs):
        self.assertTrue(callable(getattr(registry, "plan_artifact_registration", None)), "Registration adapter required")
        return registry.plan_artifact_registration(project.root, entry or make_entry(), issue_id="001-synthetic-a",
                                                  project_context=project.context, **kwargs)

    def apply(self, project, plan):
        return registry.apply_artifact_registration(project.root, plan, project_context=project.context)

    def test_preview_and_apply_preserve_shared_lifecycle_and_retry_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            before = shared_lifecycle_bytes(project)
            catalog = project.root / "workspace/artifacts.md"
            old_catalog = catalog.read_bytes()
            plan = self.plan(project)
            self.assertEqual(old_catalog, catalog.read_bytes())
            self.assertEqual(before, shared_lifecycle_bytes(project))
            result = self.apply(project, plan)
            self.assertEqual(result["status"], "applied", result)
            self.assertTrue(result["registered"])
            self.assertEqual(before, shared_lifecycle_bytes(project))
            self.assertEqual(registry.parse_artifact_registry(catalog.read_text())["entries"][0]["id"], ARTIFACT_A)
            issue = project.root / "issues/001-synthetic-a.md"
            self.assertEqual(issue.read_text().count("#" + ARTIFACT_A), 1)
            self.assertIn("**Status: backlog**", issue.read_text())
            after = catalog.read_bytes(), issue.read_bytes()
            replay = self.apply(project, plan)
            self.assertEqual(replay["status"], "noop", replay)
            self.assertEqual(after, (catalog.read_bytes(), issue.read_bytes()))

    def test_preview_conflict_preserves_concurrent_catalog_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            plan = self.plan(project)
            catalog = project.root / "workspace/artifacts.md"
            catalog.write_text(catalog.read_text() + "\nHuman concurrent edit.\n")
            before = catalog.read_bytes()
            result = self.apply(project, plan)
            self.assertEqual(result["status"], "conflict", result)
            self.assertEqual(before, catalog.read_bytes())

    def test_issue_backlink_only_appends_without_normalizing_original_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            issue = project.root / "issues/001-synthetic-a.md"
            issue.write_bytes(issue.read_bytes() + b"\n\n\n")
            original = issue.read_bytes()
            result = self.apply(project, self.plan(project))
            self.assertEqual(result["status"], "applied", result)
            self.assertTrue(issue.read_bytes().startswith(original))

    def test_source_change_after_preview_blocks_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            plan = self.plan(project)
            project.write("knowledge/references/population.md", "CHANGED SOURCE")
            result = self.apply(project, plan)
            self.assertEqual(result["status"], "conflict", result)
            self.assertEqual(registry.parse_artifact_registry((project.root / "workspace/artifacts.md").read_text())["entries"], [])

    def test_nested_registration_changes_only_selected_catalog_and_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp, nested=True)
            entry = make_entry(local_path="product/knowledge/references/population.md")
            before = shared_lifecycle_bytes(project)
            result = self.apply(project, self.plan(project, entry))
            self.assertEqual(result["status"], "applied", result)
            self.assertFalse((project.root / "workspace/artifacts.md").exists())
            self.assertEqual(before, shared_lifecycle_bytes(project))

    def test_archived_apply_denies_before_lock_or_catalog_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            plan = self.plan(project)
            project.context.update(project_operation.compute_project_policy("archived", "internal"))
            with self.assertRaises(Exception):
                self.apply(project, plan)
            self.assertFalse((project.root / ".moduflow/transactions").exists())

    def test_new_knowledge_is_generated_with_catalog_and_rolled_back_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            entry = make_entry(local_path="knowledge/reports/2026-09-02-synthetic-report.md", kind="report")
            plan = self.plan(project, entry, new_knowledge={"kind": "report", "title": "Synthetic report",
                "spec_path": "", "decision_supported": "Synthetic decision"})
            transaction = registry._transaction_module()
            original = transaction.transaction_storage.os.replace
            failed = False
            def fail_once(src, dst, **kwargs):
                nonlocal failed
                if dst == "001-synthetic-a.md" and not failed:
                    failed = True
                    raise OSError("Injected replace failure")
                return original(src, dst, **kwargs)
            with mock.patch.object(transaction.transaction_storage.os, "replace", side_effect=fail_once):
                result = self.apply(project, plan)
            self.assertEqual(result["status"], "rolled_back", result)
            self.assertFalse((project.root / entry["local_path"]).exists())
            self.assertEqual(registry.parse_artifact_registry((project.root / "workspace/artifacts.md").read_text())["entries"], [])
            result = self.apply(project, plan)
            self.assertEqual(result["status"], "applied", result)
            self.assertIn("date: 2026-09-02", (project.root / entry["local_path"]).read_text())

    def test_missing_issue_or_uninitialized_project_blocks_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            (project.root / "issues/001-synthetic-a.md").unlink()
            with self.assertRaises(ValueError):
                self.plan(project)
            self.assertFalse((project.root / ".moduflow/transactions").exists())

    def test_missing_transaction_directory_blocks_preview_before_any_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            (project.root / "workspace/transactions").rmdir()
            with self.assertRaisesRegex(ValueError, "PREREQUISITE"):
                self.plan(project)
            self.assertFalse((project.root / ".moduflow/transactions").exists())

    def test_source_change_during_apply_rolls_back_metadata_not_external_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            plan = self.plan(project)
            transaction = registry._transaction_module()
            original = transaction.transaction_storage.apply_staged_target
            def change_source(*args, **kwargs):
                result = original(*args, **kwargs)
                project.write("knowledge/references/population.md", "External concurrent edit")
                return result
            with mock.patch.object(transaction.transaction_storage, "apply_staged_target", side_effect=change_source):
                result = self.apply(project, plan)
            self.assertEqual(result["status"], "rolled_back", result)
            self.assertEqual((project.root / "knowledge/references/population.md").read_text(), "External concurrent edit")
            self.assertNotIn(ARTIFACT_A, (project.root / "workspace/artifacts.md").read_text())

    def test_same_id_amendment_is_explicit_and_preserves_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            self.assertEqual(self.apply(project, self.plan(project))["status"], "applied")
            updated = make_entry(summary="Revised scoped definition")
            with self.assertRaises(ValueError):
                self.plan(project, updated)
            catalog = project.root / "workspace/artifacts.md"
            catalog.write_text(catalog.read_text() + "\nHuman notes remain.\n")
            result = self.apply(project, self.plan(project, updated, amend=True))
            self.assertEqual(result["status"], "applied", result)
            self.assertIn("Human notes remain.", catalog.read_text())
            self.assertEqual(catalog.read_text().count("## " + ARTIFACT_A), 1)

    def test_forged_plan_target_bytes_are_not_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            plan = self.plan(project)
            target = plan.targets[0]
            forged = replace(plan, targets=(replace(target, _after_bytes=b"FORGED"), *plan.targets[1:]))
            before = shared_lifecycle_bytes(project)
            result = self.apply(project, forged)
            self.assertEqual(result["status"], "applied", result)
            self.assertEqual(before, shared_lifecycle_bytes(project))

    def test_replaced_same_byte_source_identity_blocks_preview_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            plan = self.plan(project)
            source = project.root / "knowledge/references/population.md"
            replacement = project.write("knowledge/references/replacement.md", source.read_text())
            os.replace(replacement, source)
            result = self.apply(project, plan)
            self.assertEqual(result["status"], "conflict", result)
            self.assertNotIn(ARTIFACT_A, (project.root / "workspace/artifacts.md").read_text())

    def test_replacement_faults_before_and_after_each_target_rollback_and_retry(self):
        for name in ("artifacts.md", "001-synthetic-a.md", "2026-09-02-synthetic-report.md", "evidence"):
            for after in (False, True):
                with self.subTest(target=name, after=after), tempfile.TemporaryDirectory() as tmp:
                    project = transaction_project(tmp)
                    before = shared_lifecycle_bytes(project)
                    entry = make_entry(local_path="knowledge/reports/2026-09-02-synthetic-report.md", kind="report")
                    plan = self.plan(project, entry, new_knowledge={"kind": "report", "title": "Synthetic report",
                        "spec_path": "", "decision_supported": "Synthetic decision"})
                    transaction = registry._transaction_module()
                    original = transaction.transaction_storage.os.replace
                    failed = False
                    def fail_once(src, dst, **kwargs):
                        nonlocal failed
                        selected = dst == name or (name == "evidence" and dst == plan.transaction_id + ".json")
                        if selected and not failed:
                            failed = True
                            if after:
                                original(src, dst, **kwargs)
                            raise OSError("Injected canonical replacement failure")
                        return original(src, dst, **kwargs)
                    with mock.patch.object(transaction.transaction_storage.os, "replace", side_effect=fail_once):
                        result = self.apply(project, plan)
                    self.assertEqual(result["status"], "rolled_back", result)
                    self.assertEqual(before, shared_lifecycle_bytes(project))
                    self.assertFalse((project.root / entry["local_path"]).exists())
                    self.assertNotIn(ARTIFACT_A, (project.root / "workspace/artifacts.md").read_text())
                    self.assertEqual(self.apply(project, plan)["status"], "applied")

    def test_interrupted_apply_is_recovered_by_existing_engine_then_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            plan = self.plan(project)
            transaction = registry._transaction_module()
            original = transaction.transaction_storage.os.replace
            def crash(src, dst, **kwargs):
                result = original(src, dst, **kwargs)
                if dst == "artifacts.md":
                    raise SystemExit("Simulated process interruption")
                return result
            with mock.patch.object(transaction.transaction_storage.os, "replace", side_effect=crash):
                with self.assertRaises(SystemExit):
                    self.apply(project, plan)
            recovered = transaction.recover_incomplete_transaction(project.root, "", project_context=project.context)
            self.assertEqual(recovered["status"], "rolled_back", recovered)
            self.assertNotIn(ARTIFACT_A, (project.root / "workspace/artifacts.md").read_text())
            self.assertEqual(self.apply(project, plan)["status"], "applied")


class KnowledgeRegistrationEntrypointTests(unittest.TestCase):
    def cli(self, project, *arguments):
        return subprocess.run([sys.executable, str(Path(project_knowledge.__file__)), str(project.root), *arguments],
                              capture_output=True, text=True)

    def test_opt_in_creation_registers_once_and_preserves_legacy_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            entry = make_entry(kind="report", local_path="knowledge/reports/2026-09-02-synthetic-report.md")
            self.assertIn("registry_entry", __import__("inspect").signature(project_knowledge.create_knowledge_artifact).parameters)
            result = project_knowledge.create_knowledge_artifact(project.root, "report", "Synthetic report",
                issue_id="001-synthetic-a", project_context=project.context, registry_entry=entry)
            self.assertEqual(result["status"], "applied", result)
            self.assertTrue(result["registered"])
            self.assertEqual(result["path"], entry["local_path"])
            self.assertTrue((project.root / result["path"]).is_file())
            replay = project_knowledge.create_knowledge_artifact(project.root, "report", "Synthetic report",
                issue_id="001-synthetic-a", project_context=project.context, registry_entry=entry)
            self.assertEqual(replay["status"], "noop", replay)

    def test_cli_inspect_and_explicit_source_read_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            plan = registry.plan_artifact_registration(project.root, make_entry(), issue_id="001-synthetic-a", project_context=project.context)
            registry.apply_artifact_registration(project.root, plan, project_context=project.context)
            read = self.cli(project, "--inspect", "--query", "population")
            self.assertEqual(read.returncode, 0, read.stderr)
            metadata = json.loads(read.stdout)
            self.assertEqual(metadata["identity_status"], "unbound")
            self.assertEqual(metadata["returned"], 1)
            self.assertNotIn("Synthetic content", read.stdout)
            source = self.cli(project, "--read-sources", "--artifact-id", ARTIFACT_A)
            self.assertEqual(source.returncode, 0, source.stderr)
            self.assertIn("Synthetic content", json.loads(source.stdout)["sources"][0]["content"])
            denied = self.cli(project, "--read-sources")
            self.assertNotEqual(denied.returncode, 0)

    def test_cli_register_defaults_to_preview_and_write_applies(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            metadata = project.write("entry.json", json.dumps(make_entry()))
            preview = self.cli(project, "--register", str(metadata), "--issue-id", "001-synthetic-a")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(json.loads(preview.stdout)["artifact_id"], ARTIFACT_A)
            self.assertNotIn(ARTIFACT_A, (project.root / "workspace/artifacts.md").read_text())
            applied = self.cli(project, "--register", str(metadata), "--issue-id", "001-synthetic-a", "--write")
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertTrue(json.loads(applied.stdout)["registered"])

    def test_cli_malformed_registration_returns_safe_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            metadata = project.write("entry.json", '["PRIVATE_INVALID_VALUE"]')
            result = self.cli(project, "--register", str(metadata), "--issue-id", "001-synthetic-a")
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(json.loads(result.stdout)["error_code"], "KNOWLEDGE_REQUEST_INVALID")
            self.assertNotIn("PRIVATE_INVALID_VALUE", result.stdout + result.stderr)

    def test_existing_memory_registration_never_rewrites_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            source = project.write("memory/decisions/synthetic-decision.md",
                "---\nid: original-memory-id\nreferences: [original-other-id]\n---\nSynthetic body\n")
            before = source.read_bytes()
            entry = make_entry(kind="memory", local_path="memory/decisions/synthetic-decision.md")
            plan = registry.plan_artifact_registration(project.root, entry, issue_id="001-synthetic-a", project_context=project.context)
            result = registry.apply_artifact_registration(project.root, plan, project_context=project.context)
            self.assertEqual(result["status"], "applied", result)
            self.assertEqual(before, source.read_bytes())


if __name__ == "__main__":
    unittest.main()
