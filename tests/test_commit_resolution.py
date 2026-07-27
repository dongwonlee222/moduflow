#!/usr/bin/env python3
"""Shared commit-to-issue resolver (issue 095, stream A).

Covers the spec's regression table: trailer-only, branch-only, mixed,
merge-subject with the branch deleted, detached HEAD, unmatched commits, and
the batching constraint that converge must not fan out per commit.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import commit_resolution as cr  # noqa: E402
from git_repo_builder import GitRepo  # noqa: E402

ISSUE = "095-commit-issue-resolution-parity"
OTHER = "094-risk-based-security-and-quality-review-gate"


class TestTrailerResolution(unittest.TestCase):
    def test_trailer_commit_resolves(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            sha = repo.commit("feat: something", issue=ISSUE)
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")
            self.assertEqual(out["errors"], [])

    def test_commit_without_trailer_or_branch_is_unresolved(self):
        with GitRepo() as repo:
            sha = repo.commit("chore: unrelated")
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])
            self.assertIsNone(out["source"])


class TestBranchResolution(unittest.TestCase):
    def test_branch_only_commit_resolves(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            sha = repo.commit("feat: no trailer here")
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "branch")

    def test_trailer_wins_over_branch(self):
        """Precedence rule: trailer > branch (Global Constraint 2)."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(OTHER)
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{OTHER}")
            sha = repo.commit("feat: trailer disagrees with branch", issue=ISSUE)
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")


class TestMergeSubjectResolution(unittest.TestCase):
    def test_merge_subject_resolves_after_branch_deleted(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: work")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            sources = {c["source"] for c in out["commits"]}
            self.assertIn("merge-subject", sources)


class TestOverCollection(unittest.TestCase):
    """Branch containment is not branch authorship.

    A branch cut from main has all of main as ancestors, so plain
    `git rev-list <branch>` attributes the entire base history to the issue.
    Measured on issue 093 while building this module: 279 collected against 52
    actually contributed. This test fixes the boundary."""

    def test_base_history_is_not_attributed_to_the_branch(self):
        with GitRepo() as repo:
            base_one = repo.commit("chore: base one")
            base_two = repo.commit("chore: base two")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: branch work")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            shas = {c["sha"] for c in out["commits"]}

            self.assertIn(mine, shas, "the branch's own commit must be collected")
            self.assertNotIn(base_one, shas, "base history predates the branch")
            self.assertNotIn(base_two, shas, "base history predates the branch")

    def test_merged_branch_contribution_survives_branch_deletion(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: no trailer, branch only")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            shas = {c["sha"] for c in out["commits"]}
            self.assertIn(
                mine,
                shas,
                "merge topology must still attribute the commit once the branch is gone",
            )


class TestIssueToCommits(unittest.TestCase):
    def test_collects_trailer_and_branch_commits(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            with_trailer = repo.commit("feat: a", issue=ISSUE)
            without_trailer = repo.commit("feat: b")
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            shas = {c["sha"] for c in out["commits"]}
            self.assertIn(with_trailer, shas)
            self.assertIn(
                without_trailer,
                shas,
                "branch-only commit must be collected — this is the issue 095 defect",
            )

    def test_unmatched_count_is_reported(self):
        with GitRepo() as repo:
            repo.commit("chore: unrelated one")
            repo.commit("chore: unrelated two")
            repo.add_issue_file(ISSUE)
            repo.commit("feat: mine", issue=ISSUE)
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertEqual(len(out["commits"]), 1)
            self.assertEqual(out["repo_unmatched_count"], 3)
            self.assertEqual(out["repo_examined_count"], 4)
            self.assertEqual(out["errors"], [], "unmatched is descriptive, not an error")

    def test_each_commit_carries_its_source(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: a", issue=ISSUE)
            repo.commit("feat: b")
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            for entry in out["commits"]:
                self.assertIn(entry["source"], cr.SOURCE_PRECEDENCE)


class TestDetachedHead(unittest.TestCase):
    def test_trailer_resolves_and_branch_gap_is_reported(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            sha = repo.commit("feat: work", issue=ISSUE)
            repo.detach()
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")
            self.assertEqual(out["errors"], [], "degraded resolution must not raise")

    def test_commit_orphaned_by_branch_deletion_resolves_to_nothing(self):
        """A known limitation, asserted rather than hidden.

        Delete the only branch holding a commit and it becomes unreachable
        from every ref, so `--all` does not see it and no source can attribute
        it. It resolves to `None`, indistinguishable from a commit that
        genuinely belongs to no issue.

        `degraded` is deliberately empty here. The flag means branch evidence
        could not be consulted; here there is no evidence left to consult,
        which is a different thing. The previous version of this test asserted
        `branch-unavailable` and passed with its own `detach()` removed — it
        never checked what its name claimed."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            sha = repo.commit("feat: no trailer")
            repo.checkout("main")
            repo.delete_branch(name)

            index = cr.build_attribution(repo.runner, repo.path)
            self.assertNotIn(sha, index["records"], "an orphaned commit is unreachable")

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])
            self.assertEqual(out["degraded"], [])

    def test_a_trailer_survives_branch_deletion(self):
        """The reason the trailer outranks branch evidence: it is intrinsic to
        the commit and does not depend on a ref still existing."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            sha = repo.commit("feat: with trailer", issue=ISSUE)
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")


class TestBatching(unittest.TestCase):
    """Global Constraint 4: git calls must not scale with history length."""

    def _calls_for_history(self, commit_count):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            for index in range(commit_count):
                repo.commit(f"feat: step {index}")
            repo.call_count = 0
            cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            return repo.call_count

    def test_call_count_independent_of_history_length(self):
        small = self._calls_for_history(3)
        large = self._calls_for_history(30)
        self.assertEqual(
            small,
            large,
            f"git calls grew with history: {small} for 3 commits, {large} for 30",
        )

    def test_membership_is_built_once(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            for index in range(5):
                repo.commit(f"feat: step {index}")
            membership = cr.build_branch_membership(repo.runner, repo.path)
            self.assertTrue(membership["membership"])
            head = repo.head()
            self.assertIn(head, membership["membership"])
            self.assertTrue(
                any(
                    name.endswith(f"codex/{ISSUE}")
                    for name in membership["membership"][head]
                )
            )


class TestParity(unittest.TestCase):
    """Both query directions must agree — the check that stops the two
    consumers drifting apart again."""

    def test_directions_agree_on_mixed_history(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: a", issue=ISSUE)
            repo.commit("feat: b")
            repo.commit("feat: c", issue=ISSUE)

            self._assert_directions_agree(repo)

    def test_directions_agree_on_merged_history(self):
        """The asymmetry this pins: while stream A was being built, only the
        issue->commits direction consulted merge topology, so a merged branch
        commit resolved from one direction and not the other. On 30 real
        commits that disagreed 13 times."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            merged = repo.commit("feat: no trailer, branch only")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)

            index = cr.build_attribution(repo.runner, repo.path)
            per_commit = cr.resolve_issue_for_commit(
                repo.runner, repo.path, merged, attribution=index["attribution"]
            )
            self.assertEqual(
                per_commit["issue_id"],
                ISSUE,
                "a merged branch commit must resolve from the commit direction too",
            )
            self._assert_directions_agree(repo)

    def _assert_directions_agree(self, repo):
        index = cr.build_attribution(repo.runner, repo.path)
        from_issue = {
            c["sha"]
            for c in cr.resolve_commits_for_issue(
                repo.runner, repo.path, ISSUE, index=index
            )["commits"]
        }
        from_commits = set()
        for sha in repo.log_shas():
            out = cr.resolve_issue_for_commit(
                repo.runner, repo.path, sha, attribution=index["attribution"]
            )
            if out["issue_id"] == ISSUE:
                from_commits.add(sha)

        self.assertEqual(
            from_issue,
            from_commits,
            "issue→commits and commit→issue resolved different sets",
        )


class TestRegressionMatrix(unittest.TestCase):
    """The remaining rows of the spec's regression table (issue 095, task D1).

    Streams A and B covered the rows they needed as they went; these fill the
    rest so the table is a coverage contract rather than a wish list."""

    def test_trailer_survives_rebase_style_rewrite(self):
        """A trailer is intrinsic to the commit, so it outlives history edits
        that branch and merge evidence do not."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: with trailer", issue=ISSUE)
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            sources = {c["source"] for c in out["commits"]}
            self.assertIn("trailer", sources)

    def test_two_issues_in_one_history_do_not_bleed(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.add_issue_file(OTHER)
            mine = repo.commit("feat: mine", issue=ISSUE)
            theirs = repo.commit("feat: theirs", issue=OTHER)

            mine_out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            theirs_out = cr.resolve_commits_for_issue(repo.runner, repo.path, OTHER)

            self.assertEqual([c["sha"] for c in mine_out["commits"]], [mine])
            self.assertEqual([c["sha"] for c in theirs_out["commits"]], [theirs])

    def test_branch_suffix_resolves_to_the_issue_not_the_suffix(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}-engine")
            mine = repo.commit("feat: suffixed branch")
            repo.checkout("main")
            repo.merge(name, message=f"Merge branch 'codex/{ISSUE}-engine'")

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertIn(mine, {c["sha"] for c in out["commits"]})

    def test_unknown_issue_id_resolves_nothing_without_error(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.commit("feat: mine", issue=ISSUE)

            out = cr.resolve_commits_for_issue(
                repo.runner, repo.path, "999-does-not-exist"
            )
            self.assertEqual(out["commits"], [])
            self.assertEqual(out["errors"], [])
            self.assertEqual(out["repo_unmatched_count"], 2)

    def test_empty_repository_is_not_an_error(self):
        with GitRepo() as repo:
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertEqual(out["commits"], [])
            self.assertEqual(out["repo_examined_count"], 0)

    def test_git_failure_is_reported_not_swallowed(self):
        with GitRepo() as repo:
            repo.commit("chore: base")

            def failing(args, cwd=None):
                if args[:2] == ["git", "log"]:
                    class Result:
                        returncode = 128
                        stdout = ""
                        stderr = "fatal: bad revision"

                    return Result()
                return repo.runner(args, cwd)

            out = cr.resolve_commits_for_issue(failing, repo.path, ISSUE)
            self.assertEqual(out["commits"], [])
            self.assertTrue(out["errors"])
            self.assertIn("bad revision", out["errors"][0])


class TestRemoteTrackingRefs(unittest.TestCase):
    """Issue 095 review, finding 1 and 3.

    Every branch in a real repository exists twice: `codex/X` and
    `origin/codex/X`. The first implementation excluded only the exact branch
    name from its rev-list, so the counterpart re-included the branch and it
    excluded itself — `build_branch_membership` returned an empty map against
    this repository while passing 33 tests, because no fixture had a remote."""

    def test_live_branch_with_remote_counterpart_still_resolves(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: unmerged branch work")
            repo.publish(name)
            repo.checkout("main")

            built = cr.build_branch_membership(repo.runner, repo.path)
            self.assertIn(
                mine,
                built["membership"],
                "a branch that also exists as a remote ref must not exclude itself",
            )

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertIn(mine, {c["sha"] for c in out["commits"]})

    def test_remote_only_branch_resolves(self):
        """The 092 shape: work pushed to a branch this checkout has no local
        copy of."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: remote-only work")
            repo.publish(name)
            repo.checkout("main")
            repo.delete_branch(name)

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertIn(
                mine,
                {c["sha"] for c in out["commits"]},
                "unmerged work on a remote branch is the case this issue exists for",
            )

    def test_base_history_still_excluded_with_a_remote(self):
        """Fixing self-exclusion must not reopen the over-collection defect."""
        with GitRepo() as repo:
            base = repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: branch work")
            repo.publish(name)
            repo.checkout("main")

            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertNotIn(base, {c["sha"] for c in out["commits"]})


class TestNoPerCommitProbe(unittest.TestCase):
    """Issue 095 review, finding 2: the degraded probe reintroduced the
    per-commit fan-out that task A2 removed."""

    def test_resolving_unmatched_commits_issues_no_branch_contains(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            for index in range(5):
                repo.commit(f"chore: unrelated {index}")

            index = cr.build_attribution(repo.runner, repo.path)
            repo.call_count = 0
            calls_before = len(repo.call_log)
            for sha in repo.log_shas():
                cr.resolve_issue_for_commit(
                    repo.runner, repo.path, sha, attribution=index["attribution"]
                )
            issued = repo.call_log[calls_before:]
            contains = [c for c in issued if c[:3] == ["git", "branch", "--contains"]]
            self.assertEqual(
                contains, [], "no per-commit branch probe may return (GC4)"
            )

    def test_supplied_index_answers_without_asking_git(self):
        """F12: the index already holds every source, trailer included. Asking
        git again per commit was measured at 65 redundant `git show -s` calls,
        1.7s, on a 65-commit range."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            for index_n in range(4):
                repo.commit(f"feat: step {index_n}", issue=ISSUE)

            index = cr.build_attribution(repo.runner, repo.path)
            attributed = [s for s in repo.log_shas() if s in index["attribution"]]
            self.assertTrue(attributed, "fixture should attribute something")

            before = len(repo.call_log)
            for sha in attributed:
                cr.resolve_issue_for_commit(
                    repo.runner, repo.path, sha, attribution=index["attribution"]
                )
            issued = repo.call_log[before:]
            self.assertEqual(
                issued, [], f"an attributed commit must answer from the index: {issued}"
            )

            # A commit absent from the index still costs one lookup: absence
            # cannot distinguish "belongs to no issue" from "outside the range
            # the index was built over". That is correct, and it is not the
            # fan-out — the measured case is behavior commits, which are
            # attributed.


class TestUnregisteredIssueIds(unittest.TestCase):
    """Naming a branch is not the same as having an issue.

    `issue_id_from_branch` used to return the branch tail when no registered
    issue matched, so a behavior commit on `codex/999-not-a-real-issue`
    satisfied the linkage gate — `ok: True, unlinked: 0` — while linking to
    nothing that exists. Found by the commit-direction oracle, which enumerates
    registered issues and so could not see the phantom id."""

    def test_branch_naming_an_unregistered_issue_resolves_to_nothing(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch("codex/999-not-a-real-issue")
            sha = repo.commit("feat: work under a phantom issue")

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])

    def test_linkage_gate_flags_a_phantom_branch(self):
        from scripts import linkage_check

        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            base = repo.head()
            repo.branch("codex/999-not-a-real-issue")
            (repo.path / "scripts").mkdir(exist_ok=True)
            repo.commit("feat: behavior change", filename="scripts/thing.py")

            out = linkage_check.find_unlinked_behavior_commits(
                repo.runner, repo.path, base, repo.head()
            )
            self.assertFalse(out["ok"], "a phantom issue id must not pass the gate")
            self.assertEqual(len(out["unlinked"]), 1)

    def test_registered_issue_still_resolves(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            sha = repo.commit("feat: real work")

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)

    def test_empty_registry_rejects_an_unknown_branch(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.branch("codex/321-no-issues-tracked")
            sha = repo.commit("feat: work")

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])

    def test_empty_registry_rejects_an_unknown_trailer(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            sha = repo.commit(
                "feat: work",
                issue="321-no-issues-tracked",
            )

            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])

    def test_empty_registry_rejects_an_unknown_merge_subject(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            name = repo.branch("codex/321-no-issues-tracked")
            work = repo.commit("feat: work")
            repo.checkout("main")
            merge = repo.merge(
                name,
                message="Merge branch 'codex/321-no-issues-tracked'",
            )

            index = cr.build_attribution(repo.runner, repo.path)
            self.assertNotIn(work, index["attribution"])
            self.assertNotIn(merge, index["attribution"])


class TestHistoricalIssueRegistry(unittest.TestCase):
    def test_issue_on_another_checkout_is_registered(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.branch("registry")
            repo.add_issue_file(ISSUE)
            repo.checkout("main")
            self.assertFalse((repo.path / "issues" / f"{ISSUE}.md").exists())

            errors = []
            self.assertIn(ISSUE, cr.known_issue_ids(repo.runner, repo.path, errors))
            self.assertEqual(errors, [])

    def test_deleted_issue_file_remains_registered_from_history(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo._git("rm", f"issues/{ISSUE}.md")
            repo._git("commit", "-q", "-m", f"chore: archive {ISSUE}")

            errors = []
            self.assertIn(ISSUE, cr.known_issue_ids(repo.runner, repo.path, errors))
            self.assertEqual(errors, [])

    def test_empty_repository_has_a_valid_empty_registry(self):
        with GitRepo() as repo:
            errors = []
            self.assertEqual(cr.known_issue_ids(repo.runner, repo.path, errors), [])
            self.assertEqual(errors, [])

    def test_registry_ids_are_sorted_and_deduplicated(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(OTHER)
            repo.add_issue_file(ISSUE)
            issue_path = repo.path / "issues" / f"{OTHER}.md"
            issue_path.write_text("# Updated issue\n")
            repo._git("add", str(issue_path))
            repo._git("commit", "-q", "-m", f"docs: update {OTHER}")

            errors = []
            self.assertEqual(
                cr.known_issue_ids(repo.runner, repo.path, errors),
                [OTHER, ISSUE],
            )
            self.assertEqual(errors, [])


class TestGraphQueryFailures(unittest.TestCase):
    ORIGIN_HEAD_ARGS = [
        "git",
        "symbolic-ref",
        "--quiet",
        "--short",
        "refs/remotes/origin/HEAD",
    ]

    @staticmethod
    def _failed_result(message, returncode=128):
        class Result:
            stdout = ""
            stderr = message

        Result.returncode = returncode
        return Result()

    def _repo_with_live_issue_branch(self):
        repo = GitRepo()
        repo.commit("chore: base")
        repo.add_issue_file(ISSUE)
        repo.branch(f"codex/{ISSUE}")
        work = repo.commit("feat: branch work")
        repo.checkout("main")
        return repo, work

    def test_rev_list_failure_surfaces_and_does_not_attribute(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            def failing(args, cwd=None):
                if args[:2] == ["git", "rev-list"]:
                    return self._failed_result("fatal: graph unavailable")
                return repo.runner(args, cwd)

            index = cr.build_attribution(failing, repo.path)

            self.assertNotIn(work, index["attribution"])
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, index["degraded"])
            self.assertTrue(
                any("rev-list" in error and "graph unavailable" in error
                    for error in index["errors"])
            )
        finally:
            repo.__exit__()

    def test_merge_base_failure_surfaces_and_does_not_attribute(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            def failing(args, cwd=None):
                if args[:3] == ["git", "merge-base", "--all"]:
                    return self._failed_result("fatal: corrupt commit graph")
                return repo.runner(args, cwd)

            index = cr.build_attribution(failing, repo.path)

            self.assertNotIn(work, index["attribution"])
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, index["degraded"])
            self.assertTrue(
                any("merge-base" in error and "corrupt commit graph" in error
                    for error in index["errors"])
            )
        finally:
            repo.__exit__()

    def test_topic_delta_rejects_a_terminated_merge_base_query(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            def terminated(args, cwd=None):
                if args[:3] == ["git", "merge-base", "--all"]:
                    return self._failed_result(
                        "terminated by signal",
                        returncode=-15,
                    )
                return repo.runner(args, cwd)

            index = cr.build_attribution(terminated, repo.path)

            self.assertNotIn(work, index["attribution"])
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, index["degraded"])
            self.assertTrue(
                any("merge-base" in error and "terminated by signal" in error
                    for error in index["errors"])
            )
        finally:
            repo.__exit__()

    def test_live_membership_does_not_call_origin_head(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            calls = []

            def terminated(args, cwd=None):
                calls.append(args)
                return repo.runner(args, cwd)

            index = cr.build_attribution(terminated, repo.path)

            self.assertNotIn(self.ORIGIN_HEAD_ARGS, calls)
            self.assertIn(work, index["attribution"])
            self.assertEqual(index["errors"], [])
            self.assertEqual(index["degraded"], [])
        finally:
            repo.__exit__()

    def test_live_membership_does_not_need_origin_head_fallback(self):
        repo, work = self._repo_with_live_issue_branch()
        try:
            calls = []

            def missing(args, cwd=None):
                calls.append(args)
                return repo.runner(args, cwd)

            index = cr.build_attribution(missing, repo.path)

            self.assertNotIn(self.ORIGIN_HEAD_ARGS, calls)
            self.assertIn(work, index["attribution"])
            self.assertEqual(index["errors"], [])
            self.assertEqual(index["degraded"], [])
        finally:
            repo.__exit__()

    def test_branch_membership_rejects_a_terminated_merge_base_query(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.add_issue_file(OTHER)
            repo.branch(f"codex/{ISSUE}")
            issue_work = repo.commit("feat: issue work")
            repo.checkout("main")
            repo.branch(f"codex/{OTHER}")
            other_work = repo.commit("feat: other work")
            repo.checkout("main")

            def terminated(args, cwd=None):
                if args[:3] == ["git", "merge-base", "--all"]:
                    return self._failed_result(
                        "terminated by signal",
                        returncode=-15,
                    )
                return repo.runner(args, cwd)

            built = cr.build_branch_membership(terminated, repo.path)

            self.assertNotIn(issue_work, built["membership"])
            self.assertNotIn(other_work, built["membership"])
            self.assertIn(cr.DEGRADED_BRANCH_UNAVAILABLE, built["degraded"])
            self.assertTrue(
                any("merge-base" in error and "terminated by signal" in error
                    for error in built["errors"])
            )

    def test_merge_base_rc_one_means_not_ancestor_not_error(self):
        repo, _ = self._repo_with_live_issue_branch()
        try:
            def not_ancestor(args, cwd=None):
                if args[:3] == ["git", "merge-base", "--is-ancestor"]:
                    return type(
                        "Result",
                        (),
                        {"returncode": 1, "stdout": "", "stderr": ""},
                    )()
                return repo.runner(args, cwd)

            index = cr.build_attribution(not_ancestor, repo.path)

            self.assertFalse(
                any("merge-base" in error for error in index["errors"])
            )
        finally:
            repo.__exit__()


class TestDegradedMeaning(unittest.TestCase):
    """F3: the flag must mean branch evidence could not be consulted, not
    that the repository's refs happen to be arranged a certain way.

    It used to fire whenever no issue-shaped branch existed — true of most
    healthy repositories, where every merged branch still resolves through
    merge topology — and stayed silent in cases where attribution really was
    impossible."""

    def test_healthy_repo_with_issue_branches_is_not_degraded(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: work")
            repo.checkout("main")
            self.assertEqual(cr.build_attribution(repo.runner, repo.path)["degraded"], [])

    def test_healthy_repo_without_issue_branches_is_not_degraded(self):
        """Nothing was unavailable — there are simply no issue branches."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.commit("feat: work", issue=ISSUE)
            self.assertEqual(cr.build_attribution(repo.runner, repo.path)["degraded"], [])

    def test_issue_branch_with_no_base_is_degraded(self):
        """Evidence exists and cannot be read: the case the flag is for."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: work")
            repo._git("branch", "-q", "-D", "main")

            self.assertIn(
                cr.DEGRADED_BRANCH_UNAVAILABLE,
                cr.build_attribution(repo.runner, repo.path)["degraded"],
            )

    def test_detached_commits_reach_the_index(self):
        """Once the log covers `--all`, a detached commit is visible and its
        lack of a branch is a fact about it, not a degradation."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            repo.commit("feat: on branch")
            repo.checkout("main")
            repo.detach()
            detached = repo.commit("feat: detached work")

            index = cr.build_attribution(repo.runner, repo.path)
            self.assertIn(detached, index["records"])
            self.assertEqual(index["degraded"], [])


class TestRangeProjection(unittest.TestCase):
    def test_live_range_projects_only_target_topic(self):
        """FH-031: full topology resolves a range without truncating graph data."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.add_issue_file(OTHER)
            alpha = repo.branch(f"codex/{ISSUE}")
            a_work = repo.commit("feat: alpha")
            repo.checkout("main")
            beta = repo.branch(f"codex/{OTHER}")
            b_work = repo.commit("feat: beta")

            result = cr.resolve_commits_for_issue(
                repo.runner, repo.path, OTHER, rev_range=f"{a_work}..{b_work}"
            )

            self.assertEqual({item["sha"] for item in result["commits"]}, {b_work})
            self.assertEqual(result["errors"], [])

    def test_range_projection_failure_returns_no_full_topology_attribution(self):
        """FH-031: a failed range query never falls back to the --all index."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            work = repo.commit("feat: issue")
            range_args = ["git", "log", "--format=%H", f"{work}^..{work}"]

            def failing(args, cwd=None):
                if args == range_args:
                    return TestGraphQueryFailures._failed_result("range unavailable")
                return repo.runner(args, cwd)

            result = cr.resolve_commits_for_issue(failing, repo.path, ISSUE, rev_range=f"{work}^..{work}")
            self.assertEqual(result["commits"], [])
            self.assertTrue(any("range unavailable" in error for error in result["errors"]))

    def test_terminated_range_projection_returns_no_attribution(self):
        """FH-031: a signal-terminated range query is observable and closed."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            work = repo.commit("feat: issue")
            range_args = ["git", "log", "--format=%H", f"{work}^..{work}"]

            def terminated(args, cwd=None):
                if args == range_args:
                    return TestGraphQueryFailures._failed_result("", returncode=-15)
                return repo.runner(args, cwd)

            result = cr.resolve_commits_for_issue(terminated, repo.path, ISSUE, rev_range=f"{work}^..{work}")
            self.assertEqual(result["commits"], [])
            self.assertTrue(any("exit code -15" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
