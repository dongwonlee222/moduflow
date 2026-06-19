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


class WorkerOrchestrationTests(unittest.TestCase):
    def make_project(self, root, tasks):
        spec_root = root / "specs" / "007-worker-orchestration"
        spec_root.mkdir(parents=True)
        (spec_root / "tasks.md").write_text(tasks, encoding="utf-8")
        workers_root = root / "workers"
        workers_root.mkdir()
        for name in [
            "pm-strategist",
            "spec-architect",
            "roadmap-planner",
            "ux-flow-worker",
            "data-reviewer",
            "implementation-worker",
            "qa-reviewer",
            "release-manager",
        ]:
            (workers_root / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")

    def test_build_worker_plan_marks_independent_tasks_parallel_eligible(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] PM: refine acceptance criteria
- [ ] Design: validate onboarding flow
- [ ] Data: define activation metric
- [ ] QA: verify regression checklist
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertTrue(plan["parallel"]["eligible"])
            self.assertGreaterEqual(len(plan["tasks"]), 4)
            self.assertEqual(plan["tasks"][0]["worker"], "pm-strategist")
            self.assertTrue(any(task["worker"] == "ux-flow-worker" for task in plan["tasks"]))

    def test_shared_state_tasks_are_sequential(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] Update shared config schema
- [ ] Change state migration handling
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertFalse(plan["parallel"]["eligible"])
            self.assertEqual(plan["parallel"]["mode"], "sequential")
            self.assertTrue(plan["parallel"]["risks"])

    def test_acceptance_verification_routes_to_qa_before_pm(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")

        self.assertEqual(
            orchestrator.assign_worker("Acceptance verification and regression checklist"),
            "qa-reviewer",
        )

    def test_overlapping_expected_files_force_sequential_mode(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] Implementation: update loop command [files: commands/product-loop.md]
- [ ] Release: document loop command [files: commands/product-loop.md]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertFalse(plan["parallel"]["eligible"])
            self.assertEqual(plan["parallel"]["mode"], "sequential")
            self.assertIn("commands/product-loop.md", plan["parallel"]["risks"][0])
            self.assertEqual(plan["tasks"][0]["expected_files"], ["commands/product-loop.md"])

    def test_disjoint_files_include_isolation_and_merge_order(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] PM: refine acceptance criteria [files: specs/023-worker-routing-and-isolation/spec.md]
- [ ] Implementation: update worker planner [files: scripts/worker_orchestrator.py]
- [ ] QA: verify routing tests [files: tests/test_worker_orchestration.py] [depends: T02]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertTrue(plan["parallel"]["eligible"])
            self.assertEqual(plan["tasks"][1]["isolation"]["worktree"], "codex/007-worker-orchestration-t02")
            self.assertEqual(plan["tasks"][2]["dependencies"], ["T02"])
            self.assertEqual(plan["parallel"]["merge_order"], ["T01", "T02", "T03"])

    def test_dead_worker_files_are_reported(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] Implementation: add command wiring [files: scripts/worker_orchestrator.py]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)
            (root / "workers" / "business-planner.md").write_text("# business-planner\n", encoding="utf-8")

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertIn("business-planner", plan["workers"]["dead_workers"])
            self.assertNotIn("implementation-worker", plan["workers"]["dead_workers"])


    def test_write_worker_plan_creates_json_and_markdown(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] Implementation: add command wiring
- [ ] Release: update docs
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            result = orchestrator.write_worker_plan(root, "007-worker-orchestration")

            self.assertEqual(result["written"], ["worker-plan.json", "worker-plan.md"])
            plan_json = root / "specs" / "007-worker-orchestration" / "worker-plan.json"
            plan_md = root / "specs" / "007-worker-orchestration" / "worker-plan.md"
            self.assertTrue(plan_json.exists())
            self.assertTrue(plan_md.exists())
            self.assertEqual(json.loads(plan_json.read_text(encoding="utf-8"))["schema"], "moduflow.worker-plan.v1")


if __name__ == "__main__":
    unittest.main()
