#!/usr/bin/env python3
"""
Test: Worker Cognitive Demand Model Routing (Issue 030)

Verifies that:
1. worker-plan.json subagent blocks contain CognitiveDemand field
2. deep workers get "deep", fast workers get "fast"
3. Prompt text contains the correct model selection instruction
4. An actual subagent invocation respects the demand hint
   (simulated: checks that Prompt carries the right instruction string)
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import worker_orchestrator as wo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEEP_TASK_TEXT = "spec: define API contract for sync connector [files: spec.md]"
FAST_TASK_TEXT = "release: write release notes and update changelog [files: CHANGELOG.md]"
BALANCED_TASK_TEXT = "implementation: write sync connector script [files: scripts/sync.py]"


def make_tasks_md(tasks: list[str]) -> str:
    return "\n".join(f"- [ ] {t}" for t in tasks) + "\n"


def build_plan_for(tasks: list[str]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        spec_dir = tmp_root / "specs" / "test-issue"
        spec_dir.mkdir(parents=True)
        (spec_dir / "tasks.md").write_text(make_tasks_md(tasks), encoding="utf-8")
        (tmp_root / "workers").mkdir()
        return wo.build_worker_plan(tmp_root, "test-issue")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCognitiveDemandDict(unittest.TestCase):
    """WORKER_COGNITIVE_DEMAND covers all configured workers."""

    def test_all_workers_have_demand(self):
        for worker, _ in wo.WORKER_RULES:
            self.assertIn(
                worker,
                wo.WORKER_COGNITIVE_DEMAND,
                f"{worker} missing from WORKER_COGNITIVE_DEMAND",
            )

    def test_default_worker_has_demand(self):
        self.assertIn(wo.DEFAULT_WORKER, wo.WORKER_COGNITIVE_DEMAND)

    def test_only_valid_levels(self):
        valid = {"deep", "balanced", "fast"}
        for worker, level in wo.WORKER_COGNITIVE_DEMAND.items():
            self.assertIn(level, valid, f"{worker} has invalid demand level: {level}")


class TestSubagentBlockContainsDemand(unittest.TestCase):
    """worker-plan subagent blocks carry CognitiveDemand and correct Prompt."""

    def _get_task(self, text: str) -> dict:
        plan = build_plan_for([text])
        self.assertEqual(len(plan["tasks"]), 1)
        return plan["tasks"][0]

    def test_deep_worker_has_deep_demand(self):
        task = self._get_task(DEEP_TASK_TEXT)
        self.assertEqual(task["worker"], "spec-architect")
        self.assertEqual(task["subagent"]["CognitiveDemand"], "deep")

    def test_fast_worker_has_fast_demand(self):
        task = self._get_task(FAST_TASK_TEXT)
        self.assertEqual(task["worker"], "release-manager")
        self.assertEqual(task["subagent"]["CognitiveDemand"], "fast")

    def test_balanced_worker_has_balanced_demand(self):
        task = self._get_task(BALANCED_TASK_TEXT)
        self.assertEqual(task["worker"], "implementation-worker")
        self.assertEqual(task["subagent"]["CognitiveDemand"], "balanced")

    def test_deep_prompt_says_most_capable(self):
        task = self._get_task(DEEP_TASK_TEXT)
        self.assertIn("most capable reasoning model", task["subagent"]["Prompt"])

    def test_fast_prompt_says_lightest(self):
        task = self._get_task(FAST_TASK_TEXT)
        self.assertIn("lightest, fastest model", task["subagent"]["Prompt"])

    def test_balanced_prompt_says_standard(self):
        task = self._get_task(BALANCED_TASK_TEXT)
        self.assertIn("standard production model", task["subagent"]["Prompt"])


class TestMixedPlanDemandDistribution(unittest.TestCase):
    """A plan with mixed workers produces the correct demand distribution."""

    def test_mixed_plan(self):
        plan = build_plan_for([DEEP_TASK_TEXT, BALANCED_TASK_TEXT, FAST_TASK_TEXT])
        demands = {t["subagent"]["CognitiveDemand"] for t in plan["tasks"]}
        self.assertIn("deep", demands)
        self.assertIn("balanced", demands)
        self.assertIn("fast", demands)


class TestWorkerMdFiles(unittest.TestCase):
    """Each workers/*.md file declares cognitive_demand."""

    def test_all_worker_files_have_cognitive_demand(self):
        workers_dir = ROOT / "workers"
        for md_file in workers_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            self.assertIn(
                "cognitive_demand:",
                content,
                f"{md_file.name} is missing 'cognitive_demand:' metadata",
            )

    def test_skill_md_has_model_self_selection_guide(self):
        skill_file = ROOT / "skills" / "superpowers-execution-bridge" / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        self.assertIn("CognitiveDemand", content)
        self.assertIn("deep", content)
        self.assertIn("balanced", content)
        self.assertIn("fast", content)

    def test_product_execute_dispatch_card_has_demand(self):
        cmd_file = ROOT / "commands" / "product-execute.md"
        content = cmd_file.read_text(encoding="utf-8")
        self.assertIn("Cognitive Demand", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
