import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import project_review as pr
from scripts import review_intake as ri


def sample_final_packet(review_id="review-1", *, source=None):
    packet = ri.new_packet(
        review_id=review_id,
        source=source
        or {
            "kind": "human",
            "provider": "external",
            "identity": "source-reviewer",
            "received_at": "2026-07-16",
            "retention": "hash_only",
            "sha256": "a" * 64,
        },
        target={
            "repository": "github.com/o/r",
            "commit": "b" * 40,
            "base_branch": "main",
        },
        trigger={
            "event": "manual_intake",
            "reason_codes": ["external_review_received"],
        },
        adapter_run={
            "invoked": ["manual-review-document", "superpowers-review"],
            "skipped": ["github-review", "security-review", "spec-kit"],
            "reason_codes": ["manual_source"],
        },
        raw_findings=[
            {
                "observation": "Observed behavior",
                "recommendation": "Fix behavior",
                "locations": [
                    {"path": "src/a.py", "line": 1, "anchor": "run"}
                ],
                "severity": "low",
                "release_impact": "non_blocking",
                "router": {
                    "classification": "actionable",
                    "confidence": "high",
                    "proposed_lane": "post_release_refactor",
                    "reason_codes": ["router_actionable"],
                    "actor": {
                        "kind": "ai",
                        "identity": "router",
                        "run_id": "r1",
                    },
                },
            }
        ],
    )
    decision = {
        "finding_id": "F-001",
        "target_commit": "b" * 40,
        "verification": {
            "state": "confirmed",
            "verifier": {
                "kind": "tool",
                "identity": "verifier",
                "role": "verifier",
                "run_id": "v1",
            },
            "files_checked": ["src/a.py"],
            "reproduction": ["fixture"],
            "tests": ["test_a"],
            "architecture": [],
            "import_boundaries": ["src/a.py -> stdlib"],
            "contradictions": [],
            "verified_at": "2026-07-16",
        },
        "disposition": "accept",
        "rationale": "Reproduced and tested.",
        "actor": {"kind": "human", "identity": "owner", "run_id": "d1"},
        "human_approved": True,
    }
    return ri.apply_decision(packet, decision)


def new_args(source, findings_file, write=False):
    return argparse.Namespace(
        review_id="review-preview",
        adapter="manual",
        source=str(source),
        findings_file=str(findings_file),
        source_kind="human",
        provider="external",
        source_identity="unknown",
        received_at="2026-07-16",
        retention="reference",
        source_hash=None,
        target_repository="github.com/o/r",
        target_commit="b" * 40,
        base_branch="main",
        write=write,
    )


class SourceAdapterTests(unittest.TestCase):
    def test_manual_adapter_requires_and_copies_findings_list(self):
        payload = {"findings": [{"observation": "Check this"}]}

        findings = pr.adapt_manual_findings(payload)
        findings[0]["observation"] = "changed"

        self.assertEqual(payload["findings"][0]["observation"], "Check this")

    def test_github_adapter_keeps_only_unresolved_current_threads(self):
        payload = {
            "threads": [
                {
                    "id": "T1",
                    "isResolved": False,
                    "isOutdated": False,
                    "path": "src/a.py",
                    "line": 8,
                    "comments": {
                        "nodes": [
                            {
                                "body": "Validate input",
                                "author": {"login": "reviewer", "type": "User"},
                            }
                        ]
                    },
                },
                {
                    "id": "T2",
                    "isResolved": True,
                    "isOutdated": False,
                    "path": "src/b.py",
                    "line": 9,
                    "comments": [
                        {"body": "Done", "author": {"login": "reviewer"}}
                    ],
                },
                {
                    "id": "T3",
                    "isResolved": False,
                    "isOutdated": True,
                    "path": "src/c.py",
                    "line": 10,
                    "comments": [
                        {"body": "Old", "author": {"login": "reviewer"}}
                    ],
                },
            ]
        }

        findings = pr.adapt_github_threads(payload)

        self.assertEqual([item["rule_id"] for item in findings], ["github-thread:T1"])
        self.assertEqual(findings[0]["source_author"]["identity"], "reviewer")
        self.assertEqual(findings[0]["source_author"]["kind"], "human")
        self.assertEqual(findings[0]["provider_evidence"]["resolved"], False)

    def test_github_adapter_marks_bot_comment_as_ai(self):
        payload = {
            "threads": [
                {
                    "id": "T1",
                    "isResolved": False,
                    "isOutdated": False,
                    "path": "src/a.py",
                    "line": 8,
                    "comments": [
                        {
                            "body": "AI suggestion",
                            "author": {"login": "copilot[bot]", "type": "Bot"},
                        }
                    ],
                }
            ]
        }

        finding = pr.adapt_github_threads(payload)[0]

        self.assertEqual(finding["source_author"]["kind"], "ai")

    def test_sarif_adapter_preserves_rule_partial_fingerprint_and_tool(self):
        payload = {
            "runs": [
                {
                    "tool": {
                        "driver": {"name": "scanner", "version": "1", "rules": []}
                    },
                    "results": [
                        {
                            "ruleId": "SEC-1",
                            "level": "warning",
                            "message": {"text": "Unsafe input"},
                            "partialFingerprints": {
                                "primaryLocationLineHash": "abc"
                            },
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "src/a.py"},
                                        "region": {"startLine": 4},
                                    }
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        finding = pr.adapt_sarif(payload)[0]

        self.assertEqual(finding["rule_id"], "SEC-1")
        self.assertEqual(finding["provider_fingerprint"], "abc")
        self.assertEqual(finding["severity"], "medium")
        self.assertEqual(finding["provider_evidence"]["tool"], "scanner")
        self.assertEqual(finding["provider_evidence"]["kind"], "security")

    def test_codeql_adapter_preserves_alert_disposition_history(self):
        payload = {
            "alerts": [
                {
                    "number": 7,
                    "state": "dismissed",
                    "dismissed_reason": "false positive",
                    "dismissed_comment": "sanitized test fixture",
                    "dismissed_by": {"login": "security-owner"},
                    "dismissed_at": "2026-07-16T00:00:00Z",
                    "rule": {
                        "id": "js/xss",
                        "description": "Unsafe output",
                        "security_severity_level": "high",
                    },
                    "tool": {"name": "CodeQL", "version": "2"},
                    "most_recent_instance": {
                        "location": {"path": "src/view.js", "start_line": 12}
                    },
                }
            ]
        }

        finding = pr.adapt_codeql_alerts(payload)[0]

        self.assertEqual(finding["provider_fingerprint"], "codeql-alert:7")
        self.assertEqual(
            finding["provider_evidence"]["dismissed_reason"], "false positive"
        )
        self.assertEqual(finding["provider_evidence"]["kind"], "security")
        self.assertEqual(finding["locations"][0]["path"], "src/view.js")


class LazyAdapterSelectionTests(unittest.TestCase):
    def test_l0_selects_no_review_adapters(self):
        result = pr.select_adapters(
            event="routine", adapter=None, changed_paths=[]
        )

        self.assertEqual(result["invoked"], [])
        self.assertIn("l0_routine", result["reason_codes"])

    def test_manual_review_invokes_manual_and_superpowers_only(self):
        result = pr.select_adapters(
            event="manual_intake", adapter="manual", changed_paths=["src/a.py"]
        )

        self.assertEqual(
            result["invoked"], ["manual-review-document", "superpowers-review"]
        )
        self.assertIn("github-review", result["skipped"])
        self.assertIn("security-review", result["skipped"])

    def test_sensitive_path_adds_security_adapter(self):
        result = pr.select_adapters(
            event="manual_intake",
            adapter="manual",
            changed_paths=["src/auth/token.py"],
        )

        self.assertIn("security-review", result["invoked"])
        self.assertIn("sensitive_path", result["reason_codes"])

    def test_router_can_request_security_and_planning_adapters(self):
        result = pr.select_adapters(
            event="manual_intake",
            adapter="manual",
            changed_paths=["src/export.py"],
            requires_plan=True,
            security_requested=True,
        )

        self.assertIn("security-review", result["invoked"])
        self.assertIn("spec-kit", result["invoked"])
        self.assertIn("router_security_request", result["reason_codes"])
        self.assertIn("planning_required", result["reason_codes"])


class ArtifactAndCliTests(unittest.TestCase):
    def test_script_help_runs_from_project_root(self):
        root = Path(__file__).resolve().parents[1]

        result = subprocess.run(
            [sys.executable, "scripts/project_review.py", "--help"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified ModuFlow code-review intake", result.stdout)

    def test_write_packet_creates_json_korean_summary_and_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            paths = pr.write_review_artifacts(root, sample_final_packet())

            self.assertTrue(paths["packet"].is_file())
            packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
            self.assertEqual(packet["candidates"][0]["finding_ids"], ["F-001"])
            self.assertEqual(
                packet["trace"]["finding_to_candidates"]["F-001"],
                ["review-1-RC-001"],
            )
            summary = paths["summary"].read_text(encoding="utf-8")
            self.assertIn("검증 상태", summary)
            self.assertIn("리뷰어 확신도", summary)
            self.assertIn("CognitiveDemand", paths["candidates"].read_text(encoding="utf-8"))

    def test_dry_run_does_not_create_workspace_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            source.write_text("external source", encoding="utf-8")
            findings = root / "findings.json"
            findings.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "observation": "Observed behavior",
                                "locations": [
                                    {
                                        "path": "src/a.py",
                                        "line": 1,
                                        "anchor": "run",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = pr.run_new_intake(
                root, new_args(source, findings, write=False)
            )

            self.assertEqual(result["action"], "preview")
            self.assertEqual(
                result["packet"]["schema"], "moduflow.review-intake.v1"
            )
            self.assertFalse((root / "workspace" / "reviews").exists())

    def test_hash_mismatch_blocks_decision_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "source.md"
            source_path.write_text("original", encoding="utf-8")
            source = ri.build_source_record(
                "human",
                "external",
                "reviewer",
                "2026-07-16",
                "reference",
                locator=source_path,
            )
            packet = sample_final_packet(source=source)
            reviews = root / "workspace" / "reviews"
            reviews.mkdir(parents=True)
            (reviews / "review-1.json").write_text(
                json.dumps(packet), encoding="utf-8"
            )
            decisions = root / "decisions.json"
            decisions.write_text(
                json.dumps({"decisions": []}), encoding="utf-8"
            )
            source_path.write_text("changed", encoding="utf-8")

            with self.assertRaises(ri.ReviewIntakeError) as caught:
                pr.apply_decisions_to_path(
                    root, "review-1", decisions, write=True
                )

            self.assertEqual(caught.exception.code, "source_integrity_mismatch")

    def test_candidate_queue_retains_other_review_packets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pr.write_review_artifacts(root, sample_final_packet("review-one"))

            paths = pr.write_review_artifacts(
                root, sample_final_packet("review-two")
            )

            queue = paths["candidates"].read_text(encoding="utf-8")
            self.assertIn("review-one-RC-001", queue)
            self.assertIn("review-two-RC-001", queue)

    def test_existing_issue_becomes_overlap_hint_without_auto_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "issues").mkdir()
            (root / "issues" / "123-fix-behavior.md").write_text(
                "# Issue 123: Fix behavior\n\nObserved behavior\n",
                encoding="utf-8",
            )

            paths = pr.write_review_artifacts(root, sample_final_packet())

            packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
            candidate = packet["candidates"][0]
            self.assertEqual(candidate["state"], "candidate")
            self.assertEqual(
                candidate["overlap_hints"][0]["issue_id"],
                "123-fix-behavior",
            )

    def test_korean_summary_never_renders_copied_source_text(self):
        source = ri.build_source_record(
            "human",
            "external",
            "reviewer",
            "2026-07-16",
            "copy",
            copied_text="sensitive-original-review",
        )

        summary = pr.render_summary_ko(sample_final_packet(source=source))

        self.assertNotIn("sensitive-original-review", summary)

    def test_validate_final_reports_pending_disposition(self):
        packet = sample_final_packet()
        packet["findings"][0]["disposition"]["state"] = "pending_verification"

        result = pr.run_validation(packet, final=True)

        self.assertFalse(result["valid"])
        self.assertIn(
            "disposition_pending", {error["code"] for error in result["errors"]}
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
