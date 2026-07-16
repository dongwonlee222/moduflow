import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts import review_intake as ri


def make_packet(
    *,
    severity="medium",
    path="src/a.py",
    no_risk_claim=False,
    raw_findings=None,
    review_id="review-1",
):
    source = {
        "kind": "human",
        "provider": "external",
        "identity": "source-reviewer",
        "received_at": "2026-07-16",
        "retention": "hash_only",
        "sha256": "a" * 64,
    }
    target = {
        "repository": "github.com/o/r",
        "commit": "b" * 40,
        "base_branch": "main",
    }
    findings = raw_findings or [
        {
            "observation": "Observed behavior",
            "recommendation": "Suggested change",
            "root_cause_hypothesis": "Possible cause",
            "locations": [{"path": path, "line": 10, "anchor": "run"}],
            "severity": severity,
            "release_impact": (
                "blocking" if severity in {"high", "critical"} else "non_blocking"
            ),
            "no_risk_claim": no_risk_claim,
        }
    ]
    return ri.new_packet(
        review_id=review_id,
        source=source,
        target=target,
        trigger={
            "event": "manual_intake",
            "reason_codes": ["external_review_received"],
        },
        adapter_run={
            "invoked": ["manual-review-document"],
            "skipped": [],
            "reason_codes": ["manual_source"],
        },
        raw_findings=findings,
    )


def decision_for(
    finding_id,
    *,
    disposition="accept",
    actor_kind="human",
    human_approved=False,
    verification_state="confirmed",
    target_commit="b" * 40,
):
    return {
        "finding_id": finding_id,
        "target_commit": target_commit,
        "verification": {
            "state": verification_state,
            "verifier": {
                "kind": "tool",
                "identity": "independent-verifier",
                "role": "verifier",
                "run_id": "verify-1",
            },
            "files_checked": ["src/a.py"],
            "reproduction": ["reproduced with fixture"],
            "tests": ["tests/test_a.py::test_behavior"],
            "architecture": [],
            "import_boundaries": ["src/a.py -> stdlib"],
            "contradictions": [],
            "verified_at": "2026-07-16",
        },
        "disposition": disposition,
        "rationale": f"Evidence supports {disposition}.",
        "actor": {
            "kind": actor_kind,
            "identity": "decision-owner",
            "run_id": "decision-1",
        },
        "human_approved": human_approved,
    }


class SourceAndPacketTests(unittest.TestCase):
    def test_reference_retention_hashes_without_copying_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.md"
            path.write_text("external review", encoding="utf-8")
            source = ri.build_source_record(
                kind="human",
                provider="external-reviewer",
                identity="unknown",
                received_at="2026-07-16",
                retention="reference",
                locator=str(path),
            )

        self.assertEqual(
            source["sha256"], hashlib.sha256(b"external review").hexdigest()
        )
        self.assertNotIn("copied_text", source)

    def test_reference_url_removes_credentials_query_and_fragment(self):
        source = ri.build_source_record(
            kind="human",
            provider="external",
            identity="unknown",
            received_at="2026-07-16",
            retention="reference",
            locator="https://user:token@example.com/review.md?sig=secret#section",
            source_hash="c" * 64,
        )

        self.assertEqual(source["locator"], "https://example.com/review.md")
        self.assertNotIn("token", repr(source))
        self.assertNotIn("secret", repr(source))

    def test_hash_only_requires_explicit_lowercase_sha256(self):
        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.build_source_record(
                kind="tool",
                provider="scanner",
                identity="scanner",
                received_at="2026-07-16",
                retention="hash_only",
                source_hash="not-a-hash",
            )

        self.assertEqual(caught.exception.code, "source_hash_invalid")

    def test_finding_separates_review_content_and_provenance(self):
        packet = make_packet(
            raw_findings=[
                {
                    "observation": "Observed behavior",
                    "recommendation": "Suggested change",
                    "root_cause_hypothesis": "Possible cause",
                    "reviewer_confidence": "medium",
                    "locations": [
                        {"path": "src/a.py", "line": 10, "anchor": "run"}
                    ],
                    "provider_evidence": {"format": "manual"},
                }
            ]
        )

        finding = packet["findings"][0]
        self.assertEqual(finding["id"], "F-001")
        self.assertEqual(finding["observation"], "Observed behavior")
        self.assertEqual(finding["recommendation"], "Suggested change")
        self.assertEqual(finding["root_cause_hypothesis"], "Possible cause")
        self.assertEqual(finding["reviewer_confidence"], "medium")
        self.assertEqual(finding["provider_evidence"]["format"], "manual")
        self.assertEqual(finding["verification"]["state"], "unverified")
        self.assertEqual(finding["disposition"]["state"], "pending_verification")
        self.assertEqual(finding["decision_history"], [])
        self.assertTrue(finding["fingerprint"].startswith("sha256:"))

    def test_line_movement_does_not_change_fingerprint(self):
        first = make_packet(
            raw_findings=[
                {
                    "observation": "Same finding",
                    "rule_id": "R1",
                    "locations": [
                        {"path": "src/a.py", "line": 10, "anchor": "run"}
                    ],
                }
            ]
        )
        second = make_packet(
            raw_findings=[
                {
                    "observation": "Same finding",
                    "rule_id": "R1",
                    "locations": [
                        {"path": "src/a.py", "line": 99, "anchor": "run"}
                    ],
                }
            ]
        )

        self.assertEqual(
            first["findings"][0]["fingerprint"],
            second["findings"][0]["fingerprint"],
        )

    def test_provider_fingerprint_changes_cross_run_identity(self):
        first = make_packet(
            raw_findings=[
                {
                    "observation": "Same finding",
                    "rule_id": "R1",
                    "provider_fingerprint": "provider-a",
                    "locations": [
                        {"path": "src/a.py", "line": 10, "anchor": "run"}
                    ],
                }
            ]
        )
        second = make_packet(
            raw_findings=[
                {
                    "observation": "Same finding",
                    "rule_id": "R1",
                    "provider_fingerprint": "provider-b",
                    "locations": [
                        {"path": "src/a.py", "line": 10, "anchor": "run"}
                    ],
                }
            ]
        )

        self.assertNotEqual(
            first["findings"][0]["fingerprint"],
            second["findings"][0]["fingerprint"],
        )

    def test_review_id_cannot_escape_review_directory(self):
        packet = make_packet()
        packet["review_id"] = "../../outside"

        errors = ri.validate_packet(packet)

        self.assertIn("review_id_invalid", {error["code"] for error in errors})

    def test_validate_packet_does_not_mutate_input(self):
        packet = {"schema": "wrong"}
        before = copy.deepcopy(packet)

        self.assertTrue(ri.validate_packet(packet))
        self.assertEqual(packet, before)


class DecisionPolicyTests(unittest.TestCase):
    def test_no_risk_stays_unverified_without_tests_and_boundaries(self):
        finding = make_packet(no_risk_claim=True)["findings"][0]

        policy = ri.evaluate_policy(finding)

        self.assertIn("no_risk_evidence_missing", policy["reason_codes"])

    def test_ai_cannot_reject_high_risk_without_human_approval(self):
        packet = make_packet(severity="high")
        decision = decision_for(
            "F-001",
            disposition="reject",
            actor_kind="ai",
            human_approved=False,
        )

        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(packet, decision)

        self.assertEqual(
            caught.exception.code, "high_risk_reject_requires_human"
        )
        self.assertEqual(
            packet["findings"][0]["disposition"]["state"],
            "pending_verification",
        )

    def test_confirmed_sensitive_finding_routes_security(self):
        packet = make_packet(path="src/auth/token.py")

        updated = ri.apply_decision(
            packet,
            decision_for(
                "F-001",
                disposition="accept",
                actor_kind="human",
                human_approved=True,
            ),
        )

        finding = updated["findings"][0]
        self.assertEqual(finding["route"]["lane"], "security")
        self.assertEqual(finding["route"]["CognitiveDemand"], "deep")

    def test_high_nonsecurity_finding_routes_pre_release(self):
        packet = make_packet(severity="high", path="src/calculator.py")

        updated = ri.apply_decision(
            packet,
            decision_for("F-001", disposition="accept", human_approved=True),
        )

        finding = updated["findings"][0]
        self.assertEqual(finding["route"]["lane"], "pre_release")
        self.assertEqual(finding["route"]["CognitiveDemand"], "balanced")

    def test_tool_security_evidence_routes_security(self):
        packet = make_packet(
            raw_findings=[
                {
                    "observation": "Scanner finding",
                    "locations": [
                        {"path": "src/view.py", "line": 2, "anchor": "render"}
                    ],
                    "severity": "medium",
                    "provider_evidence": {"kind": "security"},
                }
            ]
        )

        updated = ri.apply_decision(
            packet,
            decision_for("F-001", disposition="accept", human_approved=True),
        )

        self.assertEqual(updated["findings"][0]["route"]["lane"], "security")

    def test_target_commit_mismatch_requires_reverification(self):
        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(
                make_packet(),
                decision_for("F-001", target_commit="c" * 40),
            )

        self.assertEqual(caught.exception.code, "target_commit_mismatch")

    def test_required_verifier_must_be_independent(self):
        packet = make_packet(severity="medium")
        decision = decision_for("F-001")
        decision["verification"]["verifier"] = {
            "kind": "human",
            "identity": "source-reviewer",
            "role": "verifier",
        }

        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(packet, decision)

        self.assertEqual(caught.exception.code, "verifier_not_independent")

    def test_source_reviewer_cannot_self_verify_with_new_run_id(self):
        packet = make_packet(severity="medium")
        decision = decision_for("F-001")
        decision["verification"]["verifier"] = {
            "kind": "human",
            "identity": "source-reviewer",
            "role": "verifier",
            "run_id": "different-run",
        }

        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(packet, decision)

        self.assertEqual(caught.exception.code, "verifier_not_independent")

    def test_accept_requires_confirmed_evidence(self):
        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(
                make_packet(),
                decision_for(
                    "F-001",
                    disposition="accept",
                    verification_state="inconclusive",
                ),
            )

        self.assertEqual(caught.exception.code, "accept_requires_evidence")

    def test_partial_accept_allows_explicit_inconclusive_evidence(self):
        decision = decision_for(
            "F-001",
            disposition="partial_accept",
            verification_state="inconclusive",
        )
        decision["accepted_scope"] = "Preserve the verified observation only."
        updated = ri.apply_decision(
            make_packet(),
            decision,
        )

        self.assertEqual(
            updated["findings"][0]["disposition"]["state"],
            "partial_accept",
        )

    def test_partial_accept_candidate_uses_accepted_scope_not_original_remedy(self):
        decision = decision_for(
            "F-001",
            disposition="partial_accept",
            verification_state="inconclusive",
        )
        decision["accepted_scope"] = "Preserve the verified observation only."
        packet = ri.apply_decision(make_packet(), decision)

        candidate = ri.build_candidates(packet)["candidates"][0]

        self.assertEqual(
            candidate["title"], "Preserve the verified observation only."
        )
        self.assertNotEqual(
            candidate["title"], packet["findings"][0]["recommendation"]
        )

    def test_partial_accept_requires_accepted_scope(self):
        decision = decision_for(
            "F-001",
            disposition="partial_accept",
            verification_state="inconclusive",
        )

        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(make_packet(), decision)

        self.assertEqual(caught.exception.code, "partial_accept_scope_missing")

    def test_every_disposition_requires_rationale(self):
        decision = decision_for("F-001", disposition="defer")
        decision["rationale"] = ""

        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(make_packet(), decision)

        self.assertEqual(caught.exception.code, "disposition_rationale_missing")

    def test_no_risk_becomes_verified_with_tests_and_boundaries(self):
        updated = ri.apply_decision(
            make_packet(no_risk_claim=True),
            decision_for("F-001", disposition="accept"),
        )

        self.assertEqual(
            updated["findings"][0]["risk"]["no_risk_state"], "verified"
        )

    def test_changed_disposition_keeps_append_only_history(self):
        packet = ri.apply_decision(
            make_packet(severity="low"),
            decision_for(
                "F-001",
                disposition="defer",
                verification_state="inconclusive",
            ),
        )
        packet = ri.apply_decision(
            packet,
            decision_for(
                "F-001",
                disposition="accept",
                verification_state="confirmed",
            ),
        )

        self.assertEqual(
            [
                event["state"]
                for event in packet["findings"][0]["decision_history"]
            ],
            ["defer", "accept"],
        )


def finalized_packet(dispositions, *, severity="low"):
    raw_findings = [
        {
            "observation": f"Observation {index}",
            "recommendation": f"Recommendation {index}",
            "locations": [
                {
                    "path": f"src/file_{index}.py",
                    "line": index,
                    "anchor": f"fn_{index}",
                }
            ],
            "severity": severity,
            "release_impact": "non_blocking",
            "router": {
                "classification": "actionable",
                "confidence": "high",
                "proposed_lane": None,
                "reason_codes": ["router_actionable"],
                "dependency_hints": ["010-foundation"] if index == 1 else [],
                "actor": {
                    "kind": "ai",
                    "identity": "router",
                    "run_id": "router-1",
                },
            },
        }
        for index in range(1, len(dispositions) + 1)
    ]
    packet = make_packet(raw_findings=raw_findings)
    for index, disposition in enumerate(dispositions, 1):
        verification_state = (
            "contradicted"
            if disposition == "reject"
            else (
                "inconclusive"
                if disposition in {"partial_accept", "defer"}
                else "confirmed"
            )
        )
        decision = decision_for(
            f"F-{index:03d}",
            disposition=disposition,
            verification_state=verification_state,
        )
        if disposition == "partial_accept":
            decision["accepted_scope"] = f"Observation {index} only"
        packet = ri.apply_decision(packet, decision)
    return packet


def accepted_packet():
    return finalized_packet(["accept"])


class CandidateRoutingTests(unittest.TestCase):
    def test_only_accept_and_partial_create_candidates(self):
        packet = finalized_packet(
            ["accept", "partial_accept", "defer", "reject"]
        )

        candidates = ri.build_candidates(packet)["candidates"]

        self.assertEqual(len(candidates), 2)
        self.assertEqual(
            [candidate["finding_ids"] for candidate in candidates],
            [["F-001"], ["F-002"]],
        )

    def test_exact_fingerprint_links_existing_candidate(self):
        packet = accepted_packet()
        existing = [
            {
                "id": "older-review-RC-001",
                "fingerprint": packet["findings"][0]["fingerprint"],
                "issue_id": "123-existing",
            }
        ]

        result = ri.build_candidates(packet, existing_candidates=existing)

        candidate = result["candidates"][0]
        self.assertEqual(candidate["state"], "linked_existing")
        self.assertEqual(candidate["existing_issue_ids"], ["123-existing"])
        self.assertEqual(candidate["linked_candidate_id"], "older-review-RC-001")

    def test_local_candidate_duplicate_does_not_invent_issue_id(self):
        packet = accepted_packet()
        existing = [
            {
                "id": "older-review-RC-001",
                "fingerprint": packet["findings"][0]["fingerprint"],
                "existing_issue_ids": [],
            }
        ]

        candidate = ri.build_candidates(
            packet, existing_candidates=existing
        )["candidates"][0]

        self.assertEqual(candidate["existing_issue_ids"], [])
        self.assertEqual(candidate["next_command"], "product:review --intake")

    def test_trace_is_bidirectional(self):
        result = ri.build_candidates(accepted_packet())
        candidate = result["candidates"][0]

        self.assertEqual(
            result["trace"]["finding_to_candidates"]["F-001"],
            [candidate["id"]],
        )
        self.assertEqual(
            result["trace"]["candidate_to_findings"][candidate["id"]],
            ["F-001"],
        )

    def test_explicit_proposals_support_grouping_and_splitting(self):
        packet = finalized_packet(["accept", "accept"])
        proposals = [
            {
                "title": "Shared remediation",
                "finding_ids": ["F-001", "F-002"],
            },
            {"title": "Separate hardening", "finding_ids": ["F-001"]},
        ]

        trace = ri.build_candidates(packet, proposals=proposals)["trace"]

        self.assertEqual(len(trace["finding_to_candidates"]["F-001"]), 2)
        self.assertEqual(len(trace["finding_to_candidates"]["F-002"]), 1)

    def test_proposal_cannot_leave_accepted_finding_unmapped(self):
        packet = finalized_packet(["accept", "accept"])

        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.build_candidates(
                packet,
                proposals=[{"title": "Only first", "finding_ids": ["F-001"]}],
            )

        self.assertEqual(caught.exception.code, "accepted_finding_unmapped")

    def test_candidate_carries_priority_dependencies_and_route_reasons(self):
        packet = finalized_packet(["accept"], severity="high")

        candidate = ri.build_candidates(packet)["candidates"][0]

        self.assertEqual(candidate["priority"], "p1")
        self.assertEqual(candidate["lane"], "pre_release")
        self.assertEqual(candidate["CognitiveDemand"], "balanced")
        self.assertEqual(candidate["dependencies"], ["010-foundation"])
        self.assertIn("elevated_severity", candidate["routing_reason_codes"])
        self.assertIn("router_actionable", candidate["routing_reason_codes"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
