import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "spec_kit_pilot.py"
FIXTURES = ROOT / "tests" / "fixtures" / "spec-kit-selective-validation" / "cases.json"
ISSUE_ID = "098-speckit-selective-validation-adapter"
FUNCTIONS = ("clarify", "analyze", "checklist", "converge")
INPUTS = {
    "clarify": [f"issues/{ISSUE_ID}.md", f"specs/{ISSUE_ID}/spec.md"],
    "analyze": [
        f"specs/{ISSUE_ID}/spec.md",
        f"specs/{ISSUE_ID}/plan.md",
        f"specs/{ISSUE_ID}/tasks.md",
        "workspace/constitution.md",
    ],
    "checklist": [f"issues/{ISSUE_ID}.md", f"specs/{ISSUE_ID}/spec.md"],
    "converge": [
        f"specs/{ISSUE_ID}/spec.md",
        f"specs/{ISSUE_ID}/plan.md",
        f"specs/{ISSUE_ID}/tasks.md",
        "workspace/constitution.md",
    ],
}


def load_module():
    spec = importlib.util.spec_from_file_location("spec_kit_pilot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independent_input_hash(function):
    records = []
    for relative in INPUTS[function]:
        content = (ROOT / relative).read_bytes()
        records.append({"path": relative, "sha256": hashlib.sha256(content).hexdigest()})
    canonical = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def independent_loaded_context_chars(function):
    paths = [
        ROOT / "overlays" / "spec-kit" / "selective-validation-policy.md",
        ROOT / "vendor" / "spec-kit" / "0.16.1" / "commands" / f"{function}.md",
        *(ROOT / relative for relative in INPUTS[function]),
    ]
    return sum(len(path.read_text(encoding="utf-8")) for path in paths)


class SpecKitPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pilot = load_module()

    def canonical_cases(self):
        return json.loads(json.dumps(self.pilot.load_cases(FIXTURES)["cases"]))

    def evaluate_cases(self, cases, result_base=FIXTURES.parent):
        return self.pilot.evaluate_cases(
            cases,
            result_base=result_base,
            package_root=ROOT,
        )

    def case(self, cases, case_id):
        return next(case for case in cases if case["id"] == case_id)

    def copy_fixtures(self, root):
        destination = root / "tests" / "fixtures" / "spec-kit-selective-validation"
        destination.parent.mkdir(parents=True)
        shutil.copytree(FIXTURES.parent, destination)
        return destination / "cases.json"

    def run_cli(self, root, fixtures, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(root), "--fixtures", str(fixtures), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_fixture_matrix_is_request_driven_without_self_declared_safety(self):
        cases = self.canonical_cases()
        self.assertEqual(len(cases), 24)
        self.assertEqual(
            {case["function"] for case in cases if case["class"] == "success"},
            set(FUNCTIONS),
        )
        for case in cases:
            self.assertRegex(case["id"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertTrue(case["request"].strip())
            self.assertIn(case["expected_outcome"], {"ready", "disabled", "unavailable", "unsupported"})
            for untrusted in (
                "passed",
                "boundary_violation",
                "unauthorized_write",
                "fanout",
                "false_execution_claim",
                "output_artifact",
            ):
                self.assertNotIn(untrusted, case)

    def test_finite_grammar_matrix_has_required_evidence_counts(self):
        cases = self.canonical_cases()
        counts = {
            "canonical_success": sum(case["class"] == "success" for case in cases),
            "availability_fallback": sum(
                case["class"] in {"disabled", "unavailable"} for case in cases
            ),
            "grammar_fallback": sum(case["class"] == "grammar" for case in cases),
        }

        self.assertEqual(
            counts,
            {
                "canonical_success": 8,
                "availability_fallback": 4,
                "grammar_fallback": 12,
            },
        )

    def test_real_router_and_adapter_derive_every_case_outcome(self):
        report = self.evaluate_cases(self.canonical_cases())

        self.assertEqual(report["passed_cases"], 24)
        self.assertTrue(report["passed"])
        for case in report["cases"]:
            self.assertTrue(case["passed"], case)
            self.assertFalse(case["artifact_created"], case)
            if case["class"] == "success":
                self.assertEqual(case["route_outcome"], "delegate")
                self.assertEqual(case["adapter_outcome"], "ready")
                self.assertEqual(case["selected_function"], case["function"])
                self.assertEqual(case["fanout"], 1)
            elif case["class"] in {"disabled", "unavailable"}:
                self.assertEqual(case["adapter_outcome"], case["expected_outcome"])
                self.assertEqual(case["fanout"], 0)
            else:
                self.assertIsNone(case["selected_function"])
                self.assertEqual(case["adapter_outcome"], "unsupported")
                self.assertEqual(case["fanout"], 0)

    def test_declared_pass_or_boundary_booleans_are_rejected_not_trusted(self):
        cases = self.canonical_cases()
        cases[0]["passed"] = True
        cases[0]["boundary_violation"] = False

        with self.assertRaisesRegex(self.pilot.PilotError, "unknown_case_field"):
            self.evaluate_cases(cases)

    def test_wrong_expected_outcome_is_observed_as_failure(self):
        cases = self.canonical_cases()
        self.case(cases, "disabled-analyze")["expected_outcome"] = "ready"

        report = self.evaluate_cases(cases)

        observed = self.case(report["cases"], "disabled-analyze")
        self.assertFalse(observed["passed"])
        self.assertFalse(report["passed"])

    def test_grammar_request_cannot_hide_a_real_boundary_violation(self):
        cases = self.canonical_cases()
        grammar = self.case(cases, "grammar-git")
        grammar["request"] = "Spec Kit analyze requirements"

        report = self.evaluate_cases(cases)

        self.assertFalse(self.case(report["cases"], "grammar-git")["passed"])
        self.assertEqual(report["metrics"]["ownership_escape_count"], 1)
        self.assertFalse(report["passed"])

    def test_real_pilot_proves_canonical_selection_and_zero_load_fallback(self):
        report = self.evaluate_cases(self.canonical_cases())

        self.assertEqual(
            report["evidence_counts"],
            {
                "canonical_success_count": 8,
                "availability_fallback_count": 4,
                "grammar_fallback_count": 12,
            },
        )
        for case in report["cases"]:
            if case["class"] == "success":
                self.assertEqual(case["selected_function"], case["function"])
                self.assertEqual(case["fanout"], 1)
            elif case["class"] == "grammar":
                self.assertIsNone(case["selected_function"])
                self.assertEqual(case["adapter_outcome"], "unsupported")
                self.assertEqual(case["fanout"], 0)
                self.assertFalse(case["artifact_created"])

    def test_success_snapshots_use_derived_input_hash_context_and_synthetic_latency(self):
        report = self.evaluate_cases(self.canonical_cases())

        for function in FUNCTIONS:
            case = self.case(report["cases"], f"success-{function}-en")
            result = json.loads((FIXTURES.parent / case["result_file"]).read_text(encoding="utf-8"))
            self.assertEqual(result["input_hash"], independent_input_hash(function))
            self.assertEqual(
                result["loaded_context_chars"],
                independent_loaded_context_chars(function),
            )
            self.assertEqual(result["elapsed_ms"], 0)

    def test_tampered_snapshot_cost_or_input_identity_is_rejected(self):
        for field, value in (("input_hash", "sha256:" + "0" * 64), ("loaded_context_chars", 1)):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmp:
                    fixtures = self.copy_fixtures(Path(tmp))
                    result_path = fixtures.parent / "results" / "analyze.json"
                    result = json.loads(result_path.read_text(encoding="utf-8"))
                    result[field] = value
                    result["run_id"] = self.pilot.spec_kit_adapter._result_hash(result)
                    result_path.write_text(json.dumps(result), encoding="utf-8")
                    cases = self.pilot.load_cases(fixtures)["cases"]
                    with self.assertRaisesRegex(self.pilot.PilotError, "invalid_result_snapshot"):
                        self.evaluate_cases(cases, result_base=fixtures.parent)

    def test_case_ids_outside_safe_markdown_identifier_are_rejected(self):
        for unsafe in ("Upper-Case", "bad|cell", "line\nbreak", "../escape", "html<script>"):
            with self.subTest(case_id=unsafe):
                cases = self.canonical_cases()
                cases[0]["id"] = unsafe
                with self.assertRaisesRegex(self.pilot.PilotError, "invalid_case"):
                    self.evaluate_cases(cases)

    def test_markdown_table_cells_escape_pipes_controls_and_html(self):
        report = self.evaluate_cases(self.canonical_cases())
        report["cases"][0]["function"] = "analyze|x\n<script>"

        rendered = self.pilot.render_report(report)

        self.assertIn(r"analyze\|x &lt;script&gt;", rendered)
        self.assertNotIn("| analyze|x", rendered)
        self.assertNotIn("<script>", rendered)

    def test_matrix_coverage_and_snapshot_provenance_remain_fail_closed(self):
        cases = self.canonical_cases()
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
            self.evaluate_cases(cases[:-1])

        cases = self.canonical_cases()
        self.case(cases, "success-clarify-en")["result_file"] = "results/does-not-exist.json"
        with self.assertRaisesRegex(self.pilot.PilotError, "unsafe_result_path"):
            self.evaluate_cases(cases)

    def test_metric_denominators_use_reviewed_findings_and_derived_costs(self):
        report = self.evaluate_cases(self.canonical_cases())
        total_chars = sum(independent_loaded_context_chars(function) for function in FUNCTIONS)

        self.assertEqual(report["metrics"]["actionable_value"], 8)
        self.assertEqual(report["metrics"]["false_positive_rate"], 0.1429)
        self.assertEqual(report["metrics"]["native_overlap_rate"], 0.2857)
        self.assertEqual(report["metrics"]["elapsed_ms"], 0)
        self.assertEqual(report["metrics"]["loaded_context_chars"], total_chars * 2)
        self.assertEqual(report["metrics"]["estimated_loaded_tokens"], (total_chars * 2 + 3) // 4)
        for metric in (
            "ownership_escape_count",
            "unauthorized_write_count",
            "template_fanout_violations",
            "false_execution_claims",
        ):
            self.assertEqual(report["metrics"][metric], 0)

    def test_report_is_sorted_and_labels_latency_as_synthetic(self):
        cases = self.canonical_cases()
        report = self.evaluate_cases(list(reversed(cases)))
        rendered = self.pilot.render_report(report)

        self.assertEqual(
            [case["id"] for case in report["cases"]],
            sorted(case["id"] for case in cases),
        )
        self.assertIn("Human decision: pending", rendered)
        self.assertIn("Wider/default activation: prohibited", rendered)
        self.assertIn("Synthetic fixture latency", rendered)
        self.assertIn("real router and adapter", rendered)

    def test_default_cli_is_dry_run_and_write_is_repeat_byte_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            target = root / "specs" / ISSUE_ID / "pilot-report.md"

            dry_run = self.run_cli(root, fixtures)
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertFalse(target.exists())
            self.assertTrue(json.loads(dry_run.stdout)["passed"])

            first = self.run_cli(root, fixtures, "--write")
            self.assertEqual(first.returncode, 0, first.stderr)
            first_bytes = target.read_bytes()
            second = self.run_cli(root, fixtures, "--write")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(target.read_bytes(), first_bytes)

    def test_failed_observation_exits_nonzero_without_replacing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            payload = json.loads(fixtures.read_text(encoding="utf-8"))
            payload["cases"][0]["expected_outcome"] = "ready"
            fixtures.write_text(json.dumps(payload), encoding="utf-8")
            target = root / "specs" / ISSUE_ID / "pilot-report.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserve-me\n")

            result = self.run_cli(root, fixtures, "--write")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_bytes(), b"preserve-me\n")

    def test_cli_parse_and_utf8_errors_use_common_json_envelope_without_traceback(self):
        missing = subprocess.run(
            [sys.executable, str(SCRIPT), "."],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(missing.stderr, "")
        self.assertEqual(
            json.loads(missing.stdout)["schema"], "moduflow.spec-kit-error.v1"
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            fixtures.write_bytes(b"\xff")
            bad_cases = self.run_cli(root, fixtures)
            self.assertEqual(bad_cases.returncode, 2)
            self.assertEqual(bad_cases.stderr, "")
            self.assertEqual(
                json.loads(bad_cases.stdout)["schema"], "moduflow.spec-kit-error.v1"
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            (fixtures.parent / "results" / "analyze.json").write_bytes(b"\xff")
            bad_result = self.run_cli(root, fixtures)
            self.assertEqual(bad_result.returncode, 2)
            self.assertEqual(bad_result.stderr, "")
            self.assertEqual(
                json.loads(bad_result.stdout)["schema"], "moduflow.spec-kit-error.v1"
            )

    def test_direct_write_reexecutes_cases_before_replacing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "specs" / ISSUE_ID / "pilot-report.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserve-me\n")
            report = self.evaluate_cases(self.canonical_cases())
            report["cases"][0]["expected_outcome"] = "ready"

            with self.assertRaisesRegex(self.pilot.PilotError, "invalid_report"):
                self.pilot.write_report(
                    root,
                    report,
                    result_base=FIXTURES.parent,
                    package_root=ROOT,
                )
            self.assertEqual(target.read_bytes(), b"preserve-me\n")

    def test_symlinked_output_ancestor_is_rejected_without_external_write(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            (root / "specs").symlink_to(Path(outside), target_is_directory=True)

            result = self.run_cli(root, fixtures, "--write")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(outside).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
