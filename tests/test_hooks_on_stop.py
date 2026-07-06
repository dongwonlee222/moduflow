"""Tests for hooks/on_stop.py (issue 072, task A2).

Function-level tests exercise the logic directly; a few subprocess smoke
tests pin the hook contract (exit 0 everywhere, stdout = JSON or nothing).
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "hooks" / "on_stop.py"

sys.path.insert(0, str(REPO_ROOT))
from hooks import on_stop  # noqa: E402


def _git(cwd, *args):
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _init_repo(root, branch="main"):
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test User")
    _git(root, "checkout", "-q", "-b", branch)
    _git(root, "commit", "-q", "--allow-empty", "-m", "init")


def _make_project(root, branch="main", issue_status="active"):
    """Minimal ModuFlow project fixture inside a real git repo."""
    root = Path(root)
    _init_repo(root, branch=branch)
    (root / ".moduflow").mkdir()
    (root / ".moduflow" / "state.json").write_text(
        json.dumps({"schema": "moduflow.state.v1", "active_issue": "", "phase": "select"})
        + "\n",
        encoding="utf-8",
    )
    (root / "issues").mkdir()
    (root / "issues" / "001-sample-issue.md").write_text(
        f"# Issue: sample issue\n\n**Status: {issue_status}**\n\n## Problem\n\nx\n",
        encoding="utf-8",
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "fixture project")
    return root


def _run_hook(cwd):
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="on-stop-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def deadline(self):
        return time.monotonic() + 5.0


class IssuesHashTests(TempDirTestCase):
    def test_hash_stable_and_changes_on_mutation(self):
        root = _make_project(self.tmp)
        first = on_stop.compute_issues_hash(root)
        self.assertEqual(first, on_stop.compute_issues_hash(root))

        issue = root / "issues" / "001-sample-issue.md"
        issue.write_text(
            issue.read_text(encoding="utf-8") + "\nmore\n", encoding="utf-8"
        )
        self.assertNotEqual(first, on_stop.compute_issues_hash(root))

    def test_missing_issues_dir_still_hashes(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertEqual(
            on_stop.compute_issues_hash(empty), on_stop.compute_issues_hash(empty)
        )


class MaybeSyncTests(TempDirTestCase):
    def test_sync_runs_then_skips_on_unchanged_marker(self):
        root = _make_project(self.tmp, issue_status="active")

        first = on_stop.maybe_sync(root, self.deadline())
        self.assertTrue(first["synced"])
        marker = root / ".moduflow" / "state" / ".last-sync"
        self.assertTrue(marker.is_file())
        state = json.loads((root / ".moduflow" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["active_issue"], "001-sample-issue")

        second = on_stop.maybe_sync(root, self.deadline())
        self.assertFalse(second["synced"])
        self.assertEqual(second["reason"], "unchanged")

    def test_issue_mutation_retriggers_sync(self):
        root = _make_project(self.tmp, issue_status="active")
        on_stop.maybe_sync(root, self.deadline())

        issue = root / "issues" / "001-sample-issue.md"
        issue.write_text(
            issue.read_text(encoding="utf-8").replace("Status: active", "Status: done"),
            encoding="utf-8",
        )
        result = on_stop.maybe_sync(root, self.deadline())
        self.assertTrue(result["synced"])
        state = json.loads((root / ".moduflow" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["active_issue"], "")

    def test_budget_exhausted_skips_and_logs(self):
        root = _make_project(self.tmp)
        result = on_stop.maybe_sync(root, time.monotonic())  # deadline already passed
        self.assertFalse(result["synced"])
        self.assertEqual(result["reason"], "budget")
        log = (root / ".moduflow" / "logs" / "hooks.log").read_text(encoding="utf-8")
        self.assertIn("on_stop warn", log)
        # No marker written -> next Stop retries the sync.
        self.assertFalse((root / ".moduflow" / "state" / ".last-sync").exists())


class DetectUnlinkedTests(TempDirTestCase):
    def test_unlinked_behavior_paths_on_plain_branch(self):
        root = _make_project(self.tmp, branch="main")
        (root / "scripts").mkdir()
        (root / "scripts" / "new_tool.py").write_text("print('x')\n", encoding="utf-8")

        result = on_stop.detect_unlinked(root)
        self.assertEqual(result["unlinked"], ["scripts/new_tool.py"])
        self.assertEqual(result["errors"], [])

    def test_codex_branch_is_linked(self):
        root = _make_project(self.tmp, branch="codex/001-sample-issue")
        (root / "scripts").mkdir()
        (root / "scripts" / "new_tool.py").write_text("print('x')\n", encoding="utf-8")

        result = on_stop.detect_unlinked(root)
        self.assertEqual(result["unlinked"], [])
        self.assertEqual(result["reason"], "codex-branch")

    def test_neutral_changes_only(self):
        root = _make_project(self.tmp)
        (root / "notes.md").write_text("neutral\n", encoding="utf-8")

        result = on_stop.detect_unlinked(root)
        self.assertEqual(result["unlinked"], [])
        self.assertEqual(result["reason"], "no-behavior-changes")

    def test_no_issue_declaration_out_of_scope(self):
        root = _make_project(self.tmp, branch="main")
        (root / "scripts").mkdir()
        (root / "scripts" / "new_tool.py").write_text("print('x')\n", encoding="utf-8")
        (root / "releases").mkdir()
        (root / "releases" / "no-issue-declarations.md").write_text(
            "# Declarations\n\n- scripts/new_tool.py: tooling\n", encoding="utf-8"
        )

        result = on_stop.detect_unlinked(root)
        self.assertEqual(result["unlinked"], [])
        self.assertEqual(result["reason"], "no-issue-declaration")

    def test_git_failure_reports_error_not_warning(self):
        root = self.tmp / "not-a-repo"
        root.mkdir()
        result = on_stop.detect_unlinked(root)
        self.assertEqual(result["unlinked"], [])
        self.assertEqual(result["reason"], "git-error")
        self.assertTrue(result["errors"])


class WarningFormatTests(unittest.TestCase):
    def test_three_paths_no_more_suffix(self):
        warning = on_stop.build_warning(["a/x.py", "b/y.py", "c/z.py"])
        self.assertIn("a/x.py, b/y.py, c/z.py", warning)
        self.assertNotIn("more", warning)
        self.assertTrue(warning.startswith("⚠️ 이슈 연결 없는 동작 변경 감지: "))
        self.assertIn("릴리즈 게이트가 차단함", warning)

    def test_overflow_paths_collapse_to_more(self):
        warning = on_stop.build_warning([f"scripts/f{i}.py" for i in range(5)])
        self.assertIn("+2 more", warning)
        self.assertEqual(warning.count(", "), 2)  # only 3 paths listed

    def test_fingerprint_order_independent(self):
        self.assertEqual(
            on_stop.warning_fingerprint(["b", "a"]),
            on_stop.warning_fingerprint(["a", "b", "a"]),
        )
        self.assertNotEqual(
            on_stop.warning_fingerprint(["a"]), on_stop.warning_fingerprint(["a", "b"])
        )


class LinkageWarningDedupeTests(TempDirTestCase):
    def test_warn_once_then_suppress_then_rewarn_on_change(self):
        root = _make_project(self.tmp, branch="main")
        (root / "scripts").mkdir()
        (root / "scripts" / "new_tool.py").write_text("print('x')\n", encoding="utf-8")

        first = on_stop.linkage_warning(root)
        self.assertIsNotNone(first)
        fingerprint_path = root / ".moduflow" / "state" / ".linkage-warned"
        self.assertTrue(fingerprint_path.is_file())

        # Same unlinked set -> suppressed.
        self.assertIsNone(on_stop.linkage_warning(root))

        # Path set changed -> warns anew, fingerprint updated.
        old_fingerprint = fingerprint_path.read_text(encoding="utf-8")
        (root / "commands").mkdir()
        (root / "commands" / "new-cmd.md").write_text("cmd\n", encoding="utf-8")
        second = on_stop.linkage_warning(root)
        self.assertIsNotNone(second)
        self.assertIn("commands/new-cmd.md", second)
        self.assertNotEqual(old_fingerprint, fingerprint_path.read_text(encoding="utf-8"))

    def test_resolved_state_removes_fingerprint(self):
        root = _make_project(self.tmp, branch="main")
        (root / "scripts").mkdir()
        offender = root / "scripts" / "new_tool.py"
        offender.write_text("print('x')\n", encoding="utf-8")
        self.assertIsNotNone(on_stop.linkage_warning(root))
        fingerprint_path = root / ".moduflow" / "state" / ".linkage-warned"
        self.assertTrue(fingerprint_path.is_file())

        offender.unlink()
        (root / "scripts").rmdir()
        self.assertIsNone(on_stop.linkage_warning(root))
        self.assertFalse(fingerprint_path.exists())

        # Same offense later warns again (fingerprint was cleared).
        (root / "scripts").mkdir()
        offender.write_text("print('x')\n", encoding="utf-8")
        self.assertIsNotNone(on_stop.linkage_warning(root))


class PorcelainParsingTests(unittest.TestCase):
    def test_rename_and_quoted_paths(self):
        out = (
            " M scripts/a.py\n"
            "R  scripts/old.py -> scripts/new.py\n"
            '?? "scripts/with space.py"\n'
        )
        self.assertEqual(
            on_stop._paths_from_porcelain(out),
            ["scripts/a.py", "scripts/new.py", "scripts/with space.py"],
        )


class HookSubprocessContractTests(TempDirTestCase):
    """End-to-end: run hooks/on_stop.py as the hook runtime would."""

    def test_non_moduflow_dir_silent_exit_zero(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        result = _run_hook(plain)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse((plain / ".moduflow").exists())  # no log spam

    def test_unlinked_warning_json_then_suppressed_second_run(self):
        root = _make_project(self.tmp, branch="main")
        (root / "scripts").mkdir()
        (root / "scripts" / "new_tool.py").write_text("print('x')\n", encoding="utf-8")

        first = _run_hook(root)
        self.assertEqual(first.returncode, 0)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "Stop")
        self.assertTrue(payload["suppressOutput"])
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("이슈 연결 없는 동작 변경 감지", context)
        self.assertIn("scripts/new_tool.py", context)
        # Sync also ran: marker written, state.json propagated.
        self.assertTrue((root / ".moduflow" / "state" / ".last-sync").is_file())
        state = json.loads((root / ".moduflow" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["active_issue"], "001-sample-issue")

        second = _run_hook(root)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(second.stdout, "")  # same state -> total silence

    def test_codex_branch_silent(self):
        root = _make_project(self.tmp, branch="codex/001-sample-issue")
        (root / "scripts").mkdir()
        (root / "scripts" / "new_tool.py").write_text("print('x')\n", encoding="utf-8")

        result = _run_hook(root)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_git_failure_logs_and_exits_zero(self):
        root = self.tmp / "broken"
        root.mkdir()
        (root / ".moduflow").mkdir()
        (root / ".moduflow" / "state.json").write_text("{}\n", encoding="utf-8")
        # A corrupt .git directory makes every git command fail.
        (root / ".git").mkdir()
        (root / ".git" / "HEAD").write_text("garbage\n", encoding="utf-8")

        result = _run_hook(root)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        log = (root / ".moduflow" / "logs" / "hooks.log").read_text(encoding="utf-8")
        self.assertIn("on_stop error", log)


if __name__ == "__main__":
    unittest.main()
