#!/usr/bin/env python3
"""Evaluate deterministic, offline evidence for the selective Spec Kit pilot."""

import argparse
import json
import math
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import spec_kit_adapter


PILOT_SCHEMA = "moduflow.spec-kit-pilot.v1"
CASES_SCHEMA = "moduflow.spec-kit-pilot-cases.v1"
ISSUE_ID = "098-speckit-selective-validation-adapter"
FUNCTIONS = {"clarify", "analyze", "checklist", "converge"}
CLASSES = {"success", "disabled", "unavailable", "ownership"}
BOUNDARIES = {"implementation", "lifecycle", "git", "review", "release"}
DISPOSITIONS = {"useful_unique", "accepted_native", "rejected_invalid"}
CASE_KEYS = {
    "id",
    "class",
    "function",
    "boundary",
    "passed",
    "result_file",
    "findings",
    "elapsed_ms",
    "loaded_context_chars",
    "boundary_violation",
    "unauthorized_write",
    "fanout",
    "false_execution_claim",
    "output_artifact",
}
CASE_REQUIRED = {
    "id",
    "class",
    "function",
    "boundary",
    "passed",
    "boundary_violation",
    "unauthorized_write",
    "fanout",
    "false_execution_claim",
    "output_artifact",
}
FINDING_KEYS = {"id", "summary", "reviewer_disposition", "native_overlap"}
REPORT_RELATIVE_PATH = Path("specs") / ISSUE_ID / "pilot-report.md"


class PilotError(ValueError):
    """A fail-closed pilot input or output error safe to expose to a caller."""

    def __init__(self, code, message):
        self.code = code
        self.safe_message = message
        super().__init__(f"{code}: {message}")


def _error(code, message):
    raise PilotError(code, message)


def safe_ratio(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else 0.0


def _strict_non_negative_int(value, field):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        _error("invalid_metric", f"{field} must be a non-negative integer")
    return value


def _validate_finding(finding):
    if not isinstance(finding, dict) or set(finding) != FINDING_KEYS:
        _error("invalid_finding", "finding must contain exactly the approved fields")
    if not isinstance(finding["id"], str) or not finding["id"].strip():
        _error("invalid_finding", "finding id must be a non-empty string")
    if not isinstance(finding["summary"], str) or not finding["summary"].strip():
        _error("invalid_finding", "finding summary must be a non-empty string")
    if finding["reviewer_disposition"] not in DISPOSITIONS:
        _error("invalid_finding", "reviewer disposition is unsupported")
    if not isinstance(finding["native_overlap"], bool):
        _error("invalid_finding", "native_overlap must be boolean")
    return json.loads(json.dumps(finding, ensure_ascii=False))


def _contained_file(base_dir, relative_name):
    if not isinstance(relative_name, str) or not relative_name.strip():
        _error("unsafe_result_path", "result_file must be a non-empty relative path")
    relative = Path(relative_name)
    if relative.is_absolute() or ".." in relative.parts:
        _error("unsafe_result_path", "result_file must remain under the fixture directory")
    base = Path(base_dir).resolve()
    candidate = Path(base_dir)
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            _error("unsafe_result_path", "result_file path must not contain symlinks")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(base)
    except (OSError, ValueError) as exc:
        raise PilotError(
            "unsafe_result_path", "result_file must be a readable file under the fixture directory"
        ) from exc
    if not resolved.is_file():
        _error("unsafe_result_path", "result_file must be a regular file")
    return resolved


def _load_result(base_dir, relative_name):
    path = _contained_file(base_dir, relative_name)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return spec_kit_adapter.validate_result_shape(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotError("invalid_result_snapshot", "result snapshot cannot be read") from exc
    except spec_kit_adapter.SpecKitAdapterError as exc:
        raise PilotError("invalid_result_snapshot", exc.safe_message) from exc


def _validate_output_path(value, case_class):
    if case_class != "success":
        if value is not None:
            _error("unsafe_output_path", "only success evidence may name an advisory output")
        return None
    expected = f"specs/{ISSUE_ID}/validation.md"
    if value != expected:
        _error("unsafe_output_path", f"success output_artifact must be {expected}")
    return value


def _normalize_case(case, result_base=None):
    if not isinstance(case, dict):
        _error("invalid_case", "each case must be an object")
    unknown = set(case) - CASE_KEYS
    if unknown:
        _error("unknown_case_field", "case contains unsupported fields")
    missing = CASE_REQUIRED - set(case)
    if missing:
        _error("invalid_case", "case is missing required fields")

    case_id = case["id"]
    if not isinstance(case_id, str) or not case_id.strip():
        _error("invalid_case", "case id must be a non-empty string")
    case_class = case["class"]
    if case_class not in CLASSES:
        _error("invalid_class", "case class is unsupported")
    function = case["function"]
    boundary = case["boundary"]
    if case_class == "ownership":
        if function is not None or boundary not in BOUNDARIES:
            _error("invalid_function", "ownership cases require one approved boundary and no function")
    else:
        if function not in FUNCTIONS or boundary is not None:
            _error("invalid_function", "function cases require one approved function and no boundary")

    for field in ("passed", "boundary_violation", "unauthorized_write", "false_execution_claim"):
        if not isinstance(case[field], bool):
            _error("invalid_case", f"{field} must be boolean")
    fanout = _strict_non_negative_int(case["fanout"], "fanout")
    output_artifact = _validate_output_path(case["output_artifact"], case_class)

    result_file = case.get("result_file")
    findings = case.get("findings")
    elapsed_ms = case.get("elapsed_ms")
    loaded_context_chars = case.get("loaded_context_chars")
    if result_file is not None:
        if case_class != "success":
            _error("invalid_result_snapshot", "only success cases may reference a result snapshot")
        if result_base is not None:
            result = _load_result(result_base, result_file)
            if result["issue_id"] != ISSUE_ID or result["function"] != function:
                _error("invalid_result_snapshot", "result issue/function does not match its case")
            snapshot_values = (
                result["findings"],
                result["elapsed_ms"],
                result["loaded_context_chars"],
            )
            supplied_values = (findings, elapsed_ms, loaded_context_chars)
            if any(value is not None for value in supplied_values) and supplied_values != snapshot_values:
                _error("invalid_result_snapshot", "case metrics must match the result snapshot")
            findings, elapsed_ms, loaded_context_chars = snapshot_values
        elif findings is None or elapsed_ms is None or loaded_context_chars is None:
            _error("invalid_result_snapshot", "loaded result evidence is incomplete")

    findings = [] if findings is None else findings
    elapsed_ms = 0 if elapsed_ms is None else elapsed_ms
    loaded_context_chars = 0 if loaded_context_chars is None else loaded_context_chars
    if not isinstance(findings, list):
        _error("invalid_finding", "findings must be a list")
    normalized_findings = [_validate_finding(finding) for finding in findings]
    finding_ids = [finding["id"] for finding in normalized_findings]
    if len(finding_ids) != len(set(finding_ids)):
        _error("invalid_finding", "finding ids must be unique within a case")
    elapsed_ms = _strict_non_negative_int(elapsed_ms, "elapsed_ms")
    loaded_context_chars = _strict_non_negative_int(
        loaded_context_chars, "loaded_context_chars"
    )
    if case_class != "success" and (
        normalized_findings or elapsed_ms or loaded_context_chars or result_file is not None
    ):
        _error("invalid_case", "fallback and ownership cases cannot claim model results or cost")

    return {
        "id": case_id,
        "class": case_class,
        "function": function,
        "boundary": boundary,
        "passed": case["passed"],
        "result_file": result_file,
        "findings": normalized_findings,
        "elapsed_ms": elapsed_ms,
        "loaded_context_chars": loaded_context_chars,
        "boundary_violation": case["boundary_violation"],
        "unauthorized_write": case["unauthorized_write"],
        "fanout": fanout,
        "false_execution_claim": case["false_execution_claim"],
        "output_artifact": output_artifact,
    }


def load_cases(path):
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotError("invalid_cases", "case matrix cannot be read") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema", "cases"}:
        _error("invalid_cases", "case matrix must contain exactly schema and cases")
    if payload["schema"] != CASES_SCHEMA or not isinstance(payload["cases"], list):
        _error("invalid_cases", "case matrix schema or cases is invalid")
    cases = [_normalize_case(case, path.parent) for case in payload["cases"]]
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        _error("duplicate_case_id", "case ids must be unique")
    _validate_matrix(cases)
    return {"schema": CASES_SCHEMA, "cases": cases}


def _validate_matrix(cases):
    """Require the complete approved pilot matrix before metrics or writes."""
    if len(cases) < 13:
        _error("invalid_matrix", "pilot matrix must contain at least 13 cases")

    success = [case for case in cases if case["class"] == "success"]
    success_functions = [case["function"] for case in success]
    if len(success) != len(FUNCTIONS) or any(
        success_functions.count(function) != 1 for function in FUNCTIONS
    ):
        _error(
            "invalid_matrix",
            "pilot matrix requires exactly one success for each approved function",
        )
    if any(
        not isinstance(case["result_file"], str)
        or not case["result_file"].strip()
        or case["fanout"] != 1
        for case in success
    ):
        _error(
            "invalid_matrix",
            "success cases require one result snapshot and exactly one loaded template",
        )

    fallbacks = [
        case for case in cases if case["class"] in {"disabled", "unavailable"}
    ]
    if len(fallbacks) < 4 or {case["function"] for case in fallbacks} != FUNCTIONS:
        _error(
            "invalid_matrix",
            "fallback cases must cover all four approved functions",
        )
    if any(case["result_file"] is not None or case["fanout"] != 0 for case in fallbacks):
        _error(
            "invalid_matrix",
            "disabled and unavailable cases cannot claim results or template fan-out",
        )

    ownership = [case for case in cases if case["class"] == "ownership"]
    if {case["boundary"] for case in ownership} != BOUNDARIES:
        _error(
            "invalid_matrix",
            "ownership cases must cover implementation, lifecycle, Git, review, and release",
        )
    if any(
        case["function"] is not None
        or case["result_file"] is not None
        or case["fanout"] != 0
        for case in ownership
    ):
        _error(
            "invalid_matrix",
            "ownership cases cannot claim a function, result, or template fan-out",
        )


def _function_metrics(cases):
    per_function = {}
    for function in sorted(FUNCTIONS):
        selected = [case for case in cases if case["class"] == "success" and case["function"] == function]
        findings = [finding for case in selected for finding in case["findings"]]
        total = len(findings)
        chars = sum(case["loaded_context_chars"] for case in selected)
        per_function[function] = {
            "cases": len(selected),
            "findings": total,
            "actionable_value": sum(
                finding["reviewer_disposition"] == "useful_unique" for finding in findings
            ),
            "elapsed_ms": sum(case["elapsed_ms"] for case in selected),
            "loaded_context_chars": chars,
            "estimated_loaded_tokens": math.ceil(chars / 4),
            "false_positive_rate": safe_ratio(
                sum(finding["reviewer_disposition"] == "rejected_invalid" for finding in findings),
                total,
            ),
            "native_overlap_rate": safe_ratio(
                sum(finding["native_overlap"] for finding in findings), total
            ),
        }
    return per_function


def evaluate_cases(cases):
    if not isinstance(cases, list):
        _error("invalid_cases", "cases must be a list")
    normalized = [_normalize_case(case) for case in cases]
    ids = [case["id"] for case in normalized]
    if len(ids) != len(set(ids)):
        _error("duplicate_case_id", "case ids must be unique")
    _validate_matrix(normalized)
    normalized.sort(key=lambda case: case["id"])
    findings = [finding for case in normalized for finding in case["findings"]]
    total_findings = len(findings)
    loaded_chars = sum(case["loaded_context_chars"] for case in normalized)
    safety = {
        "boundary_violations": sum(case["boundary_violation"] for case in normalized),
        "unauthorized_writes": sum(case["unauthorized_write"] for case in normalized),
        "unwanted_fanout": sum(case["fanout"] > 1 for case in normalized),
        "false_execution_claims": sum(case["false_execution_claim"] for case in normalized),
    }
    metrics = {
        "actionable_value": sum(
            finding["reviewer_disposition"] == "useful_unique" for finding in findings
        ),
        "elapsed_ms": sum(case["elapsed_ms"] for case in normalized),
        "loaded_context_chars": loaded_chars,
        "estimated_loaded_tokens": math.ceil(loaded_chars / 4),
        "false_positive_rate": safe_ratio(
            sum(finding["reviewer_disposition"] == "rejected_invalid" for finding in findings),
            total_findings,
        ),
        "native_overlap_rate": safe_ratio(
            sum(finding["native_overlap"] for finding in findings), total_findings
        ),
        **safety,
    }
    passed_cases = sum(case["passed"] for case in normalized)
    return {
        "schema": PILOT_SCHEMA,
        "total_cases": len(normalized),
        "passed_cases": passed_cases,
        "passed": passed_cases == len(normalized) and not any(safety.values()),
        "metrics": metrics,
        "per_function": _function_metrics(normalized),
        "cases": normalized,
    }


def render_report(report):
    metrics = report["metrics"]
    lines = [
        "# Spec Kit Selective Validation Pilot Report",
        "",
        "Issue: `098-speckit-selective-validation-adapter`",
        "Evidence type: deterministic offline evidence snapshots; no live model or Spec Kit CLI execution.",
        "Human decision: pending",
        "Wider/default activation: prohibited",
        "",
        "## Outcome",
        "",
        f"- Pilot passed: `{'yes' if report['passed'] else 'no'}`",
        f"- Cases: `{report['passed_cases']}/{report['total_cases']}` passed",
        "",
        "## Aggregate Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Actionable unique findings | {metrics['actionable_value']} |",
        f"| Elapsed time (ms) | {metrics['elapsed_ms']} |",
        f"| Loaded context (characters) | {metrics['loaded_context_chars']} |",
        f"| Estimated loaded context (tokens) | {metrics['estimated_loaded_tokens']} |",
        f"| False-positive rate | {metrics['false_positive_rate']:.4f} |",
        f"| Native-overlap rate | {metrics['native_overlap_rate']:.4f} |",
        f"| Boundary violations | {metrics['boundary_violations']} |",
        f"| Unauthorized writes | {metrics['unauthorized_writes']} |",
        f"| Unwanted fan-out | {metrics['unwanted_fanout']} |",
        f"| False execution claims | {metrics['false_execution_claims']} |",
        "",
        "## Per-Function Evidence",
        "",
        "| Function | Findings | Unique | Elapsed ms | Chars | Tokens | False positive | Native overlap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for function, evidence in report["per_function"].items():
        lines.append(
            f"| {function} | {evidence['findings']} | {evidence['actionable_value']} | "
            f"{evidence['elapsed_ms']} | {evidence['loaded_context_chars']} | "
            f"{evidence['estimated_loaded_tokens']} | {evidence['false_positive_rate']:.4f} | "
            f"{evidence['native_overlap_rate']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Case Evidence",
            "",
            "| Case | Class | Function / boundary | Passed |",
            "| --- | --- | --- | --- |",
        ]
    )
    for case in report["cases"]:
        subject = case["function"] or case["boundary"]
        lines.append(
            f"| {case['id']} | {case['class']} | {subject} | "
            f"{'yes' if case['passed'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Decision Boundary",
            "",
            "Deterministic checks prove fixture integrity, bounded cost accounting, and zero recorded safety violations.",
            "Reviewer dispositions are committed pilot evidence, but the human value/activation decision remains pending.",
            "The next command is `product:review 098-speckit-selective-validation-adapter`.",
            "",
        ]
    )
    return "\n".join(lines)


def _contained_under_root(root, path, code):
    root = Path(root).resolve()
    lexical = Path(path)
    current = Path(root)
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise PilotError(code, "path must remain under the target project") from exc
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            _error(code, "path must not contain symlinks")
    try:
        lexical.resolve().relative_to(root)
    except ValueError as exc:
        raise PilotError(code, "path escapes the target project") from exc
    return lexical


def _contained_fixture_path(root, fixtures):
    root = Path(root).resolve()
    fixtures = Path(fixtures)
    if not fixtures.is_absolute():
        fixtures = root / fixtures
    try:
        fixtures = fixtures.resolve(strict=True)
        fixtures.relative_to(root)
    except (OSError, ValueError) as exc:
        raise PilotError(
            "unsafe_fixture_path", "fixture matrix must remain under the target project"
        ) from exc
    fixtures = _contained_under_root(root, fixtures, "unsafe_fixture_path")
    if not fixtures.is_file():
        _error("unsafe_fixture_path", "fixture matrix must be a regular file")
    return fixtures


def _report_target(root):
    root = Path(root).resolve()
    return _contained_under_root(root, root / REPORT_RELATIVE_PATH, "unsafe_output_path")


def write_report(root, report):
    if not isinstance(report, dict) or "cases" not in report:
        _error("invalid_report", "pilot report must contain evaluated cases")
    validated_report = evaluate_cases(report["cases"])
    if report != validated_report:
        _error("invalid_report", "pilot report metrics must match its canonical case matrix")
    report = validated_report
    target = _report_target(root)
    rendered = render_report(report).encode("utf-8")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target = _report_target(root)
        temporary = target.with_name(target.name + ".tmp")
        if temporary.is_symlink():
            _error("unsafe_output_path", "temporary report path must not be a symlink")
        temporary.write_bytes(rendered)
        os.replace(temporary, target)
    except PilotError:
        raise
    except OSError as exc:
        raise PilotError("output_unavailable", "pilot report cannot be written") from exc
    return target


def _error_envelope(error):
    return {
        "schema": PILOT_SCHEMA,
        "passed": False,
        "error": {"code": error.code, "message": error.safe_message},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate the offline selective Spec Kit pilot")
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = Path(args.project_root).resolve()
        fixtures = _contained_fixture_path(root, args.fixtures)
        report = evaluate_cases(load_cases(fixtures)["cases"])
        if args.write and report["passed"]:
            report["report_path"] = str(write_report(root, report).relative_to(root))
            report["written"] = True
        else:
            report["written"] = False
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report["passed"] else 1
    except PilotError as exc:
        print(json.dumps(_error_envelope(exc), ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
