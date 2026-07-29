import contextlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import linkage_check

sys.path.insert(0, str(Path(__file__).resolve().parent))
from git_repo_builder import GitRepo  # noqa: E402


HEAD_REF_ARGS = tuple(linkage_check.commit_resolution.HEAD_REF_ARGS)
BRANCH_REF_ARGS = tuple(linkage_check.commit_resolution.BRANCH_REF_ARGS)
ALPHA = "101-alpha"
BETA = "102-beta"


@contextlib.contextmanager
def ambiguous_release_repo(*, ambiguity_in_range):
    """FH-018: the same ambiguity, inside or outside the release range."""
    with GitRepo() as repo:
        repo.commit("chore: base", belongs_to=None)
        repo.add_issue_file(ALPHA)
        repo.add_issue_file(BETA)
        base = repo.head()

        first = repo.branch(f"codex/{ALPHA}")
        (repo.path / "scripts").mkdir()
        repo.commit(
            "feat: alpha",
            filename="scripts/alpha.py",
            belongs_to=ALPHA,
        )
        repo.checkout("main")
        second = repo.branch(f"codex/{BETA}")
        (repo.path / "scripts").mkdir(exist_ok=True)
        repo.commit(
            "feat: beta",
            filename="scripts/beta.py",
            belongs_to=BETA,
        )
        repo.checkout("main")
        repo._git(
            "merge",
            "-q",
            "--no-ff",
            "-m",
            f"Merge branches 'codex/{BETA}' and 'codex/{ALPHA}'",
            first,
            second,
        )
        repo.record(repo.head(), [ALPHA, BETA])
        repo.delete_branch(first)
        repo.delete_branch(second)

        if ambiguity_in_range:
            repo.release_base = base
        else:
            repo.release_base = repo.head()
            repo.commit(
                "fix: current linked change",
                issue=ALPHA,
                filename="scripts/current.py",
                belongs_to=ALPHA,
            )
        yield repo


class FakeRunner:
    def __init__(self, responses):
        # Snapshot state is explicitly attached unless a detached-head fixture
        # overrides this boundary.
        self.responses = {
            HEAD_REF_ARGS: "refs/heads/main\n",
            **responses,
        }
        self.calls = []

    def __call__(self, args, cwd, timeout=None):
        self.calls.append(tuple(args))
        key = tuple(args)
        if key not in self.responses:
            return linkage_check.CommandResult(1, "", f"unexpected command: {' '.join(args)}")
        value = self.responses[key]
        if isinstance(value, BaseException):
            raise value
        if isinstance(value, linkage_check.CommandResult):
            return value
        return linkage_check.CommandResult(0, value, "")


def attribution_stubs(entries, issue_files=()):
    """Stub the command set `commit_resolution.build_attribution` issues.

    `entries` maps sha -> (subject, parents, body). `issue_files` are tracked
    issue ids used for branch-name disambiguation.
    """
    log = "".join(
        f"{sha}\x00{subject}\x00{parents}\x00{body}\x01"
        for sha, (subject, parents, body) in entries.items()
    )
    stubs = {
        tuple(linkage_check.commit_resolution.GIT_LOG_ARGS): log,
        BRANCH_REF_ARGS: "",
        tuple(linkage_check.commit_resolution.ISSUE_HISTORY_ARGS): "".join(
            f"issues/{issue_id}.md\n" for issue_id in issue_files
        ),
    }
    return stubs


def branch_stubs(branch_name, shas, issue_files=()):
    """Stub for-each-ref plus the branch-exclusive rev-list for one branch."""
    return {
        BRANCH_REF_ARGS: (
            f"{branch_name}\n"
        ),
        (
            "git",
            "rev-list",
            branch_name,
            "--not",
            "--exclude=" + branch_name,
            "--branches",
            "--remotes",
        ): "".join(f"{sha}\n" for sha in shas),
        tuple(linkage_check.commit_resolution.ISSUE_HISTORY_ARGS): "".join(
            f"issues/{issue_id}.md\n" for issue_id in issue_files
        ),
    }


class ResolveIssueForCommitTests(unittest.TestCase):
    def test_trailer_resolution(self):
        """FH-021/FH-027: the direct consumer uses the shared snapshot contract."""
        issue_id = "074-sync-fetch-sandbox-handling"
        runner = FakeRunner(
            attribution_stubs(
                {
                    "abc123": (
                        "fix: handle sandboxed fetch",
                        "",
                        f"fix: handle sandboxed fetch\n\nIssue: {issue_id}\n",
                    ),
                },
                issue_files=(issue_id,),
            )
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "abc123")

        self.assertEqual(result["sha"], "abc123")
        self.assertEqual(result["issue_id"], issue_id)
        self.assertEqual(result["source"], "trailer")
        self.assertEqual(result["errors"], [])
        self.assertIn(
            tuple(linkage_check.commit_resolution.GIT_LOG_ARGS),
            runner.calls,
        )

    # Branch resolution is exercised against real temporary repositories
    # rather than stubbed command sequences. These three used to pin the exact
    # git commands the resolver issued, so every change to its access strategy
    # broke them for reasons unrelated to behavior — and a stub can only
    # reproduce the git the author imagined, which is what three review rounds
    # found to be the defect source.

    def test_branch_resolution(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file("074-sync-fetch-sandbox-handling")
            name = repo.branch("codex/074-sync-fetch-sandbox-handling")
            sha = repo.commit("fix: handle sandboxed fetch")
            repo.publish(name)
            repo.checkout("main")

            result = linkage_check.resolve_issue_for_commit(repo.runner, repo.path, sha)

            self.assertEqual(result["issue_id"], "074-sync-fetch-sandbox-handling")
            self.assertEqual(result["source"], "branch")
            self.assertEqual(result["errors"], [])

    def test_local_branch_resolution(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file("075-issue-less-context-capture")
            repo.branch("codex/075-issue-less-context-capture")
            sha = repo.commit("feat: promote")

            result = linkage_check.resolve_issue_for_commit(repo.runner, repo.path, sha)

            self.assertEqual(result["issue_id"], "075-issue-less-context-capture")
            self.assertEqual(result["source"], "branch")

    def test_branch_suffix_resolves_full_issue_id(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file("075-issue-less-context-capture")
            name = repo.branch("codex/075-issue-less-context-capture-gate")
            sha = repo.commit("feat: gate")
            repo.publish(name)
            repo.checkout("main")

            result = linkage_check.resolve_issue_for_commit(repo.runner, repo.path, sha)

            self.assertEqual(result["issue_id"], "075-issue-less-context-capture")
            self.assertEqual(result["source"], "branch")

    def test_trailer_beats_branch_on_conflict(self):
        """FH-027: precedence is exercised through the full attribution path."""
        trailer_issue = "070-spec-consistency-analyze"
        branch_issue = "074-sync-fetch-sandbox-handling"
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file(trailer_issue)
            repo.add_issue_file(branch_issue)
            repo.branch(f"codex/{branch_issue}")
            sha = repo.commit("fix: thing", issue=trailer_issue)

            result = linkage_check.resolve_issue_for_commit(
                repo.runner,
                repo.path,
                sha,
            )

        self.assertEqual(result["issue_id"], trailer_issue)
        self.assertEqual(result["source"], "trailer")

    def test_no_trailer_no_issue_branch_resolves_none(self):
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "abc123"): "chore: misc\n",
                tuple(linkage_check.commit_resolution.GIT_LOG_ARGS): "abc123\x00chore: misc\x00\x00chore: misc\n\x01",
                BRANCH_REF_ARGS: (
                    "refs/remotes/origin/main abc123\nrefs/heads/main abc123\n"
                ),
                tuple(linkage_check.commit_resolution.ISSUE_HISTORY_ARGS): "",
                ("git", "branch", "--contains", "abc123"): "* main\n",
            }
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "abc123")

        self.assertIsNone(result["issue_id"])
        self.assertIsNone(result["source"])
        self.assertEqual(result["errors"], [])

    def test_snapshot_failure_surfaces_structured_fatal_error(self):
        """FH-010/FH-027: fatal graph failure survives SHA projection."""
        runner = FakeRunner(
            {
                tuple(linkage_check.commit_resolution.GIT_LOG_ARGS): (
                    linkage_check.CommandResult(
                        128,
                        "",
                        "fatal: snapshot unavailable",
                    )
                ),
                BRANCH_REF_ARGS: "",
            }
        )

        result = linkage_check.commit_resolution.resolve_issue_for_commit(
            runner,
            Path("."),
            "deadbeef",
        )

        self.assertIsNone(result["issue_id"])
        self.assertIsNone(result["source"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("fatal: snapshot unavailable", result["errors"][0])
        self.assertEqual(result["fatal_errors"], result["errors"])

    def test_branch_listing_failure_surfaces_error(self):
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "abc123"): "fix: thing\n",
                tuple(linkage_check.commit_resolution.GIT_LOG_ARGS): "abc123\x00fix: thing\x00\x00fix: thing\n\x01",
                tuple(linkage_check.commit_resolution.ISSUE_HISTORY_ARGS): "",
                BRANCH_REF_ARGS: linkage_check.CommandResult(
                    128, "", "fatal: malformed object name"
                ),
            }
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "abc123")

        self.assertIsNone(result["issue_id"])
        self.assertTrue(result["errors"])
        self.assertIn("malformed object name", result["errors"][0])


class ClassifyChangedPathsTests(unittest.TestCase):
    def test_behavior_prefixes_and_manifests(self):
        result = linkage_check.classify_changed_paths(
            [
                "scripts/linkage_check.py",
                "commands/product-promote.md",
                "skills/product-issue/SKILL.md",
                "templates/issues/issue.md",
                ".github/workflows/ci.yml",
                ".claude-plugin/plugin.json",
                ".codex-plugin/plugin.json",
            ]
        )

        self.assertEqual(len(result["behavior"]), 7)
        self.assertEqual(result["neutral"], [])

    def test_commands_md_is_behavior_not_docs(self):
        # Global Constraint 4.
        result = linkage_check.classify_changed_paths(["commands/product-release.md"])
        self.assertEqual(result["behavior"], ["commands/product-release.md"])

    def test_hooks_dir_is_behavior(self):
        # Issue 072: plugin hooks are executable surface, gated from day one.
        result = linkage_check.classify_changed_paths(["hooks/on_stop.py", "hooks/hooks.json"])
        self.assertEqual(result["behavior"], ["hooks/on_stop.py", "hooks/hooks.json"])
        self.assertEqual(result["neutral"], [])

    def test_neutral_paths(self):
        result = linkage_check.classify_changed_paths(
            [
                "README.md",
                "memory/decisions/2026-07-06-gate.md",
                "issues/075-issue-less-context-capture.md",
                "specs/075-issue-less-context-capture/plan.md",
                "releases/no-issue-declarations.md",
            ]
        )

        self.assertEqual(result["behavior"], [])
        self.assertEqual(len(result["neutral"]), 5)

    def test_lookalike_paths_are_neutral(self):
        # Prefix matching must not catch cousins outside the real directories.
        result = linkage_check.classify_changed_paths(
            ["docs/scripts/overview.md", "scripts.md", ".github/CODEOWNERS"]
        )

        self.assertEqual(result["behavior"], [])
        self.assertEqual(
            result["neutral"], ["docs/scripts/overview.md", "scripts.md", ".github/CODEOWNERS"]
        )

    def test_blank_entries_dropped(self):
        result = linkage_check.classify_changed_paths(["", "  ", "README.md"])
        self.assertEqual(result["behavior"], [])
        self.assertEqual(result["neutral"], ["README.md"])


class FindUnlinkedBehaviorCommitsTests(unittest.TestCase):
    def test_out_of_range_ambiguity_does_not_fail_release_linkage(self):
        """FH-018: diagnostics outside the behavior range stay out of errors."""
        with ambiguous_release_repo(ambiguity_in_range=False) as repo:
            result = linkage_check.find_unlinked_behavior_commits(
                repo.runner,
                repo.path,
                repo.release_base,
                repo.head(),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])

    def test_in_range_ambiguity_fails_closed(self):
        """FH-018: a diagnostic touching a release behavior SHA is fatal."""
        with ambiguous_release_repo(ambiguity_in_range=True) as repo:
            result = linkage_check.find_unlinked_behavior_commits(
                repo.runner,
                repo.path,
                repo.release_base,
                repo.head(),
            )

        self.assertFalse(result["ok"])
        self.assertTrue(result["errors"])

    def test_linked_behavior_commit_passes(self):
        runner = FakeRunner(
            {
                ("git", "rev-list", "base..head"): "sha1\n",
                tuple(linkage_check.commit_resolution.GIT_LOG_ARGS): "sha1\x00feat: foo\x00\x00feat: foo\n\nIssue: 070-spec-consistency-analyze\n\x01",
                BRANCH_REF_ARGS: "",
                tuple(linkage_check.commit_resolution.ISSUE_HISTORY_ARGS): (
                    "issues/070-spec-consistency-analyze.md\n"
                ),
                ("git", "show", "--name-only", "--format=", "sha1"): (
                    "scripts/foo.py\nREADME.md\n"
                ),
                ("git", "show", "-s", "--format=%B", "sha1"): (
                    "feat: foo\n\nIssue: 070-spec-consistency-analyze\n"
                ),
            }
        )

        result = linkage_check.find_unlinked_behavior_commits(runner, Path("."), "base", "head")

        self.assertTrue(result["ok"])
        self.assertEqual(result["unlinked"], [])
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            result["commits"],
            [
                {
                    "sha": "sha1",
                    "issue_id": "070-spec-consistency-analyze",
                    "source": "trailer",
                    "behavior_paths": ["scripts/foo.py"],
                }
            ],
        )

    def test_unlinked_behavior_commit_flagged(self):
        runner = FakeRunner(
            {
                ("git", "rev-list", "base..head"): "sha2\n",
                tuple(linkage_check.commit_resolution.GIT_LOG_ARGS): "sha2\x00docs tweak\x00\x00docs tweak\n\x01",
                BRANCH_REF_ARGS: "",
                tuple(linkage_check.commit_resolution.ISSUE_HISTORY_ARGS): "",
                ("git", "show", "--name-only", "--format=", "sha2"): "commands/product-x.md\n",
                ("git", "show", "-s", "--format=%B", "sha2"): "docs tweak\n",
                ("git", "branch", "--contains", "sha2"): "* main\n",
            }
        )

        result = linkage_check.find_unlinked_behavior_commits(runner, Path("."), "base", "head")

        self.assertFalse(result["ok"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["unlinked"]), 1)
        self.assertEqual(result["unlinked"][0]["sha"], "sha2")
        self.assertIsNone(result["unlinked"][0]["issue_id"])
        self.assertEqual(result["unlinked"][0]["behavior_paths"], ["commands/product-x.md"])

    def test_unknown_trailer_does_not_link_against_an_empty_registry(self):
        with GitRepo() as repo:
            base = repo.commit("chore: base")
            (repo.path / "scripts").mkdir()
            sha = repo.commit(
                "feat: behavior under a phantom issue",
                issue="321-no-issues-tracked",
                filename="scripts/thing.py",
            )

            result = linkage_check.find_unlinked_behavior_commits(
                repo.runner, repo.path, base, sha
            )

            self.assertFalse(result["ok"])
            self.assertEqual([entry["sha"] for entry in result["unlinked"]], [sha])
            self.assertIsNone(result["unlinked"][0]["issue_id"])

    def test_graph_failure_is_reported_and_branch_commit_stays_unlinked(self):
        with GitRepo() as repo:
            repo.commit("chore: base")
            repo.add_issue_file("074-sync-fetch-sandbox-handling")
            base = repo.head()
            repo.branch("codex/074-sync-fetch-sandbox-handling")
            (repo.path / "scripts").mkdir()
            sha = repo.commit(
                "feat: behavior change",
                filename="scripts/thing.py",
            )

            def failing(args, cwd=None, timeout=None):
                if args[:2] == ["git", "rev-list"] and ".." not in args[2]:
                    return linkage_check.CommandResult(
                        128, "", "fatal: graph unavailable"
                    )
                return repo.runner(args, cwd)

            result = linkage_check.find_unlinked_behavior_commits(
                failing, repo.path, base, sha
            )

            self.assertFalse(result["ok"])
            self.assertEqual([entry["sha"] for entry in result["unlinked"]], [sha])
            self.assertIsNone(result["unlinked"][0]["issue_id"])
            self.assertIn(
                linkage_check.commit_resolution.DEGRADED_BRANCH_UNAVAILABLE,
                result["degraded"],
            )
            self.assertTrue(
                any("rev-list" in error and "graph unavailable" in error
                    for error in result["errors"])
            )

    def test_neutral_only_commit_ignored(self):
        runner = FakeRunner(
            {
                ("git", "rev-list", "base..head"): "sha3\n",
                ("git", "show", "--name-only", "--format=", "sha3"): "README.md\nmemory/notes.md\n",
            }
        )

        result = linkage_check.find_unlinked_behavior_commits(runner, Path("."), "base", "head")

        self.assertTrue(result["ok"])
        self.assertEqual(result["commits"], [])
        self.assertEqual(result["unlinked"], [])
        # Neutral-only commits never trigger issue resolution.
        self.assertNotIn(("git", "show", "-s", "--format=%B", "sha3"), runner.calls)

    def test_mixed_range(self):
        runner = FakeRunner(
            {
                ("git", "rev-list", "base..head"): "sha1\nsha2\nsha3\n",
                tuple(linkage_check.commit_resolution.GIT_LOG_ARGS): (
                    "sha1\x00feat: foo\x00\x00"
                    "feat: foo\n\nIssue: 070-spec-consistency-analyze\n\x01"
                    "sha2\x00tweak\x00\x00tweak\n\x01"
                    "sha3\x00docs\x00\x00docs\n\x01"
                ),
                tuple(linkage_check.commit_resolution.ISSUE_HISTORY_ARGS): (
                    "issues/070-spec-consistency-analyze.md\n"
                ),
                BRANCH_REF_ARGS: "",
                ("git", "show", "--name-only", "--format=", "sha1"): "scripts/foo.py\n",
                ("git", "show", "-s", "--format=%B", "sha1"): (
                    "feat: foo\n\nIssue: 070-spec-consistency-analyze\n"
                ),
                ("git", "show", "--name-only", "--format=", "sha2"): "commands/product-x.md\n",
                ("git", "show", "-s", "--format=%B", "sha2"): "tweak\n",
                ("git", "branch", "--contains", "sha2"): "* main\n",
                ("git", "show", "--name-only", "--format=", "sha3"): "README.md\n",
            }
        )

        result = linkage_check.find_unlinked_behavior_commits(runner, Path("."), "base", "head")

        self.assertFalse(result["ok"])
        self.assertEqual(len(result["commits"]), 2)
        self.assertEqual([c["sha"] for c in result["unlinked"]], ["sha2"])

    def test_rev_list_failure_is_not_silent_pass(self):
        runner = FakeRunner(
            {
                ("git", "rev-list", "base..head"): linkage_check.CommandResult(
                    128, "", "fatal: bad revision 'base..head'"
                ),
            }
        )

        result = linkage_check.find_unlinked_behavior_commits(runner, Path("."), "base", "head")

        self.assertFalse(result["ok"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("bad revision", result["errors"][0])
        self.assertEqual(result["commits"], [])
        self.assertEqual(result["unlinked"], [])

    def test_show_failure_is_not_silent_pass(self):
        runner = FakeRunner(
            {
                ("git", "rev-list", "base..head"): "sha1\n",
                ("git", "show", "--name-only", "--format=", "sha1"): linkage_check.CommandResult(
                    128, "", "fatal: bad object sha1"
                ),
            }
        )

        result = linkage_check.find_unlinked_behavior_commits(runner, Path("."), "base", "head")

        self.assertFalse(result["ok"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("bad object sha1", result["errors"][0])

    def test_empty_range_is_ok(self):
        runner = FakeRunner({("git", "rev-list", "base..head"): ""})

        result = linkage_check.find_unlinked_behavior_commits(runner, Path("."), "base", "head")

        self.assertTrue(result["ok"])
        self.assertEqual(result["commits"], [])
        self.assertEqual(result["errors"], [])


BLAME_HUMAN = (
    "5d54310cabc0000000000000000000000000dead 12 12 1\n"
    "author Dongwon Lee\n"
    "author-mail <webn77@gmail.com>\n"
    "author-time 1751500000\n"
    "author-tz +0900\n"
    "committer Dongwon Lee\n"
    "committer-mail <webn77@gmail.com>\n"
    "summary docs: declare no-issue scope\n"
    "filename releases/no-issue-declarations.md\n"
    "\t2026-07-06 scripts/hotfix.py — emergency fix\n"
)

BLAME_AGENT = (
    "5d54310cabc0000000000000000000000000beef 12 12 1\n"
    "author Claude Fable 5\n"
    "author-mail <noreply@anthropic.com>\n"
    "author-time 1751500000\n"
    "author-tz +0900\n"
    "summary chore: agent edit\n"
    "filename releases/no-issue-declarations.md\n"
    "\t2026-07-06 scripts/hotfix.py — emergency fix\n"
)

BLAME_ARGS = (
    "git",
    "blame",
    "-L",
    "12,12",
    "--line-porcelain",
    "releases/no-issue-declarations.md",
)

HUMANS = [{"name": "Dongwon Lee", "email": "webn77@gmail.com"}]


class ValidateNoIssueDeclarationTests(unittest.TestCase):
    def test_human_identity_is_valid(self):
        runner = FakeRunner({BLAME_ARGS: BLAME_HUMAN})

        result = linkage_check.validate_no_issue_declaration(
            runner, Path("."), "releases/no-issue-declarations.md", 12, HUMANS
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["author_name"], "Dongwon Lee")
        self.assertEqual(result["author_email"], "webn77@gmail.com")
        self.assertIsNone(result["reason"])

    def test_email_only_match_is_valid(self):
        runner = FakeRunner({BLAME_ARGS: BLAME_HUMAN})

        result = linkage_check.validate_no_issue_declaration(
            runner,
            Path("."),
            "releases/no-issue-declarations.md",
            12,
            [{"name": "Different Display Name", "email": "webn77@gmail.com"}],
        )

        self.assertTrue(result["valid"])

    def test_agent_identity_is_invalid(self):
        runner = FakeRunner({BLAME_ARGS: BLAME_AGENT})

        result = linkage_check.validate_no_issue_declaration(
            runner, Path("."), "releases/no-issue-declarations.md", 12, HUMANS
        )

        self.assertFalse(result["valid"])
        self.assertEqual(result["author_name"], "Claude Fable 5")
        self.assertEqual(result["author_email"], "noreply@anthropic.com")
        self.assertIn("does not match", result["reason"])

    def test_empty_identity_list_never_passes(self):
        runner = FakeRunner({BLAME_ARGS: BLAME_HUMAN})

        result = linkage_check.validate_no_issue_declaration(
            runner, Path("."), "releases/no-issue-declarations.md", 12, []
        )

        self.assertFalse(result["valid"])
        self.assertIn("no configured human identities", result["reason"])

    def test_blame_failure_is_invalid_with_reason(self):
        runner = FakeRunner(
            {
                BLAME_ARGS: linkage_check.CommandResult(
                    128, "", "fatal: no such path 'releases/no-issue-declarations.md'"
                )
            }
        )

        result = linkage_check.validate_no_issue_declaration(
            runner, Path("."), "releases/no-issue-declarations.md", 12, HUMANS
        )

        self.assertFalse(result["valid"])
        self.assertIn("no such path", result["reason"])


class LoadHumanIdentitiesTests(unittest.TestCase):
    def test_missing_file_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(linkage_check.load_human_identities(tmp), [])

    def test_reads_list_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / ".moduflow"
            config_dir.mkdir()
            (config_dir / "humans.json").write_text(json.dumps(HUMANS), encoding="utf-8")

            self.assertEqual(linkage_check.load_human_identities(tmp), HUMANS)

    def test_reads_wrapped_humans_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / ".moduflow"
            config_dir.mkdir()
            (config_dir / "humans.json").write_text(
                json.dumps({"humans": HUMANS}), encoding="utf-8"
            )

            self.assertEqual(linkage_check.load_human_identities(tmp), HUMANS)

    def test_malformed_config_raises_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / ".moduflow"
            config_dir.mkdir()
            (config_dir / "humans.json").write_text('{"not": "a list"}', encoding="utf-8")

            with self.assertRaises(ValueError):
                linkage_check.load_human_identities(tmp)


if __name__ == "__main__":
    unittest.main()
