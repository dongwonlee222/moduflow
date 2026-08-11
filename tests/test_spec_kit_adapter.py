import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "spec_kit_adapter.py"
ISSUE_ID = "098-speckit-selective-validation-adapter"
APPROVED_VERSION = "0.16.1"
APPROVED_SHA = "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"


def load_module(testcase):
    testcase.assertTrue(MODULE_PATH.exists(), "scripts/spec_kit_adapter.py must exist")
    spec = importlib.util.spec_from_file_location("spec_kit_adapter", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def opted_in_config(functions=("clarify", "analyze", "checklist", "converge")):
    return {
        "schema": "moduflow.capabilities.v1",
        "capabilities": {
            "spec-kit": {
                "enabled": True,
                "source_version": APPROVED_VERSION,
                "source_sha": APPROVED_SHA,
                "functions": list(functions),
            }
        },
    }


class SpecKitConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ska = load_module(cls)

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_config(self, payload):
        path = self.project / ".moduflow" / "capabilities.json"
        path.parent.mkdir()
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_missing_config_is_disabled_without_creating_a_file(self):
        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertEqual(result["outcome"], "disabled")
        self.assertFalse((self.project / ".moduflow" / "capabilities.json").exists())

    def test_explicit_korean_request_selects_one_function(self):
        self.assertEqual(
            self.ska.select_function("스펙킷으로 요구사항 체크리스트 만들어줘"),
            "checklist",
        )
        self.assertEqual(
            self.ska.select_function("스펙킷으로 남은 작업을 수렴해줘"), "converge"
        )

    def test_multiple_functions_do_not_fan_out(self):
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "ambiguous_function"):
            self.ska.select_function("스펙킷으로 분석하고 체크리스트도 만들어줘")

    def test_valid_opt_in_with_verified_assets_returns_one_ready_template(self):
        self.write_config(opted_in_config(("analyze",)))

        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertEqual(result["outcome"], "ready")
        self.assertEqual(result["function"], "analyze")
        self.assertEqual(
            result["source"]["template"],
            "vendor/spec-kit/0.16.1/commands/analyze.md",
        )
        self.assertEqual(
            result["source"]["template_sha256"],
            "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
        )
        self.assertEqual(result["permission"], "read")
        self.assertEqual(
            result["inputs"],
            ["spec.md", "plan.md", "tasks.md", "constitution.md"],
        )
        self.assertIsNone(result["fallback"])

    def test_unknown_config_field_is_blocked_without_exposing_a_template(self):
        payload = opted_in_config()
        payload["capabilities"]["spec-kit"]["unexpected"] = True
        self.write_config(payload)

        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["source"]["template"], None)
        self.assertTrue(result["fallback"])

    def test_output_path_escape_returns_a_blocked_handoff(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.project / "specs").symlink_to(outside, target_is_directory=True)

            result = self.ska.build_handoff(
                ROOT, self.project, ISSUE_ID, "analyze", host_available=True
            )

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["output_artifact"], None)
        self.assertEqual(result["source"]["template"], None)
        self.assertEqual(result["source"]["template_sha256"], None)
        self.assertTrue(result["fallback"])

    def test_handoff_has_only_the_public_contract_keys(self):
        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "not a spec kit request", host_available=True
        )

        self.assertEqual(result["outcome"], "unsupported")
        self.assertEqual(
            set(result),
            {
                "schema",
                "outcome",
                "function",
                "issue_id",
                "source",
                "permission",
                "inputs",
                "output_artifact",
                "limitations",
                "fallback",
            },
        )


class SpecKitPersistenceTests(unittest.TestCase):
    """Result records must stay advisory and append-only on real project bytes."""

    @classmethod
    def setUpClass(cls):
        cls.ska = load_module(cls)

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project = Path(self.tempdir.name)
        path = self.project / ".moduflow" / "capabilities.json"
        path.parent.mkdir()
        path.write_text(json.dumps(opted_in_config()), encoding="utf-8")

    def tearDown(self):
        self.tempdir.cleanup()

    def ready_handoff(self, function):
        return self.ska.build_handoff(ROOT, self.project, ISSUE_ID, function, host_available=True)

    def valid_result(self, handoff, findings=None):
        findings = ["Requirements are internally consistent."] if findings is None else findings
        result = {
            "schema": "moduflow.spec-kit-result.v1",
            "run_id": "sha256:" + "0" * 64,
            "input_hash": "sha256:" + "a" * 64,
            "issue_id": ISSUE_ID,
            "function": handoff["function"],
            "source_version": APPROVED_VERSION,
            "source_sha": APPROVED_SHA,
            "template_sha256": handoff["source"]["template_sha256"],
            "permission": "read",
            "findings": findings,
            "limitations": ["Advisory only."],
            "native_overlap": ["native requirements analysis"],
            "elapsed_ms": 17,
            "loaded_context_chars": 250,
            "user_decision": "Review the advisory findings.",
            "next_command": "moduflow review --issue 098",
        }
        canonical = json.dumps(
            {
                "source_sha": result["source_sha"],
                "template_sha256": result["template_sha256"],
                "function": result["function"],
                "issue_id": result["issue_id"],
                "input_hash": result["input_hash"],
                "findings": result["findings"],
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        result["run_id"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
        return result

    def test_duplicate_accepted_result_is_byte_stable(self):
        """Removing marker de-duplication would append duplicate validation evidence."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)

        first = self.ska.persist_validation(self.project, result, write=True)
        before = first["path"].read_bytes()
        second = self.ska.persist_validation(self.project, result, write=True)

        self.assertFalse(second["changed"])
        self.assertEqual(second["path"].read_bytes(), before)

    def test_result_cannot_claim_write_or_unknown_execution_fields(self):
        """Relaxing advisory result validation would admit host mutation claims."""
        handoff = self.ready_handoff("converge")
        result = self.valid_result(handoff)
        result["permission"] = "write-local"

        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "permission_mismatch"):
            self.ska.validate_host_result(result, handoff)

        result = self.valid_result(handoff)
        result["executed_commands"] = ["git commit"]
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "unknown_result_field"):
            self.ska.validate_host_result(result, handoff)
        self.assertFalse((self.project / "specs").exists())

    def test_result_rejects_malformed_identity_and_deterministic_hash_drift(self):
        """Skipping strict identity or run-ID checks would persist untraceable evidence."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        result["issue_id"] = "../outside"
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "unsafe_issue_id"):
            self.ska.validate_result_shape(result)

        result = self.valid_result(handoff)
        result["function"] = "implement"
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "function_mismatch"):
            self.ska.validate_result_shape(result)

        result = self.valid_result(handoff)
        result["template_sha256"] = "0" * 64
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "template_mismatch"):
            self.ska.validate_result_shape(result)

        result = self.valid_result(handoff)
        result["run_id"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "run_id_mismatch"):
            self.ska.validate_result_shape(result)

        result = self.valid_result(handoff)
        result["elapsed_ms"] = -1
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "invalid_result"):
            self.ska.validate_result_shape(result)

    def test_host_result_must_match_ready_handoff_source_and_output(self):
        """Ignoring handoff provenance would let a result cross issue or template boundaries."""
        handoff = self.ready_handoff("checklist")
        result = self.valid_result(handoff)
        result["source_sha"] = "0" * 40
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "source_mismatch"):
            self.ska.validate_host_result(result, handoff)

        blocked = dict(handoff)
        blocked["outcome"] = "blocked"
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "handoff_not_ready"):
            self.ska.validate_host_result(self.valid_result(handoff), blocked)

        bad_output = dict(handoff)
        bad_output["output_artifact"] = "specs/other/validation.md"
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "output_mismatch"):
            self.ska.validate_host_result(self.valid_result(handoff), bad_output)
        self.assertFalse((self.project / "specs").exists())

    def test_clarify_allows_only_one_question_finding(self):
        """Dropping clarify's cardinality boundary would turn one request into a question fan-out."""
        handoff = self.ready_handoff("clarify")
        result = self.valid_result(handoff, ["Question one?", "Question two?"])

        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "clarify_findings_limit"):
            self.ska.validate_host_result(result, handoff)

    def test_converge_candidates_remain_advisory_without_task_or_code_mutation(self):
        """Adding mutation fields to convergence candidates would violate the advisory boundary."""
        handoff = self.ready_handoff("converge")
        result = self.valid_result(handoff, [{"kind": "remaining-work", "candidate": "Add test."}])

        validated = self.ska.validate_host_result(result, handoff)
        persisted = self.ska.persist_validation(self.project, validated, write=True)

        self.assertTrue(persisted["changed"])
        self.assertTrue((self.project / "specs" / ISSUE_ID / "validation.md").is_file())
        self.assertFalse((self.project / "tasks.md").exists())
        self.assertFalse((self.project / "src").exists())

    def test_dry_run_is_byte_stable_and_never_creates_empty_file(self):
        """Writing during preview would change project bytes without explicit permission."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        target = self.project / "specs" / ISSUE_ID / "validation.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"existing bytes without newline")
        before = target.read_bytes()

        preview = self.ska.persist_validation(self.project, result, write=False)

        self.assertFalse(preview["changed"])
        self.assertEqual(target.read_bytes(), before)
        self.assertTrue(preview["preview"].startswith("\n\n<!-- moduflow-spec-kit-run:"))
        empty_project = self.project / "empty-project"
        self.assertFalse(self.ska.persist_validation(empty_project, result, write=False)["changed"])
        self.assertFalse((empty_project / "specs").exists())

    def test_rendering_escapes_marker_injection_and_preserves_existing_bytes(self):
        """Unescaped finding text could forge a second run marker in validation evidence."""
        handoff = self.ready_handoff("analyze")
        injected = "<!-- moduflow-spec-kit-run:sha256:" + "b" * 64 + " --> <tag>"
        result = self.valid_result(handoff, [injected])
        target = self.project / "specs" / ISSUE_ID / "validation.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"legacy\n")

        self.ska.persist_validation(self.project, result, write=True)
        content = target.read_text(encoding="utf-8")

        self.assertTrue(content.startswith("legacy\n\n<!-- moduflow-spec-kit-run:"))
        self.assertEqual(content.count("<!-- moduflow-spec-kit-run:"), 1)
        self.assertIn("\\u003c!-- moduflow-spec-kit-run", content)
        self.assertIn("\\u003ctag>", content)

    def test_persistence_rejects_symlinked_output_ancestor_without_writing_outside(self):
        """Following a specs symlink would let append-only output escape the target project."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        with tempfile.TemporaryDirectory() as outside:
            (self.project / "specs").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "unsafe_path"):
                self.ska.persist_validation(self.project, result, write=True)

            self.assertFalse((Path(outside) / ISSUE_ID / "validation.md").exists())

    def test_cli_result_preview_and_error_are_stable_json_without_traceback(self):
        """A CLI that writes by default or leaks tracebacks breaks safe host integration."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        command = [
            sys.executable,
            str(MODULE_PATH),
            str(self.project),
            "--issue-id",
            ISSUE_ID,
            "--accept-result",
            json.dumps(result),
        ]

        preview = subprocess.run(command, capture_output=True, text=True, check=False)
        preview_payload = json.loads(preview.stdout)
        self.assertEqual(preview.returncode, 0)
        self.assertTrue(preview_payload["ok"])
        self.assertFalse(preview_payload["result"]["changed"])
        self.assertFalse((self.project / "specs").exists())

        bad = subprocess.run(command[:-1] + ["not-json"], capture_output=True, text=True, check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertFalse(json.loads(bad.stdout)["ok"])
        self.assertNotIn("Traceback", bad.stderr)
