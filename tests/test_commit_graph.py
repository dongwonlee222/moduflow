#!/usr/bin/env python3
"""Commit graph snapshot contracts for issue 095 task A1."""
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import commit_graph  # noqa: E402
import commit_resolution as cr  # noqa: E402
from git_repo_builder import GitRepo  # noqa: E402


def disconnected_runner(returncode):
    """Return a runner whose graph query has no stdout or stderr."""
    def runner(args, cwd=None):
        return subprocess.CompletedProcess(args, returncode, "", "")

    return runner


def empty_snapshot():
    """Return the smallest valid graph snapshot for isolated query tests."""
    return {
        "records": {},
        "order": [],
        "refs": {},
        "merge_base_cache": {},
        "ancestor_cache": {},
        "fatal_errors": [],
    }


class SnapshotTests(unittest.TestCase):
    def test_loads_log_and_refs_once(self):
        """FH-010/FH-014: one immutable snapshot reads each source once."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file("095-commit-issue-resolution-parity")
            repo.call_log.clear()

            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)

            self.assertEqual(snapshot["fatal_errors"], [])
            self.assertEqual(len(snapshot["records"]), 2)
            self.assertEqual(len(snapshot["order"]), 2)
            self.assertTrue(all(ref.startswith("refs/") for ref in snapshot["refs"]))
            self.assertEqual(
                sum(call[:2] == ["git", "log"] for call in repo.call_log), 1
            )
            self.assertEqual(
                sum(call[:2] == ["git", "for-each-ref"] for call in repo.call_log),
                1,
            )

    def test_merge_base_distinguishes_no_base_from_failure(self):
        """FH-014: return code 1 is no common base, not a Git failure."""
        no_base = empty_snapshot()
        result = commit_graph.merge_base(
            disconnected_runner(1), ".", no_base, "left", "right"
        )
        self.assertEqual(result, {"sha": None, "fatal_errors": []})
        self.assertEqual(no_base["fatal_errors"], [])

        failed = empty_snapshot()
        result = commit_graph.merge_base(
            disconnected_runner(128), ".", failed, "left", "right"
        )
        self.assertIsNone(result["sha"])
        self.assertTrue(result["fatal_errors"])
        self.assertEqual(failed["fatal_errors"], [])

    def test_terminated_ancestry_query_is_a_failure(self):
        """FH-019: a signal-terminated Git probe is never a negative answer."""
        snapshot = empty_snapshot()

        result = commit_graph.is_ancestor(
            disconnected_runner(-15), ".", snapshot, "older", "newer"
        )

        self.assertIsNone(result["value"])
        self.assertTrue(result["fatal_errors"])
        self.assertIn("terminated", result["fatal_errors"][0])
        self.assertEqual(snapshot["fatal_errors"], [])

    def test_build_attribution_reads_refs_once(self):
        """FH-010: resolver attribution reuses the snapshot ref inventory."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file("095-commit-issue-resolution-parity")
            repo.call_log.clear()

            result = cr.build_attribution(repo.runner, repo.path)

            self.assertEqual(result["errors"], [])
            self.assertEqual(
                sum(call[:2] == ["git", "for-each-ref"] for call in repo.call_log),
                1,
            )
