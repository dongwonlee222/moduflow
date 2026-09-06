"""Issue 126 — a refusal must name something the operator can change.

Reproduced on 2026-09-06. `validate_project` found six problems, one of them
`issues/048-x.md: linked artifact missing: specs/048-x/spec.md`, and the person
running `--sync` received exactly this:

    PROJECTED_VALIDATION_INVALID: Lifecycle reconcile transaction did not
    commit. Recommendation: Run product:doctor before retrying.

A rule id, and advice that closes a loop — doctor's own remedy is to run sync.

The sentences deliberately do **not** come from the transaction. Its result
envelope, its validation summaries and its journal record are all strictly
redacted by issue 103: logical codes and hashes only. The state they describe
is a throwaway staging copy whose paths no longer exist when the error is read.
So the refusal re-validates the canonical project instead — the files the
operator can actually open. These tests hold both halves: the refusal names the
artifact, and the transaction's redaction is untouched.
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lifecycle = load_module("project_lifecycle_126", "scripts/project_lifecycle.py")


MISSING_LINK = "\n## Links\n\n- Spec: `specs/048-x/spec.md`\n"


def scaffold(root, issues, *, active_in_dashboard="048-x", state_active="048-x", body=""):
    (root / "issues").mkdir()
    for issue_id, status in issues.items():
        (root / "issues" / f"{issue_id}.md").write_text(
            f"# Issue: `{issue_id}`\n\n**Status: {status}** — created.\n{body}",
            encoding="utf-8",
        )
    (root / ".moduflow").mkdir()
    (root / ".moduflow" / "state.json").write_text(
        json.dumps(
            {
                "schema": "moduflow.state.v1",
                "phase": "spec",
                "active_goal": "g",
                "active_issue": state_active,
                "next_command": "product:status",
                "blockers": [],
                "updated_at": "2026-09-06",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "workspace").mkdir()
    (root / "workspace" / "dashboard.md").write_text(
        "# Dashboard\n\n## Active Issue\n\n- `"
        + active_in_dashboard
        + "` (phase: spec).\n\n## Next Command\n\n`product:status`\n",
        encoding="utf-8",
    )
    (root / "workspace" / "loop-state.json").write_text(
        json.dumps(
            {
                "schema": "moduflow.loop-state.v2",
                "goal_id": "g",
                "issue_ids": [state_active] if state_active else [],
                "active_issue_id": state_active or None,
                "status": "active",
                "next_command": "product:status",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "workspace" / "transactions").mkdir()


class SyncRefusalNamesTheArtifact(unittest.TestCase):
    def _refuse(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        scaffold(root, {"048-x": "active"}, body=MISSING_LINK)
        return root, lifecycle.sync_lifecycle(root)

    def test_the_refusal_still_happens(self):
        """Guard: this must not be 'fixed' by letting the sync through."""
        _root, result = self._refuse()
        self.assertEqual(result["status"], "blocked")

    def test_the_refusal_names_the_missing_artifact(self):
        _root, result = self._refuse()
        self.assertIn("specs/048-x/spec.md", "\n".join(result["errors"]))

    def test_the_refusal_names_the_file_that_holds_the_link(self):
        _root, result = self._refuse()
        self.assertIn("issues/048-x.md", "\n".join(result["errors"]))

    def test_the_refusal_keeps_the_machine_code(self):
        """Sentences are added beside the code, not substituted for it."""
        _root, result = self._refuse()
        self.assertIn("PROJECTED_VALIDATION_INVALID", "\n".join(result["errors"]))

    def test_the_refusal_no_longer_recommends_doctor(self):
        """The transaction said run doctor; doctor says run sync."""
        _root, result = self._refuse()
        self.assertNotIn("product:doctor", "\n".join(result["errors"]))

    def test_the_refusal_leaks_no_host_path(self):
        """Validation runs against a private staging copy. Its absolute paths
        must not reach the operator — they name a directory that is already
        gone, and the transaction envelope forbids them for the same reason."""
        root, result = self._refuse()
        joined = "\n".join(result["errors"])
        self.assertNotIn(str(root.resolve()), joined)
        self.assertNotIn(".txn-", joined)


class ARefusalWithNothingToShowSaysSo(unittest.TestCase):
    def test_a_clean_project_yields_no_sentences(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, {"048-x": "active"})
            findings = lifecycle.project_validation_sentences(root)
            self.assertNotIn("specs/048-x/spec.md", "\n".join(findings))

    def test_the_no_finding_branch_does_not_invent_a_cause(self):
        """Naming a cause here would be the exact failure this issue exists to
        stop. It must say the projection was rejected and stop there."""
        lines = lifecycle.refusal_lines(
            "PROJECTED_VALIDATION_INVALID",
            Path("/nonexistent-project-root-for-126"),
            subject="Lifecycle reconcile transaction",
        )
        joined = "\n".join(lines)
        self.assertIn("PROJECTED_VALIDATION_INVALID", joined)
        self.assertNotIn("product:doctor", joined)
        self.assertIn("projection-only", joined)


class SentencesComeFromEverySource(unittest.TestCase):
    """`refusal_lines` reads three fields, because a refusal can come from any
    of them and reading only `errors` would report 'no problems' for drift."""

    class _Validator:
        def __init__(self, payload):
            self.payload = payload

        def validate_project(self, root, project_context=None):
            return self.payload

    def _sentences(self, payload):
        original = lifecycle._load_validate_project_artifacts
        lifecycle._load_validate_project_artifacts = lambda: self._Validator(payload)
        try:
            return lifecycle.project_validation_sentences(Path("."))
        finally:
            lifecycle._load_validate_project_artifacts = original

    def test_plain_errors_are_reported(self):
        sentences = self._sentences({"errors": ["workspace/roadmap.md: missing"]})
        self.assertIn("workspace/roadmap.md: missing", sentences)

    def test_lifecycle_drift_is_reported(self):
        sentences = self._sentences(
            {"lifecycle_drift": ["state.json active_issue '' != issue-file '048-x'"]}
        )
        self.assertTrue(any("active_issue" in s for s in sentences), sentences)

    def test_issue_schema_diagnostics_name_their_field(self):
        """These already carry source_path and field, which is precisely what
        the acceptance criterion asks a refusal to name."""
        sentences = self._sentences(
            {
                "issue_schema": {
                    "diagnostics": [
                        {
                            "severity": "error",
                            "source_path": "issues/083-x.md",
                            "field": "depends_on",
                            "message": "Dependency 082-y is unfinished",
                        }
                    ]
                }
            }
        )
        joined = "\n".join(sentences)
        self.assertIn("issues/083-x.md", joined)
        self.assertIn("depends_on", joined)

    def test_warnings_are_not_reported_as_causes(self):
        """A warning does not make a project invalid, so it did not cause this
        refusal and must not be offered as its reason."""
        sentences = self._sentences(
            {
                "errors": ["workspace/roadmap.md: missing"],
                "issue_schema": {
                    "diagnostics": [
                        {
                            "severity": "warning",
                            "source_path": "issues/083-x.md",
                            "field": "depends_on",
                            "message": "Dependency 082-y is unfinished",
                        }
                    ]
                },
            }
        )
        self.assertNotIn("083-x", "\n".join(sentences))

    def test_a_broken_validator_reports_nothing_rather_than_raising(self):
        """The refusal path must not itself fail. A refusal that crashes tells
        the operator even less than a bare code."""

        class Exploding:
            def validate_project(self, root, project_context=None):
                raise RuntimeError("validator is broken")

        original = lifecycle._load_validate_project_artifacts
        lifecycle._load_validate_project_artifacts = lambda: Exploding()
        try:
            self.assertEqual(lifecycle.project_validation_sentences(Path(".")), [])
        finally:
            lifecycle._load_validate_project_artifacts = original


class TheTransactionStaysRedacted(unittest.TestCase):
    """126 must not be paid for with issue 103's redaction guarantees."""

    def test_the_transaction_module_is_unchanged_by_this_issue(self):
        import subprocess

        diff = subprocess.run(
            ["git", "diff", "HEAD", "--", "scripts/project_lifecycle_transaction.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            diff.stdout.strip(),
            "",
            "the refusal must read the canonical project, never widen the "
            "redacted transaction contract",
        )

    def test_the_transaction_result_still_carries_no_prose(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        scaffold(root, {"048-x": "active"}, body=MISSING_LINK)
        result = lifecycle.sync_lifecycle(root)
        projected = result["transaction"]["projected_validation"]
        self.assertEqual(
            set(projected), {"valid", "rule_ids", "error_codes"},
            "the validation summary schema is three logical keys wide",
        )


if __name__ == "__main__":
    unittest.main()
