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
            "e48c0513a012eb46329b7e51fa68b6f7e1d205a4ee6e56db5193eb653a1edbf3",
        )
        self.assertEqual(second_key, first_key)
        self.assertEqual(
            transaction.derive_transaction_id(first_context, intent),
            "txn-80b0c06ce9fe5355571a4bc8b9074bb8",
        )
        self.assertEqual(
            transaction.derive_transaction_id(second_context, intent),
            "txn-80b0c06ce9fe5355571a4bc8b9074bb8",
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
