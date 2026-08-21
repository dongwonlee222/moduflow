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
    def test_archived_project_denies_loop_state_write_without_creating_file(self):
        project_registry = load_module("project_registry_loop", "scripts/project_registry.py")
        project_operation = load_module("project_operation_loop", "scripts/project_operation.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = project_registry.project_context_for_root(root)
            context.update(project_operation.compute_project_policy("archived", "internal"))

            with self.assertRaisesRegex(Exception, "Archived projects are read-only"):
                project_loop.write_loop_state(
                    root,
                    project_loop.default_loop_state(root),
                    project_context=context,
                )

            self.assertFalse((root / "workspace" / "loop-state.json").exists())

    def write_loop_state(
        self,
        root,
        issue_id,
        *,
        delegation_level="full",
        backend_status="approved",
        attempts=1,
    ):
        (root / "workspace").mkdir(exist_ok=True)
        (root / "workspace" / "loop-state.json").write_text(
            json.dumps(
                {
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": [issue_id],
                    "active_issue_id": issue_id,
                    "delegation_level": delegation_level,
                    "status": "active",
                    "next_command": f"product:execute {issue_id}",
                    "attempts": {
                        "command": f"product:execute {issue_id}",
                        "count": attempts,
                        "max": 3,
                    },
                    "git_binding": {
                        "execution_backend": {
                            "type": "codex",
                            "status": backend_status,
                        }
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def write_versioned_issue(
        self,
        root,
        issue_id,
        *,
        lifecycle="backlog",
        definition="ready",
        gate="passed",
        dependencies=(),
        phase=None,
        next_command=None,
    ):
        (root / "issues").mkdir(exist_ok=True)
        status = {
            "backlog": "backlog",
            "active": "in_progress",
            "done": "done",
        }[lifecycle]
        phase_line = f"phase: {phase}\n" if phase else ""
        dependency_text = ", ".join(dependencies)
        next_command = next_command or f"product:execute {issue_id}"
        (root / "issues" / f"{issue_id}.md").write_text(
            f"""---
schema_version: 0.1.0
issue_id: {issue_id}
canonical_state: {lifecycle}
status: {status}
priority: p2
definition_readiness: {definition}
gate_state: {gate}
{phase_line}depends_on: [{dependency_text}]
next_command: {next_command}
---
# Issue: `{issue_id}` Loop fixture

**Status: {lifecycle}** — created 2026-07-24.
""",
            encoding="utf-8",
        )

    def add_artifacts(self, root, issue_id, *names):
        artifact_root = root / "specs" / issue_id
        artifact_root.mkdir(parents=True, exist_ok=True)
        for name in names:
            (artifact_root / f"{name}.md").write_text(
                f"# {name.title()}\n", encoding="utf-8"
            )

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
            self.add_artifacts(root, "019-loop-kernel-and-state-model", "spec")

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["active_issue_id"], "019-loop-kernel-and-state-model")
            self.assertEqual(result["phase"], "plan")
            self.assertEqual(result["next_command"], "product:plan 019-loop-kernel-and-state-model")
            self.assertEqual(result["status"], "needs_decision")
            self.assertIn("Missing structural artifact", result["blocker"])

    def test_recommend_loop_routes_not_ready_execute_phase_back_to_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "077-implementation-readiness-gate"
            (root / "workspace").mkdir()
            (root / "issues").mkdir()
            spec_dir = root / "specs" / issue_id
            spec_dir.mkdir(parents=True)
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": [issue_id],
                    "active_issue_id": issue_id,
                    "status": "active",
                    "next_command": f"product:execute {issue_id}",
                    "attempts": {"command": f"product:execute {issue_id}", "count": 1, "max": 3},
                }) + "\n",
                encoding="utf-8",
            )
            (root / "issues" / f"{issue_id}.md").write_text(
                f"# Issue\n\n## Workflow Tasks\n\n"
                f"- [x] spec → `specs/{issue_id}/spec.md`\n"
                f"- [x] plan → `specs/{issue_id}/plan.md`\n"
                f"- [ ] execute → implementation\n",
                encoding="utf-8",
            )
            (spec_dir / "implementation-readiness.json").write_text(
                json.dumps({
                    "schema": "moduflow.implementation-readiness.v1",
                    "issue_id": issue_id,
                    "status": "not_ready",
                    "mode": "report-only",
                    "checks": [],
                    "next_command": f"product:plan {issue_id}",
                }) + "\n",
                encoding="utf-8",
            )
            self.add_artifacts(root, issue_id, "spec", "plan", "tasks")

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["phase"], "plan")
            self.assertEqual(result["next_command"], f"product:plan {issue_id}")
            self.assertEqual(result["status"], "needs_decision")
            self.assertIn("Implementation readiness is not_ready", result["blocker"])

    def test_structural_gate_routes_before_issue_077_and_delegation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocker_id = "BIZ-090"
            issue_id = "BIZ-093"
            self.write_versioned_issue(root, blocker_id)
            self.write_versioned_issue(
                root,
                issue_id,
                dependencies=(blocker_id,),
                next_command=f"product:execute {issue_id}",
            )
            self.add_artifacts(root, issue_id, "spec", "plan", "tasks")
            self.write_loop_state(
                root,
                issue_id,
                delegation_level="manual",
                attempts=2,
            )
            readiness_path = root / "specs" / issue_id / "implementation-readiness.json"
            readiness_path.write_text(
                json.dumps(
                    {
                        "schema": "moduflow.implementation-readiness.v1",
                        "issue_id": issue_id,
                        "status": "not_ready",
                        "next_command": f"product:plan {issue_id}",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["phase"], "status")
            self.assertEqual(result["status"], "needs_decision")
            self.assertEqual(result["next_command"], "product:status")
            self.assertNotIn("product:execute", result["next_command"])
            self.assertIn("ISSUE_DEPENDENCY_UNMET", result["blocker"])
            self.assertNotIn("Implementation readiness", result["blocker"])
            self.assertNotIn("delegation_level", result["blocker"])
            self.assertEqual(result["attempts"]["count"], 2)

    def test_structural_ready_advances_to_review_without_execution_approval_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "BIZ-REVIEW"
            self.write_versioned_issue(root, issue_id)
            issue_path = root / "issues" / f"{issue_id}.md"
            issue_path.write_text(
                issue_path.read_text(encoding="utf-8")
                + """
## Workflow Tasks

- [x] spec
- [x] plan
- [x] execute
- [ ] review
""",
                encoding="utf-8",
            )
            self.add_artifacts(root, issue_id, "spec", "plan", "tasks")
            self.write_loop_state(
                root,
                issue_id,
                delegation_level="review_required",
                backend_status="not_selected",
            )

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["phase"], "review")
            self.assertEqual(result["status"], "active")
            self.assertEqual(result["next_command"], f"product:review {issue_id}")
            self.assertIsNone(result["blocker"])

    def test_structural_ready_execute_pending_still_requires_execution_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "BIZ-EXECUTE"
            self.write_versioned_issue(root, issue_id)
            issue_path = root / "issues" / f"{issue_id}.md"
            issue_path.write_text(
                issue_path.read_text(encoding="utf-8")
                + """
## Workflow Tasks

- [x] spec
- [x] plan
- [ ] execute
- [ ] review
""",
                encoding="utf-8",
            )
            self.add_artifacts(root, issue_id, "spec", "plan", "tasks")
            self.write_loop_state(
                root,
                issue_id,
                delegation_level="review_required",
                backend_status="not_selected",
            )

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["phase"], "execute")
            self.assertEqual(result["status"], "needs_decision")
            self.assertEqual(result["next_command"], f"product:execute {issue_id}")
            self.assertIn("Execution blocked", result["blocker"])

    def test_structural_routes_derive_phase_from_shared_command(self):
        cases = (
            ("BIZ-DRAFT", {"definition": "draft"}, (), "spec", "product:spec BIZ-DRAFT"),
            ("BIZ-NO-PLAN", {}, ("spec",), "plan", "product:plan BIZ-NO-PLAN"),
            (
                "BIZ-NO-TASKS",
                {},
                ("spec", "plan"),
                "plan",
                "product:plan BIZ-NO-TASKS",
            ),
            (
                "BIZ-PHASE-DRIFT",
                {"phase": "release"},
                ("spec", "plan", "tasks"),
                "status",
                "product:doctor",
            ),
            (
                "BIZ-GATE-PENDING",
                {"gate": "pending"},
                ("spec", "plan", "tasks"),
                "review",
                "product:review BIZ-GATE-PENDING",
            ),
        )
        for issue_id, issue_options, artifacts, phase, command in cases:
            with self.subTest(issue_id=issue_id), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.write_versioned_issue(
                    root,
                    issue_id,
                    next_command=command,
                    **issue_options,
                )
                self.add_artifacts(root, issue_id, *artifacts)
                self.write_loop_state(root, issue_id)

                result = project_loop.recommend_loop(root)

                self.assertEqual(result["phase"], phase)
                self.assertEqual(result["status"], "needs_decision")
                self.assertEqual(result["next_command"], command)
                self.assertNotIn("product:execute", result["next_command"])
                self.assertTrue(result["blocker"])
                if issue_id in {"BIZ-NO-PLAN", "BIZ-NO-TASKS"}:
                    self.assertIn("Missing structural artifact", result["blocker"])
                if issue_id == "BIZ-PHASE-DRIFT":
                    self.assertIn("ISSUE_STATE_PROJECTION_MISMATCH", result["blocker"])

    def test_unsupported_schema_blocks_but_unversioned_issue_remains_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "BIZ-UNSUPPORTED"
            self.write_versioned_issue(root, issue_id)
            issue_path = root / "issues" / f"{issue_id}.md"
            issue_path.write_text(
                issue_path.read_text(encoding="utf-8").replace(
                    "schema_version: 0.1.0", "schema_version: 9.9.9"
                ),
                encoding="utf-8",
            )
            self.add_artifacts(root, issue_id, "spec", "plan", "tasks")
            self.write_loop_state(root, issue_id)

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["phase"], "status")
            self.assertEqual(result["next_command"], "product:doctor")
            self.assertIn("ISSUE_SCHEMA_UNSUPPORTED", result["blocker"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "BIZ-UNVERSIONED"
            (root / "issues").mkdir()
            (root / "issues" / f"{issue_id}.md").write_text(
                f"""---
issue_id: {issue_id}
definition_readiness: ready
gate_state: passed
---
# Advisory issue

**Status: backlog** — created 2026-07-24.

## Workflow Tasks

- [x] spec
- [x] plan
- [ ] execute
- [ ] review
""",
                encoding="utf-8",
            )
            self.add_artifacts(root, issue_id, "spec", "plan", "tasks")
            self.write_loop_state(root, issue_id)

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["phase"], "execute")
            self.assertEqual(result["next_command"], f"product:execute {issue_id}")
            self.assertEqual(result["status"], "active")

    def test_missing_active_issue_keeps_legacy_recommendation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "missing-issue"
            self.write_loop_state(root, issue_id)

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["phase"], "issue")
            self.assertEqual(result["next_command"], "product:status")

    def test_unsafe_configured_issues_root_blocks_before_phase_inference(self):
        for unsafe_root_kind in ("parent", "absolute", "external-symlink"):
            with (
                self.subTest(unsafe_root_kind=unsafe_root_kind),
                tempfile.TemporaryDirectory() as tmp,
            ):
                base = Path(tmp)
                root = base / "project"
                outside_issues = base / "outside-issues"
                root.mkdir()
                outside_issues.mkdir()
                self.write_loop_state(root, "BIZ-UNSAFE-ROOT")

                if unsafe_root_kind == "external-symlink":
                    (root / "issues").symlink_to(
                        outside_issues,
                        target_is_directory=True,
                    )
                else:
                    (root / ".moduflow").mkdir()
                    configured_issues = (
                        "../outside-issues"
                        if unsafe_root_kind == "parent"
                        else str(outside_issues)
                    )
                    (root / ".moduflow" / "config.json").write_text(
                        json.dumps(
                            {
                                "schema": "moduflow.config.v1",
                                "paths": {"issues": configured_issues},
                            }
                        )
                        + "\n",
                        encoding="utf-8",
                    )

                result = project_loop.recommend_loop(root)

                self.assertEqual(result["phase"], "status")
                self.assertEqual(result["status"], "needs_decision")
                self.assertEqual(result["next_command"], "product:doctor")
                self.assertIn("ISSUE_SOURCE_OUTSIDE_ROOT", result["blocker"])
                self.assertIn(
                    "Configured issues root resolves outside the project root.",
                    result["blocker"],
                )
                self.assertIn(
                    "Replace the external issues path or directory symlink",
                    result["blocker"],
                )

    def test_recommend_loop_uses_configured_issue_and_spec_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "BIZ-CUSTOM"
            self.write_versioned_issue(root, issue_id)
            issue_path = root / "issues" / f"{issue_id}.md"
            issue_path.write_text(
                issue_path.read_text(encoding="utf-8")
                + """
## Workflow Tasks

- [x] spec
- [x] plan
- [ ] execute
- [ ] review
""",
                encoding="utf-8",
            )
            self.add_artifacts(root, issue_id, "spec", "plan", "tasks")
            custom_root = root / "projects" / "billing"
            custom_root.mkdir(parents=True)
            (root / "issues").rename(custom_root / "issues")
            (root / "specs").rename(custom_root / "specs")
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.config.v1",
                        "paths": {
                            "issues": "projects/billing/issues",
                            "specs": "projects/billing/specs",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            self.write_loop_state(root, issue_id)

            result = project_loop.recommend_loop(root)
            loop_errors = project_loop.validate_loop_state(root)

        self.assertEqual(result["phase"], "execute")
        self.assertEqual(
            result["next_command"], f"product:execute {issue_id}"
        )
        self.assertEqual(result["status"], "active")
        self.assertEqual(loop_errors, [])

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

    def test_loop_state_read_and_write_use_configured_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {"paths": {"workspace": "product/workspace"}}
                ),
                encoding="utf-8",
            )
            workspace = root / "product" / "workspace"
            workspace.mkdir(parents=True)
            (workspace / "loop-state.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.loop-state.v2",
                        "goal_id": "configured-goal",
                        "issue_ids": [],
                        "active_issue_id": None,
                        "status": "active",
                        "next_command": "product:goal",
                    }
                ),
                encoding="utf-8",
            )
            default_workspace = root / "workspace"
            default_workspace.mkdir()
            decoy = default_workspace / "loop-state.json"
            decoy.write_text(
                json.dumps({"goal_id": "wrong-goal"}), encoding="utf-8"
            )

            state = project_loop.load_loop_state(root)
            state["last_action"] = "configured-write"
            written = project_loop.write_loop_state(root, state)

            self.assertEqual(state["goal_id"], "configured-goal")
            self.assertEqual(written, (workspace / "loop-state.json").resolve())
            self.assertIn(
                "configured-write",
                (workspace / "loop-state.json").read_text(encoding="utf-8"),
            )
            self.assertNotIn("configured-write", decoy.read_text(encoding="utf-8"))

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

    def test_recommend_execution_backend_prefers_host_subagent(self):
        backend = project_loop.recommend_execution_backend(
            task_type="code", risk="medium", github_available=False, host_supports_subagents=True
        )
        self.assertEqual(backend["type"], "host-subagent")
        self.assertEqual(backend["status"], "recommended")
        self.assertIn("host execution", backend["reason"])

    def test_load_loop_state_normalizes_delegation_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["019-loop-kernel-and-state-model"],
                    "active_issue_id": "019-loop-kernel-and-state-model",
                    "delegation_level": "invalid_level",
                    "next_command": "product:loop",
                }) + "\n",
                encoding="utf-8",
            )
            state = project_loop.load_loop_state(root)
            self.assertEqual(state["delegation_level"], "review_required")

            # Check that a valid one is preserved
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["019-loop-kernel-and-state-model"],
                    "active_issue_id": "019-loop-kernel-and-state-model",
                    "delegation_level": "manual",
                    "next_command": "product:loop",
                }) + "\n",
                encoding="utf-8",
            )
            state = project_loop.load_loop_state(root)
            self.assertEqual(state["delegation_level"], "manual")

    def test_recommend_loop_blocks_when_manual_or_unapproved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()
            # We mock the issue file so phase is inferred as 'execute'
            # (checked spec/plan done, execute pending)
            (root / "issues" / "037-test.md").write_text(
                "- [x] spec\n- [x] plan\n- [ ] execute\n",
                encoding="utf-8",
            )
            self.add_artifacts(root, "037-test", "spec", "plan", "tasks")

            # 1. delegation_level = manual should always block
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["037-test"],
                    "active_issue_id": "037-test",
                    "delegation_level": "manual",
                    "next_command": "product:execute 037-test",
                    "git_binding": {
                        "execution_backend": {
                            "type": "codex",
                            "status": "approved"
                        }
                    }
                }) + "\n",
                encoding="utf-8",
            )

            state = project_loop.recommend_loop(root)
            self.assertEqual(state["status"], "needs_decision")
            self.assertIn("Execution blocked", state["blocker"])

            # 2. delegation_level = review_required and status != approved should block
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["037-test"],
                    "active_issue_id": "037-test",
                    "delegation_level": "review_required",
                    "next_command": "product:execute 037-test",
                    "git_binding": {
                        "execution_backend": {
                            "type": "codex",
                            "status": "not_selected"
                        }
                    }
                }) + "\n",
                encoding="utf-8",
            )

            state = project_loop.recommend_loop(root)
            self.assertEqual(state["status"], "needs_decision")
            self.assertIn("Execution blocked", state["blocker"])

    def test_invalid_issue_ids_fail_closed_before_issue_or_artifact_lookup(self):
        invalid_issue_ids = (
            "../../outside",
            "/tmp/outside",
            "folder/issue",
            r"folder\issue",
            ".",
            "..",
        )
        for issue_id in invalid_issue_ids:
            with self.subTest(issue_id=issue_id), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.write_loop_state(root, issue_id)

                state = project_loop.recommend_loop(root)
                errors = project_loop.validate_loop_state(root)

                self.assertEqual(state["status"], "needs_decision")
                self.assertEqual(state["next_command"], "product:doctor")
                self.assertNotIn("product:execute", state["next_command"])
                self.assertIn("Invalid active_issue_id", state["blocker"])
                self.assertTrue(
                    any("invalid active_issue_id" in error for error in errors)
                )
                self.assertTrue(
                    any("invalid issue_id" in error for error in errors)
                )
                with self.assertRaises(ValueError):
                    project_loop.issue_path(root, issue_id)

    def test_invalid_secondary_issue_id_blocks_valid_active_issue_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_loop_state(root, "BIZ-SAFE")
            state_path = root / "workspace" / "loop-state.json"
            raw = json.loads(state_path.read_text(encoding="utf-8"))
            raw["issue_ids"] = ["BIZ-SAFE", "../../outside"]
            state_path.write_text(
                json.dumps(raw) + "\n",
                encoding="utf-8",
            )
            self.write_versioned_issue(root, "BIZ-SAFE")
            self.add_artifacts(root, "BIZ-SAFE", "spec", "plan", "tasks")

            state = project_loop.recommend_loop(root)
            errors = project_loop.validate_loop_state(root)

        self.assertEqual(state["status"], "needs_decision")
        self.assertEqual(state["next_command"], "product:doctor")
        self.assertIn("Invalid issue_ids", state["blocker"])
        self.assertTrue(any("invalid issue_id" in error for error in errors))

    def test_structural_blocker_preserves_outside_root_diagnostics(self):
        for code in (
            "ISSUE_SOURCE_OUTSIDE_ROOT",
            "ISSUE_ARTIFACT_OUTSIDE_ROOT",
        ):
            with self.subTest(code=code):
                issue = {
                    "issue_id": "BIZ-SYMLINK",
                    "readiness": "blocked",
                    "recommended_next_command": "product:doctor",
                    "diagnostics": [
                        {
                            "code": code,
                            "source_path": "issues/BIZ-SYMLINK.md",
                            "message": "Symlink target is outside the configured root.",
                            "recommendation": "Replace the external symlink.",
                        }
                    ],
                }

                blocker = project_loop.structural_blocker(Path("."), issue)

                self.assertIn(code, blocker)
                self.assertIn(
                    "Symlink target is outside the configured root.",
                    blocker,
                )
                self.assertIn("Replace the external symlink.", blocker)

    def test_checkbox_less_issue_reaches_execute_phase_but_stays_gated(self):
        """Pin the a50947b default flip so it cannot become fail-open.

        infer_issue_phase now returns "execute" instead of "status" for an
        issue carrying no workflow checkboxes. That is only safe because a
        gate still stands between the phase and actually executing: a missing
        implementation-readiness.json must never read as approval.
        """
        issue_id = "019-loop-kernel-and-state-model"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": [issue_id],
                    "active_issue_id": issue_id,
                    "status": "active",
                    "next_command": f"product:spec {issue_id}",
                    "attempts": {"command": "x", "count": 1, "max": 3},
                }) + "\n",
                encoding="utf-8",
            )
            (root / "issues").mkdir()
            (root / "issues" / f"{issue_id}.md").write_text(
                "# Issue 019\n\n**Status: active**\n\n## Summary\n\nNo workflow checkboxes.\n",
                encoding="utf-8",
            )
            self.add_artifacts(root, issue_id, "spec", "plan", "tasks")
            self.assertFalse(
                (root / "specs" / issue_id / "implementation-readiness.json").exists()
            )

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["phase"], "execute")
            self.assertEqual(result["status"], "needs_decision")
            self.assertTrue(result["blocker"])

    def test_directory_shaped_issue_file_fails_closed_instead_of_raising(self):
        """A `*.md` directory must route to doctor, not raise out of the loop.

        The schema layer used to skip non-file sources silently, which left
        infer_issue_phase to call read_text() on a directory and raise
        IsADirectoryError out of recommend_loop.
        """
        issue_id = "019-loop-kernel-and-state-model"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": [issue_id],
                    "active_issue_id": issue_id,
                    "status": "active",
                    "next_command": f"product:spec {issue_id}",
                    "attempts": {"command": "x", "count": 1, "max": 3},
                }) + "\n",
                encoding="utf-8",
            )
            (root / "issues").mkdir()
            (root / "issues" / f"{issue_id}.md").mkdir()
            self.add_artifacts(root, issue_id, "spec", "plan", "tasks")

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["status"], "needs_decision")
            self.assertEqual(result["next_command"], "product:doctor")
            self.assertIn("ISSUE_SOURCE_UNREADABLE", result["blocker"])


if __name__ == "__main__":
    unittest.main()
