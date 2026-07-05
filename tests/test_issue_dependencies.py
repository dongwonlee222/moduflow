import json
import tempfile
import unittest
from pathlib import Path

from scripts import project_lifecycle


def write_issue(root, issue_id, status, extra_lines=None, created="2026-07-05"):
    lines = [
        f"# Issue: `{issue_id}`",
        "",
        f"**Status: {status}** — created {created}.",
    ]
    if extra_lines:
        lines.extend(extra_lines)
    lines.append("")
    lines.append("## Outcome")
    lines.append("")
    lines.append("Test fixture issue.")
    lines.append("")
    (root / "issues" / f"{issue_id}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


class IssueDependenciesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "issues").mkdir()

    # 1. explicit priority parsed; absent -> p2; invalid -> p2
    def test_priority_parsing(self):
        explicit = "**Status: backlog** — created 2026-07-05.\n**Priority: p1**\n"
        self.assertEqual(project_lifecycle._issue_priority(explicit), "p1")

        absent = "**Status: backlog** — created 2026-07-05.\n"
        self.assertEqual(project_lifecycle._issue_priority(absent), "p2")

        invalid_num = "**Status: backlog** — created 2026-07-05.\n**Priority: p9**\n"
        self.assertEqual(project_lifecycle._issue_priority(invalid_num), "p2")

        invalid_word = "**Status: backlog** — created 2026-07-05.\n**Priority: high**\n"
        self.assertEqual(project_lifecycle._issue_priority(invalid_word), "p2")

    # 2. blocked_by multi + backticks parsed; absent -> []
    def test_blocked_by_parsing(self):
        multi = "**Status: backlog** — created 2026-07-05.\n**Blocked-by: `001-a`, `002-b`**\n"
        self.assertEqual(project_lifecycle._issue_blocked_by(multi), ["001-a", "002-b"])

        absent = "**Status: backlog** — created 2026-07-05.\n"
        self.assertEqual(project_lifecycle._issue_blocked_by(absent), [])

        spaced = "**Status: backlog** — created 2026-07-05.\n**Blocked-by: 003-c ,  004-d**\n"
        self.assertEqual(project_lifecycle._issue_blocked_by(spaced), ["003-c", "004-d"])

    # 3. ready excludes issue blocked by an active issue
    def test_ready_excludes_issue_blocked_by_active(self):
        write_issue(self.root, "001-a", "active")
        write_issue(self.root, "002-b", "backlog", extra_lines=["**Blocked-by: 001-a**"])
        ready_ids = [i["id"] for i in project_lifecycle.ready_issues(self.root)]
        self.assertNotIn("002-b", ready_ids)

    # 4. blocker flipped to done -> issue becomes ready; superseded blocker also satisfies
    def test_ready_includes_after_blocker_done_or_superseded(self):
        write_issue(self.root, "001-a", "done")
        write_issue(self.root, "002-b", "backlog", extra_lines=["**Blocked-by: 001-a**"])
        ready_ids = [i["id"] for i in project_lifecycle.ready_issues(self.root)]
        self.assertIn("002-b", ready_ids)

        write_issue(self.root, "003-c", "superseded")
        write_issue(self.root, "004-d", "backlog", extra_lines=["**Blocked-by: 003-c**"])
        ready_ids2 = [i["id"] for i in project_lifecycle.ready_issues(self.root)]
        self.assertIn("004-d", ready_ids2)

    # 5. blocked_by unknown id -> issue NOT ready AND lifecycle_drift contains dangling-ref entry
    def test_unknown_blocked_by_not_ready_and_drift_reported(self):
        write_issue(self.root, "001-a", "backlog", extra_lines=["**Blocked-by: 999-ghost**"])
        ready_ids = [i["id"] for i in project_lifecycle.ready_issues(self.root)]
        self.assertNotIn("001-a", ready_ids)

        drift = project_lifecycle.lifecycle_drift(self.root)
        self.assertTrue(any("999-ghost" in d and "001-a" in d for d in drift))

    # 6. priority ordering p0 < p1 < (absent=p2) < p3, tie by id
    def test_priority_ordering_and_tie_break_by_id(self):
        write_issue(self.root, "004-p3", "backlog", extra_lines=["**Priority: p3**"])
        write_issue(self.root, "003-p2b", "backlog")  # absent -> p2
        write_issue(self.root, "002-p2a", "backlog")  # absent -> p2
        write_issue(self.root, "001-p0", "backlog", extra_lines=["**Priority: p0**"])
        write_issue(self.root, "005-p1", "backlog", extra_lines=["**Priority: p1**"])

        ready_ids = [i["id"] for i in project_lifecycle.ready_issues(self.root)]
        self.assertEqual(
            ready_ids,
            ["001-p0", "005-p1", "002-p2a", "003-p2b", "004-p3"],
        )

    # 7. 2-node cycle between two backlog issues -> drift entry mentioning "cycle"
    def test_two_node_cycle_detected(self):
        write_issue(self.root, "001-a", "backlog", extra_lines=["**Blocked-by: 002-b**"])
        write_issue(self.root, "002-b", "backlog", extra_lines=["**Blocked-by: 001-a**"])
        drift = project_lifecycle.lifecycle_drift(self.root)
        self.assertTrue(any("cycle" in d.lower() for d in drift))

    # 8. done issue referencing another done issue -> NO cycle/dangling drift
    def test_done_referencing_done_no_drift(self):
        write_issue(self.root, "001-a", "done")
        write_issue(self.root, "002-b", "done", extra_lines=["**Blocked-by: 001-a**"])
        drift = project_lifecycle.lifecycle_drift(self.root)
        self.assertEqual(drift, [])

    # 9. ready_issues returns JSON-serializable list (json.dumps round-trip)
    def test_ready_issues_json_serializable(self):
        write_issue(self.root, "001-a", "backlog")
        ready = project_lifecycle.ready_issues(self.root)
        roundtrip = json.loads(json.dumps(ready, ensure_ascii=False))
        self.assertEqual(roundtrip, ready)

    # Review finding 1: prose quoting the syntax inside a section must not
    # be parsed as metadata — parsing is scoped to the pre-section header.
    def test_prose_quoting_syntax_in_body_is_not_metadata(self):
        text = (
            "# Issue: `001-a`\n\n"
            "**Status: backlog** — created 2026-07-05.\n\n"
            "## Sessions\n\n"
            "- Convention note: use `**Priority: p0|p1|p2|p3**` and\n"
            "  **Blocked-by: 999-fake** lines in the header.\n"
        )
        self.assertEqual(project_lifecycle._issue_priority(text), "p2")
        self.assertEqual(project_lifecycle._issue_blocked_by(text), [])

    def test_real_header_metadata_wins_over_body_prose(self):
        text = (
            "# Issue: `001-a`\n\n"
            "**Status: backlog** — created 2026-07-05.\n\n"
            "**Priority: p0**\n\n"
            "**Blocked-by: 002-real**\n\n"
            "## Why\n\n"
            "Docs mention **Priority: p3** and **Blocked-by: 999-fake** as examples.\n"
        )
        self.assertEqual(project_lifecycle._issue_priority(text), "p0")
        self.assertEqual(project_lifecycle._issue_blocked_by(text), ["002-real"])

    # Review finding 2: recursive DFS crashed with RecursionError on long
    # chains — the iterative version must survive a 2500-node chain in the
    # crash-triggering direction (lexicographically-first id at chain head).
    def test_long_dependency_chain_does_not_crash(self):
        n = 2500
        for i in range(n):
            blocked = [f"{i + 1:05d}-c"] if i + 1 < n else None
            extra = [f"**Blocked-by: {blocked[0]}**"] if blocked else None
            write_issue(self.root, f"{i:05d}-c", "backlog", extra_lines=extra)
        drift = project_lifecycle._dependency_drift(self.root)
        self.assertEqual(drift, [])  # a chain is not a cycle

    def test_self_reference_is_reported_as_cycle(self):
        write_issue(self.root, "001-a", "backlog", extra_lines=["**Blocked-by: 001-a**"])
        drift = project_lifecycle._dependency_drift(self.root)
        self.assertTrue(any("cycle" in d for d in drift))

    # Review finding 4 (scope addition): an active issue with an unmet
    # blocker previously produced zero signal anywhere.
    def test_active_issue_with_unmet_blocker_is_drift(self):
        write_issue(self.root, "001-blocker", "backlog")
        write_issue(self.root, "002-worker", "active", extra_lines=["**Blocked-by: 001-blocker**"])
        drift = project_lifecycle._dependency_drift(self.root)
        self.assertTrue(any("unmet blocker" in d and "002-worker" in d for d in drift))

    def test_active_issue_with_done_blocker_is_clean(self):
        write_issue(self.root, "001-blocker", "done")
        write_issue(self.root, "002-worker", "active", extra_lines=["**Blocked-by: 001-blocker**"])
        drift = project_lifecycle._dependency_drift(self.root)
        self.assertEqual([d for d in drift if "unmet blocker" in d], [])


if __name__ == "__main__":
    unittest.main()
