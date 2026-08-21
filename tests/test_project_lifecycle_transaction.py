import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import project_lifecycle_transaction as transaction
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
