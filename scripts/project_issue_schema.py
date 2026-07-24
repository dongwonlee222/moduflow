#!/usr/bin/env python3
"""Safe, standard-library issue schema parsing boundary.

The accepted frontmatter grammar is intentionally smaller than YAML: top-level
scalar fields and top-level lists of scalars.  Rich YAML features are rejected
as diagnostic data so reading a user-authored issue never invokes constructors
or executes tags.
"""

import json
import re
from pathlib import Path


NORMALIZED_SCHEMA = "moduflow.issue.v2"
SUPPORTED_SCHEMA_VERSIONS = {"0.1.0"}
LIFECYCLE_STATES = {"backlog", "active", "done"}
PROJECTION_TO_LIFECYCLE = {
    "backlog": "backlog",
    "in_progress": "active",
    "done": "done",
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
_SCHEMA_ERROR_CODES = {"ISSUE_SCHEMA_MALFORMED", "ISSUE_SCHEMA_UNSUPPORTED"}
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

    if "depends_on" in fields and (
        not isinstance(fields["depends_on"], list)
        or not all(isinstance(value, str) for value in fields["depends_on"])
    ):
        invalid_fields.add("depends_on")
        sanitized.pop("depends_on", None)
        diagnostics.append(
            _malformed(
                issue_id,
                source_path,
                "Contract field 'depends_on' must be a list of issue ID strings.",
                field="depends_on",
                current=fields["depends_on"],
                expected="list of strings",
                recommendation=(
                    "Set depends_on to a supported top-level list of issue ID strings."
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


def markdown_status_projection(text):
    match = re.search(
        r"^\*\*Status:\s*([A-Za-z0-9_-]+)",
        metadata_region(text),
        re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).lower() if match else None


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
        if value:
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
    try:
        return str(path.resolve().relative_to(Path(project_root).resolve()))
    except ValueError:
        return str(path)


def _base_issue(path, project_root, text):
    source_path = _relative_source_path(path, project_root)
    return {
        "schema": NORMALIZED_SCHEMA,
        "schema_version": None,
        "issue_id": path.stem,
        "source_path": source_path,
        "source_format": "markdown",
        "title": markdown_title(text),
        "lifecycle_state": markdown_status(text),
        "projection_status": markdown_status(text),
        "priority": markdown_priority(text),
        "blocked_by": markdown_blocked_by(text),
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


def _adapter_diagnostic(
    issue,
    code,
    field,
    current,
    expected,
    message,
    recommendation,
    severity="error",
):
    return _diagnostic(
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


def _normalized_dependency_list(value):
    if not isinstance(value, list) or not all(
        isinstance(dependency, str) for dependency in value
    ):
        return []
    normalized = []
    for dependency in value:
        dependency = dependency.strip().strip("`").strip()
        if dependency and dependency not in normalized:
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
    issue["diagnostics"].extend(parse_diagnostics or [])

    declared_issue_id = fields.get("issue_id")
    if isinstance(declared_issue_id, str) and declared_issue_id:
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
    issue["lifecycle_state"] = None
    issue["projection_status"] = None
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
        issue["diagnostics"].append(
            _malformed(path.stem, source_path, f"issue file could not be read: {exc}")
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


def list_normalized_issues(project_root):
    """Return normalized issue records sorted by their canonical issue id."""
    project_root = Path(project_root)
    issues_dir = project_root / "issues"
    if not issues_dir.is_dir():
        return []
    issues = [
        parse_issue(path, project_root)
        for path in sorted(issues_dir.glob("*.md"))
        if path.is_file()
    ]
    return sorted(issues, key=lambda issue: issue["issue_id"])


def build_artifact_index(project_root, issue_ids):
    """Return actual workflow-artifact coverage for each supplied issue id."""
    project_root = Path(project_root)
    artifact_index = {}
    for issue_id in sorted(set(issue_ids)):
        artifact_root = project_root / "specs" / issue_id
        coverage = {
            phase: (artifact_root / f"{phase}.md").is_file()
            for phase in _ARTIFACT_PHASES
        }
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


def _dependency_diagnostic(issue, code, current, expected, message, recommendation):
    return _adapter_diagnostic(
        issue,
        code,
        "depends_on",
        current,
        expected,
        message,
        recommendation,
    )


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


def dependency_diagnostics(issue_index):
    """Return dependency errors by issue id using iterative graph traversal."""
    diagnostics = {}

    def add(issue_id, diagnostic):
        diagnostics.setdefault(issue_id, []).append(diagnostic)

    graph = {}
    for issue_id in sorted(issue_index):
        issue = issue_index[issue_id]
        dependencies = _issue_dependencies(issue)
        graph[issue_id] = [
            dependency for dependency in dependencies if dependency in issue_index
        ]
        for dependency in dependencies:
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

    for cycle_members in sorted(cycle_groups, key=lambda group: sorted(group)):
        current = ", ".join(sorted(cycle_members))
        for issue_id in sorted(cycle_members):
            issue = issue_index[issue_id]
            add(
                issue_id,
                _dependency_diagnostic(
                    issue,
                    "ISSUE_DEPENDENCY_CYCLE",
                    current,
                    "an acyclic dependency graph",
                    f"Issue {issue_id} participates in a dependency cycle.",
                    "Remove or redirect a depends_on edge in the cycle, then run product:status.",
                ),
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
        issue["diagnostics"].append(diagnostic)


def _is_recognized_versioned(issue):
    return issue.get("source_format") == "frontmatter-0.1.0"


def _append_structural_state_diagnostics(issue):
    if not _is_recognized_versioned(issue):
        return

    issue_id = issue["issue_id"]
    definition = issue.get("definition_readiness")
    if definition != "ready":
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
    if gate != "passed":
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
    return "ready", f"product:execute {issue_id}"


def _evaluate_issue_after_dependency(issue, issue_index, artifact_index):
    evaluated = dict(issue)
    evaluated["diagnostics"] = list(issue.get("diagnostics", []))
    coverage = artifact_index.get(issue["issue_id"], {})
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
    prepared["diagnostics"] = list(issue.get("diagnostics", []))
    for diagnostic in dependency_diagnostics(issue_index).get(
        issue["issue_id"], []
    ):
        _append_unique_diagnostic(prepared, diagnostic)
    return _evaluate_issue_after_dependency(prepared, issue_index, artifact_index)


def evaluate_project(project_root):
    """Return evaluated issues and project-level dependency diagnostics."""
    project_root = Path(project_root)
    issues = list_normalized_issues(project_root)
    issue_index = {issue["issue_id"]: issue for issue in issues}
    artifact_index = build_artifact_index(project_root, issue_index)
    project_dependency_diagnostics = dependency_diagnostics(issue_index)
    evaluated = []
    for issue in issues:
        prepared = dict(issue)
        prepared["diagnostics"] = list(issue["diagnostics"])
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
