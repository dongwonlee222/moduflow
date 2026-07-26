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


if __name__ == "__main__":
    unittest.main()
