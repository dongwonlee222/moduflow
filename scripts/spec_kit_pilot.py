#!/usr/bin/env python3
"""Evaluate deterministic, offline evidence for the selective Spec Kit pilot."""

import argparse
import html
import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import capability_routing, project_operation, project_registry, spec_kit_adapter


PILOT_SCHEMA = "moduflow.spec-kit-pilot.v1"
ERROR_SCHEMA = "moduflow.spec-kit-error.v1"
CASES_SCHEMA = "moduflow.spec-kit-pilot-cases.v1"
ISSUE_ID = "098-speckit-selective-validation-adapter"
FUNCTIONS = {"clarify", "analyze", "checklist", "converge"}
CLASSES = {"success", "disabled", "unavailable", "grammar"}
BOUNDARIES = {
    "unknown",
    "multiple-functions",
    "punctuation",
    "implementation",
    "lifecycle",
    "git",
    "review",
    "release",
    "mixed",
}
DISPOSITIONS = {"useful_unique", "accepted_native", "rejected_invalid"}
CASE_KEYS = {
    "id",
    "class",
    "function",
    "boundary",
    "request",
    "expected_outcome",
    "result_file",
}
CASE_REQUIRED = {"id", "class", "function", "boundary", "request", "expected_outcome"}
FINDING_KEYS = {"id", "summary", "reviewer_disposition", "native_overlap"}
REPORT_RELATIVE_PATH = Path("specs") / ISSUE_ID / "pilot-report.md"
SAFE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXPECTED_OUTCOMES = {"ready", "disabled", "unavailable", "unsupported"}


class PilotError(ValueError):
    """A fail-closed pilot input or output error safe to expose to a caller."""

    def __init__(self, code, message):
        self.code = code
        self.safe_message = message
        super().__init__(f"{code}: {message}")


class JsonErrorArgumentParser(argparse.ArgumentParser):
    """Keep pilot argument failures on the shared Spec Kit JSON boundary."""

    def error(self, message):
        print(
            json.dumps(
                {
                    "schema": ERROR_SCHEMA,
                    "ok": False,
                    "error": {"code": "invalid_arguments", "message": message},
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        self.exit(2)


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
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PilotError("invalid_result_snapshot", "result snapshot cannot be read") from exc
    except spec_kit_adapter.SpecKitAdapterError as exc:
        raise PilotError("invalid_result_snapshot", exc.safe_message) from exc


def _normalize_case(case):
    if not isinstance(case, dict):
        _error("invalid_case", "each case must be an object")
    unknown = set(case) - CASE_KEYS
    if unknown:
        _error("unknown_case_field", "case contains unsupported fields")
    missing = CASE_REQUIRED - set(case)
    if missing:
        _error("invalid_case", "case is missing required fields")

    case_id = case["id"]
    if not isinstance(case_id, str) or not SAFE_ID_PATTERN.fullmatch(case_id):
        _error("invalid_case", "case id must be a strict lowercase Markdown-safe identifier")
    case_class = case["class"]
    if case_class not in CLASSES:
        _error("invalid_class", "case class is unsupported")
    function = case["function"]
    boundary = case["boundary"]
    if case_class == "grammar":
        if function is not None or boundary not in BOUNDARIES:
            _error("invalid_function", "grammar cases require one approved boundary and no function")
    else:
        if function not in FUNCTIONS or boundary is not None:
            _error("invalid_function", "function cases require one approved function and no boundary")

    request = case["request"]
    if not isinstance(request, str) or not request.strip():
        _error("invalid_case", "case request must be a non-empty string")
    expected_outcome = case["expected_outcome"]
    if expected_outcome not in EXPECTED_OUTCOMES:
        _error("invalid_case", "case expected_outcome is unsupported")
    result_file = case.get("result_file")
    if case_class == "success":
        if not isinstance(result_file, str) or not result_file.strip():
            _error("invalid_result_snapshot", "success cases require a result snapshot")
    elif result_file is not None:
        _error("invalid_result_snapshot", "only success cases may reference a result snapshot")

    return {
        "id": case_id,
        "class": case_class,
        "function": function,
        "boundary": boundary,
        "request": request,
        "expected_outcome": expected_outcome,
        "result_file": result_file,
    }


def load_cases(path):
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PilotError("invalid_cases", "case matrix cannot be read") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema", "cases"}:
        _error("invalid_cases", "case matrix must contain exactly schema and cases")
    if payload["schema"] != CASES_SCHEMA or not isinstance(payload["cases"], list):
        _error("invalid_cases", "case matrix schema or cases is invalid")
    cases = [_normalize_case(case) for case in payload["cases"]]
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        _error("duplicate_case_id", "case ids must be unique")
    _validate_matrix(cases)
    return {"schema": CASES_SCHEMA, "cases": cases}


def _validate_matrix(cases):
    """Require the complete approved pilot matrix before metrics or writes."""
    if len(cases) < 24:
        _error("invalid_matrix", "pilot matrix must contain at least 24 cases")

    success = [case for case in cases if case["class"] == "success"]
    success_functions = [case["function"] for case in success]
    if len(success) != len(FUNCTIONS) * 2 or any(
        success_functions.count(function) != 2 for function in FUNCTIONS
    ):
        _error(
            "invalid_matrix",
            "pilot matrix requires English and Korean success for each approved function",
        )
    if any(not isinstance(case["result_file"], str) or not case["result_file"].strip() for case in success):
        _error(
            "invalid_matrix",
            "success cases require one result snapshot",
        )

    fallbacks = [
        case for case in cases if case["class"] in {"disabled", "unavailable"}
    ]
    if len(fallbacks) < 4 or {case["function"] for case in fallbacks} != FUNCTIONS:
        _error(
            "invalid_matrix",
            "fallback cases must cover all four approved functions",
        )
    if any(case["result_file"] is not None for case in fallbacks):
        _error(
            "invalid_matrix",
            "disabled and unavailable cases cannot claim results",
        )

    grammar = [case for case in cases if case["class"] == "grammar"]
    if len(grammar) < 12 or not BOUNDARIES.issubset(
        {case["boundary"] for case in grammar}
    ):
        _error(
            "invalid_matrix",
            "grammar cases must cover every approved fallback boundary",
        )
    if any(case["function"] is not None or case["result_file"] is not None for case in grammar):
        _error(
            "invalid_matrix",
            "grammar cases cannot claim a function or result",
        )


def _copy_canonical_project(package_root, target):
    relative_paths = sorted(
        {
            relative
            for function in FUNCTIONS
            for relative in spec_kit_adapter.canonical_input_paths(ISSUE_ID, function)
        }
    )
    for relative in relative_paths:
        source = spec_kit_adapter._project_path(package_root, relative, require_regular=True)
        content = spec_kit_adapter._read_regular_file(source, "pilot canonical input")
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)


def _write_opt_in(target):
    path = target / ".moduflow" / "capabilities.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": spec_kit_adapter.CONFIG_SCHEMA,
                "capabilities": {
                    "spec-kit": {
                        "enabled": True,
                        "source_version": spec_kit_adapter.APPROVED_VERSION,
                        "source_sha": spec_kit_adapter.APPROVED_SHA,
                        "functions": list(spec_kit_adapter.FUNCTIONS),
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _derived_context_chars(package_root, project_root, handoff):
    overlay = spec_kit_adapter._contained_package_path(
        package_root, "overlays", "spec-kit", "selective-validation-policy.md"
    )
    template = spec_kit_adapter._contained_package_path(
        package_root, *Path(handoff["source"]["template"]).parts
    )
    payloads = [
        spec_kit_adapter._read_regular_file(overlay, "Spec Kit safety overlay"),
        spec_kit_adapter._read_regular_file(template, "Spec Kit template"),
        *[
            record["content"]
            for record in spec_kit_adapter.read_canonical_inputs(
                project_root, handoff["issue_id"], handoff["function"]
            )
        ],
    ]
    try:
        return sum(len(payload.decode("utf-8")) for payload in payloads)
    except UnicodeDecodeError as exc:
        raise PilotError("invalid_context", "pilot context must be UTF-8 text") from exc


def _load_success_result(result_base, case, handoff, package_root, project_root):
    if result_base is None:
        _error(
            "result_base_required",
            "success evidence requires an explicit result fixture directory",
        )
    result = _load_result(result_base, case["result_file"])
    if result["issue_id"] != ISSUE_ID or result["function"] != case["function"]:
        _error("invalid_result_snapshot", "result issue/function does not match its case")
    try:
        spec_kit_adapter.validate_host_result(result, handoff)
    except spec_kit_adapter.SpecKitAdapterError as exc:
        raise PilotError("invalid_result_snapshot", exc.safe_message) from exc
    expected_chars = _derived_context_chars(package_root, project_root, handoff)
    if result["loaded_context_chars"] != expected_chars:
        _error("invalid_result_snapshot", "result context cost is not derived from current inputs")
    if result["elapsed_ms"] != 0:
        _error("invalid_result_snapshot", "synthetic fixture latency must be zero")
    return result


def _execute_case(case, package_root, registry, result_base):
    with tempfile.TemporaryDirectory(prefix="moduflow-spec-kit-pilot-") as tmp:
        project = Path(tmp)
        _copy_canonical_project(package_root, project)
        if case["class"] != "disabled":
            _write_opt_in(project)
        host_available = case["class"] != "unavailable"
        availability = {
            descriptor["id"]: True for descriptor in registry["capabilities"]
        }
        availability["spec-kit"] = host_available
        route = capability_routing.route_request(
            case["request"],
            registry,
            issue_id=ISSUE_ID,
            target_root=project,
            availability=availability,
        )
        selected = spec_kit_adapter.select_function(case["request"])
        handoff = spec_kit_adapter.build_handoff(
            package_root,
            project,
            ISSUE_ID,
            case["request"],
            host_available=host_available,
        )
        target = project / REPORT_RELATIVE_PATH.with_name("validation.md")
        artifact_created = target.exists()
        spec_stages = [stage for stage in route["stages"] if stage["adapter_id"] == "spec-kit"]
        ready_stage = (
            len(spec_stages) == 1
            and spec_stages[0]["availability"] == "available"
            and spec_stages[0]["permission"] == "read"
            and spec_stages[0]["permission_state"] == "allowed"
        )
        template_loaded = bool(handoff["outcome"] == "ready" and handoff["source"]["template"])
        fanout = int(template_loaded)
        boundary_violation = bool(
            case["class"] == "grammar"
            and (selected is not None or handoff["outcome"] == "ready" or template_loaded)
        )
        false_execution_claim = bool(handoff["outcome"] != "ready" and handoff["source"]["template"])
        if case["class"] == "success":
            passed = bool(
                route["outcome"] == "delegate"
                and len(route["stages"]) == 1
                and ready_stage
                and selected == case["function"]
                and handoff["outcome"] == case["expected_outcome"] == "ready"
                and handoff["function"] == case["function"]
                and fanout == 1
                and not artifact_created
            )
            result = _load_success_result(
                result_base, case, handoff, package_root, project
            )
            findings = [_validate_finding(finding) for finding in result["findings"]]
            elapsed_ms = result["elapsed_ms"]
            loaded_context_chars = result["loaded_context_chars"]
        elif case["class"] in {"disabled", "unavailable"}:
            passed = bool(
                handoff["outcome"] == case["expected_outcome"]
                and handoff["source"]["template"] is None
                and fanout == 0
                and not artifact_created
            )
            findings, elapsed_ms, loaded_context_chars = [], 0, 0
        else:
            passed = bool(
                selected is None
                and handoff["outcome"] == case["expected_outcome"] == "unsupported"
                and handoff["source"]["template"] is None
                and fanout == 0
                and not artifact_created
                and not boundary_violation
            )
            findings, elapsed_ms, loaded_context_chars = [], 0, 0
        return {
            **case,
            "passed": passed,
            "route_outcome": route["outcome"],
            "adapter_outcome": handoff["outcome"],
            "selected_function": selected,
            "findings": findings,
            "elapsed_ms": elapsed_ms,
            "loaded_context_chars": loaded_context_chars,
            "boundary_violation": boundary_violation,
            "unauthorized_write": artifact_created,
            "fanout": fanout,
            "false_execution_claim": false_execution_claim,
            "artifact_created": artifact_created,
            "output_artifact": handoff["output_artifact"] if handoff["outcome"] == "ready" else None,
        }


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


def evaluate_cases(cases, result_base=None, package_root=None):
    if not isinstance(cases, list):
        _error("invalid_cases", "cases must be a list")
    normalized = [_normalize_case(case) for case in cases]
    ids = [case["id"] for case in normalized]
    if len(ids) != len(set(ids)):
        _error("duplicate_case_id", "case ids must be unique")
    _validate_matrix(normalized)
    package_root = Path(package_root or Path(__file__).resolve().parents[1]).resolve()
    try:
        registry = capability_routing.load_registry(package_root)
    except capability_routing.RegistryError as exc:
        raise PilotError("invalid_router", "capability router registry is unavailable") from exc
    observed = [
        _execute_case(case, package_root, registry, result_base) for case in normalized
    ]
    observed.sort(key=lambda case: case["id"])
    findings = [finding for case in observed for finding in case["findings"]]
    total_findings = len(findings)
    loaded_chars = sum(case["loaded_context_chars"] for case in observed)
    safety = {
        "ownership_escape_count": sum(case["boundary_violation"] for case in observed),
        "unauthorized_write_count": sum(case["unauthorized_write"] for case in observed),
        "template_fanout_violations": sum(case["fanout"] > 1 for case in observed),
        "false_execution_claims": sum(case["false_execution_claim"] for case in observed),
    }
    metrics = {
        "actionable_value": sum(
            finding["reviewer_disposition"] == "useful_unique" for finding in findings
        ),
        "elapsed_ms": sum(case["elapsed_ms"] for case in observed),
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
    passed_cases = sum(case["passed"] for case in observed)
    evidence_counts = {
        "canonical_success_count": sum(case["class"] == "success" for case in observed),
        "availability_fallback_count": sum(
            case["class"] in {"disabled", "unavailable"} for case in observed
        ),
        "grammar_fallback_count": sum(case["class"] == "grammar" for case in observed),
    }
    return {
        "schema": PILOT_SCHEMA,
        "total_cases": len(observed),
        "passed_cases": passed_cases,
        "passed": passed_cases == len(observed) and not any(safety.values()),
        "evidence_counts": evidence_counts,
        "metrics": metrics,
        "per_function": _function_metrics(observed),
        "cases": observed,
    }


def _markdown_cell(value):
    text = "".join(
        " " if ord(character) < 32 or ord(character) == 127 else character
        for character in str(value)
    )
    return html.escape(text, quote=True).replace("\\", "\\\\").replace("|", "\\|")


def render_report(report):
    metrics = report["metrics"]
    lines = [
        "# Spec Kit Selective Validation Pilot Report",
        "",
        "Issue: `098-speckit-selective-validation-adapter`",
        "Evidence type: deterministic offline evidence from the real router and adapter; no live model or Spec Kit CLI execution.",
        "Synthetic fixture latency: `0 ms`; it is not presented as live performance.",
        "Human decision: pending",
        "Wider/default activation: prohibited",
        "",
        "## Outcome",
        "",
        f"- Pilot passed: `{'yes' if report['passed'] else 'no'}`",
        f"- Cases: `{report['passed_cases']}/{report['total_cases']}` passed",
        f"- Canonical English/Korean successes: `{report['evidence_counts']['canonical_success_count']}`",
        f"- Availability fallbacks: `{report['evidence_counts']['availability_fallback_count']}`",
        f"- Conservative grammar fallbacks: `{report['evidence_counts']['grammar_fallback_count']}`",
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
        f"| Ownership escapes | {metrics['ownership_escape_count']} |",
        f"| Unauthorized writes | {metrics['unauthorized_write_count']} |",
        f"| Template fan-out violations | {metrics['template_fanout_violations']} |",
        f"| False execution claims | {metrics['false_execution_claims']} |",
        "",
        "## Per-Function Evidence",
        "",
        "| Function | Findings | Unique | Elapsed ms | Chars | Tokens | False positive | Native overlap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for function, evidence in report["per_function"].items():
        lines.append(
            "| "
            + " | ".join(
                _markdown_cell(value)
                for value in (
                    function,
                    evidence["findings"],
                    evidence["actionable_value"],
                    evidence["elapsed_ms"],
                    evidence["loaded_context_chars"],
                    evidence["estimated_loaded_tokens"],
                    f"{evidence['false_positive_rate']:.4f}",
                    f"{evidence['native_overlap_rate']:.4f}",
                )
            )
            + " |"
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
            "| "
            + " | ".join(
                _markdown_cell(value)
                for value in (
                    case["id"],
                    case["class"],
                    subject,
                    "yes" if case["passed"] else "no",
                )
            )
            + " |"
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


def write_report(
    root,
    report,
    result_base=None,
    package_root=None,
    *,
    project_context=None,
):
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    project_operation.require_project_capability(context, "write")
    if not isinstance(report, dict) or "cases" not in report:
        _error("invalid_report", "pilot report must contain evaluated cases")
    declarations = [
        {key: case[key] for key in CASE_KEYS if key in case}
        for case in report["cases"]
    ]
    validated_report = evaluate_cases(
        declarations,
        result_base=result_base,
        package_root=package_root,
    )
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
        "schema": ERROR_SCHEMA,
        "ok": False,
        "error": {"code": error.code, "message": error.safe_message},
    }


@project_operation.cli_denial_boundary
def main(argv=None):
    parser = JsonErrorArgumentParser(
        description="Evaluate the offline selective Spec Kit pilot"
    )
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = Path(args.project_root).resolve()
        package_root = Path(__file__).resolve().parents[1]
        fixtures = _contained_fixture_path(root, args.fixtures)
        result_base = fixtures.parent
        report = evaluate_cases(
            load_cases(fixtures)["cases"],
            result_base=result_base,
            package_root=package_root,
        )
        if args.write and report["passed"]:
            report["report_path"] = str(
                write_report(
                    root,
                    report,
                    result_base=result_base,
                    package_root=package_root,
                ).relative_to(root)
            )
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
