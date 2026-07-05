import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
