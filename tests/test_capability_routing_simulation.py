import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMULATION_PATH = ROOT / "scripts" / "capability_routing_simulation.py"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "capability-routing" / "cases.json"


def load_simulation(testcase):
    testcase.assertTrue(
        SIMULATION_PATH.exists(),
        "scripts/capability_routing_simulation.py must exist",
    )
    spec = importlib.util.spec_from_file_location(
        "capability_routing_simulation", SIMULATION_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def registry_for(simulation):
    return simulation.capability_routing.load_registry(ROOT)


def fixture_cases():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]


class CapabilityRoutingSimulationTests(unittest.TestCase):
    def test_committed_fixture_corpus_has_eight_classes_and_24_cases(self):
        cases = fixture_cases()

        self.assertGreaterEqual(len(cases), 24)
        self.assertEqual(
            {case["class"] for case in cases},
            {
                "lifecycle",
                "analytics",
                "design",
                "implementation",
                "overlap",
                "unavailable",
                "external-write",
                "multi-stage",
            },
        )
        pairs = {}
        for case in cases:
            if case.get("semantic_pair_id"):
                pairs.setdefault(case["semantic_pair_id"], set()).add(case["locale"])
        self.assertTrue(all(locales == {"ko-KR", "en-US"} for locales in pairs.values()))

    def test_simulation_has_zero_mismatches_and_safety_failures(self):
        simulation = load_simulation(self)

        report = simulation.simulate_cases(ROOT, fixture_cases())

        self.assertGreaterEqual(report["total"], 24)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["passed"], report["total"])
        self.assertTrue(all(value == 0 for value in report["metrics"].values()))

    def test_changed_expected_adapter_is_not_silently_accepted(self):
        simulation = load_simulation(self)
        cases = copy.deepcopy(fixture_cases())
        cases[3]["expected"]["adapters"] = ["product-design"]

        report = simulation.simulate_cases(ROOT, cases)

        self.assertEqual(report["metrics"]["adapter_mismatches"], 1)
        self.assertEqual(report["failed"], 1)

    def test_safety_metrics_are_independent_of_expected_values(self):
        simulation = load_simulation(self)
        case = copy.deepcopy(next(item for item in fixture_cases() if item["id"] == "P01-ko-posthog"))
        actual = {
            "outcome": "delegate",
            "stages": [
                {
                    "adapter_id": "data-analytics",
                    "reason_code": "trigger_match",
                    "permission": "write-external",
                    "permission_state": "allowed",
                    "availability": "available",
                    "gate_after": None
                },
                {
                    "adapter_id": "product-design",
                    "reason_code": "trigger_match",
                    "permission": "write-local",
                    "permission_state": "allowed",
                    "availability": "available",
                    "output_artifact": "specs/097-single-entry-capability-routing-contract/design-brief.md",
                    "gate_after": None
                }
            ],
            "fallback": None
        }

        result = simulation.evaluate_case(case, actual, registry_for(simulation))

        self.assertEqual(result["metrics"]["unwanted_fanout"], 1)
        self.assertEqual(result["metrics"]["permission_violations"], 1)
        self.assertEqual(result["metrics"]["missing_handoff_fields"], 1)

    def test_unavailable_capability_cannot_claim_ready(self):
        simulation = load_simulation(self)
        case = copy.deepcopy(next(item for item in fixture_cases() if item["id"] == "U02-en-analytics"))
        actual = {
            "outcome": "delegate",
            "stages": [{
                "adapter_id": "data-analytics",
                "reason_code": "trigger_match",
                "permission": "read",
                "permission_state": "allowed",
                "availability": "available",
                "output_artifact": "specs/097-single-entry-capability-routing-contract/analysis.md",
                "gate_after": None
            }],
            "fallback": None
        }

        case["expected"]["availability"] = ["available"]
        result = simulation.evaluate_case(case, actual, registry_for(simulation))

        self.assertEqual(result["metrics"]["false_capability_claims"], 1)

    def test_permission_metric_ignores_mutated_expected_and_actual_labels(self):
        simulation = load_simulation(self)
        case = copy.deepcopy(next(item for item in fixture_cases() if item["id"] == "P01-ko-posthog"))
        case["expected"]["permissions"] = ["read"]
        case["expected"]["permission_states"] = ["allowed"]
        actual = {
            "outcome": "delegate",
            "stages": [{
                "adapter_id": "data-analytics",
                "reason_code": "trigger_match",
                "permission": "read",
                "permission_state": "allowed",
                "availability": "available",
                "output_artifact": "specs/097-single-entry-capability-routing-contract/analysis.md",
                "gate_after": None,
            }],
            "fallback": None,
        }

        result = simulation.evaluate_case(case, actual, registry_for(simulation))

        self.assertEqual(result["metrics"]["permission_violations"], 1)

    def test_semantic_pair_drift_is_reported(self):
        simulation = load_simulation(self)
        cases = copy.deepcopy(fixture_cases())
        target = next(item for item in cases if item["id"] == "A02-en-conversion")
        target["request"] = "Implement the payment API"

        report = simulation.simulate_cases(ROOT, cases)

        self.assertEqual(report["metrics"]["semantic_pair_inconsistencies"], 1)
        self.assertEqual(
            report["semantic_pair_findings"],
            [{
                "pair_id": "analytics-conversion",
                "case_ids": ["A01-ko-conversion", "A02-en-conversion"],
            }],
        )
        self.assertEqual(report["failed"], 2)
        by_id = {case["id"]: case for case in report["cases"]}
        self.assertFalse(by_id["A01-ko-conversion"]["passed"])
        self.assertFalse(by_id["A02-en-conversion"]["passed"])

    def test_report_write_is_byte_stable(self):
        simulation = load_simulation(self)
        report = simulation.simulate_cases(ROOT, fixture_cases())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"

            simulation.write_report(path, report)
            first = path.read_bytes()
            simulation.write_report(path, report)

            self.assertEqual(path.read_bytes(), first)

    def test_cli_prints_passing_report(self):
        completed = subprocess.run(
            [sys.executable, str(SIMULATION_PATH), str(ROOT)],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(completed.stdout.strip(), "simulation CLI must print JSON")
        report = json.loads(completed.stdout)
        self.assertEqual(report["failed"], 0)


if __name__ == "__main__":
    unittest.main()
