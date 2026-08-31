import errno
import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
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

    def test_post_apply_validation_summary_is_stage_specific_redacted_and_strict(self):
        summarize = getattr(
            transaction,
            "_summarize_post_apply_validation",
            None,
        )
        failure_summary = getattr(
            transaction,
            "_post_apply_failure_summary",
            None,
        )
        self.assertIsNotNone(summarize)
        self.assertIsNotNone(failure_summary)
        invalid = {
            "schema": "moduflow.project-validation.v1",
            "project_root": "/PRIVATE/ROOT",
            "valid": False,
            "errors": ["PRIVATE PROJECT ERROR"],
            "warnings": ["PRIVATE WARNING"],
            "issue_schema": {
                "errors": 1,
                "warnings": 1,
                "codes": ["PRIVATE_CODE"],
                "diagnostics": [{"payload": "PRIVATE PAYLOAD"}],
            },
            "lifecycle_drift": ["PRIVATE DRIFT"],
        }
        self.assertEqual(
            summarize(invalid),
            {
                "valid": False,
                "rule_ids": [
                    "canonical-targets",
                    "project-artifacts",
                    "issue-schema",
                    "lifecycle-consensus",
                    "production-records",
                ],
                "error_codes": [
                    "POST_APPLY_PROJECT_INVALID",
                    "POST_APPLY_ISSUE_SCHEMA_INVALID",
                    "POST_APPLY_LIFECYCLE_DRIFT",
                ],
            },
        )
        self.assertEqual(
            summarize({"schema": "PRIVATE MALFORMED"})["error_codes"],
            ["POST_APPLY_VALIDATION_CONTRACT_INVALID"],
        )
        for warnings in ([], ["PRIVATE WARNING"]):
            with self.subTest(warnings=warnings):
                self.assertEqual(
                    summarize(
                        {
                            "schema": "moduflow.project-validation.v1",
                            "project_root": "/PRIVATE/ROOT",
                            "valid": True,
                            "errors": [],
                            "warnings": warnings,
                            "issue_schema": {
                                "errors": 0,
                                "warnings": len(warnings),
                                "codes": [],
                                "diagnostics": [],
                            },
                            "lifecycle_drift": [],
                        }
                    ),
                    {
                        "valid": True,
                        "rule_ids": [
                            "canonical-targets",
                            "project-artifacts",
                            "issue-schema",
                            "lifecycle-consensus",
                            "production-records",
                        ],
                        "error_codes": [],
                    },
                )
        for error_code in (
            "POST_APPLY_TARGET_MISMATCH",
            "POST_APPLY_TARGET_UNPROVEN",
            "POST_APPLY_VALIDATION_FAILED",
        ):
            with self.subTest(error_code=error_code):
                self.assertEqual(
                    failure_summary(error_code),
                    {
                        "valid": False,
                        "rule_ids": [
                            "canonical-targets",
                            "project-artifacts",
                            "issue-schema",
                            "lifecycle-consensus",
                            "production-records",
                        ],
                        "error_codes": [error_code],
                    },
                )
        self.assertNotIn("PRIVATE", json.dumps(summarize(invalid)))
        with self.assertRaises(transaction.LifecycleJournalError) as raised:
            failure_summary("PRIVATE UNSAFE")
        self.assertEqual(raised.exception.code, "JOURNAL_RECORD_INVALID")

    def test_post_apply_validation_error_is_frozen_and_redacted(self):
        error_type = getattr(
            transaction,
            "LifecyclePostApplyValidationError",
            None,
        )
        self.assertIsNotNone(error_type)
        summary = {
            "valid": False,
            "rule_ids": ["canonical-targets"],
            "error_codes": ["POST_APPLY_TARGET_MISMATCH"],
        }
        error = error_type(
            "POST_APPLY_VALIDATION_INVALID",
            summary,
        )
        summary["rule_ids"].append("PRIVATE_POISON")
        summary["error_codes"].append("PRIVATE_POISON")

        self.assertEqual(error.code, "POST_APPLY_VALIDATION_INVALID")
        self.assertEqual(
            dict(error.post_apply_validation),
            {
                "valid": False,
                "rule_ids": ("canonical-targets",),
                "error_codes": ("POST_APPLY_TARGET_MISMATCH",),
            },
        )
        self.assertEqual(str(error), "POST_APPLY_VALIDATION_INVALID")
        self.assertEqual(
            repr(error),
            "LifecyclePostApplyValidationError('POST_APPLY_VALIDATION_INVALID')",
        )
        self.assertNotIn("PRIVATE", repr(error))

        invalid = (
            (
                "POST_APPLY_UNKNOWN",
                {
                    "valid": False,
                    "rule_ids": ["canonical-targets"],
                    "error_codes": ["POST_APPLY_TARGET_MISMATCH"],
                },
            ),
            (
                "POST_APPLY_VALIDATION_INVALID",
                {
                    "valid": True,
                    "rule_ids": ["canonical-targets"],
                    "error_codes": [],
                },
            ),
            (
                "POST_APPLY_VALIDATION_INVALID",
                {
                    "valid": False,
                    "rule_ids": ["unsafe value"],
                    "error_codes": ["POST_APPLY_TARGET_MISMATCH"],
                },
            ),
            (
                "POST_APPLY_VALIDATION_INVALID",
                {
                    "valid": False,
                    "rule_ids": ["canonical-targets"],
                    "error_codes": ["POST_APPLY_TARGET_MISMATCH"],
                    "private": "payload",
                },
            ),
        )
        for code, candidate in invalid:
            with self.subTest(code=code, candidate=candidate):
                with self.assertRaises(
                    transaction.LifecycleJournalError
                ) as raised:
                    error_type(code, candidate)
                self.assertEqual(
                    raised.exception.code,
                    "JOURNAL_RECORD_INVALID",
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


class TransactionEvidenceContractTests(unittest.TestCase):
    def target(self, role, index, total=2, *, after_sha256=None, after_bytes=None):
        is_evidence = role == "evidence"
        return {
            "role": role,
            "relative_path": (
                "workspace/transactions/txn-103.json"
                if is_evidence
                else "issues/103-atomic-lifecycle-state-transaction.md"
            ),
            "existed": not is_evidence,
            "before_sha256": "absent" if is_evidence else "a" * 64,
            "after_sha256": after_sha256 or (("c" if is_evidence else "b") * 64),
            "after_bytes": after_bytes if after_bytes is not None else 20 + index,
            "changed": True,
            "validation_rules": [
                "transaction-evidence-schema" if is_evidence else "issue-schema"
            ],
            "apply_order": index,
            "rollback_order": total - index - 1,
        }

    def result(self, status="applied", *, targets=None):
        failed = status not in {"applied", "noop"}
        return {
            "schema": "moduflow.lifecycle-transaction.v1",
            "transaction_id": "txn-103",
            "idempotency_key": "d" * 64,
            "status": status,
            "project_id": "alpha",
            "canonical_root": "/private/projects/alpha",
            "issue_id": "103-atomic-lifecycle-state-transaction",
            "action": "start",
            "target_lifecycle": "active",
            "targets": targets or [
                self.target("issue", 0),
                self.target("evidence", 1),
            ],
            "projected_validation": {
                "valid": True,
                "rule_ids": ["project-artifacts"],
                "error_codes": [],
            },
            "post_apply_validation": {
                "valid": True,
                "rule_ids": ["project-artifacts"],
                "error_codes": [],
            },
            "failed_stage": "apply" if failed else "",
            "error_code": "APPLY_FAILED" if failed else "",
            "rollback_status": "not-required" if not failed else "verified",
            "verified_target_count": 2,
            "next_command": "product:status",
            "actor": "dongwon",
            "source_event": "request:B1d",
            "created_at": "2030-01-01T00:00:00Z",
            "started_at": "2030-01-01T00:00:01Z",
            "completed_at": "2030-01-01T00:00:02Z",
        }

    def expected_evidence(self, status="applied"):
        failed = status not in {"applied", "noop"}
        return {
            "schema": "moduflow.lifecycle-transaction-evidence.v1",
            "transaction_id": "txn-103",
            "idempotency_key": "d" * 64,
            "status": status,
            "project_id": "alpha",
            "issue_id": "103-atomic-lifecycle-state-transaction",
            "action": "start",
            "target_lifecycle": "active",
            "targets": [
                {
                    "role": "issue",
                    "relative_path": "issues/103-atomic-lifecycle-state-transaction.md",
                    "existed": True,
                    "before_sha256": "a" * 64,
                    "after_sha256": "b" * 64,
                    "after_bytes": 20,
                    "changed": True,
                    "validation_rules": ["issue-schema"],
                    "apply_order": 0,
                    "rollback_order": 1,
                }
            ],
            "projected_validation": {
                "valid": True,
                "rule_ids": ["project-artifacts"],
                "error_codes": [],
            },
            "post_apply_validation": {
                "valid": True,
                "rule_ids": ["project-artifacts"],
                "error_codes": [],
            },
            "failed_stage": "apply" if failed else "",
            "error_code": "APPLY_FAILED" if failed else "",
            "rollback_status": "not-required" if not failed else "verified",
            "verified_target_count": 2,
            "next_command": "product:status",
            "actor": "dongwon",
            "source_event": "request:B1d",
            "created_at": "2030-01-01T00:00:00Z",
            "started_at": "2030-01-01T00:00:01Z",
            "completed_at": "2030-01-01T00:00:02Z",
        }

    def test_evidence_serializer_returns_exact_redacted_result_without_self_target(self):
        serializer = getattr(transaction, "serialize_transaction_evidence", None)
        self.assertIsNotNone(serializer)
        result = self.result()

        evidence = serializer(result)

        self.assertEqual(evidence, self.expected_evidence())
        self.assertNotIn("canonical_root", evidence)
        self.assertEqual([target["role"] for target in evidence["targets"]], ["issue"])

    def test_evidence_renderer_is_deterministic_detached_and_not_self_referential(self):
        serializer = getattr(transaction, "serialize_transaction_evidence", None)
        renderer = getattr(transaction, "render_transaction_evidence", None)
        self.assertIsNotNone(serializer)
        self.assertIsNotNone(renderer)
        first_result = self.result()
        second_result = self.result(
            targets=[
                self.target("issue", 0),
                self.target(
                    "evidence",
                    1,
                    after_sha256="e" * 64,
                    after_bytes=999,
                ),
            ]
        )

        evidence = serializer(first_result)
        first_bytes = renderer(first_result)
        second_bytes = renderer(second_result)
        expected_bytes = (
            json.dumps(
                self.expected_evidence(),
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ).encode("utf-8")
            + b"\n"
        )
        first_result["targets"][0]["validation_rules"].append("poison")
        first_result["projected_validation"]["rule_ids"].append("poison")
        first_result["post_apply_validation"]["rule_ids"].append("poison")

        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first_bytes, expected_bytes)
        self.assertTrue(first_bytes.endswith(b"\n"))
        self.assertFalse(first_bytes.endswith(b"\n\n"))
        self.assertEqual(evidence, self.expected_evidence())

    def test_evidence_serializer_rejects_missing_duplicate_or_nonfinal_self_target(self):
        serializer = getattr(transaction, "serialize_transaction_evidence", None)
        self.assertIsNotNone(serializer)
        secret = "workspace/transactions/SECRET-CONTENT.json"
        duplicate_secret = self.target("evidence", 2, total=3)
        duplicate_secret["relative_path"] = secret
        nonfinal_secret = self.target("evidence", 0)
        nonfinal_secret["relative_path"] = secret
        cases = (
            [self.target("issue", 0, total=1)],
            [
                self.target("issue", 0, total=3),
                self.target("evidence", 1, total=3),
                duplicate_secret,
            ],
            [nonfinal_secret, self.target("issue", 1)],
        )

        for targets in cases:
            with self.subTest(targets=[target["role"] for target in targets]):
                with self.assertRaises(ValueError) as raised:
                    serializer(self.result(targets=targets))
                self.assertEqual(
                    str(raised.exception),
                    "Transaction evidence target layout invalid",
                )
                self.assertNotIn(secret, str(raised.exception))
                self.assertNotIn(secret, repr(raised.exception))

    def test_evidence_contract_reuses_all_statuses_and_has_zero_io_or_private_output(self):
        serializer = getattr(transaction, "serialize_transaction_evidence", None)
        renderer = getattr(transaction, "render_transaction_evidence", None)
        self.assertIsNotNone(serializer)
        self.assertIsNotNone(renderer)
        forbidden = (
            "/private/projects/alpha",
            "_before_bytes",
            "_after_bytes",
            "preimages/",
            ".moduflow-stage-",
            "recovery-manifest",
            "journal.json",
            "owner_token",
            "workspace/transactions/txn-103.json",
        )

        with (
            mock.patch.object(transaction.os, "open") as open_file,
            mock.patch.object(transaction.os, "mkdir") as make_directory,
            mock.patch.object(transaction.os, "fsync") as sync_file,
            mock.patch.object(transaction.os, "replace") as replace_file,
        ):
            for status in (
                "applied",
                "noop",
                "denied",
                "conflict",
                "rolled_back",
                "recovery_required",
            ):
                with self.subTest(status=status):
                    result = self.result(status)
                    evidence = serializer(result)
                    rendered = renderer(result).decode("utf-8")
                    self.assertEqual(evidence, self.expected_evidence(status))
                    self.assertTrue(all(value not in rendered for value in forbidden))

        open_file.assert_not_called()
        make_directory.assert_not_called()
        sync_file.assert_not_called()
        replace_file.assert_not_called()
        with self.assertRaisesRegex(ValueError, "^Unsupported transaction status$"):
            serializer(self.result("unknown"))


class TransactionJournalContractTests(unittest.TestCase):
    def target(self, index, total=2):
        return {
            "role": ("issue", "evidence")[index],
            "relative_path": (
                "issues/103-atomic-lifecycle-state-transaction.md",
                "workspace/transactions/txn-103.json",
            )[index],
            "existed": index == 0,
            "before_sha256": "a" * 64 if index == 0 else "absent",
            "after_sha256": ("b", "c")[index] * 64,
            "after_bytes": 10 + index,
            "changed": True,
            "validation_rules": [
                "issue-schema" if index == 0 else "transaction-evidence-schema"
            ],
            "apply_order": index,
            "rollback_order": total - index - 1,
        }

    def journal(
        self,
        phase="planned",
        *,
        manifest="absent",
        applied=None,
        rollback=None,
    ):
        return {
            "schema": "moduflow.lifecycle-transaction-journal.v1",
            "transaction_id": "txn-103",
            "idempotency_key": "d" * 64,
            "phase": phase,
            "targets": [self.target(0), self.target(1)],
            "recovery_manifest_sha256": manifest,
            "applied_target_indexes": list(applied or []),
            "rollback_target_indexes": list(rollback or []),
            "created_at": "2030-01-01T00:00:00Z",
            "updated_at": "2030-01-01T00:00:01Z",
        }

    def test_journal_serializer_accepts_exact_phase_snapshots(self):
        serializer = getattr(transaction, "serialize_transaction_journal", None)
        self.assertIsNotNone(serializer)
        digest = "e" * 64
        cases = (
            ("planned", "absent", [], []),
            ("staged", "absent", [], []),
            ("prepared", digest, [], []),
            ("applying", digest, [0], []),
            ("post-validating", digest, [0], []),
            ("finalizing", digest, [0], []),
            ("finalizing", digest, [0, 1], []),
            ("rolling-back", digest, [0, 1], [1]),
            ("complete", digest, [0, 1], []),
            ("rolled-back", digest, [0, 1], [1, 0]),
            ("recovery-required", "absent", [], []),
        )

        for phase, manifest, applied, rollback in cases:
            with self.subTest(phase=phase):
                journal = self.journal(
                    phase,
                    manifest=manifest,
                    applied=applied,
                    rollback=rollback,
                )
                self.assertEqual(
                    serializer(journal),
                    journal,
                )

    def test_journal_schema_and_phase_failures_are_stable_and_redacted(self):
        serializer = getattr(transaction, "serialize_transaction_journal", None)
        error_type = getattr(transaction, "LifecycleJournalError", None)
        self.assertIsNotNone(serializer)
        self.assertIsNotNone(error_type)
        secret = "/private/recovery/SECRET-CONTENT"
        cases = (
            ({**self.journal(), "private_payload": secret}, "JOURNAL_RECORD_INVALID"),
            ({**self.journal(), "schema": secret}, "JOURNAL_SCHEMA_UNSUPPORTED"),
            ({**self.journal(), "phase": secret}, "JOURNAL_PHASE_INVALID"),
            ({**self.journal(), "created_at": {"secret": secret}}, "JOURNAL_RECORD_INVALID"),
        )

        for journal, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(error_type) as raised:
                    serializer(journal)
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(str(raised.exception), code)
                self.assertNotIn(secret, str(raised.exception))

    def test_journal_phase_transition_contract_distinguishes_recovery(self):
        transition = getattr(transaction, "validate_journal_phase_transition", None)
        error_type = getattr(transaction, "LifecycleJournalError", None)
        self.assertIsNotNone(transition)
        self.assertIsNotNone(error_type)
        valid = (
            ("planned", "staged", False),
            ("staged", "prepared", False),
            ("prepared", "applying", False),
            ("applying", "applying", False),
            ("applying", "post-validating", False),
            ("post-validating", "finalizing", False),
            ("finalizing", "finalizing", False),
            ("finalizing", "complete", False),
            ("prepared", "rolling-back", False),
            ("rolling-back", "rolling-back", False),
            ("rolling-back", "rolled-back", False),
            ("recovery-required", "rolling-back", True),
            ("recovery-required", "finalizing", True),
        )
        for current, following, recovery in valid:
            with self.subTest(current=current, following=following, recovery=recovery):
                transition(
                    current,
                    following,
                    recovery=recovery,
                )

        invalid = (
            ("complete", "applying", False, "JOURNAL_TRANSITION_INVALID"),
            ("rolled-back", "rolling-back", True, "JOURNAL_TRANSITION_INVALID"),
            ("recovery-required", "rolling-back", False, "JOURNAL_TRANSITION_INVALID"),
            ("unknown", "staged", False, "JOURNAL_PHASE_INVALID"),
            ("planned", "unknown", False, "JOURNAL_PHASE_INVALID"),
        )
        for current, following, recovery, code in invalid:
            with self.subTest(current=current, following=following, recovery=recovery):
                with self.assertRaises(error_type) as raised:
                    transition(
                        current,
                        following,
                        recovery=recovery,
                    )
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(str(raised.exception), code)

    def test_journal_rejects_invalid_progress_and_phase_invariants(self):
        serializer = getattr(transaction, "serialize_transaction_journal", None)
        self.assertIsNotNone(serializer)
        digest = "e" * 64
        cases = (
            (self.journal("applying", manifest=digest, applied=[1]), "non-prefix"),
            (self.journal("applying", manifest=digest, applied=[0, 0]), "duplicate"),
            (self.journal("applying", manifest=digest, applied=[True]), "boolean"),
            (self.journal("applying", manifest=digest, applied=[2]), "out-of-range"),
            (
                self.journal(
                    "rolling-back",
                    manifest=digest,
                    applied=[0, 1],
                    rollback=[0],
                ),
                "rollback-order",
            ),
            (self.journal("prepared", manifest=digest, applied=[0]), "prepared-progress"),
            (
                self.journal("post-validating", manifest=digest, applied=[]),
                "incomplete-canonical-apply",
            ),
            (
                self.journal("post-validating", manifest=digest, applied=[0, 1]),
                "early-evidence-apply",
            ),
            (self.journal("prepared", manifest="absent"), "missing-manifest"),
            (self.journal("staged", manifest=digest), "early-manifest"),
            (
                self.journal("recovery-required", applied=[0]),
                "recovery-progress-without-manifest",
            ),
            (
                self.journal("rolled-back", applied=[0], rollback=[0]),
                "rollback-progress-without-manifest",
            ),
        )

        for journal, label in cases:
            with self.subTest(label=label):
                with self.assertRaises(transaction.LifecycleJournalError) as raised:
                    serializer(journal)
                self.assertEqual(raised.exception.code, "JOURNAL_PROGRESS_INVALID")
                self.assertEqual(str(raised.exception), "JOURNAL_PROGRESS_INVALID")

    def test_journal_rejects_ambiguous_targets_and_invalid_manifest_values(self):
        serializer = getattr(transaction, "serialize_transaction_journal", None)
        self.assertIsNotNone(serializer)
        wrong_order = self.journal()
        wrong_order["targets"][0]["apply_order"] = 1
        absolute_path = self.journal()
        absolute_path["targets"][0]["relative_path"] = "/private/SECRET"
        invalid_manifest = self.journal("prepared", manifest="SECRET-MANIFEST")

        for journal in (wrong_order, absolute_path, invalid_manifest):
            with self.subTest(journal=journal):
                with self.assertRaises(transaction.LifecycleJournalError) as raised:
                    serializer(journal)
                self.assertEqual(raised.exception.code, "JOURNAL_RECORD_INVALID")
                self.assertEqual(str(raised.exception), "JOURNAL_RECORD_INVALID")
                self.assertNotIn("SECRET", str(raised.exception))

    def test_journal_output_is_detached_redacted_and_has_zero_io(self):
        serializer = getattr(transaction, "serialize_transaction_journal", None)
        self.assertIsNotNone(serializer)
        journal = self.journal(
            "applying",
            manifest="e" * 64,
            applied=[0],
        )
        with (
            mock.patch.object(transaction.os, "open") as open_file,
            mock.patch.object(transaction.os, "mkdir") as make_directory,
            mock.patch.object(transaction.os, "fsync") as sync_file,
            mock.patch.object(transaction.os, "replace") as replace_file,
        ):
            rendered = serializer(journal)

        journal["targets"][0]["validation_rules"].append("private-rule")
        journal["applied_target_indexes"].append(1)
        journal["rollback_target_indexes"].append(0)

        self.assertEqual(rendered["targets"][0]["validation_rules"], ["issue-schema"])
        self.assertEqual(rendered["applied_target_indexes"], [0])
        self.assertEqual(rendered["rollback_target_indexes"], [])
        serialized = json.dumps(rendered, ensure_ascii=False)
        self.assertNotIn("_before_bytes", serialized)
        self.assertNotIn("_after_bytes", serialized)
        self.assertNotIn("canonical_root", serialized)
        self.assertNotIn("/private/", serialized)
        open_file.assert_not_called()
        make_directory.assert_not_called()
        sync_file.assert_not_called()
        replace_file.assert_not_called()


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

    def validation_result(
        self,
        *,
        valid=True,
        errors=None,
        issue_errors=0,
        lifecycle_drift=None,
        warnings=None,
    ):
        return {
            "schema": "moduflow.project-validation.v1",
            "project_root": "PRIVATE OMITTED",
            "valid": valid,
            "errors": list(errors or ()),
            "warnings": list(warnings or ()),
            "issue_schema": {
                "errors": issue_errors,
                "warnings": 0,
                "codes": [],
                "diagnostics": [],
            },
            "lifecycle_drift": list(lifecycle_drift or ()),
        }

    def projected_summary(self):
        return transaction._summarize_projected_validation(
            self.validation_result()
        )

    def completion_input(self, plan):
        state_target = next(
            target for target in plan.targets if target.role == "state"
        )
        next_command = json.loads(state_target._after_bytes)["next_command"]
        return transaction._prepare_completion_input(
            plan,
            self.intent(require_issue_index=True),
            next_command,
            self.projected_summary(),
        )

    def public_clock(self):
        values = [date(2030, 1, 2)]
        start = datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        values.extend(
            start + timedelta(seconds=index)
            for index in range(80)
        )
        iterator = iter(values)
        return lambda: next(iterator)

    def apply_privately_once(self, root, context, intent):
        (root / "workspace" / "transactions").mkdir(exist_ok=True)
        plan = transaction.plan_lifecycle_transaction(
            root,
            intent,
            project_context=context,
            clock="2030-01-02",
        )
        completion = transaction._prepare_completion_input(
            plan,
            intent,
            transaction._planned_next_command(plan),
            self.projected_summary(),
        )
        changed_count = sum(
            target.changed and target.role != "evidence"
            for target in plan.targets
        )
        timestamps = iter(
            tuple(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(5, 5 + 11 + 2 * changed_count)
            )
        )
        with mock.patch.object(
            transaction.validate_project_artifacts,
            "validate_project",
            return_value=self.validation_result(),
        ):
            with transaction._private_applied_workspace(
                plan,
                completion_input=completion,
                journal_clock=lambda: next(timestamps),
                lock_clock="2030-01-02T03:05:30Z",
                lock_pid=103,
                lock_token_factory=lambda: "a" * 32,
            ) as completed:
                return transaction._json_value(completed.transaction_result)

    def prepare_restart_recovery_case(
        self,
        root,
        phase_case,
        *,
        applied_count=0,
        rollback_count=0,
    ):
        context = self.scaffold(root)
        (root / "workspace" / "transactions").mkdir()
        plan = transaction.plan_lifecycle_transaction(
            root,
            self.intent(),
            project_context=context,
            clock="2030-01-02",
        )
        setup_times = iter(
            f"2030-01-02T03:04:{second:02d}Z"
            for second in range(5, 40)
        )
        with transaction._private_prepared_workspace(
            plan,
            journal_clock=lambda: next(setup_times),
            lock_clock="2030-01-02T03:04:04Z",
            lock_pid=103,
            lock_token_factory=lambda: "a" * 32,
        ) as prepared:
            changed = [
                (target, preimage, proposal)
                for target, preimage, proposal in zip(
                    prepared.storage_targets,
                    prepared.preimages,
                    prepared.staged_proposals,
                )
                if target.changed and target.role != "evidence"
            ]
            latest = prepared.journal_sha256
            applied = []
            rollback = []
            if phase_case != "prepared":
                latest = transaction._persist_progress_journal(
                    prepared,
                    plan,
                    phase="applying",
                    updated_at=next(setup_times),
                    applied_target_indexes=(),
                    rollback_target_indexes=(),
                    expected_previous_sha256=latest,
                )
                for position, (target, _preimage, proposal) in enumerate(
                    changed[:applied_count]
                ):
                    transaction.transaction_storage.apply_staged_target(
                        prepared._workspace,
                        target,
                        proposal,
                    )
                    applied.append(target.index)
                    unjournaled_apply = (
                        phase_case == "applying-unrecorded"
                        and position == applied_count - 1
                    )
                    if not unjournaled_apply:
                        latest = transaction._persist_progress_journal(
                            prepared,
                            plan,
                            phase="applying",
                            updated_at=next(setup_times),
                            applied_target_indexes=tuple(applied),
                            rollback_target_indexes=(),
                            expected_previous_sha256=latest,
                        )
                if phase_case == "post-validating":
                    latest = transaction._persist_progress_journal(
                        prepared,
                        plan,
                        phase="post-validating",
                        updated_at=next(setup_times),
                        applied_target_indexes=tuple(applied),
                        rollback_target_indexes=(),
                        expected_previous_sha256=latest,
                    )
                elif phase_case in {
                    "rolling-back-recorded",
                    "rolling-back-unrecorded",
                }:
                    latest = transaction._persist_progress_journal(
                        prepared,
                        plan,
                        phase="rolling-back",
                        updated_at=next(setup_times),
                        applied_target_indexes=tuple(applied),
                        rollback_target_indexes=(),
                        expected_previous_sha256=latest,
                    )
                    for position, (target, preimage, _proposal) in enumerate(
                        tuple(reversed(changed[:applied_count]))[:rollback_count]
                    ):
                        transaction._rollback_changed_target(
                            prepared._workspace,
                            target,
                            preimage,
                        )
                        rollback.append(target.index)
                        unjournaled_rollback = (
                            phase_case == "rolling-back-unrecorded"
                            and position == rollback_count - 1
                        )
                        if not unjournaled_rollback:
                            latest = transaction._persist_progress_journal(
                                prepared,
                                plan,
                                phase="rolling-back",
                                updated_at=next(setup_times),
                                applied_target_indexes=tuple(applied),
                                rollback_target_indexes=tuple(rollback),
                                expected_previous_sha256=latest,
                            )
            return context, plan, tuple(applied), tuple(rollback)

    def prepare_restart_finalizing_case(self, root, evidence_state):
        context = self.scaffold(root)
        (root / "workspace" / "transactions").mkdir()
        plan = transaction.plan_lifecycle_transaction(
            root,
            self.intent(),
            project_context=context,
            clock="2030-01-02",
        )
        setup_times = iter(
            f"2030-01-02T03:04:{second:02d}Z"
            for second in range(5, 40)
        )
        with transaction._private_prepared_workspace(
            plan,
            journal_clock=lambda: next(setup_times),
            lock_clock="2030-01-02T03:04:04Z",
            lock_pid=103,
            lock_token_factory=lambda: "a" * 32,
        ) as prepared:
            changed_ordinary = [
                (target, proposal)
                for target, proposal in zip(
                    prepared.storage_targets,
                    prepared.staged_proposals,
                )
                if target.changed and target.role != "evidence"
            ]
            latest = transaction._persist_progress_journal(
                prepared,
                plan,
                phase="applying",
                updated_at=next(setup_times),
                applied_target_indexes=(),
                rollback_target_indexes=(),
                expected_previous_sha256=prepared.journal_sha256,
            )
            applied = []
            for target, proposal in changed_ordinary:
                transaction.transaction_storage.apply_staged_target(
                    prepared._workspace,
                    target,
                    proposal,
                )
                applied.append(target.index)
                latest = transaction._persist_progress_journal(
                    prepared,
                    plan,
                    phase="applying",
                    updated_at=next(setup_times),
                    applied_target_indexes=tuple(applied),
                    rollback_target_indexes=(),
                    expected_previous_sha256=latest,
                )
            latest = transaction._persist_progress_journal(
                prepared,
                plan,
                phase="post-validating",
                updated_at=next(setup_times),
                applied_target_indexes=tuple(applied),
                rollback_target_indexes=(),
                expected_previous_sha256=latest,
            )
            latest = transaction._persist_progress_journal(
                prepared,
                plan,
                phase="finalizing",
                updated_at=next(setup_times),
                applied_target_indexes=tuple(applied),
                rollback_target_indexes=(),
                expected_previous_sha256=latest,
            )
            if evidence_state in {"after-unrecorded", "after-recorded"}:
                evidence = prepared.storage_targets[-1]
                proposal = prepared.staged_proposals[-1]
                transaction.transaction_storage.finalize_staged_evidence(
                    prepared._workspace,
                    evidence,
                    proposal,
                )
                applied.append(evidence.index)
                if evidence_state == "after-recorded":
                    transaction._persist_progress_journal(
                        prepared,
                        plan,
                        phase="finalizing",
                        updated_at=next(setup_times),
                        applied_target_indexes=tuple(applied),
                        rollback_target_indexes=(),
                        expected_previous_sha256=latest,
                    )
        return context, plan

    def test_completed_replay_returns_strict_noop_from_original_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            applied = self.apply_privately_once(root, context, intent)
            replay_plan = transaction.plan_lifecycle_transaction(
                root,
                intent,
                project_context=context,
                clock="2030-01-03",
            )

            result = transaction._completed_replay_result(replay_plan, intent)

            self.assertEqual(result["status"], "noop")
            self.assertEqual(result["transaction_id"], applied["transaction_id"])
            self.assertEqual(result["idempotency_key"], applied["idempotency_key"])
            self.assertEqual(result["created_at"], applied["created_at"])
            self.assertEqual(result["completed_at"], applied["completed_at"])
            self.assertEqual(result["targets"][:-1], applied["targets"][:-1])
            self.assertEqual(result["targets"][-1]["role"], "evidence")
            self.assertTrue(result["targets"][-1]["existed"])
            self.assertFalse(result["targets"][-1]["changed"])
            self.assertEqual(
                result["targets"][-1]["before_sha256"],
                result["targets"][-1]["after_sha256"],
            )
            self.assertEqual(
                result,
                transaction.serialize_transaction_result(result),
            )

    def test_completed_replay_returns_none_only_when_evidence_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            plan = transaction.plan_lifecycle_transaction(
                root,
                intent,
                project_context=context,
                clock="2030-01-02",
            )

            self.assertIsNone(
                transaction._completed_replay_result(plan, intent)
            )

    def test_completed_replay_rejects_malformed_foreign_and_reordered_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            applied = self.apply_privately_once(root, context, intent)
            evidence_path = root / applied["targets"][-1]["relative_path"]
            original_bytes = evidence_path.read_bytes()
            original = json.loads(original_bytes)
            cases = {
                "malformed": b"{PRIVATE-BROKEN\n",
                "unknown-key": {
                    **original,
                    "private": "PRIVATE-FORBIDDEN",
                },
                "non-applied": {**original, "status": "noop"},
                "foreign-id": {
                    **original,
                    "transaction_id": "txn-foreign",
                },
                "reordered": {
                    **original,
                    "targets": list(reversed(original["targets"])),
                },
            }

            for label, candidate in cases.items():
                with self.subTest(label=label):
                    if isinstance(candidate, bytes):
                        evidence_path.write_bytes(candidate)
                    else:
                        evidence_path.write_text(
                            json.dumps(
                                candidate,
                                ensure_ascii=False,
                                sort_keys=True,
                                indent=2,
                            )
                            + "\n",
                            encoding="utf-8",
                        )
                    replay_plan = transaction.plan_lifecycle_transaction(
                        root,
                        intent,
                        project_context=context,
                        clock="2030-01-03",
                    )

                    with self.assertRaises(
                        transaction.LifecycleReplayConflict
                    ) as raised:
                        transaction._completed_replay_result(
                            replay_plan,
                            intent,
                        )

                    self.assertEqual(
                        raised.exception.code,
                        "REPLAY_EVIDENCE_CONFLICT",
                    )
                    rendered_error = str(raised.exception) + repr(
                        raised.exception
                    )
                    self.assertNotIn(str(root.resolve()), rendered_error)
                    self.assertNotIn("PRIVATE", rendered_error)
                    evidence_path.write_bytes(original_bytes)

    def test_completed_replay_rejects_canonical_drift_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            applied = self.apply_privately_once(root, context, intent)
            issue_path = root / applied["targets"][0]["relative_path"]
            issue_path.write_text(
                issue_path.read_text(encoding="utf-8")
                + "\nPRIVATE EXTERNAL EDIT\n",
                encoding="utf-8",
            )
            replay_plan = transaction.plan_lifecycle_transaction(
                root,
                intent,
                project_context=context,
                clock="2030-01-03",
            )

            with (
                mock.patch.object(transaction.os, "replace") as replacement,
                mock.patch.object(
                    transaction,
                    "validate_projected_transaction",
                ) as validator,
                mock.patch.object(
                    transaction.transaction_storage,
                    "private_transaction_workspace",
                ) as workspace,
                self.assertRaises(
                    transaction.LifecycleReplayConflict
                ) as raised,
            ):
                transaction._completed_replay_result(replay_plan, intent)

            self.assertEqual(
                raised.exception.code,
                "REPLAY_CANONICAL_DRIFT",
            )
            rendered_error = str(raised.exception) + repr(raised.exception)
            self.assertNotIn(str(root.resolve()), rendered_error)
            self.assertNotIn("PRIVATE", rendered_error)
            replacement.assert_not_called()
            validator.assert_not_called()
            workspace.assert_not_called()

    def test_public_apply_returns_private_completed_result_then_zero_work_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            (root / "workspace" / "transactions").mkdir()
            intent = self.intent(require_issue_index=True)

            with mock.patch.object(
                transaction.validate_project_artifacts,
                "validate_project",
                return_value=self.validation_result(),
            ):
                applied = transaction.apply_lifecycle_transaction(
                    root,
                    intent,
                    project_context=context,
                    clock=self.public_clock(),
                )

            with (
                mock.patch.object(
                    transaction,
                    "validate_projected_transaction",
                ) as validator,
                mock.patch.object(
                    transaction,
                    "_private_applied_workspace",
                ) as private_apply,
                mock.patch.object(
                    transaction,
                    "_journal_timestamps",
                ) as journal_timestamps,
                mock.patch.object(
                    transaction,
                    "_lock_timestamp",
                ) as lock_timestamp,
                mock.patch.object(
                    transaction.transaction_storage,
                    "private_transaction_workspace",
                ) as workspace,
                mock.patch.object(transaction.os, "replace") as replacement,
            ):
                noop = transaction.apply_lifecycle_transaction(
                    root,
                    intent,
                    project_context=context,
                    clock="2030-01-03",
                )

            self.assertEqual(applied["status"], "applied")
            self.assertEqual(
                applied,
                transaction.serialize_transaction_result(applied),
            )
            self.assertEqual(noop["status"], "noop")
            self.assertEqual(
                noop["transaction_id"],
                applied["transaction_id"],
            )
            validator.assert_not_called()
            private_apply.assert_not_called()
            journal_timestamps.assert_not_called()
            lock_timestamp.assert_not_called()
            workspace.assert_not_called()
            replacement.assert_not_called()

    def test_public_apply_denial_has_zero_transaction_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            denial = transaction.project_operation.ProjectOperationDenied({
                "message": "PRIVATE DENIAL",
                "reason_code": "PROJECT_OPERATION_DENIED_READ_ONLY",
            })

            with (
                mock.patch.object(
                    transaction,
                    "_writable_projected_plan_context",
                    side_effect=denial,
                ),
                mock.patch.object(transaction.os, "mkdir") as make_directory,
                mock.patch.object(transaction.os, "replace") as replacement,
                mock.patch.object(
                    transaction.transaction_storage,
                    "private_transaction_workspace",
                ) as workspace,
                mock.patch.object(
                    transaction.transaction_storage,
                    "persist_serialized_journal",
                ) as persist,
            ):
                result = transaction.apply_lifecycle_transaction(
                    root,
                    intent,
                    project_context=context,
                    clock=self.public_clock(),
                )

            self.assertEqual(result["status"], "denied")
            self.assertEqual(result["failed_stage"], "authorization")
            self.assertEqual(
                result["error_code"],
                "PROJECT_OPERATION_DENIED_READ_ONLY",
            )
            self.assertEqual(
                result,
                transaction.serialize_transaction_result(result),
            )
            self.assertNotIn("PRIVATE", json.dumps(result))
            make_directory.assert_not_called()
            replacement.assert_not_called()
            workspace.assert_not_called()
            persist.assert_not_called()

    def test_public_apply_maps_replay_and_projected_conflicts_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            projected_invalid = {
                "valid": False,
                "rule_ids": list(
                    transaction._PROJECTED_VALIDATION_RULE_IDS
                ),
                "error_codes": ["PROJECTED_PROJECT_INVALID"],
            }
            cases = (
                (
                    "replay",
                    {
                        "replay": transaction.LifecycleReplayConflict(
                            "REPLAY_EVIDENCE_CONFLICT"
                        )
                    },
                    "replay",
                    "REPLAY_EVIDENCE_CONFLICT",
                ),
                (
                    "projected-invalid",
                    {"projected": projected_invalid},
                    "projected-validation",
                    "PROJECTED_VALIDATION_INVALID",
                ),
                (
                    "projected-failed",
                    {
                        "projected": (
                            transaction.LifecycleProjectedValidationError(
                                "PROJECTED_VALIDATION_FAILED"
                            )
                        )
                    },
                    "projected-validation",
                    "PROJECTED_VALIDATION_FAILED",
                ),
            )

            for label, configured, failed_stage, error_code in cases:
                with self.subTest(label=label), (
                    mock.patch.object(
                        transaction,
                        "_completed_replay_result",
                        side_effect=configured.get("replay"),
                        return_value=None,
                    )
                ), mock.patch.object(
                    transaction,
                    "validate_projected_transaction",
                    side_effect=(
                        configured.get("projected")
                        if isinstance(
                            configured.get("projected"),
                            Exception,
                        )
                        else None
                    ),
                    return_value=(
                        configured.get("projected")
                        if isinstance(configured.get("projected"), dict)
                        else self.projected_summary()
                    ),
                ), mock.patch.object(
                    transaction,
                    "_private_applied_workspace",
                ) as private_apply, mock.patch.object(
                    transaction.os,
                    "replace",
                ) as replacement:
                    result = transaction.apply_lifecycle_transaction(
                        root,
                        intent,
                        project_context=context,
                        clock=self.public_clock(),
                    )

                self.assertEqual(result["status"], "conflict")
                self.assertEqual(result["failed_stage"], failed_stage)
                self.assertEqual(result["error_code"], error_code)
                self.assertEqual(
                    result,
                    transaction.serialize_transaction_result(result),
                )
                private_apply.assert_not_called()
                replacement.assert_not_called()

    def test_public_apply_maps_preflight_and_lock_conflicts_without_rollback(self):
        @contextmanager
        def lock_held(*_args, **_kwargs):
            raise transaction.LifecycleLockError("LOCK_HELD")
            yield

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            (root / "workspace" / "transactions").mkdir()
            intent = self.intent(require_issue_index=True)
            cases = (
                (
                    "preflight",
                    mock.patch.object(
                        transaction.transaction_storage,
                        "verify_canonical_preimages",
                        side_effect=(
                            transaction.transaction_storage
                            .LifecycleCanonicalConflict(
                                0
                            )
                        ),
                    ),
                    "preflight",
                    "CANONICAL_PREIMAGE_CONFLICT",
                ),
                (
                    "lock",
                    mock.patch.object(
                        transaction,
                        "_private_applied_workspace",
                        side_effect=lock_held,
                    ),
                    "lock",
                    "LOCK_HELD",
                ),
            )

            for label, failure_patch, failed_stage, error_code in cases:
                with self.subTest(label=label), failure_patch, (
                    mock.patch.object(
                        transaction,
                        "validate_projected_transaction",
                        return_value=self.projected_summary(),
                    )
                ), mock.patch.object(
                    transaction.transaction_storage,
                    "rollback_canonical_target",
                ) as rollback, mock.patch.object(
                    transaction.os,
                    "replace",
                ) as replacement:
                    result = transaction.apply_lifecycle_transaction(
                        root,
                        intent,
                        project_context=context,
                        clock=self.public_clock(),
                    )

                self.assertEqual(result["status"], "conflict")
                self.assertEqual(result["failed_stage"], failed_stage)
                self.assertEqual(result["error_code"], error_code)
                self.assertEqual(result["rollback_status"], "not-required")
                rollback.assert_not_called()
                replacement.assert_not_called()

    def test_public_apply_maps_verified_rollback_result(self):
        @contextmanager
        def rolled_back(*_args, **_kwargs):
            raise transaction.LifecycleApplyRolledBack(
                original_error_code="POST_APPLY_VALIDATION_INVALID",
                applied_target_indexes=(0,),
                rollback_target_indexes=(0,),
                journal_sha256="a" * 64,
                post_apply_validation={
                    "valid": False,
                    "rule_ids": list(
                        transaction._POST_APPLY_VALIDATION_RULE_IDS
                    ),
                    "error_codes": ["POST_APPLY_VALIDATION_INVALID"],
                },
            )
            yield

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            with (
                mock.patch.object(
                    transaction,
                    "validate_projected_transaction",
                    return_value=self.projected_summary(),
                ),
                mock.patch.object(
                    transaction,
                    "_private_applied_workspace",
                    side_effect=rolled_back,
                ),
            ):
                result = transaction.apply_lifecycle_transaction(
                    root,
                    intent,
                    project_context=context,
                    clock=self.public_clock(),
                )

            self.assertEqual(result["status"], "rolled_back")
            self.assertEqual(
                result["failed_stage"],
                "post-apply-validation",
            )
            self.assertEqual(
                result["error_code"],
                "POST_APPLY_VALIDATION_INVALID",
            )
            self.assertEqual(result["rollback_status"], "verified")
            self.assertEqual(
                result["post_apply_validation"]["error_codes"],
                ["POST_APPLY_VALIDATION_INVALID"],
            )
            self.assertEqual(
                result,
                transaction.serialize_transaction_result(result),
            )

    def test_public_apply_maps_recovery_required_without_private_progress(self):
        @contextmanager
        def recovery_required(*_args, **_kwargs):
            raise transaction.LifecycleRecoveryRequired(
                original_error_code="FINALIZATION_TARGET_MISMATCH",
                rollback_error_code="STORAGE_CANONICAL_STATE_UNKNOWN",
                applied_target_indexes=(0,),
                rollback_target_indexes=(),
                journal_sha256="b" * 64,
            )
            yield

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            with (
                mock.patch.object(
                    transaction,
                    "validate_projected_transaction",
                    return_value=self.projected_summary(),
                ),
                mock.patch.object(
                    transaction,
                    "_private_applied_workspace",
                    side_effect=recovery_required,
                ),
            ):
                result = transaction.apply_lifecycle_transaction(
                    root,
                    intent,
                    project_context=context,
                    clock=self.public_clock(),
                )

            self.assertEqual(result["status"], "recovery_required")
            self.assertEqual(result["failed_stage"], "rollback")
            self.assertEqual(
                result["error_code"],
                "TRANSACTION_RECOVERY_REQUIRED",
            )
            self.assertEqual(result["rollback_status"], "required")
            rendered = json.dumps(result, ensure_ascii=False)
            self.assertNotIn("applied_target_indexes", rendered)
            self.assertNotIn("rollback_target_indexes", rendered)
            self.assertNotIn("journal_sha256", rendered)
            self.assertNotIn("STORAGE_CANONICAL_STATE_UNKNOWN", rendered)

    def test_public_apply_retains_existing_workspace_and_requires_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            (root / "workspace" / "transactions").mkdir()
            (root / ".moduflow" / "transactions").mkdir()
            intent = self.intent(require_issue_index=True)
            plan = transaction.plan_lifecycle_transaction(
                root,
                intent,
                project_context=context,
                clock="2030-01-02",
            )
            workspace_path = (
                root
                / ".moduflow"
                / "transactions"
                / plan.transaction_id
            )
            with transaction.transaction_storage.private_transaction_workspace(
                root,
                plan.transaction_id,
            ):
                pass

            with (
                mock.patch.object(
                    transaction,
                    "validate_projected_transaction",
                    return_value=self.projected_summary(),
                ),
                mock.patch.object(transaction.os, "replace") as replacement,
                mock.patch.object(transaction.os, "rmdir") as remove_directory,
            ):
                result = transaction.apply_lifecycle_transaction(
                    root,
                    intent,
                    project_context=context,
                    clock=self.public_clock(),
                )

            self.assertEqual(result["status"], "recovery_required")
            self.assertEqual(result["failed_stage"], "recovery")
            self.assertEqual(result["error_code"], "STORAGE_CONFLICT")
            self.assertEqual(result["rollback_status"], "required")
            self.assertTrue(workspace_path.is_dir())
            replacement.assert_not_called()
            remove_directory.assert_not_called()

    def test_public_failure_stage_accepts_every_private_error_family(self):
        expected = {
            "POST_APPLY_VALIDATION_INVALID": "post-apply-validation",
            "FINALIZATION_TARGET_MISMATCH": "finalizing",
            "CANONICAL_PREIMAGE_CONFLICT": "preflight",
            "LOCK_HELD": "lock",
            "STORAGE_REPLACE_FAILED": "apply",
            "JOURNAL_PROGRESS_INVALID": "apply",
        }

        for error_code, failed_stage in expected.items():
            with self.subTest(error_code=error_code):
                self.assertEqual(
                    transaction._public_failure_stage(error_code),
                    failed_stage,
                )
        with self.assertRaises(transaction.LifecycleJournalError) as raised:
            transaction._public_failure_stage("private error text")
        self.assertEqual(raised.exception.code, "JOURNAL_RECORD_INVALID")
        self.assertNotIn("private", str(raised.exception))

    def test_public_apply_lock_release_failure_keeps_completed_validation_proof(self):
        @contextmanager
        def completed_then_lock_failed(plan, *, completion_input, **_kwargs):
            changed_count = sum(
                target.changed and target.role != "evidence"
                for target in plan.targets
            )
            timestamps = tuple(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(5, 5 + 11 + 2 * changed_count)
            )
            result = transaction.serialize_transaction_result(
                transaction._successful_result_candidate(
                    plan,
                    completion_input,
                    timestamps,
                    changed_count,
                )
            )
            yield SimpleNamespace(
                transaction_result=transaction._freeze_json_value(result)
            )
            raise transaction.LifecycleLockError("LOCK_RELEASE_FAILED")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            with (
                mock.patch.object(
                    transaction,
                    "validate_projected_transaction",
                    return_value=self.projected_summary(),
                ),
                mock.patch.object(
                    transaction,
                    "_private_applied_workspace",
                    side_effect=completed_then_lock_failed,
                ),
            ):
                result = transaction.apply_lifecycle_transaction(
                    root,
                    intent,
                    project_context=context,
                    clock=self.public_clock(),
                )

            self.assertEqual(result["status"], "recovery_required")
            self.assertEqual(result["failed_stage"], "lock")
            self.assertEqual(result["error_code"], "LOCK_RELEASE_FAILED")
            self.assertTrue(result["projected_validation"]["valid"])
            self.assertTrue(result["post_apply_validation"]["valid"])
            self.assertEqual(
                result["verified_target_count"],
                len(result["targets"]),
            )

    def test_public_apply_rejects_explicit_key_conflict_before_replay_or_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            foreign_key = transaction.derive_idempotency_key(
                context,
                self.intent(
                    action="complete",
                    require_issue_index=True,
                ),
            )
            conflicting = self.intent(
                require_issue_index=True,
                idempotency_key=foreign_key,
            )

            with (
                mock.patch.object(
                    transaction,
                    "_completed_replay_result",
                ) as replay,
                mock.patch.object(
                    transaction,
                    "_private_applied_workspace",
                ) as private_apply,
                mock.patch.object(transaction.os, "replace") as replacement,
                self.assertRaisesRegex(
                    ValueError,
                    "^IDEMPOTENCY_KEY_CONFLICT$",
                ),
            ):
                transaction.apply_lifecycle_transaction(
                    root,
                    conflicting,
                    project_context=context,
                    clock="2030-01-02",
                )

            replay.assert_not_called()
            private_apply.assert_not_called()
            replacement.assert_not_called()

    def test_public_apply_fault_injector_is_synchronous_and_never_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            with (
                mock.patch.object(
                    transaction,
                    "_private_applied_workspace",
                ) as private_apply,
                self.assertRaisesRegex(
                    TypeError,
                    "fault_injector must be callable or None",
                ),
            ):
                transaction.apply_lifecycle_transaction(
                    root,
                    intent,
                    project_context=context,
                    clock="2030-01-02",
                    fault_injector="invalid",
                )
            private_apply.assert_not_called()

            observed = []

            def inject(stage):
                observed.append(stage)
                if stage == "after-replay-classification":
                    raise RuntimeError("PRIVATE INJECTED FAILURE")

            with (
                mock.patch.object(
                    transaction,
                    "validate_projected_transaction",
                ) as validator,
                mock.patch.object(
                    transaction,
                    "_private_applied_workspace",
                ) as private_apply,
                self.assertRaisesRegex(
                    RuntimeError,
                    "PRIVATE INJECTED FAILURE",
                ),
            ):
                transaction.apply_lifecycle_transaction(
                    root,
                    intent,
                    project_context=context,
                    clock="2030-01-02",
                    fault_injector=inject,
                )

            self.assertEqual(
                observed,
                ["after-plan", "after-replay-classification"],
            )
            validator.assert_not_called()
            private_apply.assert_not_called()

    def replace_projected_bytes(self, plan, replacements):
        remaining = set(replacements)
        targets = []
        for target in plan.targets:
            if target.role in replacements:
                payload = replacements[target.role]
                target = replace(
                    target,
                    after_size=len(payload),
                    after_sha256=transaction.target_sha256(payload),
                    changed=True,
                    _after_bytes=payload,
                )
                remaining.remove(target.role)
            targets.append(target)
        if remaining:
            raise AssertionError(
                f"planned roles not found: {', '.join(sorted(remaining))}"
            )
        return replace(plan, targets=tuple(targets))

    def test_completion_input_binds_final_evidence_before_io_and_freezes_result(self):
        prepare = getattr(transaction, "_prepare_completion_input", None)
        bind = getattr(transaction, "_bind_success_evidence", None)
        self.assertIsNotNone(prepare)
        self.assertIsNotNone(bind)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            projected = self.projected_summary()
            state_target = next(
                target for target in plan.targets if target.role == "state"
            )
            next_command = json.loads(state_target._after_bytes)["next_command"]
            completion = prepare(
                plan,
                self.intent(require_issue_index=True),
                next_command,
                projected,
            )
            n = sum(
                target.changed and target.role != "evidence"
                for target in plan.targets
            )
            timestamps = tuple(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(5, 5 + 11 + 2 * n)
            )
            provisional_bytes = b"PRIVATE PROVISIONAL EVIDENCE\n"
            provisional_evidence = replace(
                plan.targets[-1],
                after_sha256=transaction.target_sha256(provisional_bytes),
                after_size=len(provisional_bytes),
                changed=True,
                _after_bytes=provisional_bytes,
            )
            second_plan = replace(
                plan,
                targets=plan.targets[:-1] + (provisional_evidence,),
            )

            with (
                mock.patch.object(transaction.os, "open") as open_file,
                mock.patch.object(transaction.os, "mkdir") as make_directory,
                mock.patch.object(transaction.os, "replace") as replace_file,
                mock.patch.object(
                    transaction.validate_project_artifacts,
                    "validate_project",
                ) as validate_project,
            ):
                binding = bind(plan, completion, timestamps)
                second_binding = bind(second_plan, completion, timestamps)

            evidence = binding.plan.targets[-1]
            self.assertEqual(evidence.role, "evidence")
            self.assertTrue(evidence.changed)
            self.assertEqual(evidence._after_bytes, binding.evidence_bytes)
            self.assertEqual(evidence.after_size, len(binding.evidence_bytes))
            self.assertEqual(
                evidence.after_sha256,
                transaction.target_sha256(binding.evidence_bytes),
            )
            self.assertEqual(
                binding.evidence_bytes,
                transaction.render_transaction_evidence(
                    transaction._json_value(binding.transaction_result)
                ),
            )
            self.assertEqual(binding.completed_at, timestamps[7 + n])
            self.assertEqual(
                binding.transaction_result["post_apply_validation"]["rule_ids"],
                (
                    "canonical-targets",
                    "project-artifacts",
                    "issue-schema",
                    "lifecycle-consensus",
                    "production-records",
                ),
            )
            self.assertEqual(second_binding.evidence_bytes, binding.evidence_bytes)
            self.assertEqual(
                second_binding.plan.targets[-1].after_sha256,
                evidence.after_sha256,
            )
            self.assertEqual(
                second_binding.plan.targets[-1].after_size,
                evidence.after_size,
            )

            projected["rule_ids"].append("PRIVATE MUTATION")
            self.assertNotIn(
                "PRIVATE MUTATION",
                completion.projected_validation["rule_ids"],
            )
            self.assertNotIn(
                "PRIVATE MUTATION",
                binding.transaction_result["projected_validation"]["rule_ids"],
            )
            open_file.assert_not_called()
            make_directory.assert_not_called()
            replace_file.assert_not_called()
            validate_project.assert_not_called()
            for private in (
                str(root),
                "dongwon",
                "request:A2",
                next_command,
                "PRIVATE PROVISIONAL EVIDENCE",
                "project-artifacts",
            ):
                self.assertNotIn(private, repr(completion))
                self.assertNotIn(private, repr(binding))

    def test_completion_input_rejects_mismatch_replay_and_invalid_values_before_io(self):
        prepare = getattr(transaction, "_prepare_completion_input", None)
        bind = getattr(transaction, "_bind_success_evidence", None)
        error_type = getattr(transaction, "LifecycleFinalizationError", None)
        self.assertIsNotNone(prepare)
        self.assertIsNotNone(bind)
        self.assertIsNotNone(error_type)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            intent = self.intent(require_issue_index=True)
            plan = transaction.plan_lifecycle_transaction(
                root,
                intent,
                project_context=context,
                clock="2030-01-02",
            )
            state_target = next(
                target for target in plan.targets if target.role == "state"
            )
            next_command = json.loads(state_target._after_bytes)["next_command"]
            valid_summary = self.projected_summary()
            completion = prepare(
                plan,
                intent,
                next_command,
                valid_summary,
            )
            n = sum(
                target.changed and target.role != "evidence"
                for target in plan.targets
            )
            timestamps = tuple(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(5, 5 + 11 + 2 * n)
            )
            binding = bind(plan, completion, timestamps)
            replay_evidence = replace(
                plan.targets[-1],
                existed=True,
                before_sha256=transaction.target_sha256(
                    binding.evidence_bytes
                ),
                _before_bytes=binding.evidence_bytes,
            )
            replay_plan = replace(
                plan,
                targets=plan.targets[:-1] + (replay_evidence,),
            )

            invalid_prepare = (
                (
                    plan,
                    self.intent(
                        require_issue_index=True,
                        source_event="request:other",
                    ),
                    next_command,
                    valid_summary,
                ),
                (replace(plan, issue_id="BIZ-OTHER"), intent, next_command, valid_summary),
                (replace(plan, action="complete"), intent, next_command, valid_summary),
                (replace(plan, target_lifecycle="done"), intent, next_command, valid_summary),
                (plan, intent, "product:private-wrong", valid_summary),
                (
                    plan,
                    intent,
                    next_command,
                    {**valid_summary, "valid": False},
                ),
                (
                    plan,
                    intent,
                    next_command,
                    {**valid_summary, "rule_ids": ["unsafe value"]},
                ),
                (
                    plan,
                    intent,
                    next_command,
                    {**valid_summary, "private": True},
                ),
                (
                    plan,
                    intent,
                    next_command,
                    {**valid_summary, "error_codes": "mutable-string"},
                ),
            )

            with (
                mock.patch.object(transaction.os, "open") as open_file,
                mock.patch.object(transaction.os, "mkdir") as make_directory,
                mock.patch.object(transaction.os, "replace") as replace_file,
                mock.patch.object(
                    transaction.validate_project_artifacts,
                    "validate_project",
                ) as validate_project,
            ):
                for arguments in invalid_prepare:
                    with self.subTest(arguments=arguments[0:3]):
                        with self.assertRaises(error_type) as raised:
                            prepare(*arguments)
                        self.assertEqual(
                            raised.exception.code,
                            "FINALIZATION_INPUT_INVALID",
                        )
                        self.assertEqual(
                            repr(raised.exception),
                            "LifecycleFinalizationError('FINALIZATION_INPUT_INVALID')",
                        )

                invalid_timestamps = (
                    timestamps[:-1],
                    timestamps[:-1] + ("PRIVATE INVALID TIMESTAMP",),
                )
                for values in invalid_timestamps:
                    with self.subTest(timestamp_count=len(values)):
                        with self.assertRaises(error_type) as raised:
                            bind(plan, completion, values)
                        self.assertEqual(
                            raised.exception.code,
                            "FINALIZATION_INPUT_INVALID",
                        )

                replay_completion = prepare(
                    replay_plan,
                    intent,
                    next_command,
                    valid_summary,
                )
                with self.assertRaises(error_type) as raised:
                    bind(replay_plan, replay_completion, timestamps)
                self.assertEqual(
                    raised.exception.code,
                    "FINALIZATION_EVIDENCE_ALREADY_PRESENT",
                )
                self.assertEqual(
                    str(raised.exception),
                    "FINALIZATION_EVIDENCE_ALREADY_PRESENT",
                )
                open_file.assert_not_called()
                make_directory.assert_not_called()
                replace_file.assert_not_called()
                validate_project.assert_not_called()

    def test_rollback_signals_are_validated_detached_and_redacted(self):
        rolled_back = transaction.LifecycleApplyRolledBack(
            original_error_code="STORAGE_REPLACE_FAILED",
            applied_target_indexes=(0, 2),
            rollback_target_indexes=(2, 0),
            journal_sha256="1" * 64,
        )
        self.assertEqual(rolled_back.code, "TRANSACTION_ROLLED_BACK")
        self.assertEqual(
            rolled_back.original_error_code,
            "STORAGE_REPLACE_FAILED",
        )
        self.assertEqual(rolled_back.applied_target_indexes, (0, 2))
        self.assertEqual(rolled_back.rollback_target_indexes, (2, 0))
        self.assertEqual(rolled_back.journal_sha256, "1" * 64)
        self.assertIsNone(rolled_back.post_apply_validation)
        self.assertEqual(str(rolled_back), "TRANSACTION_ROLLED_BACK")
        self.assertEqual(
            repr(rolled_back),
            "LifecycleApplyRolledBack('TRANSACTION_ROLLED_BACK')",
        )

        recovery = transaction.LifecycleRecoveryRequired(
            original_error_code="STORAGE_REPLACE_FAILED",
            rollback_error_code="STORAGE_VERIFY_FAILED",
            applied_target_indexes=(0, 2),
            rollback_target_indexes=(2,),
            journal_sha256="2" * 64,
        )
        self.assertEqual(recovery.code, "TRANSACTION_RECOVERY_REQUIRED")
        self.assertEqual(
            recovery.rollback_error_code,
            "STORAGE_VERIFY_FAILED",
        )
        self.assertEqual(recovery.applied_target_indexes, (0, 2))
        self.assertEqual(recovery.rollback_target_indexes, (2,))
        self.assertIsNone(recovery.post_apply_validation)
        self.assertEqual(str(recovery), "TRANSACTION_RECOVERY_REQUIRED")
        self.assertEqual(
            repr(recovery),
            "LifecycleRecoveryRequired('TRANSACTION_RECOVERY_REQUIRED')",
        )

        invalid = (
            {"applied_target_indexes": [0, 2]},
            {"applied_target_indexes": (False, 2)},
            {"applied_target_indexes": (-1, 2)},
            {"applied_target_indexes": (0, 0)},
            {"applied_target_indexes": (2, 0)},
            {"rollback_target_indexes": (0,)},
            {"rollback_target_indexes": (2, 2)},
            {"original_error_code": "unsafe value"},
            {"journal_sha256": "not-a-hash"},
        )
        defaults = {
            "original_error_code": "STORAGE_REPLACE_FAILED",
            "applied_target_indexes": (0, 2),
            "rollback_target_indexes": (2,),
            "journal_sha256": "3" * 64,
        }
        for changes in invalid:
            with self.subTest(changes=changes):
                values = dict(defaults)
                values.update(changes)
                with self.assertRaises(transaction.LifecycleJournalError) as raised:
                    transaction.LifecycleApplyRolledBack(**values)
                self.assertEqual(
                    raised.exception.code,
                    "JOURNAL_RECORD_INVALID",
                )

        with self.assertRaises(transaction.LifecycleJournalError) as raised:
            transaction.LifecycleRecoveryRequired(
                rollback_error_code="unsafe value",
                **defaults,
            )
        self.assertEqual(raised.exception.code, "JOURNAL_RECORD_INVALID")

        summary = {
            "valid": False,
            "rule_ids": ["canonical-targets"],
            "error_codes": ["POST_APPLY_TARGET_MISMATCH"],
        }
        summarized_rollback = transaction.LifecycleApplyRolledBack(
            original_error_code="POST_APPLY_VALIDATION_INVALID",
            applied_target_indexes=(0, 2),
            rollback_target_indexes=(2, 0),
            journal_sha256="4" * 64,
            post_apply_validation=summary,
        )
        summarized_recovery = transaction.LifecycleRecoveryRequired(
            original_error_code="POST_APPLY_VALIDATION_FAILED",
            rollback_error_code="STORAGE_VERIFY_FAILED",
            applied_target_indexes=(0, 2),
            rollback_target_indexes=(2,),
            journal_sha256="5" * 64,
            post_apply_validation=summary,
        )
        summary["error_codes"].append("PRIVATE_POISON")
        expected_summary = {
            "valid": False,
            "rule_ids": ("canonical-targets",),
            "error_codes": ("POST_APPLY_TARGET_MISMATCH",),
        }
        self.assertEqual(
            dict(summarized_rollback.post_apply_validation),
            expected_summary,
        )
        self.assertEqual(
            dict(summarized_recovery.post_apply_validation),
            expected_summary,
        )
        self.assertNotIn("PRIVATE", repr(summarized_rollback))
        self.assertNotIn("PRIVATE", repr(summarized_recovery))

        with self.assertRaises(transaction.LifecycleJournalError) as raised:
            transaction.LifecycleApplyRolledBack(
                **defaults,
                post_apply_validation={
                    "valid": False,
                    "rule_ids": ["unsafe value"],
                    "error_codes": ["POST_APPLY_TARGET_MISMATCH"],
                },
            )
        self.assertEqual(raised.exception.code, "JOURNAL_RECORD_INVALID")

        with self.assertRaises(transaction.LifecycleJournalError) as raised:
            transaction.LifecycleApplyRolledBack(
                **defaults,
                post_apply_validation={
                    "valid": True,
                    "rule_ids": ["project-artifacts"],
                    "error_codes": [],
                },
            )
        self.assertEqual(raised.exception.code, "JOURNAL_RECORD_INVALID")

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

    def test_recovery_workspace_discovery_and_reopen_are_read_only(self):
        storage = transaction.transaction_storage
        self.assertIsNotNone(getattr(storage, "discover_recovery_workspaces", None))
        self.assertIsNotNone(getattr(storage, "reopen_transaction_workspace", None))
        self.assertIsNotNone(getattr(storage, "read_recovery_control_snapshot", None))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            transactions = root / ".moduflow" / "transactions"
            transactions.mkdir(mode=0o700)
            for transaction_id in ("txn-b", "txn-a"):
                with storage.private_transaction_workspace(root, transaction_id):
                    pass

            with (
                mock.patch.object(storage.os, "mkdir") as make_directory,
                mock.patch.object(storage.os, "chmod") as change_mode,
                mock.patch.object(storage.os, "fchmod") as change_fd_mode,
                mock.patch.object(storage.os, "unlink") as unlink,
                mock.patch.object(storage.os, "replace") as replace_file,
                mock.patch.object(storage.os, "fsync") as sync_file,
            ):
                self.assertEqual(
                    storage.discover_recovery_workspaces(root),
                    ("txn-a", "txn-b"),
                )
                self.assertEqual(
                    storage.discover_recovery_workspaces(root, "txn-b"),
                    ("txn-b",),
                )
                with storage.reopen_transaction_workspace(
                    root,
                    "txn-a",
                ) as workspace:
                    snapshot = storage.read_recovery_control_snapshot(workspace)
                    self.assertEqual(snapshot.journal.state, "absent")
                    self.assertEqual(snapshot.journal_next.state, "absent")
                    self.assertEqual(snapshot.recovery_manifest.state, "absent")
                    self.assertNotIn(str(root), repr(snapshot))

            for operation in (
                make_directory,
                change_mode,
                change_fd_mode,
                unlink,
                replace_file,
                sync_file,
            ):
                operation.assert_not_called()

    def test_recovery_workspace_discovery_rejects_unsafe_entries_without_repair(self):
        storage = transaction.transaction_storage
        error_type = getattr(storage, "LifecycleRecoveryStorageError", None)
        self.assertIsNotNone(error_type)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            transactions = root / ".moduflow" / "transactions"
            transactions.mkdir(mode=0o700)
            foreign = transactions / "foreign.txt"
            foreign.write_text("do not expose\n", encoding="utf-8")
            before = foreign.stat()

            with mock.patch.object(storage.os, "unlink") as unlink:
                with self.assertRaises(error_type) as raised:
                    storage.discover_recovery_workspaces(root)

            self.assertEqual(
                raised.exception.code,
                "RECOVERY_DISCOVERY_UNSAFE",
            )
            self.assertEqual(
                str(raised.exception),
                "RECOVERY_DISCOVERY_UNSAFE",
            )
            self.assertNotIn("foreign.txt", repr(raised.exception))
            unlink.assert_not_called()
            self.assertEqual(foreign.read_bytes(), b"do not expose\n")
            self.assertEqual(foreign.stat().st_ino, before.st_ino)

    def test_recovery_reopen_rejects_unsafe_workspace_and_control_files(self):
        storage = transaction.transaction_storage
        error_type = storage.LifecycleRecoveryStorageError
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            transactions = root / ".moduflow" / "transactions"
            transactions.mkdir(mode=0o700)

            with self.assertRaises(RuntimeError) as invalid_id:
                with storage.reopen_transaction_workspace(root, "../escape"):
                    self.fail("invalid transaction ID must not open")
            self.assertIsInstance(invalid_id.exception, error_type)
            self.assertEqual(
                invalid_id.exception.code,
                "RECOVERY_WORKSPACE_UNSAFE",
            )

            with storage.private_transaction_workspace(root, "txn-extra"):
                pass
            extra_workspace = transactions / "txn-extra"
            extra = extra_workspace / "foreign.bin"
            extra.write_bytes(b"private extra\n")
            with storage.reopen_transaction_workspace(
                root,
                "txn-extra",
            ) as workspace:
                with self.assertRaises(error_type) as extra_error:
                    storage.read_recovery_control_snapshot(workspace)
            self.assertEqual(
                extra_error.exception.code,
                "RECOVERY_CONTROL_FILE_UNSAFE",
            )
            self.assertEqual(extra.read_bytes(), b"private extra\n")

            with storage.private_transaction_workspace(root, "txn-linked"):
                pass
            linked_workspace = transactions / "txn-linked"
            journal = linked_workspace / "journal.json"
            journal.write_bytes(b"{}\n")
            journal.chmod(0o600)
            hard_link = root / "outside-journal-copy"
            os.link(journal, hard_link)
            with storage.reopen_transaction_workspace(
                root,
                "txn-linked",
            ) as workspace:
                with self.assertRaises(error_type) as linked_error:
                    storage.read_recovery_control_snapshot(workspace)
            self.assertEqual(
                linked_error.exception.code,
                "RECOVERY_CONTROL_FILE_UNSAFE",
            )
            self.assertEqual(journal.read_bytes(), b"{}\n")

    def test_recovered_journal_workspace_loads_exact_current_snapshot_read_only(self):
        entry = getattr(transaction, "_private_recovered_journal_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            with transaction._private_prepared_workspace(
                plan,
                journal_clock=lambda: next(timestamps),
                lock_clock="2030-01-02T03:04:05Z",
                lock_pid=123,
                lock_token_factory=lambda: "1" * 32,
            ):
                pass
            workspace = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            journal_before = (workspace / "journal.json").read_bytes()

            with mock.patch.object(transaction.os, "replace") as replace_file:
                with entry(root, plan.transaction_id) as recovered:
                    self.assertEqual(recovered.authority, "current")
                    self.assertEqual(recovered.journal["phase"], "prepared")
                    self.assertIsNone(recovered.journal_next)
                    self.assertEqual(
                        recovered.journal_sha256,
                        hashlib.sha256(journal_before).hexdigest(),
                    )
                    self.assertNotIn(str(root), repr(recovered))
            replace_file.assert_not_called()
            self.assertEqual(
                (workspace / "journal.json").read_bytes(),
                journal_before,
            )

    def test_recovered_journal_workspace_classifies_only_exact_legal_next(self):
        entry = getattr(transaction, "_private_recovered_journal_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            with transaction._private_prepared_workspace(
                plan,
                journal_clock=lambda: next(timestamps),
                lock_clock="2030-01-02T03:04:05Z",
                lock_pid=123,
                lock_token_factory=lambda: "1" * 32,
            ):
                pass
            workspace = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            journal_path = workspace / "journal.json"
            next_path = workspace / "journal.next"
            current_bytes = journal_path.read_bytes()
            successor = json.loads(current_bytes)
            successor["phase"] = "applying"
            successor["updated_at"] = "2030-01-02T03:04:08Z"
            next_bytes = transaction.canonical_json_bytes(
                transaction.serialize_transaction_journal(successor)
            ) + b"\n"
            next_path.write_bytes(next_bytes)
            next_path.chmod(0o600)

            with entry(root, plan.transaction_id) as recovered:
                self.assertEqual(recovered.authority, "current")
                self.assertEqual(recovered.journal["phase"], "prepared")
                self.assertEqual(recovered.journal_next["phase"], "applying")
                self.assertEqual(
                    recovered.journal_next_sha256,
                    hashlib.sha256(next_bytes).hexdigest(),
                )

            self.assertEqual(journal_path.read_bytes(), current_bytes)
            self.assertEqual(next_path.read_bytes(), next_bytes)

    def test_recovered_journal_workspace_rejects_foreign_successor_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            with transaction._private_prepared_workspace(
                plan,
                journal_clock=lambda: next(timestamps),
                lock_clock="2030-01-02T03:04:05Z",
                lock_pid=123,
                lock_token_factory=lambda: "1" * 32,
            ):
                pass
            workspace = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            current_bytes = (workspace / "journal.json").read_bytes()
            successor = json.loads(current_bytes)
            successor["phase"] = "applying"
            successor["updated_at"] = "2030-01-02T03:04:08Z"
            successor["recovery_manifest_sha256"] = "f" * 64
            next_bytes = transaction.canonical_json_bytes(
                transaction.serialize_transaction_journal(successor)
            ) + b"\n"
            next_path = workspace / "journal.next"
            next_path.write_bytes(next_bytes)
            next_path.chmod(0o600)

            with self.assertRaises(
                transaction.LifecycleRecoveryReadError
            ) as raised:
                with transaction._private_recovered_journal_workspace(
                    root,
                    plan.transaction_id,
                ):
                    self.fail("foreign manifest successor must not be yielded")

            self.assertEqual(
                raised.exception.code,
                "RECOVERY_JOURNAL_NEXT_CONFLICT",
            )
            self.assertEqual(
                (workspace / "journal.json").read_bytes(),
                current_bytes,
            )
            self.assertEqual(next_path.read_bytes(), next_bytes)

    def test_recovered_transaction_workspace_rehydrates_exact_manifest_payloads(self):
        entry = getattr(
            transaction,
            "_private_recovered_transaction_workspace",
            None,
        )
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, nested=True)
            (root / "product" / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            with transaction._private_prepared_workspace(
                plan,
                journal_clock=lambda: next(timestamps),
                lock_clock="2030-01-02T03:04:05Z",
                lock_pid=123,
                lock_token_factory=lambda: "1" * 32,
            ):
                pass
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }

            with entry(root, plan.transaction_id) as recovered:
                self.assertEqual(
                    recovered.journal_state.journal["phase"],
                    "prepared",
                )
                self.assertEqual(
                    [
                        target.relative_path
                        for target in recovered.storage_targets
                    ],
                    [target.relative_path for target in plan.targets],
                )
                self.assertEqual(
                    [target.before_sha256 for target in recovered.storage_targets],
                    [target.before_sha256 for target in plan.targets],
                )
                self.assertEqual(
                    [target.after_sha256 for target in recovered.storage_targets],
                    [target.after_sha256 for target in plan.targets],
                )
                self.assertEqual(
                    recovered.recovery_manifest.sha256,
                    recovered.journal_state.journal[
                        "recovery_manifest_sha256"
                    ],
                )
                self.assertEqual(
                    len(recovered.preimages),
                    len(plan.targets),
                )
                self.assertEqual(
                    len(recovered.staged_proposals),
                    len(plan.targets),
                )
                self.assertNotIn(str(root), repr(recovered))
                self.assertNotIn("Preserve issue prose", repr(recovered))

            after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_recovered_transaction_workspace_rejects_manifest_and_payload_mismatch(self):
        cases = (
            ("manifest-schema", "RECOVERY_MANIFEST_MISMATCH"),
            ("manifest-transaction", "RECOVERY_MANIFEST_MISMATCH"),
            ("manifest-order", "RECOVERY_MANIFEST_MISMATCH"),
            ("manifest-role", "RECOVERY_MANIFEST_MISMATCH"),
            ("manifest-path", "RECOVERY_MANIFEST_MISMATCH"),
            ("manifest-hash", "RECOVERY_MANIFEST_MISMATCH"),
            ("preimage-bytes", "RECOVERY_PAYLOAD_MISMATCH"),
            ("preimage-mode", "RECOVERY_PAYLOAD_INVALID"),
            ("stage-bytes", "RECOVERY_PAYLOAD_MISMATCH"),
            ("stage-mode", "RECOVERY_PAYLOAD_INVALID"),
            ("stage-inode", "RECOVERY_PAYLOAD_INVALID"),
            ("stage-device", "RECOVERY_MANIFEST_MISMATCH"),
            ("stage-missing", "RECOVERY_PAYLOAD_MISSING"),
            ("nested-parent-symlink", "RECOVERY_PAYLOAD_INVALID"),
        )
        for mutation, expected_code in cases:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root, nested=True)
                (root / "product" / "workspace" / "transactions").mkdir()
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(),
                    project_context=context,
                    clock="2030-01-02",
                )
                timestamps = iter(
                    (
                        "2030-01-02T03:04:05Z",
                        "2030-01-02T03:04:06Z",
                        "2030-01-02T03:04:07Z",
                    )
                )
                with transaction._private_prepared_workspace(
                    plan,
                    journal_clock=lambda: next(timestamps),
                    lock_clock="2030-01-02T03:04:05Z",
                    lock_pid=123,
                    lock_token_factory=lambda: "1" * 32,
                ):
                    pass
                workspace = (
                    root / ".moduflow" / "transactions" / plan.transaction_id
                )
                manifest_path = workspace / "recovery-manifest.json"
                journal_path = workspace / "journal.json"
                changed_target = next(target for target in plan.targets if target.changed)
                changed_index = plan.targets.index(changed_target)
                digest = hashlib.sha256(
                    plan.transaction_id.encode("utf-8")
                ).hexdigest()
                stage_path = (
                    root
                    / Path(changed_target.relative_path).parent
                    / f".moduflow-stage-{digest}-{changed_index:06d}"
                )

                if mutation.startswith("manifest-") or mutation == "stage-device":
                    manifest = json.loads(manifest_path.read_bytes())
                    if mutation == "manifest-schema":
                        manifest["schema"] = "moduflow.recovery-manifest.poison"
                    elif mutation == "manifest-transaction":
                        manifest["transaction_id"] = "foreign-transaction"
                    elif mutation == "manifest-order":
                        manifest["targets"].reverse()
                    elif mutation == "manifest-role":
                        manifest["targets"][0]["role"] = "state"
                    elif mutation == "manifest-path":
                        manifest["targets"][0]["relative_path"] = (
                            "product/issues/OTHER.md"
                        )
                    elif mutation == "manifest-hash":
                        manifest["targets"][0]["after_sha256"] = "0" * 64
                    else:
                        manifest["targets"][changed_index]["proposed"][
                            "device"
                        ] += 1
                    manifest_bytes = transaction.canonical_json_bytes(manifest) + b"\n"
                    manifest_path.write_bytes(manifest_bytes)
                    journal = json.loads(journal_path.read_bytes())
                    journal["recovery_manifest_sha256"] = hashlib.sha256(
                        manifest_bytes
                    ).hexdigest()
                    journal_path.write_bytes(
                        transaction.canonical_json_bytes(
                            transaction.serialize_transaction_journal(journal)
                        )
                        + b"\n"
                    )
                elif mutation == "preimage-bytes":
                    preimage = workspace / "preimages" / "000000.bin"
                    preimage.write_bytes(b"corrupted recovery preimage\n")
                elif mutation == "preimage-mode":
                    (workspace / "preimages" / "000000.bin").chmod(0o644)
                elif mutation == "stage-bytes":
                    stage_path.write_bytes(b"corrupted recovery proposal\n")
                elif mutation == "stage-mode":
                    stage_path.chmod(0o644)
                elif mutation == "stage-inode":
                    replacement = stage_path.with_name(stage_path.name + ".replacement")
                    replacement.write_bytes(stage_path.read_bytes())
                    replacement.chmod(0o600)
                    os.replace(replacement, stage_path)
                elif mutation == "stage-missing":
                    stage_path.unlink()
                else:
                    parent = root / Path(changed_target.relative_path).parent
                    moved = parent.with_name(parent.name + "-real")
                    parent.rename(moved)
                    parent.symlink_to(moved, target_is_directory=True)

                with self.assertRaises(
                    transaction.transaction_storage.LifecycleRecoveryStorageError
                ) as raised:
                    with transaction._private_recovered_transaction_workspace(
                        root,
                        plan.transaction_id,
                    ):
                        self.fail("mismatched recovery material must be rejected")

                self.assertEqual(raised.exception.code, expected_code)
                self.assertEqual(str(raised.exception), expected_code)
                self.assertNotIn(str(root), repr(raised.exception))

    def test_recovered_transaction_workspace_classifies_all_journal_phases(self):
        phases = (
            "planned",
            "staged",
            "prepared",
            "applying",
            "post-validating",
            "finalizing-canonical",
            "finalizing-complete",
            "rolling-back",
            "complete",
            "rolled-back",
            "recovery-required",
        )
        for phase_case in phases:
            with self.subTest(phase=phase_case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root)
                (root / "workspace" / "transactions").mkdir()
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(),
                    project_context=context,
                    clock="2030-01-02",
                )
                timestamps = iter(
                    (
                        "2030-01-02T03:04:05Z",
                        "2030-01-02T03:04:06Z",
                        "2030-01-02T03:04:07Z",
                    )
                )
                with transaction._private_prepared_workspace(
                    plan,
                    journal_clock=lambda: next(timestamps),
                    lock_clock="2030-01-02T03:04:05Z",
                    lock_pid=123,
                    lock_token_factory=lambda: "1" * 32,
                ):
                    pass
                workspace = (
                    root / ".moduflow" / "transactions" / plan.transaction_id
                )
                journal_path = workspace / "journal.json"
                journal = json.loads(journal_path.read_bytes())
                changed = [
                    index
                    for index, target in enumerate(plan.targets)
                    if target.changed
                ]
                canonical_changed = [
                    index
                    for index in changed
                    if plan.targets[index].role != "evidence"
                ]
                manifest_absent = phase_case in {
                    "planned",
                    "staged",
                    "recovery-required",
                }
                journal["phase"] = phase_case.split("-canonical")[0].split(
                    "-complete"
                )[0]
                journal["recovery_manifest_sha256"] = (
                    "absent"
                    if manifest_absent
                    else hashlib.sha256(
                        (workspace / "recovery-manifest.json").read_bytes()
                    ).hexdigest()
                )
                journal["applied_target_indexes"] = []
                journal["rollback_target_indexes"] = []
                if phase_case == "applying":
                    journal["applied_target_indexes"] = canonical_changed[:1]
                elif phase_case == "post-validating":
                    journal["applied_target_indexes"] = canonical_changed
                elif phase_case == "finalizing-canonical":
                    journal["applied_target_indexes"] = canonical_changed
                elif phase_case in {"finalizing-complete", "complete"}:
                    journal["applied_target_indexes"] = changed
                elif phase_case == "rolling-back":
                    journal["applied_target_indexes"] = changed
                    journal["rollback_target_indexes"] = list(reversed(changed))[:1]
                elif phase_case == "rolled-back":
                    journal["applied_target_indexes"] = changed
                    journal["rollback_target_indexes"] = list(reversed(changed))
                journal["updated_at"] = "2030-01-02T03:04:08Z"
                journal_path.write_bytes(
                    transaction.canonical_json_bytes(
                        transaction.serialize_transaction_journal(journal)
                    )
                    + b"\n"
                )

                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ) as recovered:
                    self.assertEqual(
                        recovered.journal_state.journal["phase"],
                        journal["phase"],
                    )
                    if manifest_absent:
                        self.assertEqual(recovered.storage_targets, ())
                        self.assertIsNone(recovered.recovery_manifest)
                    else:
                        self.assertEqual(
                            len(recovered.storage_targets),
                            len(plan.targets),
                        )
                        self.assertIsNotNone(recovered.recovery_manifest)

    def test_recover_reversible_transaction_resumes_exact_rollback_prefixes(self):
        recover = getattr(transaction, "_recover_reversible_transaction", None)
        outcome_type = getattr(transaction, "_PrivateRecoveryOutcome", None)
        self.assertIsNotNone(recover)
        self.assertIsNotNone(outcome_type)
        cases = (
            [("prepared", 0, 0)]
            + [("applying-recorded", count, 0) for count in range(5)]
            + [("applying-unrecorded", count, 0) for count in range(1, 5)]
            + [("post-validating", 4, 0)]
            + [
                ("rolling-back-recorded", 4, count)
                for count in range(5)
            ]
            + [
                ("rolling-back-unrecorded", 4, count)
                for count in range(1, 5)
            ]
        )
        for phase_case, applied_count, rollback_count in cases:
            with self.subTest(
                phase=phase_case,
                applied=applied_count,
                rollback=rollback_count,
            ), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context, plan, applied, setup_rollback = (
                    self.prepare_restart_recovery_case(
                        root,
                        phase_case,
                        applied_count=applied_count,
                        rollback_count=rollback_count,
                    )
                )
                canonical_before = {
                    target.relative_path: target._before_bytes
                    if target.existed
                    else None
                    for target in plan.targets
                }
                subject = transaction._authorized_recovery_subject(
                    root,
                    plan.transaction_id,
                    project_context=context,
                )
                recovery_times = iter(
                    f"2030-01-02T03:05:{second:02d}Z"
                    for second in range(40)
                )
                with (
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                    ) as validate_project,
                    transaction._exclusive_recovery_lock(
                        subject,
                        clock="2030-01-02T03:05:30Z",
                        pid=203,
                        token_factory=lambda: "b" * 32,
                    ),
                ):
                    with transaction._private_recovered_transaction_workspace(
                        root,
                        plan.transaction_id,
                    ) as recovered:
                        outcome = recover(
                            recovered,
                            journal_clock=lambda: next(recovery_times),
                        )

                self.assertIsInstance(outcome, outcome_type)
                self.assertEqual(outcome.status, "rolled_back")
                self.assertEqual(outcome.resulting_phase, "rolled-back")
                self.assertEqual(outcome.verified_target_count, len(plan.targets))
                validate_project.assert_not_called()
                journal = json.loads(
                    (
                        root
                        / ".moduflow"
                        / "transactions"
                        / plan.transaction_id
                        / "journal.json"
                    ).read_bytes()
                )
                self.assertEqual(journal["phase"], "rolled-back")
                self.assertEqual(journal["applied_target_indexes"], list(applied))
                self.assertEqual(
                    journal["rollback_target_indexes"],
                    list(reversed(applied)),
                )
                self.assertEqual(
                    setup_rollback,
                    tuple(reversed(applied))[:rollback_count],
                )
                for target in plan.targets:
                    canonical = root / target.relative_path
                    self.assertEqual(
                        canonical.read_bytes() if canonical.exists() else None,
                        canonical_before[target.relative_path],
                    )
                self.assertTrue(
                    (
                        root
                        / ".moduflow"
                        / "transactions"
                        / plan.transaction_id
                    ).is_dir()
                )

    def test_recover_reversible_transaction_preserves_noncontiguous_state(self):
        recover = getattr(transaction, "_recover_reversible_transaction", None)
        error_type = getattr(transaction, "LifecycleRecoveryStateError", None)
        self.assertIsNotNone(recover)
        self.assertIsNotNone(error_type)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context, plan, _applied, _rollback = self.prepare_restart_recovery_case(
                root,
                "applying-recorded",
                applied_count=0,
            )
            with transaction._private_recovered_transaction_workspace(
                root,
                plan.transaction_id,
            ) as recovered:
                second = recovered.storage_targets[1]
                canonical = root / second.relative_path
                canonical.write_bytes(second._after_bytes)
                canonical.chmod(0o600)
            journal_path = (
                root
                / ".moduflow"
                / "transactions"
                / plan.transaction_id
                / "journal.json"
            )
            before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if (root / target.relative_path).exists()
                    else None
                )
                for target in plan.targets
            }
            journal_before = journal_path.read_bytes()
            subject = transaction._authorized_recovery_subject(
                root,
                plan.transaction_id,
                project_context=context,
            )

            with transaction._exclusive_recovery_lock(
                subject,
                clock="2030-01-02T03:05:30Z",
                pid=203,
                token_factory=lambda: "b" * 32,
            ):
                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ) as recovered:
                    with self.assertRaises(error_type) as raised:
                        recover(
                            recovered,
                            journal_clock="2030-01-02T03:05:31Z",
                        )

            self.assertEqual(
                raised.exception.code,
                "RECOVERY_STATE_PROGRESS_INVALID",
            )
            self.assertEqual(journal_path.read_bytes(), journal_before)
            self.assertEqual(
                {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if (root / target.relative_path).exists()
                        else None
                    )
                    for target in plan.targets
                },
                before,
            )

    def test_recover_reversible_transaction_preserves_unknown_canonical_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context, plan, _applied, _rollback = self.prepare_restart_recovery_case(
                root,
                "applying-recorded",
                applied_count=0,
            )
            target = plan.targets[0]
            canonical = root / target.relative_path
            canonical.write_bytes(b"unknown private canonical state\n")
            journal_path = (
                root
                / ".moduflow"
                / "transactions"
                / plan.transaction_id
                / "journal.json"
            )
            journal_before = journal_path.read_bytes()
            canonical_before = canonical.read_bytes()
            subject = transaction._authorized_recovery_subject(
                root,
                plan.transaction_id,
                project_context=context,
            )

            with transaction._exclusive_recovery_lock(
                subject,
                clock="2030-01-02T03:05:30Z",
                pid=203,
                token_factory=lambda: "b" * 32,
            ):
                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ) as recovered:
                    with self.assertRaises(
                        transaction.LifecycleRecoveryStateError
                    ) as raised:
                        transaction._recover_reversible_transaction(
                            recovered,
                            journal_clock="2030-01-02T03:05:31Z",
                        )

            self.assertEqual(
                raised.exception.code,
                "RECOVERY_STATE_CANONICAL_UNKNOWN",
            )
            self.assertEqual(canonical.read_bytes(), canonical_before)
            self.assertEqual(journal_path.read_bytes(), journal_before)

    def test_recover_reversible_transaction_terminalizes_preapply_phases(self):
        cases = ("planned", "staged", "pre-journal-orphan")
        for phase_case in cases:
            with self.subTest(phase=phase_case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context, plan, _applied, _rollback = (
                    self.prepare_restart_recovery_case(
                        root,
                        "prepared",
                    )
                )
                workspace = (
                    root / ".moduflow" / "transactions" / plan.transaction_id
                )
                journal_path = workspace / "journal.json"
                next_path = workspace / "journal.next"
                journal = json.loads(journal_path.read_bytes())
                manifest_sha256 = journal["recovery_manifest_sha256"]
                journal["phase"] = (
                    "planned"
                    if phase_case == "pre-journal-orphan"
                    else phase_case
                )
                journal["recovery_manifest_sha256"] = "absent"
                journal["applied_target_indexes"] = []
                journal["rollback_target_indexes"] = []
                journal["updated_at"] = "2030-01-02T03:04:08Z"
                current_bytes = (
                    transaction.canonical_json_bytes(
                        transaction.serialize_transaction_journal(journal)
                    )
                    + b"\n"
                )
                journal_path.write_bytes(current_bytes)
                journal_path.chmod(0o600)
                if phase_case == "pre-journal-orphan":
                    journal_path.unlink()
                    next_path.write_bytes(current_bytes)
                else:
                    successor = dict(journal)
                    successor["phase"] = (
                        "staged" if phase_case == "planned" else "prepared"
                    )
                    successor["recovery_manifest_sha256"] = (
                        "absent"
                        if phase_case == "planned"
                        else manifest_sha256
                    )
                    successor["updated_at"] = "2030-01-02T03:04:09Z"
                    next_path.write_bytes(
                        transaction.canonical_json_bytes(
                            transaction.serialize_transaction_journal(successor)
                        )
                        + b"\n"
                    )
                next_path.chmod(0o600)
                subject = transaction._authorized_recovery_subject(
                    root,
                    plan.transaction_id,
                    project_context=context,
                )
                with transaction._exclusive_recovery_lock(
                    subject,
                    clock="2030-01-02T03:05:30Z",
                    pid=203,
                    token_factory=lambda: "b" * 32,
                ):
                    with transaction._private_recovered_transaction_workspace(
                        root,
                        plan.transaction_id,
                    ) as recovered:
                        outcome = transaction._recover_reversible_transaction(
                            recovered,
                            journal_clock="2030-01-02T03:05:31Z",
                        )

                self.assertEqual(outcome.status, "rolled_back")
                if phase_case == "pre-journal-orphan":
                    self.assertEqual(
                        outcome.resulting_phase,
                        "pre-journal-orphan",
                    )
                    self.assertFalse(journal_path.exists())
                    self.assertEqual(next_path.read_bytes(), current_bytes)
                else:
                    self.assertEqual(outcome.resulting_phase, "rolled-back")
                    self.assertEqual(
                        json.loads(journal_path.read_bytes())["phase"],
                        "rolled-back",
                    )
                    self.assertFalse(next_path.exists())
                for target in plan.targets:
                    canonical = root / target.relative_path
                    self.assertEqual(
                        canonical.read_bytes() if canonical.exists() else None,
                        target._before_bytes if target.existed else None,
                    )

    def test_recover_finalizing_transaction_completes_both_crash_positions(self):
        recover = getattr(transaction, "_recover_finalizing_transaction", None)
        self.assertIsNotNone(recover)
        for evidence_state in ("before", "after-unrecorded", "after-recorded"):
            with self.subTest(evidence=evidence_state), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context, plan = self.prepare_restart_finalizing_case(
                    root,
                    evidence_state,
                )
                subject = transaction._authorized_recovery_subject(
                    root,
                    plan.transaction_id,
                    project_context=context,
                )
                recovery_times = iter(
                    f"2030-01-02T03:05:{second:02d}Z"
                    for second in range(40)
                )
                with (
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                    ) as validate_project,
                    transaction._exclusive_recovery_lock(
                        subject,
                        clock="2030-01-02T03:05:30Z",
                        pid=203,
                        token_factory=lambda: "b" * 32,
                    ),
                ):
                    with transaction._private_recovered_transaction_workspace(
                        root,
                        plan.transaction_id,
                    ) as recovered:
                        outcome = recover(
                            recovered,
                            journal_clock=lambda: next(recovery_times),
                        )

                self.assertEqual(outcome.status, "applied")
                self.assertEqual(outcome.resulting_phase, "complete")
                self.assertEqual(outcome.verified_target_count, len(plan.targets))
                validate_project.assert_not_called()
                journal = json.loads(
                    (
                        root
                        / ".moduflow"
                        / "transactions"
                        / plan.transaction_id
                        / "journal.json"
                    ).read_bytes()
                )
                changed = [
                    index for index, target in enumerate(plan.targets) if target.changed
                ]
                self.assertEqual(journal["phase"], "complete")
                self.assertEqual(journal["applied_target_indexes"], changed)
                for target in plan.targets:
                    canonical = root / target.relative_path
                    self.assertEqual(canonical.read_bytes(), target._after_bytes)

    def test_recover_recovery_required_selects_only_proven_direction(self):
        recover = getattr(
            transaction,
            "_recover_recovery_required_transaction",
            None,
        )
        self.assertIsNotNone(recover)
        cases = ("partial-apply", "rollback-prefix", "evidence-after")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                if case == "partial-apply":
                    context, plan, _applied, _rollback = (
                        self.prepare_restart_recovery_case(
                            root,
                            "applying-recorded",
                            applied_count=2,
                        )
                    )
                elif case == "rollback-prefix":
                    context, plan, _applied, _rollback = (
                        self.prepare_restart_recovery_case(
                            root,
                            "rolling-back-recorded",
                            applied_count=4,
                            rollback_count=1,
                        )
                    )
                else:
                    context, plan = self.prepare_restart_finalizing_case(
                        root,
                        "after-unrecorded",
                    )
                journal_path = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                    / "journal.json"
                )
                journal = json.loads(journal_path.read_bytes())
                journal["phase"] = "recovery-required"
                journal["updated_at"] = "2030-01-02T03:05:00Z"
                journal_path.write_bytes(
                    transaction.canonical_json_bytes(
                        transaction.serialize_transaction_journal(journal)
                    )
                    + b"\n"
                )
                subject = transaction._authorized_recovery_subject(
                    root,
                    plan.transaction_id,
                    project_context=context,
                )
                recovery_times = iter(
                    f"2030-01-02T03:06:{second:02d}Z"
                    for second in range(40)
                )
                with transaction._exclusive_recovery_lock(
                    subject,
                    clock="2030-01-02T03:05:30Z",
                    pid=203,
                    token_factory=lambda: "b" * 32,
                ):
                    with transaction._private_recovered_transaction_workspace(
                        root,
                        plan.transaction_id,
                    ) as recovered:
                        outcome = recover(
                            recovered,
                            journal_clock=lambda: next(recovery_times),
                        )

                expected = "applied" if case == "evidence-after" else "rolled_back"
                resulting = "complete" if case == "evidence-after" else "rolled-back"
                self.assertEqual(outcome.status, expected)
                self.assertEqual(outcome.resulting_phase, resulting)

    def test_recover_recovery_required_preserves_ambiguous_finalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context, plan = self.prepare_restart_finalizing_case(root, "before")
            journal_path = (
                root
                / ".moduflow"
                / "transactions"
                / plan.transaction_id
                / "journal.json"
            )
            journal = json.loads(journal_path.read_bytes())
            journal["phase"] = "recovery-required"
            journal["updated_at"] = "2030-01-02T03:05:00Z"
            journal_path.write_bytes(
                transaction.canonical_json_bytes(
                    transaction.serialize_transaction_journal(journal)
                )
                + b"\n"
            )
            before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if (root / target.relative_path).exists()
                    else None
                )
                for target in plan.targets
            }
            journal_before = journal_path.read_bytes()
            subject = transaction._authorized_recovery_subject(
                root,
                plan.transaction_id,
                project_context=context,
            )
            with transaction._exclusive_recovery_lock(
                subject,
                clock="2030-01-02T03:05:30Z",
                pid=203,
                token_factory=lambda: "b" * 32,
            ):
                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ) as recovered:
                    with self.assertRaises(
                        transaction.LifecycleRecoveryStateError
                    ) as raised:
                        transaction._recover_recovery_required_transaction(
                            recovered,
                            journal_clock="2030-01-02T03:06:00Z",
                        )

            self.assertEqual(raised.exception.code, "RECOVERY_STATE_AMBIGUOUS")
            self.assertEqual(journal_path.read_bytes(), journal_before)
            self.assertEqual(
                {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if (root / target.relative_path).exists()
                        else None
                    )
                    for target in plan.targets
                },
                before,
            )

    def test_recover_finalizing_transaction_preserves_missing_evidence_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context, plan = self.prepare_restart_finalizing_case(root, "before")
            evidence_stage = next(root.glob("**/.moduflow-stage-*"))
            evidence_stage.unlink()
            journal_path = (
                root
                / ".moduflow"
                / "transactions"
                / plan.transaction_id
                / "journal.json"
            )
            journal_before = journal_path.read_bytes()
            canonical_before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if (root / target.relative_path).exists()
                    else None
                )
                for target in plan.targets
            }
            subject = transaction._authorized_recovery_subject(
                root,
                plan.transaction_id,
                project_context=context,
            )
            with transaction._exclusive_recovery_lock(
                subject,
                clock="2030-01-02T03:05:30Z",
                pid=203,
                token_factory=lambda: "b" * 32,
            ):
                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ) as recovered:
                    with self.assertRaises(
                        transaction.LifecycleRecoveryStateError
                    ) as raised:
                        transaction._recover_finalizing_transaction(
                            recovered,
                            journal_clock="2030-01-02T03:06:00Z",
                        )

            self.assertEqual(
                raised.exception.code,
                "RECOVERY_STATE_CANONICAL_UNKNOWN",
            )
            self.assertEqual(journal_path.read_bytes(), journal_before)
            self.assertEqual(
                {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if (root / target.relative_path).exists()
                        else None
                    )
                    for target in plan.targets
                },
                canonical_before,
            )

    def test_recover_loaded_transaction_verifies_terminal_phases_without_mutation(self):
        recover = getattr(transaction, "_recover_loaded_transaction", None)
        self.assertIsNotNone(recover)
        for phase in ("complete", "rolled-back"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                if phase == "complete":
                    context, plan = self.prepare_restart_finalizing_case(
                        root,
                        "after-recorded",
                    )
                else:
                    context, plan, _applied, _rollback = (
                        self.prepare_restart_recovery_case(
                            root,
                            "rolling-back-recorded",
                            applied_count=4,
                            rollback_count=4,
                        )
                    )
                journal_path = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                    / "journal.json"
                )
                journal = json.loads(journal_path.read_bytes())
                journal["phase"] = phase
                journal["applied_target_indexes"] = (
                    [
                        index
                        for index, target in enumerate(plan.targets)
                        if target.changed
                    ]
                    if phase == "complete"
                    else journal["applied_target_indexes"]
                )
                journal["rollback_target_indexes"] = (
                    []
                    if phase == "complete"
                    else journal["rollback_target_indexes"]
                )
                journal["updated_at"] = "2030-01-02T03:06:00Z"
                journal_path.write_bytes(
                    transaction.canonical_json_bytes(
                        transaction.serialize_transaction_journal(journal)
                    )
                    + b"\n"
                )
                before = {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if (root / target.relative_path).exists()
                        else None
                    )
                    for target in plan.targets
                }
                journal_before = journal_path.read_bytes()
                subject = transaction._authorized_recovery_subject(
                    root,
                    plan.transaction_id,
                    project_context=context,
                )
                with (
                    mock.patch.object(
                        transaction.transaction_storage,
                        "persist_serialized_journal",
                    ) as persist,
                    mock.patch.object(
                        transaction.transaction_storage,
                        "finalize_staged_evidence",
                    ) as finalize,
                    mock.patch.object(
                        transaction,
                        "_rollback_changed_target",
                    ) as rollback,
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                    ) as validate_project,
                    transaction._exclusive_recovery_lock(
                        subject,
                        clock="2030-01-02T03:06:30Z",
                        pid=203,
                        token_factory=lambda: "b" * 32,
                    ),
                ):
                    with transaction._private_recovered_transaction_workspace(
                        root,
                        plan.transaction_id,
                    ) as recovered:
                        outcome = recover(recovered)

                self.assertEqual(outcome.status, "noop")
                self.assertEqual(outcome.resulting_phase, phase)
                persist.assert_not_called()
                finalize.assert_not_called()
                rollback.assert_not_called()
                validate_project.assert_not_called()
                self.assertEqual(journal_path.read_bytes(), journal_before)
                self.assertEqual(
                    {
                        target.relative_path: (
                            (root / target.relative_path).read_bytes()
                            if (root / target.relative_path).exists()
                            else None
                        )
                        for target in plan.targets
                    },
                    before,
                )

    def test_transaction_recovery_report_is_strict_deterministic_and_redacted(self):
        serializer = getattr(transaction, "serialize_transaction_recovery", None)
        renderer = getattr(transaction, "render_transaction_recovery", None)
        self.assertIsNotNone(serializer)
        self.assertIsNotNone(renderer)
        report = {
            "schema": "moduflow.lifecycle-transaction-recovery.v1",
            "project_id": "project-103",
            "canonical_root": "/projects/moduflow",
            "status": "rolled_back",
            "transactions": [
                {
                    "transaction_id": "txn-103",
                    "idempotency_key": "d" * 64,
                    "observed_phase": "applying",
                    "resulting_phase": "rolled-back",
                    "status": "rolled_back",
                    "error_code": "none",
                    "targets": [
                        {
                            "role": "issue",
                            "relative_path": "issues/BIZ-103.md",
                            "existed": True,
                            "before_sha256": "a" * 64,
                            "after_sha256": "b" * 64,
                            "changed": True,
                        }
                    ],
                    "verified_target_count": 1,
                }
            ],
        }

        serialized = serializer(report)
        rendered = renderer(report)
        report["transactions"][0]["targets"][0]["role"] = "private"

        self.assertEqual(serialized["status"], "rolled_back")
        self.assertEqual(serialized["transactions"][0]["targets"][0]["role"], "issue")
        self.assertEqual(json.loads(rendered), serialized)
        self.assertTrue(rendered.endswith(b"\n"))
        self.assertFalse(rendered.endswith(b"\n\n"))
        for forbidden in (
            "preimages/",
            ".moduflow-stage-",
            "owner_token",
            "pid",
            "PRIVATE",
            "projected_validation",
            "actor",
        ):
            self.assertNotIn(forbidden, rendered.decode("utf-8"))

        invalid = json.loads(rendered)
        invalid["transactions"][0]["error_code"] = "PRIVATE_ERROR"
        with self.assertRaises(ValueError):
            serializer(invalid)
        invalid = json.loads(rendered)
        invalid["transactions"][0]["resulting_phase"] = "private-phase"
        with self.assertRaises(ValueError):
            serializer(invalid)
        invalid = json.loads(rendered)
        invalid["private"] = "forbidden"
        with self.assertRaises(ValueError):
            serializer(invalid)

    def test_public_explicit_recovery_maps_success_terminal_and_ambiguity(self):
        entry = getattr(transaction, "recover_incomplete_transaction", None)
        self.assertIsNotNone(entry)
        cases = ("rollback", "finalize", "ambiguous")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                if case == "rollback":
                    context, plan, _applied, _rollback = (
                        self.prepare_restart_recovery_case(
                            root,
                            "applying-unrecorded",
                            applied_count=2,
                        )
                    )
                else:
                    context, plan = self.prepare_restart_finalizing_case(
                        root,
                        "before",
                    )
                journal_path = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                    / "journal.json"
                )
                if case == "ambiguous":
                    journal = json.loads(journal_path.read_bytes())
                    journal["phase"] = "recovery-required"
                    journal["updated_at"] = "2030-01-02T03:05:00Z"
                    journal_path.write_bytes(
                        transaction.canonical_json_bytes(
                            transaction.serialize_transaction_journal(journal)
                        )
                        + b"\n"
                    )
                before = {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if (root / target.relative_path).exists()
                        else None
                    )
                    for target in plan.targets
                }
                journal_before = journal_path.read_bytes()
                clock_values = iter(
                    f"2030-01-02T03:06:{second:02d}Z"
                    for second in range(50)
                )
                result = entry(
                    root,
                    plan.transaction_id,
                    project_context=context,
                    clock=lambda: next(clock_values),
                    lock_pid=203,
                    lock_token_factory=lambda: "b" * 32,
                )

                expected = {
                    "rollback": "rolled_back",
                    "finalize": "applied",
                    "ambiguous": "recovery_required",
                }[case]
                self.assertEqual(result["status"], expected)
                self.assertEqual(len(result["transactions"]), 1)
                record = result["transactions"][0]
                self.assertEqual(record["transaction_id"], plan.transaction_id)
                self.assertEqual(record["status"], expected)
                if case == "ambiguous":
                    self.assertEqual(
                        record["error_code"],
                        "RECOVERY_STATE_AMBIGUOUS",
                    )
                    self.assertEqual(journal_path.read_bytes(), journal_before)
                    self.assertEqual(
                        {
                            target.relative_path: (
                                (root / target.relative_path).read_bytes()
                                if (root / target.relative_path).exists()
                                else None
                            )
                            for target in plan.targets
                        },
                        before,
                    )
                else:
                    terminal_clock = iter(
                        f"2030-01-02T03:07:{second:02d}Z"
                        for second in range(10)
                    )
                    terminal = entry(
                        root,
                        plan.transaction_id,
                        project_context=context,
                        clock=lambda: next(terminal_clock),
                        lock_pid=204,
                        lock_token_factory=lambda: "c" * 32,
                    )
                    self.assertEqual(terminal["status"], "noop")

    def test_public_explicit_recovery_denies_or_blocks_before_mutation(self):
        entry = getattr(transaction, "recover_incomplete_transaction", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            denied_context = transaction._json_value(context)
            denied_context.update(
                transaction.project_operation.compute_project_policy(
                    "archived",
                    "internal",
                )
            )
            with mock.patch.object(
                transaction,
                "_private_recovered_transaction_workspace",
            ) as reopen:
                denied = entry(
                    root,
                    "txn-denied",
                    project_context=denied_context,
                )
            self.assertEqual(denied["status"], "denied")
            self.assertEqual(
                denied["transactions"][0]["error_code"],
                "PROJECT_OPERATION_DENIED_ARCHIVED",
            )
            reopen.assert_not_called()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context, plan, _applied, _rollback = self.prepare_restart_recovery_case(
                root,
                "applying-recorded",
                applied_count=1,
            )
            transactions = root / ".moduflow" / "transactions"
            lock_path = transactions / "lifecycle.lock"
            lock_path.write_bytes(
                transaction.canonical_json_bytes(
                    {
                        "schema": "moduflow.lifecycle-transaction-lock.v1",
                        "transaction_id": plan.transaction_id,
                        "pid": 111,
                        "acquired_at": "2030-01-02T03:05:00Z",
                        "owner_token": "a" * 32,
                    }
                )
                + b"\n"
            )
            lock_path.chmod(0o600)
            journal_path = (
                transactions / plan.transaction_id / "journal.json"
            )
            before = journal_path.read_bytes()
            blocked = entry(
                root,
                plan.transaction_id,
                project_context=context,
                pid_probe=lambda _pid, _signal: None,
                lock_pid=203,
                lock_token_factory=lambda: "b" * 32,
            )

            self.assertEqual(blocked["status"], "recovery_required")
            self.assertEqual(
                blocked["transactions"][0]["error_code"],
                "RECOVERY_LOCK_LIVE",
            )
            self.assertEqual(journal_path.read_bytes(), before)
            self.assertTrue(lock_path.exists())

    def test_public_explicit_recovery_faults_only_at_durable_boundaries(self):
        entry = getattr(transaction, "recover_incomplete_transaction", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            with (
                mock.patch.object(
                    transaction,
                    "_authorized_recovery_subject",
                ) as authorize,
                self.assertRaisesRegex(
                    TypeError,
                    "fault_injector must be callable or None",
                ),
            ):
                entry(
                    root,
                    "txn-invalid-injector",
                    project_context=context,
                    fault_injector="invalid",
                )
            authorize.assert_not_called()

        for fault_stage in (
            "after-recovery-read",
            "after-recovery-lock",
            "after-recovery-complete",
        ):
            with self.subTest(fault_stage=fault_stage), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context, plan, _applied, _rollback = (
                    self.prepare_restart_recovery_case(
                        root,
                        "applying-recorded",
                        applied_count=1,
                    )
                )
                transactions = root / ".moduflow" / "transactions"
                lock_path = transactions / "lifecycle.lock"
                journal_path = (
                    transactions / plan.transaction_id / "journal.json"
                )
                journal_before = journal_path.read_bytes()
                canonical_before = {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if (root / target.relative_path).exists()
                        else None
                    )
                    for target in plan.targets
                }
                observed = []

                def inject(stage):
                    observed.append((stage, lock_path.exists()))
                    if stage == fault_stage:
                        raise RuntimeError("PRIVATE RECOVERY INTERRUPTION")

                clock_values = iter(
                    f"2030-01-02T03:08:{second:02d}Z"
                    for second in range(50)
                )
                with self.assertRaisesRegex(
                    RuntimeError,
                    "PRIVATE RECOVERY INTERRUPTION",
                ):
                    entry(
                        root,
                        plan.transaction_id,
                        project_context=context,
                        clock=lambda: next(clock_values),
                        lock_pid=205,
                        lock_token_factory=lambda: "d" * 32,
                        fault_injector=inject,
                    )

                self.assertFalse(lock_path.exists())
                self.assertEqual(observed[0], ("after-recovery-read", False))
                if fault_stage != "after-recovery-read":
                    self.assertEqual(observed[1], ("after-recovery-lock", True))
                if fault_stage == "after-recovery-complete":
                    self.assertEqual(
                        observed[2],
                        ("after-recovery-complete", True),
                    )
                    terminal_clock = iter(
                        f"2030-01-02T03:09:{second:02d}Z"
                        for second in range(10)
                    )
                    retry = entry(
                        root,
                        plan.transaction_id,
                        project_context=context,
                        clock=lambda: next(terminal_clock),
                        lock_pid=206,
                        lock_token_factory=lambda: "e" * 32,
                    )
                    self.assertEqual(retry["status"], "noop")
                else:
                    self.assertEqual(journal_path.read_bytes(), journal_before)
                    self.assertEqual(
                        {
                            target.relative_path: (
                                (root / target.relative_path).read_bytes()
                                if (root / target.relative_path).exists()
                                else None
                            )
                            for target in plan.targets
                        },
                        canonical_before,
                    )

    def test_recovered_transaction_workspace_rejects_unbound_extra_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            with transaction._private_prepared_workspace(
                plan,
                journal_clock=lambda: next(timestamps),
                lock_clock="2030-01-02T03:04:05Z",
                lock_pid=123,
                lock_token_factory=lambda: "1" * 32,
            ):
                pass
            digest = hashlib.sha256(
                plan.transaction_id.encode("utf-8")
            ).hexdigest()
            extra = root / "issues" / f".moduflow-stage-{digest}-999999"
            extra.write_bytes(b"foreign recovery stage\n")
            extra.chmod(0o600)
            before = extra.stat()

            with self.assertRaises(
                transaction.transaction_storage.LifecycleRecoveryStorageError
            ) as raised:
                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ):
                    self.fail("unbound stage must not be adopted")

            self.assertEqual(
                raised.exception.code,
                "RECOVERY_PAYLOAD_MISMATCH",
            )
            self.assertEqual(extra.read_bytes(), b"foreign recovery stage\n")
            self.assertEqual(extra.stat().st_ino, before.st_ino)

    def test_recovered_transaction_workspace_verifies_unbound_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            with transaction._private_prepared_workspace(
                plan,
                journal_clock=lambda: next(timestamps),
                lock_clock="2030-01-02T03:04:05Z",
                lock_pid=123,
                lock_token_factory=lambda: "1" * 32,
            ):
                pass
            workspace = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            journal_path = workspace / "journal.json"
            staged = json.loads(journal_path.read_bytes())
            staged["phase"] = "staged"
            staged["recovery_manifest_sha256"] = "absent"
            staged["applied_target_indexes"] = []
            staged["rollback_target_indexes"] = []
            staged["updated_at"] = "2030-01-02T03:04:06Z"
            journal_path.write_bytes(
                transaction.canonical_json_bytes(
                    transaction.serialize_transaction_journal(staged)
                )
                + b"\n"
            )
            preimage = workspace / "preimages" / "000000.bin"
            preimage.write_bytes(b"corrupted unbound preimage\n")

            with self.assertRaises(
                transaction.transaction_storage.LifecycleRecoveryStorageError
            ) as raised:
                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ):
                    self.fail("unbound private material must still verify")

            self.assertEqual(
                raised.exception.code,
                "RECOVERY_PAYLOAD_MISMATCH",
            )
            self.assertEqual(
                journal_path.read_bytes(),
                transaction.canonical_json_bytes(
                    transaction.serialize_transaction_journal(staged)
                )
                + b"\n",
            )

    def test_cleanup_inventory_proof_is_private_frozen_and_read_only(self):
        verify = getattr(
            transaction.transaction_storage,
            "verify_recovery_cleanup_inventory",
            None,
        )
        self.assertIsNotNone(verify)
        for terminal in ("complete", "rolled-back"):
            with self.subTest(terminal=terminal), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                if terminal == "complete":
                    context, plan = self.prepare_restart_finalizing_case(
                        root,
                        "after-recorded",
                    )
                else:
                    context, plan, _applied, _rollback = (
                        self.prepare_restart_recovery_case(
                            root,
                            "rolling-back-recorded",
                            applied_count=4,
                            rollback_count=4,
                        )
                    )
                recovery_times = iter(
                    f"2030-01-02T03:10:{second:02d}Z"
                    for second in range(50)
                )
                recovered_report = transaction.recover_incomplete_transaction(
                    root,
                    plan.transaction_id,
                    project_context=context,
                    clock=lambda: next(recovery_times),
                    lock_pid=207,
                    lock_token_factory=lambda: "f" * 32,
                )
                self.assertIn(
                    recovered_report["status"],
                    {"applied", "rolled_back"},
                )

                def tree_snapshot():
                    snapshot = {}
                    for path in sorted(root.rglob("*")):
                        metadata = path.lstat()
                        relative = path.relative_to(root).as_posix()
                        snapshot[relative] = (
                            stat.S_IFMT(metadata.st_mode),
                            stat.S_IMODE(metadata.st_mode),
                            metadata.st_ino,
                            metadata.st_nlink,
                            path.read_bytes() if path.is_file() else None,
                        )
                    return snapshot

                before = tree_snapshot()
                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ) as recovered:
                    journal = recovered.journal_state.journal
                    with (
                        mock.patch.object(
                            transaction.transaction_storage.os,
                            "unlink",
                            side_effect=AssertionError("cleanup proof unlinked"),
                        ) as unlink,
                        mock.patch.object(
                            transaction.transaction_storage.os,
                            "rmdir",
                            side_effect=AssertionError("cleanup proof removed directory"),
                        ) as rmdir,
                        mock.patch.object(
                            transaction.transaction_storage.os,
                            "replace",
                            side_effect=AssertionError("cleanup proof replaced file"),
                        ) as replacement,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "persist_serialized_journal",
                            side_effect=AssertionError("cleanup proof persisted journal"),
                        ) as persist,
                    ):
                        proof = verify(
                            recovered._workspace,
                            transaction._recovery_targets_from_journal(journal),
                            recovered.journal_state._control_snapshot,
                            recoverable_missing_indexes=(
                                transaction._recoverable_missing_stage_indexes(
                                    journal
                                )
                            ),
                        )
                    unlink.assert_not_called()
                    rmdir.assert_not_called()
                    replacement.assert_not_called()
                    persist.assert_not_called()

                self.assertEqual(repr(proof), "_RecoveryCleanupInventory()")
                with self.assertRaises(FrozenInstanceError):
                    proof._workspace_directory = None
                for forbidden in (
                    str(root),
                    plan.transaction_id,
                    ".moduflow-stage-",
                    "preimages",
                    "journal.json",
                ):
                    self.assertNotIn(forbidden, repr(proof))
                self.assertEqual(tree_snapshot(), before)

    def test_cleanup_inventory_proof_rejects_post_reopen_inventory_changes(self):
        verify = getattr(
            transaction.transaction_storage,
            "verify_recovery_cleanup_inventory",
            None,
        )
        self.assertIsNotNone(verify)
        for corruption in (
            "extra-control",
            "hardlinked-preimage",
            "extra-stage",
            "workspace-replaced",
        ):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context, plan, _applied, _rollback = (
                    self.prepare_restart_recovery_case(
                        root,
                        "rolling-back-recorded",
                        applied_count=4,
                        rollback_count=4,
                    )
                )
                recovery_times = iter(
                    f"2030-01-02T03:11:{second:02d}Z"
                    for second in range(50)
                )
                transaction.recover_incomplete_transaction(
                    root,
                    plan.transaction_id,
                    project_context=context,
                    clock=lambda: next(recovery_times),
                    lock_pid=208,
                    lock_token_factory=lambda: "1" * 32,
                )
                workspace = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                )
                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ) as recovered:
                    journal = recovered.journal_state.journal
                    if corruption == "extra-control":
                        changed = workspace / "foreign-private-file"
                        changed.write_bytes(b"foreign\n")
                        changed.chmod(0o600)
                    elif corruption == "hardlinked-preimage":
                        changed = workspace / "preimages" / "000000.bin"
                        original = changed.read_bytes()
                        changed.unlink()
                        external = root / "hardlinked-private-payload"
                        external.write_bytes(original)
                        os.link(external, changed)
                    elif corruption == "extra-stage":
                        digest = hashlib.sha256(
                            plan.transaction_id.encode("utf-8")
                        ).hexdigest()
                        changed = (
                            root
                            / "issues"
                            / f".moduflow-stage-{digest}-999999"
                        )
                        changed.write_bytes(b"foreign stage\n")
                        changed.chmod(0o600)
                    else:
                        moved = workspace.with_name(
                            f"{plan.transaction_id}-original"
                        )
                        workspace.rename(moved)
                        workspace.mkdir(mode=0o700)
                        (workspace / "preimages").mkdir(mode=0o700)
                        changed = workspace
                    before = changed.lstat()
                    with self.assertRaises(
                        transaction.transaction_storage.LifecycleRecoveryStorageError
                    ) as raised:
                        verify(
                            recovered._workspace,
                            transaction._recovery_targets_from_journal(journal),
                            recovered.journal_state._control_snapshot,
                            recoverable_missing_indexes=(
                                transaction._recoverable_missing_stage_indexes(
                                    journal
                                )
                            ),
                        )

                self.assertIn(
                    raised.exception.code,
                    {
                        "RECOVERY_WORKSPACE_UNSAFE",
                        "RECOVERY_CONTROL_FILE_UNSAFE",
                        "RECOVERY_PAYLOAD_INVALID",
                        "RECOVERY_PAYLOAD_MISMATCH",
                    },
                )
                self.assertTrue(changed.exists())
                self.assertEqual(changed.lstat().st_ino, before.st_ino)

    def test_cleanup_inventory_proof_accepts_exact_pre_journal_orphan(self):
        verify = getattr(
            transaction.transaction_storage,
            "verify_recovery_cleanup_inventory",
            None,
        )
        self.assertIsNotNone(verify)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            with transaction._private_prepared_workspace(
                plan,
                journal_clock=lambda: next(timestamps),
                lock_clock="2030-01-02T03:04:05Z",
                lock_pid=123,
                lock_token_factory=lambda: "1" * 32,
            ):
                pass
            workspace = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            journal_path = workspace / "journal.json"
            next_path = workspace / "journal.next"
            planned = json.loads(journal_path.read_bytes())
            planned["phase"] = "planned"
            planned["recovery_manifest_sha256"] = "absent"
            planned["applied_target_indexes"] = []
            planned["rollback_target_indexes"] = []
            planned["updated_at"] = "2030-01-02T03:04:05Z"
            planned_bytes = (
                transaction.canonical_json_bytes(
                    transaction.serialize_transaction_journal(planned)
                )
                + b"\n"
            )
            next_path.write_bytes(planned_bytes)
            next_path.chmod(0o600)
            journal_path.unlink()

            with transaction._private_recovered_transaction_workspace(
                root,
                plan.transaction_id,
            ) as recovered:
                self.assertEqual(
                    recovered.journal_state.authority,
                    "pre-journal-orphan",
                )
                proof = verify(
                    recovered._workspace,
                    transaction._recovery_targets_from_journal(
                        recovered.journal_state.journal
                    ),
                    recovered.journal_state._control_snapshot,
                    recoverable_missing_indexes=(),
                )

            self.assertEqual(repr(proof), "_RecoveryCleanupInventory()")
            self.assertEqual(next_path.read_bytes(), planned_bytes)
            self.assertFalse(journal_path.exists())
            with transaction._private_recovered_cleanup_workspace(
                root,
                plan.transaction_id,
            ) as cleanup:
                self.assertEqual(
                    cleanup.terminal_kind,
                    "pre-journal-orphan",
                )
                self.assertEqual(
                    cleanup.verified_target_count,
                    len(plan.targets),
                )

    def test_cleanup_candidate_accepts_only_proven_terminal_states_under_lock(self):
        prove = getattr(
            transaction,
            "_prove_recovery_cleanup_candidate",
            None,
        )
        self.assertIsNotNone(prove)
        for terminal in ("complete", "rolled-back", "pre-journal-orphan"):
            with self.subTest(terminal=terminal), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                if terminal == "complete":
                    context, plan = self.prepare_restart_finalizing_case(
                        root,
                        "after-recorded",
                    )
                    recovery_times = iter(
                        f"2030-01-02T03:12:{second:02d}Z"
                        for second in range(50)
                    )
                    transaction.recover_incomplete_transaction(
                        root,
                        plan.transaction_id,
                        project_context=context,
                        clock=lambda: next(recovery_times),
                        lock_pid=209,
                        lock_token_factory=lambda: "2" * 32,
                    )
                elif terminal == "rolled-back":
                    context, plan, _applied, _rollback = (
                        self.prepare_restart_recovery_case(
                            root,
                            "rolling-back-recorded",
                            applied_count=4,
                            rollback_count=4,
                        )
                    )
                    recovery_times = iter(
                        f"2030-01-02T03:13:{second:02d}Z"
                        for second in range(50)
                    )
                    transaction.recover_incomplete_transaction(
                        root,
                        plan.transaction_id,
                        project_context=context,
                        clock=lambda: next(recovery_times),
                        lock_pid=210,
                        lock_token_factory=lambda: "3" * 32,
                    )
                else:
                    context = self.scaffold(root)
                    (root / "workspace" / "transactions").mkdir()
                    plan = transaction.plan_lifecycle_transaction(
                        root,
                        self.intent(),
                        project_context=context,
                        clock="2030-01-02",
                    )
                    timestamps = iter(
                        (
                            "2030-01-02T03:04:05Z",
                            "2030-01-02T03:04:06Z",
                            "2030-01-02T03:04:07Z",
                        )
                    )
                    with transaction._private_prepared_workspace(
                        plan,
                        journal_clock=lambda: next(timestamps),
                        lock_clock="2030-01-02T03:04:05Z",
                        lock_pid=123,
                        lock_token_factory=lambda: "1" * 32,
                    ):
                        pass
                    workspace = (
                        root
                        / ".moduflow"
                        / "transactions"
                        / plan.transaction_id
                    )
                    journal_path = workspace / "journal.json"
                    next_path = workspace / "journal.next"
                    planned = json.loads(journal_path.read_bytes())
                    planned["phase"] = "planned"
                    planned["recovery_manifest_sha256"] = "absent"
                    planned["applied_target_indexes"] = []
                    planned["rollback_target_indexes"] = []
                    planned["updated_at"] = "2030-01-02T03:04:05Z"
                    next_path.write_bytes(
                        transaction.canonical_json_bytes(
                            transaction.serialize_transaction_journal(planned)
                        )
                        + b"\n"
                    )
                    next_path.chmod(0o600)
                    journal_path.unlink()

                subject = transaction._authorized_recovery_subject(
                    root,
                    plan.transaction_id,
                    project_context=context,
                )
                lock_path = root / ".moduflow/transactions/lifecycle.lock"
                with transaction._exclusive_recovery_lock(
                    subject,
                    clock="2030-01-02T03:14:00Z",
                    pid=211,
                    token_factory=lambda: "4" * 32,
                ):
                    self.assertTrue(lock_path.is_file())
                    with transaction._private_recovered_transaction_workspace(
                        root,
                        plan.transaction_id,
                    ) as recovered:
                        candidate = prove(recovered)

                self.assertFalse(lock_path.exists())
                self.assertEqual(candidate.terminal_kind, terminal)
                self.assertEqual(
                    candidate.verified_target_count,
                    len(plan.targets),
                )
                expected_authority = (
                    "pre-journal-orphan"
                    if terminal == "pre-journal-orphan"
                    else "current"
                )
                self.assertEqual(candidate.journal_authority, expected_authority)
                self.assertNotIn(str(root), repr(candidate))
                self.assertNotIn("_inventory", repr(candidate))
                with self.assertRaises(FrozenInstanceError):
                    candidate.terminal_kind = "private"

    def test_cleanup_candidate_rejects_nonterminal_phases_before_inventory(self):
        prove = getattr(
            transaction,
            "_prove_recovery_cleanup_candidate",
            None,
        )
        error_type = getattr(
            transaction,
            "LifecycleRecoveryCleanupError",
            None,
        )
        self.assertIsNotNone(prove)
        self.assertIsNotNone(error_type)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context, plan, _applied, _rollback = (
                self.prepare_restart_recovery_case(
                    root,
                    "applying-recorded",
                    applied_count=1,
                )
            )
            subject = transaction._authorized_recovery_subject(
                root,
                plan.transaction_id,
                project_context=context,
            )
            with transaction._exclusive_recovery_lock(
                subject,
                clock="2030-01-02T03:15:00Z",
                pid=212,
                token_factory=lambda: "5" * 32,
            ):
                with transaction._private_recovered_transaction_workspace(
                    root,
                    plan.transaction_id,
                ) as recovered:
                    with mock.patch.object(
                        transaction.transaction_storage,
                        "verify_recovery_cleanup_inventory",
                    ) as inventory:
                        for phase in (
                            "planned",
                            "staged",
                            "prepared",
                            "applying",
                            "post-validating",
                            "finalizing",
                            "rolling-back",
                            "recovery-required",
                        ):
                            with self.subTest(phase=phase):
                                journal = transaction._json_value(
                                    recovered.journal_state.journal
                                )
                                journal["phase"] = phase
                                selected = replace(
                                    recovered,
                                    journal_state=replace(
                                        recovered.journal_state,
                                        journal=journal,
                                    ),
                                )
                                with self.assertRaises(error_type) as raised:
                                    prove(selected)
                                self.assertEqual(
                                    raised.exception.code,
                                    "RECOVERY_CLEANUP_INELIGIBLE",
                                )
                                self.assertEqual(
                                    str(raised.exception),
                                    "RECOVERY_CLEANUP_INELIGIBLE",
                                )
                        inventory.assert_not_called()

                    malformed = replace(
                        recovered,
                        journal_state=replace(
                            recovered.journal_state,
                            journal={},
                        ),
                    )
                    with self.assertRaises(error_type) as raised:
                        prove(malformed)
                    self.assertEqual(
                        raised.exception.code,
                        "RECOVERY_CLEANUP_INELIGIBLE",
                    )

        invalid = error_type("PRIVATE CLEANUP ERROR")
        self.assertEqual(invalid.code, "RECOVERY_CLEANUP_INELIGIBLE")
        self.assertEqual(str(invalid), "RECOVERY_CLEANUP_INELIGIBLE")

    def test_cleanup_candidate_maps_canonical_and_inventory_uncertainty(self):
        prove = getattr(
            transaction,
            "_prove_recovery_cleanup_candidate",
            None,
        )
        error_type = getattr(
            transaction,
            "LifecycleRecoveryCleanupError",
            None,
        )
        self.assertIsNotNone(prove)
        self.assertIsNotNone(error_type)
        for uncertainty in ("canonical", "inventory"):
            with self.subTest(uncertainty=uncertainty), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context, plan = self.prepare_restart_finalizing_case(
                    root,
                    "after-recorded",
                )
                recovery_times = iter(
                    f"2030-01-02T03:16:{second:02d}Z"
                    for second in range(50)
                )
                transaction.recover_incomplete_transaction(
                    root,
                    plan.transaction_id,
                    project_context=context,
                    clock=lambda: next(recovery_times),
                    lock_pid=213,
                    lock_token_factory=lambda: "6" * 32,
                )
                subject = transaction._authorized_recovery_subject(
                    root,
                    plan.transaction_id,
                    project_context=context,
                )
                lock_path = root / ".moduflow/transactions/lifecycle.lock"
                workspace = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                )
                with transaction._exclusive_recovery_lock(
                    subject,
                    clock="2030-01-02T03:17:00Z",
                    pid=214,
                    token_factory=lambda: "7" * 32,
                ):
                    with transaction._private_recovered_transaction_workspace(
                        root,
                        plan.transaction_id,
                    ) as recovered:
                        self.assertTrue(lock_path.is_file())
                        if uncertainty == "canonical":
                            changed_target = next(
                                target for target in plan.targets if target.changed
                            )
                            canonical = root / changed_target.relative_path
                            canonical.write_bytes(b"unknown canonical bytes\n")
                            with mock.patch.object(
                                transaction.transaction_storage,
                                "verify_recovery_cleanup_inventory",
                            ) as inventory:
                                with self.assertRaises(error_type) as raised:
                                    prove(recovered)
                            inventory.assert_not_called()
                            expected = "RECOVERY_CLEANUP_CANONICAL_UNPROVEN"
                        else:
                            foreign = workspace / "foreign-cleanup-entry"
                            foreign.write_bytes(b"must remain\n")
                            foreign.chmod(0o600)
                            with self.assertRaises(error_type) as raised:
                                prove(recovered)
                            self.assertEqual(foreign.read_bytes(), b"must remain\n")
                            expected = "RECOVERY_CLEANUP_INVENTORY_UNSAFE"
                        self.assertEqual(raised.exception.code, expected)
                        self.assertEqual(str(raised.exception), expected)

                self.assertFalse(lock_path.exists())

    def test_cleanup_resume_workspace_accepts_only_protocol_suffixes_read_only(self):
        reopen = getattr(
            transaction,
            "_private_recovered_cleanup_workspace",
            None,
        )
        self.assertIsNotNone(reopen)
        for remainder in (
            "terminal-full",
            "terminal-private-suffix",
            "terminal-control-suffix",
            "empty-workspace",
        ):
            with self.subTest(remainder=remainder), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context, plan = self.prepare_restart_finalizing_case(
                    root,
                    "after-recorded",
                )
                recovery_times = iter(
                    f"2030-01-02T03:18:{second:02d}Z"
                    for second in range(50)
                )
                transaction.recover_incomplete_transaction(
                    root,
                    plan.transaction_id,
                    project_context=context,
                    clock=lambda: next(recovery_times),
                    lock_pid=215,
                    lock_token_factory=lambda: "8" * 32,
                )
                workspace = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                )
                preimages = workspace / "preimages"
                manifest = workspace / "recovery-manifest.json"
                journal = workspace / "journal.json"
                if remainder != "terminal-full":
                    for path in tuple(preimages.iterdir()):
                        path.unlink()
                    preimages.rmdir()
                if remainder in {"terminal-control-suffix", "empty-workspace"}:
                    manifest.unlink()
                if remainder == "empty-workspace":
                    journal.unlink()

                before = {
                    path.relative_to(root).as_posix(): (
                        path.lstat().st_ino,
                        path.read_bytes() if path.is_file() else None,
                    )
                    for path in root.rglob("*")
                }
                subject = transaction._authorized_recovery_subject(
                    root,
                    plan.transaction_id,
                    project_context=context,
                )
                with transaction._exclusive_recovery_lock(
                    subject,
                    clock="2030-01-02T03:19:00Z",
                    pid=216,
                    token_factory=lambda: "9" * 32,
                ):
                    with reopen(root, plan.transaction_id) as resumed:
                        self.assertEqual(resumed.remainder_kind, remainder)
                        self.assertEqual(
                            resumed.terminal_kind,
                            "unknown" if remainder == "empty-workspace" else "complete",
                        )
                        if remainder != "empty-workspace":
                            self.assertEqual(
                                resumed.verified_target_count,
                                len(plan.targets),
                            )
                        self.assertNotIn(str(root), repr(resumed))
                        self.assertNotIn(plan.transaction_id, repr(resumed))

                after = {
                    path.relative_to(root).as_posix(): (
                        path.lstat().st_ino,
                        path.read_bytes() if path.is_file() else None,
                    )
                    for path in root.rglob("*")
                }
                self.assertEqual(after, before)
                if remainder != "terminal-full":
                    with self.assertRaises(
                        transaction.transaction_storage.LifecycleRecoveryStorageError
                    ):
                        with transaction.transaction_storage.reopen_transaction_workspace(
                            root,
                            plan.transaction_id,
                        ):
                            self.fail("ordinary recovery reopen must remain strict")

    def test_cleanup_resume_workspace_rejects_non_suffix_remainders(self):
        reopen = getattr(
            transaction,
            "_private_recovered_cleanup_workspace",
            None,
        )
        error_type = getattr(
            transaction,
            "LifecycleRecoveryCleanupError",
            None,
        )
        self.assertIsNotNone(reopen)
        self.assertIsNotNone(error_type)
        for corruption in (
            "manifest-missing-with-preimages",
            "journal-missing-with-manifest",
            "journal-missing-with-foreign",
        ):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context, plan = self.prepare_restart_finalizing_case(
                    root,
                    "after-recorded",
                )
                recovery_times = iter(
                    f"2030-01-02T03:20:{second:02d}Z"
                    for second in range(50)
                )
                transaction.recover_incomplete_transaction(
                    root,
                    plan.transaction_id,
                    project_context=context,
                    clock=lambda: next(recovery_times),
                    lock_pid=217,
                    lock_token_factory=lambda: "a" * 32,
                )
                workspace = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                )
                if corruption == "manifest-missing-with-preimages":
                    changed = workspace / "recovery-manifest.json"
                    changed.unlink()
                else:
                    changed = workspace / "journal.json"
                    changed.unlink()
                    if corruption == "journal-missing-with-foreign":
                        (workspace / "recovery-manifest.json").unlink()
                        preimages = workspace / "preimages"
                        for path in tuple(preimages.iterdir()):
                            path.unlink()
                        preimages.rmdir()
                        changed = workspace / "foreign-remainder"
                        changed.write_bytes(b"must remain\n")
                        changed.chmod(0o600)
                with self.assertRaises(error_type) as raised:
                    with reopen(root, plan.transaction_id):
                        self.fail("unsafe cleanup remainder must not be yielded")

                self.assertEqual(
                    raised.exception.code,
                    "RECOVERY_CLEANUP_REMAINDER_UNSAFE",
                )
                if changed.exists():
                    self.assertTrue(changed.exists())

    def test_private_preimage_workspace_denies_or_rejects_before_side_effects(self):
        entry = getattr(transaction, "_private_preimage_workspace", None)
        self.assertIsNotNone(entry)
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
            denied = replace(plan, _project_context=denied_context)
            with (
                mock.patch.object(transaction.os, "open") as open_file,
                mock.patch.object(transaction.os, "mkdir") as make_directory,
                mock.patch.object(transaction.os, "fsync") as sync_file,
                mock.patch.object(
                    transaction.transaction_storage,
                    "private_transaction_workspace",
                ) as open_workspace,
            ):
                with self.assertRaises(
                    transaction.project_operation.ProjectOperationDenied
                ) as raised:
                    with entry(denied):
                        self.fail("denied storage must not be yielded")
            self.assertEqual(
                raised.exception.decision["reason_code"],
                "PROJECT_OPERATION_DENIED_ARCHIVED",
            )
            open_file.assert_not_called()
            make_directory.assert_not_called()
            sync_file.assert_not_called()
            open_workspace.assert_not_called()

            invalid_target = replace(
                plan.targets[0],
                before_sha256="0" * 64,
            )
            invalid = replace(
                plan,
                targets=(invalid_target, *plan.targets[1:]),
            )
            with mock.patch.object(
                transaction,
                "_exclusive_lifecycle_lock",
            ) as acquire_lock:
                with self.assertRaises(
                    transaction.transaction_storage.LifecycleStorageError
                ) as raised:
                    with entry(invalid):
                        self.fail("invalid storage target must not be yielded")
            self.assertEqual(raised.exception.code, "STORAGE_CONTEXT_INVALID")
            acquire_lock.assert_not_called()
            self.assertFalse((root / ".moduflow" / "transactions").exists())

    def test_private_preimage_workspace_holds_lock_and_persists_exact_plan_bytes(self):
        entry = getattr(transaction, "_private_preimage_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            canonical_before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if target.existed
                    else None
                )
                for target in plan.targets
            }
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            workspace_path = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )

            with entry(
                plan,
                lock_clock="2030-01-02T03:04:05Z",
                lock_pid=123,
                lock_token_factory=lambda: "1" * 32,
            ) as state:
                self.assertTrue(lock_path.is_file())
                self.assertEqual(
                    [target.index for target in state.storage_targets],
                    list(range(len(plan.targets))),
                )
                self.assertEqual(
                    [record.index for record in state.preimages],
                    list(range(len(plan.targets))),
                )
                for target, record in zip(plan.targets, state.preimages):
                    if target.existed:
                        stored = workspace_path / record.relative_name
                        self.assertEqual(stored.read_bytes(), target._before_bytes)
                        self.assertEqual(record.sha256, target.before_sha256)
                    else:
                        self.assertEqual(record.state, "absent")
                        self.assertEqual(record.relative_name, "absent")
                self.assertNotIn(str(root), repr(state))
                self.assertNotIn("_before_bytes", repr(state))
                self.assertNotIn("_after_bytes", repr(state))

            self.assertFalse(lock_path.exists())
            self.assertTrue(workspace_path.is_dir())
            self.assertEqual(
                {
                    relative: (
                        (root / relative).read_bytes()
                        if (root / relative).exists()
                        else None
                    )
                    for relative in canonical_before
                },
                canonical_before,
            )

    def test_private_staged_workspace_holds_lock_seals_manifest_and_never_changes_canonical_targets(self):
        entry = getattr(transaction, "_private_staged_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            canonical_before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if target.existed
                    else None
                )
                for target in plan.targets
            }
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            workspace_path = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )

            with entry(
                plan,
                lock_clock="2030-01-02T03:04:05Z",
                lock_pid=123,
                lock_token_factory=lambda: "1" * 32,
            ) as state:
                self.assertTrue(lock_path.is_file())
                self.assertEqual(
                    [target.index for target in state.storage_targets],
                    list(range(len(plan.targets))),
                )
                self.assertEqual(
                    [record.index for record in state.preimages],
                    list(range(len(plan.targets))),
                )
                self.assertEqual(
                    [record.index for record in state.staged_proposals],
                    list(range(len(plan.targets))),
                )
                for target, proposal in zip(plan.targets, state.staged_proposals):
                    if target.changed:
                        staged = root / proposal.relative_name
                        self.assertEqual(proposal.state, "staged")
                        self.assertEqual(staged.read_bytes(), target._after_bytes)
                        self.assertEqual(proposal.sha256, target.after_sha256)
                    else:
                        self.assertEqual(proposal.state, "unchanged")
                        self.assertEqual(proposal.relative_name, "unchanged")
                manifest_path = workspace_path / "recovery-manifest.json"
                manifest_bytes = manifest_path.read_bytes()
                manifest = json.loads(manifest_bytes)
                self.assertEqual(
                    state.recovery_manifest.sha256,
                    hashlib.sha256(manifest_bytes).hexdigest(),
                )
                self.assertEqual(
                    [record["relative_path"] for record in manifest["targets"]],
                    [target.relative_path for target in plan.targets],
                )
                rendered = repr(state)
                self.assertNotIn(str(root), rendered)
                self.assertNotIn("_before_bytes", rendered)
                self.assertNotIn("_after_bytes", rendered)

            self.assertFalse(lock_path.exists())
            self.assertTrue(workspace_path.is_dir())
            self.assertTrue((workspace_path / "recovery-manifest.json").is_file())
            self.assertEqual(
                {
                    relative: (
                        (root / relative).read_bytes()
                        if (root / relative).exists()
                        else None
                    )
                    for relative in canonical_before
                },
                canonical_before,
            )

    def test_private_prepared_workspace_rejects_canonical_conflict_under_lock_before_private_state(self):
        entry = getattr(transaction, "_private_prepared_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            changed_target = next(target for target in plan.targets if target.existed)
            changed_path = root / changed_target.relative_path
            changed_path.write_bytes(b"external edit after planning")
            canonical_at_entry = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if (root / target.relative_path).is_file()
                    else None
                )
                for target in plan.targets
            }
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            workspace_path = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            real_verify = transaction.transaction_storage.verify_canonical_preimages
            observed_lock = []

            def tracked_verify(canonical_root, storage_targets):
                observed_lock.append(lock_path.is_file())
                return real_verify(canonical_root, storage_targets)

            conflict = None
            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            with mock.patch.object(
                transaction.transaction_storage,
                "verify_canonical_preimages",
                side_effect=tracked_verify,
            ):
                try:
                    with entry(
                        plan,
                        journal_clock=lambda: next(timestamps),
                        lock_clock="2030-01-02T03:04:05Z",
                        lock_pid=123,
                        lock_token_factory=lambda: "1" * 32,
                    ):
                        pass
                except transaction.transaction_storage.LifecycleCanonicalConflict as exc:
                    conflict = exc

            self.assertIsNotNone(conflict)
            self.assertEqual(conflict.code, "CANONICAL_PREIMAGE_CONFLICT")
            self.assertEqual(
                conflict.target_index,
                changed_target.apply_order,
            )
            self.assertEqual(observed_lock, [True])
            self.assertFalse(lock_path.exists())
            self.assertFalse(workspace_path.exists())
            self.assertEqual(
                {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if (root / target.relative_path).is_file()
                        else None
                    )
                    for target in plan.targets
                },
                canonical_at_entry,
            )

    def test_private_prepared_workspace_verifies_once_under_lock_before_workspace(self):
        entry = getattr(transaction, "_private_prepared_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            workspace_path = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            events = []
            real_verify = transaction.transaction_storage.verify_canonical_preimages
            real_workspace = (
                transaction.transaction_storage.private_transaction_workspace
            )

            def tracked_verify(canonical_root, storage_targets):
                self.assertTrue(lock_path.is_file())
                self.assertFalse(workspace_path.exists())
                events.append("verify")
                return real_verify(canonical_root, storage_targets)

            def tracked_workspace(*args, **kwargs):
                events.append("workspace")
                return real_workspace(*args, **kwargs)

            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            with (
                mock.patch.object(
                    transaction.transaction_storage,
                    "verify_canonical_preimages",
                    side_effect=tracked_verify,
                ) as verify,
                mock.patch.object(
                    transaction.transaction_storage,
                    "private_transaction_workspace",
                    side_effect=tracked_workspace,
                ) as open_workspace,
            ):
                with entry(
                    plan,
                    journal_clock=lambda: next(timestamps),
                    lock_clock="2030-01-02T03:04:05Z",
                    lock_pid=123,
                    lock_token_factory=lambda: "1" * 32,
                ) as state:
                    journal_bytes = (workspace_path / "journal.json").read_bytes()
                    self.assertEqual(
                        state.journal_sha256,
                        hashlib.sha256(journal_bytes).hexdigest(),
                    )

            self.assertEqual(events[:2], ["verify", "workspace"])
            verify.assert_called_once()
            open_workspace.assert_called_once()
            self.assertTrue(workspace_path.is_dir())
            self.assertFalse(lock_path.exists())

    def test_private_prepared_workspace_rejects_invalid_journal_before_storage_side_effects(self):
        entry = getattr(transaction, "_private_prepared_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )

            with (
                mock.patch.object(
                    transaction,
                    "serialize_transaction_journal",
                    side_effect=transaction.LifecycleJournalError(
                        "JOURNAL_RECORD_INVALID"
                    ),
                ),
                mock.patch.object(transaction, "_exclusive_lifecycle_lock") as acquire_lock,
                mock.patch.object(
                    transaction.transaction_storage,
                    "verify_canonical_preimages",
                ) as verify_preimages,
                mock.patch.object(
                    transaction.transaction_storage,
                    "private_transaction_workspace",
                ) as open_workspace,
                mock.patch.object(
                    transaction.transaction_storage,
                    "persist_serialized_journal",
                ) as persist_journal,
                mock.patch.object(
                    transaction.transaction_storage,
                    "store_preimages",
                ) as store_preimages,
                mock.patch.object(
                    transaction.transaction_storage,
                    "stage_proposed_targets",
                ) as stage_targets,
                mock.patch.object(
                    transaction.transaction_storage,
                    "finalize_recovery_manifest",
                ) as finalize_manifest,
                mock.patch.object(transaction.os, "replace") as replace_file,
                mock.patch.object(transaction.os, "fsync") as sync_file,
            ):
                with self.assertRaises(transaction.LifecycleJournalError) as raised:
                    with entry(
                        plan,
                        journal_clock="2030-01-02T03:04:05Z",
                    ):
                        self.fail("invalid journal must not be yielded")
            self.assertEqual(raised.exception.code, "JOURNAL_RECORD_INVALID")
            acquire_lock.assert_not_called()
            verify_preimages.assert_not_called()
            open_workspace.assert_not_called()
            persist_journal.assert_not_called()
            store_preimages.assert_not_called()
            stage_targets.assert_not_called()
            finalize_manifest.assert_not_called()
            replace_file.assert_not_called()
            sync_file.assert_not_called()

            with (
                mock.patch.object(transaction, "_exclusive_lifecycle_lock") as acquire_lock,
                mock.patch.object(
                    transaction.transaction_storage,
                    "verify_canonical_preimages",
                ) as verify_preimages,
                mock.patch.object(
                    transaction.transaction_storage,
                    "private_transaction_workspace",
                ) as open_workspace,
                mock.patch.object(
                    transaction.transaction_storage,
                    "persist_serialized_journal",
                ) as persist_journal,
                mock.patch.object(
                    transaction.transaction_storage,
                    "store_preimages",
                ) as store_preimages,
                mock.patch.object(
                    transaction.transaction_storage,
                    "stage_proposed_targets",
                ) as stage_targets,
                mock.patch.object(
                    transaction.transaction_storage,
                    "finalize_recovery_manifest",
                ) as finalize_manifest,
                mock.patch.object(transaction.os, "replace") as replace_file,
                mock.patch.object(transaction.os, "fsync") as sync_file,
            ):
                with self.assertRaises(transaction.LifecycleJournalError) as raised:
                    with entry(plan, journal_clock="NOT-A-TIMESTAMP"):
                        self.fail("invalid journal clock must not be yielded")
            self.assertEqual(raised.exception.code, "JOURNAL_RECORD_INVALID")
            acquire_lock.assert_not_called()
            verify_preimages.assert_not_called()
            open_workspace.assert_not_called()
            persist_journal.assert_not_called()
            store_preimages.assert_not_called()
            stage_targets.assert_not_called()
            finalize_manifest.assert_not_called()
            replace_file.assert_not_called()
            sync_file.assert_not_called()

    def test_private_prepared_workspace_persists_exact_phase_order_under_one_lock_without_canonical_changes(self):
        entry = getattr(transaction, "_private_prepared_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            canonical_before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if target.existed
                    else None
                )
                for target in plan.targets
            }
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            workspace_path = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            timestamps = iter(
                (
                    "2030-01-02T03:04:05Z",
                    "2030-01-02T03:04:06Z",
                    "2030-01-02T03:04:07Z",
                )
            )
            persisted = []
            real_persist = transaction.transaction_storage.persist_serialized_journal

            def tracked_persist(
                workspace,
                journal_bytes,
                *,
                expected_previous_sha256,
            ):
                persisted.append((bytes(journal_bytes), expected_previous_sha256))
                return real_persist(
                    workspace,
                    journal_bytes,
                    expected_previous_sha256=expected_previous_sha256,
                )

            with mock.patch.object(
                transaction.transaction_storage,
                "persist_serialized_journal",
                side_effect=tracked_persist,
            ):
                with entry(
                    plan,
                    journal_clock=lambda: next(timestamps),
                    lock_clock="2030-01-02T03:04:05Z",
                    lock_pid=123,
                    lock_token_factory=lambda: "1" * 32,
                ) as state:
                    self.assertTrue(lock_path.is_file())
                    journals = [
                        json.loads(journal_bytes)
                        for journal_bytes, _expected in persisted
                    ]
                    self.assertEqual(
                        [journal["phase"] for journal in journals],
                        ["planned", "staged", "prepared"],
                    )
                    self.assertTrue(
                        all(
                            journal_bytes.endswith(b"\n")
                            and not journal_bytes.endswith(b"\n\n")
                            for journal_bytes, _expected in persisted
                        )
                    )
                    self.assertEqual(
                        [expected for _journal, expected in persisted],
                        [
                            "absent",
                            hashlib.sha256(persisted[0][0]).hexdigest(),
                            hashlib.sha256(persisted[1][0]).hexdigest(),
                        ],
                    )
                    self.assertEqual(
                        [journal["recovery_manifest_sha256"] for journal in journals],
                        ["absent", "absent", state.recovery_manifest.sha256],
                    )
                    self.assertEqual(
                        [journal["created_at"] for journal in journals],
                        ["2030-01-02T03:04:05Z"] * 3,
                    )
                    self.assertEqual(
                        [journal["updated_at"] for journal in journals],
                        [
                            "2030-01-02T03:04:05Z",
                            "2030-01-02T03:04:06Z",
                            "2030-01-02T03:04:07Z",
                        ],
                    )
                    self.assertEqual(
                        [
                            target["relative_path"]
                            for target in journals[-1]["targets"]
                        ],
                        [target.relative_path for target in plan.targets],
                    )
                    journal_bytes = (workspace_path / "journal.json").read_bytes()
                    self.assertEqual(journal_bytes, persisted[-1][0])
                    self.assertEqual(json.loads(journal_bytes)["phase"], "prepared")
                    self.assertEqual(
                        state.journal_sha256,
                        hashlib.sha256(journal_bytes).hexdigest(),
                    )
                    self.assertFalse((workspace_path / "journal.next").exists())
                    rendered = repr(state)
                    self.assertNotIn(str(root), rendered)
                    self.assertNotIn("_before_bytes", rendered)
                    self.assertNotIn("_after_bytes", rendered)

            self.assertFalse(lock_path.exists())
            self.assertTrue(workspace_path.is_dir())
            self.assertTrue((workspace_path / "preimages").is_dir())
            self.assertTrue((workspace_path / "recovery-manifest.json").is_file())
            self.assertTrue((workspace_path / "journal.json").is_file())
            for proposal in state.staged_proposals:
                if proposal.state == "staged":
                    self.assertTrue((root / proposal.relative_name).is_file())
            self.assertEqual(
                {
                    relative: (
                        (root / relative).read_bytes()
                        if (root / relative).exists()
                        else None
                    )
                    for relative in canonical_before
                },
                canonical_before,
            )

    def test_private_applied_workspace_finalizes_evidence_and_complete_journal_under_same_lock(self):
        entry = getattr(transaction, "_private_applied_workspace", None)
        completed_type = getattr(transaction, "_PrivateCompletedState", None)
        self.assertIsNotNone(entry)
        self.assertIsNotNone(completed_type)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, issue_index=True)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            completion = self.completion_input(plan)
            n = sum(
                target.changed and target.role != "evidence"
                for target in plan.targets
            )
            timestamp_values = tuple(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(5, 5 + 11 + 2 * n)
            )
            binding = transaction._bind_success_evidence(
                plan,
                completion,
                timestamp_values,
            )
            evidence_path = root / binding.plan.targets[-1].relative_path
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            persisted = []
            events = []
            real_persist = transaction.transaction_storage.persist_serialized_journal
            real_apply = transaction.transaction_storage.apply_staged_target
            real_finalize = transaction.transaction_storage.finalize_staged_evidence
            real_classify = transaction.transaction_storage.classify_canonical_target
            real_evidence_classify = (
                transaction.transaction_storage.classify_finalized_evidence
            )

            def tracked_persist(
                workspace,
                journal_bytes,
                *,
                expected_previous_sha256,
            ):
                self.assertTrue(lock_path.is_file())
                journal = json.loads(journal_bytes)
                persisted.append((journal, expected_previous_sha256, bytes(journal_bytes)))
                events.append(("journal", journal["phase"]))
                return real_persist(
                    workspace,
                    journal_bytes,
                    expected_previous_sha256=expected_previous_sha256,
                )

            def tracked_apply(workspace, target, proposal):
                self.assertTrue(lock_path.is_file())
                self.assertNotEqual(target.role, "evidence")
                events.append(("apply", target.index))
                return real_apply(workspace, target, proposal)

            def tracked_validate(*args, **kwargs):
                self.assertTrue(lock_path.is_file())
                self.assertFalse(evidence_path.exists())
                events.append(("validate", None))
                return self.validation_result()

            def tracked_finalize(workspace, target, proposal):
                self.assertTrue(lock_path.is_file())
                self.assertEqual(target.role, "evidence")
                self.assertFalse(evidence_path.exists())
                self.assertEqual(events[-1], ("journal", "finalizing"))
                events.append(("finalize", target.index))
                return real_finalize(workspace, target, proposal)

            def tracked_classify(workspace, target):
                self.assertTrue(lock_path.is_file())
                events.append(("classify", target.index))
                return real_classify(workspace, target)

            def tracked_evidence_classify(workspace, target):
                self.assertTrue(lock_path.is_file())
                events.append(("classify-evidence", target.index))
                return real_evidence_classify(workspace, target)

            with (
                mock.patch.object(
                    transaction.transaction_storage,
                    "persist_serialized_journal",
                    side_effect=tracked_persist,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "apply_staged_target",
                    side_effect=tracked_apply,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "finalize_staged_evidence",
                    side_effect=tracked_finalize,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "classify_canonical_target",
                    side_effect=tracked_classify,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "classify_finalized_evidence",
                    side_effect=tracked_evidence_classify,
                ),
                mock.patch.object(
                    transaction.validate_project_artifacts,
                    "validate_project",
                    side_effect=tracked_validate,
                ),
            ):
                timestamps = iter(timestamp_values)
                with entry(
                    plan,
                    completion_input=completion,
                    journal_clock=lambda: next(timestamps),
                    lock_clock="2030-01-02T03:04:05Z",
                    lock_pid=123,
                    lock_token_factory=lambda: "1" * 32,
                ) as state:
                    self.assertTrue(lock_path.is_file())
                    self.assertIsInstance(state, completed_type)
                    self.assertEqual(
                        state.applied_target_indexes,
                        tuple(
                            target.apply_order
                            for target in binding.plan.targets
                            if target.changed
                        ),
                    )
                    self.assertEqual(
                        state.verified_target_count,
                        len(binding.plan.targets),
                    )
                    self.assertEqual(
                        state.completed_at,
                        timestamp_values[7 + n],
                    )
                    self.assertEqual(
                        evidence_path.read_bytes(),
                        binding.evidence_bytes,
                    )
                    self.assertEqual(
                        binding.evidence_bytes,
                        transaction.render_transaction_evidence(
                            transaction._json_value(
                                state.transaction_result
                            )
                        ),
                    )
                self.assertFalse(lock_path.exists())

            phases = [journal["phase"] for journal, _previous, _raw in persisted]
            self.assertEqual(
                phases,
                ["planned", "staged", "prepared", "applying"]
                + ["applying"] * n
                + ["post-validating", "finalizing", "finalizing", "complete"],
            )
            expected_previous = ["absent"] + [
                hashlib.sha256(raw).hexdigest()
                for _journal, _previous, raw in persisted[:-1]
            ]
            self.assertEqual(
                [previous for _journal, previous, _raw in persisted],
                expected_previous,
            )
            final_journal = persisted[-1][0]
            self.assertEqual(
                final_journal["applied_target_indexes"],
                [
                    target.apply_order
                    for target in binding.plan.targets
                    if target.changed
                ],
            )
            self.assertEqual(final_journal["rollback_target_indexes"], [])
            self.assertLess(
                events.index(("validate", None)),
                events.index(("journal", "finalizing")),
            )
            self.assertLess(
                events.index(("journal", "finalizing")),
                events.index(
                    ("finalize", binding.plan.targets[-1].apply_order)
                ),
            )

    def test_private_applied_workspace_rolls_back_finalization_failures_with_evidence_first(self):
        failures = (
            "first-finalizing",
            "evidence-before-mutation",
            "evidence-after-mutation",
            "evidence-progress",
            "complete-proof",
            "complete-journal",
        )
        for failure in failures:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root, issue_index=True)
                (root / "workspace" / "transactions").mkdir()
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(require_issue_index=True),
                    project_context=context,
                    clock="2030-01-02",
                )
                completion = self.completion_input(plan)
                n = sum(
                    target.changed and target.role != "evidence"
                    for target in plan.targets
                )
                timestamp_values = tuple(
                    f"2030-01-02T03:04:{second:02d}Z"
                    for second in range(5, 5 + 11 + 2 * n)
                )
                binding = transaction._bind_success_evidence(
                    plan,
                    completion,
                    timestamp_values,
                )
                changed_ordinary = tuple(
                    target.apply_order
                    for target in binding.plan.targets
                    if target.changed and target.role != "evidence"
                )
                changed_all = tuple(
                    target.apply_order
                    for target in binding.plan.targets
                    if target.changed
                )
                canonical_before = {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if target.existed
                        else None
                    )
                    for target in binding.plan.targets
                }
                persisted_phases = []
                rollback_order = []
                real_persist = (
                    transaction.transaction_storage.persist_serialized_journal
                )
                real_finalize = (
                    transaction.transaction_storage.finalize_staged_evidence
                )
                real_verify = transaction._verify_complete_after_state
                real_ordinary_rollback = (
                    transaction.transaction_storage.rollback_canonical_target
                )
                real_evidence_rollback = (
                    transaction.transaction_storage.rollback_finalized_evidence
                )

                def failing_persist(
                    workspace,
                    journal_bytes,
                    *,
                    expected_previous_sha256,
                ):
                    journal = json.loads(journal_bytes)
                    phase = journal["phase"]
                    applied = tuple(journal["applied_target_indexes"])
                    if (
                        failure == "first-finalizing"
                        and phase == "finalizing"
                        and applied == changed_ordinary
                    ):
                        raise transaction.LifecycleJournalError(
                            "JOURNAL_RECORD_INVALID"
                        )
                    if (
                        failure == "evidence-progress"
                        and phase == "finalizing"
                        and applied == changed_all
                    ):
                        raise transaction.LifecycleJournalError(
                            "JOURNAL_RECORD_INVALID"
                        )
                    if failure == "complete-journal" and phase == "complete":
                        raise transaction.LifecycleJournalError(
                            "JOURNAL_RECORD_INVALID"
                        )
                    persisted_phases.append(phase)
                    return real_persist(
                        workspace,
                        journal_bytes,
                        expected_previous_sha256=expected_previous_sha256,
                    )

                def failing_finalize(workspace, target, proposal):
                    if failure == "evidence-before-mutation":
                        raise transaction.transaction_storage.LifecycleStorageError(
                            "STORAGE_REPLACE_FAILED"
                        )
                    result = real_finalize(workspace, target, proposal)
                    if failure == "evidence-after-mutation":
                        raise transaction.transaction_storage.LifecycleStorageError(
                            "STORAGE_REPLACE_FAILED"
                        )
                    return result

                def failing_verify(state):
                    if failure == "complete-proof":
                        raise transaction.LifecycleFinalizationError(
                            "FINALIZATION_TARGET_MISMATCH"
                        )
                    return real_verify(state)

                def tracked_ordinary_rollback(workspace, target, preimage):
                    rollback_order.append(("ordinary", target.index))
                    return real_ordinary_rollback(workspace, target, preimage)

                def tracked_evidence_rollback(workspace, target, preimage):
                    rollback_order.append(("evidence", target.index))
                    return real_evidence_rollback(workspace, target, preimage)

                with (
                    mock.patch.object(
                        transaction.transaction_storage,
                        "persist_serialized_journal",
                        side_effect=failing_persist,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "finalize_staged_evidence",
                        side_effect=failing_finalize,
                    ),
                    mock.patch.object(
                        transaction,
                        "_verify_complete_after_state",
                        side_effect=failing_verify,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "rollback_canonical_target",
                        side_effect=tracked_ordinary_rollback,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "rollback_finalized_evidence",
                        side_effect=tracked_evidence_rollback,
                    ),
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                        return_value=self.validation_result(),
                    ) as validate_project,
                ):
                    timestamps = iter(timestamp_values)
                    with self.assertRaises(
                        transaction.LifecycleApplyRolledBack
                    ) as raised:
                        with transaction._private_applied_workspace(
                            plan,
                            completion_input=completion,
                            journal_clock=lambda: next(timestamps),
                            lock_clock="2030-01-02T03:04:05Z",
                            lock_pid=123,
                            lock_token_factory=lambda: "1" * 32,
                        ):
                            self.fail("failed finalization must not yield")

                validate_project.assert_called_once()
                signal = raised.exception
                self.assertEqual(signal.code, "TRANSACTION_ROLLED_BACK")
                self.assertIsNotNone(signal.post_apply_validation)
                self.assertEqual(
                    dict(signal.post_apply_validation),
                    dict(transaction._successful_post_apply_summary()),
                )
                self.assertEqual(persisted_phases[-1], "rolled-back")
                evidence_reached_after = failure in {
                    "evidence-after-mutation",
                    "evidence-progress",
                    "complete-proof",
                    "complete-journal",
                }
                if evidence_reached_after:
                    self.assertEqual(signal.applied_target_indexes, changed_all)
                    self.assertEqual(
                        rollback_order[0],
                        ("evidence", changed_all[-1]),
                    )
                else:
                    self.assertEqual(
                        signal.applied_target_indexes,
                        changed_ordinary,
                    )
                    self.assertFalse(
                        any(role == "evidence" for role, _index in rollback_order)
                    )
                self.assertEqual(
                    signal.rollback_target_indexes,
                    tuple(reversed(signal.applied_target_indexes)),
                )
                for target in binding.plan.targets:
                    canonical = root / target.relative_path
                    self.assertEqual(
                        canonical.read_bytes() if canonical.exists() else None,
                        canonical_before[target.relative_path],
                    )
                rendered = f"{signal!s} {signal!r}"
                self.assertNotIn(str(root), rendered)

    def test_private_applied_workspace_requires_recovery_for_unproven_final_evidence(self):
        for failure in ("after-finalize", "during-evidence-rollback"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root, issue_index=True)
                (root / "workspace" / "transactions").mkdir()
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(require_issue_index=True),
                    project_context=context,
                    clock="2030-01-02",
                )
                completion = self.completion_input(plan)
                n = sum(
                    target.changed and target.role != "evidence"
                    for target in plan.targets
                )
                timestamps = iter(
                    f"2030-01-02T03:04:{second:02d}Z"
                    for second in range(5, 5 + 11 + 2 * n)
                )
                evidence_path = root / plan.targets[-1].relative_path
                workspace_path = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                )
                foreign = f"PRIVATE FOREIGN {failure}\n".encode()
                phases = []
                real_finalize = (
                    transaction.transaction_storage.finalize_staged_evidence
                )
                real_persist = (
                    transaction.transaction_storage.persist_serialized_journal
                )

                def mutating_finalize(workspace, target, proposal):
                    result = real_finalize(workspace, target, proposal)
                    if failure == "after-finalize":
                        evidence_path.write_bytes(foreign)
                    return result

                def failing_persist(
                    workspace,
                    journal_bytes,
                    *,
                    expected_previous_sha256,
                ):
                    journal = json.loads(journal_bytes)
                    if (
                        failure == "during-evidence-rollback"
                        and journal["phase"] == "complete"
                    ):
                        raise transaction.LifecycleJournalError(
                            "JOURNAL_RECORD_INVALID"
                        )
                    phases.append(journal["phase"])
                    return real_persist(
                        workspace,
                        journal_bytes,
                        expected_previous_sha256=expected_previous_sha256,
                    )

                def corrupting_rollback(workspace, target, preimage):
                    evidence_path.write_bytes(foreign)
                    raise transaction.transaction_storage.LifecycleStorageError(
                        "STORAGE_CANONICAL_STATE_UNKNOWN"
                    )

                rollback_patch = (
                    corrupting_rollback
                    if failure == "during-evidence-rollback"
                    else transaction.transaction_storage.rollback_finalized_evidence
                )
                with (
                    mock.patch.object(
                        transaction.transaction_storage,
                        "finalize_staged_evidence",
                        side_effect=mutating_finalize,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "persist_serialized_journal",
                        side_effect=failing_persist,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "rollback_finalized_evidence",
                        side_effect=rollback_patch,
                    ),
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                        return_value=self.validation_result(),
                    ),
                ):
                    with self.assertRaises(
                        transaction.LifecycleRecoveryRequired
                    ) as raised:
                        with transaction._private_applied_workspace(
                            plan,
                            completion_input=completion,
                            journal_clock=lambda: next(timestamps),
                            lock_clock="2030-01-02T03:04:05Z",
                            lock_pid=123,
                            lock_token_factory=lambda: "1" * 32,
                        ):
                            self.fail("foreign evidence must not yield")

                self.assertEqual(
                    raised.exception.code,
                    "TRANSACTION_RECOVERY_REQUIRED",
                )
                self.assertEqual(evidence_path.read_bytes(), foreign)
                self.assertNotIn("complete", phases)
                self.assertNotIn("rolled-back", phases)
                self.assertEqual(phases[-1], "recovery-required")
                self.assertTrue((workspace_path / "preimages").is_dir())
                self.assertTrue(
                    (workspace_path / "recovery-manifest.json").is_file()
                )
                self.assertTrue((workspace_path / "journal.json").is_file())

    def test_private_applied_workspace_does_not_claim_complete_when_target_changes_during_final_proof(self):
        for target_class in ("changed", "unchanged", "evidence"):
            with self.subTest(target_class=target_class), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root, issue_index=True)
                (root / "workspace" / "transactions").mkdir()
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(require_issue_index=True),
                    project_context=context,
                    clock="2030-01-02",
                )
                targets = []
                for target in plan.targets:
                    if target.role == "dashboard":
                        target = replace(
                            target,
                            after_sha256=target.before_sha256,
                            after_size=len(target._before_bytes),
                            changed=False,
                            _after_bytes=target._before_bytes,
                        )
                    targets.append(target)
                plan = replace(plan, targets=tuple(targets))
                completion = self.completion_input(plan)
                n = sum(
                    target.changed and target.role != "evidence"
                    for target in plan.targets
                )
                timestamp_values = tuple(
                    f"2030-01-02T03:04:{second:02d}Z"
                    for second in range(5, 5 + 11 + 2 * n)
                )
                binding = transaction._bind_success_evidence(
                    plan,
                    completion,
                    timestamp_values,
                )
                selected = {
                    "changed": next(
                        target
                        for target in binding.plan.targets
                        if target.changed and target.role != "evidence"
                    ),
                    "unchanged": next(
                        target for target in binding.plan.targets if not target.changed
                    ),
                    "evidence": binding.plan.targets[-1],
                }[target_class]
                canonical_before = {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if target.existed
                        else None
                    )
                    for target in binding.plan.targets
                }
                phases = []
                real_verify = transaction._verify_complete_after_state
                real_persist = (
                    transaction.transaction_storage.persist_serialized_journal
                )

                def mutate_then_verify(state):
                    canonical = root / selected.relative_path
                    if target_class == "unchanged":
                        canonical.write_bytes(b"PRIVATE FOREIGN UNCHANGED")
                    elif selected.existed:
                        canonical.write_bytes(selected._before_bytes)
                    elif canonical.exists():
                        canonical.unlink()
                    return real_verify(state)

                def tracked_persist(
                    workspace,
                    journal_bytes,
                    *,
                    expected_previous_sha256,
                ):
                    journal = json.loads(journal_bytes)
                    phases.append(journal["phase"])
                    return real_persist(
                        workspace,
                        journal_bytes,
                        expected_previous_sha256=expected_previous_sha256,
                    )

                expected_error = (
                    transaction.LifecycleRecoveryRequired
                    if target_class == "unchanged"
                    else transaction.LifecycleApplyRolledBack
                )
                with (
                    mock.patch.object(
                        transaction,
                        "_verify_complete_after_state",
                        side_effect=mutate_then_verify,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "persist_serialized_journal",
                        side_effect=tracked_persist,
                    ),
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                        return_value=self.validation_result(),
                    ),
                ):
                    timestamps = iter(timestamp_values)
                    with self.assertRaises(expected_error):
                        with transaction._private_applied_workspace(
                            plan,
                            completion_input=completion,
                            journal_clock=lambda: next(timestamps),
                            lock_clock="2030-01-02T03:04:05Z",
                            lock_pid=123,
                            lock_token_factory=lambda: "1" * 32,
                        ):
                            self.fail("changed final proof must not yield")

                self.assertNotIn("complete", phases)
                if target_class == "unchanged":
                    self.assertEqual(
                        (root / selected.relative_path).read_bytes(),
                        b"PRIVATE FOREIGN UNCHANGED",
                    )
                    self.assertEqual(phases[-1], "recovery-required")
                else:
                    self.assertEqual(phases[-1], "rolled-back")
                    for target in binding.plan.targets:
                        canonical = root / target.relative_path
                        self.assertEqual(
                            canonical.read_bytes() if canonical.exists() else None,
                            canonical_before[target.relative_path],
                        )

    def test_private_applied_workspace_promotes_only_changed_ordinary_targets_and_persists_progress(self):
        entry = getattr(transaction, "_private_applied_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            detached_targets = []
            for target in plan.targets:
                if target.role == "dashboard":
                    target = replace(
                        target,
                        after_size=len(target._before_bytes),
                        after_sha256=transaction.target_sha256(
                            target._before_bytes
                        ),
                        changed=False,
                        _after_bytes=target._before_bytes,
                    )
                detached_targets.append(target)
            plan = replace(plan, targets=tuple(detached_targets))
            changed_ordinary = tuple(
                target.apply_order
                for target in plan.targets
                if target.changed and target.role != "evidence"
            )
            self.assertTrue(changed_ordinary)
            self.assertTrue(
                any(
                    target.changed
                    and not target.existed
                    and target.role != "evidence"
                    for target in plan.targets
                )
            )
            canonical_before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if target.existed
                    else None
                )
                for target in plan.targets
            }
            evidence = plan.targets[-1]
            self.assertEqual(evidence.role, "evidence")
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            workspace_path = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            timestamp_values = tuple(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(
                    5,
                    5 + 11 + 2 * len(changed_ordinary),
                )
            )
            timestamps = iter(timestamp_values)
            completion = self.completion_input(plan)
            binding = transaction._bind_success_evidence(
                plan,
                completion,
                timestamp_values,
            )
            changed_all = tuple(
                target.apply_order
                for target in binding.plan.targets
                if target.changed
            )
            persisted = []
            verified = []
            applied = []
            real_persist = transaction.transaction_storage.persist_serialized_journal
            real_verify = transaction.transaction_storage.verify_canonical_target
            real_apply = transaction.transaction_storage.apply_staged_target

            def tracked_persist(
                workspace,
                journal_bytes,
                *,
                expected_previous_sha256,
            ):
                self.assertTrue(lock_path.is_file())
                persisted.append((bytes(journal_bytes), expected_previous_sha256))
                return real_persist(
                    workspace,
                    journal_bytes,
                    expected_previous_sha256=expected_previous_sha256,
                )

            def tracked_verify(workspace, target):
                self.assertTrue(lock_path.is_file())
                verified.append(target.index)
                return real_verify(workspace, target)

            def tracked_apply(workspace, target, proposal):
                self.assertTrue(lock_path.is_file())
                applied.append(target.index)
                return real_apply(workspace, target, proposal)

            with (
                mock.patch.object(
                    transaction.transaction_storage,
                    "persist_serialized_journal",
                    side_effect=tracked_persist,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "verify_canonical_target",
                    side_effect=tracked_verify,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "apply_staged_target",
                    side_effect=tracked_apply,
                ),
                mock.patch.object(
                    transaction.validate_project_artifacts,
                    "validate_project",
                    return_value=self.validation_result(),
                ) as validate_project,
            ):
                with entry(
                    plan,
                    completion_input=completion,
                    journal_clock=lambda: next(timestamps),
                    lock_clock="2030-01-02T03:04:05Z",
                    lock_pid=123,
                    lock_token_factory=lambda: "1" * 32,
                ) as state:
                    self.assertTrue(lock_path.is_file())
                    journals = [
                        json.loads(payload)
                        for payload, _previous in persisted
                    ]
                    self.assertEqual(
                        [journal["phase"] for journal in journals],
                        ["planned", "staged", "prepared", "applying"]
                        + ["applying"] * len(changed_ordinary)
                        + [
                            "post-validating",
                            "finalizing",
                            "finalizing",
                            "complete",
                        ],
                    )
                    self.assertEqual(
                        [
                            journal["applied_target_indexes"]
                            for journal in journals[3:]
                        ],
                        [
                            [],
                            *[
                                list(changed_ordinary[:index])
                                for index in range(
                                    1,
                                    len(changed_ordinary) + 1,
                                )
                            ],
                            list(changed_ordinary),
                            list(changed_ordinary),
                            list(changed_all),
                            list(changed_all),
                        ],
                    )
                    self.assertTrue(
                        all(
                            journal["rollback_target_indexes"] == []
                            for journal in journals
                        )
                    )
                    self.assertEqual(
                        [journal["created_at"] for journal in journals],
                        [timestamp_values[0]] * len(journals),
                    )
                    self.assertEqual(
                        [journal["updated_at"] for journal in journals],
                        list(timestamp_values[:len(journals)]),
                    )
                    self.assertEqual(
                        [previous for _payload, previous in persisted],
                        ["absent"]
                        + [
                            hashlib.sha256(payload).hexdigest()
                            for payload, _previous in persisted[:-1]
                        ],
                    )
                    self.assertEqual(
                        state.applied_target_indexes,
                        changed_all,
                    )
                    self.assertIsInstance(
                        state,
                        transaction._PrivateCompletedState,
                    )
                    self.assertEqual(state.created_at, timestamp_values[0])
                    self.assertEqual(
                        state.journal_sha256,
                        hashlib.sha256(persisted[-1][0]).hexdigest(),
                    )
                    self.assertEqual(
                        verified,
                        [
                            target.apply_order
                            for target in plan.targets
                            if not target.changed and target.role != "evidence"
                        ]
                        + [
                            target.apply_order
                            for target in plan.targets
                            if not target.changed or target.role == "evidence"
                        ]
                        + [
                            target.apply_order
                            for target in plan.targets
                            if not target.changed
                        ],
                    )
                    self.assertEqual(applied, list(changed_ordinary))
                    validate_project.assert_called_once()
                    evidence_proposal = state.staged_proposals[-1]
                    self.assertEqual(evidence_proposal.state, "staged")
                    self.assertFalse(
                        (root / evidence_proposal.relative_name).exists()
                    )
                    self.assertNotIn(str(root), repr(state))

            self.assertFalse(lock_path.exists())
            self.assertTrue(workspace_path.is_dir())
            for target in binding.plan.targets:
                canonical = root / target.relative_path
                if target.role == "evidence":
                    self.assertEqual(
                        canonical.read_bytes(),
                        binding.evidence_bytes,
                    )
                elif target.changed:
                    self.assertEqual(canonical.read_bytes(), target._after_bytes)
                    self.assertEqual(stat.S_IMODE(canonical.stat().st_mode), 0o600)
                else:
                    self.assertEqual(
                        canonical.read_bytes(),
                        canonical_before[target.relative_path],
                    )

    def test_private_applied_workspace_post_validates_exact_canonical_state_under_same_lock(self):
        entry = getattr(transaction, "_private_applied_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            targets = []
            for target in plan.targets:
                if target.role == "dashboard":
                    target = replace(
                        target,
                        after_size=len(target._before_bytes),
                        after_sha256=transaction.target_sha256(
                            target._before_bytes
                        ),
                        changed=False,
                        _after_bytes=target._before_bytes,
                    )
                targets.append(target)
            plan = replace(plan, targets=tuple(targets))
            changed_ordinary = tuple(
                target.apply_order
                for target in plan.targets
                if target.changed and target.role != "evidence"
            )
            unchanged_or_evidence = tuple(
                target.apply_order
                for target in plan.targets
                if not target.changed or target.role == "evidence"
            )
            evidence = plan.targets[-1]
            evidence_before = (
                (root / evidence.relative_path).read_bytes()
                if (root / evidence.relative_path).exists()
                else None
            )
            lock_path = (
                root / ".moduflow" / "transactions" / "lifecycle.lock"
            )
            timestamps = iter(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(
                    5,
                    5 + 11 + 2 * len(changed_ordinary),
                )
            )
            completion = self.completion_input(plan)
            post_phase = False
            classified = []
            verified = []
            validator_calls = []
            real_apply_prepared = transaction._apply_prepared_targets
            real_classify = (
                transaction.transaction_storage.classify_canonical_target
            )
            real_verify = (
                transaction.transaction_storage.verify_canonical_target
            )

            def tracked_apply_prepared(*args, **kwargs):
                nonlocal post_phase
                state = real_apply_prepared(*args, **kwargs)
                post_phase = True
                return state

            def tracked_classify(workspace, target):
                self.assertTrue(lock_path.is_file())
                if post_phase:
                    classified.append(target.index)
                return real_classify(workspace, target)

            def tracked_verify(workspace, target):
                self.assertTrue(lock_path.is_file())
                if post_phase:
                    verified.append(target.index)
                return real_verify(workspace, target)

            def tracked_validator(canonical_root, *, project_context):
                self.assertTrue(lock_path.is_file())
                validator_calls.append((canonical_root, project_context))
                self.assertEqual(canonical_root, root.resolve())
                self.assertEqual(
                    Path(project_context["canonical_root"]),
                    root.resolve(),
                )
                for path in project_context["paths"].values():
                    Path(path).relative_to(root.resolve())
                return self.validation_result()

            with (
                mock.patch.object(
                    transaction,
                    "_apply_prepared_targets",
                    side_effect=tracked_apply_prepared,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "classify_canonical_target",
                    side_effect=tracked_classify,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "verify_canonical_target",
                    side_effect=tracked_verify,
                ),
                mock.patch.object(
                    transaction.validate_project_artifacts,
                    "validate_project",
                    side_effect=tracked_validator,
                ),
            ):
                with entry(
                    plan,
                    completion_input=completion,
                    journal_clock=lambda: next(timestamps),
                    lock_clock="2030-01-02T03:04:05Z",
                    lock_pid=123,
                    lock_token_factory=lambda: "1" * 32,
                ) as state:
                    self.assertIsInstance(
                        state,
                        transaction._PrivateCompletedState,
                    )
                    self.assertEqual(
                        state.applied_target_indexes,
                        changed_ordinary + (evidence.apply_order,),
                    )
                    self.assertEqual(
                        state.verified_target_count,
                        len(plan.targets),
                    )
                    self.assertEqual(
                        dict(state.post_apply_validation),
                        {
                            "valid": True,
                            "rule_ids": (
                                "canonical-targets",
                                "project-artifacts",
                                "issue-schema",
                                "lifecycle-consensus",
                                "production-records",
                            ),
                            "error_codes": (),
                        },
                    )
                    self.assertEqual(
                        classified,
                        list(changed_ordinary) + list(changed_ordinary),
                    )
                    self.assertEqual(
                        verified,
                        list(unchanged_or_evidence)
                        + [
                            target.apply_order
                            for target in plan.targets
                            if not target.changed
                        ],
                    )
                    self.assertEqual(len(validator_calls), 1)
                    journal = json.loads(
                        (
                            root
                            / ".moduflow"
                            / "transactions"
                            / plan.transaction_id
                            / "journal.json"
                        ).read_bytes()
                    )
                    self.assertEqual(journal["phase"], "complete")
                    evidence_proposal = state.staged_proposals[-1]
                    self.assertEqual(evidence_proposal.state, "staged")
                    self.assertFalse(
                        (root / evidence_proposal.relative_name).exists()
                    )
                    self.assertEqual(
                        (root / evidence.relative_path).read_bytes(),
                        state.transaction_result
                        and transaction.render_transaction_evidence(
                            transaction._json_value(state.transaction_result)
                        ),
                    )

    def test_private_applied_workspace_rolls_back_invalid_post_apply_validation_under_same_lock(self):
        cases = (
            (
                "project-invalid",
                self.validation_result(
                    valid=False,
                    errors=["PRIVATE ERROR"],
                ),
                ("POST_APPLY_PROJECT_INVALID",),
            ),
            (
                "issue-invalid",
                self.validation_result(valid=False, issue_errors=1),
                ("POST_APPLY_ISSUE_SCHEMA_INVALID",),
            ),
            (
                "lifecycle-drift",
                self.validation_result(
                    valid=False,
                    lifecycle_drift=["PRIVATE"],
                ),
                ("POST_APPLY_LIFECYCLE_DRIFT",),
            ),
            (
                "malformed-contract",
                {"schema": "PRIVATE"},
                ("POST_APPLY_VALIDATION_CONTRACT_INVALID",),
            ),
        )
        for name, result, expected_codes in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root)
                (root / "workspace" / "transactions").mkdir()
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(require_issue_index=True),
                    project_context=context,
                    clock="2030-01-02",
                )
                changed_ordinary = tuple(
                    target.apply_order
                    for target in plan.targets
                    if target.changed and target.role != "evidence"
                )
                canonical_before = {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if target.existed
                        else None
                    )
                    for target in plan.targets
                }
                lock_path = (
                    root / ".moduflow" / "transactions" / "lifecycle.lock"
                )
                timestamps = iter(
                    f"2030-01-02T03:04:{second:02d}Z"
                    for second in range(
                        5,
                        5 + 11 + 2 * len(changed_ordinary),
                    )
                )
                rollback_calls = []
                real_rollback = (
                    transaction.transaction_storage.rollback_canonical_target
                )

                def tracked_validator(canonical_root, *, project_context):
                    self.assertTrue(lock_path.is_file())
                    self.assertEqual(canonical_root, root.resolve())
                    return result

                def tracked_rollback(workspace, target, preimage):
                    self.assertTrue(lock_path.is_file())
                    rollback_calls.append(target.index)
                    return real_rollback(workspace, target, preimage)

                with (
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                        side_effect=tracked_validator,
                    ) as validate_project,
                    mock.patch.object(
                        transaction.transaction_storage,
                        "rollback_canonical_target",
                        side_effect=tracked_rollback,
                    ),
                ):
                    with self.assertRaises(
                        transaction.LifecycleApplyRolledBack
                    ) as raised:
                        with transaction._private_applied_workspace(
                            plan,
                            completion_input=self.completion_input(plan),
                            journal_clock=lambda: next(timestamps),
                            lock_clock="2030-01-02T03:04:05Z",
                            lock_pid=123,
                            lock_token_factory=lambda: "1" * 32,
                        ):
                            self.fail("invalid post-apply state must not yield")

                signal = raised.exception
                self.assertEqual(
                    signal.original_error_code,
                    "POST_APPLY_VALIDATION_INVALID",
                )
                self.assertEqual(
                    signal.applied_target_indexes,
                    changed_ordinary,
                )
                self.assertEqual(
                    signal.rollback_target_indexes,
                    tuple(reversed(changed_ordinary)),
                )
                self.assertEqual(
                    rollback_calls,
                    list(reversed(changed_ordinary)),
                )
                self.assertEqual(
                    signal.post_apply_validation["error_codes"],
                    expected_codes,
                )
                validate_project.assert_called_once()
                self.assertFalse(lock_path.exists())
                for target in plan.targets:
                    canonical = root / target.relative_path
                    self.assertEqual(
                        canonical.read_bytes() if canonical.exists() else None,
                        canonical_before[target.relative_path],
                    )
                workspace_path = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                )
                self.assertEqual(
                    json.loads(
                        (workspace_path / "journal.json").read_bytes()
                    )["phase"],
                    "rolled-back",
                )
                self.assertEqual(
                    plan.targets[-1].role,
                    "evidence",
                )
                self.assertTrue(tuple(root.glob("**/.moduflow-stage-*")))

    def test_private_applied_workspace_rolls_back_exact_before_target_without_calling_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            changed_targets = tuple(
                target
                for target in plan.targets
                if target.changed and target.role != "evidence"
            )
            changed_ordinary = tuple(
                target.apply_order for target in changed_targets
            )
            restored = changed_targets[0]
            canonical_before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if target.existed
                    else None
                )
                for target in plan.targets
            }
            timestamps = iter(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(
                    5,
                    5 + 11 + 2 * len(changed_ordinary),
                )
            )
            real_apply_prepared = transaction._apply_prepared_targets

            def restore_before_after_apply(*args, **kwargs):
                state = real_apply_prepared(*args, **kwargs)
                canonical = root / restored.relative_path
                if restored.existed:
                    canonical.write_bytes(restored._before_bytes)
                else:
                    canonical.unlink()
                return state

            with (
                mock.patch.object(
                    transaction,
                    "_apply_prepared_targets",
                    side_effect=restore_before_after_apply,
                ),
                mock.patch.object(
                    transaction.validate_project_artifacts,
                    "validate_project",
                ) as validate_project,
            ):
                with self.assertRaises(
                    transaction.LifecycleApplyRolledBack
                ) as raised:
                    with transaction._private_applied_workspace(
                        plan,
                        completion_input=self.completion_input(plan),
                        journal_clock=lambda: next(timestamps),
                        lock_clock="2030-01-02T03:04:05Z",
                        lock_pid=123,
                        lock_token_factory=lambda: "1" * 32,
                    ):
                        self.fail("exact-before changed target must not yield")

            signal = raised.exception
            self.assertEqual(
                signal.original_error_code,
                "POST_APPLY_VALIDATION_INVALID",
            )
            self.assertEqual(
                signal.post_apply_validation["error_codes"],
                ("POST_APPLY_TARGET_MISMATCH",),
            )
            self.assertEqual(
                signal.rollback_target_indexes,
                tuple(reversed(changed_ordinary)),
            )
            validate_project.assert_not_called()
            for target in plan.targets:
                canonical = root / target.relative_path
                self.assertEqual(
                    canonical.read_bytes() if canonical.exists() else None,
                    canonical_before[target.relative_path],
                )

    def test_private_applied_workspace_requires_recovery_for_unproven_changed_unchanged_and_evidence_targets(self):
        for target_class in ("changed", "unchanged", "evidence"):
            with (
                self.subTest(target_class=target_class),
                tempfile.TemporaryDirectory() as tmp,
            ):
                root = Path(tmp)
                context = self.scaffold(root)
                (root / "workspace" / "transactions").mkdir()
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(require_issue_index=True),
                    project_context=context,
                    clock="2030-01-02",
                )
                targets = []
                for target in plan.targets:
                    if target.role == "dashboard":
                        target = replace(
                            target,
                            after_size=len(target._before_bytes),
                            after_sha256=transaction.target_sha256(
                                target._before_bytes
                            ),
                            changed=False,
                            _after_bytes=target._before_bytes,
                        )
                    targets.append(target)
                plan = replace(plan, targets=tuple(targets))
                selected = {
                    "changed": next(
                        target
                        for target in plan.targets
                        if target.changed and target.role != "evidence"
                    ),
                    "unchanged": next(
                        target for target in plan.targets if not target.changed
                    ),
                    "evidence": next(
                        target
                        for target in plan.targets
                        if target.role == "evidence"
                    ),
                }[target_class]
                changed_ordinary = tuple(
                    target.apply_order
                    for target in plan.targets
                    if target.changed and target.role != "evidence"
                )
                timestamps = iter(
                    f"2030-01-02T03:04:{second:02d}Z"
                    for second in range(
                        5,
                        5 + 11 + 2 * len(changed_ordinary),
                    )
                )
                lock_path = (
                    root / ".moduflow" / "transactions" / "lifecycle.lock"
                )
                workspace_path = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                )
                foreign = f"PRIVATE FOREIGN {target_class}\n".encode()
                real_apply_prepared = transaction._apply_prepared_targets

                def inject_foreign_state(*args, **kwargs):
                    state = real_apply_prepared(*args, **kwargs)
                    (root / selected.relative_path).write_bytes(foreign)
                    return state

                with (
                    mock.patch.object(
                        transaction,
                        "_apply_prepared_targets",
                        side_effect=inject_foreign_state,
                    ),
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                        return_value=self.validation_result(),
                    ) as validate_project,
                ):
                    with self.assertRaises(
                        transaction.LifecycleRecoveryRequired
                    ) as raised:
                        with transaction._private_applied_workspace(
                            plan,
                            completion_input=self.completion_input(plan),
                            journal_clock=lambda: next(timestamps),
                            lock_clock="2030-01-02T03:04:05Z",
                            lock_pid=123,
                            lock_token_factory=lambda: "1" * 32,
                        ):
                            self.fail("unproven canonical state must not yield")

                signal = raised.exception
                self.assertEqual(
                    signal.original_error_code,
                    "POST_APPLY_VALIDATION_FAILED",
                )
                self.assertIn(
                    signal.rollback_error_code,
                    {
                        "STORAGE_CANONICAL_STATE_UNKNOWN",
                        "CANONICAL_PREIMAGE_CONFLICT",
                        "STORAGE_VERIFY_FAILED",
                    },
                )
                self.assertEqual(
                    signal.post_apply_validation["error_codes"],
                    ("POST_APPLY_TARGET_UNPROVEN",),
                )
                validate_project.assert_not_called()
                self.assertEqual(
                    (root / selected.relative_path).read_bytes(),
                    foreign,
                )
                self.assertFalse(lock_path.exists())
                self.assertTrue((workspace_path / "preimages").is_dir())
                self.assertTrue(
                    (workspace_path / "recovery-manifest.json").is_file()
                )
                self.assertEqual(
                    json.loads(
                        (workspace_path / "journal.json").read_bytes()
                    )["phase"],
                    "recovery-required",
                )

    def test_private_applied_workspace_redacts_validator_runtime_failure_before_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            changed_ordinary = tuple(
                target.apply_order
                for target in plan.targets
                if target.changed and target.role != "evidence"
            )
            canonical_before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if target.existed
                    else None
                )
                for target in plan.targets
            }
            timestamps = iter(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(
                    5,
                    5 + 11 + 2 * len(changed_ordinary),
                )
            )

            def failing_validator(canonical_root, *, project_context):
                raise RuntimeError(f"PRIVATE at {canonical_root}")

            with mock.patch.object(
                transaction.validate_project_artifacts,
                "validate_project",
                side_effect=failing_validator,
            ):
                with self.assertRaises(
                    transaction.LifecycleApplyRolledBack
                ) as raised:
                    with transaction._private_applied_workspace(
                        plan,
                        completion_input=self.completion_input(plan),
                        journal_clock=lambda: next(timestamps),
                        lock_clock="2030-01-02T03:04:05Z",
                        lock_pid=123,
                        lock_token_factory=lambda: "1" * 32,
                    ):
                        self.fail("validator runtime failure must not yield")

            signal = raised.exception
            self.assertEqual(
                signal.original_error_code,
                "POST_APPLY_VALIDATION_FAILED",
            )
            self.assertEqual(
                signal.post_apply_validation["error_codes"],
                ("POST_APPLY_VALIDATION_FAILED",),
            )
            rendered = json.dumps(
                {
                    "str": str(signal),
                    "repr": repr(signal),
                    "summary": {
                        key: list(value) if isinstance(value, tuple) else value
                        for key, value in signal.post_apply_validation.items()
                    },
                }
            )
            self.assertNotIn("PRIVATE", rendered)
            self.assertNotIn(str(root), rendered)
            workspace_path = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            journal_bytes = (workspace_path / "journal.json").read_bytes()
            self.assertNotIn(b"PRIVATE", journal_bytes)
            self.assertNotIn(str(root).encode(), journal_bytes)
            for target in plan.targets:
                canonical = root / target.relative_path
                self.assertEqual(
                    canonical.read_bytes() if canonical.exists() else None,
                    canonical_before[target.relative_path],
                )

    def test_private_applied_workspace_does_not_claim_rolled_back_when_unchanged_or_evidence_changes_during_rollback(self):
        for target_class in ("unchanged", "evidence"):
            with (
                self.subTest(target_class=target_class),
                tempfile.TemporaryDirectory() as tmp,
            ):
                root = Path(tmp)
                context = self.scaffold(root)
                (root / "workspace" / "transactions").mkdir()
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(require_issue_index=True),
                    project_context=context,
                    clock="2030-01-02",
                )
                targets = []
                for target in plan.targets:
                    if target.role == "dashboard":
                        target = replace(
                            target,
                            after_size=len(target._before_bytes),
                            after_sha256=transaction.target_sha256(
                                target._before_bytes
                            ),
                            changed=False,
                            _after_bytes=target._before_bytes,
                        )
                    targets.append(target)
                plan = replace(plan, targets=tuple(targets))
                selected = {
                    "unchanged": next(
                        target for target in plan.targets if not target.changed
                    ),
                    "evidence": next(
                        target
                        for target in plan.targets
                        if target.role == "evidence"
                    ),
                }[target_class]
                changed_ordinary = tuple(
                    target.apply_order
                    for target in plan.targets
                    if target.changed and target.role != "evidence"
                )
                timestamps = iter(
                    f"2030-01-02T03:04:{second:02d}Z"
                    for second in range(
                        5,
                        5 + 11 + 2 * len(changed_ordinary),
                    )
                )
                lock_path = (
                    root / ".moduflow" / "transactions" / "lifecycle.lock"
                )
                workspace_path = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / plan.transaction_id
                )
                foreign = f"PRIVATE RACE {target_class}\n".encode()
                persisted_phases = []
                real_verify_complete = transaction._verify_complete_rollback
                real_persist = (
                    transaction.transaction_storage.persist_serialized_journal
                )

                def mutate_before_final_proof(prepared):
                    self.assertTrue(lock_path.is_file())
                    (root / selected.relative_path).write_bytes(foreign)
                    return real_verify_complete(prepared)

                def tracked_persist(
                    workspace,
                    journal_bytes,
                    *,
                    expected_previous_sha256,
                ):
                    persisted_phases.append(
                        json.loads(journal_bytes)["phase"]
                    )
                    return real_persist(
                        workspace,
                        journal_bytes,
                        expected_previous_sha256=expected_previous_sha256,
                    )

                with (
                    mock.patch.object(
                        transaction,
                        "_verify_complete_rollback",
                        side_effect=mutate_before_final_proof,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "persist_serialized_journal",
                        side_effect=tracked_persist,
                    ),
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                        return_value=self.validation_result(
                            valid=False,
                            errors=["PRIVATE INVALID"],
                        ),
                    ),
                ):
                    with self.assertRaises(
                        transaction.LifecycleRecoveryRequired
                    ) as raised:
                        with transaction._private_applied_workspace(
                            plan,
                            completion_input=self.completion_input(plan),
                            journal_clock=lambda: next(timestamps),
                            lock_clock="2030-01-02T03:04:05Z",
                            lock_pid=123,
                            lock_token_factory=lambda: "1" * 32,
                        ):
                            self.fail("raced rollback proof must not yield")

                signal = raised.exception
                self.assertEqual(
                    signal.original_error_code,
                    "POST_APPLY_VALIDATION_INVALID",
                )
                self.assertEqual(
                    signal.rollback_error_code,
                    (
                        "STORAGE_CANONICAL_STATE_UNKNOWN"
                        if target_class == "evidence"
                        else "CANONICAL_PREIMAGE_CONFLICT"
                    ),
                )
                self.assertEqual(
                    signal.post_apply_validation["error_codes"],
                    ("POST_APPLY_PROJECT_INVALID",),
                )
                self.assertNotIn("rolled-back", persisted_phases)
                self.assertEqual(
                    persisted_phases.count("recovery-required"),
                    1,
                )
                self.assertEqual(
                    (root / selected.relative_path).read_bytes(),
                    foreign,
                )
                self.assertTrue((workspace_path / "preimages").is_dir())
                self.assertTrue(
                    (workspace_path / "recovery-manifest.json").is_file()
                )
                self.assertFalse(lock_path.exists())
                rendered = repr(signal) + str(signal)
                self.assertNotIn("PRIVATE", rendered)
                self.assertNotIn(str(root), rendered)

    def test_private_applied_workspace_prevalidates_all_forward_and_rollback_timestamps_before_lock(self):
        entry = getattr(transaction, "_private_applied_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            changed_ordinary = tuple(
                target.apply_order
                for target in plan.targets
                if target.changed and target.role != "evidence"
            )
            required = 11 + 2 * len(changed_ordinary)
            canonical_before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if target.existed
                    else None
                )
                for target in plan.targets
            }
            workspace_path = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )

            for bad_index in range(required):
                with self.subTest(bad_index=bad_index):
                    values = ["2030-01-02T03:04:05Z"] * required
                    values[bad_index] = "NOT-A-TIMESTAMP"
                    timestamps = iter(values)
                    with (
                        mock.patch.object(
                            transaction,
                            "_exclusive_lifecycle_lock",
                        ) as acquire_lock,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "verify_canonical_preimages",
                        ) as verify_preimages,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "private_transaction_workspace",
                        ) as open_workspace,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "persist_serialized_journal",
                        ) as persist_journal,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "store_preimages",
                        ) as store_preimages,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "stage_proposed_targets",
                        ) as stage_targets,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "finalize_recovery_manifest",
                        ) as finalize_manifest,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "verify_canonical_target",
                        ) as verify_target,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "apply_staged_target",
                        ) as apply_target,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "classify_canonical_target",
                        ) as classify_target,
                        mock.patch.multiple(
                            transaction.transaction_storage,
                            finalize_staged_evidence=mock.DEFAULT,
                            classify_finalized_evidence=mock.DEFAULT,
                            rollback_finalized_evidence=mock.DEFAULT,
                        ) as evidence_operations,
                        mock.patch.object(
                            transaction.transaction_storage,
                            "rollback_canonical_target",
                        ) as rollback_target,
                        mock.patch.object(transaction.os, "replace") as replace_file,
                        mock.patch.object(transaction.os, "unlink") as unlink_file,
                        mock.patch.object(transaction.os, "fsync") as sync_file,
                    ):
                        with self.assertRaises(
                            transaction.LifecycleJournalError
                        ) as raised:
                            with entry(
                                plan,
                                completion_input=self.completion_input(plan),
                                journal_clock=lambda: next(timestamps),
                            ):
                                self.fail("invalid timestamp must not yield")
                    self.assertEqual(
                        raised.exception.code,
                        "JOURNAL_RECORD_INVALID",
                    )
                    for operation in (
                        acquire_lock,
                        verify_preimages,
                        open_workspace,
                        persist_journal,
                        store_preimages,
                        stage_targets,
                        finalize_manifest,
                        verify_target,
                        apply_target,
                        classify_target,
                        rollback_target,
                        *evidence_operations.values(),
                        replace_file,
                        unlink_file,
                        sync_file,
                    ):
                        operation.assert_not_called()
                    self.assertFalse(workspace_path.exists())
                    self.assertEqual(
                        {
                            target.relative_path: (
                                (root / target.relative_path).read_bytes()
                                if (root / target.relative_path).exists()
                                else None
                            )
                            for target in plan.targets
                        },
                        canonical_before,
                    )

    def test_private_applied_workspace_rolls_back_attempted_prefix_in_reverse_under_same_lock(self):
        entry = getattr(transaction, "_private_applied_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            changed_ordinary = tuple(
                target.apply_order
                for target in plan.targets
                if target.changed and target.role != "evidence"
            )
            self.assertGreaterEqual(len(changed_ordinary), 3)
            canonical_before = {
                target.relative_path: (
                    (root / target.relative_path).read_bytes()
                    if target.existed
                    else None
                )
                for target in plan.targets
            }
            evidence = plan.targets[-1]
            self.assertEqual(evidence.role, "evidence")
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            workspace_path = (
                root / ".moduflow" / "transactions" / plan.transaction_id
            )
            timestamp_values = tuple(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(5, 5 + 11 + 2 * len(changed_ordinary))
            )
            timestamps = iter(timestamp_values)
            persisted = []
            rollback_calls = []
            apply_calls = 0
            real_apply = transaction.transaction_storage.apply_staged_target
            real_classify = (
                transaction.transaction_storage.classify_canonical_target
            )
            real_rollback = (
                transaction.transaction_storage.rollback_canonical_target
            )
            real_persist = (
                transaction.transaction_storage.persist_serialized_journal
            )

            def failing_apply(workspace, target, proposal):
                nonlocal apply_calls
                apply_calls += 1
                result = real_apply(workspace, target, proposal)
                if apply_calls == 3:
                    raise transaction.transaction_storage.LifecycleStorageError(
                        "STORAGE_REPLACE_FAILED"
                    )
                return result

            def tracked_classify(workspace, target):
                self.assertTrue(lock_path.is_file())
                return real_classify(workspace, target)

            def tracked_rollback(workspace, target, preimage):
                self.assertTrue(lock_path.is_file())
                rollback_calls.append(target.index)
                return real_rollback(workspace, target, preimage)

            def tracked_persist(
                workspace,
                journal_bytes,
                *,
                expected_previous_sha256,
            ):
                self.assertTrue(lock_path.is_file())
                persisted.append((bytes(journal_bytes), expected_previous_sha256))
                return real_persist(
                    workspace,
                    journal_bytes,
                    expected_previous_sha256=expected_previous_sha256,
                )

            with (
                mock.patch.object(
                    transaction.transaction_storage,
                    "apply_staged_target",
                    side_effect=failing_apply,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "classify_canonical_target",
                    side_effect=tracked_classify,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "rollback_canonical_target",
                    side_effect=tracked_rollback,
                ),
                mock.patch.object(
                    transaction.transaction_storage,
                    "persist_serialized_journal",
                    side_effect=tracked_persist,
                ),
                mock.patch.object(
                    transaction.validate_project_artifacts,
                    "validate_project",
                ) as validate_project,
            ):
                with self.assertRaises(
                    transaction.LifecycleApplyRolledBack
                ) as raised:
                    with entry(
                        plan,
                        completion_input=self.completion_input(plan),
                        journal_clock=lambda: next(timestamps),
                        lock_clock="2030-01-02T03:04:05Z",
                        lock_pid=123,
                        lock_token_factory=lambda: "1" * 32,
                    ):
                        self.fail("failed apply must not yield")

            validate_project.assert_not_called()

            attempted = changed_ordinary[:3]
            self.assertEqual(raised.exception.code, "TRANSACTION_ROLLED_BACK")
            self.assertEqual(
                raised.exception.original_error_code,
                "STORAGE_REPLACE_FAILED",
            )
            self.assertIsNone(raised.exception.post_apply_validation)
            self.assertEqual(raised.exception.applied_target_indexes, attempted)
            self.assertEqual(
                raised.exception.rollback_target_indexes,
                tuple(reversed(attempted)),
            )
            self.assertEqual(rollback_calls, list(reversed(attempted)))
            self.assertFalse(lock_path.exists())
            self.assertTrue(workspace_path.is_dir())
            self.assertTrue((workspace_path / "preimages").is_dir())
            self.assertTrue(
                (workspace_path / "recovery-manifest.json").is_file()
            )
            for target in plan.targets:
                canonical = root / target.relative_path
                self.assertEqual(
                    canonical.read_bytes() if canonical.exists() else None,
                    canonical_before[target.relative_path],
                )
            evidence_stages = tuple(root.glob("**/.moduflow-stage-*"))
            self.assertTrue(evidence_stages)

            journals = [json.loads(payload) for payload, _previous in persisted]
            suffix = [
                (
                    journal["phase"],
                    journal["applied_target_indexes"],
                    journal["rollback_target_indexes"],
                )
                for journal in journals[-5:]
            ]
            self.assertEqual(
                suffix,
                [
                    ("rolling-back", list(attempted), []),
                    ("rolling-back", list(attempted), [attempted[2]]),
                    (
                        "rolling-back",
                        list(attempted),
                        [attempted[2], attempted[1]],
                    ),
                    (
                        "rolling-back",
                        list(attempted),
                        [attempted[2], attempted[1], attempted[0]],
                    ),
                    (
                        "rolled-back",
                        list(attempted),
                        [attempted[2], attempted[1], attempted[0]],
                    ),
                ],
            )
            self.assertEqual(
                [previous for _payload, previous in persisted],
                ["absent"]
                + [
                    hashlib.sha256(payload).hexdigest()
                    for payload, _previous in persisted[:-1]
                ],
            )
            self.assertTrue(
                all(
                    journal["created_at"] == timestamp_values[0]
                    for journal in journals
                )
            )

    def test_private_applied_workspace_persists_recovery_required_and_retains_state_on_rollback_failures(self):
        entry = getattr(transaction, "_private_applied_workspace", None)
        self.assertIsNotNone(entry)
        failures = (
            "classification",
            "restore-existing",
            "remove-new",
            "rollback-progress-journal",
            "rolled-back-journal",
            "recovery-required-journal",
        )
        for failure in failures:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root)
                (root / "workspace" / "transactions").mkdir()
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(require_issue_index=True),
                    project_context=context,
                    clock="2030-01-02",
                )
                changed_ordinary = tuple(
                    target.apply_order
                    for target in plan.targets
                    if target.changed and target.role != "evidence"
                )
                new_index = next(
                    target.apply_order
                    for target in plan.targets
                    if target.changed
                    and not target.existed
                    and target.role != "evidence"
                )
                self.assertEqual(new_index, changed_ordinary[-1])
                canonical_before = {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if target.existed
                        else None
                    )
                    for target in plan.targets
                }
                evidence = plan.targets[-1]
                workspace_path = (
                    root / ".moduflow" / "transactions" / plan.transaction_id
                )
                lock_path = (
                    root / ".moduflow" / "transactions" / "lifecycle.lock"
                )
                timestamp_values = iter(
                    f"2030-01-02T03:04:{second:02d}Z"
                    for second in range(
                        5,
                        5 + 11 + 2 * len(changed_ordinary),
                    )
                )
                real_apply = transaction.transaction_storage.apply_staged_target
                real_classify = (
                    transaction.transaction_storage.classify_canonical_target
                )
                real_rollback = (
                    transaction.transaction_storage.rollback_canonical_target
                )
                real_persist = (
                    transaction.transaction_storage.persist_serialized_journal
                )
                apply_calls = 0
                rollback_calls = []
                recovery_persist_calls = 0

                def failing_apply(workspace, target, proposal):
                    nonlocal apply_calls
                    apply_calls += 1
                    result = real_apply(workspace, target, proposal)
                    if apply_calls == len(changed_ordinary):
                        raise transaction.transaction_storage.LifecycleStorageError(
                            "STORAGE_REPLACE_FAILED"
                        )
                    return result

                def failing_classify(workspace, target):
                    self.assertTrue(lock_path.is_file())
                    if failure in {
                        "classification",
                        "recovery-required-journal",
                    }:
                        raise transaction.transaction_storage.LifecycleStorageError(
                            "STORAGE_CANONICAL_STATE_UNKNOWN"
                        )
                    return real_classify(workspace, target)

                def failing_rollback(workspace, target, preimage):
                    self.assertTrue(lock_path.is_file())
                    rollback_calls.append(target.index)
                    if failure == "remove-new" and target.index == new_index:
                        raise transaction.transaction_storage.LifecycleStorageError(
                            "STORAGE_REMOVE_FAILED"
                        )
                    if (
                        failure == "restore-existing"
                        and target.index == changed_ordinary[-2]
                    ):
                        raise transaction.transaction_storage.LifecycleStorageError(
                            "STORAGE_VERIFY_FAILED"
                        )
                    return real_rollback(workspace, target, preimage)

                def failing_persist(
                    workspace,
                    journal_bytes,
                    *,
                    expected_previous_sha256,
                ):
                    nonlocal recovery_persist_calls
                    journal = json.loads(journal_bytes)
                    if journal["phase"] == "recovery-required":
                        recovery_persist_calls += 1
                        if failure == "recovery-required-journal":
                            raise transaction.transaction_storage.LifecycleStorageError(
                                "STORAGE_WRITE_FAILED"
                            )
                    if (
                        failure == "rollback-progress-journal"
                        and journal["phase"] == "rolling-back"
                        and journal["rollback_target_indexes"]
                    ):
                        raise transaction.transaction_storage.LifecycleStorageError(
                            "STORAGE_WRITE_FAILED"
                        )
                    if (
                        failure == "rolled-back-journal"
                        and journal["phase"] == "rolled-back"
                    ):
                        raise transaction.transaction_storage.LifecycleStorageError(
                            "STORAGE_WRITE_FAILED"
                        )
                    return real_persist(
                        workspace,
                        journal_bytes,
                        expected_previous_sha256=expected_previous_sha256,
                    )

                with (
                    mock.patch.object(
                        transaction.transaction_storage,
                        "apply_staged_target",
                        side_effect=failing_apply,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "classify_canonical_target",
                        side_effect=failing_classify,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "rollback_canonical_target",
                        side_effect=failing_rollback,
                    ),
                    mock.patch.object(
                        transaction.transaction_storage,
                        "persist_serialized_journal",
                        side_effect=failing_persist,
                    ),
                    mock.patch.object(
                        transaction.validate_project_artifacts,
                        "validate_project",
                    ) as validate_project,
                ):
                    with self.assertRaises(
                        transaction.LifecycleRecoveryRequired
                    ) as raised:
                        with entry(
                            plan,
                            completion_input=self.completion_input(plan),
                            journal_clock=lambda: next(timestamp_values),
                            lock_clock="2030-01-02T03:04:05Z",
                            lock_pid=123,
                            lock_token_factory=lambda: "1" * 32,
                        ):
                            self.fail("failed apply must not yield")

                validate_project.assert_not_called()

                self.assertEqual(
                    raised.exception.code,
                    "TRANSACTION_RECOVERY_REQUIRED",
                )
                self.assertEqual(
                    raised.exception.original_error_code,
                    "STORAGE_REPLACE_FAILED",
                )
                self.assertIsNone(raised.exception.post_apply_validation)
                expected_rollback_error = {
                    "classification": "STORAGE_CANONICAL_STATE_UNKNOWN",
                    "restore-existing": "STORAGE_VERIFY_FAILED",
                    "remove-new": "STORAGE_REMOVE_FAILED",
                    "rollback-progress-journal": "STORAGE_WRITE_FAILED",
                    "rolled-back-journal": "STORAGE_WRITE_FAILED",
                    "recovery-required-journal": (
                        "STORAGE_CANONICAL_STATE_UNKNOWN"
                    ),
                }[failure]
                self.assertEqual(
                    raised.exception.rollback_error_code,
                    expected_rollback_error,
                )
                self.assertEqual(str(raised.exception), raised.exception.code)
                self.assertNotIn(str(root), repr(raised.exception))
                self.assertLessEqual(
                    len(raised.exception.rollback_target_indexes),
                    len(raised.exception.applied_target_indexes),
                )
                self.assertEqual(recovery_persist_calls, 1)
                self.assertFalse(lock_path.exists())
                self.assertTrue(workspace_path.is_dir())
                self.assertTrue((workspace_path / "preimages").is_dir())
                self.assertTrue(
                    (workspace_path / "recovery-manifest.json").is_file()
                )
                self.assertTrue((workspace_path / "journal.json").is_file())
                journal = json.loads(
                    (workspace_path / "journal.json").read_bytes()
                )
                self.assertEqual(
                    journal["phase"],
                    (
                        "applying"
                        if failure == "recovery-required-journal"
                        else "recovery-required"
                    ),
                )
                self.assertTrue(tuple(root.glob("**/.moduflow-stage-*")))
                self.assertEqual(
                    (root / evidence.relative_path).read_bytes()
                    if (root / evidence.relative_path).exists()
                    else None,
                    canonical_before[evidence.relative_path],
                )

    def test_private_applied_workspace_does_not_rollback_caller_body_exception(self):
        entry = getattr(transaction, "_private_applied_workspace", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            (root / "workspace" / "transactions").mkdir()
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(require_issue_index=True),
                project_context=context,
                clock="2030-01-02",
            )
            changed_ordinary = tuple(
                target.apply_order
                for target in plan.targets
                if target.changed and target.role != "evidence"
            )
            timestamps = iter(
                f"2030-01-02T03:04:{second:02d}Z"
                for second in range(
                    5,
                    5 + 11 + 2 * len(changed_ordinary),
                )
            )
            canonical_after = {}
            calls_at_yield = None
            real_classify = (
                transaction.transaction_storage.classify_canonical_target
            )
            real_finalize = (
                transaction.transaction_storage.finalize_staged_evidence
            )
            real_evidence_classify = (
                transaction.transaction_storage.classify_finalized_evidence
            )
            real_persist = (
                transaction.transaction_storage.persist_serialized_journal
            )
            with (
                mock.patch.object(
                    transaction.transaction_storage,
                    "classify_canonical_target",
                    wraps=real_classify,
                ) as classify_target,
                mock.patch.object(
                    transaction.transaction_storage,
                    "finalize_staged_evidence",
                    wraps=real_finalize,
                ) as finalize_evidence,
                mock.patch.object(
                    transaction.transaction_storage,
                    "classify_finalized_evidence",
                    wraps=real_evidence_classify,
                ) as classify_evidence,
                mock.patch.object(
                    transaction.transaction_storage,
                    "persist_serialized_journal",
                    wraps=real_persist,
                ) as persist_journal,
                mock.patch.object(
                    transaction.transaction_storage,
                    "rollback_canonical_target",
                ) as rollback_target,
                mock.patch.object(
                    transaction.transaction_storage,
                    "rollback_finalized_evidence",
                ) as rollback_evidence,
                mock.patch.object(
                    transaction.validate_project_artifacts,
                    "validate_project",
                    return_value=self.validation_result(),
                ) as validate_project,
            ):
                with self.assertRaisesRegex(RuntimeError, "CALLER FAILURE"):
                    with entry(
                        plan,
                        completion_input=self.completion_input(plan),
                        journal_clock=lambda: next(timestamps),
                        lock_clock="2030-01-02T03:04:05Z",
                        lock_pid=123,
                        lock_token_factory=lambda: "1" * 32,
                    ) as state:
                        self.assertIsInstance(
                            state,
                            transaction._PrivateCompletedState,
                        )
                        canonical_after = {
                            target.relative_path: (
                                (root / target.relative_path).read_bytes()
                                if (root / target.relative_path).exists()
                                else None
                            )
                            for target in plan.targets
                        }
                        calls_at_yield = (
                            classify_target.call_count,
                            finalize_evidence.call_count,
                            classify_evidence.call_count,
                            persist_journal.call_count,
                            rollback_target.call_count,
                            rollback_evidence.call_count,
                        )
                        raise RuntimeError("CALLER FAILURE")
            self.assertEqual(
                (
                    classify_target.call_count,
                    finalize_evidence.call_count,
                    classify_evidence.call_count,
                    persist_journal.call_count,
                    rollback_target.call_count,
                    rollback_evidence.call_count,
                ),
                calls_at_yield,
            )
            validate_project.assert_called_once()
            rollback_target.assert_not_called()
            rollback_evidence.assert_not_called()
            self.assertEqual(
                {
                    target.relative_path: (
                        (root / target.relative_path).read_bytes()
                        if (root / target.relative_path).exists()
                        else None
                    )
                    for target in plan.targets
                },
                canonical_after,
            )
            journal_path = (
                root
                / ".moduflow"
                / "transactions"
                / plan.transaction_id
                / "journal.json"
            )
            self.assertEqual(
                json.loads(journal_path.read_bytes())["phase"],
                "complete",
            )

    def test_exclusive_lifecycle_lock_creates_redacted_owner_and_releases(self):
        entry = getattr(transaction, "_exclusive_lifecycle_lock", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            owner_tokens = []

            for token in ("1" * 32, "2" * 32):
                with entry(
                    plan,
                    clock="2030-01-02T03:04:05Z",
                    pid=12345,
                    token_factory=lambda token=token: token,
                ) as owner:
                    owner_tokens.append(owner.owner_token)
                    self.assertTrue(lock_path.is_file())
                    self.assertEqual(
                        stat.S_IMODE(lock_path.parent.stat().st_mode),
                        0o700,
                    )
                    self.assertEqual(
                        stat.S_IMODE(lock_path.stat().st_mode),
                        0o600,
                    )
                    self.assertEqual(
                        json.loads(lock_path.read_text(encoding="utf-8")),
                        {
                            "schema": "moduflow.lifecycle-transaction-lock.v1",
                            "transaction_id": plan.transaction_id,
                            "pid": 12345,
                            "acquired_at": "2030-01-02T03:04:05Z",
                            "owner_token": token,
                        },
                    )
                    rendered = lock_path.read_text(encoding="utf-8")
                    self.assertTrue(lock_path.read_bytes().endswith(b"\n"))
                    self.assertNotIn(str(root), rendered)
                    self.assertNotIn("_before_bytes", rendered)
                    self.assertNotIn("_after_bytes", rendered)
                    self.assertFalse(hasattr(owner, "directory_fd"))
                self.assertFalse(lock_path.exists())

            self.assertEqual(owner_tokens, ["1" * 32, "2" * 32])
            self.assertTrue(lock_path.parent.is_dir())

    def test_authorized_recovery_subject_denies_before_recovery_io(self):
        entry = getattr(transaction, "_authorized_recovery_subject", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            denied_context = transaction._json_value(context)
            denied_context.update(
                transaction.project_operation.compute_project_policy(
                    "archived",
                    "internal",
                )
            )
            with (
                mock.patch.object(
                    transaction.transaction_storage,
                    "discover_recovery_workspaces",
                ) as discover,
                mock.patch.object(transaction.os, "kill") as kill_process,
                mock.patch.object(transaction.os, "unlink") as unlink,
                mock.patch.object(transaction.os, "fsync") as fsync,
            ):
                with self.assertRaises(
                    transaction.project_operation.ProjectOperationDenied
                ) as raised:
                    entry(
                        root,
                        "txn-recovery",
                        project_context=denied_context,
                    )

            self.assertEqual(
                raised.exception.decision["reason_code"],
                "PROJECT_OPERATION_DENIED_ARCHIVED",
            )
            discover.assert_not_called()
            kill_process.assert_not_called()
            unlink.assert_not_called()
            fsync.assert_not_called()

    def test_exclusive_recovery_lock_reclaims_only_exact_absent_pid_owner(self):
        subject_entry = getattr(transaction, "_authorized_recovery_subject", None)
        lock_entry = getattr(transaction, "_exclusive_recovery_lock", None)
        self.assertIsNotNone(subject_entry)
        self.assertIsNotNone(lock_entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            transactions = root / ".moduflow" / "transactions"
            transactions.mkdir(mode=0o700)
            subject = subject_entry(
                root,
                "txn-recovery",
                project_context=context,
            )
            lock_path = transactions / "lifecycle.lock"
            with mock.patch.object(transaction.os, "kill") as pid_probe:
                with lock_entry(
                    subject,
                    clock="2030-01-02T03:04:05Z",
                    pid=110,
                    token_factory=lambda: "0" * 32,
                ) as owner:
                    self.assertEqual(owner.transaction_id, "txn-recovery")
                    self.assertTrue(lock_path.is_file())
            pid_probe.assert_not_called()
            self.assertFalse(lock_path.exists())

            stale = transaction.canonical_json_bytes(
                {
                    "schema": "moduflow.lifecycle-transaction-lock.v1",
                    "transaction_id": "txn-recovery",
                    "pid": 111,
                    "acquired_at": "2030-01-02T03:04:05Z",
                    "owner_token": "1" * 32,
                }
            ) + b"\n"
            lock_path.write_bytes(stale)
            lock_path.chmod(0o600)
            stale_inode = lock_path.stat().st_ino
            probes = []

            def absent_pid(pid, signal):
                probes.append((pid, signal))
                raise ProcessLookupError(errno.ESRCH, "absent")

            real_fsync = transaction.os.fsync
            with mock.patch.object(
                transaction.os,
                "fsync",
                wraps=real_fsync,
            ) as fsync:
                with lock_entry(
                    subject,
                    clock="2030-01-02T03:04:06Z",
                    pid=222,
                    token_factory=lambda: "2" * 32,
                    pid_probe=absent_pid,
                ) as owner:
                    self.assertEqual(owner.transaction_id, "txn-recovery")
                    self.assertNotEqual(lock_path.stat().st_ino, stale_inode)
                    self.assertEqual(
                        json.loads(lock_path.read_bytes()),
                        {
                            "schema": "moduflow.lifecycle-transaction-lock.v1",
                            "transaction_id": "txn-recovery",
                            "pid": 222,
                            "acquired_at": "2030-01-02T03:04:06Z",
                            "owner_token": "2" * 32,
                        },
                    )
            self.assertEqual(probes, [(111, 0)])
            self.assertGreaterEqual(fsync.call_count, 1)
            self.assertFalse(lock_path.exists())

    def test_exclusive_recovery_lock_preserves_unproven_owner(self):
        subject_entry = getattr(transaction, "_authorized_recovery_subject", None)
        lock_entry = getattr(transaction, "_exclusive_recovery_lock", None)
        error_type = getattr(transaction, "LifecycleRecoveryLockError", None)
        self.assertIsNotNone(subject_entry)
        self.assertIsNotNone(lock_entry)
        self.assertIsNotNone(error_type)

        cases = (
            ("live", "RECOVERY_LOCK_LIVE"),
            ("uncertain", "RECOVERY_LOCK_UNCERTAIN"),
            ("malformed", "RECOVERY_LOCK_INVALID"),
            ("noncanonical", "RECOVERY_LOCK_INVALID"),
            ("foreign", "RECOVERY_LOCK_FOREIGN"),
            ("mode", "RECOVERY_LOCK_INVALID"),
            ("hardlink", "RECOVERY_LOCK_INVALID"),
            ("symlink", "RECOVERY_LOCK_INVALID"),
        )
        for case, expected_code in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root)
                transactions = root / ".moduflow" / "transactions"
                transactions.mkdir(mode=0o700)
                subject = subject_entry(
                    root,
                    "txn-recovery",
                    project_context=context,
                )
                lock_path = transactions / "lifecycle.lock"
                record = {
                    "schema": "moduflow.lifecycle-transaction-lock.v1",
                    "transaction_id": "txn-recovery",
                    "pid": 111,
                    "acquired_at": "2030-01-02T03:04:05Z",
                    "owner_token": "1" * 32,
                }
                payload = transaction.canonical_json_bytes(record) + b"\n"
                if case == "malformed":
                    payload = b"{private malformed lock\n"
                elif case == "noncanonical":
                    payload = json.dumps(record, indent=2).encode("utf-8") + b"\n"
                elif case == "foreign":
                    record["transaction_id"] = "txn-foreign"
                    payload = transaction.canonical_json_bytes(record) + b"\n"
                lock_path.write_bytes(payload)
                lock_path.chmod(0o644 if case == "mode" else 0o600)
                if case == "hardlink":
                    os.link(lock_path, transactions / "owner-copy")
                elif case == "symlink":
                    decoy = root / "lock-decoy"
                    decoy.write_bytes(payload)
                    decoy.chmod(0o600)
                    lock_path.unlink()
                    lock_path.symlink_to(decoy)
                before_bytes = lock_path.read_bytes()
                before_inode = lock_path.stat().st_ino

                def probe(_pid, _signal):
                    if case == "uncertain":
                        raise PermissionError(errno.EPERM, "uncertain")
                    return None

                with (
                    mock.patch.object(transaction.os, "unlink") as unlink,
                    mock.patch.object(transaction.os, "fsync") as fsync,
                ):
                    with self.assertRaises(error_type) as raised:
                        with lock_entry(subject, pid_probe=probe):
                            self.fail("unproven owner must remain blocking")

                self.assertEqual(raised.exception.code, expected_code)
                self.assertEqual(str(raised.exception), expected_code)
                self.assertNotIn(str(root), repr(raised.exception))
                unlink.assert_not_called()
                fsync.assert_not_called()
                self.assertEqual(lock_path.read_bytes(), before_bytes)
                self.assertEqual(lock_path.stat().st_ino, before_inode)

    def test_exclusive_recovery_lock_rejects_replaced_stale_candidate(self):
        subject_entry = getattr(transaction, "_authorized_recovery_subject", None)
        lock_entry = getattr(transaction, "_exclusive_recovery_lock", None)
        self.assertIsNotNone(subject_entry)
        self.assertIsNotNone(lock_entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            transactions = root / ".moduflow" / "transactions"
            transactions.mkdir(mode=0o700)
            subject = subject_entry(
                root,
                "txn-recovery",
                project_context=context,
            )
            lock_path = transactions / "lifecycle.lock"
            payload = transaction.canonical_json_bytes(
                {
                    "schema": "moduflow.lifecycle-transaction-lock.v1",
                    "transaction_id": "txn-recovery",
                    "pid": 111,
                    "acquired_at": "2030-01-02T03:04:05Z",
                    "owner_token": "1" * 32,
                }
            ) + b"\n"
            lock_path.write_bytes(payload)
            lock_path.chmod(0o600)
            original_inode = lock_path.stat().st_ino

            def replace_then_absent(_pid, _signal):
                replacement = transactions / "replacement"
                replacement.write_bytes(payload)
                replacement.chmod(0o600)
                os.replace(replacement, lock_path)
                raise ProcessLookupError(errno.ESRCH, "absent")

            with self.assertRaises(
                transaction.LifecycleRecoveryLockError
            ) as raised:
                with lock_entry(subject, pid_probe=replace_then_absent):
                    self.fail("replaced stale candidate must not be reclaimed")

            self.assertEqual(raised.exception.code, "RECOVERY_LOCK_REPLACED")
            self.assertNotEqual(lock_path.stat().st_ino, original_inode)
            self.assertEqual(lock_path.read_bytes(), payload)

    def test_exclusive_lifecycle_lock_rejects_concurrent_owner_without_changes(self):
        entry = getattr(transaction, "_exclusive_lifecycle_lock", None)
        error_type = getattr(transaction, "LifecycleLockError", None)
        self.assertIsNotNone(entry)
        self.assertIsNotNone(error_type)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"

            with entry(
                plan,
                clock="2030-01-02T03:04:05Z",
                pid=111,
                token_factory=lambda: "1" * 32,
            ):
                before_bytes = lock_path.read_bytes()
                before_stat = lock_path.stat()
                with mock.patch.object(transaction.os, "kill") as kill_process:
                    with self.assertRaises(error_type) as raised:
                        with entry(
                            plan,
                            clock="2030-01-02T03:04:06Z",
                            pid=222,
                            token_factory=lambda: "2" * 32,
                        ):
                            self.fail("concurrent lock must not be yielded")
                self.assertEqual(raised.exception.code, "LOCK_HELD")
                self.assertEqual(str(raised.exception), "LOCK_HELD")
                self.assertEqual(lock_path.read_bytes(), before_bytes)
                self.assertEqual(lock_path.stat().st_ino, before_stat.st_ino)
                self.assertEqual(lock_path.stat().st_mtime_ns, before_stat.st_mtime_ns)
                kill_process.assert_not_called()

    def test_exclusive_lifecycle_lock_denies_before_side_effects_and_rejects_symlinks(self):
        entry = getattr(transaction, "_exclusive_lifecycle_lock", None)
        self.assertIsNotNone(entry)
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
            denied = replace(plan, _project_context=denied_context)
            with (
                mock.patch.object(transaction.os, "open") as open_file,
                mock.patch.object(transaction.os, "mkdir") as make_directory,
                mock.patch.object(transaction.os, "unlink") as remove_file,
            ):
                with self.assertRaises(
                    transaction.project_operation.ProjectOperationDenied
                ) as raised:
                    with entry(denied):
                        self.fail("denied lock must not be yielded")
            self.assertEqual(
                raised.exception.decision["reason_code"],
                "PROJECT_OPERATION_DENIED_ARCHIVED",
            )
            open_file.assert_not_called()
            make_directory.assert_not_called()
            remove_file.assert_not_called()

            invalid_context = replace(
                plan,
                _project_context={"status": "unresolved"},
            )
            for candidate, options in (
                (invalid_context, {}),
                (plan, {"token_factory": "not-callable"}),
            ):
                with self.subTest(options=options):
                    with (
                        mock.patch.object(transaction.os, "open") as open_file,
                        mock.patch.object(transaction.os, "mkdir") as make_directory,
                        mock.patch.object(transaction.os, "unlink") as remove_file,
                    ):
                        with self.assertRaises(
                            transaction.LifecycleLockError
                        ) as raised:
                            with entry(candidate, **options):
                                self.fail("invalid lock input must not be yielded")
                    self.assertEqual(
                        raised.exception.code,
                        "LOCK_CONTEXT_INVALID",
                    )
                    open_file.assert_not_called()
                    make_directory.assert_not_called()
                    remove_file.assert_not_called()

        for component in (".moduflow", "transactions"):
            with self.subTest(component=component), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root)
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(),
                    project_context=context,
                    clock="2030-01-02",
                )
                if component == ".moduflow":
                    control = root / ".moduflow"
                    real = root / "real-moduflow"
                    control.rename(real)
                    control.symlink_to(real, target_is_directory=True)
                else:
                    external = root / "external-transactions"
                    external.mkdir()
                    (root / ".moduflow" / "transactions").symlink_to(
                        external,
                        target_is_directory=True,
                    )
                with self.assertRaises(transaction.LifecycleLockError) as raised:
                    with entry(
                        plan,
                        clock="2030-01-02T03:04:05Z",
                        pid=123,
                        token_factory=lambda: "1" * 32,
                    ):
                        self.fail("unsafe path lock must not be yielded")
                self.assertEqual(raised.exception.code, "LOCK_PATH_UNSAFE")

    def test_exclusive_lifecycle_lock_releases_body_failure_but_preserves_mismatch(self):
        entry = getattr(transaction, "_exclusive_lifecycle_lock", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            with self.assertRaisesRegex(ValueError, "protected body failed"):
                with entry(
                    plan,
                    clock="2030-01-02T03:04:05Z",
                    pid=123,
                    token_factory=lambda: "1" * 32,
                ):
                    raise ValueError("protected body failed")
            self.assertFalse(lock_path.exists())

        for sabotage in ("mutate", "replace", "delete", "symlink"):
            with self.subTest(sabotage=sabotage), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root)
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(),
                    project_context=context,
                    clock="2030-01-02",
                )
                lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
                with self.assertRaises(transaction.LifecycleLockError) as raised:
                    with entry(
                        plan,
                        clock="2030-01-02T03:04:05Z",
                        pid=123,
                        token_factory=lambda: "1" * 32,
                    ):
                        original = lock_path.read_bytes()
                        if sabotage == "mutate":
                            lock_path.write_bytes(b"mutated owner\n")
                        elif sabotage == "replace":
                            replacement = lock_path.with_name("replacement")
                            replacement.write_bytes(original)
                            os.replace(replacement, lock_path)
                        elif sabotage == "delete":
                            lock_path.unlink()
                        else:
                            decoy = lock_path.with_name("decoy")
                            decoy.write_bytes(original)
                            lock_path.unlink()
                            lock_path.symlink_to(decoy)
                self.assertEqual(raised.exception.code, "LOCK_OWNER_MISMATCH")
                if sabotage != "delete":
                    self.assertTrue(lock_path.exists() or lock_path.is_symlink())

    def test_exclusive_lifecycle_lock_cleans_only_its_partial_creation(self):
        entry = getattr(transaction, "_exclusive_lifecycle_lock", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            lock_path = root / ".moduflow" / "transactions" / "lifecycle.lock"
            real_write = transaction.os.write
            calls = []

            def fail_after_prefix(descriptor, payload):
                calls.append(len(payload))
                if len(calls) == 1:
                    return real_write(descriptor, payload[:3])
                raise OSError(errno.EIO, "PRIVATE WRITE FAILURE")

            with mock.patch.object(
                transaction.os,
                "write",
                side_effect=fail_after_prefix,
            ):
                with self.assertRaises(transaction.LifecycleLockError) as raised:
                    with entry(
                        plan,
                        clock="2030-01-02T03:04:05Z",
                        pid=123,
                        token_factory=lambda: "1" * 32,
                    ):
                        self.fail("partial lock must not be yielded")

            self.assertEqual(raised.exception.code, "LOCK_CREATE_FAILED")
            self.assertEqual(str(raised.exception), "LOCK_CREATE_FAILED")
            self.assertNotIn("PRIVATE", str(raised.exception))
            self.assertGreaterEqual(len(calls), 2)
            self.assertFalse(lock_path.exists())

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

    def test_private_projected_state_overlays_every_target_and_rebinds_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, nested=True)
            unrelated = root / "product/specs/unrelated/spec.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_bytes(b"canonical unrelated bytes\n")
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(
                    action="production-version",
                    require_issue_index=True,
                    roadmap_change={"priority": "p1"},
                    production_change={
                        "version": "1.2.3",
                        "record_id": "biz-103-release",
                        "content": "projected production bytes\n",
                    },
                ),
                project_context=context,
                clock="2030-01-02",
            )
            canonical_before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            projected_state = getattr(transaction, "_private_projected_state", None)
            self.assertIsNotNone(projected_state)

            with projected_state(plan) as projected:
                self.assertEqual(
                    [target.role for target in plan.targets],
                    [
                        "issue",
                        "state",
                        "loop",
                        "dashboard",
                        "issue-index",
                        "roadmap",
                        "production-record",
                        "evidence",
                    ],
                )
                for target in plan.targets:
                    destination = projected.root / target.relative_path
                    self.assertEqual(destination.read_bytes(), target._after_bytes)
                    self.assertEqual(
                        stat.S_IMODE(destination.stat().st_mode),
                        0o600,
                    )
                    self.assertEqual(
                        transaction.target_sha256(destination.read_bytes()),
                        target.after_sha256,
                    )
                self.assertEqual(
                    (
                        projected.root / "product/specs/unrelated/spec.md"
                    ).read_bytes(),
                    b"canonical unrelated bytes\n",
                )
                self.assertEqual(
                    projected.context["canonical_root"],
                    str(projected.root),
                )
                self.assertEqual(
                    projected.context["relative_paths"],
                    context["relative_paths"],
                )
                for role, relative in context["relative_paths"].items():
                    expected = projected.root / relative
                    self.assertEqual(
                        projected.context["paths"][role],
                        str(expected),
                    )
                    expected.relative_to(projected.root)
                for omitted in (
                    "candidates",
                    "question",
                    "warnings",
                    "reason_code",
                ):
                    self.assertNotIn(omitted, projected.context)
                transaction.project_registry.context_for_operation(
                    projected.root,
                    project_context=projected.context,
                )
                evidence = next(
                    target for target in plan.targets if target.role == "evidence"
                )
                production = next(
                    target
                    for target in plan.targets
                    if target.role == "production-record"
                )
                self.assertEqual(
                    stat.S_IMODE(
                        (projected.root / evidence.relative_path).parent.stat().st_mode
                    ),
                    0o700,
                )
                self.assertEqual(
                    stat.S_IMODE(
                        (projected.root / production.relative_path).parent.stat().st_mode
                    ),
                    0o700,
                )

            self.assertFalse(projected.root.exists())
            canonical_after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(canonical_after, canonical_before)
            self.assertEqual(plan.canonical_root, str(root.resolve()))

    def test_private_projected_state_rejects_invalid_targets_before_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            invalid = replace(
                plan,
                targets=(
                    replace(plan.targets[0], relative_path="../escape"),
                ),
            )
            projected_state = getattr(transaction, "_private_projected_state", None)
            self.assertIsNotNone(projected_state)

            with (
                mock.patch.object(transaction.os, "open") as open_file,
                mock.patch.object(transaction.os, "mkdir") as mkdir,
            ):
                with self.assertRaises(
                    transaction.LifecycleProjectedValidationError
                ) as raised:
                    with projected_state(invalid):
                        self.fail("invalid targets must not create projected state")
            self.assertEqual(raised.exception.code, "PROJECTED_TARGET_INVALID")
            open_file.assert_not_called()
            mkdir.assert_not_called()

    def test_private_projected_state_redacts_overlay_io_failure_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            canonical_before = (root / "issues/BIZ-103.md").read_bytes()
            projected_state = getattr(transaction, "_private_projected_state", None)
            self.assertIsNotNone(projected_state)

            with mock.patch.object(
                transaction.os,
                "lseek",
                side_effect=OSError("private projected path detail"),
            ):
                with self.assertRaises(
                    transaction.LifecycleProjectedValidationError
                ) as raised:
                    with projected_state(plan):
                        self.fail("failed read-back must not yield projected state")

            self.assertEqual(raised.exception.code, "PROJECTED_OVERLAY_FAILED")
            self.assertEqual(str(raised.exception), "PROJECTED_OVERLAY_FAILED")
            self.assertNotIn(
                "private projected path detail",
                str(raised.exception),
            )
            self.assertEqual(
                (root / "issues/BIZ-103.md").read_bytes(),
                canonical_before,
            )
            self.assertFalse(
                any(
                    "-projected-" in path.name
                    for path in (root / ".moduflow").iterdir()
                )
            )

    def test_private_projected_state_rejects_destination_collision_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            evidence = next(
                target for target in plan.targets if target.role == "evidence"
            )
            collision = root / evidence.relative_path
            collision.mkdir(parents=True)
            canonical_issue = (root / "issues/BIZ-103.md").read_bytes()

            with self.assertRaises(
                transaction.LifecycleProjectedValidationError
            ) as raised:
                with transaction._private_projected_state(plan):
                    self.fail("directory collision must not be overlaid")

            self.assertEqual(raised.exception.code, "PROJECTED_TARGET_UNSAFE")
            self.assertEqual(
                (root / "issues/BIZ-103.md").read_bytes(),
                canonical_issue,
            )
            self.assertTrue(collision.is_dir())
            self.assertFalse(
                any(
                    "-projected-" in path.name
                    for path in (root / ".moduflow").iterdir()
                )
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

    def test_validate_projected_transaction_calls_bound_validator_once_and_redacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root, nested=True)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            canonical_before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            entry = getattr(transaction, "validate_projected_transaction", None)
            validator_module = getattr(
                transaction,
                "validate_project_artifacts",
                None,
            )
            self.assertIsNotNone(entry)
            self.assertIsNotNone(validator_module)
            observed = {}

            def validate(projected_root, *, project_context=None):
                observed["root"] = Path(projected_root)
                observed["context"] = project_context
                self.assertTrue(observed["root"].is_dir())
                self.assertEqual(
                    project_context["canonical_root"],
                    str(observed["root"].resolve()),
                )
                for resolved in project_context["paths"].values():
                    Path(resolved).relative_to(observed["root"])
                return {
                    "schema": "moduflow.project-validation.v1",
                    "project_root": str(observed["root"]),
                    "valid": True,
                    "errors": [],
                    "warnings": ["PRIVATE VALIDATOR WARNING"],
                    "issue_schema": {
                        "errors": 0,
                        "warnings": 1,
                        "codes": ["PRIVATE_CODE"],
                        "diagnostics": [{"payload": "PRIVATE PAYLOAD"}],
                    },
                    "lifecycle_drift": [],
                }

            validator_call = mock.Mock(side_effect=validate)
            with (
                mock.patch.object(
                    validator_module,
                    "validate_project",
                    validator_call,
                ),
                mock.patch.object(transaction.os, "replace") as replacement,
            ):
                summary = entry(plan)

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
            validator_call.assert_called_once()
            replacement.assert_not_called()
            self.assertFalse(observed["root"].exists())
            self.assertNotIn("PRIVATE", json.dumps(summary))
            canonical_after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(canonical_after, canonical_before)

    def test_validate_projected_transaction_collapses_malformed_result_and_rejects_non_plan(self):
        entry = getattr(transaction, "validate_projected_transaction", None)
        self.assertIsNotNone(entry)
        with self.assertRaisesRegex(
            TypeError,
            "plan must be a LifecycleTransactionPlan",
        ):
            entry({})

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            with mock.patch.object(
                transaction.validate_project_artifacts,
                "validate_project",
                return_value={"schema": "PRIVATE INVALID CONTRACT"},
            ):
                summary = entry(plan)

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
                "error_codes": ["PROJECTED_VALIDATION_CONTRACT_INVALID"],
            },
        )
        self.assertNotIn("PRIVATE", json.dumps(summary))

    def test_validate_projected_transaction_redacts_runtime_failure_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.scaffold(root)
            plan = transaction.plan_lifecycle_transaction(
                root,
                self.intent(),
                project_context=context,
                clock="2030-01-02",
            )
            canonical_before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            observed = {}
            entry = getattr(transaction, "validate_projected_transaction", None)
            validator_module = getattr(
                transaction,
                "validate_project_artifacts",
                None,
            )
            self.assertIsNotNone(entry)
            self.assertIsNotNone(validator_module)

            def fail(projected_root, *, project_context=None):
                observed["root"] = Path(projected_root)
                raise RuntimeError(
                    f"PRIVATE VALIDATOR PAYLOAD at {projected_root}"
                )

            with mock.patch.object(
                validator_module,
                "validate_project",
                side_effect=fail,
            ):
                with self.assertRaises(
                    transaction.LifecycleProjectedValidationError
                ) as raised:
                    entry(plan)

            self.assertEqual(raised.exception.code, "PROJECTED_VALIDATION_FAILED")
            self.assertEqual(str(raised.exception), "PROJECTED_VALIDATION_FAILED")
            self.assertNotIn("PRIVATE", str(raised.exception))
            self.assertFalse(observed["root"].exists())
            canonical_after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(canonical_after, canonical_before)

    def test_validate_projected_transaction_denies_before_validator_or_filesystem_side_effects(self):
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
            denied = replace(plan, _project_context=denied_context)
            entry = getattr(transaction, "validate_projected_transaction", None)
            validator_module = getattr(
                transaction,
                "validate_project_artifacts",
                None,
            )
            self.assertIsNotNone(entry)
            self.assertIsNotNone(validator_module)

            with (
                mock.patch.object(
                    validator_module,
                    "validate_project",
                ) as validator_call,
                mock.patch.object(transaction.os, "open") as open_file,
                mock.patch.object(transaction.os, "mkdir") as mkdir,
            ):
                with self.assertRaises(
                    transaction.project_operation.ProjectOperationDenied
                ) as raised:
                    entry(denied)

            self.assertEqual(
                raised.exception.decision["reason_code"],
                "PROJECT_OPERATION_DENIED_ARCHIVED",
            )
            validator_call.assert_not_called()
            open_file.assert_not_called()
            mkdir.assert_not_called()

    def test_validate_projected_transaction_uses_real_validator_for_valid_and_invalid_proposals(self):
        entry = getattr(transaction, "validate_projected_transaction", None)
        self.assertIsNotNone(entry)
        active_issue = b"""---
schema_version: 0.1.0
issue_id: BIZ-103
canonical_state: active
status: in_progress
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:spec BIZ-103
---
# Issue: `BIZ-103`

**Status: active** -- created 2029-12-01, started 2030-01-02.
"""
        backlog_issue = b"""---
schema_version: 0.1.0
issue_id: BIZ-103
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:spec BIZ-103
---
# Issue: `BIZ-103`

**Status: backlog** -- created 2029-12-01.
"""
        cases = (
            (
                "valid",
                "start",
                {},
                {"issue": active_issue},
                [],
            ),
            (
                "invalid-issue",
                "start",
                {},
                {"issue": b"\xffPRIVATE ISSUE PAYLOAD"},
                [
                    "PROJECTED_PROJECT_INVALID",
                    "PROJECTED_ISSUE_SCHEMA_INVALID",
                    "PROJECTED_LIFECYCLE_DRIFT",
                ],
            ),
            (
                "invalid-state",
                "start",
                {},
                {
                    "issue": active_issue,
                    "state": b"{PRIVATE INVALID STATE",
                },
                ["PROJECTED_PROJECT_INVALID"],
            ),
            (
                "invalid-production-record",
                "production-version",
                {
                    "production_change": {
                        "version": "1.2.3",
                        "record_id": "biz-103-release",
                        "content": "initial production bytes\n",
                    }
                },
                {
                    "issue": backlog_issue,
                    "production-record": b"PRIVATE INVALID PRODUCTION\n",
                },
                ["PROJECTED_PROJECT_INVALID"],
            ),
        )

        for label, action, intent_changes, replacements, error_codes in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                context = self.scaffold(root)
                plan = transaction.plan_lifecycle_transaction(
                    root,
                    self.intent(action=action, **intent_changes),
                    project_context=context,
                    clock="2030-01-02",
                )
                plan = self.replace_projected_bytes(plan, replacements)
                canonical_before = {
                    path.relative_to(root).as_posix(): path.read_bytes()
                    for path in root.rglob("*")
                    if path.is_file()
                }

                summary = entry(plan)

                self.assertEqual(summary["valid"], not error_codes)
                self.assertEqual(summary["error_codes"], error_codes)
                self.assertEqual(
                    summary["rule_ids"],
                    [
                        "project-artifacts",
                        "issue-schema",
                        "lifecycle-consensus",
                        "production-records",
                    ],
                )
                rendered = json.dumps(summary, ensure_ascii=False)
                self.assertNotIn("PRIVATE", rendered)
                self.assertNotIn(str(root.resolve()), rendered)
                self.assertFalse(
                    any(
                        "-projected-" in path.name
                        for path in (root / ".moduflow").iterdir()
                    )
                )
                canonical_after = {
                    path.relative_to(root).as_posix(): path.read_bytes()
                    for path in root.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(canonical_after, canonical_before)
