import tempfile
import unittest
import json
from pathlib import Path

from scripts import project_git_handoff
from scripts.project_sync import CommandResult


class CheckCommitCapabilityTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _runner(self, mapping):
        def runner(args, cwd, timeout=None):
            key = tuple(args)
            if key not in mapping:
                raise AssertionError(f"unexpected command: {key}")
            return mapping[key]

        return runner

    def test_local_git_write_succeeds(self):
        (self.root / ".git").mkdir()
        result = project_git_handoff.check_commit_capability(self.root)
        self.assertEqual(result["mode"], "local-git-write")
        self.assertTrue(result["ok"])
        self.assertTrue(result["local_git_write"])
        self.assertEqual(result["reason"], "")
        self.assertFalse((self.root / ".git" / project_git_handoff.PROBE_FILENAME).exists())

    def test_missing_git_dir_falls_back_to_github_api_when_available(self):
        runner = self._runner({("gh", "auth", "status"): CommandResult(0, "Logged in", "")})
        result = project_git_handoff.check_commit_capability(self.root, runner=runner)
        self.assertEqual(result["mode"], "github-api-commit")
        self.assertTrue(result["ok"])
        self.assertFalse(result["local_git_write"])
        self.assertIn("not a git repository", result["reason"])

    def test_blocked_local_write_falls_back_to_github_api(self):
        (self.root / ".git").mkdir()
        runner = self._runner({("gh", "auth", "status"): CommandResult(0, "Logged in", "")})
        probe_write = lambda git_dir: (False, "local .git write failed: index.lock permission denied")
        result = project_git_handoff.check_commit_capability(self.root, runner=runner, probe_write=probe_write)
        self.assertEqual(result["mode"], "github-api-commit")
        self.assertTrue(result["ok"])
        self.assertIn("index.lock", result["reason"])
        self.assertTrue(result["recommendations"])

    def test_blocked_when_both_local_and_github_api_unavailable(self):
        (self.root / ".git").mkdir()
        runner = self._runner({("gh", "auth", "status"): CommandResult(1, "", "not logged in")})
        probe_write = lambda git_dir: (False, "local .git write failed: read-only filesystem")
        result = project_git_handoff.check_commit_capability(self.root, runner=runner, probe_write=probe_write)
        self.assertEqual(result["mode"], "blocked")
        self.assertFalse(result["ok"])
        self.assertFalse(result["github_api_available"])
        self.assertTrue(result["recommendations"])

    def test_never_touches_existing_index_lock(self):
        git_dir = self.root / ".git"
        git_dir.mkdir()
        lock_path = git_dir / "index.lock"
        lock_path.write_text("held by another process", encoding="utf-8")

        result = project_git_handoff.check_commit_capability(self.root)

        self.assertEqual(lock_path.read_text(encoding="utf-8"), "held by another process")
        self.assertEqual(result["mode"], "local-git-write")

    def test_identity_mismatch_blocks_before_git_probe_or_github_fallback(self):
        config_path = self.root / ".moduflow" / "config.json"
        config_path.parent.mkdir()
        config_path.write_text(
            json.dumps(
                {
                    "schema": "moduflow.config.v1",
                    "git": {
                        "identity": {
                            "mode": "remote",
                            "provider": "github",
                            "canonical_repository": "github.com/owner/repo",
                            "remote_name_hint": "origin",
                            "base_branch": "main",
                            "lifecycle": "active",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        identity = {
            "schema": "moduflow.repository-identity.v1",
            "status": "mismatch",
            "capabilities": {"read": True, "commit": False, "push": False},
            "reasons": [
                {"code": "push_remote_mismatch", "message": "wrong push repository"}
            ],
        }
        original = getattr(project_git_handoff, "inspect_repository_identity", None)
        project_git_handoff.inspect_repository_identity = lambda root, runner=None: identity
        probe_calls = []

        def probe(git_dir):
            probe_calls.append(git_dir)
            return True, ""

        def runner(args, cwd, timeout=None):
            raise AssertionError(f"runner must not be called after identity denial: {args}")

        try:
            result = project_git_handoff.check_commit_capability(
                self.root,
                runner=runner,
                probe_write=probe,
            )
        finally:
            if original is None:
                delattr(project_git_handoff, "inspect_repository_identity")
            else:
                project_git_handoff.inspect_repository_identity = original

        self.assertFalse(result["ok"])
        self.assertEqual(result["mode"], "identity-blocked")
        self.assertEqual(probe_calls, [])
        self.assertEqual(result["repository_identity"]["reasons"][0]["code"], "push_remote_mismatch")

    def test_local_only_commit_never_falls_back_to_github_api(self):
        config_path = self.root / ".moduflow" / "config.json"
        config_path.parent.mkdir()
        config_path.write_text("{}\n", encoding="utf-8")
        identity = {
            "schema": "moduflow.repository-identity.v1",
            "status": "local_only",
            "expected": {"mode": "local_only", "provider": "generic"},
            "capabilities": {
                "read": True,
                "execute": True,
                "commit": True,
                "push": False,
                "github_write": False,
                "release": False,
            },
            "reasons": [],
        }
        original = getattr(project_git_handoff, "inspect_repository_identity", None)
        project_git_handoff.inspect_repository_identity = lambda root, runner=None: identity
        runner_calls = []

        def runner(args, cwd, timeout=None):
            runner_calls.append(tuple(args))
            return CommandResult(0, "", "")

        try:
            result = project_git_handoff.check_commit_capability(
                self.root,
                runner=runner,
                probe_write=lambda git_dir: (False, "local .git write failed"),
            )
        finally:
            if original is None:
                delattr(project_git_handoff, "inspect_repository_identity")
            else:
                project_git_handoff.inspect_repository_identity = original

        self.assertFalse(result["ok"])
        self.assertEqual(result["mode"], "blocked")
        self.assertEqual(runner_calls, [])
        self.assertIn("GitHub API fallback", result["recommendations"][0])


if __name__ == "__main__":
    unittest.main()
