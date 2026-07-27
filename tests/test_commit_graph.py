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


def disconnected_runner_with_stdout(returncode, stdout):
    """Return a graph runner with controlled successful output."""
    def runner(args, cwd=None):
        return subprocess.CompletedProcess(args, returncode, stdout, "")

    return runner


def results_runner(log_result, ref_result):
    """Route the snapshot's two inventory commands to fixed results."""
    def runner(args, cwd=None):
        result = log_result if args[:2] == ["git", "log"] else ref_result
        return subprocess.CompletedProcess(args, *result)

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

    def test_merge_base_rejects_empty_or_multitoken_success_output(self):
        """FH-022: rc=0 must carry exactly one nonempty merge-base SHA token."""
        for output in ("", "   \n", "first second\n", "first\nsecond\n"):
            with self.subTest(output=output):
                snapshot = empty_snapshot()

                result = commit_graph.merge_base(
                    disconnected_runner_with_stdout(0, output),
                    ".",
                    snapshot,
                    "left",
                    "right",
                )

                self.assertIsNone(result["sha"])
                self.assertTrue(result["fatal_errors"])

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

    def test_cached_query_result_is_defensive(self):
        """FH-019: a caller cannot mutate a cached graph-query result."""
        snapshot = empty_snapshot()
        first = commit_graph.merge_base(
            disconnected_runner(1), ".", snapshot, "left", "right"
        )
        first["fatal_errors"].append("caller mutation")

        second = commit_graph.merge_base(
            disconnected_runner(1), ".", snapshot, "right", "left"
        )

        self.assertEqual(second, {"sha": None, "fatal_errors": []})

    def test_snapshot_failures_propagate_as_strings_without_crashing_resolver(self):
        """FH-014: snapshot command failures fail attribution closed as text."""
        for detail, log_result, ref_result in (
            ("bad log", (128, "", "fatal: bad log"), (0, "", "")),
            ("bad refs", (0, "", ""), (128, "", "fatal: bad refs")),
        ):
            with self.subTest(detail=detail):
                result = cr.build_attribution(
                    results_runner(log_result, ref_result), "."
                )
                self.assertTrue(result["errors"])
                self.assertTrue(
                    all(isinstance(error, str) for error in result["errors"])
                )
                self.assertIn(detail, result["errors"][0])

    def test_malformed_log_sha_is_a_fatal_error(self):
        """FH-014: a successful log response still needs a nonempty SHA."""
        runner = results_runner(
            (0, "\x00subject\x00\x00body\x01", ""),
            (0, "refs/heads/main abc123\n", ""),
        )

        snapshot = commit_graph.load_snapshot(runner, ".")

        self.assertEqual(snapshot["records"], {})
        self.assertTrue(snapshot["fatal_errors"])
        self.assertTrue(all(isinstance(error, str) for error in snapshot["fatal_errors"]))

    def test_malformed_ref_output_is_a_fatal_error(self):
        """FH-010: refs require a name and object while remote HEAD is ignored."""
        cases = ("refs/heads/main\n", " deadbeef\n", "refs/heads/main \n")
        for output in cases:
            with self.subTest(output=output):
                runner = results_runner((0, "", ""), (0, output, ""))
                snapshot = commit_graph.load_snapshot(runner, ".")
                self.assertTrue(snapshot["fatal_errors"])
        valid_head = results_runner(
            (0, "", ""), (0, "refs/remotes/origin/HEAD deadbeef\n", "")
        )
        self.assertEqual(commit_graph.load_snapshot(valid_head, ".")["fatal_errors"], [])

    def test_package_consumers_import_without_test_sys_path(self):
        """FH-010: sibling loading supports package consumers in a clean process."""
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from scripts import linkage_check, project_converge",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_file_mode_import_rejects_an_unrelated_preloaded_graph_module(self):
        """FH-021: file-mode resolver loading must not reuse foreign modules."""
        root = Path(__file__).resolve().parents[1]
        code = """
import importlib.util
import sys
import types
from pathlib import Path
foreign = types.ModuleType('commit_graph')
foreign.GIT_LOG_FORMAT = 'foreign'
sys.modules['commit_graph'] = foreign
path = Path('scripts/commit_resolution.py').resolve()
spec = importlib.util.spec_from_file_location('isolated_commit_resolution', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert Path(module.commit_graph.__file__).resolve() == path.with_name('commit_graph.py')
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

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
