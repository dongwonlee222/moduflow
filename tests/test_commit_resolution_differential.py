#!/usr/bin/env python3
"""Differential test: the shipped resolver against a slow reference oracle.

Issue 095 was reviewed three times and each round found defects the tests could
not have caught, because the tests were written from the same understanding of
git that produced the bugs. This file removes the author's understanding from
the loop: correctness is whatever `commit_resolution_reference` — which asks git
one plain question at a time — says it is, across every shape in
`commit_resolution_shapes`.

When one of these fails, the reference is the thing to check first. If the
reference is wrong, fix it and say why in its docstring; if it is right, the
shipped implementation is wrong.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import commit_resolution as cr  # noqa: E402
import commit_resolution_shapes as shapes  # noqa: E402
from commit_resolution_reference import reference_commits_for_issue  # noqa: E402
from git_repo_builder import GitRepo  # noqa: E402


class DifferentialTests(unittest.TestCase):
    def _check(self, shape_name):
        builder = shapes.ALL_SHAPES[shape_name]
        with GitRepo() as repo:
            issue_ids = builder(repo)
            for issue_id in issue_ids:
                expected = reference_commits_for_issue(repo.runner, repo.path, issue_id)
                actual = {
                    c["sha"]
                    for c in cr.resolve_commits_for_issue(
                        repo.runner, repo.path, issue_id
                    )["commits"]
                }
                short = lambda shas: sorted(s[:8] for s in shas)  # noqa: E731
                self.assertEqual(
                    actual,
                    expected,
                    f"\nshape:   {shape_name}"
                    f"\nissue:   {issue_id}"
                    f"\nextra:   {short(actual - expected)}"
                    f"\nmissing: {short(expected - actual)}",
                )


def _attach(name):
    def test(self):
        self._check(name)

    test.__name__ = f"test_{name}"
    test.__doc__ = shapes.ALL_SHAPES[name].__doc__
    setattr(DifferentialTests, test.__name__, test)


for _shape in shapes.ALL_SHAPES:
    _attach(_shape)



class ConsumerParityTests(unittest.TestCase):
    """Acceptance criterion 1, checked across every shape rather than in the
    fixtures the author happened to build.

    Round 3's F1 found the two consumers disagreeing on a commit outside the
    index window. The window is now `--all`, which is a superset of any range a
    caller can name, so the two should agree everywhere — this is where that is
    established rather than assumed."""

    def _check(self, shape_name):
        from scripts import linkage_check, project_converge

        builder = shapes.ALL_SHAPES[shape_name]
        with GitRepo() as repo:
            issue_ids = builder(repo)
            index = cr.build_attribution(repo.runner, repo.path)
            all_shas = set(index["order"])

            for issue_id in issue_ids:
                converge = {
                    c["sha"]
                    for c in project_converge.resolve_commits(
                        repo.runner, repo.path, issue_id
                    )["commits"]
                }
                for sha in all_shas:
                    resolved = linkage_check.resolve_issue_for_commit(
                        repo.runner, repo.path, sha
                    )
                    claimed = set((index["attribution"].get(sha) or {}))

                    if resolved["issue_id"] is not None:
                        self.assertIn(
                            resolved["issue_id"],
                            claimed,
                            f"\nshape {shape_name}: linkage_check named "
                            f"{resolved['issue_id']} for {sha[:8]}, which converge "
                            f"would not claim it for (claims: {sorted(claimed)})",
                        )
                    if sha in converge:
                        self.assertTrue(
                            claimed,
                            f"\nshape {shape_name}: converge collected {sha[:8]} for "
                            f"{issue_id} while linkage_check resolves it to nothing",
                        )


def _attach_consumer(name):
    def test(self):
        self._check(name)

    test.__name__ = f"test_consumers_agree_{name}"
    setattr(ConsumerParityTests, test.__name__, test)


for _shape in shapes.ALL_SHAPES:
    _attach_consumer(_shape)


if __name__ == "__main__":
    unittest.main()
