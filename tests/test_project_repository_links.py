import json
import tempfile
import unittest
from pathlib import Path

from scripts import project_repository_identity
from scripts import validate_project_artifacts


def write_identity(root):
    target = Path(root) / ".moduflow" / "config.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "schema": "moduflow.config.v1",
                "git": {
                    "identity": {
                        "mode": "remote",
                        "provider": "github",
                        "canonical_repository": "github.com/owner/repo",
                        "remote_name_hint": "origin",
                        "base_branch": "main",
                        "lifecycle": "active",
                    }
                },
            }
        ),
        encoding="utf-8",
    )


class RepositoryLinkAuditTests(unittest.TestCase):
    def test_classifier_distinguishes_canonical_reference_and_unsafe_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_identity(root)
            (root / "issues").mkdir()
            (root / "issues" / "001-test.md").write_text(
                "# Issue\n\n## Links\n\n"
                "- GitHub: https://github.com/owner/repo/issues/1\n\n"
                "## Reference Implementations\n\n"
                "- https://github.com/example/reference\n",
                encoding="utf-8",
            )
            spec_dir = root / "specs" / "001-test"
            spec_dir.mkdir(parents=True)
            (spec_dir / "status.md").write_text(
                "# Status\n\nEvidence: https://github.com/old/repo/issues/2\n",
                encoding="utf-8",
            )
            (spec_dir / "pr.md").write_text(
                "# PR\n\nGitHub PR: https://github.com/old/repo/pull/9\n",
                encoding="utf-8",
            )

            findings = project_repository_identity.audit_repository_links(root)

        by_classification = {}
        for finding in findings:
            by_classification.setdefault(finding["classification"], []).append(finding)
        self.assertEqual(len(by_classification["canonical"]), 1)
        self.assertEqual(len(by_classification["reference"]), 1)
        self.assertEqual(len(by_classification["mismatch"]), 2)
        pr_finding = next(item for item in findings if item["artifact"].endswith("/pr.md"))
        self.assertTrue(pr_finding["write_handoff"])

    def test_validator_warns_for_undeclared_read_link_and_errors_for_write_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_identity(root)
            spec_dir = root / "specs" / "001-test"
            spec_dir.mkdir(parents=True)
            (spec_dir / "status.md").write_text(
                "# Status\n\nEvidence: https://github.com/old/repo/issues/2\n",
                encoding="utf-8",
            )
            (spec_dir / "release.md").write_text(
                "# Release\n\nTarget: https://github.com/old/repo/releases/tag/v1\n",
                encoding="utf-8",
            )
            errors = []
            warnings = []

            validate_project_artifacts.validate_repository_links(root, errors, warnings)

        self.assertTrue(any("release.md" in error and "non-canonical" in error for error in errors))
        self.assertTrue(any("status.md" in warning and "mirror/reference" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
