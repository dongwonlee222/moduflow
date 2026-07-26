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
            self.assertEqual(out["unmatched_count"], 2)
            self.assertEqual(out["examined_count"], 3)
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


if __name__ == "__main__":
    unittest.main()
