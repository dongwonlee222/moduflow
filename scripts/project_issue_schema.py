#!/usr/bin/env python3
"""Safe, standard-library issue schema parsing boundary.

The accepted frontmatter grammar is intentionally smaller than YAML: top-level
scalar fields and top-level lists of scalars.  Rich YAML features are rejected
as diagnostic data so reading a user-authored issue never invokes constructors
or executes tags.
"""

import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path


NORMALIZED_SCHEMA = "moduflow.issue.v2"
SUPPORTED_SCHEMA_VERSIONS = {"0.1.0"}
LIFECYCLE_STATES = {"backlog", "active", "done"}
PROJECTION_TO_LIFECYCLE = {
    "backlog": "backlog",
    "in_progress": "active",
    "done": "done",
}
LIFECYCLE_TO_PROJECTION = {
    lifecycle: projection
    for projection, lifecycle in PROJECTION_TO_LIFECYCLE.items()
}
DEFINITION_READINESS_EXCEPTIONS = frozenset()
DEFINITION_READINESS_VALUES = frozenset(("draft", "ready"))
GATE_STATE_VALUES = frozenset(("pending", "in_progress", "blocked", "passed"))
DECLARED_PHASE_TO_ARTIFACT_PHASE = {
    "issue": "issue",
    "spec": "spec",
    "plan": "plan",
    "implementation": "tasks",
    "execute": "tasks",
    "review": "review",
    "release": "release",
}

_ARTIFACT_PHASES = ("spec", "plan", "tasks", "review", "release")
_SCHEMA_ERROR_CODES = {
    "ISSUE_ARTIFACT_OUTSIDE_ROOT",
    "ISSUE_SOURCE_OUTSIDE_ROOT",
    "ISSUE_SOURCE_UNREADABLE",
    "ISSUE_SCHEMA_MALFORMED",
    "ISSUE_SCHEMA_UNSUPPORTED",
    "ISSUE_DUPLICATE_FIELD",
}
_PROJECTION_ERROR_CODES = {
    "ISSUE_STATE_PROJECTION_MISMATCH",
    "ISSUE_DEPENDENCY_PROJECTION_MISMATCH",
}
_DEPENDENCY_ERROR_CODES = {
    "ISSUE_DEPENDENCY_UNMET",
    "ISSUE_DEPENDENCY_DANGLING",
    "ISSUE_DEPENDENCY_CYCLE",
}

_SCALAR_CONTRACT_FIELDS = (
    "schema_version",
    "issue_id",
    "canonical_state",
    "status",
    "priority",
    "definition_readiness",
    "gate_state",
    "phase",
    "declared_phase",
    "next_command",
)
_CONTRACT_FIELDS = set(_SCALAR_CONTRACT_FIELDS) | {"depends_on"}
_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")
_INTEGER_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)$")
_ISSUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DEFAULT_PROJECT_PATHS = {
    "issues": "issues",
    "specs": "specs",
    "workspace": "workspace",
}


def validate_issue_id(value):
    """Return whether value is a safe, non-empty issue filename stem."""
    return (
        isinstance(value, str)
        and value not in {".", ".."}
        and _ISSUE_ID_RE.fullmatch(value) is not None
    )


def _contained_path(root, *parts):
    """Resolve a descendant path and reject any escape from root."""
    resolved_root = Path(root).resolve()
    candidate = resolved_root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"path escapes configured root: {candidate}") from exc
    return candidate


def _safe_project_relative_path(project_root, value, default):
    if not isinstance(value, str) or not value.strip():
        return default
    relative = Path(value)
    if relative.is_absolute():
        return default
    root = Path(project_root).resolve()
    try:
        resolved = (root / relative).resolve()
        normalized = resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return default
    return normalized.as_posix() or "."


def configured_project_paths(project_root):
    """Return safe configured artifact paths rooted inside the project."""
    root = Path(project_root).resolve()
    config_path = root / ".moduflow" / "config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        config = {}
    raw_paths = config.get("paths", {}) if isinstance(config, dict) else {}
    if not isinstance(raw_paths, dict):
        raw_paths = {}
    return {
        key: _safe_project_relative_path(
            root, raw_paths.get(key), default
        )
        for key, default in DEFAULT_PROJECT_PATHS.items()
    }


def _configured_path_violations(project_root):
    """Return explicitly configured paths that do not stay inside the project."""
    root = Path(project_root).resolve()
    config_path = root / ".moduflow" / "config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    raw_paths = config.get("paths", {}) if isinstance(config, dict) else {}
    if not isinstance(raw_paths, dict):
        return {}
    violations = {}
    for key in DEFAULT_PROJECT_PATHS:
        value = raw_paths.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        relative = Path(value)
        try:
            if relative.is_absolute():
                raise ValueError("absolute path")
            (root / relative).resolve().relative_to(root)
        except (OSError, RuntimeError, ValueError):
            violations[key] = value
    return violations


def split_frontmatter(text):
    """Return ``(frontmatter, body)`` or ``(None, text)`` when absent/invalid."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].lstrip("\ufeff").strip() != "---":
        return None, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "".join(lines[1:index]), "".join(lines[index + 1 :])
    return None, text


def _diagnostic(code, issue_id, source_path, message, severity="error", **details):
    diagnostic = {
        "code": code,
        "severity": severity,
        "issue_id": issue_id,
        "source_path": str(source_path),
        "field": details.pop("field", None),
        "current": details.pop("current", None),
        "expected": details.pop("expected", None),
        "message": message,
        "recommendation": details.pop(
            "recommendation",
            "Use supported top-level scalar or list syntax in issue frontmatter.",
        ),
    }
    diagnostic.update(details)
    return diagnostic


def _malformed(
    issue_id,
    source_path,
    message,
    line=None,
    field=None,
    current=None,
    expected="supported top-level scalar or list of scalars",
    recommendation=(
        "Use supported top-level scalar or list syntax in issue frontmatter."
    ),
):
    details = {}
    if line is not None:
        details["line"] = line
    return _diagnostic(
        "ISSUE_SCHEMA_MALFORMED",
        issue_id,
        source_path,
        message,
        field=field,
        current=current,
        expected=expected,
        recommendation=recommendation,
        **details,
    )


def _has_forbidden_token(value):
    """Detect YAML tags, anchors, and aliases outside quoted strings."""
    quote = None
    escaped = False
    index = 0
    while index < len(value):
        char = value[index]
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if quote == "'":
            if char == quote:
                if index + 1 < len(value) and value[index + 1] == "'":
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in ("'", '"'):
            quote = char
            index += 1
            continue
        if char in "&*!" and (
            index == 0 or value[index - 1].isspace() or value[index - 1] in "[,"
        ):
            return True
        index += 1
    return False


def _split_inline_items(inner):
    items = []
    start = 0
    quote = None
    escaped = False
    index = 0
    while index < len(inner):
        char = inner[index]
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if quote == "'":
            if char == quote:
                if index + 1 < len(inner) and inner[index + 1] == "'":
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in ("'", '"'):
            quote = char
            index += 1
        elif char == ",":
            items.append(inner[start:index].strip())
            start = index + 1
            index += 1
        else:
            index += 1
    if quote is not None:
        raise ValueError("unterminated quoted string")
    items.append(inner[start:].strip())
    return items


def _parse_scalar(value):
    value = value.strip()
    if not value:
        raise ValueError("empty list item")
    if _has_forbidden_token(value):
        raise ValueError("YAML tags, anchors, and aliases are not supported")
    if value.startswith("{") or value.endswith("}"):
        raise ValueError("nested mappings are not supported")
    if value.startswith("[") or value.endswith("]"):
        raise ValueError("nested lists are not supported")
    if value.startswith(("|", ">")):
        raise ValueError("multiline scalar syntax is not supported")
    if value.startswith('"'):
        if not value.endswith('"') or len(value) < 2:
            raise ValueError("unterminated quoted string")
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid double-quoted string") from exc
        if not isinstance(parsed, str):
            raise ValueError("quoted scalar must be a string")
        return parsed
    if value.startswith("'"):
        if not value.endswith("'") or len(value) < 2:
            raise ValueError("unterminated quoted string")
        inner = value[1:-1]
        index = 0
        while index < len(inner):
            if inner[index] != "'":
                index += 1
                continue
            if index + 1 >= len(inner) or inner[index + 1] != "'":
                raise ValueError("invalid single-quoted string")
            index += 2
        return inner.replace("''", "'")
    if value.endswith(("'", '"')):
        raise ValueError("unexpected quote")
    if re.match(r"[-?](?:\s|$)", value):
        raise ValueError("nested sequences and mappings are not supported")
    lowered = value.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("null", "~"):
        return None
    if _INTEGER_RE.fullmatch(value):
        return int(value)
    if re.search(r":(?:\s|$)", value):
        raise ValueError("nested mappings are not supported")
    return value


def _parse_value(value):
    value = value.strip()
    if value.startswith("["):
        if not value.endswith("]"):
            raise ValueError("unterminated inline list")
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item) for item in _split_inline_items(inner)]
    return _parse_scalar(value)


def parse_frontmatter_subset(frontmatter_text, issue_id, source_path):
    """Parse the supported frontmatter subset into ``(fields, diagnostics)``.

    Parsing errors never escape this function. Valid fields parsed before or
    after an invalid line remain available, while every invalid construct is
    represented by an ``ISSUE_SCHEMA_MALFORMED`` diagnostic.
    """
    fields = {}
    seen_keys = set()
    diagnostics = []
    lines = frontmatter_text.splitlines()
    index = 0

    while index < len(lines):
        raw = lines[index]
        line_number = index + 1
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if stripped in ("---", "..."):
            diagnostics.append(
                _malformed(
                    issue_id,
                    source_path,
                    "multiple YAML documents are not supported",
                    line=line_number,
                )
            )
            index += 1
            continue
        if raw.startswith((" ", "\t")):
            diagnostics.append(
                _malformed(
                    issue_id,
                    source_path,
                    "unexpected indentation or nested structure",
                    line=line_number,
                )
            )
            index += 1
            continue

        match = _KEY_RE.fullmatch(raw)
        if not match:
            diagnostics.append(
                _malformed(
                    issue_id,
                    source_path,
                    "expected a top-level key and scalar value",
                    line=line_number,
                )
            )
            index += 1
            continue

        key, raw_value = match.groups()
        if key in seen_keys:
            diagnostics.append(
                _malformed(
                    issue_id,
                    source_path,
                    f"duplicate key '{key}'",
                    line=line_number,
                    field=key,
                )
            )
            index += 1
            continue
        seen_keys.add(key)

        raw_value = raw_value or ""
        if raw_value.strip():
            try:
                fields[key] = _parse_value(raw_value)
            except ValueError as exc:
                diagnostics.append(
                    _malformed(
                        issue_id,
                        source_path,
                        str(exc),
                        line=line_number,
                        field=key,
                        current=raw_value.strip(),
                    )
                )
            index += 1
            continue

        # A blank value is either null or the head of an indented scalar list.
        lookahead = index + 1
        while lookahead < len(lines) and not lines[lookahead].strip():
            lookahead += 1
        if lookahead >= len(lines) or not lines[lookahead].startswith((" ", "\t")):
            fields[key] = None
            index += 1
            continue

        values = []
        nested_error = False
        cursor = lookahead
        list_indent = len(lines[lookahead]) - len(lines[lookahead].lstrip(" \t"))
        while cursor < len(lines) and lines[cursor].startswith((" ", "\t")):
            item_raw = lines[cursor]
            item_stripped = item_raw.strip()
            if not item_stripped:
                cursor += 1
                continue
            indent_end = len(item_raw) - len(item_raw.lstrip(" \t"))
            item_indent_text = item_raw[:indent_end]
            item_indent = len(item_indent_text)
            item_match = re.fullmatch(r"-\s+(.+)", item_stripped)
            if (
                not item_match
                or "\t" in item_indent_text
                or item_indent != list_indent
            ):
                diagnostics.append(
                    _malformed(
                        issue_id,
                        source_path,
                        "nested YAML structures are not supported",
                        line=cursor + 1,
                        field=key,
                    )
                )
                nested_error = True
                cursor += 1
                continue
            try:
                values.append(_parse_scalar(item_match.group(1)))
            except ValueError as exc:
                diagnostics.append(
                    _malformed(
                        issue_id,
                        source_path,
                        str(exc),
                        line=cursor + 1,
                        field=key,
                        current=item_match.group(1),
                    )
                )
                nested_error = True
            cursor += 1
        if not nested_error:
            fields[key] = values
        index = cursor

    return fields, diagnostics


def _normalized_dependency_id(value):
    return value.strip().strip("`").strip()


def validate_contract_field_types(fields, issue_id, source_path):
    """Return contract fields safe for adapters plus hard type diagnostics."""
    sanitized = dict(fields)
    diagnostics = []
    invalid_fields = set()

    for field in _SCALAR_CONTRACT_FIELDS:
        if field not in fields or isinstance(fields[field], str):
            continue
        invalid_fields.add(field)
        sanitized.pop(field, None)
        diagnostics.append(
            _malformed(
                issue_id,
                source_path,
                f"Contract field '{field}' must be a string.",
                field=field,
                current=fields[field],
                expected="string",
                recommendation=(
                    f"Set {field} to a supported top-level scalar string."
                ),
            )
        )

    declared_issue_id = fields.get("issue_id")
    if (
        "issue_id" in fields
        and "issue_id" not in invalid_fields
        and not validate_issue_id(declared_issue_id)
    ):
        invalid_fields.add("issue_id")
        sanitized.pop("issue_id", None)
        diagnostics.append(
            _malformed(
                issue_id,
                source_path,
                "Contract field 'issue_id' must be a safe filename-stem token.",
                field="issue_id",
                current=declared_issue_id,
                expected="^[A-Za-z0-9][A-Za-z0-9._-]*$",
                recommendation=(
                    "Set issue_id to a non-empty filename-stem token without "
                    "absolute paths, slashes, backslashes, or path segments."
                ),
            )
        )

    if "depends_on" in fields and (
        not isinstance(fields["depends_on"], list)
        or not all(isinstance(value, str) for value in fields["depends_on"])
        or any(
            not validate_issue_id(_normalized_dependency_id(value))
            for value in fields["depends_on"]
            if isinstance(value, str)
        )
    ):
        invalid_fields.add("depends_on")
        sanitized.pop("depends_on", None)
        diagnostics.append(
            _malformed(
                issue_id,
                source_path,
                "Contract field 'depends_on' must contain safe issue ID tokens.",
                field="depends_on",
                current=fields["depends_on"],
                expected="list of non-empty issue ID strings",
                recommendation=(
                    "Set depends_on to a supported top-level list of safe "
                    "issue filename-stem tokens; replace path-like or blank "
                    "dependency values."
                ),
            )
        )

    return sanitized, diagnostics, invalid_fields


def metadata_region(text):
    """Return the Markdown header region where issue metadata is valid."""
    _, body = split_frontmatter(text)
    match = re.search(r"^##\s", body, re.MULTILINE)
    return body[: match.start()] if match else body


def markdown_status(text):
    status = markdown_status_projection(text)
    if status is None:
        return "backlog"
    if status.startswith("superseded"):
        return "superseded"
    return status if status in LIFECYCLE_STATES else "backlog"


def _markdown_status_token(text):
    match = re.search(
        r"^\*\*Status:\s*([A-Za-z0-9_-]+)",
        metadata_region(text),
        re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1) if match else None


def markdown_status_projection(text):
    status = _markdown_status_token(text)
    return status.lower() if status else None


def markdown_superseded_by(text):
    """Return the validated successor encoded by a legacy status projection."""
    status = _markdown_status_token(text)
    prefix = "superseded-by-"
    if not status or not status.lower().startswith(prefix):
        return None
    target = status[len(prefix):]
    return target if validate_issue_id(target) else None


def markdown_priority(text):
    match = re.search(
        r"^\*\*Priority:\s*(p[0-3])\b",
        metadata_region(text),
        re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).lower() if match else "p2"


def markdown_blocked_by(text):
    match = re.search(
        r"^\*\*Blocked-by:\s*([^*\n]+)\*\*", metadata_region(text), re.MULTILINE
    )
    if not match:
        return []
    blocked_by = []
    for value in match.group(1).split(","):
        value = value.strip().strip("`").strip()
        if value and value not in blocked_by:
            blocked_by.append(value)
    return blocked_by


def has_markdown_blocked_by(text):
    return bool(
        re.search(r"^\*\*Blocked-by:\s*", metadata_region(text), re.MULTILINE)
    )


def markdown_title(text):
    _, body = split_frontmatter(text)
    for line in body.splitlines():
        if line.startswith("# "):
            heading = line[2:].strip()
            if ":" in heading:
                heading = heading.split(":", 1)[1].strip()
            return heading.strip("`").strip()
    return ""


def _relative_source_path(path, project_root):
    """Return a safe lexical source path without resolving symlink targets."""
    try:
        lexical_path = Path(os.path.abspath(path))
        lexical_root = Path(os.path.abspath(project_root))
        return str(lexical_path.relative_to(lexical_root))
    except (OSError, RuntimeError, ValueError):
        return Path(path).name


def _base_issue(path, project_root, text):
    source_path = _relative_source_path(path, project_root)
    source_issue_id = path.stem
    safe_issue_id = (
        source_issue_id if validate_issue_id(source_issue_id) else "invalid-issue"
    )
    raw_dependencies = markdown_blocked_by(text)
    invalid_dependencies = [
        dependency
        for dependency in raw_dependencies
        if not validate_issue_id(dependency)
    ]
    issue = {
        "schema": NORMALIZED_SCHEMA,
        "schema_version": None,
        "issue_id": safe_issue_id,
        "source_path": source_path,
        "source_format": "markdown",
        "title": markdown_title(text),
        "lifecycle_state": markdown_status(text),
        "projection_status": markdown_status(text),
        "superseded_by": markdown_superseded_by(text),
        "priority": markdown_priority(text),
        "blocked_by": _normalized_dependency_list(raw_dependencies),
        "advisory_blocked_by": [],
        "definition_readiness": None,
        "gate_state": None,
        "declared_phase": None,
        "artifact_phase": None,
        "declared_next_command": None,
        "recommended_next_command": None,
        "readiness": None,
        "extensions": {},
        "diagnostics": [],
    }
    if safe_issue_id != source_issue_id:
        issue["diagnostics"].append(
            _malformed(
                safe_issue_id,
                source_path,
                "Issue filename stem is not a safe issue ID token.",
                field="issue_id",
                current=source_issue_id,
                expected="^[A-Za-z0-9][A-Za-z0-9._-]*$",
                recommendation="Rename the issue file to a safe issue ID token.",
            )
        )
    if invalid_dependencies:
        issue["diagnostics"].append(
            _malformed(
                safe_issue_id,
                source_path,
                "Markdown Blocked-by contains unsafe issue ID tokens.",
                field="blocked_by",
                current=invalid_dependencies,
                expected="issue IDs matching ^[A-Za-z0-9][A-Za-z0-9._-]*$",
                recommendation=(
                    "Replace path-like dependency values with safe issue "
                    "filename-stem tokens."
                ),
            )
        )
    return issue


def _blocked_issue_source(path, project_root):
    """Build a minimal fail-closed record without reading an external target."""
    issue = _base_issue(path, project_root, "")
    issue["source_format"] = "blocked"
    issue["lifecycle_state"] = None
    issue["projection_status"] = None
    issue["readiness"] = "blocked"
    issue["diagnostics"].append(
        _diagnostic(
            "ISSUE_SOURCE_OUTSIDE_ROOT",
            issue["issue_id"],
            issue["source_path"],
            "Issue source resolves outside the configured issues root.",
            field="source",
            current=issue["source_path"],
            expected="a file resolving inside the configured issues root",
            recommendation=(
                "Replace the external symlink with a regular issue file or "
                "a symlink whose target remains inside the issues root."
            ),
        )
    )
    return issue


def _blocked_issues_root(project_root, source_path, current):
    """Build one synthetic hard record for an unsafe configured issues root."""
    path = Path(project_root) / "project-issues-root.md"
    issue = _base_issue(path, project_root, "")
    issue["issue_id"] = "project-issues-root"
    issue["source_path"] = source_path
    issue["source_format"] = "blocked"
    issue["lifecycle_state"] = None
    issue["projection_status"] = None
    issue["readiness"] = "blocked"
    issue["diagnostics"].append(
        _diagnostic(
            "ISSUE_SOURCE_OUTSIDE_ROOT",
            issue["issue_id"],
            source_path,
            "Configured issues root resolves outside the project root.",
            field="issues_root",
            current=current,
            expected="an issues directory resolving inside the project root",
            recommendation=(
                "Replace the external issues path or directory symlink with "
                "a path whose target remains inside the project root."
            ),
        )
    )
    return issue


def _adapter_diagnostic(
    issue,
    code,
    field,
    current,
    expected,
    message,
    recommendation,
    severity="error",
    origin=None,
):
    diagnostic = _diagnostic(
        code,
        issue["issue_id"],
        issue["source_path"],
        message,
        severity=severity,
        field=field,
        current=current,
        expected=expected,
        recommendation=recommendation,
    )
    if origin is not None:
        diagnostic["origin"] = origin
    return diagnostic


def _normalized_dependency_list(value):
    if not isinstance(value, list) or not all(
        isinstance(dependency, str) for dependency in value
    ):
        return []
    normalized = []
    for dependency in value:
        dependency = _normalized_dependency_id(dependency)
        if validate_issue_id(dependency) and dependency not in normalized:
            normalized.append(dependency)
    return normalized


def _extensions(fields):
    return {
        key: value for key, value in fields.items() if key not in _CONTRACT_FIELDS
    }


def normalize_markdown_issue(path, project_root, body, parse_diagnostics=None):
    issue = _base_issue(path, project_root, body)
    issue["diagnostics"].extend(parse_diagnostics or [])
    return issue


def normalize_frontmatter_0_1_0(
    path,
    project_root,
    fields,
    body,
    parse_diagnostics=None,
    invalid_fields=None,
):
    invalid_fields = invalid_fields or set()
    issue = _base_issue(path, project_root, body)
    version = fields["schema_version"]
    issue["source_format"] = f"frontmatter-{version}"
    issue["schema_version"] = version
    issue["superseded_by"] = None
    issue["diagnostics"].extend(parse_diagnostics or [])

    declared_issue_id = fields.get("issue_id")
    if (
        "issue_id" not in invalid_fields
        and validate_issue_id(declared_issue_id)
    ):
        issue["issue_id"] = declared_issue_id

    canonical_state = fields.get("canonical_state")
    canonical_state_is_valid = (
        isinstance(canonical_state, str) and canonical_state in LIFECYCLE_STATES
    )
    if "canonical_state" in invalid_fields:
        issue["lifecycle_state"] = None
    elif canonical_state_is_valid:
        issue["lifecycle_state"] = canonical_state
    else:
        issue["lifecycle_state"] = "backlog"
        issue["diagnostics"].append(
            _adapter_diagnostic(
                issue,
                "ISSUE_STATE_PROJECTION_MISMATCH",
                "canonical_state",
                canonical_state,
                "backlog, active, or done",
                "Versioned issues require a supported canonical lifecycle state.",
                "Set canonical_state to backlog, active, or done.",
            )
        )

    markdown_projection = markdown_status_projection(body)
    if canonical_state_is_valid and (
        markdown_projection not in LIFECYCLE_STATES
        or markdown_projection != canonical_state
    ):
        issue["diagnostics"].append(
            _adapter_diagnostic(
                issue,
                "ISSUE_STATE_PROJECTION_MISMATCH",
                "markdown_status",
                markdown_projection,
                canonical_state,
                "Markdown Status must project the canonical lifecycle state.",
                f"Set Markdown Status to {canonical_state or 'a valid canonical state'}.",
            )
        )

    auxiliary_status = fields.get("status")
    issue["projection_status"] = (
        auxiliary_status if isinstance(auxiliary_status, str) else None
    )
    if "status" in invalid_fields:
        pass
    elif isinstance(auxiliary_status, str) and auxiliary_status in (
        "ready",
        "blocked",
    ):
        issue["diagnostics"].append(
            _adapter_diagnostic(
                issue,
                "ISSUE_AUX_STATUS_INVALID",
                "status",
                auxiliary_status,
                "backlog, in_progress, or done",
                f"{auxiliary_status.capitalize()} is derived and cannot be declared as the lifecycle projection.",
                f"Set status to backlog, in_progress, or done and let the readiness gate calculate {auxiliary_status}.",
            )
        )
    elif not isinstance(auxiliary_status, str) or (
        auxiliary_status not in PROJECTION_TO_LIFECYCLE
    ):
        issue["diagnostics"].append(
            _adapter_diagnostic(
                issue,
                "ISSUE_AUX_STATUS_INVALID",
                "status",
                auxiliary_status,
                "backlog, in_progress, or done",
                "Versioned issue status must be a supported lifecycle projection.",
                "Set status to backlog, in_progress, or done.",
            )
        )
    elif canonical_state_is_valid and (
        PROJECTION_TO_LIFECYCLE[auxiliary_status] != canonical_state
    ):
        issue["diagnostics"].append(
            _adapter_diagnostic(
                issue,
                "ISSUE_STATE_PROJECTION_MISMATCH",
                "status",
                auxiliary_status,
                f"the projection for canonical_state {canonical_state}",
                "Auxiliary status must agree with canonical_state.",
                f"Set status to the lifecycle projection for {canonical_state}.",
            )
        )

    priority = fields.get("priority")
    if "priority" in invalid_fields:
        issue["priority"] = None
    elif isinstance(priority, str):
        issue["priority"] = priority.lower()
    if "depends_on" in invalid_fields:
        dependencies = None
        issue["blocked_by"] = []
    else:
        dependencies = _normalized_dependency_list(fields.get("depends_on"))
        issue["blocked_by"] = dependencies
    if dependencies is not None and has_markdown_blocked_by(body):
        markdown_dependencies = _normalized_dependency_list(markdown_blocked_by(body))
        if set(markdown_dependencies) != set(dependencies):
            issue["diagnostics"].append(
                _adapter_diagnostic(
                    issue,
                    "ISSUE_DEPENDENCY_PROJECTION_MISMATCH",
                    "blocked_by",
                    markdown_dependencies,
                    dependencies,
                    "Markdown Blocked-by must agree with canonical frontmatter depends_on.",
                    "Update Markdown Blocked-by to contain the same issue IDs as depends_on.",
                )
            )

    issue["definition_readiness"] = fields.get("definition_readiness")
    issue["gate_state"] = fields.get("gate_state")
    if invalid_fields.intersection(("phase", "declared_phase")):
        issue["declared_phase"] = None
    else:
        issue["declared_phase"] = fields.get(
            "phase", fields.get("declared_phase")
        )
    issue["declared_next_command"] = fields.get("next_command")
    issue["extensions"] = _extensions(fields)
    return issue


def normalize_unversioned_frontmatter(
    path,
    project_root,
    fields,
    body,
    parse_diagnostics=None,
    invalid_fields=None,
):
    invalid_fields = invalid_fields or set()
    issue = _base_issue(path, project_root, body)
    issue["source_format"] = "frontmatter-unversioned"
    issue["diagnostics"].extend(parse_diagnostics or [])
    if "depends_on" in invalid_fields:
        issue["advisory_blocked_by"] = []
    else:
        issue["advisory_blocked_by"] = _normalized_dependency_list(
            fields.get("depends_on")
        )
    issue["extensions"] = _extensions(fields)
    issue["diagnostics"].append(
        _adapter_diagnostic(
            issue,
            "ISSUE_FRONTMATTER_UNVERSIONED",
            "schema_version",
            None,
            "0.1.0",
            "Frontmatter without schema_version is advisory and cannot advance issue state.",
            "Migrate the frontmatter to schema_version 0.1.0 and reconcile its projections.",
            severity="warning",
        )
    )
    return issue


def normalize_unsupported_frontmatter(
    path,
    project_root,
    fields,
    body,
    parse_diagnostics=None,
    declared_version=None,
):
    issue = _base_issue(path, project_root, body)
    issue["source_format"] = "frontmatter-unsupported"
    issue["schema_version"] = fields.get("schema_version")
    declared_issue_id = fields.get("issue_id")
    issue["tentative_issue_id"] = (
        declared_issue_id
        if validate_issue_id(declared_issue_id)
        else None
    )
    issue["lifecycle_state"] = None
    issue["projection_status"] = None
    issue["superseded_by"] = None
    issue["blocked_by"] = []
    issue["readiness"] = "blocked"
    issue["extensions"] = _extensions(fields)
    issue["diagnostics"].extend(parse_diagnostics or [])
    issue["diagnostics"].append(
        _adapter_diagnostic(
            issue,
            "ISSUE_SCHEMA_UNSUPPORTED",
            "schema_version",
            declared_version,
            ", ".join(sorted(SUPPORTED_SCHEMA_VERSIONS)),
            "The issue schema version is unsupported and cannot be routed safely.",
            "Migrate the issue frontmatter to a supported schema_version before execution.",
        )
    )
    return issue


def parse_issue(path, project_root):
    """Read one Markdown issue and return the normalized issue read model."""
    path = Path(path)
    source_path = _relative_source_path(path, project_root)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        issue = _base_issue(path, project_root, "")
        issue["source_format"] = "unreadable"
        issue["lifecycle_state"] = None
        issue["projection_status"] = None
        issue["readiness"] = "blocked"
        issue["diagnostics"].append(
            _diagnostic(
                "ISSUE_SOURCE_UNREADABLE",
                path.stem,
                source_path,
                f"Issue source could not be read as UTF-8: {exc}",
                field="source",
                current=type(exc).__name__,
                expected="a readable UTF-8 issue file",
                recommendation=(
                    "Restore file readability and permissions, ensure the issue "
                    "is valid UTF-8, then run product:doctor."
                ),
            )
        )
        return issue

    frontmatter, body = split_frontmatter(text)
    if frontmatter is None:
        issue = normalize_markdown_issue(path, project_root, text)
        if text.lstrip("\ufeff").startswith("---"):
            issue["diagnostics"].append(
                _malformed(
                    path.stem,
                    source_path,
                    "frontmatter opening delimiter has no closing delimiter",
                )
            )
        return issue

    parsed_fields, diagnostics = parse_frontmatter_subset(
        frontmatter, path.stem, source_path
    )
    invalid_fields = {
        diagnostic["field"]
        for diagnostic in diagnostics
        if diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
        and diagnostic["field"] in _CONTRACT_FIELDS
    }
    fields, type_diagnostics, type_invalid_fields = validate_contract_field_types(
        parsed_fields, path.stem, source_path
    )
    diagnostics.extend(type_diagnostics)
    invalid_fields.update(type_invalid_fields)

    declared_version = parsed_fields.get("schema_version")
    has_declared_version = (
        "schema_version" in parsed_fields or "schema_version" in invalid_fields
    )
    version = fields.get("schema_version")
    if version in SUPPORTED_SCHEMA_VERSIONS:
        return normalize_frontmatter_0_1_0(
            path,
            project_root,
            fields,
            body,
            diagnostics,
            invalid_fields,
        )
    if not has_declared_version:
        return normalize_unversioned_frontmatter(
            path,
            project_root,
            fields,
            body,
            diagnostics,
            invalid_fields,
        )
    return normalize_unsupported_frontmatter(
        path,
        project_root,
        fields,
        body,
        diagnostics,
        declared_version,
    )


def list_normalized_issues(project_root, project_paths=None):
    """Return normalized issue records sorted by their canonical issue id."""
    project_root = Path(project_root)
    project_paths = project_paths or configured_project_paths(project_root)
    lexical_issues_dir = project_root / project_paths["issues"]
    try:
        issues_dir = _contained_path(project_root, project_paths["issues"])
    except ValueError:
        return [
            _blocked_issues_root(
                project_root,
                _relative_source_path(lexical_issues_dir, project_root),
                _relative_source_path(lexical_issues_dir, project_root),
            )
        ]
    if not issues_dir.is_dir():
        return []
    issues = []
    for path in sorted(lexical_issues_dir.glob("*.md")):
        try:
            resolved = _contained_path(issues_dir, path.name)
        except ValueError:
            issues.append(_blocked_issue_source(path, project_root))
            continue
        if resolved.is_file():
            issues.append(parse_issue(path, project_root))
    return sorted(issues, key=lambda issue: issue["issue_id"])


def _empty_artifact_coverage():
    return {
        **{phase: False for phase in _ARTIFACT_PHASES},
        "artifact_phase": "issue",
        "diagnostics": [],
    }


def _artifact_outside_root_diagnostic(issue_id, source_path):
    return _diagnostic(
        "ISSUE_ARTIFACT_OUTSIDE_ROOT",
        issue_id,
        source_path,
        "Issue artifact resolves outside the configured specs root.",
        field="artifact",
        current=source_path,
        expected="a path resolving inside the configured specs root",
        recommendation=(
            "Replace the external symlink with a regular artifact or a symlink "
            "whose target remains inside the specs root."
        ),
        origin="evaluator",
    )


def build_artifact_index(project_root, issue_ids, project_paths=None):
    """Return actual workflow-artifact coverage for each supplied issue id."""
    project_root = Path(project_root)
    project_paths = project_paths or configured_project_paths(project_root)
    lexical_specs_root = project_root / project_paths["specs"]
    try:
        specs_root = _contained_path(project_root, project_paths["specs"])
    except ValueError:
        specs_root = None
    artifact_index = {}
    for issue_id in sorted(set(issue_ids), key=str):
        coverage = _empty_artifact_coverage()
        if not validate_issue_id(issue_id):
            artifact_index[issue_id] = coverage
            continue
        artifact_source = _relative_source_path(
            lexical_specs_root / issue_id,
            project_root,
        )
        if specs_root is None:
            coverage["diagnostics"].append(
                _artifact_outside_root_diagnostic(issue_id, artifact_source)
            )
            artifact_index[issue_id] = coverage
            continue
        try:
            _contained_path(specs_root, issue_id)
        except ValueError:
            coverage["diagnostics"].append(
                _artifact_outside_root_diagnostic(issue_id, artifact_source)
            )
            artifact_index[issue_id] = coverage
            continue
        for phase in _ARTIFACT_PHASES:
            artifact_file_source = _relative_source_path(
                lexical_specs_root / issue_id / f"{phase}.md",
                project_root,
            )
            try:
                artifact_file = _contained_path(
                    specs_root,
                    issue_id,
                    f"{phase}.md",
                )
            except ValueError:
                coverage["diagnostics"].append(
                    _artifact_outside_root_diagnostic(
                        issue_id,
                        artifact_file_source,
                    )
                )
                continue
            coverage[phase] = artifact_file.is_file()
        present_phases = [phase for phase in _ARTIFACT_PHASES if coverage[phase]]
        coverage["artifact_phase"] = (
            present_phases[-1] if present_phases else "issue"
        )
        artifact_index[issue_id] = coverage
    return artifact_index


def _issue_dependencies(issue):
    dependencies = []
    for field in ("blocked_by", "advisory_blocked_by"):
        for dependency in issue.get(field) or []:
            if dependency not in dependencies:
                dependencies.append(dependency)
    return dependencies


def _dependency_diagnostic(
    issue,
    code,
    current,
    expected,
    message,
    recommendation,
    severity="error",
):
    return _adapter_diagnostic(
        issue,
        code,
        "depends_on",
        current,
        expected,
        message,
        recommendation,
        severity=severity,
    )


def _unmet_dependency_severity(issue):
    declared_command = issue.get("declared_next_command")
    claims_execute = (
        isinstance(declared_command, str)
        and declared_command.startswith("product:execute")
    )
    if issue.get("lifecycle_state") == "active" or claims_execute:
        return "error"
    return "warning"


def _strongly_connected_components(graph):
    """Return graph components using iterative Kosaraju traversal."""
    visited = set()
    finish_order = []
    for start in sorted(graph):
        if start in visited:
            continue
        visited.add(start)
        stack = [(start, 0)]
        while stack:
            node, dependency_index = stack[-1]
            dependencies = graph[node]
            if dependency_index < len(dependencies):
                dependency = dependencies[dependency_index]
                stack[-1] = (node, dependency_index + 1)
                if dependency not in visited:
                    visited.add(dependency)
                    stack.append((dependency, 0))
                continue
            stack.pop()
            finish_order.append(node)

    reverse_graph = {issue_id: [] for issue_id in graph}
    for issue_id in sorted(graph):
        for dependency in graph[issue_id]:
            reverse_graph[dependency].append(issue_id)

    assigned = set()
    components = []
    for start in reversed(finish_order):
        if start in assigned:
            continue
        assigned.add(start)
        component = set()
        stack = [start]
        while stack:
            node = stack.pop()
            component.add(node)
            for predecessor in reversed(reverse_graph[node]):
                if predecessor not in assigned:
                    assigned.add(predecessor)
                    stack.append(predecessor)
        components.append(component)
    return components


def _ordered_back_edge_cycle_paths(graph):
    """Return the real cycles reported by legacy ordered iterative DFS."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {issue_id: WHITE for issue_id in graph}
    reported_cycles = set()
    cycle_paths = []

    for start in sorted(graph):
        if color[start] != WHITE:
            continue
        color[start] = GRAY
        path = [start]
        stack = [(start, 0)]
        while stack:
            node, dependency_index = stack[-1]
            dependencies = graph[node]
            if dependency_index < len(dependencies):
                dependency = dependencies[dependency_index]
                stack[-1] = (node, dependency_index + 1)
                if color[dependency] == GRAY:
                    cycle_start = path.index(dependency)
                    cycle_path = path[cycle_start:] + [dependency]
                    cycle_key = tuple(sorted(set(cycle_path)))
                    if cycle_key not in reported_cycles:
                        reported_cycles.add(cycle_key)
                        cycle_paths.append(cycle_path)
                elif color[dependency] == WHITE:
                    color[dependency] = GRAY
                    path.append(dependency)
                    stack.append((dependency, 0))
                continue
            stack.pop()
            path.pop()
            color[node] = BLACK

    return cycle_paths


def _cycle_path_through_member(graph, component, start):
    """Return a deterministic real-edge cycle containing ``start``."""
    visited = {start}
    path = [start]
    stack = [(start, 0)]
    while stack:
        node, dependency_index = stack[-1]
        dependencies = graph[node]
        if dependency_index < len(dependencies):
            dependency = dependencies[dependency_index]
            stack[-1] = (node, dependency_index + 1)
            if dependency not in component:
                continue
            if dependency == start and len(path) > 1:
                return path + [start]
            if dependency in visited:
                continue
            visited.add(dependency)
            path.append(dependency)
            stack.append((dependency, 0))
            continue
        stack.pop()
        path.pop()

    raise RuntimeError("strongly connected component has no representative cycle")


def dependency_diagnostics(issue_index, ambiguous_targets=None):
    """Return dependency errors by issue id using iterative graph traversal."""
    diagnostics = {}
    ambiguous_targets = ambiguous_targets or {}

    def add(issue_id, diagnostic):
        diagnostics.setdefault(issue_id, []).append(diagnostic)

    open_issue_ids = {
        issue_id
        for issue_id, issue in issue_index.items()
        if issue.get("lifecycle_state") not in ("done", "superseded")
    }
    graph = {}
    for issue_id in sorted(issue_index):
        issue = issue_index[issue_id]
        if issue_id not in open_issue_ids:
            continue
        raw_dependencies = _issue_dependencies(issue)
        invalid_dependencies = [
            dependency
            for dependency in raw_dependencies
            if not validate_issue_id(dependency)
        ]
        for dependency in invalid_dependencies:
            add(
                issue_id,
                _dependency_diagnostic(
                    issue,
                    "ISSUE_SCHEMA_MALFORMED",
                    dependency,
                    "an issue ID matching ^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    f"Dependency {dependency!r} is not a safe issue ID token.",
                    "Replace the dependency with a safe filename-stem issue ID, then run product:doctor.",
                ),
            )
        dependencies = [
            dependency
            for dependency in raw_dependencies
            if validate_issue_id(dependency)
        ]
        graph[issue_id] = [
            dependency
            for dependency in dependencies
            if dependency in open_issue_ids
            and dependency not in ambiguous_targets
        ]
        for dependency in dependencies:
            if dependency in ambiguous_targets:
                source_paths = sorted(ambiguous_targets[dependency])
                add(
                    issue_id,
                    _dependency_diagnostic(
                        issue,
                        "ISSUE_DUPLICATE_FIELD",
                        {
                            "issue_id": dependency,
                            "source_paths": source_paths,
                        },
                        "one unique dependency target",
                        f"Dependency target {dependency} has multiple issue definitions: {', '.join(source_paths)}.",
                        f"Assign a unique issue_id to all but one definition of {dependency}, then run product:doctor.",
                    ),
                )
                continue
            blocker = issue_index.get(dependency)
            if blocker is None:
                add(
                    issue_id,
                    _dependency_diagnostic(
                        issue,
                        "ISSUE_DEPENDENCY_DANGLING",
                        dependency,
                        "an existing issue id",
                        f"Dependency {dependency} does not exist in the project issue index.",
                        f"Create {dependency} or remove it from depends_on before routing {issue_id}.",
                    ),
                )
                continue
            blocker_state = blocker.get("lifecycle_state")
            if blocker_state not in ("done", "superseded"):
                add(
                    issue_id,
                    _dependency_diagnostic(
                        issue,
                        "ISSUE_DEPENDENCY_UNMET",
                        f"{dependency}: {blocker_state or 'unknown'}",
                        "done or superseded",
                        f"Dependency {dependency} is unfinished and blocks {issue_id}.",
                        f"Complete or supersede {dependency}, then run product:status.",
                        severity=_unmet_dependency_severity(issue),
                    ),
                )

    cycle_groups = []
    for component in _strongly_connected_components(graph):
        if len(component) > 1:
            cycle_groups.append(component)
            continue
        issue_id = next(iter(component))
        if issue_id in graph[issue_id]:
            cycle_groups.append(component)

    ordered_cycle_paths = _ordered_back_edge_cycle_paths(graph)
    cycle_groups = sorted(cycle_groups, key=lambda group: sorted(group))
    cycle_group_by_member = {
        member: frozenset(cycle_members)
        for cycle_members in cycle_groups
        for member in cycle_members
    }
    paths_by_group = {
        frozenset(cycle_members): [] for cycle_members in cycle_groups
    }
    for cycle_path in ordered_cycle_paths:
        cycle_group = cycle_group_by_member[cycle_path[0]]
        paths_by_group[cycle_group].append(list(cycle_path))

    for cycle_members in cycle_groups:
        representative_issue_id = min(cycle_members)
        cycle_paths = paths_by_group[frozenset(cycle_members)]
        covered_members = {
            member for cycle_path in cycle_paths for member in cycle_path[:-1]
        }
        for uncovered_member in sorted(cycle_members - covered_members):
            if uncovered_member in covered_members:
                continue
            cycle_path = _cycle_path_through_member(
                graph, cycle_members, uncovered_member
            )
            cycle_paths.append(cycle_path)
            covered_members.update(cycle_path[:-1])
        cycle_path = cycle_paths[0]
        for issue_id in sorted(cycle_members):
            issue = issue_index[issue_id]
            current = {
                "issue_id": issue_id,
                "representative_issue_id": representative_issue_id,
                "component_size": len(cycle_members),
            }
            diagnostic = _dependency_diagnostic(
                issue,
                "ISSUE_DEPENDENCY_CYCLE",
                current,
                "an acyclic dependency graph",
                f"Issue {issue_id} participates in a dependency cycle.",
                "Remove or redirect a depends_on edge in the cycle, then run product:status.",
            )
            if issue_id == representative_issue_id:
                diagnostic["cycle_path"] = list(cycle_path)
                diagnostic["cycle_paths"] = [
                    list(path) for path in cycle_paths
                ]
            add(
                issue_id,
                diagnostic,
            )

    return diagnostics


def _has_diagnostic(issue, codes):
    return any(diagnostic["code"] in codes for diagnostic in issue["diagnostics"])


def _has_early_projection_error(issue):
    return any(
        diagnostic["code"] in _PROJECTION_ERROR_CODES
        and not (
            diagnostic["code"] == "ISSUE_STATE_PROJECTION_MISMATCH"
            and diagnostic["field"] == "phase"
        )
        for diagnostic in issue["diagnostics"]
    )


def _has_artifact_phase_drift(issue):
    return any(
        diagnostic["code"] == "ISSUE_STATE_PROJECTION_MISMATCH"
        and diagnostic["field"] == "phase"
        for diagnostic in issue["diagnostics"]
    )


def _append_unique_diagnostic(issue, diagnostic):
    identity = (
        diagnostic["code"],
        diagnostic["field"],
        repr(diagnostic["current"]),
    )
    if not any(
        (
            existing["code"],
            existing["field"],
            repr(existing["current"]),
        )
        == identity
        for existing in issue["diagnostics"]
    ):
        issue["diagnostics"].append(copy.deepcopy(diagnostic))


def _is_evaluator_diagnostic(diagnostic):
    code = diagnostic["code"]
    if code in _DEPENDENCY_ERROR_CODES or code in {
        "ISSUE_ARTIFACT_OUTSIDE_ROOT",
        "ISSUE_DEFINITION_NOT_READY",
        "ISSUE_GATE_BLOCKED",
        "ISSUE_NEXT_COMMAND_INVALID",
    }:
        return True
    if (
        code == "ISSUE_STATE_PROJECTION_MISMATCH"
        and diagnostic["field"] == "phase"
    ):
        return True
    if (
        code == "ISSUE_SCHEMA_MALFORMED"
        and diagnostic["field"] == "phase"
        and diagnostic.get("origin") == "evaluator"
    ):
        return True
    return code == "ISSUE_DUPLICATE_FIELD" and diagnostic["field"] in {
        "issue_id",
        "depends_on",
        "blocked_by",
    }


def _parser_diagnostics(issue):
    return [
        copy.deepcopy(diagnostic)
        for diagnostic in issue.get("diagnostics", [])
        if not _is_evaluator_diagnostic(diagnostic)
    ]


def _is_recognized_versioned(issue):
    return issue.get("source_format") == "frontmatter-0.1.0"


def _append_structural_state_diagnostics(issue):
    if not _is_recognized_versioned(issue):
        return

    issue_id = issue["issue_id"]
    definition = issue.get("definition_readiness")
    definition_is_malformed = any(
        diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
        and diagnostic["field"] == "definition_readiness"
        for diagnostic in issue["diagnostics"]
    )
    if definition != "ready" and not definition_is_malformed:
        expected = (
            "ready" if definition == "draft" else "draft or ready"
        )
        _append_unique_diagnostic(
            issue,
            _adapter_diagnostic(
                issue,
                "ISSUE_DEFINITION_NOT_READY",
                "definition_readiness",
                definition,
                expected,
                "The recognized issue definition is not ready for execution.",
                f"Set definition_readiness to ready after running product:spec {issue_id}.",
            ),
        )

    gate = issue.get("gate_state")
    gate_is_malformed = any(
        diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
        and diagnostic["field"] == "gate_state"
        for diagnostic in issue["diagnostics"]
    )
    if gate != "passed" and not gate_is_malformed:
        expected = (
            "passed"
            if gate in GATE_STATE_VALUES
            else "pending, in_progress, blocked, or passed"
        )
        _append_unique_diagnostic(
            issue,
            _adapter_diagnostic(
                issue,
                "ISSUE_GATE_BLOCKED",
                "gate_state",
                gate,
                expected,
                "The recognized issue gate is unresolved or invalid.",
                f"Set a supported gate_state and run product:review {issue_id} until it passes.",
            ),
        )

    declared_phase = issue.get("declared_phase")
    if declared_phase is None:
        return
    actual_phase = issue["artifact_phase"]
    mapped_phase = DECLARED_PHASE_TO_ARTIFACT_PHASE.get(declared_phase)
    if mapped_phase is None:
        expected = ", ".join(DECLARED_PHASE_TO_ARTIFACT_PHASE)
        _append_unique_diagnostic(
            issue,
            _adapter_diagnostic(
                issue,
                "ISSUE_SCHEMA_MALFORMED",
                "phase",
                declared_phase,
                expected,
                "The declared phase is unsupported by the structural evaluator.",
                f"Set phase to one of {expected}.",
                origin="evaluator",
            ),
        )
    elif mapped_phase != actual_phase:
        _append_unique_diagnostic(
            issue,
            _adapter_diagnostic(
                issue,
                "ISSUE_STATE_PROJECTION_MISMATCH",
                "phase",
                declared_phase,
                actual_phase,
                "The declared phase does not match actual artifact coverage.",
                f"Align the artifacts to {declared_phase} or declare the actual {actual_phase} phase.",
            ),
        )


def derive_structural_route(issue, issue_index, artifact_index):
    """Derive structural readiness and command using first-blocker precedence."""
    issue_id = issue["issue_id"]
    if _has_diagnostic(issue, _SCHEMA_ERROR_CODES):
        return "blocked", "product:doctor"
    if _has_early_projection_error(issue):
        return "blocked", "product:doctor"
    if _has_diagnostic(issue, _DEPENDENCY_ERROR_CODES):
        return "blocked", "product:status"
    if issue.get("lifecycle_state") in ("done", "superseded"):
        return "not_ready", "product:status"
    if issue.get("definition_readiness") == "draft" or (
        _is_recognized_versioned(issue)
        and issue.get("definition_readiness") not in DEFINITION_READINESS_VALUES
    ):
        return "blocked", f"product:spec {issue_id}"

    coverage = artifact_index.get(issue_id, {})
    if not coverage.get("spec", False):
        return "not_ready", f"product:spec {issue_id}"
    if not coverage.get("plan", False):
        return "not_ready", f"product:plan {issue_id}"
    if not coverage.get("tasks", False):
        return "not_ready", f"product:plan {issue_id}"
    if _has_artifact_phase_drift(issue):
        return "blocked", "product:doctor"
    if issue.get("gate_state") in ("blocked", "pending", "in_progress") or (
        _is_recognized_versioned(issue)
        and issue.get("gate_state") not in GATE_STATE_VALUES
    ):
        return "blocked", f"product:review {issue_id}"
    if _has_diagnostic(issue, {"ISSUE_AUX_STATUS_INVALID"}):
        return "blocked", "product:doctor"
    return "ready", f"product:execute {issue_id}"


def _evaluate_issue_after_dependency(issue, issue_index, artifact_index):
    evaluated = dict(issue)
    evaluated["diagnostics"] = copy.deepcopy(issue.get("diagnostics", []))
    coverage = artifact_index.get(issue["issue_id"], {})
    for diagnostic in coverage.get("diagnostics", []):
        _append_unique_diagnostic(evaluated, diagnostic)
    evaluated["artifact_phase"] = coverage.get("artifact_phase", "issue")
    _append_structural_state_diagnostics(evaluated)

    readiness, command = derive_structural_route(
        evaluated, issue_index, artifact_index
    )
    evaluated["readiness"] = readiness
    evaluated["recommended_next_command"] = command

    declared = evaluated.get("declared_next_command")
    if declared is not None and declared != command:
        _append_unique_diagnostic(
            evaluated,
            _adapter_diagnostic(
                evaluated,
                "ISSUE_NEXT_COMMAND_INVALID",
                "next_command",
                declared,
                command,
                "The declared next command skips or disagrees with the structural route.",
                f"Set next_command to {command} or complete the earlier gate first.",
            ),
        )
    return evaluated


def evaluate_issue(issue, issue_index, artifact_index):
    """Evaluate one issue against project dependencies and actual artifacts."""
    prepared = dict(issue)
    prepared["diagnostics"] = _parser_diagnostics(issue)
    for diagnostic in dependency_diagnostics(issue_index).get(
        issue["issue_id"], []
    ):
        _append_unique_diagnostic(prepared, diagnostic)
    return _evaluate_issue_after_dependency(prepared, issue_index, artifact_index)


def _duplicate_issue_diagnostic(issue, source_paths):
    return _adapter_diagnostic(
        issue,
        "ISSUE_DUPLICATE_FIELD",
        "issue_id",
        source_paths,
        "a unique issue id",
        f"Issue ID {issue['issue_id']} is declared by multiple issue files.",
        "Assign a unique issue_id to every colliding source file, then run product:doctor.",
    )


def evaluate_project(project_root):
    """Return evaluated issues and project-level dependency diagnostics."""
    project_root = Path(project_root)
    project_paths = configured_project_paths(project_root)
    issues = list_normalized_issues(project_root, project_paths)
    configured_issues_violation = _configured_path_violations(
        project_root
    ).get("issues")
    if configured_issues_violation is not None and not any(
        any(
            diagnostic.get("code") == "ISSUE_SOURCE_OUTSIDE_ROOT"
            and diagnostic.get("field") == "issues_root"
            for diagnostic in issue.get("diagnostics", [])
        )
        for issue in issues
    ):
        issues.append(
            _blocked_issues_root(
                project_root,
                ".moduflow/config.json",
                configured_issues_violation,
            )
        )
    return _evaluate_issue_records(project_root, issues, project_paths)


def _evaluate_issue_records(project_root, issues, project_paths=None):
    """Evaluate already-normalized records using the shared project evaluator."""
    project_root = Path(project_root)
    project_paths = project_paths or configured_project_paths(project_root)
    issues_by_id = {}
    for issue in issues:
        issues_by_id.setdefault(issue["issue_id"], []).append(issue)
    duplicate_paths = {
        issue_id: sorted(issue["source_path"] for issue in matching)
        for issue_id, matching in issues_by_id.items()
        if len(matching) > 1
    }
    issue_index = {
        issue_id: matching[0]
        for issue_id, matching in issues_by_id.items()
        if issue_id not in duplicate_paths
    }
    artifact_index = build_artifact_index(
        project_root, issues_by_id, project_paths
    )
    project_dependency_diagnostics = dependency_diagnostics(
        issue_index, duplicate_paths
    )
    evaluated = []
    for issue in issues:
        prepared = dict(issue)
        prepared["diagnostics"] = copy.deepcopy(issue["diagnostics"])
        if issue["issue_id"] in duplicate_paths:
            _append_unique_diagnostic(
                prepared,
                _duplicate_issue_diagnostic(
                    issue, duplicate_paths[issue["issue_id"]]
                ),
            )
        else:
            for diagnostic in project_dependency_diagnostics.get(
                issue["issue_id"], []
            ):
                _append_unique_diagnostic(prepared, diagnostic)
        evaluated.append(
            _evaluate_issue_after_dependency(prepared, issue_index, artifact_index)
        )
    return {
        "project_root": str(project_root.resolve()),
        "issues": evaluated,
        "dependency_diagnostics": project_dependency_diagnostics,
    }


def _routing_summary(issue):
    return {
        "lifecycle_state": issue.get("lifecycle_state"),
        "readiness": issue.get("readiness"),
        "recommended_next_command": issue.get("recommended_next_command"),
    }


def _diagnostic_summary(diagnostics):
    return {
        "errors": sum(
            diagnostic.get("severity") == "error"
            for diagnostic in diagnostics
        ),
        "warnings": sum(
            diagnostic.get("severity") == "warning"
            for diagnostic in diagnostics
        ),
        "codes": sorted(
            {diagnostic.get("code") for diagnostic in diagnostics}
        ),
    }


def _source_contract(project_root, issue):
    """Return already-supported parsed fields and body for report projection."""
    path = Path(project_root) / issue["source_path"]
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return path, {}, "", set()
    frontmatter, body = split_frontmatter(text)
    if frontmatter is None:
        return path, {}, text, set()

    parsed_fields, parse_diagnostics = parse_frontmatter_subset(
        frontmatter, path.stem, issue["source_path"]
    )
    fields, type_diagnostics, type_invalid_fields = validate_contract_field_types(
        parsed_fields, path.stem, issue["source_path"]
    )
    invalid_fields = {
        diagnostic.get("field")
        for diagnostic in parse_diagnostics
        if diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
        and diagnostic.get("field") in _CONTRACT_FIELDS
    }
    invalid_fields.update(type_invalid_fields)
    return path, fields, body, invalid_fields


def _safe_mapping(field, value, reason):
    return {
        "field": field,
        "value": copy.deepcopy(value),
        "reason": reason,
    }


def _human_decision(field, current, reason, recommendation):
    return {
        "field": field,
        "current": copy.deepcopy(current),
        "reason": reason,
        "recommendation": recommendation,
    }


def _decision_from_diagnostic(diagnostic):
    decision = _human_decision(
        diagnostic.get("field") or "frontmatter",
        diagnostic.get("current"),
        diagnostic.get("message"),
        diagnostic.get("recommendation"),
    )
    decision["expected"] = copy.deepcopy(diagnostic.get("expected"))
    return decision


def _unversioned_field_decisions(fields, body, invalid_fields):
    validators = {
        "issue_id": lambda value: isinstance(value, str) and bool(value.strip()),
        "canonical_state": lambda value: value in LIFECYCLE_STATES,
        "status": lambda value: value in PROJECTION_TO_LIFECYCLE,
        "priority": lambda value: isinstance(value, str) and bool(value.strip()),
        "definition_readiness": lambda value: value in DEFINITION_READINESS_VALUES,
        "gate_state": lambda value: value in GATE_STATE_VALUES,
        "depends_on": lambda value: isinstance(value, list)
        and all(isinstance(item, str) for item in value),
        "next_command": lambda value: isinstance(value, str) and bool(value.strip()),
    }
    decisions = []
    for field in validators:
        value = fields.get(field)
        if field in invalid_fields:
            reason = "The advisory field is malformed and cannot become canonical truth."
        elif field not in fields:
            reason = "The required canonical field is missing."
        elif not validators[field](value):
            reason = "The advisory value is not a supported canonical value."
        else:
            continue
        decisions.append(
            _human_decision(
                field,
                value,
                reason,
                f"Choose a valid {field} value before adding schema_version 0.1.0.",
            )
        )

    canonical = fields.get("canonical_state")
    status = fields.get("status")
    if (
        canonical in LIFECYCLE_STATES
        and status in PROJECTION_TO_LIFECYCLE
        and PROJECTION_TO_LIFECYCLE[status] != canonical
    ):
        decisions.append(
            _human_decision(
                "status",
                status,
                "The advisory status conflicts with advisory canonical_state.",
                f"Choose status {LIFECYCLE_TO_PROJECTION[canonical]} or revise canonical_state.",
            )
        )
    markdown_projection = markdown_status_projection(body)
    if (
        canonical in LIFECYCLE_STATES
        and markdown_projection != canonical
    ):
        decisions.append(
            _human_decision(
                "markdown_status",
                markdown_projection,
                "Markdown Status conflicts with advisory canonical_state.",
                "Choose the canonical lifecycle state before versioning the frontmatter.",
            )
        )
    if "depends_on" in fields and has_markdown_blocked_by(body):
        frontmatter_dependencies = _normalized_dependency_list(
            fields.get("depends_on")
        )
        markdown_dependencies = _normalized_dependency_list(
            markdown_blocked_by(body)
        )
        if set(frontmatter_dependencies) != set(markdown_dependencies):
            decisions.append(
                _human_decision(
                    "depends_on",
                    fields.get("depends_on"),
                    "Frontmatter dependencies conflict with Markdown Blocked-by.",
                    "Choose one dependency set before versioning the frontmatter.",
                )
            )
    unique = {}
    for decision in decisions:
        unique.setdefault(decision["field"], decision)
    return [unique[field] for field in sorted(unique)]


def _classify_migration_issue(project_root, issue):
    path, fields, body, invalid_fields = _source_contract(project_root, issue)
    source_format = issue["source_format"]
    safe_mappings = []
    human_decisions = [
        _decision_from_diagnostic(diagnostic)
        for diagnostic in issue["diagnostics"]
        if diagnostic["code"] == "ISSUE_SCHEMA_MALFORMED"
    ]
    proposed_changes = {}
    proposed_issue_id = None
    projected = copy.deepcopy(issue)
    addressed = set()

    if source_format == "frontmatter-0.1.0":
        declared_canonical = fields.get("canonical_state")
        canonical = (
            declared_canonical
            if declared_canonical in LIFECYCLE_STATES
            else None
        )
        desired_status = LIFECYCLE_TO_PROJECTION.get(canonical)
        for diagnostic in issue["diagnostics"]:
            code = diagnostic["code"]
            field = diagnostic.get("field")
            if (
                code == "ISSUE_STATE_PROJECTION_MISMATCH"
                and field == "markdown_status"
                and canonical in LIFECYCLE_STATES
            ):
                proposed_changes["align_markdown_status"] = canonical
                safe_mappings.append(
                    _safe_mapping(
                        "markdown_status",
                        canonical,
                        "Markdown Status deterministically projects canonical_state.",
                    )
                )
                addressed.add((code, field))
            elif (
                code in {
                    "ISSUE_STATE_PROJECTION_MISMATCH",
                    "ISSUE_AUX_STATUS_INVALID",
                }
                and field == "status"
                and desired_status is not None
            ):
                proposed_changes["align_frontmatter_status"] = desired_status
                safe_mappings.append(
                    _safe_mapping(
                        "status",
                        desired_status,
                        "Frontmatter status deterministically projects canonical_state.",
                    )
                )
                addressed.add((code, field))
                projected["projection_status"] = desired_status
            elif (
                code == "ISSUE_DEPENDENCY_PROJECTION_MISMATCH"
                and field == "blocked_by"
            ):
                dependencies = list(issue.get("blocked_by") or [])
                proposed_changes["align_dependency_projection"] = dependencies
                safe_mappings.append(
                    _safe_mapping(
                        "markdown_blocked_by",
                        dependencies,
                        "Markdown Blocked-by deterministically projects depends_on.",
                    )
                )
                addressed.add((code, field))
            elif code in {
                "ISSUE_SCHEMA_MALFORMED",
                "ISSUE_DUPLICATE_FIELD",
                "ISSUE_SCHEMA_UNSUPPORTED",
            } or (
                code == "ISSUE_STATE_PROJECTION_MISMATCH"
                and field in {"canonical_state", "phase"}
            ):
                human_decisions.append(_decision_from_diagnostic(diagnostic))

        projected["diagnostics"] = [
            copy.deepcopy(diagnostic)
            for diagnostic in _parser_diagnostics(projected)
            if (diagnostic["code"], diagnostic.get("field")) not in addressed
        ]

    elif source_format == "frontmatter-unversioned":
        candidate_issue_id = fields.get("issue_id")
        if (
            isinstance(candidate_issue_id, str)
            and candidate_issue_id.strip()
            and "issue_id" not in invalid_fields
        ):
            proposed_issue_id = candidate_issue_id
        malformed_fields = {
            decision["field"]
            for decision in human_decisions
            if "expected" in decision
        }
        human_decisions.extend(
            decision
            for decision in _unversioned_field_decisions(
                fields, body, invalid_fields
            )
            if decision["field"] not in malformed_fields
        )
        for field in (
            "issue_id",
            "canonical_state",
            "status",
            "priority",
            "definition_readiness",
            "gate_state",
            "depends_on",
            "next_command",
        ):
            if field in fields and field not in {
                decision["field"] for decision in human_decisions
            }:
                safe_mappings.append(
                    _safe_mapping(
                        field,
                        fields[field],
                        "The advisory value is syntactically valid but remains a proposal until the full contract is unambiguous.",
                    )
                )
        if not human_decisions:
            proposed_changes["set_schema_version"] = "0.1.0"
            safe_mappings.append(
                _safe_mapping(
                    "schema_version",
                    "0.1.0",
                    "Every required canonical field maps unambiguously.",
                )
            )
            projected_fields = dict(fields)
            projected_fields["schema_version"] = "0.1.0"
            projected = normalize_frontmatter_0_1_0(
                path,
                project_root,
                projected_fields,
                body,
            )
        else:
            projected["diagnostics"] = _parser_diagnostics(projected)

    elif source_format == "frontmatter-unsupported":
        proposed_issue_id = issue.get("tentative_issue_id")
        if not any(
            decision["field"] == "schema_version"
            and "expected" in decision
            for decision in human_decisions
        ):
            human_decisions.append(
                _human_decision(
                    "schema_version",
                    issue.get("schema_version"),
                    "The declared schema version is unsupported.",
                    "Choose a supported schema and map its fields explicitly.",
                )
            )
        for field in sorted(issue.get("extensions", {})):
            human_decisions.append(
                _human_decision(
                    field,
                    issue["extensions"][field],
                    "The field is unknown to the supported schema.",
                    "Decide whether to preserve, rename, or remove this field.",
                )
            )
        projected["diagnostics"] = _parser_diagnostics(projected)

    else:
        human_decisions.extend(
            _decision_from_diagnostic(diagnostic)
            for diagnostic in issue["diagnostics"]
            if diagnostic["code"] in {
                "ISSUE_SOURCE_UNREADABLE",
                "ISSUE_SCHEMA_MALFORMED",
                "ISSUE_DUPLICATE_FIELD",
            }
        )
        projected["diagnostics"] = _parser_diagnostics(projected)

    safe_mappings.sort(key=lambda mapping: mapping["field"])
    unique_decisions = {}
    for decision in human_decisions:
        identity = (
            decision["field"],
            repr(decision.get("current")),
            decision["reason"],
            decision["recommendation"],
            repr(decision.get("expected")),
        )
        unique_decisions.setdefault(identity, decision)
    human_decisions = sorted(
        unique_decisions.values(),
        key=lambda decision: (
            decision["field"],
            repr(decision.get("current")),
            decision["reason"],
            decision["recommendation"],
            repr(decision.get("expected")),
        )
    )
    proposed_changes = {
        key: proposed_changes[key] for key in sorted(proposed_changes)
    }
    return {
        "safe_mappings": safe_mappings,
        "human_decisions": human_decisions,
        "proposed_changes": proposed_changes,
        "proposed_issue_id": proposed_issue_id,
        "projected": projected,
    }


def _apply_migration_identity_collisions(evaluated_issues, classifications):
    identity_sources = {}
    for issue in evaluated_issues:
        if issue["source_format"] == "frontmatter-unsupported":
            continue
        identity_sources.setdefault(issue["issue_id"], set()).add(
            issue["source_path"]
        )
    for issue in evaluated_issues:
        classification = classifications[issue["source_path"]]
        proposed_id = classification["proposed_issue_id"]
        if proposed_id is None:
            continue
        identity_sources.setdefault(proposed_id, set()).add(issue["source_path"])

    for issue in evaluated_issues:
        classification = classifications[issue["source_path"]]
        proposed_id = classification["proposed_issue_id"]
        if proposed_id is None:
            continue
        source_paths = sorted(identity_sources[proposed_id])
        if len(source_paths) < 2:
            continue

        classification["proposed_changes"].pop("set_schema_version", None)
        classification["safe_mappings"] = [
            mapping
            for mapping in classification["safe_mappings"]
            if mapping["field"] not in {"issue_id", "schema_version"}
        ]
        classification["human_decisions"].append(
            _human_decision(
                "issue_id",
                {
                    "issue_id": proposed_id,
                    "source_paths": source_paths,
                },
                f"Proposed canonical issue ID {proposed_id} is duplicated across source files.",
                "Choose unique canonical issue IDs for all listed source paths before setting schema_version 0.1.0.",
            )
        )
        classification["human_decisions"].sort(
            key=lambda decision: (
                decision["field"],
                repr(decision.get("current")),
                decision["reason"],
            )
        )
        projected = copy.deepcopy(issue)
        projected["diagnostics"] = _parser_diagnostics(projected)
        classification["projected"] = projected


def build_migration_report(project_root):
    """Return deterministic migration proposals without modifying source files."""
    project_root = Path(project_root)
    evaluated_project = evaluate_project(project_root)
    evaluated_issues = sorted(
        evaluated_project["issues"],
        key=lambda issue: (issue["source_path"], issue["issue_id"]),
    )
    classifications = {
        issue["source_path"]: _classify_migration_issue(project_root, issue)
        for issue in evaluated_issues
    }
    _apply_migration_identity_collisions(evaluated_issues, classifications)
    projected_records = [
        classifications[issue["source_path"]]["projected"]
        for issue in evaluated_issues
    ]
    projected_project = _evaluate_issue_records(project_root, projected_records)
    projected_by_path = {
        issue["source_path"]: issue for issue in projected_project["issues"]
    }

    entries = []
    for issue in evaluated_issues:
        classification = classifications[issue["source_path"]]
        before = _routing_summary(issue)
        projected_issue = projected_by_path[issue["source_path"]]
        after = _routing_summary(projected_issue)
        if classification["human_decisions"]:
            after["readiness"] = "blocked"
            after["recommended_next_command"] = "product:doctor"

        declared = issue.get("declared_next_command")
        after_command = after["recommended_next_command"]
        if (
            not classification["human_decisions"]
            and declared is not None
            and declared != after_command
        ):
            classification["proposed_changes"]["align_next_command"] = after_command
            classification["proposed_changes"] = {
                key: classification["proposed_changes"][key]
                for key in sorted(classification["proposed_changes"])
            }
            classification["safe_mappings"].append(
                _safe_mapping(
                    "next_command",
                    after_command,
                    "The shared evaluator deterministically derives the post-migration route.",
                )
            )
            classification["safe_mappings"].sort(
                key=lambda mapping: mapping["field"]
            )

        diagnostics = copy.deepcopy(issue["diagnostics"])
        migration_required = bool(
            diagnostics
            or classification["proposed_changes"]
            or classification["human_decisions"]
        )
        entries.append(
            {
                "issue_id": issue["issue_id"],
                "source_path": issue["source_path"],
                "source_format": issue["source_format"],
                "schema_version": issue.get("schema_version"),
                "tentative_issue_id": issue.get("tentative_issue_id"),
                "lifecycle_state": issue.get("lifecycle_state"),
                "readiness": issue.get("readiness"),
                "diagnostic_summary": _diagnostic_summary(diagnostics),
                "diagnostics": diagnostics,
                "safe_mappings": classification["safe_mappings"],
                "human_decisions": classification["human_decisions"],
                "proposed_changes": classification["proposed_changes"],
                "routing_before": before,
                "routing_after": after,
                "migration_required": migration_required,
            }
        )

    source_formats = {}
    for entry in entries:
        source_format = entry["source_format"]
        source_formats[source_format] = source_formats.get(source_format, 0) + 1
    source_formats = {
        key: source_formats[key] for key in sorted(source_formats)
    }
    diagnostics = [
        diagnostic
        for entry in entries
        for diagnostic in entry["diagnostics"]
    ]
    return {
        "schema": "moduflow.issue-migration-report.v1",
        "project_root": str(project_root.resolve()),
        "summary": {
            "issues_scanned": len(entries),
            "source_formats": source_formats,
            "errors": sum(
                diagnostic.get("severity") == "error"
                for diagnostic in diagnostics
            ),
            "warnings": sum(
                diagnostic.get("severity") == "warning"
                for diagnostic in diagnostics
            ),
            "migration_required": sum(
                entry["migration_required"] for entry in entries
            ),
        },
        "issues": entries,
    }


def _error_report(code, project_root, message):
    return {
        "schema": "moduflow.issue-migration-report.error.v1",
        "project_root": str(Path(project_root).resolve()),
        "error": {
            "code": code,
            "message": message,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inspect ModuFlow issue schema migrations without writing files."
    )
    parser.add_argument("project_path")
    parser.add_argument("--report", action="store_true", required=True)
    args = parser.parse_args(argv)

    project_root = Path(args.project_path)
    if not project_root.is_dir() or not os.access(
        project_root, os.R_OK | os.X_OK
    ):
        print(
            json.dumps(
                _error_report(
                    "PROJECT_ROOT_INVALID",
                    project_root,
                    "Project root must be a readable directory.",
                ),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2

    try:
        report = build_migration_report(project_root)
        if (
            report.get("schema") != "moduflow.issue-migration-report.v1"
            or not isinstance(report.get("issues"), list)
            or not isinstance(report.get("summary"), dict)
        ):
            raise ValueError("migration report contract validation failed")
    except Exception as exc:
        print(
            json.dumps(
                _error_report(
                    "REPORT_INTERNAL_ERROR",
                    project_root,
                    f"Migration report failed: {exc}",
                ),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1

    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
