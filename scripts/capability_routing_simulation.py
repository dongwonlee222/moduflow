#!/usr/bin/env python3
"""Offline golden-case simulation for the ModuFlow capability router."""

import argparse
import json
from pathlib import Path

try:
    from scripts import capability_routing
except ImportError:  # Direct execution from scripts/.
    import capability_routing


CASES_SCHEMA = "moduflow.capability-routing-cases.v1"
SIMULATION_SCHEMA = "moduflow.capability-routing-simulation.v1"
METRIC_KEYS = (
    "route_mismatches",
    "adapter_mismatches",
    "unwanted_fanout",
    "permission_violations",
    "false_capability_claims",
    "missing_handoff_fields",
    "semantic_pair_inconsistencies",
)


def load_cases(root):
    path = (
        Path(root).resolve()
        / "tests"
        / "fixtures"
        / "capability-routing"
        / "cases.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != CASES_SCHEMA:
        raise ValueError(f"fixture schema must be {CASES_SCHEMA}")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("fixture cases must be a list")
    return cases


def _projection(actual):
    stages = actual.get("stages") or []
    return {
        "outcome": actual.get("outcome"),
        "adapters": [stage.get("adapter_id") for stage in stages],
        "permissions": [stage.get("permission") for stage in stages],
        "permission_states": [stage.get("permission_state") for stage in stages],
        "availability": [stage.get("availability") for stage in stages],
        "artifacts": [stage.get("output_artifact") for stage in stages],
    }


def _unwanted_fanout(actual):
    outcome = actual.get("outcome")
    stage_count = len(actual.get("stages") or [])
    if outcome == "delegate":
        return int(stage_count != 1)
    if outcome == "sequence":
        return int(stage_count < 2)
    return int(stage_count != 0)


def _permission_violations(case, actual):
    approved = set(case.get("approved_permissions") or [])
    return sum(
        1
        for stage in actual.get("stages") or []
        if stage.get("permission") == "write-external"
        and stage.get("permission_state") == "allowed"
        and "write-external" not in approved
    )


def _false_capability_claims(case, actual):
    expected = case.get("expected") or {}
    expected_availability = dict(
        zip(expected.get("adapters") or [], expected.get("availability") or [])
    )
    false_claims = 0
    for stage in actual.get("stages") or []:
        expected_state = expected_availability.get(stage.get("adapter_id"))
        if expected_state == "unavailable" and (
            stage.get("availability") != "unavailable" or not actual.get("fallback")
        ):
            false_claims += 1
    return false_claims


def _missing_handoff_fields(actual):
    return sum(
        1
        for stage in actual.get("stages") or []
        if capability_routing.REQUIRED_HANDOFF_FIELDS - set(stage)
    )


def evaluate_case(case, actual):
    expected = case["expected"]
    projected = _projection(actual)
    mismatches = []
    metrics = {key: 0 for key in METRIC_KEYS}

    if projected["outcome"] != expected["outcome"]:
        metrics["route_mismatches"] = 1
        mismatches.append(
            f"outcome expected {expected['outcome']!r}, got {projected['outcome']!r}"
        )
    if projected["adapters"] != expected["adapters"]:
        metrics["adapter_mismatches"] = 1
        mismatches.append(
            f"adapters expected {expected['adapters']!r}, got {projected['adapters']!r}"
        )
    for field in ("permissions", "permission_states", "availability", "artifacts"):
        if projected[field] != expected[field]:
            mismatches.append(
                f"{field} expected {expected[field]!r}, got {projected[field]!r}"
            )

    metrics["unwanted_fanout"] = _unwanted_fanout(actual)
    metrics["permission_violations"] = _permission_violations(case, actual)
    metrics["false_capability_claims"] = _false_capability_claims(case, actual)
    metrics["missing_handoff_fields"] = _missing_handoff_fields(actual)
    safety_failures = sum(metrics[key] for key in METRIC_KEYS if key != "semantic_pair_inconsistencies")
    return {
        "id": case["id"],
        "class": case["class"],
        "locale": case["locale"],
        "semantic_pair_id": case.get("semantic_pair_id"),
        "passed": not mismatches and safety_failures == 0,
        "mismatches": mismatches,
        "metrics": metrics,
        "expected": expected,
        "actual": actual,
        "fingerprint": {
            key: projected[key]
            for key in (
                "outcome",
                "adapters",
                "permissions",
                "permission_states",
                "availability",
            )
        },
    }


def _semantic_pair_inconsistencies(results):
    pairs = {}
    for result in results:
        pair_id = result.get("semantic_pair_id")
        if pair_id:
            pairs.setdefault(pair_id, []).append(result)
    count = 0
    for members in pairs.values():
        fingerprints = {
            json.dumps(member["fingerprint"], ensure_ascii=False, sort_keys=True)
            for member in members
        }
        if len(fingerprints) > 1:
            count += 1
    return count


def simulate_cases(root, cases):
    root = Path(root).resolve()
    registry = capability_routing.load_registry(root)
    results = []
    for case in cases:
        actual = capability_routing.route_request(
            case["request"],
            registry,
            issue_id=case["issue_id"],
            availability=case.get("availability") or {},
            approved_permissions=set(case.get("approved_permissions") or []),
        )
        results.append(evaluate_case(case, actual))

    metrics = {key: 0 for key in METRIC_KEYS}
    for result in results:
        for key in METRIC_KEYS:
            metrics[key] += result["metrics"][key]
    metrics["semantic_pair_inconsistencies"] = _semantic_pair_inconsistencies(results)
    failed = sum(1 for result in results if not result["passed"])
    return {
        "schema": SIMULATION_SCHEMA,
        "total": len(results),
        "passed": len(results) - failed,
        "failed": failed,
        "metrics": metrics,
        "cases": results,
    }


def write_report(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def main():
    parser = argparse.ArgumentParser(
        description="Run offline ModuFlow capability routing simulations."
    )
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_path).resolve()
    report = simulate_cases(root, load_cases(root))
    if args.write:
        write_report(
            root
            / "specs"
            / "097-single-entry-capability-routing-contract"
            / "simulation-report.json",
            report,
        )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return int(report["failed"] > 0 or any(report["metrics"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
