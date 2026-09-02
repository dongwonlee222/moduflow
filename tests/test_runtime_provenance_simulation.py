"""Offline scenarios S01–S12; real host observations are deliberately separate."""
import hashlib
import json
import os
import select
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import mcp_server, project_doctor, runtime_provenance as runtime, validate_moduflow
from scripts import register_codex_personal_marketplace as installer
from tests.runtime_provenance_fixture import make_distribution, make_package, receipt_for

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {p.relative_to(root).as_posix(): (
        "directory" if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest())
        for p in root.rglob("*") if "__pycache__" not in p.parts}


def make_project(root, name="project"):
    root.mkdir(parents=True, exist_ok=True)
    (root / ".moduflow").mkdir()
    (root / ".moduflow/config.json").write_text(json.dumps({"schema": "moduflow.config.v1", "paths": {}}))
    (root / ".moduflow/state.json").write_text(json.dumps({"schema": "moduflow.state.v1", "phase": "ready",
        "active_goal": name, "next_command": "product:status"}))
    for directory in ("issues", "specs", "workspace"):
        (root / directory).mkdir()
    for filename in ("inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"):
        (root / "workspace" / filename).write_text("# Workspace\n")
    return root


class RuntimeSimulationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = make_distribution(self.root / "source")
        self.home = self.root / "home"

    def cache(self):
        return installer.copy_plugin_cache(self.source, self.home, "0.2.0+codex.test")

    def test_S01_source_requires_source_tests(self):
        (self.source / ".git").write_text("gitdir: synthetic worktree")
        for name in validate_moduflow.SOURCE_ONLY_REQUIRED_FILES:
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        self.assertTrue(validate_moduflow.validate_moduflow(self.source, mode="source")["valid"])
        (self.source / "tests/test_project_doctor.py").unlink()
        result = validate_moduflow.validate_moduflow(self.source, mode="source")
        self.assertFalse(result["valid"])
        self.assertIn("tests/test_project_doctor.py", result["missing"])

    def test_S02_installed_distribution_without_source_tree(self):
        cache = self.cache()
        result = validate_moduflow.validate_moduflow(cache, mode="installed")
        self.assertTrue(result["valid"], result["errors"])
        self.assertFalse((cache / ".git").exists())
        self.assertFalse((cache / "tests/test_runtime_provenance.py").exists())
        self.assertEqual(runtime.inspect_package(cache)["receipt_state"], "valid")

    def test_S03_missing_runtime_asset_fails(self):
        cache = self.cache()
        (cache / "scripts/project_doctor.py").unlink()
        result = validate_moduflow.validate_moduflow(cache, mode="installed")
        self.assertFalse(result["valid"])
        self.assertIn("scripts/project_doctor.py", result["missing"])
        self.assertIn("PACKAGE_PAYLOAD_MISMATCH", result["error_codes"])

    def test_S04_cache_target_never_runs_project_discovery(self):
        cache = self.cache()
        with mock.patch.object(project_doctor, "git_root", side_effect=AssertionError("parent discovery")):
            result = project_doctor.inspect_project(cache)
        self.assertEqual(result["error_codes"], ["TARGET_ROLE_MISMATCH"])
        self.assertEqual(result["moduflow"]["missing"], [])

    def test_S05_two_projects_and_empty_project(self):
        package = runtime.capture_runtime(self.cache(), runtime_kind="mcp_process")
        for name in ("project-a", "project-b"):
            project = make_project(self.root / name, name)
            response = mcp_server.handle_request({"id": 1, "method": "tools/call",
                "params": {"name": "moduflow_status"}}, project, runtime_snapshot=package)
            payload = json.loads(response["result"]["content"][0]["text"])
            self.assertEqual(payload["active_goal"], name)
            self.assertEqual(payload["runtime_provenance"], package)
        empty = self.root / "empty"
        empty.mkdir()
        self.assertTrue(project_doctor.inspect_project(empty, include_preflight=False)["moduflow"]["missing"])

    def test_S06_legacy_unknowns_remain_explicit(self):
        result = runtime.capture_runtime(self.source, runtime_kind="cli_process")
        for key in ("installed_at", "source_commit", "loaded_at", "host", "session_id"):
            self.assertIsNone(result[key])
            self.assertTrue(result["unavailable_reasons"][key])
        self.assertTrue(validate_moduflow.validate_moduflow(self.source, mode="installed")["valid"])

    def test_S07_invalid_receipt_fails_without_invalidating_other_project(self):
        cache = self.cache()
        (cache / runtime.RECEIPT_NAME).write_text("{broken")
        self.assertIn("PROVENANCE_INVALID", validate_moduflow.validate_moduflow(cache, mode="installed")["error_codes"])
        project = make_project(self.root / "project")
        result = project_doctor.inspect_project(project, include_preflight=False,
            runtime_snapshot=runtime.capture_runtime(cache, runtime_kind="cli_process"))
        self.assertTrue(result["schema_gates"]["valid"], result["schema_gates"]["errors"])
        self.assertIn("PROVENANCE_INVALID", result["runtime_provenance"]["error_codes"])

    def test_S08_copy_receipt_and_publication_failures_preserve_cache(self):
        cache = self.cache()
        before = snapshot(cache)
        for owner, method in ((installer.shutil, "copytree"), (installer.os, "fsync"),
                               (installer.os, "replace"), (Path, "rename")):
            with self.subTest(method=method), mock.patch.object(owner, method, side_effect=OSError("injected")):
                with self.assertRaises(OSError):
                    installer.copy_plugin_cache(self.source, self.home, "0.2.0+codex.new")
            self.assertEqual(snapshot(cache), before)
            self.assertEqual([p.name for p in cache.parent.iterdir()], [cache.name])

    def test_S09_identical_retry_conflict_and_symlink_destination(self):
        cache = self.cache()
        before = snapshot(cache)
        self.cache()
        self.assertEqual(snapshot(cache), before)
        (self.source / "README.md").write_text("changed")
        with self.assertRaisesRegex(RuntimeError, "PACKAGE_DESTINATION_CONFLICT"):
            self.cache()
        self.assertEqual(snapshot(cache), before)
        (cache.parent / "0.2.0+codex.link").symlink_to(cache, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "PACKAGE_DESTINATION_CONFLICT"):
            installer.copy_plugin_cache(self.source, self.home, "0.2.0+codex.link")

    def test_S10_persistent_packaged_process_and_new_process(self):
        cache = self.cache()
        project = make_project(self.root / "project")
        env = {**os.environ, "PYTHONPATH": "", "PYTHONDONTWRITEBYTECODE": "1", "MODUFLOW_ROOT": str(project)}
        with subprocess.Popen([sys.executable, str(cache / "scripts/mcp_server.py")], cwd=project,
                env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
            try:
                def rpc(method, name=None):
                    request = {"id": 1, "method": method, "params": {"name": name} if name else {}}
                    process.stdin.write(json.dumps(request) + "\n")
                    process.stdin.flush()
                    self.assertTrue(select.select([process.stdout], [], [], 10)[0], "MCP response timed out")
                    line = process.stdout.readline()
                    self.assertTrue(line, "packaged MCP exited before response")
                    return json.loads(line)["result"]
                self.assertEqual(rpc("initialize")["serverInfo"]["version"], "0.2.0+codex.test")
                initial = json.loads(rpc("tools/call", "moduflow_status")["content"][0]["text"])["runtime_provenance"]
                self.assertEqual(Path(initial["package_path"]), cache.resolve())
                self.assertIsNotNone(initial["loaded_at"])
                # Deliberately simulate a changed installation inside this temporary fixture only.
                make_package(cache, version="0.2.1")
                (cache / runtime.RECEIPT_NAME).unlink()
                for name in ("moduflow_status", "moduflow_doctor"):
                    payload = json.loads(rpc("tools/call", name)["content"][0]["text"])
                    self.assertEqual(payload["runtime_provenance"], initial)
                fresh = subprocess.run([sys.executable, str(cache / "scripts/runtime_provenance.py")],
                    cwd=project, env=env, text=True, capture_output=True, timeout=10)
                self.assertEqual(fresh.returncode, 0, fresh.stderr)
                observed = json.loads(fresh.stdout)
                self.assertEqual(observed["package_version"], "0.2.1")
                self.assertIsNone(observed["host"])
                self.assertIsNone(observed["session_id"])
            finally:
                process.stdin.close()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)

    def test_S11_inventory_never_replaces_live_snapshot(self):
        cache = self.cache()
        old = make_package(self.root / "old", version="0.1.0")
        live = runtime.capture_runtime(old, runtime_kind="mcp_process")
        inventory = project_doctor.installed_plugin_staleness(self.source, home=self.home)
        self.assertEqual(inventory["stale"], [])
        self.assertEqual(inventory["inventory"][0]["package"]["package_path"], str(cache.resolve()))
        self.assertEqual(live["package_version"], "0.1.0")
        registration = self.home / ".claude/plugins/installed_plugins.json"
        registration.parent.mkdir(parents=True)
        registration.write_text("[broken")
        self.assertTrue(project_doctor.installed_plugin_staleness(self.source, home=self.home)["diagnostics"])

    def test_S12_worktree_and_no_write_no_network_reads(self):
        (self.source / ".git").write_text("gitdir: /synthetic/shared.git/worktrees/secondary")
        self.assertTrue(runtime.inspect_validation_target(self.source, requested_role="source")["valid"])
        self.assertTrue(runtime.inspect_validation_target(ROOT, requested_role="source")["valid"])
        (self.source / ".git").unlink()
        package = self.cache()
        project = make_project(self.root / "project")
        before = snapshot(project), snapshot(package)
        with mock.patch("subprocess.run", side_effect=AssertionError("no subprocess")), \
             mock.patch("socket.create_connection", side_effect=AssertionError("no network")):
            result = project_doctor.inspect_project(project, include_preflight=False,
                runtime_snapshot=runtime.capture_runtime(package, runtime_kind="mcp_process"))
        self.assertTrue(result["schema_gates"]["valid"])
        self.assertEqual((snapshot(project), snapshot(package)), before)


if __name__ == "__main__":
    unittest.main()
