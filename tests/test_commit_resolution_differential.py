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
from commit_resolution_reference import (  # noqa: E402
    reference_commits_for_issue,
    reference_issues_for_commit,
)
from git_repo_builder import GitRepo  # noqa: E402


class DifferentialTests(unittest.TestCase):
    def _check(self, shape_name):
        builder = shapes.ALL_SHAPES[shape_name]
        with GitRepo(**shapes.REPO_KWARGS.get(shape_name, {})) as repo:
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


class CommitDirectionTests(unittest.TestCase):
    """The commit→issue half of AC1, against the oracle rather than against
    the implementation's own index.

    The test deleted at e8e4977 compared `build_attribution` to itself and
    passed under six mutations, including converge returning nothing. This one
    asks the oracle what a commit belongs to and holds the implementation to
    that answer."""

    def _check(self, shape_name):
        from scripts import linkage_check

        builder = shapes.ALL_SHAPES[shape_name]
        with GitRepo(**shapes.REPO_KWARGS.get(shape_name, {})) as repo:
            builder(repo)
            index = cr.build_attribution(repo.runner, repo.path)
            for sha in index["order"]:
                expected = reference_issues_for_commit(repo.runner, repo.path, sha)
                resolved = linkage_check.resolve_issue_for_commit(
                    repo.runner, repo.path, sha
                )["issue_id"]

                if not expected:
                    self.assertIsNone(
                        resolved,
                        f"\nshape {shape_name}: {sha[:8]} belongs to no issue, "
                        f"but linkage_check named {resolved}",
                    )
                else:
                    self.assertIn(
                        resolved,
                        expected,
                        f"\nshape {shape_name}: {sha[:8]} belongs to "
                        f"{sorted(expected)}, but linkage_check named {resolved}",
                    )


def _attach_commit_direction(name):
    def test(self):
        self._check(name)

    test.__name__ = f"test_commit_direction_{name}"
    setattr(CommitDirectionTests, test.__name__, test)


for _shape in shapes.ALL_SHAPES:
    _attach_commit_direction(_shape)


# The consumer-parity test that lived here is gone, deliberately.
#
# One was added at 81b943b and removed after the second independent review
# mutation-tested it: it passed when project_converge returned nothing (issue
# 095's founding defect), when linkage_check resolved every commit to None, and
# when either consumer reintroduced its pre-095 private rule — the exact
# condition the acceptance criterion says it must fail on. It compared
# `build_attribution` to itself, so both sides of every assertion came from one
# function and `if sha in converge: assertTrue(claimed)` was true by
# construction.
#
# A real one needs a reference for the commit->issue direction;
# `commit_resolution_reference` only implements issue->commits, so half of the
# criterion has no oracle. Writing that reference is the prerequisite, not the
# test. Until then this file covers one direction honestly rather than two
# dishonestly.
#
# Before adding any replacement: mutate the implementation and confirm the new
# test fails. A parity assertion between two views of the same index cannot.


if __name__ == "__main__":
    unittest.main()
