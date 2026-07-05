import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import project_github_issues, project_sync


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, args, cwd, timeout=None):
        self.calls.append(tuple(args))
        key = tuple(args)
        if key not in self.responses:
            return project_sync.CommandResult(1, "", f"unexpected command: {' '.join(args)}")
        value = self.responses[key]
        if isinstance(value, BaseException):
            raise value
        if isinstance(value, project_sync.CommandResult):
            return value
        return project_sync.CommandResult(0, value, "")


ISSUE_ID = "054-sample-sync"

ISSUE_TEXT = """# Issue: 054-sample-sync

**Status: active** — created 2026-07-03.

## Outcome

Sample outcome text for sync.

## Links

- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
"""


class GithubIssueSyncTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)

    def _write_project(self, github_sync="optional", issue_text=ISSUE_TEXT):
        (self.root / ".moduflow").mkdir()
        (self.root / ".moduflow" / "config.json").write_text(
            json.dumps({"git": {"github_sync": github_sync, "issue_source": "git-files"}}),
            encoding="utf-8",
        )
        (self.root / "issues").mkdir()
        issue_path = self.root / "issues" / f"{ISSUE_ID}.md"
        issue_path.write_text(issue_text, encoding="utf-8")
        return issue_path

    def test_disabled_config_makes_sync_a_noop(self):
        self._write_project(github_sync="off")
        runner = FakeRunner({})

        result = project_github_issues.sync_issue(self.root, ISSUE_ID, runner=runner)

        self.assertEqual(result["action"], "disabled")
        self.assertEqual(runner.calls, [])

    def test_create_path_creates_issue_and_writes_links_line(self):
        issue_path = self._write_project()
        repo = "dongwonlee222/moduflow"
        body = (
            "Sample outcome text for sync.\n\n"
            "---\n"
            f"Canonical source: https://github.com/{repo}/blob/HEAD/issues/{ISSUE_ID}.md\n"
            "<!-- moduflow:issue-sync -->"
        )
        url = f"https://github.com/{repo}/issues/7"
        runner = FakeRunner(
            {
                ("git", "remote", "get-url", "origin"): "git@github-evmodu:dongwonlee222/moduflow.git\n",
                ("gh", "label", "list", "-R", repo, "--json", "name"): json.dumps(
                    [{"name": "moduflow:backlog"}, {"name": "moduflow:done"}]
                ),
                ("gh", "label", "create", "moduflow:active", "-R", repo, "--color", "fbca04"): "",
                ("gh", "label", "create", "moduflow:superseded", "-R", repo, "--color", "6f42c1"): "",
                (
                    "gh",
                    "issue",
                    "create",
                    "-R",
                    repo,
                    "--title",
                    ISSUE_ID,
                    "--body",
                    body,
                    "--label",
                    "moduflow:active",
                ): url + "\n",
            }
        )

        result = project_github_issues.sync_issue(self.root, ISSUE_ID, runner=runner)

        self.assertEqual(result["action"], "created")
        self.assertEqual(result["url"], url)
        self.assertEqual(result["label"], "moduflow:active")
        updated = issue_path.read_text(encoding="utf-8")
        self.assertIn(f"- GitHub: {url}", updated)
        # The link lands inside the Links section, before the next heading.
        links_section = updated.split("## Links", 1)[1].split("## ", 1)[0]
        self.assertIn(f"- GitHub: {url}", links_section)

    def test_update_path_edits_labels_without_creating(self):
        repo = "o/r"
        issue_text = ISSUE_TEXT.replace(
            "- Roadmap: `workspace/roadmap.md`",
            "- Roadmap: `workspace/roadmap.md`\n- GitHub: https://github.com/o/r/issues/42",
        )
        self._write_project(issue_text=issue_text)
        all_labels = json.dumps([{"name": name} for name in project_github_issues.LABELS.values()])
        runner = FakeRunner(
            {
                ("git", "remote", "get-url", "origin"): "https://github.com/o/r\n",
                ("gh", "label", "list", "-R", repo, "--json", "name"): all_labels,
                (
                    "gh",
                    "issue",
                    "edit",
                    "42",
                    "-R",
                    repo,
                    "--add-label",
                    "moduflow:active",
                    "--remove-label",
                    "moduflow:backlog",
                    "--remove-label",
                    "moduflow:done",
                    "--remove-label",
                    "moduflow:superseded",
                ): "",
            }
        )

        before = (self.root / "issues" / f"{ISSUE_ID}.md").read_text(encoding="utf-8")
        result = project_github_issues.sync_issue(self.root, ISSUE_ID, runner=runner)

        self.assertEqual(result["action"], "updated")
        self.assertEqual(result["url"], "https://github.com/o/r/issues/42")
        self.assertEqual(result["label"], "moduflow:active")
        for call in runner.calls:
            self.assertNotEqual(call[:3], ("gh", "issue", "create"))
        after = (self.root / "issues" / f"{ISSUE_ID}.md").read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_parse_owner_repo_forms(self):
        cases = [
            ("git@github-evmodu:dongwonlee222/moduflow.git", "dongwonlee222/moduflow"),
            ("git@github.com:o/r.git", "o/r"),
            ("https://github.com/o/r", "o/r"),
            ("https://github.com/o/r.git", "o/r"),
            ("git@github.com:owner/nested/repo.git", None),
            ("not a url", None),
        ]
        for url, expected in cases:
            with self.subTest(url=url):
                self.assertEqual(project_github_issues._parse_owner_repo(url), expected)

    def test_outcome_section_keeps_heading_lookalikes_inside_fences(self):
        text = (
            "# Issue: x\n\n## Outcome\n\n"
            "Before fence.\n\n```\n## not a heading\ncode line\n```\n\nAfter fence.\n\n"
            "## Why\n\nreal next section\n"
        )
        section = project_github_issues._outcome_section(text)
        self.assertIn("## not a heading", section)
        self.assertIn("After fence.", section)
        self.assertNotIn("real next section", section)

    def test_github_link_ignores_bullet_outside_links_section(self):
        text = (
            "# Issue: x\n\n## Related Issues\n\n- GitHub: https://github.com/o/r/issues/9\n\n"
            "## Links\n\n- Roadmap: `workspace/roadmap.md`\n"
        )
        self.assertIsNone(project_github_issues._github_link(text))

    def test_write_github_link_replaces_existing_bullet(self):
        issue_path = self._write_project(
            issue_text=ISSUE_TEXT.replace(
                "- Roadmap: `workspace/roadmap.md`",
                "- Roadmap: `workspace/roadmap.md`\n- GitHub: https://github.com/o/r/issues/1",
            )
        )
        project_github_issues._write_github_link(issue_path, "https://github.com/o/r/issues/2")
        text = issue_path.read_text(encoding="utf-8")
        self.assertEqual(text.count("- GitHub:"), 1)
        self.assertIn("- GitHub: https://github.com/o/r/issues/2", text)

    def test_label_create_tolerates_already_exists(self):
        repo = "o/r"
        runner = FakeRunner(
            {
                ("gh", "label", "list", "-R", repo, "--json", "name"): "not json",
                ("gh", "label", "create", "moduflow:backlog", "-R", repo, "--color", "ededed"):
                    project_sync.CommandResult(1, "", "label already exists"),
                ("gh", "label", "create", "moduflow:active", "-R", repo, "--color", "fbca04"):
                    project_sync.CommandResult(1, "", "label already exists"),
                ("gh", "label", "create", "moduflow:done", "-R", repo, "--color", "0e8a16"):
                    project_sync.CommandResult(1, "", "label already exists"),
                ("gh", "label", "create", "moduflow:superseded", "-R", repo, "--color", "6f42c1"):
                    project_sync.CommandResult(1, "", "label already exists"),
            }
        )
        self.assertIsNone(project_github_issues._ensure_labels(runner, Path("."), repo))

    def test_label_bootstrap_creates_only_missing(self):
        repo = "o/r"
        runner = FakeRunner(
            {
                ("gh", "label", "list", "-R", repo, "--json", "name"): json.dumps(
                    [
                        {"name": "moduflow:backlog"},
                        {"name": "moduflow:active"},
                        {"name": "moduflow:done"},
                    ]
                ),
                ("gh", "label", "create", "moduflow:superseded", "-R", repo, "--color", "6f42c1"): "",
            }
        )

        project_github_issues._ensure_labels(runner, Path("."), repo)

        create_calls = [c for c in runner.calls if c[:3] == ("gh", "label", "create")]
        self.assertEqual(len(create_calls), 1)
        self.assertEqual(create_calls[0][3], "moduflow:superseded")


if __name__ == "__main__":
    unittest.main()
