import json
import os
import stat
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import project_lifecycle_transaction as transaction
import project_registry
from tests.lifecycle_transaction_fixture import (
    lifecycle_intent_fields,
    resolved_transaction_context,
)


class TransactionContractTests(unittest.TestCase):
    def test_each_supported_action_normalizes_to_its_canonical_lifecycle(self):
        cases = [
            ("start", None, "active"),
            ("update", None, None),
            ("update", "active", "active"),
            ("pause", None, "active"),
            ("resume", None, "active"),
            ("complete", None, "done"),
            ("reconcile", "backlog", "backlog"),
            ("production-version", None, None),
        ]

        for action, supplied_target, expected_target in cases:
            with self.subTest(action=action):
                fields = lifecycle_intent_fields(
                    action,
                    target_lifecycle=supplied_target,
                    production_change=(
                        {"version": "1.2.3"}
                        if action == "production-version"
                        else None
                    ),
                )
                intent = transaction.normalize_lifecycle_intent(
                    transaction.LifecycleIntent(**fields)
                )

                self.assertEqual(intent.action, action)
                self.assertEqual(intent.target_lifecycle, expected_target)

    def test_invalid_action_lifecycle_and_production_version_combinations_are_rejected(self):
        cases = [
            ("unknown", None, None, "Unsupported lifecycle action"),
            ("start", "done", None, "must target active"),
            ("complete", "active", None, "must target done"),
            ("pause", "backlog", None, "must target active"),
            ("production-version", None, None, "requires production_change.version"),
            ("production-version", None, {"version": "v1"}, "semantic version"),
            ("start", None, {"version": "1.2.3"}, "only valid for production-version"),
        ]

        for action, target_lifecycle, production_change, message in cases:
            with self.subTest(action=action, target_lifecycle=target_lifecycle):
                fields = lifecycle_intent_fields(
                    action,
                    target_lifecycle=target_lifecycle,
                    production_change=production_change,
                )
                with self.assertRaisesRegex(ValueError, message):
                    transaction.normalize_lifecycle_intent(
                        transaction.LifecycleIntent(**fields)
                    )

    def test_idempotency_and_transaction_identity_ignore_clock_and_staging_path(self):
        intent = transaction.LifecycleIntent(
            **lifecycle_intent_fields("start")
        )
        first_context = resolved_transaction_context(
            staging_root="/var/tmp/first", clock="2030-01-01T00:00:00Z"
        )
        second_context = resolved_transaction_context(
            staging_root="/var/tmp/second", clock="2032-02-02T02:02:02Z"
        )

        first_key = transaction.derive_idempotency_key(first_context, intent)
        second_key = transaction.derive_idempotency_key(second_context, intent)

        self.assertEqual(
            first_key,
            "9c89689c8960bf8fcdc8ccb31859a65956e4804a2c19bf46f32e614ec690484e",
        )
        self.assertEqual(second_key, first_key)
        self.assertEqual(
            transaction.derive_transaction_id(first_context, intent),
            "txn-e77c2f16d9ead05064180537024fe502",
        )
        self.assertEqual(
            transaction.derive_transaction_id(second_context, intent),
            "txn-e77c2f16d9ead05064180537024fe502",
        )

    def test_key_cannot_be_reused_for_a_different_normalized_intent(self):
        context = resolved_transaction_context()
        start = transaction.normalize_lifecycle_intent(
            transaction.LifecycleIntent(**lifecycle_intent_fields("start"))
        )
        complete = transaction.normalize_lifecycle_intent(
            transaction.LifecycleIntent(**lifecycle_intent_fields("complete"))
        )
        key = transaction.derive_idempotency_key(context, start)

        transaction.assert_idempotency_key_matches(context, key, start)
        with self.assertRaisesRegex(ValueError, "IDEMPOTENCY_KEY_CONFLICT"):
            transaction.assert_idempotency_key_matches(context, key, complete)

    def test_pause_blocker_changes_the_normalized_intent_identity(self):
        context = resolved_transaction_context()
        blocked_for_approval = transaction.LifecycleIntent(
            **lifecycle_intent_fields("pause"), loop_blocker="waiting for approval"
        )
        blocked_for_vendor = transaction.LifecycleIntent(
            **lifecycle_intent_fields("pause"), loop_blocker="waiting for vendor"
        )

        self.assertNotEqual(
            transaction.derive_idempotency_key(context, blocked_for_approval),
            transaction.derive_idempotency_key(context, blocked_for_vendor),
        )

    def test_normalization_deeply_freezes_change_payloads_and_identity(self):
        context = resolved_transaction_context()
        roadmap_change = {
            "priority": {"before": "p2", "after": "p1"},
            "dependencies": ["102-resolver"],
        }
        production_change = {
            "version": "1.2.3",
            "release": {"channel": "beta"},
        }
        normalized_update = transaction.normalize_lifecycle_intent(
            transaction.LifecycleIntent(
                **lifecycle_intent_fields("update"), roadmap_change=roadmap_change
            )
        )
        normalized_production = transaction.normalize_lifecycle_intent(
            transaction.LifecycleIntent(
                **lifecycle_intent_fields(
                    "production-version", production_change=production_change
                )
            )
        )
        update_key = transaction.derive_idempotency_key(context, normalized_update)
        production_key = transaction.derive_idempotency_key(context, normalized_production)

        roadmap_change["priority"]["after"] = "p0"
        roadmap_change["dependencies"].append("110-capabilities")
        production_change["release"]["channel"] = "stable"
        with self.assertRaises(TypeError):
            normalized_update.roadmap_change["priority"]["after"] = "p0"
        with self.assertRaises(TypeError):
            normalized_production.production_change["release"]["channel"] = "stable"

        self.assertEqual(normalized_update.roadmap_change["priority"]["after"], "p1")
        self.assertEqual(normalized_update.roadmap_change["dependencies"], ("102-resolver",))
        self.assertEqual(normalized_production.production_change["release"]["channel"], "beta")
        self.assertEqual(transaction.derive_idempotency_key(context, normalized_update), update_key)
        self.assertEqual(
            transaction.derive_idempotency_key(context, normalized_production),
            production_key,
        )

    def test_target_hashes_and_persisted_envelopes_are_redacted_and_schema_strict(self):
        before = transaction.target_sha256(b"before")
        after = transaction.target_sha256(b"after")
        self.assertEqual(
            before,
            "6db7d803e74f1ffa7d8f5adc0bf95b3e15bf4c8373fffadf546227cc6c6742cb",
        )
        self.assertEqual(
            after,
            "f39592393ef0859cb196a52693d2cea00fb2df784b3c04ae54aa7cadb8e562f8",
        )

        plan = {
            "schema": "moduflow.lifecycle-transaction-plan.v1",
            "transaction_id": "txn-123",
            "idempotency_key": "key-123",
            "project_id": "alpha",
            "canonical_root": "/projects/alpha",
            "issue_id": "103-atomic-lifecycle-state-transaction",
            "action": "start",
            "target_lifecycle": "active",
            "targets": [{
                "role": "owning-issue",
                "relative_path": "issues/103-atomic-lifecycle-state-transaction.md",
                "existed": True,
                "before_sha256": before,
                "after_sha256": after,
                "after_bytes": 5,
                "changed": True,
                "validation_rules": ["issue-schema"],
                "apply_order": 1,
                "rollback_order": 1,
            }],
        }
        rendered_plan = transaction.serialize_transaction_plan(plan)
        self.assertNotIn("before", rendered_plan)
        self.assertNotIn("staging", rendered_plan)
        self.assertEqual(rendered_plan["targets"][0]["after_bytes"], 5)

        result = {
            "schema": "moduflow.lifecycle-transaction.v1",
            "transaction_id": "txn-123",
            "idempotency_key": "key-123",
            "status": "noop",
            "project_id": "alpha",
            "canonical_root": "/projects/alpha",
            "issue_id": "103-atomic-lifecycle-state-transaction",
            "action": "start",
            "target_lifecycle": "active",
            "targets": rendered_plan["targets"],
            "projected_validation": {"valid": True},
            "post_apply_validation": {"valid": True},
            "failed_stage": "",
            "error_code": "",
            "rollback_status": "not_required",
            "verified_target_count": 1,
            "next_command": "product:status",
            "actor": "dongwon",
            "source_event": "request:42",
            "created_at": "2030-01-01T00:00:00Z",
            "started_at": "",
            "completed_at": "2030-01-01T00:00:00Z",
        }
        self.assertEqual(transaction.serialize_transaction_result(result), result)

        with self.assertRaisesRegex(ValueError, "Unknown transaction plan keys"):
            transaction.serialize_transaction_plan({**plan, "recovery_payload": "secret"})
        with self.assertRaisesRegex(ValueError, "Unknown transaction result keys"):
            transaction.serialize_transaction_result({**result, "staging_path": "/tmp/secret"})

    def test_projected_validation_summary_is_stable_redacted_and_detached(self):
        validation = {
            "schema": "moduflow.project-validation.v1",
            "project_root": "/private/projected-root",
            "valid": False,
            "errors": ["private artifact payload at /private/projected-root"],
            "warnings": ["private warning"],
            "issue_schema": {
                "errors": 1,
                "warnings": 0,
                "codes": ["ISSUE_SCHEMA_PRIVATE_DETAIL"],
                "diagnostics": [{"payload": "private diagnostic"}],
            },
            "lifecycle_drift": ["private lifecycle payload"],
        }

        summary = transaction._summarize_projected_validation(validation)
        validation["errors"].append("poison")
        validation["lifecycle_drift"].append("poison")

        self.assertEqual(
            summary,
            {
                "valid": False,
                "rule_ids": [
                    "project-artifacts",
                    "issue-schema",
                    "lifecycle-consensus",
                    "production-records",
                ],
                "error_codes": [
                    "PROJECTED_PROJECT_INVALID",
                    "PROJECTED_ISSUE_SCHEMA_INVALID",
                    "PROJECTED_LIFECYCLE_DRIFT",
                ],
            },
        )
        rendered = json.dumps(summary, ensure_ascii=False)
        self.assertNotIn("private", rendered)
        self.assertNotIn("poison", rendered)

    def test_projected_validation_summary_accepts_valid_project_result(self):
        summary = transaction._summarize_projected_validation(
            {
                "schema": "moduflow.project-validation.v1",
                "valid": True,
                "errors": [],
                "issue_schema": {"errors": 0},
                "lifecycle_drift": [],
            }
        )

        self.assertEqual(
            summary,
            {
                "valid": True,
                "rule_ids": [
                    "project-artifacts",
                    "issue-schema",
                    "lifecycle-consensus",
                    "production-records",
                ],
                "error_codes": [],
            },
        )

    def test_projected_validation_summary_collapses_malformed_results(self):
        malformed = (
            None,
            {"schema": "unsupported"},
            {
                "schema": "moduflow.project-validation.v1",
                "valid": "yes",
                "errors": [],
                "issue_schema": {"errors": 0},
                "lifecycle_drift": [],
            },
            {
                "schema": "moduflow.project-validation.v1",
                "valid": False,
                "errors": "private error",
                "issue_schema": {"errors": 0},
                "lifecycle_drift": [],
            },
            {
                "schema": "moduflow.project-validation.v1",
                "valid": False,
                "errors": ["private error"],
                "issue_schema": {"errors": True},
                "lifecycle_drift": [],
            },
            {
                "schema": "moduflow.project-validation.v1",
                "valid": False,
                "errors": ["private error"],
                "issue_schema": {"errors": 0},
                "lifecycle_drift": "private drift",
            },
            {
                "schema": "moduflow.project-validation.v1",
                "valid": True,
                "errors": [],
                "issue_schema": {"errors": 1},
                "lifecycle_drift": [],
            },
        )
        expected = {
            "valid": False,
            "rule_ids": [
                "project-artifacts",
                "issue-schema",
                "lifecycle-consensus",
                "production-records",
            ],
            "error_codes": ["PROJECTED_VALIDATION_CONTRACT_INVALID"],
        }

        for validation in malformed:
            with self.subTest(validation=validation):
                self.assertEqual(
                    transaction._summarize_projected_validation(validation),
                    expected,
                )

    def test_serializers_reject_unsafe_target_and_nested_validation_content(self):
        target = {
            "role": "owning-issue",
            "relative_path": "issues/103-atomic-lifecycle-state-transaction.md",
            "existed": True,
            "before_sha256": "6db7d803e74f1ffa7d8f5adc0bf95b3e15bf4c8373fffadf546227cc6c6742cb",
            "after_sha256": "f39592393ef0859cb196a52693d2cea00fb2df784b3c04ae54aa7cadb8e562f8",
            "after_bytes": 5,
            "changed": True,
            "validation_rules": ["issue-schema"],
            "apply_order": 1,
            "rollback_order": 1,
        }
        plan = {
            "schema": "moduflow.lifecycle-transaction-plan.v1",
            "transaction_id": "txn-123",
            "idempotency_key": "key-123",
            "project_id": "alpha",
            "canonical_root": "/projects/alpha",
            "issue_id": "103-atomic-lifecycle-state-transaction",
            "action": "start",
            "target_lifecycle": "active",
            "targets": [target],
        }
        unsafe_targets = [
            ({**target, "relative_path": "/private/recovery-payload"}, "relative_path"),
            ({**target, "relative_path": "C:/private/recovery-payload"}, "relative_path"),
            ({**target, "before_sha256": "recovery payload: secret"}, "sha256"),
            ({**target, "validation_rules": ["issue-schema", {"payload": "secret"}]}, "validation_rules"),
        ]
        for unsafe_target, message in unsafe_targets:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    transaction.serialize_transaction_plan({**plan, "targets": [unsafe_target]})

        result = {
            "schema": "moduflow.lifecycle-transaction.v1",
            "transaction_id": "txn-123",
            "idempotency_key": "key-123",
            "status": "noop",
            "project_id": "alpha",
            "canonical_root": "/projects/alpha",
            "issue_id": "103-atomic-lifecycle-state-transaction",
            "action": "start",
            "target_lifecycle": "active",
            "targets": [target],
            "projected_validation": {"valid": True, "details": {"payload": "secret"}},
            "post_apply_validation": {"valid": True},
            "failed_stage": "",
            "error_code": "",
            "rollback_status": "not_required",
            "verified_target_count": 1,
            "next_command": "product:status",
            "actor": "dongwon",
            "source_event": "request:42",
            "created_at": "2030-01-01T00:00:00Z",
            "started_at": "",
            "completed_at": "2030-01-01T00:00:00Z",
        }
        with self.assertRaisesRegex(ValueError, "validation summary keys"):
            transaction.serialize_transaction_result(result)

    def test_serializers_reject_non_scalar_envelope_fields_and_detach_outputs(self):
        target = {
            "role": "owning-issue",
            "relative_path": "issues/103-atomic-lifecycle-state-transaction.md",
            "existed": True,
            "before_sha256": "6db7d803e74f1ffa7d8f5adc0bf95b3e15bf4c8373fffadf546227cc6c6742cb",
            "after_sha256": "f39592393ef0859cb196a52693d2cea00fb2df784b3c04ae54aa7cadb8e562f8",
            "after_bytes": 5,
            "changed": True,
            "validation_rules": ["issue-schema"],
            "apply_order": 1,
            "rollback_order": 1,
        }
        plan = {
            "schema": "moduflow.lifecycle-transaction-plan.v1",
            "transaction_id": "txn-123",
            "idempotency_key": "key-123",
            "project_id": "alpha",
            "canonical_root": "/projects/alpha",
            "issue_id": "103-atomic-lifecycle-state-transaction",
            "action": "start",
            "target_lifecycle": "active",
            "targets": [target],
        }
        result = {
            "schema": "moduflow.lifecycle-transaction.v1",
            "transaction_id": "txn-123",
            "idempotency_key": "key-123",
            "status": "noop",
            "project_id": "alpha",
            "canonical_root": "/projects/alpha",
            "issue_id": "103-atomic-lifecycle-state-transaction",
            "action": "start",
            "target_lifecycle": "active",
            "targets": [target],
            "projected_validation": {"valid": True, "rule_ids": ["projected-state"]},
            "post_apply_validation": {"valid": True, "rule_ids": ["post-apply"]},
            "failed_stage": "",
            "error_code": "",
            "rollback_status": "not_required",
            "verified_target_count": 1,
            "next_command": "product:status",
            "actor": "dongwon",
            "source_event": "request:42",
            "created_at": "2030-01-01T00:00:00Z",
            "started_at": "",
            "completed_at": "2030-01-01T00:00:00Z",
        }
        plan_scalar_fields = (
            "schema", "transaction_id", "idempotency_key", "project_id",
            "canonical_root", "issue_id", "action", "target_lifecycle",
        )
        result_scalar_fields = (
            "schema", "transaction_id", "idempotency_key", "status", "project_id",
            "canonical_root", "issue_id", "action", "target_lifecycle", "failed_stage",
            "error_code", "rollback_status", "verified_target_count", "next_command",
            "actor", "source_event", "created_at", "started_at", "completed_at",
        )
        nested_recovery_value = {"recovery_payload": "must not escape"}

        for field in plan_scalar_fields:
            with self.subTest(envelope="plan", field=field):
                with self.assertRaises((TypeError, ValueError)):
                    transaction.serialize_transaction_plan(
                        {**plan, field: nested_recovery_value}
                    )
        for field in result_scalar_fields:
            with self.subTest(envelope="result", field=field):
                with self.assertRaises((TypeError, ValueError)):
                    transaction.serialize_transaction_result(
                        {**result, field: nested_recovery_value}
                    )

        rendered_plan = transaction.serialize_transaction_plan(plan)
        rendered_result = transaction.serialize_transaction_result(result)
        target["validation_rules"].append("recovery-payload")
        result["projected_validation"]["rule_ids"].append("recovery-payload")

        self.assertEqual(rendered_plan["targets"][0]["validation_rules"], ["issue-schema"])
        self.assertEqual(
            rendered_result["projected_validation"]["rule_ids"], ["projected-state"]
        )

    def test_immutable_plan_detaches_context_and_serializes_redacted_targets(self):
        context = {
            "status": "resolved",
            "canonical_root": "/project",
            "relative_paths": {"workspace": "workspace"},
            "warnings": ["keep"],
        }
        validation_rules = ["issue-schema"]
        before_bytes = bytearray(b"private before bytes")
        after_bytes = bytearray(b"private after bytes")
        target = transaction.PlannedTarget(
            role="issue",
            relative_path="issues/BIZ-103.md",
            existed=True,
            before_sha256="a" * 64,
            after_sha256="b" * 64,
            after_size=42,
            changed=True,
            validation_rules=validation_rules,
            apply_order=0,
            rollback_order=0,
            _before_bytes=before_bytes,
            _after_bytes=after_bytes,
        )
        plan = transaction.LifecycleTransactionPlan(
            schema=transaction.PLAN_SCHEMA,
            transaction_id="txn-103",
            idempotency_key="c" * 64,
            project_id="explicit-root",
            canonical_root="/project",
            issue_id="BIZ-103",
            action="start",
            target_lifecycle="active",
            targets=(target,),
            _project_context=context,
        )

        preview = plan.to_public_dict()
        context["relative_paths"]["workspace"] = "poison"
        context["warnings"].append("poison")
        validation_rules.append("poison")
        before_bytes[:] = b"poison"
        after_bytes[:] = b"poison"

        self.assertEqual(plan._project_context["relative_paths"]["workspace"], "workspace")
        self.assertEqual(plan._project_context["warnings"], ("keep",))
        self.assertEqual(target.validation_rules, ("issue-schema",))
        self.assertEqual(target._before_bytes, b"private before bytes")
        self.assertEqual(target._after_bytes, b"private after bytes")
        self.assertEqual(preview["targets"][0]["after_bytes"], 42)
        self.assertNotIn("_before_bytes", preview["targets"][0])
        self.assertNotIn("_after_bytes", preview["targets"][0])
        self.assertNotIn("private before bytes", repr(plan))
        self.assertNotIn("private after bytes", repr(plan))
        with self.assertRaises(FrozenInstanceError):
            plan.action = "complete"
        with self.assertRaises(TypeError):
            plan._project_context["status"] = "poison"


class TransactionPlanningTests(unittest.TestCase):
    ISSUE_ID = "BIZ-103"

    def scaffold(self, root, *, nested=False, issue_index=False):
        paths = {
            "issues": "product/issues" if nested else "issues",
            "specs": "product/specs" if nested else "specs",
            "workspace": "product/workspace" if nested else "workspace",
            "knowledge": "product/knowledge" if nested else "knowledge",
            "memory": "product/memory" if nested else "memory",
            "production_records": (
                "product/memory/production-records"
                if nested else "memory/production-records"
            ),
            "playbooks": "product/playbooks" if nested else "playbooks",
            "workflow": "product/workflow" if nested else "workflow",
        }
        (root / ".moduflow").mkdir()
        (root / ".moduflow" / "config.json").write_text(
            json.dumps({"schema": "moduflow.config.v1", "paths": paths}) + "\n",
            encoding="utf-8",
        )
        (root / ".moduflow" / "state.json").write_text(
            json.dumps(
                {
                    "schema": "moduflow.state.v1",
                    "active_issue": "",
                    "phase": "select",
                    "active_goal": "",
                    "next_command": "product:status",
                    "blockers": [],
                    "updated_at": "2029-12-31",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        for role in paths.values():
            (root / role).mkdir(parents=True, exist_ok=True)
        issue = root / paths["issues"] / f"{self.ISSUE_ID}.md"
        issue.write_text(
            f"# Issue: `{self.ISSUE_ID}`\n\n"
            "**Status: backlog** — created 2029-12-01.\n"
            "**Priority: p2**\n"
            "**Blocked-by: none**\n\n"
            "## Notes\n\nPreserve issue prose.\n",
            encoding="utf-8",
        )
        workspace = root / paths["workspace"]
        (workspace / "inbox.md").write_text("# Inbox\n", encoding="utf-8")
        (workspace / "opportunities.md").write_text("# Opportunities\n", encoding="utf-8")
        (workspace / "roadmap.md").write_text(
            "# Roadmap\n\nHuman roadmap prose.\n", encoding="utf-8"
        )
        (workspace / "dashboard.md").write_text(
            "# Dashboard\n\n## Active Issue\n\n- None active.\n\n"
            "## Notes\n\nPreserve dashboard prose.\n",
            encoding="utf-8",
        )
        (workspace / "loop-state.json").write_text(
            json.dumps(
                {
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-1",
                    "issue_ids": [],
                    "active_issue_id": None,
                    "status": "active",
                    "next_command": "product:status",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        if issue_index:
            (workspace / "issue-index.json").write_text("{}\n", encoding="utf-8")
        if nested:
            for relative, payload in (
                ("issues/BIZ-103.md", b"POISON DEFAULT ISSUE\n"),
                ("workspace/dashboard.md", b"POISON DEFAULT DASHBOARD\n"),
                ("workspace/loop-state.json", b"{broken-default\n"),
                ("workspace/roadmap.md", b"POISON DEFAULT ROADMAP\n"),
                ("memory/production-records/poison.md", b"POISON DEFAULT RECORD\n"),
            ):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
        return project_registry.project_context_for_root(root)

    def intent(self, action="start", **changes):
        fields = {
            "issue_id": self.ISSUE_ID,
            "action": action,
            "actor": "dongwon",
            "source_event": "request:A2",
        }
        fields.update(changes)
        return transaction.LifecycleIntent(**fields)

    def test_plan_selects_required_and_only_explicit_optional_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)

            basic = transaction.plan_lifecycle_transaction(
                root, self.intent(), project_context=context, clock="2030-01-02"
            )
            with_index = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            roadmap = transaction.plan_lifecycle_transaction(
                root,
                self.intent(
                    action="update",
                    roadmap_change={
                        "priority": "p1",
                        "dependencies": ["BIZ-100"],
                        "release_order": "7",
                    },
                ),
                project_context=context,
                clock="2030-01-02",
            )
            production = transaction.plan_lifecycle_transaction(
                root,
                self.intent(
                    action="production-version",
                    production_change={
                        "version": "1.2.3",
                        "record_id": "biz-103-release",
                        "content": "not-yet-valid-production-record\n",
                    },
                ),
                project_context=context,
                clock="2030-01-02",
            )

        self.assertIsInstance(basic, transaction.LifecycleTransactionPlan)
        self.assertEqual(
            [target.role for target in basic.targets],
            ["issue", "state", "loop", "dashboard", "evidence"],
        )
        self.assertEqual(
            [target.role for target in with_index.targets],
            ["issue", "state", "loop", "dashboard", "issue-index", "evidence"],
        )
        self.assertEqual(
            [target.role for target in roadmap.targets],
            ["issue", "state", "loop", "dashboard", "roadmap", "evidence"],
        )
        self.assertEqual(
            [target.role for target in production.targets],
            ["issue", "state", "loop", "dashboard", "production-record", "evidence"],
        )

    def test_existing_issue_index_is_selected_but_absent_optional_files_stay_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)

            plan = transaction.plan_lifecycle_transaction(
                root, self.intent(), project_context=context, clock="2030-01-02"
            )

            roles = [target.role for target in plan.targets]
            self.assertIn("issue-index", roles)
            self.assertNotIn("roadmap", roles)
            self.assertNotIn("production-record", roles)

    def test_issue_index_preserves_every_issue_and_projects_the_owner_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            (root / "issues" / "BIZ-200.md").write_text(
                "# Issue: `BIZ-200`\n\n"
                "**Status: done** — created 2029-12-01; done 2029-12-20.\n",
                encoding="utf-8",
            )

            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(action="start"),
                project_context=context,
                clock="2030-01-02",
            )

            target = next(target for target in plan.targets if target.role == "issue-index")
            self.assertEqual(
                json.loads(target._after_bytes)["issues"],
                [
                    {"id": "BIZ-103", "status": "active", "title": "BIZ-103"},
                    {"id": "BIZ-200", "status": "done", "title": "BIZ-200"},
                ],
            )

    def test_backlog_preserving_actions_do_not_activate_execution_projections(self):
        cases = (
            ("update", {}),
            ("reconcile", {}),
            (
                "production-version",
                {
                    "production_change": {
                        "version": "1.2.3",
                        "record_id": "biz-103-release",
                        "content": "record\n",
                    }
                },
            ),
        )
        for action, changes in cases:
            with self.subTest(action=action), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root)

                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(action=action, **changes),
                    project_context=context,
                    clock="2030-01-02",
                )

                state = json.loads(
                    next(target for target in plan.targets if target.role == "state")._after_bytes
                )
                loop = json.loads(
                    next(target for target in plan.targets if target.role == "loop")._after_bytes
                )
                dashboard = next(
                    target for target in plan.targets if target.role == "dashboard"
                )._after_bytes.decode("utf-8")
                self.assertEqual(state["active_issue"], "")
                self.assertEqual(state["phase"], "select")
                self.assertEqual(state["next_command"], "product:status")
                self.assertIsNone(loop["active_issue_id"])
                self.assertEqual(loop["next_command"], "product:status")
                self.assertNotIn(self.ISSUE_ID, loop["issue_ids"])
                self.assertIn("None active", dashboard)

    def test_nested_context_owns_every_target_and_poisoned_defaults_are_not_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, nested=True, issue_index=True)
            decoys = {
                relative: (root / relative).read_bytes()
                for relative in (
                    "issues/BIZ-103.md",
                    "workspace/dashboard.md",
                    "workspace/loop-state.json",
                    "workspace/roadmap.md",
                    "memory/production-records/poison.md",
                )
            }

            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(
                    action="update",
                    roadmap_change={"priority": "p1"},
                    require_issue_index=True,
                ),
                project_context=context,
                clock="2030-01-02",
            )

            self.assertEqual(
                [target.relative_path for target in plan.targets[:-1]],
                [
                    "product/issues/BIZ-103.md",
                    ".moduflow/state.json",
                    "product/workspace/loop-state.json",
                    "product/workspace/dashboard.md",
                    "product/workspace/issue-index.json",
                    "product/workspace/roadmap.md",
                ],
            )
            for target in plan.targets:
                resolved = (root / target.relative_path).resolve()
                resolved.relative_to(root.resolve())
            self.assertEqual(
                {relative: (root / relative).read_bytes() for relative in decoys},
                decoys,
            )

    def test_selected_sources_are_read_once_and_planning_never_mutates_the_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            original_read = transaction._read_regular_file_no_follow
            with mock.patch.object(
                transaction,
                "_read_regular_file_no_follow",
                wraps=original_read,
            ) as read_source:
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(
                        action="update",
                        roadmap_change={"priority": "p1"},
                    ),
                    project_context=context,
                    clock="2030-01-02",
                )

            selected_existing = {
                str(root.resolve() / target.relative_path)
                for target in plan.targets
                if target.existed
            }
            counts = {}
            for call in read_source.call_args_list:
                path = str(call.args[0])
                counts[path] = counts.get(path, 0) + 1
            self.assertEqual(
                {path: counts.get(path, 0) for path in selected_existing},
                {path: 1 for path in selected_existing},
            )
            self.assertEqual(
                {
                    path.relative_to(root).as_posix(): path.read_bytes()
                    for path in root.rglob("*")
                    if path.is_file()
                },
                before,
            )
            self.assertFalse((root / ".moduflow" / "transactions").exists())

    def test_planner_failures_use_stable_codes_without_absolute_paths_or_payloads(self):
        cases = (
            ("context", "PLAN_CONTEXT_INVALID"),
            ("context-mismatch", "PLAN_CONTEXT_INVALID"),
            ("missing", "PLAN_TARGET_MISSING"),
            ("unreadable", "PLAN_TARGET_UNREADABLE"),
            ("not-regular", "PLAN_TARGET_NOT_REGULAR"),
            ("symlink", "PLAN_TARGET_SYMLINK"),
            ("parent-symlink", "PLAN_TARGET_SYMLINK"),
            ("escape", "PLAN_PATH_ESCAPE"),
            ("render", "PLAN_RENDER_INVALID"),
        )
        for case, expected_code in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root)
                patcher = None
                if case == "context":
                    context["status"] = "unresolved"
                elif case == "context-mismatch":
                    context["relative_paths"]["issues"] = "shadow/issues"
                elif case == "missing":
                    (root / ".moduflow" / "state.json").unlink()
                elif case == "unreadable":
                    patcher = mock.patch.object(
                        transaction.os,
                        "read",
                        side_effect=PermissionError("private operating-system detail"),
                    )
                elif case == "not-regular":
                    target = root / "workspace" / "dashboard.md"
                    target.unlink()
                    target.mkdir()
                elif case == "symlink":
                    target = root / "workspace" / "loop-state.json"
                    target.unlink()
                    target.symlink_to(root / "workspace" / "dashboard.md")
                elif case == "parent-symlink":
                    workspace = root / "workspace"
                    real_workspace = root / "real-workspace"
                    workspace.rename(real_workspace)
                    workspace.symlink_to(real_workspace, target_is_directory=True)
                elif case == "escape":
                    context["paths"]["issues"] = str(root.parent / "outside-issues")
                else:
                    (root / "issues" / f"{self.ISSUE_ID}.md").write_text(
                        "# malformed without status\nprivate artifact payload\n",
                        encoding="utf-8",
                    )

                try:
                    if patcher is not None:
                        patcher.start()
                    with self.assertRaises(transaction.LifecyclePlanError) as raised:
                        transaction.plan_lifecycle_transaction(
                            root,
                            self.intent(),
                            project_context=context,
                            clock="2030-01-02",
                        )
                finally:
                    if patcher is not None:
                        patcher.stop()

                self.assertEqual(raised.exception.code, expected_code)
                self.assertNotIn(str(root), str(raised.exception))
                self.assertNotIn("private", str(raised.exception))

    def test_planner_reads_without_path_based_symlink_or_file_rechecks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            forbidden = AssertionError("path-based target read is forbidden")

            with (
                mock.patch.object(Path, "is_symlink", side_effect=forbidden),
                mock.patch.object(Path, "is_file", side_effect=forbidden),
                mock.patch.object(Path, "read_bytes", side_effect=forbidden),
            ):
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(),
                    project_context=context,
                    clock="2030-01-02",
                )

            self.assertEqual(plan.targets[0].role, "issue")

    def test_private_projected_root_denies_before_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            denied_context = transaction._json_value(plan._project_context)
            denied_context.update(
                transaction.project_operation.compute_project_policy(
                    "archived",
                    "internal",
                )
            )
            cases = (
                (
                    replace(plan, _project_context=denied_context),
                    transaction.project_operation.ProjectOperationDenied,
                    "PROJECT_OPERATION_DENIED_ARCHIVED",
                ),
                (
                    replace(plan, _project_context={"status": "unresolved"}),
                    transaction.LifecycleProjectedValidationError,
                    "PROJECTED_CONTEXT_INVALID",
                ),
                (
                    replace(plan, transaction_id="../escape"),
                    transaction.LifecycleProjectedValidationError,
                    "PROJECTED_CONTEXT_INVALID",
                ),
            )

            for candidate, error_type, expected_code in cases:
                with self.subTest(expected_code=expected_code):
                    with (
                        mock.patch.object(transaction.os, "open") as open_file,
                        mock.patch.object(transaction.os, "mkdir") as mkdir,
                    ):
                        with self.assertRaises(error_type) as raised:
                            with transaction._private_projected_root(candidate):
                                self.fail("denied projected root must not be yielded")
                    open_file.assert_not_called()
                    mkdir.assert_not_called()
                    actual_code = (
                        raised.exception.decision["reason_code"]
                        if isinstance(
                            raised.exception,
                            transaction.project_operation.ProjectOperationDenied,
                        )
                        else raised.exception.code
                    )
                    self.assertEqual(actual_code, expected_code)

            control_root = root / ".moduflow"
            real_control_root = root / "real-moduflow"
            control_root.rename(real_control_root)
            control_root.symlink_to(real_control_root, target_is_directory=True)
            with self.assertRaises(
                transaction.LifecycleProjectedValidationError
            ) as raised:
                with transaction._private_projected_root(plan):
                    self.fail("symlinked control root must not be yielded")
            self.assertEqual(raised.exception.code, "PROJECTED_ROOT_UNAVAILABLE")
            self.assertFalse(
                any("-projected-" in path.name for path in real_control_root.iterdir())
            )

    def test_private_projected_root_is_same_project_mode_0700_and_ephemeral(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }

            with transaction._private_projected_root(plan) as projected_root:
                projected_root.relative_to(root.resolve() / ".moduflow")
                self.assertTrue(projected_root.is_dir())
                self.assertEqual(
                    stat.S_IMODE(projected_root.stat().st_mode),
                    0o700,
                )
                self.assertTrue((projected_root / ".moduflow/config.json").is_file())
                self.assertTrue((projected_root / "issues/BIZ-103.md").is_file())

            self.assertFalse(projected_root.exists())
            after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_private_projected_root_copies_only_configured_snapshot_privately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, nested=True)
            selected = {
                "product/specs/BIZ-103/spec.md": b"# Spec\n",
                "product/knowledge/index.md": b"# Knowledge\n",
                "product/memory/notes/note.md": b"# Note\n",
                "product/memory/production-records/record.md": b"# Record\n",
                "product/playbooks/runbook.md": b"# Runbook\n",
                "product/workflow/review-gates.md": b"# Gates\n",
                ".moduflow/project-profile.md": b"# Profile\n",
                ".moduflow/environments.json": b"{}\n",
                ".moduflow/integrations.json": b"{}\n",
                ".moduflow/humans.json": b"[]\n",
            }
            for relative, payload in selected.items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            unrelated = {
                "README.md": b"unrelated root file\n",
                ".git/ignored": b"unrelated git file\n",
            }
            for relative, payload in unrelated.items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )

            with transaction._private_projected_root(plan) as projected_root:
                expected = {
                    **selected,
                    ".moduflow/config.json": (root / ".moduflow/config.json").read_bytes(),
                    ".moduflow/state.json": (root / ".moduflow/state.json").read_bytes(),
                    "product/issues/BIZ-103.md": (
                        root / "product/issues/BIZ-103.md"
                    ).read_bytes(),
                    "product/workspace/dashboard.md": (
                        root / "product/workspace/dashboard.md"
                    ).read_bytes(),
                }
                for relative, payload in expected.items():
                    self.assertTrue(
                        (projected_root / relative).is_file(),
                        f"missing projected snapshot file: {relative}",
                    )
                    self.assertEqual((projected_root / relative).read_bytes(), payload)
                for relative in (
                    "README.md",
                    ".git/ignored",
                    "issues/BIZ-103.md",
                    "workspace/dashboard.md",
                ):
                    self.assertFalse((projected_root / relative).exists())
                for path in projected_root.rglob("*"):
                    expected_mode = 0o700 if path.is_dir() else 0o600
                    self.assertEqual(stat.S_IMODE(path.stat().st_mode), expected_mode)

            after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_projected_copy_roots_prune_nested_canonical_roles(self):
        context = {
            "relative_paths": {
                "issues": "product/issues",
                "specs": "product/specs",
                "workspace": "product/workspace",
                "knowledge": "product/knowledge",
                "memory": "product/memory",
                "production_records": "product/memory/production-records",
                "playbooks": "product/playbooks",
                "workflow": "product/workflow",
            }
        }

        copy_roots = getattr(transaction, "_projected_copy_roots", None)
        self.assertIsNotNone(copy_roots)
        self.assertEqual(
            copy_roots(context),
            (
                ("product", "issues"),
                ("product", "knowledge"),
                ("product", "memory"),
                ("product", "playbooks"),
                ("product", "specs"),
                ("product", "workflow"),
                ("product", "workspace"),
            ),
        )

    def test_projected_target_preflight_rejects_invalid_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            target = plan.targets[0]
            cases = (
                replace(plan, targets=(replace(target, relative_path="../escape"),)),
                replace(plan, targets=(target, target)),
                replace(
                    plan,
                    targets=(replace(target, after_size=target.after_size + 1),),
                ),
                replace(
                    plan,
                    targets=(replace(target, after_sha256="0" * 64),),
                ),
            )
            preflight = getattr(transaction, "_validated_projected_targets", None)
            self.assertIsNotNone(preflight)

            for candidate in cases:
                with self.subTest(targets=candidate.targets):
                    with self.assertRaises(
                        transaction.LifecycleProjectedValidationError
                    ) as raised:
                        preflight(candidate)
                    self.assertEqual(
                        raised.exception.code,
                        "PROJECTED_TARGET_INVALID",
                    )
                    self.assertEqual(
                        str(raised.exception),
                        "PROJECTED_TARGET_INVALID",
                    )

    def test_private_projected_root_rejects_unsafe_source_nodes_and_cleans_up(self):
        for node_kind in ("symlink", "fifo"):
            with self.subTest(node_kind=node_kind), tempfile.TemporaryDirectory() as tmp:
                parent = Path(tmp)
                root = parent / "project"
                root.mkdir()
                context = self.scaffold(root)
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(),
                    project_context=context,
                    clock="2030-01-02",
                )
                unsafe = root / "issues" / "unsafe-node"
                external = parent / "external-private-payload"
                external.write_bytes(b"must not be copied\n")
                if node_kind == "symlink":
                    unsafe.symlink_to(external)
                else:
                    os.mkfifo(unsafe)

                with self.assertRaises(
                    transaction.LifecycleProjectedValidationError
                ) as raised:
                    with transaction._private_projected_root(plan):
                        self.fail("unsafe projected source must not be yielded")

                self.assertEqual(raised.exception.code, "PROJECTED_SOURCE_UNSAFE")
                self.assertEqual(str(raised.exception), "PROJECTED_SOURCE_UNSAFE")
                self.assertEqual(external.read_bytes(), b"must not be copied\n")
                self.assertFalse(
                    any(
                        "-projected-" in path.name
                        for path in (root / ".moduflow").iterdir()
                    )
                )

    def test_private_projected_root_cleans_up_after_body_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )

            with self.assertRaisesRegex(RuntimeError, "injected body failure"):
                with transaction._private_projected_root(plan) as projected_root:
                    self.assertTrue(
                        (projected_root / ".moduflow/config.json").is_file()
                    )
                    self.assertTrue(
                        (projected_root / "issues/BIZ-103.md").is_file()
                    )
                    raise RuntimeError("injected body failure")

            self.assertFalse(projected_root.exists())
