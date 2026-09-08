import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = REPO_ROOT / "hooks" / "session_start.py"
HOOKS_MANIFEST = REPO_ROOT / "hooks" / "hooks.json"

STATE = {
    "schema": "moduflow.state.v1",
    "phase": "plan",
    "active_goal": "team-visibility-onboarding",
    "active_issue": "",
    "last_command": "product:plan 072-lifecycle-hooks-automation",
    "next_command": "product:execute 072-lifecycle-hooks-automation",
    "blockers": [],
    "updated_at": "2026-07-06",
}

LOOP_STATE = {
    "schema": "moduflow.loop-state.v2",
    "goal_id": "business-document-workflow",
    "objective": "Decision-ready business documents.",
    "active_issue_id": "072-lifecycle-hooks-automation",
    "phase": "execute",
    "status": "active",
    "next_command": "product:execute 072-lifecycle-hooks-automation",
    "blocker": None,
    "updated_at": "2026-07-06",
}

LOG_LINE = re.compile(r"^\S+ session_start (warn|error) .+$")


def run_hook(cwd):
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=30,
    )


class SessionStartHookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def log_path(self):
        return self.root / ".moduflow" / "logs" / "hooks.log"

    def parse_contract(self, stdout):
        payload = json.loads(stdout)
        self.assertEqual(set(payload), {"hookSpecificOutput", "suppressOutput"})
        self.assertIs(payload["suppressOutput"], True)
        specific = payload["hookSpecificOutput"]
        self.assertEqual(set(specific), {"hookEventName", "additionalContext"})
        self.assertEqual(specific["hookEventName"], "SessionStart")
        return specific["additionalContext"]

    def test_full_state_emits_banner_contract(self):
        self.write(".moduflow/state.json", json.dumps(STATE))
        self.write("workspace/loop-state.json", json.dumps(LOOP_STATE))
        result = run_hook(self.root)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        banner = self.parse_contract(result.stdout)
        self.assertIn("team-visibility-onboarding", banner)  # goal
        self.assertIn("072-lifecycle-hooks-automation", banner)  # active issue
        self.assertIn("product:execute 072-lifecycle-hooks-automation", banner)
        self.assertIn("목표", banner)
        self.assertNotIn("막힘", banner)  # no blockers in fixture
        self.assertLessEqual(len(banner.splitlines()), 10)

    def test_missing_moduflow_is_fully_silent(self):
        result = run_hook(self.root)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertFalse(self.log_path().exists())
        self.assertFalse((self.root / ".moduflow").exists())

    def test_corrupt_state_logs_and_exits_zero(self):
        self.write(".moduflow/state.json", "{not valid json")
        result = run_hook(self.root)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        # Both sources broken (loop-state absent) -> silent stdout, or at most
        # a valid contract payload; here it must be silent.
        self.assertEqual(result.stdout, "")
        self.assertTrue(self.log_path().exists())
        lines = self.log_path().read_text(encoding="utf-8").splitlines()
        self.assertTrue(lines)
        for line in lines:
            self.assertRegex(line, LOG_LINE)
        self.assertTrue(any("state.json" in line for line in lines))

    def test_loop_state_only_still_banners(self):
        self.write(".moduflow/state.json", "{}")
        self.write("workspace/loop-state.json", json.dumps(LOOP_STATE))
        result = run_hook(self.root)
        self.assertEqual(result.returncode, 0)
        banner = self.parse_contract(result.stdout)
        self.assertIn("072-lifecycle-hooks-automation", banner)
        self.assertIn("business-document-workflow", banner)
        self.assertIn("product:execute 072-lifecycle-hooks-automation", banner)

    def test_corrupt_state_with_valid_loop_state_still_banners(self):
        self.write(".moduflow/state.json", "{broken")
        self.write("workspace/loop-state.json", json.dumps(LOOP_STATE))
        result = run_hook(self.root)
        self.assertEqual(result.returncode, 0)
        banner = self.parse_contract(result.stdout)
        self.assertIn("072-lifecycle-hooks-automation", banner)
        self.assertTrue(self.log_path().exists())

    def test_blocker_line_present_when_blocked(self):
        state = dict(STATE, blockers=["waiting on release approval"])
        self.write(".moduflow/state.json", json.dumps(state))
        result = run_hook(self.root)
        self.assertEqual(result.returncode, 0)
        banner = self.parse_contract(result.stdout)
        self.assertIn("막힘: waiting on release approval", banner)

    def test_manifest_declares_both_hooks(self):
        manifest = json.loads(HOOKS_MANIFEST.read_text(encoding="utf-8"))
        session_start = manifest["hooks"]["SessionStart"]
        self.assertEqual(len(session_start), 1)
        self.assertEqual(
            set(session_start[0]["matcher"].split("|")),
            {"startup", "resume", "clear", "compact"},
        )
        entry = session_start[0]["hooks"][0]
        self.assertEqual(entry["type"], "command")
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}"/hooks/session_start.py', entry["command"])
        self.assertEqual(entry["timeout"], 30)

        stop = manifest["hooks"]["Stop"][0]["hooks"][0]
        self.assertEqual(stop["type"], "command")
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}"/hooks/on_stop.py', stop["command"])
        self.assertEqual(stop["timeout"], 15)



class RoadmapFirstBannerTests(unittest.TestCase):
    """Issue 152 — the banner never read the roadmap, which is where the owner
    writes the order.

    Before this, `build_banner` looked at `loop-state.json` then `state.json` and
    stopped. On 2026-09-07 the roadmap said "step 1: issue 151" while both state
    files said `product:status`, and the banner showed `product:status` — the
    machine's answer, correct at its own layer, hiding the human's.

    The two are not merged: the machine writes two of the files and a person
    writes the third, and collapsing that lets a transaction overwrite an order
    somebody chose. When they disagree, **both** are shown.
    """

    def load_hook(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("session_start_mod", HOOK_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    ROADMAP = """# ModuFlow Roadmap

## 지금 순서 — 확정

- [x] **1. `151` — 끝난 것**
- [ ] **2. `150` · `152` — 다음에 할 것**
- [ ] **3. `139` — 그다음**
"""

    def test_roadmap_next_item_appears_in_the_banner(self):
        hook = self.load_hook()
        banner = hook.build_banner(
            {"next_command": "product:status", "phase": "select"},
            {},
            0,
            roadmap_next="2. `150` · `152` — 다음에 할 것",
        )
        self.assertIn("150", banner)

    def test_both_are_shown_when_they_disagree(self):
        hook = self.load_hook()
        banner = hook.build_banner(
            {"next_command": "product:status", "phase": "select"},
            {},
            0,
            roadmap_next="2. `150` · `152` — 다음에 할 것",
        )
        self.assertIn("150", banner)
        self.assertIn("product:status", banner)

    def test_no_roadmap_means_the_banner_is_unchanged(self):
        hook = self.load_hook()
        before = hook.build_banner(
            {"next_command": "product:status", "phase": "select"}, {}, 0
        )
        after = hook.build_banner(
            {"next_command": "product:status", "phase": "select"}, {}, 0,
            roadmap_next=None,
        )
        self.assertEqual(before, after)

    def test_first_unchecked_item_is_the_one_read(self):
        hook = self.load_hook()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "roadmap.md").write_text(self.ROADMAP, encoding="utf-8")
            found = hook.roadmap_next_item(root)
            self.assertIsNotNone(found)
            self.assertIn("150", found)
            self.assertNotIn("151", found, "a checked item must not be picked")

    def test_a_missing_roadmap_returns_none_and_does_not_raise(self):
        hook = self.load_hook()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(hook.roadmap_next_item(Path(tmp)))

    def test_a_roadmap_with_no_unchecked_item_returns_none(self):
        hook = self.load_hook()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "roadmap.md").write_text(
                "# Roadmap\n\n- [x] **1. done**\n", encoding="utf-8"
            )
            self.assertIsNone(hook.roadmap_next_item(root))



if __name__ == "__main__":
    unittest.main()
