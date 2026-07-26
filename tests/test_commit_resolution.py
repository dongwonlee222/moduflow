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
            repo.branch(f"codex/{OTHER}")
            sha = repo.commit("feat: trailer disagrees with branch", issue=ISSUE)
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")


class TestMergeSubjectResolution(unittest.TestCase):
    def test_merge_subject_resolves_after_branch_deleted(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
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
            repo.commit("feat: mine", issue=ISSUE)
            out = cr.resolve_commits_for_issue(repo.runner, repo.path, ISSUE)
            self.assertEqual(len(out["commits"]), 1)
            self.assertEqual(out["repo_unmatched_count"], 2)
            self.assertEqual(out["repo_examined_count"], 3)
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
            sha = repo.commit("feat: work", issue=ISSUE)
            repo.detach()
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertEqual(out["issue_id"], ISSUE)
            self.assertEqual(out["source"], "trailer")
            self.assertEqual(out["errors"], [], "degraded resolution must not raise")

    def test_branch_only_commit_reports_degraded_not_silent(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            sha = repo.commit("feat: no trailer")
            repo.checkout("main")
            repo.delete_branch(name)
            repo.detach()
            out = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            self.assertIsNone(out["issue_id"])
            self.assertIn(
                "branch-unavailable",
                out["degraded"],
                "a commit resolvable only by branch must say why it was not resolved",
            )


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
            self.assertEqual(out["repo_unmatched_count"], 1)

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


if __name__ == "__main__":
    unittest.main()
