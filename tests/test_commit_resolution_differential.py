#!/usr/bin/env python3
"""The shipped resolver against ground truth declared by the fixtures.

Issue 095 was reviewed three times and each round found defects the tests could
not have caught, because the tests were written from the same understanding of
git that produced the bugs. Round 4 tried to break that loop with a reference
oracle — a slow, plain resolver that re-derived the answer from the repository.
It did not work, and rounds 5, 7 and 8 each measured why: the oracle asked git
the same questions the implementation asked, so it shared the blind spot. Its
`origin/HEAD` layer, the one round 7 called independent, executed in 0 of 15
shapes, and its scoring fallback returned the same wrong base ref as the
implementation on every base-ref defect.

The oracle is gone. The fixture *built* this history, so it knows the answer
without deriving anything, and it says so in `commit_resolution_shapes` as a
literal. A literal cannot share a blind spot with the code it checks.

When one of these fails, read the shape's `belongs_to=` declarations. If a
declaration is wrong, fix it and say why; otherwise the implementation is.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import commit_resolution as cr  # noqa: E402
import commit_resolution_shapes as shapes  # noqa: E402
from git_repo_builder import UNDECLARED, GitRepo  # noqa: E402


def _short(shas):
    return sorted(s[:8] for s in shas)


def _built_issue_ids(repo, returned):
    """Every issue id the shape *builds*, not the list it returns.

    Round 8: differential coverage was bounded by the returned list, which hid
    an oracle self-contradiction on an id no shape reported. Deriving the sweep
    from the declarations makes the coverage structural — a shape cannot build
    work for an issue and leave it unchecked."""
    ids = set(returned)
    for declared in repo.truth.values():
        if declared is not UNDECLARED:
            ids.update(declared)
    return sorted(ids)


class _ShapeCase(unittest.TestCase):
    def _build(self, shape_name):
        builder = shapes.ALL_SHAPES[shape_name]
        repo = GitRepo(**shapes.REPO_KWARGS.get(shape_name, {}))
        returned = builder(repo)
        return repo, returned


class DeclarationCoverageTests(_ShapeCase):
    """Every commit a shape builds must carry a declaration. Without this a
    shape added next month declares nothing and silently tests nothing."""

    def _check(self, shape_name):
        repo, _ = self._build(shape_name)
        with repo:
            self.assertEqual(
                _short(repo.undeclared()),
                [],
                f"\nshape {shape_name}: commits built with no belongs_to=. "
                "Declare the issue ids, or None for 'belongs to no issue'.",
            )
            actual = set(repo._git("rev-list", "--all").split())
            self.assertEqual(
                _short(actual - set(repo.truth)),
                [],
                f"\nshape {shape_name}: commits exist that the fixture never "
                "recorded — a raw _git call needs repo.record(sha, ...).",
            )


class GroundTruthTests(_ShapeCase):
    """issue -> commits, against the declaration."""

    def _check(self, shape_name):
        repo, returned = self._build(shape_name)
        with repo:
            for issue_id in _built_issue_ids(repo, returned):
                expected = repo.truth_for(issue_id)
                actual = {
                    c["sha"]
                    for c in cr.resolve_commits_for_issue(
                        repo.runner, repo.path, issue_id
                    )["commits"]
                }
                self.assertEqual(
                    actual,
                    expected,
                    f"\nshape:   {shape_name}"
                    f"\nissue:   {issue_id}"
                    f"\nextra:   {_short(actual - expected)}"
                    f"\nmissing: {_short(expected - actual)}",
                )
            if shape_name == "disconnected_non_issue_base":
                built = cr.build_attribution(repo.runner, repo.path)
                self.assertIn(
                    cr.DEGRADED_BRANCH_UNAVAILABLE,
                    built["degraded"],
                    "a disconnected non-issue ref is not a usable base",
                )
            if shape_name == "octopus_mapping_ambiguous":
                built = cr.build_attribution(repo.runner, repo.path)
                self.assertIn(
                    cr.DEGRADED_BRANCH_UNAVAILABLE,
                    built["degraded"],
                )
                self.assertTrue(
                    any("octopus" in error for error in built["errors"]),
                    built["errors"],
                )
            if shape_name == "two_parent_multi_name_ambiguous":
                built = cr.build_attribution(repo.runner, repo.path)
                self.assertIn(
                    cr.DEGRADED_BRANCH_UNAVAILABLE,
                    built["degraded"],
                )
                self.assertTrue(
                    any("merge" in error for error in built["errors"]),
                    built["errors"],
                )
            if shape_name in {
                "ambiguous_same_tail_remotes",
                "local_with_ambiguous_same_tail_remotes",
            }:
                built = cr.build_attribution(repo.runner, repo.path)
                self.assertIn(
                    cr.DEGRADED_BRANCH_UNAVAILABLE,
                    built["degraded"],
                )
                self.assertTrue(
                    any("remote" in error for error in built["errors"]),
                    built["errors"],
                )


class CommitDirectionTests(_ShapeCase):
    """commit -> issue, the other half of AC1.

    The test deleted at e8e4977 compared `build_attribution` to itself and
    passed under six mutations, including converge returning nothing. This one
    holds the implementation to the declaration."""

    def _check(self, shape_name):
        from scripts import linkage_check

        repo, _ = self._build(shape_name)
        with repo:
            index = cr.build_attribution(repo.runner, repo.path)["attribution"]
            for sha in repo.truth:
                expected = repo.truth[sha]
                # Both call shapes. Without an index the trailer short-circuits
                # and returns before `SOURCE_PRECEDENCE` is consulted; with one,
                # the constant decides. Precedence is stated twice, so reversing
                # the constant changed only half the callers and the mutation
                # survived. Checking one path is checking one of two rules.
                bare = linkage_check.resolve_issue_for_commit(
                    repo.runner, repo.path, sha
                )["issue_id"]
                indexed = linkage_check.resolve_issue_for_commit(
                    repo.runner, repo.path, sha, attribution=index
                )["issue_id"]

                self.assertEqual(
                    bare,
                    indexed,
                    f"\nshape {shape_name}: {sha[:8]} resolves to {bare} without "
                    f"an attribution index and {indexed} with one — the caller's "
                    "call shape must not change the answer",
                )
                for label, resolved in (("bare", bare), ("indexed", indexed)):
                    if not expected:
                        self.assertIsNone(
                            resolved,
                            f"\nshape {shape_name} ({label}): {sha[:8]} belongs "
                            f"to no issue, but linkage_check named {resolved}",
                        )
                    else:
                        self.assertIn(
                            resolved,
                            expected,
                            f"\nshape {shape_name} ({label}): {sha[:8]} belongs "
                            f"to {sorted(expected)}, but linkage_check named "
                            f"{resolved}",
                        )

            if shape_name == "trailer_disagrees_with_branch":
                original = cr.SOURCE_PRECEDENCE
                try:
                    cr.SOURCE_PRECEDENCE = (
                        "branch",
                        "trailer",
                        "merge-subject",
                    )
                    alternate = cr.build_attribution(
                        repo.runner,
                        repo.path,
                    )["attribution"]
                    conflict = next(
                        sha
                        for sha, expected in repo.truth.items()
                        if expected == frozenset({shapes.BETA})
                    )
                    bare = linkage_check.resolve_issue_for_commit(
                        repo.runner,
                        repo.path,
                        conflict,
                    )["issue_id"]
                    indexed = linkage_check.resolve_issue_for_commit(
                        repo.runner,
                        repo.path,
                        conflict,
                        attribution=alternate,
                    )["issue_id"]
                    self.assertEqual(
                        bare,
                        indexed,
                        "bare and indexed resolution must consult the same "
                        "SOURCE_PRECEDENCE rule",
                    )
                    self.assertEqual(indexed, shapes.ALPHA)
                finally:
                    cr.SOURCE_PRECEDENCE = original


def _attach(cls, prefix):
    cls._prefix = prefix
    for name in shapes.ALL_SHAPES:
        def test(self, _name=name):
            self._check(_name)

        test.__name__ = f"{prefix}{name}"
        test.__doc__ = shapes.ALL_SHAPES[name].__doc__
        setattr(cls, test.__name__, test)


_attach(DeclarationCoverageTests, "test_declared_")
_attach(GroundTruthTests, "test_")
_attach(CommitDirectionTests, "test_commit_direction_")


class DeclarationSanityTests(unittest.TestCase):
    def test_some_shape_declares_real_work(self):
        """Guards the mechanism itself: if `belongs_to` stopped being recorded,
        every shape would assert emptiness against emptiness and pass."""
        total = 0
        for name in shapes.ALL_SHAPES:
            with GitRepo(**shapes.REPO_KWARGS.get(name, {})) as repo:
                shapes.ALL_SHAPES[name](repo)
                total += sum(
                    1
                    for ids in repo.truth.values()
                    if ids is not UNDECLARED and ids
                )
        self.assertGreater(total, 20, "ground truth is not being recorded")

    def test_no_reference_oracle_remains(self):
        """The oracle was deleted, not disabled. A reintroduced one would
        recreate the shared blind spot rounds 5, 7 and 8 each measured."""
        self.assertFalse(
            (Path(__file__).resolve().parent / "commit_resolution_reference.py").exists(),
            "the reference oracle is back; ground truth must stay declared",
        )


if __name__ == "__main__":
    unittest.main()
