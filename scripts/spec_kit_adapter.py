#!/usr/bin/env python3
"""Fail-closed, advisory-only project opt-in for Spec Kit validation."""

import argparse
import hashlib
import json
import re
from pathlib import Path


CONFIG_SCHEMA = "moduflow.capabilities.v1"
HANDOFF_SCHEMA = "moduflow.spec-kit-handoff.v1"
APPROVED_VERSION = "0.16.1"
APPROVED_SHA = "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"
FUNCTIONS = ("clarify", "analyze", "checklist", "converge")
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
    return Path(package_root).resolve() / "vendor" / "spec-kit" / APPROVED_VERSION / "manifest.json"


def load_manifest(package_root):
    """Load the future Task 2 asset manifest; never download or execute assets."""
    path = _manifest_path(package_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecKitAdapterError("assets_unavailable", "approved Spec Kit assets are unavailable") from exc
    if not isinstance(payload, dict):
        _error("invalid_manifest", "Spec Kit manifest must be an object")
    return payload


def verify_assets(package_root, function):
    """Task 2 will extend this to hash-gate the one selected template."""
    load_manifest(package_root)
    _error("assets_unavailable", "approved Spec Kit assets are unavailable")


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


def _handoff(issue_id, function, outcome, request, output_artifact=None):
    return {
        "schema": HANDOFF_SCHEMA,
        "outcome": outcome,
        "function": function,
        "issue_id": issue_id,
        "source": {
            "version": APPROVED_VERSION,
            "sha": APPROVED_SHA,
            "template": None,
            "template_sha256": None,
        },
        "permission": "advisory",
        "inputs": {"request": str(request or "")},
        "output_artifact": output_artifact,
        "limitations": ["Advisory only; no project artifacts or state are modified."],
        "fallback": _native_fallback(function, outcome),
    }


def _output_path(project_root, issue_id):
    root = Path(project_root).resolve()
    candidate = (root / "specs" / issue_id / "validation.md").resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SpecKitAdapterError("unsafe_path", "output path escapes target project") from exc
    return str(candidate.relative_to(root))


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
        verify_assets(package_root, function)
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
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if not args.configure or args.functions is None:
        parser.error("--configure and --functions are required")
    functions = args.functions.split(",")
    _function_list(functions)
    payload = _config_payload(functions)
    if args.write:
        path = Path(args.project_root).resolve() / ".moduflow" / "capabilities.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
