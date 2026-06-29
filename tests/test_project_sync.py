import unittest
from pathlib import Path

from scripts import project_sync


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, args, cwd):
        self.calls.append(tuple(args))
        key = tuple(args)
        if key not in self.responses:
            return project_sync.CommandResult(1, "", f"unexpected command: {' '.join(args)}")
        value = self.responses[key]
        if isinstance(value, project_sync.CommandResult):
            return value
        return project_sync.CommandResult(0, value, "")


class ProjectSyncTests(unittest.TestCase):
    def test_reports_gone_upstream_branch(self):
        runner = FakeRunner(
            {
                ("git", "rev-parse", "--is-inside-work-tree"): "true\n",
                ("git", "rev-parse", "--abbrev-ref", "HEAD"): "codex/034-memory-capture-sync\n",
                ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"): project_sync.CommandResult(
                    128,
                    "",
                    "fatal: no upstream configured for branch 'codex/034-memory-capture-sync'",
                ),
                ("git", "branch", "-vv"): "* codex/034-memory-capture-sync b775a25 [origin/codex/034-memory-capture-sync: gone] feat: show team state\n",
                ("git", "symbolic-ref", "refs/remotes/origin/HEAD"): "refs/remotes/origin/main\n",
                ("git", "rev-list", "--left-right", "--count", "HEAD...origin/main"): "0\t25\n",
                ("git", "status", "--porcelain"): "",
                ("git", "ls-tree", "-r", "--name-only", "origin/main", "issues"): "",
                ("git", "ls-files", "issues"): "",
            }
        )

        result = project_sync.inspect_repo_sync(Path("."), runner=runner)

        self.assertTrue(result["is_repo"])
        self.assertEqual(result["branch"], "codex/034-memory-capture-sync")
        self.assertTrue(result["upstream_gone"])
        self.assertEqual(result["default_remote"], "origin/main")
        self.assertEqual(result["default_remote_ahead"], 25)
        self.assertIn("upstream branch is gone", " ".join(result["recommendations"]))

    def test_reports_local_main_behind_origin_main(self):
        runner = FakeRunner(
            {
                ("git", "rev-parse", "--is-inside-work-tree"): "true\n",
                ("git", "rev-parse", "--abbrev-ref", "HEAD"): "main\n",
                ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"): "origin/main\n",
                ("git", "branch", "-vv"): "* main 5929502 [origin/main: behind 25] Add project memory and business document workflow\n",
                ("git", "rev-list", "--left-right", "--count", "HEAD...origin/main"): "0\t25\n",
                ("git", "symbolic-ref", "refs/remotes/origin/HEAD"): "refs/remotes/origin/main\n",
                ("git", "status", "--porcelain"): "",
                ("git", "ls-tree", "-r", "--name-only", "origin/main", "issues"): "",
                ("git", "ls-files", "issues"): "",
            }
        )

        result = project_sync.inspect_repo_sync(Path("."), runner=runner)

        self.assertFalse(result["upstream_gone"])
        self.assertEqual(result["upstream"], "origin/main")
        self.assertEqual(result["upstream_behind"], 25)
        self.assertEqual(result["default_remote_ahead"], 25)
        self.assertIn("fast-forward", " ".join(result["recommendations"]))

    def test_reports_remote_only_issue_files(self):
        runner = FakeRunner(
            {
                ("git", "rev-parse", "--is-inside-work-tree"): "true\n",
                ("git", "rev-parse", "--abbrev-ref", "HEAD"): "main\n",
                ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"): "origin/main\n",
                ("git", "branch", "-vv"): "* main af5b086 [origin/main] fix(049)\n",
                ("git", "rev-list", "--left-right", "--count", "HEAD...origin/main"): "0\t0\n",
                ("git", "symbolic-ref", "refs/remotes/origin/HEAD"): "refs/remotes/origin/main\n",
                ("git", "status", "--porcelain"): "",
                ("git", "ls-tree", "-r", "--name-only", "origin/main", "issues"): (
                    "issues/040-automatic-memory-candidate-capture.md\n"
                    "issues/049-bilingual-artifact-view.md\n"
                ),
                ("git", "ls-files", "issues"): "issues/049-bilingual-artifact-view.md\n",
            }
        )

        result = project_sync.inspect_repo_sync(Path("."), runner=runner)

        self.assertEqual(result["remote_only_issue_ids"], ["040-automatic-memory-candidate-capture"])
        self.assertIn("origin/main has issue files missing locally", " ".join(result["recommendations"]))

    def test_untracked_work_branch_without_upstream_is_not_reported_clean(self):
        runner = FakeRunner(
            {
                ("git", "rev-parse", "--is-inside-work-tree"): "true\n",
                ("git", "rev-parse", "--abbrev-ref", "HEAD"): "codex/050-repo-sync-preflight\n",
                ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"): project_sync.CommandResult(
                    128,
                    "",
                    "fatal: no upstream configured for branch 'codex/050-repo-sync-preflight'",
                ),
                ("git", "branch", "-vv"): "* codex/050-repo-sync-preflight af5b086 add repo sync preflight\n",
                ("git", "symbolic-ref", "refs/remotes/origin/HEAD"): "refs/remotes/origin/main\n",
                ("git", "rev-list", "--left-right", "--count", "HEAD...origin/main"): "1\t0\n",
                ("git", "status", "--porcelain"): "M commands/product-sync.md\n",
                ("git", "ls-tree", "-r", "--name-only", "origin/main", "issues"): "",
                ("git", "ls-files", "issues"): "",
            }
        )

        result = project_sync.inspect_repo_sync(Path("."), runner=runner)

        self.assertIsNone(result["upstream"])
        self.assertTrue(result["dirty"])
        joined = " ".join(result["recommendations"])
        self.assertIn("has no upstream", joined)
        self.assertIn("worktree has local changes", joined)
        self.assertNotIn("Repo sync preflight is clean", joined)


if __name__ == "__main__":
    unittest.main()
