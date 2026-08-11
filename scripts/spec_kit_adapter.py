#!/usr/bin/env python3
"""Fail-closed, advisory-only project opt-in for Spec Kit validation."""

import argparse
import hashlib
import json
import re
from pathlib import Path


CONFIG_SCHEMA = "moduflow.capabilities.v1"
HANDOFF_SCHEMA = "moduflow.spec-kit-handoff.v1"
MANIFEST_SCHEMA = "moduflow.spec-kit-manifest.v1"
RESULT_SCHEMA = "moduflow.spec-kit-result.v1"
APPROVED_VERSION = "0.16.1"
APPROVED_SHA = "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"
FUNCTIONS = ("clarify", "analyze", "checklist", "converge")
TEMPLATE_HASHES = {
    "clarify": "9fce9b3dfe037b67f52486df112f89377ff6c0c598698131cde65cec610b5bba",
    "analyze": "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
    "checklist": "0a862264b9b358138d6049590d42b392ee4dadb69d32811d460620f077924d4e",
    "converge": "aafba511dea42334373c7ffb9f58e2fb6d82889ea94ec86c1367dbb6a531ca36",
}
FUNCTION_INPUTS = {
    "clarify": ["issue.md", "spec.md"],
    "analyze": ["spec.md", "plan.md", "tasks.md", "constitution.md"],
    "checklist": ["issue.md", "spec.md"],
    "converge": [
        "spec.md",
        "plan.md",
        "tasks.md",
        "constitution.md",
        "bounded-code-scope",
    ],
}
FUNCTION_PHRASES = {
    "clarify": ("clarify", "clarification", "명확화", "핵심 질문"),
    "analyze": ("analyze", "analysis", "분석", "정합성"),
    "checklist": ("checklist", "체크리스트", "요구사항 점검"),
    "converge": ("converge", "convergence", "수렴", "남은 작업"),
}
ISSUE_ID_PATTERN = re.compile(r"^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*$")
CONFIG_TOP_LEVEL = {"schema", "capabilities"}
CONFIG_CAPABILITY_LEVEL = {"spec-kit"}
CONFIG_SPEC_KIT_LEVEL = {
    "enabled",
    "source_version",
    "source_sha",
    "functions",
}
RESULT_TOP_LEVEL = {
    "schema",
    "run_id",
    "input_hash",
    "issue_id",
    "function",
    "source_version",
    "source_sha",
    "template_sha256",
    "permission",
    "findings",
    "limitations",
    "native_overlap",
    "elapsed_ms",
    "loaded_context_chars",
    "user_decision",
    "next_command",
}
RESULT_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class SpecKitAdapterError(ValueError):
    """A safe-to-display error caused by untrusted adapter input."""

    def __init__(self, code, safe_message):
        self.code = code
        self.safe_message = safe_message
        super().__init__(f"{code}: {safe_message}")


def _error(code, message):
    raise SpecKitAdapterError(code, message)


def _only_keys(payload, allowed, level):
    unknown = set(payload) - allowed
    if unknown:
        _error("unknown_config_field", f"{level} contains unknown fields")


def _function_list(value):
    if not isinstance(value, list) or not value:
        _error("invalid_functions", "functions must be a non-empty list")
    if any(not isinstance(name, str) or not name.strip() for name in value):
        _error("invalid_functions", "functions must contain non-empty strings")
    if len(set(value)) != len(value):
        _error("duplicate_function", "functions must not contain duplicates")
    unknown = set(value) - set(FUNCTIONS)
    if unknown:
        _error("unknown_function", "functions contains an unsupported function")
    return list(value)


def load_project_config(project_root):
    """Read an explicit project's capability opt-in without implicit writes."""
    path = Path(project_root).resolve() / ".moduflow" / "capabilities.json"
    if not path.exists():
        return {
            "enabled": False,
            "source_version": APPROVED_VERSION,
            "source_sha": APPROVED_SHA,
            "functions": [],
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecKitAdapterError("invalid_config", "capability config cannot be read") from exc
    if not isinstance(payload, dict):
        _error("invalid_config", "capability config must be an object")
    _only_keys(payload, CONFIG_TOP_LEVEL, "config")
    if payload.get("schema") != CONFIG_SCHEMA:
        _error("invalid_config", f"schema must be {CONFIG_SCHEMA}")
    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, dict):
        _error("invalid_config", "capabilities must be an object")
    _only_keys(capabilities, CONFIG_CAPABILITY_LEVEL, "capabilities")
    spec_kit = capabilities.get("spec-kit")
    if not isinstance(spec_kit, dict):
        _error("invalid_config", "capabilities.spec-kit must be an object")
    _only_keys(spec_kit, CONFIG_SPEC_KIT_LEVEL, "capabilities.spec-kit")
    missing = CONFIG_SPEC_KIT_LEVEL - set(spec_kit)
    if missing:
        _error("invalid_config", "capabilities.spec-kit is missing required fields")
    if not isinstance(spec_kit["enabled"], bool):
        _error("invalid_config", "enabled must be boolean")
    if spec_kit["source_version"] != APPROVED_VERSION:
        _error("unapproved_source", "source_version is not approved")
    if spec_kit["source_sha"] != APPROVED_SHA:
        _error("unapproved_source", "source_sha is not approved")
    functions = _function_list(spec_kit["functions"])
    return {**spec_kit, "functions": functions}


def select_function(request):
    text = " ".join(str(request or "").lower().split())
    matches = [
        name
        for name, phrases in FUNCTION_PHRASES.items()
        if any(phrase in text for phrase in phrases)
    ]
    if len(matches) > 1:
        _error("ambiguous_function", "request selects more than one Spec Kit function")
    return matches[0] if matches else None


def _manifest_path(package_root):
    return _contained_package_path(
        package_root, "vendor", "spec-kit", APPROVED_VERSION, "manifest.json"
    )


def _contained_package_path(package_root, *parts):
    root = Path(package_root).resolve()
    candidate = root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            _error("unsafe_path", "approved Spec Kit asset path must not contain symlinks")
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise SpecKitAdapterError(
            "unsafe_path", "approved Spec Kit asset path escapes package root"
        ) from exc
    return candidate


def _validate_manifest(manifest):
    if not isinstance(manifest, dict):
        _error("invalid_manifest", "Spec Kit manifest must be an object")
    _only_keys(manifest, {"schema", "source", "functions"}, "manifest")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        _error("invalid_manifest", f"schema must be {MANIFEST_SCHEMA}")
    source = manifest.get("source")
    if not isinstance(source, dict):
        _error("invalid_manifest", "manifest source must be an object")
    _only_keys(source, {"repository", "version", "sha"}, "manifest source")
    if source != {
        "repository": "github/spec-kit",
        "version": APPROVED_VERSION,
        "sha": APPROVED_SHA,
    }:
        _error("unapproved_source", "manifest source is not approved")
    functions = manifest.get("functions")
    if not isinstance(functions, dict) or set(functions) != set(FUNCTIONS):
        _error("invalid_manifest", "manifest must contain exactly four approved functions")
    for function in FUNCTIONS:
        entry = functions[function]
        if not isinstance(entry, dict):
            _error("invalid_manifest", "manifest function must be an object")
        _only_keys(entry, {"template", "sha256", "fallback"}, "manifest function")
        if set(entry) != {"template", "sha256", "fallback"}:
            _error("invalid_manifest", "manifest function is missing required fields")
        if entry["template"] != f"commands/{function}.md":
            _error("unsafe_path", "template path is not an approved command path")
        if entry["sha256"] != TEMPLATE_HASHES[function]:
            _error("invalid_manifest", "template hash is not approved")
        if not isinstance(entry["fallback"], str) or not entry["fallback"]:
            _error("invalid_manifest", "manifest fallback must be a non-empty string")
    return manifest


def load_manifest(package_root):
    """Load the approved asset manifest; never download or execute assets."""
    path = _manifest_path(package_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecKitAdapterError("assets_unavailable", "approved Spec Kit assets are unavailable") from exc
    return _validate_manifest(payload)


def _template_path(package_root, template):
    package_root = Path(package_root).resolve()
    manifest_dir = _manifest_path(package_root).parent
    command_dir = _contained_package_path(
        package_root, "vendor", "spec-kit", APPROVED_VERSION, "commands"
    )
    candidate = _contained_package_path(
        package_root,
        "vendor",
        "spec-kit",
        APPROVED_VERSION,
        *Path(template).parts,
    )
    try:
        candidate.relative_to(command_dir)
    except ValueError as exc:
        raise SpecKitAdapterError("unsafe_path", "template path escapes commands") from exc
    return candidate


def verify_assets(package_root, manifest):
    """Return four approved asset hashes without reading template contents into context."""
    manifest = _validate_manifest(manifest)
    package_root = Path(package_root).resolve()
    records = []
    for function in FUNCTIONS:
        entry = manifest["functions"][function]
        template = _template_path(package_root, entry["template"])
        try:
            actual_sha256 = hashlib.sha256(template.read_bytes()).hexdigest()
        except OSError:
            actual_sha256 = None
        records.append(
            {
                "function": function,
                "path": str(template.relative_to(package_root)),
                "expected_sha256": entry["sha256"],
                "actual_sha256": actual_sha256,
                "valid": actual_sha256 == entry["sha256"],
            }
        )
    return records


def _native_fallback(function, outcome):
    names = {
        "clarify": "native clarification questions",
        "analyze": "native requirements analysis",
        "checklist": "native requirements checklist",
        "converge": "native scope convergence review",
    }
    if outcome == "disabled":
        return "Spec Kit is disabled for this project; use " + names.get(function, "native validation") + "."
    if outcome == "unavailable":
        return "Spec Kit is unavailable in this host; use " + names.get(function, "native validation") + "."
    if outcome == "unsupported":
        return "Use a single supported Spec Kit validation request or native validation."
    return "Spec Kit request was blocked; use native validation after correcting the request or config."


def _handoff(issue_id, function, outcome, request, output_artifact=None, asset=None):
    ready = outcome == "ready"
    return {
        "schema": HANDOFF_SCHEMA,
        "outcome": outcome,
        "function": function,
        "issue_id": issue_id,
        "source": {
            "version": APPROVED_VERSION,
            "sha": APPROVED_SHA,
            "template": asset["path"] if ready else None,
            "template_sha256": asset["actual_sha256"] if ready else None,
        },
        "permission": "read",
        "inputs": list(FUNCTION_INPUTS[function]) if function else ["request"],
        "output_artifact": output_artifact,
        "limitations": ["Advisory only; no project artifacts or state are modified."],
        "fallback": None if ready else _native_fallback(function, outcome),
    }


def _output_path(project_root, issue_id):
    root = Path(project_root).resolve()
    candidate = (root / "specs" / issue_id / "validation.md").resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SpecKitAdapterError("unsafe_path", "output path escapes target project") from exc
    return str(candidate.relative_to(root))


def _validation_relative_path(issue_id):
    return f"specs/{issue_id}/validation.md"


def _json_safe(value):
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, int) and not isinstance(value, bool):
        return True
    if isinstance(value, float):
        return value == value and value not in (float("inf"), float("-inf"))
    if isinstance(value, list):
        return all(_json_safe(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _json_safe(item) for key, item in value.items())
    return False


def _result_hash(payload):
    canonical = json.dumps(
        {
            "source_sha": payload["source_sha"],
            "template_sha256": payload["template_sha256"],
            "function": payload["function"],
            "issue_id": payload["issue_id"],
            "input_hash": payload["input_hash"],
            "findings": payload["findings"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def validate_result_shape(payload):
    """Strictly validate one advisory Spec Kit result and return an isolated copy."""
    if not isinstance(payload, dict):
        _error("invalid_result", "result must be an object")
    unknown = set(payload) - RESULT_TOP_LEVEL
    if unknown:
        _error("unknown_result_field", "result contains unsupported fields")
    missing = RESULT_TOP_LEVEL - set(payload)
    if missing:
        _error("invalid_result", "result is missing required fields")
    if payload["schema"] != RESULT_SCHEMA:
        _error("invalid_result", f"schema must be {RESULT_SCHEMA}")
    if not isinstance(payload["issue_id"], str) or not ISSUE_ID_PATTERN.fullmatch(payload["issue_id"]):
        _error("unsafe_issue_id", "issue_id is invalid")
    if payload["function"] not in FUNCTIONS:
        _error("function_mismatch", "function is not approved")
    if payload["source_version"] != APPROVED_VERSION or payload["source_sha"] != APPROVED_SHA:
        _error("source_mismatch", "result source is not approved")
    if payload["template_sha256"] != TEMPLATE_HASHES[payload["function"]]:
        _error("template_mismatch", "result template hash is not approved")
    if payload["permission"] != "read":
        _error("permission_mismatch", "result permission must be read")
    for field in ("run_id", "input_hash"):
        if not isinstance(payload[field], str) or not RESULT_HASH_PATTERN.fullmatch(payload[field]):
            _error("invalid_result", f"{field} must be a sha256 digest")
    for field in ("findings", "limitations", "native_overlap"):
        if not isinstance(payload[field], list) or not _json_safe(payload[field]):
            _error("invalid_result", f"{field} must be a JSON-safe list")
    for field in ("elapsed_ms", "loaded_context_chars"):
        if (
            not isinstance(payload[field], int)
            or isinstance(payload[field], bool)
            or payload[field] < 0
        ):
            _error("invalid_result", f"{field} must be a non-negative integer")
    for field in ("user_decision", "next_command"):
        if not isinstance(payload[field], str) or not payload[field]:
            _error("invalid_result", f"{field} must be a non-empty string")
    if payload["function"] == "clarify" and len(payload["findings"]) > 1:
        _error("clarify_findings_limit", "clarify accepts at most one question")
    expected_run_id = _result_hash(payload)
    if payload["run_id"] != expected_run_id:
        _error("run_id_mismatch", "run_id does not match the advisory result")
    return json.loads(json.dumps(payload, ensure_ascii=False, allow_nan=False))


def validate_host_result(payload, handoff):
    """Require a ready, matching handoff before a host result becomes evidence."""
    validated = validate_result_shape(payload)
    if not isinstance(handoff, dict) or handoff.get("outcome") != "ready":
        _error("handoff_not_ready", "a ready handoff is required")
    if handoff.get("schema") != HANDOFF_SCHEMA:
        _error("handoff_not_ready", "handoff schema is invalid")
    if handoff.get("issue_id") != validated["issue_id"]:
        _error("issue_mismatch", "handoff issue does not match result")
    if handoff.get("function") != validated["function"]:
        _error("function_mismatch", "handoff function does not match result")
    expected_source = {
        "version": validated["source_version"],
        "sha": validated["source_sha"],
        "template": f"vendor/spec-kit/{APPROVED_VERSION}/commands/{validated['function']}.md",
        "template_sha256": validated["template_sha256"],
    }
    if handoff.get("source") != expected_source:
        _error("source_mismatch", "handoff source does not match result")
    if handoff.get("permission") != validated["permission"]:
        _error("permission_mismatch", "handoff permission does not match result")
    if handoff.get("output_artifact") != _validation_relative_path(validated["issue_id"]):
        _error("output_mismatch", "handoff output does not match result issue")
    return validated


def _contained_validation_path(project_root, issue_id):
    if not isinstance(issue_id, str) or not ISSUE_ID_PATTERN.fullmatch(issue_id):
        _error("unsafe_issue_id", "issue_id is invalid")
    root = Path(project_root).resolve()
    candidate = root
    for part in ("specs", issue_id, "validation.md"):
        candidate = candidate / part
        if candidate.is_symlink():
            _error("unsafe_path", "validation output path must not contain symlinks")
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise SpecKitAdapterError(
            "unsafe_path", "validation output path escapes target project"
        ) from exc
    return candidate


def render_validation_entry(validated_result):
    """Render one human-readable result without allowing marker injection from JSON text."""
    marker = f"<!-- moduflow-spec-kit-run:{validated_result['run_id']} -->"
    details = json.dumps(
        validated_result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
    ).replace("<", "\\u003c")
    return (
        f"{marker}\n"
        f"## Spec Kit advisory validation — {validated_result['function']}\n\n"
        "<details>\n<summary>Verified advisory result</summary>\n\n"
        "```json\n"
        f"{details}\n"
        "```\n\n"
        "</details>\n"
    )


def persist_validation(project_root, validated_result, *, write=False):
    """Preview or append a shape-validated result; host provenance is checked by the bridge."""
    validated = validate_result_shape(validated_result)
    target = _contained_validation_path(project_root, validated["issue_id"])
    marker = f"<!-- moduflow-spec-kit-run:{validated['run_id']} -->"
    try:
        existing = target.read_bytes() if target.exists() else b""
    except OSError as exc:
        raise SpecKitAdapterError("output_unavailable", "validation output cannot be read") from exc
    if marker.encode("utf-8") in existing:
        return {"changed": False, "path": target, "run_id": validated["run_id"], "preview": ""}
    rendered = render_validation_entry(validated).encode("utf-8")
    prefix = b"" if not existing else (b"\n" if existing.endswith(b"\n") else b"\n\n")
    preview = (prefix + rendered).decode("utf-8")
    if write:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("ab") as handle:
                handle.write(prefix + rendered)
        except OSError as exc:
            raise SpecKitAdapterError("output_unavailable", "validation output cannot be written") from exc
    return {
        "changed": bool(write),
        "path": target,
        "run_id": validated["run_id"],
        "preview": preview,
    }


def build_handoff(package_root, project_root, issue_id, request, host_available):
    """Return a complete, non-executing handoff envelope for one request."""
    function = None
    output_artifact = None
    try:
        if not isinstance(issue_id, str) or not ISSUE_ID_PATTERN.fullmatch(issue_id):
            _error("unsafe_issue_id", "issue_id is invalid")
        output_artifact = _output_path(project_root, issue_id)
        function = select_function(request)
        if function is None:
            return _handoff(issue_id, None, "unsupported", request, output_artifact)
        config = load_project_config(project_root)
        if not config["enabled"]:
            return _handoff(issue_id, function, "disabled", request, output_artifact)
        if function not in config["functions"]:
            return _handoff(issue_id, function, "unsupported", request, output_artifact)
        if not host_available:
            return _handoff(issue_id, function, "unavailable", request, output_artifact)
        manifest = load_manifest(package_root)
        assets = verify_assets(package_root, manifest)
        if not all(asset["valid"] for asset in assets):
            _error("assets_unavailable", "approved Spec Kit assets are unavailable")
        asset = next(asset for asset in assets if asset["function"] == function)
        return _handoff(issue_id, function, "ready", request, output_artifact, asset)
    except SpecKitAdapterError as exc:
        return _handoff(
            issue_id if isinstance(issue_id, str) else None,
            function,
            "unavailable" if exc.code == "assets_unavailable" else "blocked",
            request,
            output_artifact,
        )


def _config_payload(functions):
    return {
        "schema": CONFIG_SCHEMA,
        "capabilities": {
            "spec-kit": {
                "enabled": False,
                "source_version": APPROVED_VERSION,
                "source_sha": APPROVED_SHA,
                "functions": functions,
            }
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Configure project-local Spec Kit opt-in")
    parser.add_argument("project_root")
    parser.add_argument("--configure", action="store_true")
    parser.add_argument("--functions")
    parser.add_argument("--issue-id")
    parser.add_argument("--accept-result")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.configure:
        if args.functions is None or args.accept_result is not None:
            parser.error("--configure requires --functions and cannot accept a result")
        functions = args.functions.split(",")
        _function_list(functions)
        payload = _config_payload(functions)
        if args.write:
            path = Path(args.project_root).resolve() / ".moduflow" / "capabilities.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if args.accept_result is None or args.issue_id is None:
        parser.error("--issue-id and --accept-result are required unless --configure is used")
    try:
        payload = json.loads(args.accept_result)
        validated = validate_result_shape(payload)
        if validated["issue_id"] != args.issue_id:
            _error("issue_mismatch", "--issue-id must match result issue_id")
        result = persist_validation(args.project_root, validated, write=args.write)
        envelope = {
            "ok": True,
            "result": {**result, "path": str(result["path"])},
        }
        print(json.dumps(envelope, ensure_ascii=False, sort_keys=True))
        return 0
    except json.JSONDecodeError:
        envelope = {
            "ok": False,
            "error": {"code": "invalid_result", "message": "result must be valid JSON"},
        }
    except SpecKitAdapterError as exc:
        envelope = {
            "ok": False,
            "error": {"code": exc.code, "message": exc.safe_message},
        }
    print(json.dumps(envelope, ensure_ascii=False, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
