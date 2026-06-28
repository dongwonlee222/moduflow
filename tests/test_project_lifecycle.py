import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


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

            first = lc.sync_lifecycle(root)
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
