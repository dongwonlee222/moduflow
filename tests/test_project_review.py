import unittest

from scripts import project_review as pr


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
