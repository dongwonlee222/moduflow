#!/usr/bin/env python3
"""
Test: Worker Cognitive Demand Model Routing (Issue 030)

Verifies that:
1. every worker plan task carries a cognitive_demand field
2. deep workers get "deep", fast workers get "fast"
3. that demand selects a model and an effort level per host
4. no prompt names a model

Points 3 and 4 were rewritten for issue 112. They used to assert the prompt
text `use your most capable reasoning model. If using OpenAI GPT-5.6, prefer
gpt-5.6-sol…`, which section 8 measured being written into every prompt on
every host — including hosts where GPT-5.6 is not available. The choice now
lives in the adapter's `model()` on two axes, so the same claim is asserted
there instead of in prose the host cannot use.
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


def build_plan_for(tasks: list[str], host: str | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        spec_dir = tmp_root / "specs" / "test-issue"
        spec_dir.mkdir(parents=True)
        (spec_dir / "tasks.md").write_text(make_tasks_md(tasks), encoding="utf-8")
        (tmp_root / "workers").mkdir()
        return wo.build_worker_plan(tmp_root, "test-issue", host=host)


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

    def _get_task(self, text: str, host: str | None = None) -> dict:
        plan = build_plan_for([text], host=host)
        self.assertEqual(len(plan["tasks"]), 1)
        return plan["tasks"][0]

    def test_deep_worker_has_deep_demand(self):
        task = self._get_task(DEEP_TASK_TEXT)
        self.assertEqual(task["worker"], "spec-architect")
        # Was `subagent["CognitiveDemand"]`. Since issue 112 the demand is a
        # task field, because it is intent every host needs and `CognitiveDemand`
        # is one host's key name. The Codex record still carries it (below).
        self.assertEqual(task["cognitive_demand"], "deep")

    def test_fast_worker_has_fast_demand(self):
        task = self._get_task(FAST_TASK_TEXT)
        self.assertEqual(task["worker"], "release-manager")
        self.assertEqual(task["cognitive_demand"], "fast")

    def test_balanced_worker_has_balanced_demand(self):
        task = self._get_task(BALANCED_TASK_TEXT)
        self.assertEqual(task["worker"], "implementation-worker")
        self.assertEqual(task["cognitive_demand"], "balanced")

    def test_the_codex_record_still_carries_the_demand_under_the_codex_host(self):
        task = self._get_task(DEEP_TASK_TEXT, host="codex")
        self.assertEqual(task["subagent"]["CognitiveDemand"], "deep")

    def test_deep_selects_the_most_capable_model_of_each_host(self):
        """Was: the prompt must contain "most capable reasoning model" and
        `gpt-5.6-sol`. Issue 112 section 8 takes model names out of every prompt
        — they were written on hosts where they were false — so the same claim
        is now made where the choice actually lives, on two axes."""
        self.assertEqual(
            self._get_task(DEEP_TASK_TEXT, host="codex")["model"],
            {"effort": "xhigh", "model_hint": "gpt-5.6-sol"},
        )
        self.assertEqual(
            self._get_task(DEEP_TASK_TEXT)["model"],
            {"effort": "xhigh", "model_hint": "opus"},
        )

    def test_fast_selects_the_lightest_model_of_each_host(self):
        self.assertEqual(
            self._get_task(FAST_TASK_TEXT, host="codex")["model"],
            {"effort": "low", "model_hint": "gpt-5.6-luna"},
        )
        self.assertEqual(
            self._get_task(FAST_TASK_TEXT)["model"],
            {"effort": "low", "model_hint": "haiku"},
        )

    def test_balanced_selects_the_standard_model_of_each_host(self):
        self.assertEqual(
            self._get_task(BALANCED_TASK_TEXT, host="codex")["model"],
            {"effort": "high", "model_hint": "gpt-5.6-terra"},
        )
        self.assertEqual(
            self._get_task(BALANCED_TASK_TEXT)["model"],
            {"effort": "high", "model_hint": "sonnet"},
        )

    def test_no_prompt_names_a_model_on_any_host(self):
        """The replacement claim for the three prompt-text tests above."""
        for host in ("claude-code", "codex"):
            for text in (DEEP_TASK_TEXT, BALANCED_TASK_TEXT, FAST_TASK_TEXT):
                record = self._get_task(text, host=host)["subagent"]
                prompt = record.get("Prompt") or record.get("prompt") or ""
                for name in ("gpt-5.6", "opus", "sonnet", "haiku"):
                    self.assertNotIn(name, prompt.lower(), f"{name} under {host}")


class TestMixedPlanDemandDistribution(unittest.TestCase):
    """A plan with mixed workers produces the correct demand distribution."""

    def test_mixed_plan(self):
        plan = build_plan_for([DEEP_TASK_TEXT, BALANCED_TASK_TEXT, FAST_TASK_TEXT])
        demands = {t["cognitive_demand"] for t in plan["tasks"]}
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
        self.assertIn("gpt-5.6-sol", content)
        self.assertIn("gpt-5.6-terra", content)
        self.assertIn("gpt-5.6-luna", content)

    def test_product_execute_dispatch_card_has_demand(self):
        """Was: the document must mention "GPT-5.6".

        That assertion passed while the doc told every host to use OpenAI
        models, which is the defect issue 112 removed. What matters is that the
        card shows the demand and that the mapping names each host's own
        answer — so the assertion is now the mapping, not one vendor's string.
        """
        content = (ROOT / "commands" / "product-execute.md").read_text(encoding="utf-8")
        self.assertIn("Cognitive Demand", content)
        for host_model in ("opus", "sonnet", "haiku", "gpt-5.6-sol", "gpt-5.6-terra"):
            with self.subTest(model=host_model):
                self.assertIn(host_model, content)
        for effort in ("xhigh", "high", "low"):
            with self.subTest(effort=effort):
                self.assertIn(effort, content)

    def test_product_execute_says_refusal_is_a_normal_outcome(self):
        """T11's actual point: a plan that was not written is an answer."""
        content = (ROOT / "commands" / "product-execute.md").read_text(encoding="utf-8")
        self.assertIn("needs_plan", content)
        self.assertIn("not_applicable", content)
        self.assertIn("오류가 아닙니다", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
