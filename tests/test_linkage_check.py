import json
import tempfile
import unittest
from pathlib import Path

from scripts import linkage_check


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses
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


class ResolveIssueForCommitTests(unittest.TestCase):
    def test_trailer_resolution(self):
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "abc123"): (
                    "fix: handle sandboxed fetch\n\nIssue: 074-sync-fetch-sandbox-handling\n"
                ),
            }
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "abc123")

        self.assertEqual(result["sha"], "abc123")
        self.assertEqual(result["issue_id"], "074-sync-fetch-sandbox-handling")
        self.assertEqual(result["source"], "trailer")
        self.assertEqual(result["errors"], [])
        # Trailer short-circuits: no branch lookups.
        self.assertNotIn(("git", "branch", "-r", "--contains", "abc123"), runner.calls)

    def test_branch_resolution(self):
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "abc123"): "fix: handle sandboxed fetch\n",
                ("git", "branch", "-r", "--contains", "abc123"): (
                    "  origin/codex/074-sync-fetch-sandbox-handling\n"
                ),
                ("git", "branch", "--contains", "abc123"): "",
                ("git", "ls-files", "issues"): "issues/074-sync-fetch-sandbox-handling.md\n",
            }
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "abc123")

        self.assertEqual(result["issue_id"], "074-sync-fetch-sandbox-handling")
        self.assertEqual(result["source"], "branch")
        self.assertEqual(result["errors"], [])

    def test_local_branch_resolution(self):
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "abc123"): "feat: promote\n",
                ("git", "branch", "-r", "--contains", "abc123"): "",
                ("git", "branch", "--contains", "abc123"): "* codex/075-issue-less-context-capture\n",
                ("git", "ls-files", "issues"): "issues/075-issue-less-context-capture.md\n",
            }
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "abc123")

        self.assertEqual(result["issue_id"], "075-issue-less-context-capture")
        self.assertEqual(result["source"], "branch")

    def test_branch_suffix_resolves_full_issue_id(self):
        # Global Constraint 7: codex/<issue-id>-<suffix> resolves the full id.
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "abc123"): "feat: gate\n",
                ("git", "branch", "-r", "--contains", "abc123"): (
                    "  origin/codex/075-issue-less-context-capture-gate\n"
                ),
                ("git", "branch", "--contains", "abc123"): "",
                ("git", "ls-files", "issues"): "issues/075-issue-less-context-capture.md\n",
            }
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "abc123")

        self.assertEqual(result["issue_id"], "075-issue-less-context-capture")
        self.assertEqual(result["source"], "branch")

    def test_trailer_beats_branch_on_conflict(self):
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "abc123"): (
                    "fix: thing\n\nIssue: 070-spec-consistency-analyze\n"
                ),
                # A conflicting branch exists but must not be consulted/win.
                ("git", "branch", "-r", "--contains", "abc123"): (
                    "  origin/codex/074-sync-fetch-sandbox-handling\n"
                ),
                ("git", "branch", "--contains", "abc123"): "",
                ("git", "ls-files", "issues"): (
                    "issues/070-spec-consistency-analyze.md\n"
                    "issues/074-sync-fetch-sandbox-handling.md\n"
                ),
            }
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "abc123")

        self.assertEqual(result["issue_id"], "070-spec-consistency-analyze")
        self.assertEqual(result["source"], "trailer")

    def test_no_trailer_no_issue_branch_resolves_none(self):
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "abc123"): "chore: misc\n",
                ("git", "branch", "-r", "--contains", "abc123"): "  origin/main\n",
                ("git", "branch", "--contains", "abc123"): "* main\n",
            }
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "abc123")

        self.assertIsNone(result["issue_id"])
        self.assertIsNone(result["source"])
        self.assertEqual(result["errors"], [])

    def test_git_show_failure_surfaces_error(self):
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "deadbeef"): linkage_check.CommandResult(
                    128, "", "fatal: bad object deadbeef"
                ),
            }
        )

        result = linkage_check.resolve_issue_for_commit(runner, Path("."), "deadbeef")

        self.assertIsNone(result["issue_id"])
        self.assertIsNone(result["source"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("fatal: bad object deadbeef", result["errors"][0])

    def test_branch_listing_failure_surfaces_error(self):
        runner = FakeRunner(
            {
                ("git", "show", "-s", "--format=%B", "abc123"): "fix: thing\n",
                ("git", "branch", "-r", "--contains", "abc123"): linkage_check.CommandResult(
                    128, "", "fatal: malformed object name"
                ),
                ("git", "branch", "--contains", "abc123"): "",
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
    def test_linked_behavior_commit_passes(self):
        runner = FakeRunner(
            {
                ("git", "rev-list", "base..head"): "sha1\n",
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
                ("git", "show", "--name-only", "--format=", "sha2"): "commands/product-x.md\n",
                ("git", "show", "-s", "--format=%B", "sha2"): "docs tweak\n",
                ("git", "branch", "-r", "--contains", "sha2"): "  origin/main\n",
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
                ("git", "show", "--name-only", "--format=", "sha1"): "scripts/foo.py\n",
                ("git", "show", "-s", "--format=%B", "sha1"): (
                    "feat: foo\n\nIssue: 070-spec-consistency-analyze\n"
                ),
                ("git", "show", "--name-only", "--format=", "sha2"): "commands/product-x.md\n",
                ("git", "show", "-s", "--format=%B", "sha2"): "tweak\n",
                ("git", "branch", "-r", "--contains", "sha2"): "  origin/main\n",
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
