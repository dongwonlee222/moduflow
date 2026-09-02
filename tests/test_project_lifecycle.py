import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def valid_transaction_validation():
    return mock.patch(
        "validate_project_artifacts.validate_project",
        return_value={
            "schema": "moduflow.project-validation.v1",
            "valid": True,
            "errors": [],
            "warnings": [],
            "issue_schema": {"errors": 0, "warnings": 0},
            "lifecycle_drift": [],
        },
    )


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
    (root / "workspace" / "loop-state.json").write_text(
        json.dumps(
            {
                "schema": "moduflow.loop-state.v2",
                "goal_id": "g",
                "issue_ids": [state_active] if state_active else [],
                "active_issue_id": state_active or None,
                "status": "active",
                "next_command": "product:status",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "workspace" / "transactions").mkdir()


class ProjectLifecycleTests(unittest.TestCase):
    def test_transition_lifecycle_builds_one_exact_intent_and_returns_engine_result(self):
        lc = load_module("project_lifecycle_adapter", "scripts/project_lifecycle.py")
        expected = {
            "schema": "moduflow.lifecycle-transaction.v1",
            "status": "noop",
        }
        for action, target in (
            ("start", None),
            ("update", "active"),
            ("pause", None),
            ("resume", None),
            ("complete", None),
        ):
            with self.subTest(action=action):
                apply = mock.Mock(return_value=expected)
                boundary = SimpleNamespace(
                    LifecycleIntent=lambda **values: SimpleNamespace(**values),
                    apply_lifecycle_transaction=apply,
                )
                injector = lambda _stage: None
                context = {"project_id": "project-103"}
                with mock.patch.object(
                    lc,
                    "_load_lifecycle_transaction_module",
                    return_value=boundary,
                ):
                    result = lc.transition_lifecycle(
                        "/project",
                        "BIZ-103",
                        action,
                        actor="dongwon",
                        source_event="request:C1a",
                        target_status=target,
                        idempotency_key="a" * 64,
                        expected_issue_sha256="b" * 64,
                        loop_blocker="waiting",
                        require_issue_index=True,
                        project_context=context,
                        clock="clock",
                        fault_injector=injector,
                    )

                intent = apply.call_args.args[1]
                self.assertEqual(intent.issue_id, "BIZ-103")
                self.assertEqual(intent.action, action)
                self.assertEqual(intent.target_lifecycle, target)
                self.assertIsNone(intent.roadmap_change)
                self.assertEqual(intent.actor, "dongwon")
                self.assertEqual(intent.source_event, "request:C1a")
                self.assertEqual(intent.idempotency_key, "a" * 64)
                self.assertEqual(intent.expected_issue_sha256, "b" * 64)
                self.assertEqual(intent.loop_blocker, "waiting")
                self.assertTrue(intent.require_issue_index)
                apply.assert_called_once_with(
                    "/project",
                    intent,
                    project_context=context,
                    clock="clock",
                    fault_injector=injector,
                )
                self.assertIs(result, expected)

    def test_transition_lifecycle_rejects_invalid_public_inputs_before_engine(self):
        lc = load_module("project_lifecycle_adapter_invalid", "scripts/project_lifecycle.py")
        invalid = (
            {"issue_id": "BIZ-103", "action": "reconcile", "actor": "a", "source_event": "s"},
            {"issue_id": "", "action": "start", "actor": "a", "source_event": "s"},
            {"issue_id": "BIZ-103", "action": "start", "actor": "", "source_event": "s"},
            {"issue_id": "BIZ-103", "action": "start", "actor": "a", "source_event": ""},
        )
        with mock.patch.object(lc, "_load_lifecycle_transaction_module") as load:
            for values in invalid:
                with self.subTest(values=values), self.assertRaises(ValueError):
                    lc.transition_lifecycle("/project", **values)
        load.assert_not_called()

    def test_transition_lifecycle_maps_priority_to_one_roadmap_change(self):
        lc = load_module(
            "project_lifecycle_priority_adapter", "scripts/project_lifecycle.py"
        )
        expected = {
            "schema": "moduflow.lifecycle-transaction.v1",
            "status": "applied",
        }
        apply = mock.Mock(return_value=expected)
        boundary = SimpleNamespace(
            LifecycleIntent=lambda **values: SimpleNamespace(**values),
            apply_lifecycle_transaction=apply,
        )
        with mock.patch.object(
            lc,
            "_load_lifecycle_transaction_module",
            return_value=boundary,
        ):
            result = lc.transition_lifecycle(
                "/project",
                "BIZ-103",
                "update",
                actor="dongwon",
                source_event="request:C1e",
                priority="p1",
            )

        intent = apply.call_args.args[1]
        self.assertEqual(intent.roadmap_change, {"priority": "p1"})
        self.assertIs(result, expected)

    def test_transition_lifecycle_rejects_invalid_priority_before_engine(self):
        lc = load_module(
            "project_lifecycle_invalid_priority", "scripts/project_lifecycle.py"
        )
        with mock.patch.object(lc, "_load_lifecycle_transaction_module") as load:
            with self.assertRaisesRegex(ValueError, "roadmap priority"):
                lc.transition_lifecycle(
                    "/project",
                    "BIZ-103",
                    "update",
                    actor="dongwon",
                    source_event="request:C1e",
                    priority="urgent",
                )
        load.assert_not_called()

    def test_transition_lifecycle_adapter_owns_no_direct_file_mutation(self):
        lc = load_module("project_lifecycle_adapter_no_write", "scripts/project_lifecycle.py")
        boundary = SimpleNamespace(
            LifecycleIntent=lambda **values: SimpleNamespace(**values),
            apply_lifecycle_transaction=mock.Mock(
                return_value={"schema": "transaction", "status": "noop"}
            ),
        )
        with (
            mock.patch.object(
                lc,
                "_load_lifecycle_transaction_module",
                return_value=boundary,
            ),
            mock.patch.object(Path, "write_text") as write_text,
            mock.patch.object(Path, "write_bytes") as write_bytes,
            mock.patch("os.replace") as replace_file,
            mock.patch("os.unlink") as unlink_file,
        ):
            lc.transition_lifecycle(
                "/project",
                "BIZ-103",
                "start",
                actor="dongwon",
                source_event="request:C1a",
            )

        boundary.apply_lifecycle_transaction.assert_called_once()
        write_text.assert_not_called()
        write_bytes.assert_not_called()
        replace_file.assert_not_called()
        unlink_file.assert_not_called()

    def test_pure_renderers_transition_issue_and_preserve_unmanaged_bytes(self):
        lc = load_module("project_lifecycle_renderers", "scripts/project_lifecycle.py")
        issue = (
            b"# Issue: `BIZ-103`\n\n"
            b"**Status: backlog** \xe2\x80\x94 created 2029-12-01.\n\n"
            b"## Notes\n\nPreserve exactly.\n"
        )
        dashboard = (
            b"# Dashboard\n\n## Active Issue\n\n- None active.\n\n"
            b"## Notes\n\nPreserve exactly.\n"
        )

        rendered_issue = lc.render_issue_transition(
            issue, "active", changed_on="2030-01-02"
        )
        rendered_dashboard = lc.render_dashboard_projection(
            dashboard,
            active_issue="BIZ-103",
            phase="execute",
            source_path="product/issues/BIZ-103.md",
        )

        self.assertEqual(
            rendered_issue,
            b"# Issue: `BIZ-103`\n\n"
            b"**Status: active** \xe2\x80\x94 created 2029-12-01; started 2030-01-02.\n\n"
            b"## Notes\n\nPreserve exactly.\n",
        )
        self.assertEqual(
            rendered_dashboard,
            b"# Dashboard\n\n## Active Issue\n\n"
            b"- `BIZ-103` (phase: execute). Canonical: `product/issues/BIZ-103.md`.\n\n"
            b"## Notes\n\nPreserve exactly.\n",
        )

    def test_state_and_issue_index_renderers_are_deterministic_utf8_json(self):
        lc = load_module("project_lifecycle_json_renderers", "scripts/project_lifecycle.py")
        state = b'{"schema":"moduflow.state.v1","custom":"keep"}\n'
        issues = [
            {"id": "BIZ-200", "status": "backlog", "title": "Later"},
            {"id": "BIZ-103", "status": "active", "title": "Current"},
        ]

        rendered_state = lc.render_state_projection(
            state,
            active_issue="BIZ-103",
            phase="execute",
            next_command="product:execute BIZ-103",
            changed_on="2030-01-02",
        )
        rendered_index = lc.render_issue_index(issues)

        self.assertEqual(
            json.loads(rendered_state),
            {
                "schema": "moduflow.state.v1",
                "custom": "keep",
                "active_issue": "BIZ-103",
                "phase": "execute",
                "active_goal": "",
                "next_command": "product:execute BIZ-103",
                "blockers": [],
                "updated_at": "2030-01-02",
            },
        )
        self.assertEqual(
            json.loads(rendered_index),
            {
                "schema": "moduflow.issue-index.v1",
                "issues": [
                    {"id": "BIZ-103", "status": "active", "title": "Current"},
                    {"id": "BIZ-200", "status": "backlog", "title": "Later"},
                ],
            },
        )

    def test_roadmap_renderer_changes_only_its_bounded_managed_block(self):
        lc = load_module("project_lifecycle_roadmap_renderer", "scripts/project_lifecycle.py")
        original = (
            b"# Roadmap\n\nHuman before.\n\n"
            b"<!-- moduflow:roadmap-projection:start -->\n"
            b"- `OLD` \xe2\x80\x94 priority `p3`; dependencies `none`; release order `none`.\n"
            b"<!-- moduflow:roadmap-projection:end -->\n\n"
            b"Human after.\n"
        )

        rendered = lc.render_roadmap_projection(
            original,
            issue_id="BIZ-103",
            priority="p1",
            dependencies=["BIZ-100", "BIZ-101"],
            release_order="7",
        )

        self.assertEqual(
            rendered,
            b"# Roadmap\n\nHuman before.\n\n"
            b"<!-- moduflow:roadmap-projection:start -->\n"
            b"- `BIZ-103` \xe2\x80\x94 priority `p1`; dependencies `BIZ-100, BIZ-101`; release order `7`.\n"
            b"<!-- moduflow:roadmap-projection:end -->\n\n"
            b"Human after.\n",
        )
    def test_archived_project_denies_lifecycle_sync_before_evaluation_or_write(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        project_registry = load_module("project_registry_lifecycle", "scripts/project_registry.py")
        project_operation = load_module("project_operation_lifecycle", "scripts/project_operation.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = project_registry.project_context_for_root(root)
            context.update(project_operation.compute_project_policy("archived", "internal"))

            with mock.patch.object(lc, "evaluate_project") as evaluate:
                with self.assertRaisesRegex(Exception, "Archived projects are read-only"):
                    lc.sync_lifecycle(root, project_context=context)

            evaluate.assert_not_called()
            self.assertFalse((root / ".moduflow" / "state.json").exists())

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

    def test_sync_builds_one_reconcile_intent_and_preserves_legacy_result_keys(self):
        lc = load_module("project_lifecycle_sync_adapter", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active"})
            transaction_result = {
                "schema": "moduflow.lifecycle-transaction.v1",
                "status": "applied",
                "targets": [
                    {"role": "dashboard", "changed": True},
                ],
            }
            apply = mock.Mock(return_value=transaction_result)
            boundary = SimpleNamespace(
                LifecycleIntent=lambda **values: SimpleNamespace(**values),
                apply_lifecycle_transaction=apply,
            )
            injector = lambda _stage: None

            with mock.patch.object(
                lc,
                "_load_lifecycle_transaction_module",
                return_value=boundary,
            ):
                result = lc.sync_lifecycle(
                    root,
                    actor="dongwon",
                    source_event="request:C1b",
                    idempotency_key="a" * 64,
                    expected_issue_sha256="b" * 64,
                    require_issue_index=True,
                    clock="clock",
                    fault_injector=injector,
                )

            intent = apply.call_args.args[1]
            self.assertEqual(intent.issue_id, "048-x")
            self.assertEqual(intent.action, "reconcile")
            self.assertIsNone(intent.target_lifecycle)
            self.assertEqual(intent.actor, "dongwon")
            self.assertEqual(intent.source_event, "request:C1b")
            self.assertEqual(intent.idempotency_key, "a" * 64)
            self.assertEqual(intent.expected_issue_sha256, "b" * 64)
            self.assertTrue(intent.require_issue_index)
            apply.assert_called_once_with(
                root.resolve(),
                intent,
                project_context=mock.ANY,
                clock="clock",
                fault_injector=injector,
            )
            self.assertEqual(
                result,
                {
                    "active": "048-x",
                    "phase": "select",
                    "dashboard_updated": True,
                    "transaction": transaction_result,
                },
            )

    def test_sync_maps_transaction_failure_to_legacy_blocked_shape(self):
        lc = load_module("project_lifecycle_sync_failure", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active"})
            transaction_result = {
                "schema": "moduflow.lifecycle-transaction.v1",
                "status": "rolled_back",
                "error_code": "POST_APPLY_VALIDATION_FAILED",
                "targets": [{"role": "dashboard", "changed": True}],
            }
            boundary = SimpleNamespace(
                LifecycleIntent=lambda **values: SimpleNamespace(**values),
                apply_lifecycle_transaction=mock.Mock(return_value=transaction_result),
            )

            with mock.patch.object(
                lc,
                "_load_lifecycle_transaction_module",
                return_value=boundary,
            ):
                result = lc.sync_lifecycle(root)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["active"], "048-x")
            self.assertEqual(result["phase"], "select")
            self.assertFalse(result["dashboard_updated"])
            self.assertEqual(result["transaction"], transaction_result)
            self.assertIn("POST_APPLY_VALIDATION_FAILED", result["errors"][0])

    def test_sync_adapter_owns_no_direct_file_mutation(self):
        lc = load_module("project_lifecycle_sync_no_write", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active"})
            boundary = SimpleNamespace(
                LifecycleIntent=lambda **values: SimpleNamespace(**values),
                apply_lifecycle_transaction=mock.Mock(
                    return_value={
                        "schema": "moduflow.lifecycle-transaction.v1",
                        "status": "noop",
                        "targets": [{"role": "dashboard", "changed": False}],
                    }
                ),
            )

            with (
                mock.patch.object(
                    lc,
                    "_load_lifecycle_transaction_module",
                    return_value=boundary,
                ),
                mock.patch.object(lc.Path, "write_text") as write_text,
                mock.patch.object(lc.Path, "write_bytes") as write_bytes,
            ):
                result = lc.sync_lifecycle(root)

            self.assertFalse(result["dashboard_updated"])
            write_text.assert_not_called()
            write_bytes.assert_not_called()

    def test_sync_updates_views_idempotently_and_preserves_prose(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active"}, active_in_dashboard="040-old", state_active="040-old")
            (root / "specs" / "048-x").mkdir(parents=True)
            (root / "specs" / "048-x" / "spec.md").write_text("# s\n", encoding="utf-8")

            with valid_transaction_validation(), mock.patch.object(
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

            with valid_transaction_validation():
                second = lc.sync_lifecycle(root)           # idempotent
            self.assertFalse(second["dashboard_updated"])

    def test_sync_replaces_stale_execute_command_for_dependency_blocked_active_issue(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(
                root,
                {"BIZ-ACTIVE": "active", "BIZ-BLOCKER": "backlog"},
                active_in_dashboard="BIZ-ACTIVE",
                state_active="BIZ-ACTIVE",
            )
            active_issue = root / "issues" / "BIZ-ACTIVE.md"
            active_issue.write_text(
                "# Issue: `BIZ-ACTIVE`\n\n"
                "**Status: active** — created.\n"
                "**Blocked-by: BIZ-BLOCKER**\n",
                encoding="utf-8",
            )
            spec_dir = root / "specs" / "BIZ-ACTIVE"
            spec_dir.mkdir(parents=True)
            for artifact in ("spec.md", "plan.md", "tasks.md"):
                (spec_dir / artifact).write_text("# artifact\n", encoding="utf-8")
            state_path = root / ".moduflow" / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["next_command"] = "product:execute BIZ-ACTIVE"
            state_path.write_text(
                json.dumps(state) + "\n",
                encoding="utf-8",
            )

            with valid_transaction_validation(), mock.patch.object(
                lc, "evaluate_project", wraps=lc.evaluate_project
            ) as evaluate:
                result = lc.sync_lifecycle(root)

            synced = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(evaluate.call_count, 1)
            self.assertEqual(result["phase"], "execute")
            self.assertEqual(synced["phase"], "execute")
            self.assertEqual(synced["next_command"], "product:status")

    def test_sync_uses_normalized_custom_paths_for_phase_and_dashboard_link(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issues_dir = root / "records" / "issues"
            specs_dir = root / "records" / "specs" / "BIZ-CUSTOM"
            issues_dir.mkdir(parents=True)
            specs_dir.mkdir(parents=True)
            (issues_dir / "BIZ-CUSTOM.md").write_text(
                "# Issue: `BIZ-CUSTOM`\n\n"
                "**Status: active** — created.\n",
                encoding="utf-8",
            )
            for artifact in (
                "spec.md",
                "plan.md",
                "tasks.md",
                "review.md",
                "release.md",
            ):
                (specs_dir / artifact).write_text("# artifact\n", encoding="utf-8")
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.config.v1",
                        "paths": {
                            "issues": "records/issues",
                            "specs": "records/specs",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = root / ".moduflow" / "state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "schema": "moduflow.state.v1",
                        "phase": "select",
                        "active_goal": "g",
                        "active_issue": "BIZ-CUSTOM",
                        "next_command": "product:status",
                        "blockers": [],
                        "updated_at": "2026-06-28",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "workspace").mkdir()
            dashboard_path = root / "workspace" / "dashboard.md"
            dashboard_path.write_text(
                "# Dashboard\n\n"
                "## Active Issue\n\n- None active.\n\n"
                "## Recently Completed\n\n- Preserve me.\n",
                encoding="utf-8",
            )
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.loop-state.v2",
                        "goal_id": "g",
                        "issue_ids": ["BIZ-CUSTOM"],
                        "active_issue_id": "BIZ-CUSTOM",
                        "status": "active",
                        "next_command": "product:status",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "workspace" / "transactions").mkdir()

            with valid_transaction_validation(), mock.patch.object(
                lc, "evaluate_project", wraps=lc.evaluate_project
            ) as evaluate:
                result = lc.sync_lifecycle(root)

            synced = json.loads(state_path.read_text(encoding="utf-8"))
            dashboard = dashboard_path.read_text(encoding="utf-8")
            self.assertEqual(evaluate.call_count, 1)
            self.assertEqual(result["phase"], "release")
            self.assertEqual(synced["phase"], "release")
            self.assertEqual(synced["next_command"], "product:execute BIZ-CUSTOM")
            self.assertIn("Canonical: `records/issues/BIZ-CUSTOM.md`.", dashboard)
            self.assertNotIn("Canonical: `issues/BIZ-CUSTOM.md`.", dashboard)
            self.assertIn("Preserve me.", dashboard)

    def test_sync_uses_configured_workspace_dashboard_and_ignores_default_decoy(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issues = root / "product" / "issues"
            workspace = root / "product" / "workspace"
            issues.mkdir(parents=True)
            workspace.mkdir(parents=True)
            (issues / "A-001.md").write_text(
                "# Issue: `A-001`\n\n**Status: active** — created.\n",
                encoding="utf-8",
            )
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "paths": {
                            "issues": "product/issues",
                            "specs": "product/specs",
                            "workspace": "product/workspace",
                        }
                    }
                ),
                encoding="utf-8",
            )
            (root / ".moduflow" / "state.json").write_text(
                json.dumps({"schema": "moduflow.state.v1"}), encoding="utf-8"
            )
            configured_dashboard = workspace / "dashboard.md"
            configured_dashboard.write_text(
                "# Dashboard\n\n## Active Issue\n\n- None active.\n\n"
                "## Notes\n\n- CONFIGURED-PRESERVE\n",
                encoding="utf-8",
            )
            (workspace / "loop-state.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.loop-state.v2",
                        "goal_id": "g",
                        "issue_ids": ["A-001"],
                        "active_issue_id": "A-001",
                        "status": "active",
                        "next_command": "product:status",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (workspace / "transactions").mkdir()
            default_workspace = root / "workspace"
            default_workspace.mkdir()
            decoy = default_workspace / "dashboard.md"
            decoy.write_text(
                "# Dashboard\n\n## Active Issue\n\n- WRONG-DECOY\n",
                encoding="utf-8",
            )
            before = decoy.read_bytes()

            with valid_transaction_validation():
                result = lc.sync_lifecycle(root)

            self.assertTrue(result["dashboard_updated"])
            self.assertIn(
                "`A-001`", configured_dashboard.read_text(encoding="utf-8")
            )
            self.assertIn(
                "CONFIGURED-PRESERVE",
                configured_dashboard.read_text(encoding="utf-8"),
            )
            self.assertEqual(decoy.read_bytes(), before)

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

    def test_transition_cli_forwards_arguments_and_maps_status_exit_codes(self):
        lc = load_module("project_lifecycle_transition_cli", "scripts/project_lifecycle.py")
        for status, expected_exit in (
            ("applied", 0),
            ("noop", 0),
            ("denied", 1),
            ("conflict", 1),
            ("rolled_back", 1),
            ("recovery_required", 1),
        ):
            with self.subTest(status=status):
                result = {
                    "schema": "moduflow.lifecycle-transaction.v1",
                    "status": status,
                }
                output = io.StringIO()
                with (
                    mock.patch.object(
                        lc,
                        "transition_lifecycle",
                        return_value=result,
                    ) as transition,
                    mock.patch(
                        "sys.argv",
                        [
                            "project_lifecycle.py",
                            "/project",
                            "--transition",
                            "update",
                            "--issue-id",
                            "BIZ-103",
                            "--target-status",
                            "active",
                            "--priority",
                            "p1",
                            "--actor",
                            "dongwon",
                            "--source-event",
                            "request:C1a",
                            "--idempotency-key",
                            "a" * 64,
                            "--expected-issue-sha256",
                            "b" * 64,
                            "--loop-blocker",
                            "waiting",
                            "--require-issue-index",
                        ],
                    ),
                    contextlib.redirect_stdout(output),
                ):
                    exit_code = lc.main()

                self.assertEqual(exit_code, expected_exit)
                self.assertEqual(json.loads(output.getvalue()), result)
                transition.assert_called_once_with(
                    "/project",
                    "BIZ-103",
                    "update",
                    actor="dongwon",
                    source_event="request:C1a",
                    target_status="active",
                    priority="p1",
                    idempotency_key="a" * 64,
                    expected_issue_sha256="b" * 64,
                    loop_blocker="waiting",
                    require_issue_index=True,
                )

    def test_recovery_cli_supports_all_and_one_transaction(self):
        lc = load_module("project_lifecycle_recovery_cli", "scripts/project_lifecycle.py")
        for extra, transaction_id, status, expected_exit in (
            ([], "", "noop", 0),
            (["txn-103"], "txn-103", "recovery_required", 1),
        ):
            with self.subTest(transaction_id=transaction_id or "all"):
                result = {
                    "schema": "moduflow.lifecycle-recovery.v1",
                    "status": status,
                }
                recover = mock.Mock(return_value=result)
                boundary = SimpleNamespace(
                    recover_incomplete_transaction=recover,
                )
                output = io.StringIO()
                with (
                    mock.patch.object(
                        lc,
                        "_load_lifecycle_transaction_module",
                        return_value=boundary,
                    ),
                    mock.patch(
                        "sys.argv",
                        ["project_lifecycle.py", "/project", "--recover", *extra],
                    ),
                    contextlib.redirect_stdout(output),
                ):
                    exit_code = lc.main()

                self.assertEqual(exit_code, expected_exit)
                self.assertEqual(json.loads(output.getvalue()), result)
                recover.assert_called_once_with("/project", transaction_id)

    def test_mutation_cli_rejects_invalid_combinations_before_entries(self):
        lc = load_module("project_lifecycle_invalid_cli", "scripts/project_lifecycle.py")
        cases = (
            ["/project", "--transition", "start"],
            [
                "/project",
                "--transition",
                "start",
                "--actor",
                "dongwon",
                "--source-event",
                "request:C1a",
            ],
            [
                "/project",
                "--transition",
                "start",
                "--issue-id",
                "BIZ-103",
                "--source-event",
                "request:C1a",
            ],
            [
                "/project",
                "--transition",
                "start",
                "--issue-id",
                "BIZ-103",
                "--actor",
                "dongwon",
            ],
            [
                "/project",
                "--transition",
                "start",
                "--recover",
                "txn-103",
                "--issue-id",
                "BIZ-103",
                "--actor",
                "dongwon",
                "--source-event",
                "request:C1a",
            ],
            ["/project", "--recover", "--actor", "dongwon"],
            ["/project", "--sync", "--actor", "dongwon"],
            ["/project", "--priority", "p1"],
            ["/project", "--recover", "--priority", "p1"],
            [
                "/project",
                "--transition",
                "update",
                "--issue-id",
                "BIZ-103",
                "--actor",
                "dongwon",
                "--source-event",
                "request:C1e",
                "--priority",
                "urgent",
            ],
            [
                "/project",
                "--state",
                "--transition",
                "start",
                "--issue-id",
                "BIZ-103",
                "--actor",
                "dongwon",
                "--source-event",
                "request:C1a",
            ],
        )
        for args in cases:
            with self.subTest(args=args):
                transition = mock.Mock()
                load_boundary = mock.Mock()
                with (
                    mock.patch.object(lc, "transition_lifecycle", transition),
                    mock.patch.object(
                        lc,
                        "_load_lifecycle_transaction_module",
                        load_boundary,
                    ),
                    mock.patch("sys.argv", ["project_lifecycle.py", *args]),
                    contextlib.redirect_stderr(io.StringIO()),
                    self.assertRaises(SystemExit) as raised,
                ):
                    lc.main()
                self.assertEqual(raised.exception.code, 2)
                transition.assert_not_called()
                load_boundary.assert_not_called()

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
