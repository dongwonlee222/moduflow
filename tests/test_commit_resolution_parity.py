#!/usr/bin/env python3
"""Cross-module parity for commit-to-issue resolution (issue 095, task E1).

The defect this issue exists to fix was two modules answering one question with
different rules: `project_converge` collected 10 commits for issue 093 where
`linkage_check` resolved 53, and neither reported the gap. Both now delegate to
`commit_resolution`, so they cannot disagree — this file is the check that
keeps it that way.

These tests fail if either consumer reintroduces a private matching rule, or if
one gains a source the other does not. They run against real temporary git
repositories rather than stubs, so a divergence in git access strategy shows up
here too.
"""
import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts import linkage_check, project_converge  # noqa: E402
from git_repo_builder import GitRepo  # noqa: E402

ISSUE = "095-commit-issue-resolution-parity"
OTHER = "094-risk-based-security-and-quality-review-gate"


class CrossModuleParityTests(unittest.TestCase):
    def _both_directions(self, repo, issue_id=ISSUE):
        """Resolve issue_id's commits through each consumer independently."""
        from_converge = {
            c["sha"]
            for c in project_converge.resolve_commits(repo.runner, repo.path, issue_id)[
                "commits"
            ]
        }
        from_linkage = set()
        for sha in repo.log_shas():
            resolved = linkage_check.resolve_issue_for_commit(
                repo.runner, repo.path, sha
            )
            if resolved["issue_id"] == issue_id:
                from_linkage.add(sha)
        return from_converge, from_linkage

    def assertParity(self, repo, issue_id=ISSUE):
        converge, linkage = self._both_directions(repo, issue_id)
        self.assertEqual(
            converge,
            linkage,
            "project_converge and linkage_check resolved different commit sets\n"
            f"  only converge: {sorted(converge - linkage)}\n"
            f"  only linkage:  {sorted(linkage - converge)}",
        )
        return converge

    def test_trailer_only_history(self):
        with GitRepo() as repo:
            repo.commit("chore: unrelated")
            repo.add_issue_file(ISSUE)
            mine = repo.commit("feat: work", issue=ISSUE)
            self.assertEqual(self.assertParity(repo), {mine})

    def test_branch_only_history(self):
        """The exact shape converge could not see before this issue."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: no trailer anywhere")
            resolved = self.assertParity(repo)
            self.assertIn(mine, resolved)

    def test_mixed_history(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.add_issue_file(OTHER)
            repo.branch(f"codex/{ISSUE}")
            with_trailer = repo.commit("feat: a", issue=ISSUE)
            without = repo.commit("feat: b")
            resolved = self.assertParity(repo)
            self.assertIn(with_trailer, resolved)
            self.assertIn(without, resolved)

    def test_merged_branch_then_deleted(self):
        """Post-merge is the state most of this repo's history is in."""
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            name = repo.branch(f"codex/{ISSUE}")
            mine = repo.commit("feat: branch work")
            repo.checkout("main")
            merge = repo.merge(name, message=f"Merge branch 'codex/{ISSUE}'")
            repo.delete_branch(name)
            resolved = self.assertParity(repo)
            self.assertIn(mine, resolved)
            self.assertIn(merge, resolved)

    def test_commits_belonging_to_no_issue(self):
        with GitRepo() as repo:
            repo.commit("chore: one")
            repo.commit("chore: two")
            self.assertEqual(self.assertParity(repo), set())

    def test_other_issue_commits_are_not_claimed(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(ISSUE)
            repo.add_issue_file(OTHER)
            theirs = repo.commit("feat: theirs", issue=OTHER)
            mine = repo.commit("feat: mine", issue=ISSUE)

            self.assertEqual(self.assertParity(repo, ISSUE), {mine})
            self.assertEqual(self.assertParity(repo, OTHER), {theirs})


class SharedOwnershipTests(unittest.TestCase):
    """Neither consumer may carry its own copy of the matching rules (GC1)."""

    def test_consumers_delegate_rather_than_reimplement(self):
        for module in (linkage_check, project_converge):
            with self.subTest(module=module.__name__):
                self.assertTrue(
                    hasattr(module, "commit_resolution"),
                    f"{module.__name__} must delegate to commit_resolution",
                )

    def test_no_module_outside_the_resolver_owns_branch_grammar(self):
        """GC1. `hooks/on_stop.py` read `linkage_check.BRANCH_ISSUE_RE`
        directly, making three owners of the grammar — and it accepted a branch
        named for an issue that does not exist, the same bypass the linkage
        gate had."""
        for relpath in ("scripts/linkage_check.py", "scripts/project_converge.py",
                        "hooks/on_stop.py"):
            source = Path(relpath).read_text(encoding="utf-8")
            with self.subTest(module=relpath):
                self.assertNotIn(
                    "BRANCH_ISSUE_RE",
                    source,
                    f"{relpath} reads branch grammar outside commit_resolution",
                )

    def test_dead_resolution_helpers_are_gone(self):
        """Unreferenced copies of the old rules read as a live second rule set
        to the next person."""
        source = Path("scripts/linkage_check.py").read_text(encoding="utf-8")
        for name in ("_known_issue_ids", "_branch_names", "_issue_id_from_branch"):
            with self.subTest(helper=name):
                self.assertNotIn(f"def {name}(", source)

    def test_consumers_do_not_define_their_own_trailer_pattern(self):
        source = Path("scripts/project_converge.py").read_text(encoding="utf-8")
        self.assertNotIn(
            "Issue:\\s*",
            source,
            "project_converge reintroduced a private trailer pattern",
        )

    def test_live_resolution_has_no_global_base_election_or_origin_head_probe(self):
        """FH-030: live topics derive forks independently, without origin/HEAD."""
        source = Path("scripts/commit_resolution.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = {
            node.name for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        self.assertNotIn("base_ref", functions)
        self.assertNotIn("symbolic-ref", source)

    def test_coverage_facts_reach_the_converge_payload(self):
        """The per-issue half of the payload. The repo-wide counts cannot tell
        a reviewer whether *this* bundle is complete — they are identical for
        every issue — so the actionable part is which evidence carried it."""
        with GitRepo() as repo:
            repo.commit("chore: one")
            repo.commit("chore: two")
            repo.add_issue_file(ISSUE)
            repo.commit("feat: mine", issue=ISSUE)
            result = project_converge.resolve_commits(repo.runner, repo.path, ISSUE)
            self.assertEqual(result["coverage"]["sources"], {"trailer": 1})
            self.assertEqual(result["repo_unmatched_count"], 3)
            self.assertEqual(result["repo_examined_count"], 4)
            self.assertEqual(
                result["errors"], [], "coverage is descriptive, never an error"
            )



class HumanSurfaceTests(unittest.TestCase):
    """C1: the gap must be visible without opening the JSON."""

    def test_human_summary_reports_unmatched(self):
        evidence = {
            "issue_id": ISSUE,
            "generated": "2026-07-26",
            "commits": [{"sha": "a" * 40, "subject": "feat: x", "source": "trailer"}],
            "files": [],
            "acceptance_criteria": [],
            "global_constraints": [],
            "truncated": False,
            "no_evidence": False,
            "repo_unmatched_count": 43,
            "repo_examined_count": 44,
            "coverage": {
                "sources": {"trailer": 1},
                "branch_refs": ["codex/" + ISSUE],
                "base_ref_available": True,
            },
            "degraded": [],
            "errors": [],
        }

        summary = project_converge._human_summary(evidence, None)

        self.assertIn("43 of 44", summary)
        self.assertIn("same for every issue", summary)
        self.assertIn("coverage:", summary)
        self.assertIn("base ref available: yes", summary)

    def test_review_command_requires_reporting_the_gap(self):
        text = Path("commands/product-review.md").read_text(encoding="utf-8")
        self.assertIn("unmatched_count", text)


if __name__ == "__main__":
    unittest.main()
