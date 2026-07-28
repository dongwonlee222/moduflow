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
    def test_publication_recovery_ignores_unrelated_history_for_command_count(self):
        """FH-029: unrelated snapshot records add no topic-delta Git probes."""
        with GitRepo() as small, GitRepo() as large:
            shapes.happy_merge(small)
            shapes.happy_merge(large)
            large.branch("unrelated")
            for index in range(8):
                large.commit(f"chore: unrelated {index}", belongs_to=None)
            large.checkout("main")
            large.merge("unrelated", message="Merge branch 'unrelated'", belongs_to=None)
            large.delete_branch("unrelated")

            small.call_log.clear()
            small_result = delta_for_repo(small, ALPHA)
            small_calls = len(small.call_log)
            large.call_log.clear()
            large_result = delta_for_repo(large, ALPHA)
            large_calls = len(large.call_log)

            self.assertEqual(small_result["commits"], declared_content_truth(small, ALPHA))
            self.assertEqual(large_result["commits"], declared_content_truth(large, ALPHA))
            self.assertTrue(small_result["commits"])
            self.assertTrue(large_result["commits"])
            self.assertEqual(small_calls, large_calls)
            self.assertGreaterEqual(small_calls, 3)
            self.assertLessEqual(small_calls, 8)
            self.assertTrue(any(call[:2] == ["git", "log"] for call in small.call_log))
            self.assertTrue(any(call[:2] == ["git", "for-each-ref"] for call in small.call_log))
            self.assertTrue(any(call[:3] == ["git", "merge-base", "--all"] for call in small.call_log))
            self.assertTrue(any(call[:2] == ["git", "rev-list"] for call in small.call_log))

    def test_publication_recovery_ignores_pre_topic_unrelated_merge(self):
        """FH-029: only a merge whose parent is the topic tip is publication."""
        with GitRepo() as small, GitRepo() as large:
            shapes.happy_merge(small)
            large.commit("chore: root", belongs_to=None)
            large.add_issue_file(ALPHA)
            large.branch("long-lived-unrelated")
            large.commit("chore: unrelated before topic", belongs_to=None)
            large.checkout("main")
            topic = large.branch(f"codex/{ALPHA}")
            large.commit("feat: alpha work", belongs_to=ALPHA)
            large.checkout("main")
            large.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            large.merge(
                "long-lived-unrelated",
                message="Merge branch 'long-lived-unrelated'",
                belongs_to=None,
            )
            large.delete_branch("long-lived-unrelated")

            small.call_log.clear()
            small_result = delta_for_repo(small, ALPHA)
            small_calls = len(small.call_log)
            large.call_log.clear()
            large_result = delta_for_repo(large, ALPHA)
            large_calls = len(large.call_log)

            self.assertEqual(small_result["commits"], declared_content_truth(small, ALPHA))
            self.assertEqual(large_result["commits"], declared_content_truth(large, ALPHA))
            self.assertTrue(small_result["commits"])
            self.assertTrue(large_result["commits"])
            self.assertEqual(small_calls, large_calls)
            self.assertEqual(small_calls, 6)
            self.assertTrue(any(call[:3] == ["git", "merge-base", "--all"] for call in small.call_log))
            self.assertTrue(any(call[:2] == ["git", "rev-list"] for call in small.call_log))

    def test_published_no_ff_topic_recovers_pre_publication_fork(self):
        """FH-003: main containing the topic tip does not erase its content."""
        with GitRepo() as repo:
            shapes.happy_merge(repo)

            result = delta_for_repo(repo, ALPHA)

            self.assertEqual(result["commits"], declared_content_truth(repo, ALPHA))
            self.assertTrue(result["commits"])

    def test_advanced_topic_ref_keeps_published_and_new_content(self):
        """FH-003: a live ref advanced after publication retains T1 and T2."""
        with GitRepo() as repo:
            shapes.happy_merge(repo)
            repo.checkout(f"codex/{ALPHA}")
            repo.commit("feat: alpha follow-up", belongs_to=ALPHA)

            result = delta_for_repo(repo, ALPHA)

            self.assertEqual(result["commits"], declared_content_truth(repo, ALPHA))
            self.assertTrue(result["commits"])

    def test_twice_published_topic_keeps_the_earliest_pre_publication_fork(self):
        """FH-003: two no-ff publications retain both T1 and T2, not only T2."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            topic = repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: T1", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            repo.checkout(topic)
            repo.commit("feat: T2", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)

            result = delta_for_repo(repo, ALPHA)

            self.assertEqual(result["commits"], declared_content_truth(repo, ALPHA))
            self.assertTrue(result["commits"])
            self.assertEqual(result["diagnostics"], [])

    def test_published_tip_alias_does_not_replace_the_earliest_fork(self):
        """FH-003: a non-issue alias at T1 is publication evidence, not a base."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            topic = repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: T1", belongs_to=ALPHA)
            t1 = repo.head()
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            repo._git("branch", "release/last-topic", t1)
            repo.checkout(topic)
            repo.commit("feat: T2", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            result = delta_for_repo(repo, ALPHA)
            self.assertEqual(result["commits"], declared_content_truth(repo, ALPHA))
            self.assertTrue(result["commits"])

    def test_archive_named_published_tip_alias_is_ref_order_independent(self):
        """FH-003: an alias sorted before main cannot elect T1 as the fork."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            topic = repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: T1", belongs_to=ALPHA)
            t1 = repo.head()
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            repo._git("branch", "archive/last-topic", t1)
            repo.checkout(topic)
            repo.commit("feat: T2", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            result = delta_for_repo(repo, ALPHA)
            self.assertEqual(result["commits"], declared_content_truth(repo, ALPHA))
            self.assertTrue(result["commits"])
            self.assertEqual(result["diagnostics"], [])

    def test_intermediate_published_topic_alias_does_not_replace_earliest_fork(self):
        """FH-003: Tmid alias is part of the published topic line, not a base."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            topic = repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: T1", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            repo.checkout(topic)
            repo.commit("feat: Tmid", belongs_to=ALPHA)
            mid = repo.head()
            repo._git("branch", "archive/mid-topic", mid)
            repo.commit("feat: T2", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            result = delta_for_repo(repo, ALPHA)
            self.assertEqual(result["commits"], declared_content_truth(repo, ALPHA))
            self.assertTrue(result["commits"])
            self.assertEqual(result["diagnostics"], [])

    def test_published_topic_with_incomparable_other_base_is_ambiguous(self):
        """FH-002: recovery must not discard an incomparable ordinary base."""
        with GitRepo() as repo:
            root = repo.commit("chore: root", belongs_to=None)
            repo.commit("chore: main base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            alpha = repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            repo.checkout(root)
            other = repo.branch("other-base")
            other_work = repo.commit("chore: other base", belongs_to=None)
            repo.checkout(alpha)
            repo.merge(other, message="Merge branch 'other-base'", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(alpha, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)

            result = delta_for_repo(repo, ALPHA)

            self.assertIsNone(result["fork_point"])
            self.assertEqual(result["commits"], set())
            self.assertEqual(result["diagnostics"][0]["code"], "ambiguous-topic-fork")
            self.assertNotIn(other_work, result["commits"])

    def test_sync_merged_incomparable_first_parent_base_stays_ambiguous(self):
        """FH-002: sync merge must not erase develop A as a false alias."""
        with GitRepo() as repo:
            root = repo.commit("chore: root", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.commit("chore: main F", belongs_to=None)
            repo._git("branch", "develop", root)
            repo.checkout("develop")
            repo.commit("chore: develop A", belongs_to=None)
            topic = repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            repo.merge("main", message="Merge branch 'main' into codex", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            result = delta_for_repo(repo, ALPHA)
            self.assertIsNone(result["fork_point"])
            self.assertEqual(result["commits"], set())
            self.assertEqual(result["diagnostics"][0]["code"], "ambiguous-topic-fork")

    def test_comparable_develop_base_behind_publication_side_is_retained(self):
        """FH-002: develop A behind T is a real comparable fork, not an alias."""
        with GitRepo() as repo:
            repo.commit("chore: root", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.commit("chore: main F", belongs_to=None)
            repo.branch("develop")
            repo.checkout("develop")
            a = repo.commit("chore: develop A", belongs_to=None)
            topic = repo.branch(f"codex/{ALPHA}")
            work = repo.commit("feat: topic", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            result = delta_for_repo(repo, ALPHA)
            self.assertEqual(result["fork_point"], a)
            self.assertEqual(result["commits"], {work})

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

    def test_stacked_pairwise_merge_base_failure_fails_closed_and_stays_closed_when_cached(self):
        """FH-010: a broken beta/alpha exclusion query cannot leak beta work."""
        with GitRepo() as repo:
            shapes.two_registered_stacked_issues(repo)
            errors = []
            ids = cr.known_issue_ids(repo.runner, repo.path, errors)
            self.assertEqual(errors, [])
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            topic_refs = {
                ref: cr.issue_id_from_branch(ref, ids)
                for ref in snapshot["refs"]
                if cr.issue_id_from_branch(ref, ids) is not None
            }
            base_refs = [ref for ref in snapshot["refs"] if ref not in topic_refs]
            beta_ref = next(ref for ref, issue in topic_refs.items() if issue == BETA)
            alpha_ref = next(ref for ref, issue in topic_refs.items() if issue == ALPHA)
            failing_args = [
                "git", "merge-base", "--all", snapshot["refs"][beta_ref],
                snapshot["refs"][alpha_ref],
            ]
            calls = []

            def failing(args, cwd=None):
                calls.append(args)
                if args == failing_args:
                    return subprocess.CompletedProcess(args, 128, "", "pairwise unavailable")
                return repo.runner(args, cwd)

            first = commit_graph.topic_delta(
                failing, repo.path, snapshot, beta_ref, BETA,
                topic_refs=topic_refs, base_refs=base_refs,
            )
            second = commit_graph.topic_delta(
                failing, repo.path, snapshot, beta_ref, BETA,
                topic_refs=topic_refs, base_refs=base_refs,
            )

            self.assertEqual(first["commits"], set())
            self.assertEqual(second["commits"], set())
            self.assertTrue(snapshot["fatal_errors"])
            self.assertEqual(sum(call == failing_args for call in calls), 1)

    def test_stacked_pairwise_terminated_merge_base_fails_closed(self):
        """FH-010: terminated pairwise exclusion is fatal, not a no-base negative."""
        with GitRepo() as repo:
            shapes.two_registered_stacked_issues(repo)
            errors = []
            ids = cr.known_issue_ids(repo.runner, repo.path, errors)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            topic_refs = {ref: cr.issue_id_from_branch(ref, ids) for ref in snapshot["refs"] if cr.issue_id_from_branch(ref, ids) is not None}
            base_refs = [ref for ref in snapshot["refs"] if ref not in topic_refs]
            beta_ref = next(ref for ref, issue in topic_refs.items() if issue == BETA)
            alpha_ref = next(ref for ref, issue in topic_refs.items() if issue == ALPHA)
            failing_args = ["git", "merge-base", "--all", snapshot["refs"][beta_ref], snapshot["refs"][alpha_ref]]

            def terminated(args, cwd=None):
                if args == failing_args:
                    return subprocess.CompletedProcess(args, -15, "", "")
                return repo.runner(args, cwd)

            result = commit_graph.topic_delta(terminated, repo.path, snapshot, beta_ref, BETA, topic_refs=topic_refs, base_refs=base_refs)
            self.assertEqual(result["commits"], set())
            self.assertTrue(any("terminated by signal" in error for error in snapshot["fatal_errors"]))

    def test_stacked_cached_above_fork_failure_stays_closed(self):
        """FH-010: cached ancestry failure cannot turn into a false exclusion."""
        with GitRepo() as repo:
            shapes.two_registered_stacked_issues(repo)
            errors = []
            ids = cr.known_issue_ids(repo.runner, repo.path, errors)
            self.assertEqual(errors, [])
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            topic_refs = {
                ref: cr.issue_id_from_branch(ref, ids)
                for ref in snapshot["refs"]
                if cr.issue_id_from_branch(ref, ids) is not None
            }
            base_refs = [ref for ref in snapshot["refs"] if ref not in topic_refs]
            beta_ref = next(ref for ref, issue in topic_refs.items() if issue == BETA)
            alpha_ref = next(ref for ref, issue in topic_refs.items() if issue == ALPHA)
            fork = commit_graph.derive_fork_point(
                repo.runner, repo.path, snapshot, beta_ref, BETA,
                base_refs=base_refs,
            )
            pair = commit_graph.merge_bases(
                repo.runner, repo.path, snapshot,
                snapshot["refs"][beta_ref], snapshot["refs"][alpha_ref],
            )
            candidate = next(
                sha for sha in pair["shas"]
                if sha not in (fork["fork_point"], snapshot["refs"][beta_ref])
            )
            failing_args = [
                "git", "merge-base", "--is-ancestor", fork["fork_point"], candidate,
            ]
            calls = []

            def failing(args, cwd=None):
                calls.append(args)
                if args == failing_args:
                    return subprocess.CompletedProcess(args, 128, "", "ancestry unavailable")
                return repo.runner(args, cwd)

            kwargs = {"topic_refs": topic_refs, "base_refs": base_refs}
            first = commit_graph.topic_delta(failing, repo.path, snapshot, beta_ref, BETA, **kwargs)
            second = commit_graph.topic_delta(failing, repo.path, snapshot, beta_ref, BETA, **kwargs)

            self.assertEqual(first["commits"], set())
            self.assertEqual(second["commits"], set())
            self.assertEqual(len(snapshot["fatal_errors"]), 1)
            self.assertEqual(sum(call == failing_args for call in calls), 1)
            self.assertTrue(repo.truth_for(ALPHA).isdisjoint(second["commits"]))

    def test_membership_replays_cached_pair_failure(self):
        """FH-010: pairwise cached fatal stays visible on both membership builds."""
        with GitRepo() as repo:
            shapes.two_registered_stacked_issues(repo)
            errors = []
            ids = cr.known_issue_ids(repo.runner, repo.path, errors)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            beta = snapshot["refs"][f"refs/heads/codex/{BETA}"]
            alpha = snapshot["refs"][f"refs/heads/codex/{ALPHA}"]
            target_shas = {beta, alpha}
            calls = []
            def failing(args, cwd=None):
                calls.append(args)
                if args[:3] == ["git", "merge-base", "--all"] and set(args[3:]) == target_shas:
                    return subprocess.CompletedProcess(args, 128, "", "pair unavailable")
                return repo.runner(args, cwd)
            first = cr.build_branch_membership(failing, repo.path, issue_ids=ids, snapshot=snapshot)
            second = cr.build_branch_membership(failing, repo.path, issue_ids=ids, snapshot=snapshot)
            for built in (first, second):
                self.assertEqual(built["membership"], {})
                self.assertTrue(built["errors"])
                self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, built["degraded"])
                self.assertEqual(len(built["errors"]), 1)
                self.assertEqual(len(built["errors"]), len(set(built["errors"])))
            self.assertEqual(first["errors"], second["errors"])
            self.assertEqual(first["degraded"], second["degraded"])
            self.assertEqual(sum(call[:3] == ["git", "merge-base", "--all"] and set(call[3:]) == target_shas for call in calls), 1)

    def test_membership_replays_cached_above_fork_failure(self):
        """FH-010: above-fork cached fatal stays visible on both builds."""
        with GitRepo() as repo:
            shapes.two_registered_stacked_issues(repo)
            errors = []
            ids = cr.known_issue_ids(repo.runner, repo.path, errors)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            beta_ref = f"refs/heads/codex/{BETA}"
            alpha_ref = f"refs/heads/codex/{ALPHA}"
            refs = {ref: cr.issue_id_from_branch(ref, ids) for ref in snapshot["refs"] if cr.issue_id_from_branch(ref, ids)}
            bases = [ref for ref in snapshot["refs"] if ref not in refs]
            fork = commit_graph.derive_fork_point(repo.runner, repo.path, snapshot, beta_ref, BETA, base_refs=bases)
            candidate = next(sha for sha in commit_graph.merge_bases(repo.runner, repo.path, snapshot, snapshot["refs"][beta_ref], snapshot["refs"][alpha_ref])["shas"] if sha != fork["fork_point"])
            target = ["git", "merge-base", "--is-ancestor", fork["fork_point"], candidate]
            calls = []
            def failing(args, cwd=None):
                calls.append(args)
                if args == target:
                    return subprocess.CompletedProcess(args, 128, "", "above unavailable")
                return repo.runner(args, cwd)
            first = cr.build_branch_membership(failing, repo.path, issue_ids=ids, snapshot=snapshot)
            second = cr.build_branch_membership(failing, repo.path, issue_ids=ids, snapshot=snapshot)
            for built in (first, second):
                self.assertEqual(built["membership"], {})
                self.assertTrue(built["errors"])
                self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, built["degraded"])
            self.assertEqual(sum(call == target for call in calls), 1)

    def test_membership_replays_cached_maximalization_failure(self):
        """FH-010/FH-028: cached A→B exclusion comparison stays observable."""
        gamma = "103-gamma"
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.add_issue_file(BETA)
            repo.add_issue_file(gamma)
            alpha = repo.branch(f"codex/{ALPHA}")
            a_work = repo.commit("feat: alpha", belongs_to=ALPHA)
            beta = repo.branch(f"codex/{BETA}")
            b_work = repo.commit("feat: beta", belongs_to=BETA)
            gamma_ref = repo.branch(f"codex/{gamma}")
            repo.commit("feat: gamma", belongs_to=gamma)
            repo.checkout("main")
            errors = []
            ids = cr.known_issue_ids(repo.runner, repo.path, errors)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            target = ["git", "merge-base", "--is-ancestor", a_work, b_work]
            calls = []

            def failing(args, cwd=None):
                calls.append(args)
                if args == target:
                    return subprocess.CompletedProcess(args, 128, "", "maximalization unavailable")
                return repo.runner(args, cwd)

            first = cr.build_branch_membership(failing, repo.path, issue_ids=ids, snapshot=snapshot)
            second = cr.build_branch_membership(failing, repo.path, issue_ids=ids, snapshot=snapshot)
            for built in (first, second):
                self.assertEqual(built["membership"], {})
                self.assertTrue(built["errors"])
                self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, built["degraded"])
            self.assertEqual(sum(call == target for call in calls), 1)
            self.assertEqual(len(snapshot["fatal_errors"]), 1)

    def test_cached_fork_query_failure_fails_closed_even_with_another_fork_candidate(self):
        """FH-010: a cached fork failure cannot be hidden by a good base ref."""
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            repo.checkout("main")
            repo.commit("chore: release base", belongs_to=None)
            repo._git("branch", "release/main", "main")
            repo.commit("chore: main advances", belongs_to=None)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            topic_ref = f"refs/heads/codex/{ALPHA}"
            bad_base = "refs/heads/main"
            good_base = "refs/heads/release/main"
            failing_args = ["git", "merge-base", "--all", snapshot["refs"][topic_ref], snapshot["refs"][bad_base]]

            def failing(args, cwd=None):
                if args == failing_args:
                    return subprocess.CompletedProcess(args, 128, "", "cached fork unavailable")
                return repo.runner(args, cwd)

            initial = commit_graph.derive_fork_point(
                failing, repo.path, snapshot, topic_ref, ALPHA,
                base_refs=[bad_base, good_base],
            )
            self.assertIsNotNone(initial["fork_point"])
            result = commit_graph.topic_delta(
                failing, repo.path, snapshot, topic_ref, ALPHA,
                topic_refs={topic_ref: ALPHA}, base_refs=[bad_base, good_base],
            )
            self.assertEqual(result["commits"], set())
            self.assertTrue(snapshot["fatal_errors"])

    def test_cached_publication_recovery_failure_stays_closed(self):
        """FH-010: cached recovery failures must close every later delta call."""
        with GitRepo() as repo:
            base = repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            topic = repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            repo._git("branch", "older-base", base)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            topic_ref = f"refs/heads/codex/{ALPHA}"
            topic_sha = snapshot["refs"][topic_ref]
            publication = next(
                record for record in snapshot["records"].values()
                if topic_sha in record["parents"] and len(record["parents"]) == 2
            )
            base_parent = next(parent for parent in publication["parents"] if parent != topic_sha)
            failing_args = ["git", "merge-base", "--all", topic_sha, base_parent]
            calls = []

            def failing(args, cwd=None):
                calls.append(args)
                if args == failing_args:
                    return subprocess.CompletedProcess(args, 128, "", "recovery unavailable")
                return repo.runner(args, cwd)

            kwargs = {
                "topic_refs": {topic_ref: ALPHA},
                "base_refs": ["refs/heads/main", "refs/heads/older-base"],
            }
            first = commit_graph.topic_delta(failing, repo.path, snapshot, topic_ref, ALPHA, **kwargs)
            second = commit_graph.topic_delta(failing, repo.path, snapshot, topic_ref, ALPHA, **kwargs)

            self.assertEqual(first["commits"], set())
            self.assertEqual(second["commits"], set())
            self.assertEqual(len(snapshot["fatal_errors"]), 1)
            self.assertEqual(sum(call == failing_args for call in calls), 1)

    def test_cached_publication_topology_failure_stays_closed_with_good_base(self):
        """FH-010/FH-028: cached missing topology remains fatal for this topic."""
        with GitRepo() as repo:
            root = repo.commit("chore: root", belongs_to=None)
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            topic = repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            repo.checkout("main")
            repo.merge(topic, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
            repo._git("branch", "older-good-base", root)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            topic_ref = f"refs/heads/codex/{ALPHA}"
            topic_sha = snapshot["refs"][topic_ref]
            publication = next(record for record in snapshot["records"].values() if topic_sha in record["parents"] and len(record["parents"]) == 2)
            missing = next(parent for parent in publication["parents"] if parent != topic_sha)
            del snapshot["records"][missing]
            kwargs = {"topic_refs": {topic_ref: ALPHA}, "base_refs": ["refs/heads/main", "refs/heads/older-good-base"]}

            first = commit_graph.topic_delta(repo.runner, repo.path, snapshot, topic_ref, ALPHA, **kwargs)
            second = commit_graph.topic_delta(repo.runner, repo.path, snapshot, topic_ref, ALPHA, **kwargs)

            self.assertEqual(first["commits"], set())
            self.assertEqual(second["commits"], set())
            self.assertTrue(first["fatal_errors"])
            self.assertTrue(second["fatal_errors"])
            self.assertEqual(len(snapshot["fatal_errors"]), 1)

    def test_cached_topology_failure_reaches_membership_on_every_build(self):
        """FH-010/FH-028: cached graph failure remains scoped and observable."""
        with GitRepo() as repo:
            shapes.two_registered_stacked_issues(repo)
            errors = []
            ids = cr.known_issue_ids(repo.runner, repo.path, errors)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            beta_ref = f"refs/heads/codex/{BETA}"
            parent = snapshot["records"][snapshot["refs"][beta_ref]]["parents"][0]
            del snapshot["records"][parent]

            first = cr.build_branch_membership(repo.runner, repo.path, issue_ids=ids, snapshot=snapshot)
            first_error_count = len(snapshot["fatal_errors"])
            second = cr.build_branch_membership(repo.runner, repo.path, issue_ids=ids, snapshot=snapshot)

            self.assertEqual(first["membership"], {})
            self.assertEqual(second["membership"], {})
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, first["degraded"])
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, second["degraded"])
            self.assertTrue(first["errors"])
            self.assertTrue(second["errors"])
            self.assertGreater(first_error_count, 0)
            self.assertEqual(len(snapshot["fatal_errors"]), first_error_count)

    def test_nested_merge_does_not_relabel_inner_content(self):
        """FH-005: outer topic deltas exclude the inner issue's content."""
        with GitRepo() as repo:
            shapes.nested_merges(repo)

            beta = delta_for_repo(repo, BETA)

            self.assertEqual(beta["commits"], declared_content_truth(repo, BETA))
            self.assertTrue(beta["commits"])
            self.assertTrue(repo.truth_for(ALPHA).isdisjoint(beta["commits"]))
