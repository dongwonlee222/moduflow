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


def load_module():
    spec = importlib.util.spec_from_file_location("spec_kit_pilot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SpecKitPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pilot = load_module()

    def canonical_cases(self):
        return json.loads(json.dumps(self.pilot.load_cases(FIXTURES)["cases"]))

    def evaluate_cases(self, cases, result_base=FIXTURES.parent):
        return self.pilot.evaluate_cases(cases, result_base=result_base)

    def evaluate_with_result_updates(self, updates):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures = self.copy_fixtures(Path(tmp))
            for function, values in updates.items():
                result_path = fixtures.parent / "results" / f"{function}.json"
                result = json.loads(result_path.read_text(encoding="utf-8"))
                result.update(values)
                result["run_id"] = self.pilot.spec_kit_adapter._result_hash(result)
                result_path.write_text(json.dumps(result), encoding="utf-8")
            cases = self.pilot.load_cases(fixtures)["cases"]
            return self.evaluate_cases(cases, result_base=fixtures.parent)

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

    def test_fixture_matrix_covers_functions_fallbacks_and_ownership_boundaries(self):
        payload = self.pilot.load_cases(FIXTURES)
        cases = payload["cases"]
        functions = {case["function"] for case in cases if case["class"] == "success"}

        self.assertEqual(len(cases), 13)
        self.assertEqual(functions, {"clarify", "analyze", "checklist", "converge"})
        self.assertEqual(sum(case["class"] == "success" for case in cases), 4)
        self.assertGreaterEqual(
            sum(case["class"] in {"disabled", "unavailable"} for case in cases), 4
        )
        self.assertEqual(
            {"implementation", "lifecycle", "git", "review", "release"}
            - {case["boundary"] for case in cases if case["class"] == "ownership"},
            set(),
        )

    def test_pilot_fails_when_any_boundary_metric_is_nonzero(self):
        cases = self.canonical_cases()
        case = self.case(cases, "ownership-git")
        case.update(
            passed=False,
            boundary_violation=True,
            unauthorized_write=True,
            false_execution_claim=True,
        )

        report = self.evaluate_cases(cases)

        self.assertEqual(report["metrics"]["boundary_violations"], 1)
        self.assertEqual(report["metrics"]["unauthorized_writes"], 1)
        self.assertEqual(report["metrics"]["unwanted_fanout"], 0)
        self.assertEqual(report["metrics"]["false_execution_claims"], 1)
        self.assertFalse(report["passed"])

    def test_metrics_use_total_finding_denominator_and_sum_cost(self):
        updates = {
            function: {
                "findings": [],
                "native_overlap": [],
                "elapsed_ms": 0,
                "loaded_context_chars": 0,
            }
            for function in ("clarify", "analyze", "checklist", "converge")
        }
        updates["analyze"] = {
            "findings": [
                {
                    "id": "finding-a",
                    "summary": "Unique useful finding",
                    "reviewer_disposition": "useful_unique",
                    "native_overlap": False,
                },
                {
                    "id": "finding-b",
                    "summary": "Invalid finding",
                    "reviewer_disposition": "rejected_invalid",
                    "native_overlap": True,
                },
            ],
            "native_overlap": ["finding-b"],
            "elapsed_ms": 25,
            "loaded_context_chars": 401,
        }

        report = self.evaluate_with_result_updates(updates)

        self.assertEqual(report["metrics"]["actionable_value"], 1)
        self.assertEqual(report["metrics"]["false_positive_rate"], 0.5)
        self.assertEqual(report["metrics"]["native_overlap_rate"], 0.5)
        self.assertEqual(report["metrics"]["elapsed_ms"], 25)
        self.assertEqual(report["metrics"]["loaded_context_chars"], 401)
        self.assertEqual(report["metrics"]["estimated_loaded_tokens"], 101)

    def test_zero_findings_have_zero_rates(self):
        report = self.evaluate_with_result_updates(
            {
                function: {"findings": [], "native_overlap": []}
                for function in ("clarify", "analyze", "checklist", "converge")
            }
        )

        self.assertEqual(report["metrics"]["false_positive_rate"], 0.0)
        self.assertEqual(report["metrics"]["native_overlap_rate"], 0.0)

    def test_committed_results_are_strict_validated_snapshots(self):
        payload = self.pilot.load_cases(FIXTURES)
        success = [case for case in payload["cases"] if case["class"] == "success"]

        self.assertEqual(len(success), 4)
        self.assertTrue(all(case["result_file"].startswith("results/") for case in success))
        self.assertTrue(all(case["findings"] for case in success))
        self.assertTrue(all(case["elapsed_ms"] > 0 for case in success))
        self.assertTrue(all(case["loaded_context_chars"] > 0 for case in success))

    def test_unknown_case_field_is_rejected(self):
        cases = self.canonical_cases()
        cases[0]["shell_command"] = "git status"

        with self.assertRaisesRegex(self.pilot.PilotError, "unknown_case_field"):
            self.evaluate_cases(cases)

    def test_malformed_class_function_and_finding_are_rejected(self):
        cases = self.canonical_cases()
        cases[0]["class"] = "executed"
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_class"):
            self.evaluate_cases(cases)

        cases = self.canonical_cases()
        self.case(cases, "success-analyze")["function"] = "implement"
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_function"):
            self.evaluate_cases(cases)
        finding = {
            "id": "finding-a",
            "summary": "Finding",
            "reviewer_disposition": "approved_without_review",
            "native_overlap": False,
        }
        cases = self.canonical_cases()
        self.case(cases, "success-analyze")["findings"] = [finding]
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_finding"):
            self.evaluate_cases(cases)

    def test_bool_negative_and_non_numeric_costs_are_rejected(self):
        for field, value in (
            ("elapsed_ms", True),
            ("elapsed_ms", -1),
            ("loaded_context_chars", "10"),
            ("fanout", False),
        ):
            with self.subTest(field=field, value=value):
                cases = self.canonical_cases()
                cases[0][field] = value
                with self.assertRaisesRegex(self.pilot.PilotError, "invalid_metric"):
                    self.evaluate_cases(cases)

    def test_duplicate_ids_and_unsafe_output_paths_are_rejected(self):
        cases = self.canonical_cases()
        with self.assertRaisesRegex(self.pilot.PilotError, "duplicate_case_id"):
            self.evaluate_cases(cases + [dict(cases[0])])
        cases = self.canonical_cases()
        self.case(cases, "success-analyze")["output_artifact"] = "../../outside.md"
        with self.assertRaisesRegex(self.pilot.PilotError, "unsafe_output_path"):
            self.evaluate_cases(cases)

    def test_reduced_matrix_is_rejected_before_evaluation(self):
        cases = self.canonical_cases()

        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
            self.evaluate_cases(cases[:-1])

    def test_success_matrix_requires_one_result_for_each_function(self):
        cases = self.canonical_cases()
        self.case(cases, "success-clarify")["result_file"] = None
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
            self.evaluate_cases(cases)

        cases = [case for case in self.canonical_cases() if case["id"] != "success-clarify"]
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
            self.evaluate_cases(cases)

    def test_fallback_matrix_covers_all_functions_without_result_or_fanout(self):
        cases = [
            case
            for case in self.canonical_cases()
            if case["id"] != "unavailable-checklist"
        ]
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
            self.evaluate_cases(cases)

        cases = self.canonical_cases()
        self.case(cases, "disabled-analyze")["fanout"] = 1
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
            self.evaluate_cases(cases)

    def test_ownership_matrix_covers_all_boundaries_without_result_or_fanout(self):
        cases = [case for case in self.canonical_cases() if case["id"] != "ownership-git"]
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
            self.evaluate_cases(cases)

        cases = self.canonical_cases()
        self.case(cases, "ownership-review")["fanout"] = 1
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
            self.evaluate_cases(cases)

    def test_report_and_per_function_evidence_are_deterministically_sorted(self):
        cases = self.pilot.load_cases(FIXTURES)["cases"]
        report = self.evaluate_cases(list(reversed(cases)))

        self.assertEqual([case["id"] for case in report["cases"]], sorted(case["id"] for case in cases))
        self.assertEqual(list(report["per_function"]), sorted(report["per_function"]))
        rendered = self.pilot.render_report(report)
        positions = [rendered.index(case["id"]) for case in report["cases"]]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Human decision: pending", rendered)
        self.assertIn("Wider/default activation: prohibited", rendered)
        self.assertIn("deterministic offline evidence", rendered)

    def test_default_cli_is_dry_run_and_write_is_repeat_byte_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            target = root / "specs" / "098-speckit-selective-validation-adapter" / "pilot-report.md"

            dry_run = self.run_cli(root, fixtures)

            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertFalse(target.exists())
            payload = json.loads(dry_run.stdout)
            self.assertTrue(payload["passed"])

            first = self.run_cli(root, fixtures, "--write")
            self.assertEqual(first.returncode, 0, first.stderr)
            first_bytes = target.read_bytes()
            second = self.run_cli(root, fixtures, "--write")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(target.read_bytes(), first_bytes)

    def test_safety_failure_exits_nonzero_without_replacing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            payload = json.loads(fixtures.read_text(encoding="utf-8"))
            payload["cases"][0]["passed"] = False
            payload["cases"][0]["boundary_violation"] = True
            fixtures.write_text(json.dumps(payload), encoding="utf-8")
            target = root / "specs" / "098-speckit-selective-validation-adapter" / "pilot-report.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserve-me\n")

            result = self.run_cli(root, fixtures, "--write")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_bytes(), b"preserve-me\n")

    def test_reduced_matrix_cli_exits_nonzero_without_replacing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            payload = json.loads(fixtures.read_text(encoding="utf-8"))
            payload["cases"] = payload["cases"][:-1]
            fixtures.write_text(json.dumps(payload), encoding="utf-8")
            target = root / "specs" / "098-speckit-selective-validation-adapter" / "pilot-report.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserve-me\n")

            result = self.run_cli(root, fixtures, "--write")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_bytes(), b"preserve-me\n")

    def test_direct_write_revalidates_matrix_before_replacing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "specs" / "098-speckit-selective-validation-adapter" / "pilot-report.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserve-me\n")
            report = self.evaluate_cases(self.canonical_cases())
            report["cases"] = report["cases"][:-1]

            with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
                self.pilot.write_report(root, report, result_base=FIXTURES.parent)

            self.assertEqual(target.read_bytes(), b"preserve-me\n")

    def test_direct_evaluate_rejects_nonexistent_success_snapshots(self):
        cases = self.canonical_cases()
        for case in cases:
            if case["class"] == "success":
                case["result_file"] = "results/does-not-exist.json"

        with self.assertRaisesRegex(self.pilot.PilotError, "result_base_required"):
            self.pilot.evaluate_cases(cases)
        with self.assertRaisesRegex(self.pilot.PilotError, "unsafe_result_path"):
            self.evaluate_cases(cases)

    def test_direct_write_preserves_existing_report_for_nonexistent_success_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "specs" / "098-speckit-selective-validation-adapter" / "pilot-report.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserve-me\n")
            report = self.evaluate_cases(self.canonical_cases())
            for case in report["cases"]:
                if case["class"] == "success":
                    case["result_file"] = "results/does-not-exist.json"

            with self.assertRaisesRegex(self.pilot.PilotError, "result_base_required"):
                self.pilot.write_report(root, report)
            self.assertEqual(target.read_bytes(), b"preserve-me\n")
            with self.assertRaisesRegex(self.pilot.PilotError, "unsafe_result_path"):
                self.pilot.write_report(root, report, result_base=FIXTURES.parent)

            self.assertEqual(target.read_bytes(), b"preserve-me\n")

    def test_symlinked_output_ancestor_is_rejected_without_external_write(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            (root / "specs").symlink_to(Path(outside), target_is_directory=True)

            result = self.run_cli(root, fixtures, "--write")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_committed_fixture_metrics_are_hand_checked(self):
        report = self.evaluate_cases(self.pilot.load_cases(FIXTURES)["cases"])

        self.assertEqual(report["total_cases"], 13)
        self.assertEqual(report["passed_cases"], 13)
        self.assertEqual(report["metrics"]["actionable_value"], 4)
        self.assertEqual(report["metrics"]["false_positive_rate"], 0.1429)
        self.assertEqual(report["metrics"]["native_overlap_rate"], 0.2857)
        self.assertEqual(report["metrics"]["elapsed_ms"], 72)
        self.assertEqual(report["metrics"]["loaded_context_chars"], 8000)
        self.assertEqual(report["metrics"]["estimated_loaded_tokens"], 2000)
        for metric in (
            "boundary_violations",
            "unauthorized_writes",
            "unwanted_fanout",
            "false_execution_claims",
        ):
            self.assertEqual(report["metrics"][metric], 0)
        self.assertTrue(report["passed"])


if __name__ == "__main__":
    unittest.main()
