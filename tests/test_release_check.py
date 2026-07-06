import json
import tempfile
import unittest
from pathlib import Path

from scripts import linkage_check
from scripts import release_check


class FakeRunner:
    """FakeRunner pattern from tests/test_linkage_check.py.

    Values may be a str (stdout of a successful call), a CommandResult, or a
    list of either — list entries are consumed one per call so a command can
    fail first and succeed later (shallow-clone fetch recovery)."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, args, cwd, timeout=None):
        self.calls.append(tuple(args))
        key = tuple(args)
        if key not in self.responses:
            return linkage_check.CommandResult(1, "", f"unexpected command: {' '.join(args)}")
        value = self.responses[key]
        if isinstance(value, list):
            value = value.pop(0) if len(value) > 1 else value[0]
        if isinstance(value, linkage_check.CommandResult):
            return value
        return linkage_check.CommandResult(0, value, "")


MERGE_BASE_ARGS = ("git", "merge-base", "HEAD", "origin/main")
FETCH_ARGS = ("git", "fetch", "origin", "main", "--depth=200")

HUMANS = [{"name": "Dongwon Lee", "email": "webn77@gmail.com"}]

BLAME_HUMAN = (
    "5d54310cabc0000000000000000000000000dead 3 3 1\n"
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
    "5d54310cabc0000000000000000000000000beef 3 3 1\n"
    "author Claude Fable 5\n"
    "author-mail <noreply@anthropic.com>\n"
    "author-time 1751500000\n"
    "author-tz +0900\n"
    "summary chore: agent edit\n"
    "filename releases/no-issue-declarations.md\n"
    "\t2026-07-06 scripts/hotfix.py — emergency fix\n"
)


def unlinked_commit_responses(sha="badc0ffee", path="scripts/hotfix.py"):
    """Responses for one behavior commit with no trailer and no issue branch."""
    return {
        MERGE_BASE_ARGS: "mbsha\n",
        ("git", "rev-list", "mbsha..HEAD"): f"{sha}\n",
        ("git", "show", "--name-only", "--format=", sha): f"{path}\n",
        ("git", "show", "-s", "--format=%B", sha): "hotfix without issue\n",
        ("git", "branch", "-r", "--contains", sha): "  origin/main\n",
        ("git", "branch", "--contains", sha): "* main\n",
    }


def write_declaration_project(root, declaration_line, humans=HUMANS):
    releases = root / "releases"
    releases.mkdir()
    (releases / "no-issue-declarations.md").write_text(
        f"# No-Issue Declarations\n\n{declaration_line}\n", encoding="utf-8"
    )
    moduflow = root / ".moduflow"
    moduflow.mkdir()
    (moduflow / "humans.json").write_text(json.dumps(humans), encoding="utf-8")


DECLARATION_BLAME_ARGS = (
    "git",
    "blame",
    "-L",
    "3,3",
    "--line-porcelain",
    "releases/no-issue-declarations.md",
)


class LinkageGateTests(unittest.TestCase):
    def test_linked_behavior_commits_pass(self):
        runner = FakeRunner(
            {
                MERGE_BASE_ARGS: "mbsha\n",
                ("git", "rev-list", "mbsha..HEAD"): "sha1\n",
                ("git", "show", "--name-only", "--format=", "sha1"): (
                    "scripts/foo.py\nREADME.md\n"
                ),
                ("git", "show", "-s", "--format=%B", "sha1"): (
                    "feat: foo\n\nIssue: 075-issue-less-context-capture\n"
                ),
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = release_check.run_linkage_gate(Path(tmp), runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["merge_base"], "mbsha")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["unlinked"], [])
        self.assertEqual(result["uncovered"], [])

    def test_neutral_only_range_passes_without_declarations_file(self):
        # Missing releases/no-issue-declarations.md is fine when nothing is unlinked.
        runner = FakeRunner(
            {
                MERGE_BASE_ARGS: "mbsha\n",
                ("git", "rev-list", "mbsha..HEAD"): "sha1\n",
                ("git", "show", "--name-only", "--format=", "sha1"): "docs/notes.md\n",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = release_check.run_linkage_gate(Path(tmp), runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])

    def test_unlinked_behavior_commit_fails_with_sha_and_paths(self):
        runner = FakeRunner(unlinked_commit_responses())
        with tempfile.TemporaryDirectory() as tmp:
            result = release_check.run_linkage_gate(Path(tmp), runner)

        self.assertFalse(result["ok"])
        self.assertEqual(len(result["uncovered"]), 1)
        self.assertEqual(result["uncovered"][0]["sha"], "badc0ffee")
        joined = "\n".join(result["errors"])
        self.assertIn("badc0ffee", joined)
        self.assertIn("scripts/hotfix.py", joined)

    def test_unlinked_commit_with_valid_human_declaration_passes(self):
        responses = unlinked_commit_responses()
        responses[DECLARATION_BLAME_ARGS] = BLAME_HUMAN
        runner = FakeRunner(responses)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_declaration_project(root, "2026-07-06 scripts/hotfix.py — emergency fix")

            result = release_check.run_linkage_gate(root, runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["uncovered"], [])
        # The unlinked commit is still reported, only its coverage passes.
        self.assertEqual(len(result["unlinked"]), 1)

    def test_unlinked_commit_with_agent_authored_declaration_fails(self):
        responses = unlinked_commit_responses()
        responses[DECLARATION_BLAME_ARGS] = BLAME_AGENT
        runner = FakeRunner(responses)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_declaration_project(root, "2026-07-06 scripts/hotfix.py — emergency fix")

            result = release_check.run_linkage_gate(root, runner)

        self.assertFalse(result["ok"])
        self.assertEqual(len(result["uncovered"]), 1)
        self.assertEqual(result["uncovered"][0]["sha"], "badc0ffee")
        self.assertEqual(len(result["invalid_declarations"]), 1)
        joined = "\n".join(result["errors"])
        self.assertIn("badc0ffee", joined)
        self.assertIn("does not match", joined)

    def test_declaration_without_human_identities_never_passes(self):
        responses = unlinked_commit_responses()
        responses[DECLARATION_BLAME_ARGS] = BLAME_HUMAN
        runner = FakeRunner(responses)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "releases").mkdir()
            (root / "releases" / "no-issue-declarations.md").write_text(
                "# No-Issue Declarations\n\n2026-07-06 scripts/hotfix.py — emergency fix\n",
                encoding="utf-8",
            )
            # No .moduflow/humans.json: zero identities, declaration must not validate.
            result = release_check.run_linkage_gate(root, runner)

        self.assertFalse(result["ok"])
        self.assertEqual(len(result["uncovered"]), 1)

    def test_merge_base_failure_is_error_not_pass(self):
        failure = linkage_check.CommandResult(128, "", "fatal: no merge base")
        runner = FakeRunner(
            {
                MERGE_BASE_ARGS: failure,
                FETCH_ARGS: linkage_check.CommandResult(
                    128, "", "fatal: could not read from remote repository"
                ),
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = release_check.run_linkage_gate(Path(tmp), runner)

        self.assertFalse(result["ok"])
        self.assertIsNone(result["merge_base"])
        self.assertTrue(result["errors"])
        joined = "\n".join(result["errors"])
        self.assertIn("no merge base", joined)
        self.assertIn("could not read from remote repository", joined)
        # No linkage scan is attempted without a merge base.
        self.assertNotIn(("git", "rev-list", "None..HEAD"), runner.calls)

    def test_shallow_clone_recovers_via_fetch(self):
        runner = FakeRunner(
            {
                MERGE_BASE_ARGS: [
                    linkage_check.CommandResult(128, "", "fatal: no merge base"),
                    linkage_check.CommandResult(0, "mbsha\n", ""),
                ],
                FETCH_ARGS: "",
                ("git", "rev-list", "mbsha..HEAD"): "",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = release_check.run_linkage_gate(Path(tmp), runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["merge_base"], "mbsha")
        self.assertEqual(result["errors"], [])
        self.assertIn(FETCH_ARGS, runner.calls)

    def test_linkage_errors_propagate(self):
        runner = FakeRunner(
            {
                MERGE_BASE_ARGS: "mbsha\n",
                ("git", "rev-list", "mbsha..HEAD"): linkage_check.CommandResult(
                    128, "", "fatal: bad revision"
                ),
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = release_check.run_linkage_gate(Path(tmp), runner)

        self.assertFalse(result["ok"])
        self.assertTrue(any("bad revision" in err for err in result["errors"]))


class GetModifiedPythonFilesTests(unittest.TestCase):
    def test_diff_failure_is_error_not_empty(self):
        runner = FakeRunner(
            {
                ("git", "diff", "--name-only", "main"): linkage_check.CommandResult(
                    128, "", "fatal: ambiguous argument 'main'"
                ),
                ("git", "status", "--porcelain"): "",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = release_check.get_modified_python_files(Path(tmp), runner)

        self.assertEqual(result["files"], [])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("ambiguous argument", result["errors"][0])

    def test_status_failure_is_error_not_empty(self):
        runner = FakeRunner(
            {
                ("git", "diff", "--name-only", "main"): "",
                ("git", "status", "--porcelain"): linkage_check.CommandResult(
                    128, "", "fatal: not a git repository"
                ),
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = release_check.get_modified_python_files(Path(tmp), runner)

        self.assertEqual(result["files"], [])
        self.assertTrue(any("not a git repository" in err for err in result["errors"]))

    def test_collects_existing_python_files_from_custom_diff_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "foo.py").write_text("x = 1\n", encoding="utf-8")
            runner = FakeRunner(
                {
                    ("git", "diff", "--name-only", "mbsha"): "scripts/foo.py\ndocs/a.md\n",
                    ("git", "status", "--porcelain"): " M scripts/missing.py\n",
                }
            )

            result = release_check.get_modified_python_files(root, runner, "mbsha")

        self.assertEqual(result["errors"], [])
        self.assertEqual(result["files"], [root / "scripts" / "foo.py"])

    def test_lint_check_propagates_git_errors(self):
        runner = FakeRunner(
            {
                ("git", "diff", "--name-only", "main"): linkage_check.CommandResult(
                    128, "", "fatal: bad default revision"
                ),
                ("git", "status", "--porcelain"): "",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = release_check.run_lint_check(Path(tmp), runner)

        self.assertFalse(result["ok"])
        self.assertTrue(any("bad default revision" in err for err in result["errors"]))


class DeclarationCoverageTests(unittest.TestCase):
    def test_sha_prefix_declaration_covers_commit(self):
        entry = {"sha": "badc0ffee123", "behavior_paths": ["scripts/a.py", "scripts/b.py"]}
        covered = release_check._commit_covered_by_declarations(
            entry, [{"line_no": 3, "text": "2026-07-06 badc0ff — hotfix pair"}]
        )
        self.assertTrue(covered)

    def test_all_behavior_paths_must_be_covered(self):
        entry = {"sha": "badc0ffee123", "behavior_paths": ["scripts/a.py", "commands/x.md"]}
        partial = [{"line_no": 3, "text": "2026-07-06 scripts/a.py — hotfix"}]
        self.assertFalse(release_check._commit_covered_by_declarations(entry, partial))

        full = partial + [{"line_no": 4, "text": "2026-07-06 commands/x.md — doc gate"}]
        self.assertTrue(release_check._commit_covered_by_declarations(entry, full))

    def test_directory_scope_covers_nested_paths(self):
        entry = {"sha": "badc0ffee123", "behavior_paths": ["scripts/a.py", "scripts/sub/b.py"]}
        covered = release_check._commit_covered_by_declarations(
            entry, [{"line_no": 3, "text": "2026-07-06 scripts/ — scoped hotfix"}]
        )
        self.assertTrue(covered)

    def test_no_declarations_covers_nothing(self):
        entry = {"sha": "badc0ffee123", "behavior_paths": ["scripts/a.py"]}
        self.assertFalse(release_check._commit_covered_by_declarations(entry, []))


class LoadDeclarationLinesTests(unittest.TestCase):
    def test_missing_file_returns_no_declarations(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(release_check.load_declaration_lines(Path(tmp)), [])

    def test_headings_and_blank_lines_skipped_with_real_line_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "releases").mkdir()
            (root / "releases" / "no-issue-declarations.md").write_text(
                "# No-Issue Declarations\n"
                "\n"
                "2026-07-06 scripts/a.py — first\n"
                "\n"
                "2026-07-07 scripts/b.py — second\n",
                encoding="utf-8",
            )

            declarations = release_check.load_declaration_lines(root)

        self.assertEqual(
            declarations,
            [
                {"line_no": 3, "text": "2026-07-06 scripts/a.py — first"},
                {"line_no": 5, "text": "2026-07-07 scripts/b.py — second"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
