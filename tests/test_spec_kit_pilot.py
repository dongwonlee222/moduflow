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

    def minimal_case(self, **updates):
        case = {
            "id": "ownership-git-negative",
            "class": "ownership",
            "function": None,
            "boundary": "git",
            "passed": True,
            "findings": [],
            "elapsed_ms": 0,
            "loaded_context_chars": 0,
            "boundary_violation": False,
            "unauthorized_write": False,
            "fanout": 0,
            "false_execution_claim": False,
            "output_artifact": None,
        }
        case.update(updates)
        return case

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
        case = self.minimal_case(
            passed=False,
            boundary_violation=True,
            unauthorized_write=True,
            fanout=2,
            false_execution_claim=True,
        )

        report = self.pilot.evaluate_cases([case])

        self.assertEqual(report["metrics"]["boundary_violations"], 1)
        self.assertEqual(report["metrics"]["unauthorized_writes"], 1)
        self.assertEqual(report["metrics"]["unwanted_fanout"], 1)
        self.assertEqual(report["metrics"]["false_execution_claims"], 1)
        self.assertFalse(report["passed"])

    def test_metrics_use_total_finding_denominator_and_sum_cost(self):
        cases = [
            self.minimal_case(
                id="success-analyze",
                function="analyze",
                boundary=None,
                findings=[
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
                elapsed_ms=25,
                loaded_context_chars=401,
                fanout=1,
                output_artifact="specs/098-speckit-selective-validation-adapter/validation.md",
                **{"class": "success"},
            )
        ]

        report = self.pilot.evaluate_cases(cases)

        self.assertEqual(report["metrics"]["actionable_value"], 1)
        self.assertEqual(report["metrics"]["false_positive_rate"], 0.5)
        self.assertEqual(report["metrics"]["native_overlap_rate"], 0.5)
        self.assertEqual(report["metrics"]["elapsed_ms"], 25)
        self.assertEqual(report["metrics"]["loaded_context_chars"], 401)
        self.assertEqual(report["metrics"]["estimated_loaded_tokens"], 101)

    def test_zero_findings_have_zero_rates(self):
        report = self.pilot.evaluate_cases([self.minimal_case()])

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
        case = self.minimal_case(shell_command="git status")

        with self.assertRaisesRegex(self.pilot.PilotError, "unknown_case_field"):
            self.pilot.evaluate_cases([case])

    def test_malformed_class_function_and_finding_are_rejected(self):
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_class"):
            self.pilot.evaluate_cases([self.minimal_case(**{"class": "executed"})])
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_function"):
            self.pilot.evaluate_cases(
                [self.minimal_case(**{"class": "success", "function": "implement", "boundary": None})]
            )
        finding = {
            "id": "finding-a",
            "summary": "Finding",
            "reviewer_disposition": "approved_without_review",
            "native_overlap": False,
        }
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_finding"):
            self.pilot.evaluate_cases(
                [
                    self.minimal_case(
                        **{
                            "class": "success",
                            "function": "analyze",
                            "boundary": None,
                            "findings": [finding],
                            "fanout": 1,
                            "output_artifact": "specs/098-speckit-selective-validation-adapter/validation.md",
                        }
                    )
                ]
            )

    def test_bool_negative_and_non_numeric_costs_are_rejected(self):
        for field, value in (
            ("elapsed_ms", True),
            ("elapsed_ms", -1),
            ("loaded_context_chars", "10"),
            ("fanout", False),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(self.pilot.PilotError, "invalid_metric"):
                    self.pilot.evaluate_cases([self.minimal_case(**{field: value})])

    def test_duplicate_ids_and_unsafe_output_paths_are_rejected(self):
        case = self.minimal_case()
        with self.assertRaisesRegex(self.pilot.PilotError, "duplicate_case_id"):
            self.pilot.evaluate_cases([case, dict(case)])
        with self.assertRaisesRegex(self.pilot.PilotError, "unsafe_output_path"):
            self.pilot.evaluate_cases(
                [
                    self.minimal_case(
                        **{
                            "class": "success",
                            "function": "analyze",
                            "boundary": None,
                            "fanout": 1,
                            "output_artifact": "../../outside.md",
                        }
                    )
                ]
            )

    def test_report_and_per_function_evidence_are_deterministically_sorted(self):
        cases = self.pilot.load_cases(FIXTURES)["cases"]
        report = self.pilot.evaluate_cases(list(reversed(cases)))

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

    def test_symlinked_output_ancestor_is_rejected_without_external_write(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            (root / "specs").symlink_to(Path(outside), target_is_directory=True)

            result = self.run_cli(root, fixtures, "--write")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_committed_fixture_metrics_are_hand_checked(self):
        report = self.pilot.evaluate_cases(self.pilot.load_cases(FIXTURES)["cases"])

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
