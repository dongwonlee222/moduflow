import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import release_check, validate_moduflow
from tests.runtime_provenance_fixture import make_package, receipt_for


class RuntimeProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("scripts.runtime_provenance"),
                             "shared runtime evidence reader has not been implemented")
        self.runtime = importlib.import_module("scripts.runtime_provenance")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = make_package(Path(self.tmp.name))

    def test_legacy_does_not_invent_install_or_load_time(self):
        result = self.runtime.capture_runtime(self.root, runtime_kind="cli_process")
        self.assertEqual(result["package_version"], "0.0.1")
        for name in ("installed_at", "loaded_at", "source_commit", "source_dirty", "host", "session_id"):
            self.assertIsNone(result[name])
            self.assertTrue(result["unavailable_reasons"][name])
        self.assertEqual(result["unavailable_reasons"]["loaded_at"], "startup_not_observed")

    def test_valid_receipt_and_startup_snapshot(self):
        make_package(self.root, receipt=receipt_for())
        result = self.runtime.capture_runtime(self.root, runtime_kind="mcp_process",
                                              observed_at="2026-09-02T01:00:00Z")
        self.assertEqual(result["error_codes"], [])
        self.assertEqual(result["source_commit"], "a" * 40)
        self.assertEqual(result["installed_at"], "2026-09-02T00:00:00Z")
        make_package(self.root, version="0.0.2")
        self.assertEqual(result["package_version"], "0.0.1")
        self.assertEqual(result["loaded_at"], "2026-09-02T01:00:00Z")

    def test_invalid_receipt_never_launders_evidence(self):
        for key, value in (("schema", "other"), ("package_version", "9.0.0"),
                           ("source_commit", "not-a-commit"), ("source_dirty", "false"),
                           ("installed_at", "yesterday"), ("payload_sha256", "wrong"),
                           ("provenance_source", []), ("unavailable_reasons", [])):
            with self.subTest(key=key):
                receipt = receipt_for()
                receipt[key] = value
                make_package(self.root, receipt=receipt)
                result = self.runtime.inspect_package(self.root)
                self.assertIn("PROVENANCE_INVALID", result["error_codes"])
                self.assertEqual(result["receipt_state"], "invalid")
                self.assertIsNone(result["source_commit"])

    def test_missing_reason_and_naive_timestamp_are_invalid(self):
        for field, value in (("source_commit", None), ("installed_at", "2026-09-02T00:00:00")):
            receipt = receipt_for()
            receipt[field] = value
            make_package(self.root, receipt=receipt)
            self.assertIn("PROVENANCE_INVALID", self.runtime.inspect_package(self.root)["error_codes"])

    def test_corrupt_receipt_and_manifest_report_errors(self):
        for path in (self.root / ".moduflow-package.json", self.root / ".claude-plugin/plugin.json"):
            path.write_text("{invalid", encoding="utf-8")
            self.assertTrue(self.runtime.inspect_package(self.root)["error_codes"])

    def test_codex_build_suffix_is_not_a_manifest_mismatch(self):
        codex = self.root / ".codex-plugin/plugin.json"
        codex.parent.mkdir()
        codex.write_text(json.dumps({"name": "moduflow", "version": "0.0.1+codex.test"}))
        make_package(self.root, receipt=receipt_for("0.0.1+codex.test"))
        result = self.runtime.inspect_package(self.root)
        self.assertEqual(result["error_codes"], [])
        self.assertEqual(result["package_version"], "0.0.1+codex.test")

    def test_roles_reject_cache_even_with_copied_project_files(self):
        make_package(self.root, receipt=receipt_for())
        (self.root / ".git").write_text("gitdir: ignored")
        for role in ("source", "project"):
            result = self.runtime.inspect_validation_target(self.root, requested_role=role)
            self.assertFalse(result["valid"])
            self.assertIn("TARGET_ROLE_MISMATCH", result["error_codes"])

    def test_worktree_source_and_normal_project_roles(self):
        (self.root / ".git").write_text("gitdir: /synthetic/shared.git/worktrees/test")
        for role in ("source", "project"):
            self.assertTrue(self.runtime.inspect_validation_target(self.root, requested_role=role)["valid"])
        empty = self.root / "empty"
        empty.mkdir()
        self.assertTrue(self.runtime.inspect_validation_target(empty, requested_role="project")["valid"])
        self.assertFalse(self.runtime.inspect_validation_target(empty, requested_role="source")["valid"])

    def test_digest_changes_with_paths_and_bytes_not_interpreter_cache(self):
        before = self.runtime.package_payload_sha256(self.root)
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__/ignored.pyc").write_bytes(b"cache")
        self.assertEqual(before, self.runtime.package_payload_sha256(self.root))
        (self.root / "data").write_text("one")
        after = self.runtime.package_payload_sha256(self.root)
        self.assertNotEqual(before, after)
        (self.root / "data").rename(self.root / "renamed")
        self.assertNotEqual(after, self.runtime.package_payload_sha256(self.root))
        (self.root / "escape").symlink_to(self.root / "renamed")
        with self.assertRaises(ValueError):
            self.runtime.package_payload_sha256(self.root)

    def test_readers_do_not_invoke_external_processes(self):
        with mock.patch("subprocess.run", side_effect=AssertionError("process forbidden")):
            result = self.runtime.capture_runtime(self.root, runtime_kind="cli_process")
        self.assertEqual(result["package_version"], "0.0.1")


class ValidationModeTests(unittest.TestCase):
    def test_explicit_modes_keep_runtime_requirements_and_source_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_package(Path(tmp))
            installed = validate_moduflow.validate_moduflow(root, mode="installed")
            source = validate_moduflow.validate_moduflow(root, mode="source")
            self.assertEqual(installed["validation_role"], "installed")
            self.assertIn("scripts/project_doctor.py", installed["missing"])
            self.assertNotIn("tests/test_project_doctor.py", installed["missing"])
            self.assertIn("tests/test_project_doctor.py", source["missing"])
            self.assertFalse(source["valid"])

    def test_invalid_mode_is_not_silently_auto(self):
        with self.assertRaises(ValueError):
            validate_moduflow.validate_moduflow(".", mode="typo")

    def test_release_on_cache_stops_before_source_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_package(Path(tmp), receipt=receipt_for())
            with mock.patch.object(release_check, "run_command", side_effect=AssertionError("no source checks")):
                result = release_check.run_release_check(root)
            self.assertFalse(result["valid"])
            self.assertIn("TARGET_ROLE_MISMATCH", result["error_codes"])


if __name__ == "__main__":
    unittest.main()
