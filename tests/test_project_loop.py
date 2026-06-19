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


project_loop = load_module("project_loop", "scripts/project_loop.py")


class ProjectLoopTests(unittest.TestCase):
    def test_load_loop_state_reads_v1_issue_id_as_active_issue_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v1",
                    "goal_id": "goal-a",
                    "issue_id": "019-loop-kernel-and-state-model",
                    "phase": "goal",
                    "mode": "recommend",
                    "next_command": "product:loop",
                    "attempts": 0,
                    "status": "active",
                }) + "\n",
                encoding="utf-8",
            )

            state = project_loop.load_loop_state(root)

            self.assertEqual(state["schema"], "moduflow.loop-state.v2")
            self.assertEqual(state["goal_id"], "goal-a")
            self.assertEqual(state["issue_ids"], ["019-loop-kernel-and-state-model"])
            self.assertEqual(state["active_issue_id"], "019-loop-kernel-and-state-model")
            self.assertEqual(state["attempts"]["count"], 0)

    def test_load_loop_state_reads_v2_issue_ids_and_active_cursor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["019-loop-kernel-and-state-model", "020-user-facing-simple-loop-ux"],
                    "active_issue_id": "020-user-facing-simple-loop-ux",
                    "phase": "spec",
                    "mode": "recommend",
                    "next_command": "product:plan 020-user-facing-simple-loop-ux",
                    "attempts": {"command": "product:plan 020-user-facing-simple-loop-ux", "count": 1, "max": 3},
                    "status": "active",
                }) + "\n",
                encoding="utf-8",
            )

            state = project_loop.load_loop_state(root)

            self.assertEqual(state["issue_ids"], ["019-loop-kernel-and-state-model", "020-user-facing-simple-loop-ux"])
            self.assertEqual(state["active_issue_id"], "020-user-facing-simple-loop-ux")
            self.assertEqual(state["attempts"]["max"], 3)

    def test_infer_issue_phase_returns_plan_after_spec_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_dir = root / "issues"
            issue_dir.mkdir()
            (issue_dir / "019-loop-kernel-and-state-model.md").write_text(
                """# Issue 019\n\n## Workflow Tasks\n\n- [x] spec → `specs/019-loop-kernel-and-state-model/spec.md`\n- [ ] plan → `specs/019-loop-kernel-and-state-model/plan.md`\n- [ ] execute → loop kernel/state model implementation\n""",
                encoding="utf-8",
            )
            (root / "specs" / "019-loop-kernel-and-state-model").mkdir(parents=True)
            (root / "specs" / "019-loop-kernel-and-state-model" / "spec.md").write_text("# Spec\n", encoding="utf-8")

            phase = project_loop.infer_issue_phase(root, "019-loop-kernel-and-state-model")
            command = project_loop.recommend_next_command("019-loop-kernel-and-state-model", phase)

            self.assertEqual(phase, "plan")
            self.assertEqual(command, "product:plan 019-loop-kernel-and-state-model")

    def test_infer_issue_phase_returns_execute_after_plan_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_dir = root / "issues"
            issue_dir.mkdir()
            (issue_dir / "019-loop-kernel-and-state-model.md").write_text(
                """# Issue 019\n\n## Workflow Tasks\n\n- [x] spec → `specs/019-loop-kernel-and-state-model/spec.md`\n- [x] plan → `specs/019-loop-kernel-and-state-model/plan.md`\n- [ ] execute → loop kernel/state model implementation\n- [ ] review → loop state drift and attempts guard tests\n""",
                encoding="utf-8",
            )

            phase = project_loop.infer_issue_phase(root, "019-loop-kernel-and-state-model")
            command = project_loop.recommend_next_command("019-loop-kernel-and-state-model", phase)

            self.assertEqual(phase, "execute")
            self.assertEqual(command, "product:execute 019-loop-kernel-and-state-model")

    def test_attempts_guard_sets_needs_decision_after_repeated_command(self):
        state = {
            "schema": "moduflow.loop-state.v2",
            "goal_id": "goal-a",
            "issue_ids": ["019-loop-kernel-and-state-model"],
            "active_issue_id": "019-loop-kernel-and-state-model",
            "phase": "plan",
            "status": "active",
            "next_command": "product:plan 019-loop-kernel-and-state-model",
            "attempts": {"command": "product:plan 019-loop-kernel-and-state-model", "count": 3, "max": 3},
        }

        updated = project_loop.apply_attempts_guard(state, "product:plan 019-loop-kernel-and-state-model")

        self.assertEqual(updated["status"], "needs_decision")
        self.assertEqual(updated["blocker"], "Repeated next command exceeded max attempts: product:plan 019-loop-kernel-and-state-model")

    def test_attempts_guard_resets_count_for_new_command(self):
        state = {
            "schema": "moduflow.loop-state.v2",
            "goal_id": "goal-a",
            "issue_ids": ["019-loop-kernel-and-state-model"],
            "active_issue_id": "019-loop-kernel-and-state-model",
            "status": "active",
            "next_command": "product:spec 019-loop-kernel-and-state-model",
            "attempts": {"command": "product:spec 019-loop-kernel-and-state-model", "count": 2, "max": 3},
        }

        updated = project_loop.apply_attempts_guard(state, "product:plan 019-loop-kernel-and-state-model")

        self.assertEqual(updated["status"], "active")
        self.assertEqual(updated["attempts"]["count"], 1)
        self.assertEqual(updated["attempts"]["command"], "product:plan 019-loop-kernel-and-state-model")

    def test_recommend_loop_reports_active_issue_phase_and_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["019-loop-kernel-and-state-model"],
                    "active_issue_id": "019-loop-kernel-and-state-model",
                    "status": "active",
                    "next_command": "product:spec 019-loop-kernel-and-state-model",
                    "attempts": {"command": "product:spec 019-loop-kernel-and-state-model", "count": 1, "max": 3},
                }) + "\n",
                encoding="utf-8",
            )
            (root / "issues").mkdir()
            (root / "issues" / "019-loop-kernel-and-state-model.md").write_text(
                """# Issue 019\n\n## Workflow Tasks\n\n- [x] spec → `specs/019-loop-kernel-and-state-model/spec.md`\n- [ ] plan → `specs/019-loop-kernel-and-state-model/plan.md`\n""",
                encoding="utf-8",
            )

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["active_issue_id"], "019-loop-kernel-and-state-model")
            self.assertEqual(result["phase"], "plan")
            self.assertEqual(result["next_command"], "product:plan 019-loop-kernel-and-state-model")
            self.assertEqual(result["status"], "active")

    def test_write_loop_state_persists_v2_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = project_loop.normalize_loop_state({
                "goal_id": "goal-a",
                "issue_ids": ["019-loop-kernel-and-state-model"],
                "active_issue_id": "019-loop-kernel-and-state-model",
                "next_command": "product:plan 019-loop-kernel-and-state-model",
            })

            project_loop.write_loop_state(root, state)
            saved = json.loads((root / "workspace" / "loop-state.json").read_text(encoding="utf-8"))

            self.assertEqual(saved["schema"], "moduflow.loop-state.v2")
            self.assertEqual(saved["active_issue_id"], "019-loop-kernel-and-state-model")

    def test_validate_loop_state_reports_missing_active_issue_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["missing-issue"],
                    "active_issue_id": "missing-issue",
                    "next_command": "product:spec missing-issue",
                    "status": "active",
                }) + "\n",
                encoding="utf-8",
            )

            errors = project_loop.validate_loop_state(root)

            self.assertIn("workspace/loop-state.json: active_issue_id missing-issue has no matching issue file", errors)


    def test_recommend_issue_branch_uses_codex_prefix_and_issue_id(self):
        branch = project_loop.recommend_issue_branch("021-git-binding-and-execution-backend")

        self.assertEqual(branch, "codex/021-git-binding-and-execution-backend")

    def test_normalize_loop_state_preserves_git_binding(self):
        state = project_loop.normalize_loop_state({
            "goal_id": "goal-a",
            "issue_ids": ["021-git-binding-and-execution-backend"],
            "active_issue_id": "021-git-binding-and-execution-backend",
            "next_command": "product:execute 021-git-binding-and-execution-backend",
            "git_binding": {
                "branch": "codex/021-git-binding-and-execution-backend",
                "base_branch": "main",
                "commits": ["abc1234"],
                "pull_request": "https://github.com/example/repo/pull/21",
                "release": "v0.2.8",
                "execution_backend": {
                    "type": "codex",
                    "status": "recommended",
                },
            },
        })

        self.assertEqual(state["git_binding"]["mode"], "git-files")
        self.assertEqual(state["git_binding"]["branch"], "codex/021-git-binding-and-execution-backend")
        self.assertEqual(state["git_binding"]["commits"], ["abc1234"])
        self.assertEqual(state["git_binding"]["execution_backend"]["type"], "codex")

    def test_validate_loop_state_reports_declared_branch_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()
            (root / "issues" / "021-git-binding-and-execution-backend.md").write_text("# Issue 021\n", encoding="utf-8")
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["021-git-binding-and-execution-backend"],
                    "active_issue_id": "021-git-binding-and-execution-backend",
                    "next_command": "product:execute 021-git-binding-and-execution-backend",
                    "status": "active",
                    "git_binding": {
                        "branch": "codex/020-user-facing-simple-loop-ux",
                    },
                }) + "\n",
                encoding="utf-8",
            )

            errors = project_loop.validate_loop_state(root)

            self.assertIn(
                "workspace/loop-state.json: git_binding.branch codex/020-user-facing-simple-loop-ux does not match active_issue_id 021-git-binding-and-execution-backend",
                errors,
            )

    def test_recommend_execution_backend_prefers_manual_for_high_risk(self):
        backend = project_loop.recommend_execution_backend(task_type="code", risk="high", github_available=True)

        self.assertEqual(backend["type"], "manual")
        self.assertEqual(backend["reason"], "high-risk work needs explicit human control")


if __name__ == "__main__":
    unittest.main()
