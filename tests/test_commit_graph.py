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
import commit_resolution_shapes as shapes  # noqa: E402
from git_repo_builder import GitRepo  # noqa: E402


ALPHA = shapes.ALPHA
BETA = shapes.BETA


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
        "merge_bases_cache": {},
        "ancestor_cache": {},
        "fatal_errors": [],
        "fatal_error_cache_keys": set(),
    }


def derive_for_repo(repo, issue_id):
    """Derive one issue ref's historical fork from the immutable snapshot."""
    errors = []
    ids = cr.known_issue_ids(repo.runner, repo.path, errors)
    assert errors == []
    snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
    topic_refs = {
        ref: cr.issue_id_from_branch(ref, ids)
        for ref in snapshot["refs"]
        if cr.issue_id_from_branch(ref, ids) is not None
    }
    base_refs = [ref for ref in snapshot["refs"] if ref not in topic_refs]
    topic_ref = next(
        ref for ref, found_issue in topic_refs.items() if found_issue == issue_id
    )
    return commit_graph.derive_fork_point(
        repo.runner,
        repo.path,
        snapshot,
        topic_ref,
        issue_id,
        base_refs=base_refs,
    )


def delta_for_repo(repo, issue_id):
    """Measure one registered topic against its own historical fork."""
    errors = []
    ids = cr.known_issue_ids(repo.runner, repo.path, errors)
    assert errors == []
    snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
    topic_refs = {
        ref: cr.issue_id_from_branch(ref, ids)
        for ref in snapshot["refs"]
        if cr.issue_id_from_branch(ref, ids) is not None
    }
    base_refs = [ref for ref in snapshot["refs"] if ref not in topic_refs]
    topic_ref = next(
        ref for ref, found_issue in topic_refs.items() if found_issue == issue_id
    )
    return commit_graph.topic_delta(
        repo.runner,
        repo.path,
        snapshot,
        topic_ref,
        issue_id,
        topic_refs=topic_refs,
        base_refs=base_refs,
    )


def declared_content_truth(repo, issue_id):
    """Fixture truth limited to non-merge commits, via Git's actual graph."""
    non_merges = set(repo._git("rev-list", "--no-merges", "--all").split())
    return repo.truth_for(issue_id) & non_merges


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


class ForkPointInvariantTests(unittest.TestCase):
    def test_snapshot_ref_movement_uses_captured_object_ids(self):
        """FH-023: moving a live base ref cannot change a loaded snapshot's fork."""
        with GitRepo() as repo:
            base_sha = repo.commit("chore: base", belongs_to=None)
            repo.branch(f"codex/{ALPHA}")
            topic_sha = repo.commit("feat: alpha", belongs_to=ALPHA)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            repo._git("update-ref", "refs/heads/main", topic_sha)

            result = commit_graph.derive_fork_point(
                repo.runner,
                repo.path,
                snapshot,
                f"refs/heads/codex/{ALPHA}",
                ALPHA,
                base_refs=["refs/heads/main"],
            )

            self.assertEqual(result["fork_point"], base_sha)
            self.assertEqual(result["diagnostics"], [])

    def test_criss_cross_best_bases_fail_closed_as_ambiguous(self):
        """FH-024: every incomparable --all best base is an ambiguous fork."""
        with GitRepo() as repo:
            repo.commit("chore: root", belongs_to=None)
            repo.branch(f"codex/{ALPHA}")
            topic_side = repo.commit("feat: topic side", belongs_to=ALPHA)
            repo.checkout("main")
            repo.branch("base")
            repo.commit("chore: base side", belongs_to=None)
            repo.checkout(f"codex/{ALPHA}")
            repo.merge("base", message="Merge branch 'base'", belongs_to=ALPHA)
            repo.checkout("base")
            repo.merge(
                topic_side,
                message="Merge topic first side",
                belongs_to=None,
            )
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)

            result = commit_graph.derive_fork_point(
                repo.runner,
                repo.path,
                snapshot,
                f"refs/heads/codex/{ALPHA}",
                ALPHA,
                base_refs=["refs/heads/base"],
            )

            self.assertIsNone(result["fork_point"])
            self.assertEqual(
                [item["code"] for item in result["diagnostics"]],
                ["ambiguous-topic-fork"],
            )

    def test_newer_comparable_candidate_is_the_unique_maximal_fork(self):
        """FH-025: a strict-ancestor candidate loses to the newer fork."""
        with GitRepo() as repo:
            repo.commit("chore: root", belongs_to=None)
            older = repo.commit("chore: older base", belongs_to=None)
            repo._git("branch", "older", older)
            newer = repo.commit("chore: newer base", belongs_to=None)
            repo._git("branch", "newer", newer)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)

            result = commit_graph.derive_fork_point(
                repo.runner,
                repo.path,
                snapshot,
                f"refs/heads/codex/{ALPHA}",
                ALPHA,
                base_refs=["refs/heads/older", "refs/heads/newer"],
            )

            self.assertEqual(result["fork_point"], newer)
            self.assertEqual(result["diagnostics"], [])
            self.assertEqual(snapshot["fatal_errors"], [])

    def test_duplicate_base_refs_are_deduped_in_result_and_queries(self):
        """FH-023: duplicate base inputs cannot duplicate equivalent ref output."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)

            result = commit_graph.derive_fork_point(
                repo.runner,
                repo.path,
                snapshot,
                f"refs/heads/codex/{ALPHA}",
                ALPHA,
                base_refs=["refs/heads/main", "refs/heads/main"],
            )

            self.assertEqual(result["equivalent_base_refs"], ["refs/heads/main"])
            self.assertEqual(
                sum(
                    call[:4]
                    == [
                        "git",
                        "merge-base",
                        "--all",
                        snapshot["refs"][f"refs/heads/codex/{ALPHA}"],
                    ]
                    for call in repo.call_log
                ),
                1,
            )

    def test_cached_fatal_error_is_recorded_once_per_query(self):
        """FH-023: cached failures cannot repeatedly pollute snapshot fatal errors."""
        snapshot = empty_snapshot()
        snapshot["refs"] = {
            "refs/heads/codex/101-alpha": "topic",
            "refs/heads/main": "base",
        }
        runner = disconnected_runner(128)

        for _ in range(2):
            commit_graph.derive_fork_point(
                runner,
                ".",
                snapshot,
                "refs/heads/codex/101-alpha",
                ALPHA,
                base_refs=["refs/heads/main", "refs/heads/main"],
            )

        self.assertEqual(len(snapshot["fatal_errors"]), 1)

    def test_advancing_trunk_does_not_change_fork_point(self):
        """FH-006/FH-011: later trunk work cannot move a topic's fork point."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            before = derive_for_repo(repo, ALPHA)
            repo.checkout("main")
            repo.commit("chore: main advances", belongs_to=None)
            after = derive_for_repo(repo, ALPHA)

            self.assertEqual(after["fork_point"], before["fork_point"])
            self.assertEqual(after["diagnostics"], [])

    def test_equivalent_remote_ref_does_not_change_fork_point(self):
        """FH-012/FH-017: equal-object remote refs remain equivalent by identity."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            before = derive_for_repo(repo, ALPHA)
            repo.publish("main", remote="upstream")
            after = derive_for_repo(repo, ALPHA)

            self.assertEqual(after["fork_point"], before["fork_point"])
            self.assertIn("refs/remotes/upstream/main", after["equivalent_base_refs"])

    def test_disconnected_ref_does_not_change_connected_topic(self):
        """FH-013/FH-014: disconnected refs are ordinary negatives, not failures."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            before = derive_for_repo(repo, ALPHA)
            repo.create_orphan_ref("refs/heads/unrelated")
            after = derive_for_repo(repo, ALPHA)

            self.assertEqual(after["fork_point"], before["fork_point"])
            self.assertEqual(after["diagnostics"], [])

    def test_incomparable_maximal_forks_are_scoped_to_topic(self):
        """FH-006/FH-011/FH-017: incomparable remote histories fail closed per issue."""
        with GitRepo() as repo:
            shapes.ambiguous_same_tail_remotes(repo)

            result = derive_for_repo(repo, ALPHA)

            self.assertIsNone(result["fork_point"])
            self.assertEqual(
                {item["issue_id"] for item in result["diagnostics"]}, {ALPHA}
            )

    def test_same_tail_slash_ref_stays_a_distinct_equivalent_base_ref(self):
        """FH-012/FH-017: full slash ref identity is never reduced to a tail."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            repo._git("branch", "release/main", "main")

            result = derive_for_repo(repo, ALPHA)

            self.assertEqual(result["diagnostics"], [])
            self.assertEqual(
                result["equivalent_base_refs"],
                ["refs/heads/main", "refs/heads/release/main"],
            )

    def test_missing_topic_ref_returns_scoped_diagnostic(self):
        """FH-006/FH-014: a missing topic is diagnostic, not a Git negative."""
        snapshot = empty_snapshot()

        result = commit_graph.derive_fork_point(
            disconnected_runner(1),
            ".",
            snapshot,
            "refs/heads/codex/101-alpha",
            ALPHA,
            base_refs=[],
        )

        self.assertIsNone(result["fork_point"])
        self.assertEqual(result["diagnostics"][0]["code"], "topic-ref-missing")
        self.assertEqual(result["diagnostics"][0]["issue_id"], ALPHA)
        self.assertEqual(snapshot["fatal_errors"], [])

    def test_query_failure_is_preserved_on_snapshot_not_a_negative(self):
        """FH-013/FH-014: failed merge-base probes remain snapshot fatal errors."""
        snapshot = empty_snapshot()
        snapshot["refs"] = {
            "refs/heads/codex/101-alpha": "topic",
            "refs/heads/main": "base",
        }

        result = commit_graph.derive_fork_point(
            disconnected_runner(128),
            ".",
            snapshot,
            "refs/heads/codex/101-alpha",
            ALPHA,
            base_refs=["refs/heads/main"],
        )

        self.assertIsNone(result["fork_point"])
        self.assertEqual(result["diagnostics"][0]["code"], "ambiguous-topic-fork")
        self.assertTrue(snapshot["fatal_errors"])


class TopicDeltaTests(unittest.TestCase):
    def test_published_no_ff_topic_recovers_pre_publication_fork(self):
        """FH-003: main containing the topic tip does not erase its content."""
        with GitRepo() as repo:
            shapes.happy_merge(repo)

            result = delta_for_repo(repo, ALPHA)

            self.assertEqual(result["commits"], declared_content_truth(repo, ALPHA))
            self.assertTrue(result["commits"])

    def test_base_history_is_not_topic_work(self):
        """FH-002: a stale local trunk cannot become alpha's contribution."""
        with GitRepo() as repo:
            shapes.stale_local_default_branch(repo)

            result = delta_for_repo(repo, ALPHA)

            self.assertEqual(result["commits"], repo.truth_for(ALPHA))

    def test_stacked_issue_excludes_inner_content(self):
        """FH-003/FH-005: each stacked issue retains only its declared work."""
        with GitRepo() as repo:
            shapes.two_registered_stacked_issues(repo)

            alpha = delta_for_repo(repo, ALPHA)
            beta = delta_for_repo(repo, BETA)

            self.assertEqual(alpha["commits"], declared_content_truth(repo, ALPHA))
            self.assertEqual(beta["commits"], declared_content_truth(repo, BETA))
            self.assertTrue(alpha["commits"])
            self.assertTrue(beta["commits"])
            self.assertTrue(beta["stacked_exclusions"])

    def test_nested_merge_does_not_relabel_inner_content(self):
        """FH-005: outer topic deltas exclude the inner issue's content."""
        with GitRepo() as repo:
            shapes.nested_merges(repo)

            beta = delta_for_repo(repo, BETA)

            self.assertEqual(beta["commits"], declared_content_truth(repo, BETA))
            self.assertTrue(beta["commits"])
            self.assertTrue(repo.truth_for(ALPHA).isdisjoint(beta["commits"]))
