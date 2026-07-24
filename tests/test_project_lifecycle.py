import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scaffold(root, issues, active_in_dashboard="048-x", state_active="048-x"):
    (root / "issues").mkdir()
    for iid, status in issues.items():
        (root / "issues" / f"{iid}.md").write_text(
            f"# Issue: `{iid}`\n\n**Status: {status}** — created.\n", encoding="utf-8")
    (root / ".moduflow").mkdir()
    (root / ".moduflow" / "state.json").write_text(json.dumps({
        "schema": "moduflow.state.v1", "phase": "spec", "active_goal": "g",
        "active_issue": state_active, "next_command": "product:status",
        "blockers": [], "updated_at": "2026-06-28",
    }) + "\n", encoding="utf-8")
    (root / "workspace").mkdir()
    (root / "workspace" / "dashboard.md").write_text(
        "# Dashboard\n\n## Active Issue\n\n- `" + active_in_dashboard + "` (phase: spec).\n\n"
        "## Recently Completed\n\n- IMPORTANT HUMAN PROSE that must survive sync.\n\n"
        "## Next Command\n\n`product:status`\n", encoding="utf-8")


class ProjectLifecycleTests(unittest.TestCase):
    def test_warning_dependency_wait_is_still_excluded_from_ready_queue(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(
                root,
                {"BIZ-BLOCKER": "backlog", "BIZ-WAITING": "backlog"},
                active_in_dashboard="",
                state_active="",
            )
            waiting = root / "issues" / "BIZ-WAITING.md"
            waiting.write_text(
                "# Issue: `BIZ-WAITING`\n\n"
                "**Status: backlog** — created.\n"
                "**Blocked-by: BIZ-BLOCKER**\n",
                encoding="utf-8",
            )

            ready_ids = [item["id"] for item in lc.ready_issues(root)]

        self.assertIn("BIZ-BLOCKER", ready_ids)
        self.assertNotIn("BIZ-WAITING", ready_ids)

    def test_legacy_markdown_public_shapes_remain_compatible(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active", "045-y": "done", "050-z": "backlog"})
            issue = root / "issues" / "050-z.md"
            issue.write_text(
                "# Issue: `050-z` Backlog title\n\n"
                "**Status: backlog** — created.\n"
                "**Priority: p1**\n"
                "**Blocked-by: 045-y**\n",
                encoding="utf-8",
            )

            state = lc.lifecycle_state(root)
            self.assertEqual(
                set(state),
                {"issues", "active", "done", "backlog", "superseded"},
            )
            self.assertEqual(state["issues"]["050-z"], "backlog")

            items = lc.list_issues(root)
            self.assertTrue(items)
            self.assertTrue(
                all(
                    set(item)
                    == {"id", "status", "title", "priority", "blocked_by"}
                    for item in items
                )
            )
            self.assertEqual([item["id"] for item in items], sorted(state["issues"]))
            backlog = next(item for item in items if item["id"] == "050-z")
            self.assertEqual(
                backlog,
                {
                    "id": "050-z",
                    "status": "backlog",
                    "title": "050-z` Backlog title",
                    "priority": "p1",
                    "blocked_by": ["045-y"],
                },
            )

            ready = lc.ready_issues(root)
            self.assertEqual(ready, [backlog])

    def test_lifecycle_state_parses_canonical_statuses(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active", "045-y": "done", "050-z": "backlog",
                            "041-w": "superseded-by-042"})
            st = lc.lifecycle_state(root)
            self.assertEqual(st["active"], ["048-x"])
            self.assertEqual(st["done"], ["045-y"])
            self.assertEqual(st["backlog"], ["050-z"])
            self.assertEqual(st["superseded"], ["041-w"])

    def test_drift_empty_when_in_sync(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active"})
            self.assertEqual(lc.lifecycle_drift(root), [])

    def test_drift_flags_stale_state_and_dashboard(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # issue files say 048 active, but state.json + dashboard say a different/none
            scaffold(root, {"048-x": "active", "045-y": "done"},
                     active_in_dashboard="045-y", state_active="040-old")
            drift = lc.lifecycle_drift(root)
            self.assertTrue(any("040-old" in d for d in drift))      # state mismatch
            self.assertTrue(any("045-y" in d and "done" in d for d in drift))  # done listed active

    def test_sync_updates_views_idempotently_and_preserves_prose(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active"}, active_in_dashboard="040-old", state_active="040-old")
            (root / "specs" / "048-x").mkdir(parents=True)
            (root / "specs" / "048-x" / "spec.md").write_text("# s\n", encoding="utf-8")

            with mock.patch.object(
                lc, "evaluate_project", wraps=lc.evaluate_project
            ) as evaluate:
                first = lc.sync_lifecycle(root)
            self.assertEqual(evaluate.call_count, 1)
            self.assertEqual(first["active"], "048-x")
            self.assertEqual(first["phase"], "spec")
            self.assertTrue(first["dashboard_updated"])
            self.assertEqual(lc.lifecycle_drift(root), [])

            state = json.loads((root / ".moduflow" / "state.json").read_text())
            self.assertEqual(state["active_issue"], "048-x")
            dash = (root / "workspace" / "dashboard.md").read_text()
            self.assertIn("IMPORTANT HUMAN PROSE", dash)   # prose preserved
            self.assertIn("048-x", dash)

            second = lc.sync_lifecycle(root)               # idempotent
            self.assertFalse(second["dashboard_updated"])

    def test_sync_fails_closed_without_writing_for_unreadable_active_issue(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active"})
            unreadable = root / "issues" / "048-x.md"
            unreadable.write_bytes(b"\xff\xfe\x00\x80")
            state_path = root / ".moduflow" / "state.json"
            dashboard_path = root / "workspace" / "dashboard.md"
            state_before = state_path.read_bytes()
            dashboard_before = dashboard_path.read_bytes()

            with mock.patch.object(
                lc, "evaluate_project", wraps=lc.evaluate_project
            ) as evaluate:
                result = lc.sync_lifecycle(root)

            self.assertEqual(evaluate.call_count, 1)
            self.assertEqual(result["status"], "blocked")
            self.assertFalse(result["dashboard_updated"])
            self.assertTrue(result["errors"])
            self.assertIn("ISSUE_SOURCE_UNREADABLE", result["errors"][0])
            self.assertIn("UTF-8", result["errors"][0])
            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertEqual(dashboard_path.read_bytes(), dashboard_before)

            output = io.StringIO()
            with mock.patch(
                "sys.argv",
                ["project_lifecycle.py", str(root), "--sync"],
            ), contextlib.redirect_stdout(output):
                exit_code = lc.main()
            self.assertNotEqual(exit_code, 0)
            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertEqual(dashboard_path.read_bytes(), dashboard_before)

    def test_infer_phase_from_spec_artifacts(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs" / "048-x").mkdir(parents=True)
            self.assertEqual(lc.infer_phase(root, ""), "select")
            (root / "specs" / "048-x" / "spec.md").write_text("x", encoding="utf-8")
            self.assertEqual(lc.infer_phase(root, "048-x"), "spec")
            (root / "specs" / "048-x" / "plan.md").write_text("x", encoding="utf-8")
            self.assertEqual(lc.infer_phase(root, "048-x"), "plan")
            (root / "specs" / "048-x" / "tasks.md").write_text("x", encoding="utf-8")
            self.assertEqual(lc.infer_phase(root, "048-x"), "execute")


if __name__ == "__main__":
    unittest.main()
