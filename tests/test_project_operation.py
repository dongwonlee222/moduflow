import contextlib
import io
import json
import unittest

from scripts import project_operation
from tests.project_operation_fixture import context_with_policy, resolved_context


class ProjectPolicyMatrixTests(unittest.TestCase):
    def test_status_trust_operation_matrix_is_fail_closed(self):
        cases = [
            ("active", "internal", (True, True, True, True), ""),
            ("active", "read-only", (True, False, False, False), "PROJECT_OPERATION_DENIED_READ_ONLY"),
            ("active", "unknown", (True, False, False, False), "PROJECT_OPERATION_DENIED_TRUST_UNKNOWN"),
            ("archived", "internal", (True, False, False, False), "PROJECT_OPERATION_DENIED_ARCHIVED"),
            ("archived", "read-only", (True, False, False, False), "PROJECT_OPERATION_DENIED_ARCHIVED"),
            ("archived", "unknown", (True, False, False, False), "PROJECT_OPERATION_DENIED_ARCHIVED"),
            ("unknown", "internal", (True, False, False, False), "PROJECT_OPERATION_DENIED_STATUS_UNKNOWN"),
            ("unknown", "read-only", (True, False, False, False), "PROJECT_OPERATION_DENIED_READ_ONLY"),
            ("unknown", "unknown", (True, False, False, False), "PROJECT_OPERATION_DENIED_STATUS_UNKNOWN"),
        ]
        operations = ("read", "write", "execute", "publish")

        for status, trust, expected_flags, denied_reason in cases:
            with self.subTest(status=status, trust=trust):
                policy = project_operation.compute_project_policy(status, trust)
                actual_flags = tuple(policy["capabilities"][name] for name in operations)
                self.assertEqual(actual_flags, expected_flags)
                self.assertEqual(policy["project_status"], status)
                self.assertEqual(policy["policy_trust_scope"], trust)
                if denied_reason:
                    for operation in operations[1:]:
                        self.assertEqual(
                            policy["capability_reasons"][operation]["reason_code"],
                            denied_reason,
                        )
                        self.assertTrue(policy["capability_reasons"][operation]["message"])
                        self.assertTrue(policy["capability_reasons"][operation]["recommendation"])
                    self.assertEqual(
                        policy["capability_reasons"]["read"]["reason_code"],
                        "PROJECT_READ_ALLOWED_DIAGNOSTIC",
                    )
                else:
                    for operation in operations:
                        self.assertEqual(
                            policy["capability_reasons"][operation]["reason_code"],
                            "PROJECT_OPERATION_ALLOWED",
                        )

    def test_unrecognized_inputs_normalize_to_unknown_and_preserve_observed_values(self):
        policy = project_operation.compute_project_policy("paused", "External Team")

        self.assertEqual(policy["project_status"], "unknown")
        self.assertEqual(policy["policy_trust_scope"], "unknown")
        self.assertEqual(
            policy["policy_inputs"],
            {
                "project_status_source": "paused",
                "trust_scope_source": "External Team",
            },
        )
        self.assertTrue(policy["capabilities"]["read"])
        self.assertFalse(policy["capabilities"]["write"])
        self.assertEqual(
            policy["capability_reasons"]["write"]["reason_code"],
            "PROJECT_OPERATION_DENIED_STATUS_UNKNOWN",
        )

    def test_missing_status_takes_precedence_over_missing_trust(self):
        policy = project_operation.compute_project_policy(None, None)

        self.assertEqual(
            policy["capability_reasons"]["execute"]["reason_code"],
            "PROJECT_OPERATION_DENIED_STATUS_UNKNOWN",
        )
        self.assertIsNone(policy["policy_inputs"]["project_status_source"])
        self.assertIsNone(policy["policy_inputs"]["trust_scope_source"])

    def test_explicit_root_compatibility_maps_only_policy_trust(self):
        policy = project_operation.compute_project_policy(
            "active",
            "project-local",
            explicit_root_compatibility=True,
        )

        self.assertEqual(policy["project_status"], "active")
        self.assertEqual(policy["policy_trust_scope"], "internal")
        self.assertEqual(
            policy["policy_inputs"],
            {
                "project_status_source": "active",
                "trust_scope_source": "project-local",
            },
        )
        self.assertEqual(
            policy["capabilities"],
            {"read": True, "write": True, "execute": True, "publish": True},
        )

    def test_non_resolved_context_has_complete_all_denied_shape(self):
        policy = project_operation.compute_project_policy(
            None,
            None,
            resolution_status="ambiguous",
        )

        self.assertEqual(
            policy["capabilities"],
            {"read": False, "write": False, "execute": False, "publish": False},
        )
        for operation in ("read", "write", "execute", "publish"):
            self.assertEqual(
                policy["capability_reasons"][operation]["reason_code"],
                "PROJECT_CONTEXT_UNAVAILABLE",
            )


class ProjectOperationAuthorizationTests(unittest.TestCase):
    def test_cli_denial_boundary_prints_json_without_traceback_and_returns_nonzero(self):
        context = context_with_policy(
            project_operation,
            status="archived",
            trust="internal",
        )

        @project_operation.cli_denial_boundary
        def denied_command():
            project_operation.require_project_capability(context, "write")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = denied_command()

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["reason_code"], "PROJECT_OPERATION_DENIED_ARCHIVED")
        self.assertNotIn("Traceback", output.getvalue())

    def test_allowed_decision_uses_stable_schema_and_normalized_policy(self):
        context = context_with_policy(project_operation, status="active", trust="internal")

        decision = project_operation.authorize_project_operation(context, "execute")

        self.assertEqual(
            decision,
            {
                "schema": "moduflow.project-operation-authorization.v1",
                "allowed": True,
                "operation": "execute",
                "project_id": "project-a",
                "project_status": "active",
                "policy_trust_scope": "internal",
                "policy_inputs": {
                    "project_status_source": "active",
                    "trust_scope_source": "internal",
                },
                "reason_code": "PROJECT_OPERATION_ALLOWED",
                "message": "Project policy allows this operation.",
                "recommendation": "Continue with all downstream operation gates.",
            },
        )

    def test_unknown_operation_is_denied_without_guessing(self):
        context = context_with_policy(project_operation)

        decision = project_operation.authorize_project_operation(context, "deploy-now")

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["operation"], "deploy-now")
        self.assertEqual(decision["reason_code"], "PROJECT_OPERATION_UNKNOWN")
        self.assertIn("read, write, execute, or publish", decision["recommendation"])

    def test_invalid_resolution_is_denied_even_if_capability_claims_allow(self):
        context = resolved_context()
        context["status"] = "ambiguous"
        context["capabilities"] = {"read": True, "write": True, "execute": True, "publish": True}
        context["capability_reasons"] = {
            name: {"reason_code": "PROJECT_OPERATION_ALLOWED"}
            for name in ("read", "write", "execute", "publish")
        }

        decision = project_operation.authorize_project_operation(context, "read")

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason_code"], "PROJECT_CONTEXT_UNAVAILABLE")

    def test_missing_capability_claim_denies_instead_of_recomputing(self):
        context = context_with_policy(project_operation)
        del context["capabilities"]["write"]

        decision = project_operation.authorize_project_operation(context, "write")

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason_code"], "PROJECT_CAPABILITY_UNAVAILABLE")

    def test_enforcing_guard_raises_typed_error_with_identical_payload(self):
        context = context_with_policy(project_operation, status="archived", trust="internal")
        expected = project_operation.authorize_project_operation(context, "publish")

        with self.assertRaises(project_operation.ProjectOperationDenied) as raised:
            project_operation.require_project_capability(context, "publish")

        self.assertEqual(raised.exception.decision, expected)
        self.assertIs(project_operation.denial_exit_payload(raised.exception), raised.exception.decision)
        self.assertEqual(str(raised.exception), expected["message"])

    def test_enforcing_guard_returns_allowed_decision(self):
        context = context_with_policy(project_operation)

        decision = project_operation.require_project_capability(context, "write")

        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["operation"], "write")


if __name__ == "__main__":
    unittest.main()
