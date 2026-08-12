#!/usr/bin/env python3
"""Fail-closed, advisory-only project opt-in for Spec Kit validation."""

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
import unicodedata
from pathlib import Path


CONFIG_SCHEMA = "moduflow.capabilities.v1"
HANDOFF_SCHEMA = "moduflow.spec-kit-handoff.v1"
MANIFEST_SCHEMA = "moduflow.spec-kit-manifest.v1"
RESULT_SCHEMA = "moduflow.spec-kit-result.v1"
ERROR_SCHEMA = "moduflow.spec-kit-error.v1"
APPROVED_VERSION = "0.16.1"
APPROVED_SHA = "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"
FUNCTIONS = ("clarify", "analyze", "checklist", "converge")
TEMPLATE_HASHES = {
    "clarify": "9fce9b3dfe037b67f52486df112f89377ff6c0c598698131cde65cec610b5bba",
    "analyze": "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
    "checklist": "0a862264b9b358138d6049590d42b392ee4dadb69d32811d460620f077924d4e",
    "converge": "aafba511dea42334373c7ffb9f58e2fb6d82889ea94ec86c1367dbb6a531ca36",
}
FUNCTION_PHRASES = {
    "clarify": ("clarify", "clarification", "명확화", "핵심 질문"),
    "analyze": ("analyze", "analysis", "분석", "정합성"),
    "checklist": ("checklist", "체크리스트", "요구사항 점검"),
    "converge": ("converge", "convergence", "수렴", "남은 작업"),
}
REQUEST_PREFIXES = ("spec kit", "speckit", "스펙 킷", "스펙킷")
CANONICAL_RETRY = {
    "clarify": "Spec Kit clarify requirements",
    "analyze": "Spec Kit analyze requirements",
    "checklist": "Spec Kit checklist acceptance criteria",
    "converge": "Spec Kit converge tasks",
}
ENGLISH_TARGETS = (
    "requirements",
    "requirement",
    "spec",
    "specification",
    "plan",
    "tasks",
    "task",
    "acceptance criteria",
    "consistency",
    "validation coverage",
)
KOREAN_TARGETS = (
    "요구사항",
    "요구 사항",
    "명세",
    "스펙",
    "계획",
    "작업",
    "남은 작업",
    "승인 기준",
    "수락 기준",
    "정합성",
    "검증 범위",
)
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


def _error_envelope(code, message):
    return {
        "schema": ERROR_SCHEMA,
        "ok": False,
        "error": {"code": code, "message": message},
    }


class JsonErrorArgumentParser(argparse.ArgumentParser):
    """Keep all command-line parse failures on the stable JSON error boundary."""

    def error(self, message):
        print(json.dumps(_error_envelope("invalid_arguments", message), ensure_ascii=False, sort_keys=True))
        self.exit(2)


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


def _lexists(path):
    return os.path.lexists(os.fspath(path))


def _project_root(project_root):
    try:
        root = Path(project_root).resolve(strict=True)
    except OSError as exc:
        raise SpecKitAdapterError(
            "unsafe_path", "target project root must be an existing directory"
        ) from exc
    if not root.is_dir():
        _error("unsafe_path", "target project root must be an existing directory")
    return root


def _relative_parts(parts):
    flattened = []
    for raw in parts:
        path = Path(raw)
        if path.is_absolute():
            _error("unsafe_path", "project path must be relative")
        for part in path.parts:
            if part in ("", ".", "..") or "/" in part or "\\" in part:
                _error("unsafe_path", "project path contains an unsafe component")
            flattened.append(part)
    return flattened


def _project_path(project_root, *parts, require_regular=False):
    """Resolve only the explicit root and reject every existing internal symlink."""
    root = _project_root(project_root)
    flattened = _relative_parts(parts)
    candidate = root
    for index, part in enumerate(flattened):
        candidate = candidate / part
        try:
            info = os.lstat(candidate)
        except FileNotFoundError:
            if require_regular:
                raise SpecKitAdapterError(
                    "missing_input", "required canonical prerequisite input is missing"
                )
            continue
        except OSError as exc:
            raise SpecKitAdapterError(
                "unsafe_path", "project path cannot be inspected safely"
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            if require_regular:
                _error(
                    "missing_input",
                    "required canonical prerequisite input is unavailable",
                )
            _error("unsafe_path", "project path must not contain symlinks")
        if index < len(flattened) - 1 and not stat.S_ISDIR(info.st_mode):
            if require_regular:
                _error(
                    "missing_input",
                    "required canonical prerequisite input is unavailable",
                )
            _error("unsafe_path", "project path ancestor must be a directory")
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SpecKitAdapterError("unsafe_path", "project path escapes target root") from exc
    if require_regular:
        try:
            info = os.lstat(candidate)
        except OSError as exc:
            raise SpecKitAdapterError(
                "missing_input", "required canonical prerequisite input is missing"
            ) from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            _error(
                "missing_input",
                "required canonical prerequisite input must be a no-follow regular file",
            )
    return candidate


def _read_regular_file(path, label):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SpecKitAdapterError("unsafe_path", f"{label} cannot be opened safely") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            _error("unsafe_path", f"{label} must be a regular file")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _ensure_project_directory(project_root, *parts):
    root = _project_root(project_root)
    current = root
    for part in _relative_parts(parts):
        current = current / part
        if _lexists(current):
            info = os.lstat(current)
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                _error("unsafe_path", "project directory path is not safe")
        else:
            try:
                current.mkdir(mode=0o755)
            except OSError as exc:
                raise SpecKitAdapterError(
                    "output_unavailable", "project directory cannot be created"
                ) from exc
        _project_path(root, *current.relative_to(root).parts)
    return current


def load_project_config(project_root):
    """Read an explicit project's capability opt-in without implicit writes."""
    path = _project_path(project_root, ".moduflow", "capabilities.json")
    if not _lexists(path):
        return {
            "enabled": False,
            "source_version": APPROVED_VERSION,
            "source_sha": APPROVED_SHA,
            "functions": [],
        }
    try:
        payload = json.loads(_read_regular_file(path, "capability config").decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
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


def _normalize_request(request):
    if not isinstance(request, str):
        return ""
    text = unicodedata.normalize("NFKC", request).casefold()
    text = " ".join(text.split())
    return text[:-1] if text.endswith((".", "?", "!")) else text


def _canonical_requests():
    accepted = {}
    english_targets = ("",) + tuple(
        f"{determiner}{target}"
        for target in ENGLISH_TARGETS
        for determiner in ("", "the ", "current ")
    )
    korean_targets = ("",) + tuple(
        variant
        for target in KOREAN_TARGETS
        for variant in (target, f"{target}을", f"{target}를", f"{target}의")
    )
    for prefix in REQUEST_PREFIXES[:2]:
        for function, synonyms in FUNCTION_PHRASES.items():
            for synonym in synonyms[:2] if function != "checklist" else synonyms[:1]:
                for target in english_targets:
                    accepted[" ".join(part for part in (prefix, synonym, target) if part)] = function
    korean_synonyms = {
        "clarify": ("명확화", "핵심 질문"),
        "analyze": ("분석", "정합성"),
        "checklist": ("체크리스트", "요구사항 점검"),
        "converge": ("수렴",),
    }
    for prefix in REQUEST_PREFIXES[2:]:
        for function, synonyms in korean_synonyms.items():
            for synonym in synonyms:
                for target in korean_targets:
                    accepted[" ".join(part for part in (prefix, target, synonym) if part)] = function
    return accepted


CANONICAL_REQUESTS = _canonical_requests()


def _request_body(text):
    for prefix in sorted(REQUEST_PREFIXES, key=len, reverse=True):
        if text == prefix:
            return ""
        if text.startswith(prefix + " "):
            return text[len(prefix) + 1 :]
    return None


def _matched_functions(body):
    return {
        function
        for function, phrases in FUNCTION_PHRASES.items()
        if any(phrase in body for phrase in phrases)
    }


def classify_request(request):
    """Classify only the complete, documented Spec Kit validation grammar."""
    text = _normalize_request(request)
    selected = CANONICAL_REQUESTS.get(text)
    if selected:
        return {
            "outcome": "selected",
            "function": selected,
            "reason_code": "explicit_validation",
            "retry": None,
        }

    body = _request_body(text)
    functions = _matched_functions(body or "")
    if len(functions) > 1:
        reason = "multiple_functions"
    elif body is not None and functions and (
        any(marker in body for marker in (",", ";", ":", " then ", " and ", " which ", " how ", " where "))
        or any(target in body for target in ENGLISH_TARGETS + KOREAN_TARGETS)
    ):
        reason = "ambiguous_request"
    else:
        reason = "unsupported_request"
    retry_function = next(iter(functions), "analyze")
    return {
        "outcome": "fallback",
        "function": None,
        "reason_code": reason,
        "retry": CANONICAL_RETRY[retry_function],
    }


def select_function(request):
    classification = classify_request(request)
    return classification["function"] if classification["outcome"] == "selected" else None


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
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
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


def canonical_input_paths(issue_id, function):
    if not isinstance(issue_id, str) or not ISSUE_ID_PATTERN.fullmatch(issue_id):
        _error("unsafe_issue_id", "issue_id is invalid")
    if function not in FUNCTIONS:
        return ["request"]
    issue = f"issues/{issue_id}.md"
    spec_root = f"specs/{issue_id}"
    paths = {
        "clarify": [issue, f"{spec_root}/spec.md"],
        "analyze": [
            f"{spec_root}/spec.md",
            f"{spec_root}/plan.md",
            f"{spec_root}/tasks.md",
            "workspace/constitution.md",
        ],
        "checklist": [issue, f"{spec_root}/spec.md"],
        "converge": [
            f"{spec_root}/spec.md",
            f"{spec_root}/plan.md",
            f"{spec_root}/tasks.md",
            "workspace/constitution.md",
        ],
    }
    return paths[function]


def read_canonical_inputs(project_root, issue_id, function):
    records = []
    for relative in canonical_input_paths(issue_id, function):
        path = _project_path(project_root, relative, require_regular=True)
        records.append({"path": relative, "content": _read_regular_file(path, "canonical input")})
    return records


def canonical_input_hash(records):
    identity = [
        {"path": record["path"], "sha256": hashlib.sha256(record["content"]).hexdigest()}
        for record in records
    ]
    canonical = json.dumps(
        identity,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _handoff(
    issue_id,
    function,
    outcome,
    request,
    output_artifact=None,
    asset=None,
    input_hash=None,
    fallback_override=None,
):
    ready = outcome == "ready"
    limitations = ["Advisory only; no project artifacts or state are modified."]
    if function == "converge":
        limitations.append("Bounded code scope is advisory metadata, not a canonical input file.")
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
        "inputs": canonical_input_paths(issue_id, function) if function else ["request"],
        "input_hash": input_hash if ready else None,
        "output_artifact": output_artifact,
        "limitations": limitations,
        "fallback": None
        if ready
        else (fallback_override or _native_fallback(function, outcome)),
    }


def _output_path(project_root, issue_id):
    candidate = _project_path(project_root, "specs", issue_id, "validation.md")
    return candidate.relative_to(_project_root(project_root)).as_posix()


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
    if handoff.get("input_hash") != validated["input_hash"]:
        _error("input_mismatch", "handoff canonical input identity does not match result")
    if handoff.get("output_artifact") != _validation_relative_path(validated["issue_id"]):
        _error("output_mismatch", "handoff output does not match result issue")
    return validated


def _contained_validation_path(project_root, issue_id):
    if not isinstance(issue_id, str) or not ISSUE_ID_PATTERN.fullmatch(issue_id):
        _error("unsafe_issue_id", "issue_id is invalid")
    return _project_path(project_root, "specs", issue_id, "validation.md")


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


def _current_validated_result(
    package_root,
    project_root,
    issue_id,
    request,
    result,
    *,
    host_available,
):
    validated = validate_result_shape(result)
    if validated["issue_id"] != issue_id:
        _error("issue_mismatch", "explicit issue does not match result")
    handoff = build_handoff(
        package_root,
        project_root,
        issue_id,
        request,
        host_available=host_available,
    )
    if handoff.get("outcome") != "ready":
        _error("handoff_not_ready", handoff.get("fallback") or "current handoff is not ready")
    return validate_host_result(validated, handoff)


def _read_optional_regular(path, label):
    if not _lexists(path):
        return b""
    return _read_regular_file(path, label)


def _write_all(descriptor, content):
    offset = 0
    while offset < len(content):
        written = os.write(descriptor, content[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _atomic_replace_bytes(project_root, target, content):
    root = _project_root(project_root)
    parent = target.parent
    _project_path(root, *parent.relative_to(root).parts)
    descriptor = None
    temporary_name = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=parent
        )
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            _error("unsafe_path", "temporary output must be a regular file")
        _write_all(descriptor, content)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        _project_path(root, *target.relative_to(root).parts)
        if _lexists(target):
            info = os.lstat(target)
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                _error("unsafe_path", "validation output must be a regular no-follow file")
        os.replace(temporary_name, target)
        temporary_name = None
    except SpecKitAdapterError:
        raise
    except OSError as exc:
        raise SpecKitAdapterError(
            "output_unavailable", "validation output cannot be written"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def persist_validation(
    package_root,
    project_root,
    issue_id,
    request,
    result,
    *,
    host_available,
    write=False,
):
    """Rebuild current readiness, then preview or atomically append one advisory result."""
    validated = _current_validated_result(
        package_root,
        project_root,
        issue_id,
        request,
        result,
        host_available=host_available,
    )
    target = _contained_validation_path(project_root, validated["issue_id"])
    marker = f"<!-- moduflow-spec-kit-run:{validated['run_id']} -->"
    existing = _read_optional_regular(target, "validation output")
    if not write and marker.encode("utf-8") in existing:
        return {"changed": False, "path": target, "run_id": validated["run_id"], "preview": ""}
    rendered = render_validation_entry(validated).encode("utf-8")
    prefix = b"" if not existing else (b"\n" if existing.endswith(b"\n") else b"\n\n")
    preview = (prefix + rendered).decode("utf-8")
    if write:
        lock_path = _project_path(
            project_root,
            "specs",
            validated["issue_id"],
            ".validation.md.lock",
        )
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
        try:
            lock_descriptor = os.open(lock_path, flags, 0o600)
        except OSError as exc:
            raise SpecKitAdapterError("output_unavailable", "validation lock cannot be opened") from exc
        try:
            if not stat.S_ISREG(os.fstat(lock_descriptor).st_mode):
                _error("unsafe_path", "validation lock must be a regular file")
            fcntl.flock(lock_descriptor, fcntl.LOCK_EX)
            validated = _current_validated_result(
                package_root,
                project_root,
                issue_id,
                request,
                result,
                host_available=host_available,
            )
            target = _contained_validation_path(project_root, validated["issue_id"])
            existing = _read_optional_regular(target, "validation output")
            if marker.encode("utf-8") in existing:
                return {
                    "changed": False,
                    "path": target,
                    "run_id": validated["run_id"],
                    "preview": "",
                }
            prefix = b"" if not existing else (b"\n" if existing.endswith(b"\n") else b"\n\n")
            preview = (prefix + rendered).decode("utf-8")
            _atomic_replace_bytes(project_root, target, existing + prefix + rendered)
        finally:
            try:
                fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
            finally:
                os.close(lock_descriptor)
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
        classification = classify_request(request)
        function = classification["function"]
        if classification["outcome"] == "fallback":
            return _handoff(
                issue_id,
                None,
                "unsupported",
                request,
                output_artifact,
                fallback_override=(
                    f"{classification['reason_code']}; use native ModuFlow validation or retry: "
                    f"{classification['retry']}"
                ),
            )
        config = load_project_config(project_root)
        if not config["enabled"]:
            return _handoff(issue_id, function, "disabled", request, output_artifact)
        if function not in config["functions"]:
            return _handoff(issue_id, function, "unsupported", request, output_artifact)
        if host_available is not True:
            return _handoff(issue_id, function, "unavailable", request, output_artifact)
        manifest = load_manifest(package_root)
        assets = verify_assets(package_root, manifest)
        if not all(asset["valid"] for asset in assets):
            _error("assets_unavailable", "approved Spec Kit assets are unavailable")
        asset = next(asset for asset in assets if asset["function"] == function)
        input_records = read_canonical_inputs(project_root, issue_id, function)
        return _handoff(
            issue_id,
            function,
            "ready",
            request,
            output_artifact,
            asset,
            input_hash=canonical_input_hash(input_records),
        )
    except SpecKitAdapterError as exc:
        prerequisite = exc.code == "missing_input"
        return _handoff(
            issue_id if isinstance(issue_id, str) else None,
            function,
            "unavailable" if exc.code in {"assets_unavailable", "missing_input"} else "blocked",
            request,
            None if prerequisite else output_artifact,
            fallback_override=(
                "Required canonical prerequisite inputs are unavailable; use the documented native prerequisite fallback."
                if prerequisite
                else None
            ),
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


def configure_project(project_root, functions, *, write=False):
    functions = _function_list(functions)
    payload = _config_payload(functions)
    if not write:
        return payload
    parent = _ensure_project_directory(project_root, ".moduflow")
    target = _project_path(project_root, ".moduflow", "capabilities.json")
    if _lexists(target):
        info = os.lstat(target)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            _error("unsafe_path", "capability config target must be a regular no-follow file")
    rendered = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    descriptor = None
    temporary_name = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".capabilities.", suffix=".tmp", dir=parent
        )
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            _error("unsafe_path", "temporary config must be a regular file")
        _write_all(descriptor, rendered)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        _project_path(project_root, ".moduflow", "capabilities.json")
        if _lexists(target):
            info = os.lstat(target)
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                _error("unsafe_path", "capability config target must be a regular no-follow file")
        os.replace(temporary_name, target)
        temporary_name = None
    except SpecKitAdapterError:
        raise
    except OSError as exc:
        raise SpecKitAdapterError(
            "config_unavailable", "capability config cannot be written"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
    return payload


def main(argv=None):
    parser = JsonErrorArgumentParser(description="Configure project-local Spec Kit opt-in")
    parser.add_argument("project_root")
    parser.add_argument("--configure", action="store_true")
    parser.add_argument("--functions")
    parser.add_argument("--issue-id")
    parser.add_argument("--accept-result")
    parser.add_argument("--request")
    parser.add_argument("--host-available", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.configure:
            if (
                args.functions is None
                or args.accept_result is not None
                or args.issue_id is not None
                or args.request is not None
                or args.host_available
            ):
                _error(
                    "invalid_arguments",
                    "--configure requires only --functions and optional --write",
                )
            payload = configure_project(
                args.project_root,
                args.functions.split(","),
                write=args.write,
            )
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0
        if args.accept_result is not None:
            if (
                args.functions is not None
                or args.issue_id is None
                or args.request is None
                or not args.host_available
            ):
                _error(
                    "invalid_arguments",
                    "--accept-result requires --issue-id, --request, and --host-available",
                )
            payload = json.loads(args.accept_result)
            result = persist_validation(
                Path(__file__).resolve().parents[1],
                args.project_root,
                args.issue_id,
                args.request,
                payload,
                host_available=True,
                write=args.write,
            )
            envelope = {
                "ok": True,
                "result": {**result, "path": str(result["path"])},
            }
            print(json.dumps(envelope, ensure_ascii=False, sort_keys=True))
            return 0
        if (
            args.issue_id is None
            or args.request is None
            or args.functions is not None
            or args.write
        ):
            _error(
                "invalid_arguments",
                "handoff requires --issue-id and --request and does not allow --write",
            )
        handoff = build_handoff(
            Path(__file__).resolve().parents[1],
            args.project_root,
            args.issue_id,
            args.request,
            host_available=args.host_available,
        )
        print(json.dumps(handoff, ensure_ascii=False, sort_keys=True))
        return 0
    except json.JSONDecodeError:
        envelope = _error_envelope("invalid_result", "result must be valid JSON")
    except SpecKitAdapterError as exc:
        envelope = _error_envelope(exc.code, exc.safe_message)
    print(json.dumps(envelope, ensure_ascii=False, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
