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


if __name__ == "__main__":
    unittest.main(verbosity=2)
