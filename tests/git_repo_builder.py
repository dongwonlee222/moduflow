#!/usr/bin/env python3
"""Temporary git repositories for commit-resolution tests (issue 095, task A1).

Plan 095 Global Constraint 10: fixtures build throwaway repositories in a temp
directory. No test may depend on this checkout's history, branches, or remotes.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}


class GitRepo:
    """A disposable git repository. Use as a context manager."""

    def __init__(self, default_branch="main"):
        """`default_branch` is a parameter, not a constant. Hardcoding `main`
        meant no fixture could reach a repository whose trunk is called
        anything else, and the second independent review found the resolver
        returns nothing there."""
        self.path = Path(tempfile.mkdtemp(prefix="moduflow-095-"))
        self.default_branch = default_branch
        self.call_count = 0
        self.call_log = []
        self._file_seq = 0
        self._git("init", "-q", "-b", default_branch)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.path, ignore_errors=True)
        return False

    # -- raw access ---------------------------------------------------------

    def _git(self, *args):
        import os

        env = dict(os.environ)
        env.update(GIT_ENV)
        result = subprocess.run(
            ["git", *args],
            cwd=str(self.path),
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"fixture git {' '.join(args)} failed: {result.stderr.strip()}"
            )
        return result.stdout

    def runner(self, args, cwd=None):
        """Injected runner matching the resolver contract. Counts calls so a
        test can assert subprocess use does not scale with history length."""
        import os

        self.call_count += 1
        self.call_log.append(list(args))
        env = dict(os.environ)
        env.update(GIT_ENV)
        return subprocess.run(
            args,
            cwd=str(cwd or self.path),
            capture_output=True,
            text=True,
            env=env,
        )

    # -- construction helpers ----------------------------------------------

    def commit(self, message, *, issue=None, filename=None):
        """Write a file and commit. `issue` appends an `Issue: <id>` trailer."""
        name = filename or f"f{self._next_index()}.txt"
        (self.path / name).write_text(message + "\n")
        self._git("add", name)
        body = message
        if issue:
            body = f"{message}\n\nIssue: {issue}"
        self._git("commit", "-q", "-m", body)
        return self.head()

    def branch(self, name):
        self._git("checkout", "-q", "-b", name)
        return name

    def checkout(self, ref):
        self._git("checkout", "-q", ref)

    def merge(self, branch_name, *, message=None):
        """Merge with a merge commit, mirroring `Merge branch '<name>'`."""
        subject = message or f"Merge branch '{branch_name}'"
        self._git("merge", "-q", "--no-ff", "-m", subject, branch_name)
        return self.head()

    def delete_branch(self, name):
        self._git("branch", "-q", "-D", name)

    def detach(self):
        """Leave HEAD detached at the current commit."""
        self._git("checkout", "-q", "--detach", "HEAD")

    def add_issue_file(self, issue_id):
        """Track issues/<id>.md so branch-name disambiguation has a source."""
        issues = self.path / "issues"
        issues.mkdir(exist_ok=True)
        (issues / f"{issue_id}.md").write_text(f"# Issue {issue_id}\n")
        self._git("add", f"issues/{issue_id}.md")
        self._git("commit", "-q", "-m", f"chore: register {issue_id}")
        return self.head()

    def publish(self, name, remote="origin"):
        """Create a remote-tracking ref for `name` without needing a server.

        Real repositories carry every branch twice — `codex/X` and
        `origin/codex/X`. Fixtures that only ever build local branches exercise
        one arrangement of git's ref globs, and issue 095's review found a
        live-branch defect that was invisible under exactly that gap."""
        self._git("update-ref", f"refs/remotes/{remote}/{name}", name)
        return f"{remote}/{name}"

    def head(self):
        return self._git("rev-parse", "HEAD").strip()

    def log_shas(self):
        return self._git("rev-list", "HEAD").split()

    def _next_index(self):
        """Monotonic, not a directory count. Counting files gives the same name
        on two branches, and the resulting content conflict makes a merge in a
        fixture fail for reasons unrelated to what the fixture is testing."""
        self._file_seq += 1
        return self._file_seq
