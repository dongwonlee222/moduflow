import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import project_retention


class FakeRunner:
    def __init__(self, responses, failures=None):
        self.responses = responses
        self.failures = failures or {}
        self.calls = []

    def __call__(self, args, cwd, timeout=10):
        key = tuple(args)
        self.calls.append(key)
        if key in self.failures:
            return project_retention.CommandResult(1, "", self.failures[key])
        return project_retention.CommandResult(0, self.responses.get(key, ""), "")


def log_key(date):
    return (
        "git",
        "log",
        "--format=%H",
        f"--since={date}T23:59:59",
        "--",
        project_retention.PLUGIN_MANIFEST,
    )


def write_record(root, rel, frontmatter_lines, body="\n# Title\n"):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + "\n".join(frontmatter_lines) + "\n---\n" + body, encoding="utf-8")
    return path


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_promoted_record_is_settled(self):
        write_record(
            self.root,
            "memory/decisions/a.md",
            ["kind: decision", "date: 2026-06-01", "promoted_to: 076-x"],
        )
        runner = FakeRunner({})
        status = project_retention.retention_status(self.root, runner)
        self.assertTrue(status["ok"])
        self.assertEqual(status["unpromoted_count"], 0)
        self.assertEqual(status["archive_candidates"], [])
        self.assertEqual(runner.calls, [])

    def test_unpromoted_under_threshold_not_candidate(self):
        write_record(self.root, "memory/decisions/b.md", ["kind: decision", "date: 2026-06-01"])
        runner = FakeRunner({log_key("2026-06-01"): "sha1\n"})
        status = project_retention.retention_status(self.root, runner)
        self.assertEqual(status["unpromoted_count"], 1)
        self.assertEqual(status["archive_candidates"], [])
        self.assertEqual(status["oldest"]["path"], "memory/decisions/b.md")

    def test_two_releases_makes_candidate_and_write_archives_in_place(self):
        path = write_record(
            self.root, "memory/decisions/c.md", ["kind: decision", "date: 2026-05-01"]
        )
        before = path.read_text(encoding="utf-8")
        runner = FakeRunner({log_key("2026-05-01"): "sha1\nsha2\n"})
        status = project_retention.archive_candidates(self.root, "2026-07-06", runner)
        self.assertEqual(status["archived_now"], ["memory/decisions/c.md"])
        after = path.read_text(encoding="utf-8")
        self.assertIn("archived: 2026-07-06\n---", after)
        self.assertEqual(after.replace("archived: 2026-07-06\n", ""), before)
        rerun = FakeRunner({})
        status2 = project_retention.retention_status(self.root, rerun)
        self.assertEqual(status2["archive_candidates"], [])
        self.assertEqual(status2["archived_count"], 1)

    def test_git_failure_surfaces_error_not_silent_zero(self):
        write_record(self.root, "memory/decisions/d.md", ["kind: decision", "date: 2026-05-01"])
        runner = FakeRunner({}, failures={log_key("2026-05-01"): "fatal: not a git repo"})
        status = project_retention.retention_status(self.root, runner)
        self.assertFalse(status["ok"])
        self.assertTrue(any("git log failed" in e for e in status["errors"]))

    def test_files_without_kind_frontmatter_ignored(self):
        (self.root / "memory/decisions").mkdir(parents=True)
        (self.root / "memory/decisions/readme.md").write_text("# no frontmatter\n", encoding="utf-8")
        status = project_retention.retention_status(self.root, FakeRunner({}))
        self.assertEqual(status["unpromoted_count"], 0)

    def test_write_refused_without_date_via_cli_contract(self):
        result = project_retention.archive_candidates(self.root, "2026-07-06", FakeRunner({}))
        self.assertTrue(result["ok"])
        self.assertEqual(result.get("archived_now"), [])


if __name__ == "__main__":
    unittest.main()
