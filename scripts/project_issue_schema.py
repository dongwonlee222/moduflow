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

_CONTRACT_FIELDS = {
    "schema_version",
    "issue_id",
    "canonical_state",
    "status",
    "priority",
    "definition_readiness",
    "gate_state",
    "depends_on",
    "next_command",
}
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


def _diagnostic(code, issue_id, source_path, message, **details):
    diagnostic = {
        "code": code,
        "severity": "error",
        "issue_id": issue_id,
        "source_path": str(source_path),
        "message": message,
    }
    diagnostic.update(details)
    return diagnostic


def _malformed(issue_id, source_path, message, line=None, field=None):
    details = {}
    if line is not None:
        details["line"] = line
    if field is not None:
        details["field"] = field
    return _diagnostic(
        "ISSUE_SCHEMA_MALFORMED", issue_id, source_path, message, **details
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
    lowered = value.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("null", "~"):
        return None
    if _INTEGER_RE.fullmatch(value):
        return int(value)
    if re.search(r":\s", value):
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
        while cursor < len(lines) and lines[cursor].startswith((" ", "\t")):
            item_raw = lines[cursor]
            item_stripped = item_raw.strip()
            if not item_stripped:
                cursor += 1
                continue
            item_match = re.fullmatch(r"-\s+(.+)", item_stripped)
            if not item_match or item_raw.startswith("\t"):
                diagnostics.append(
                    _malformed(
                        issue_id,
                        source_path,
                        "nested mappings are not supported",
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
                    )
                )
                nested_error = True
            cursor += 1
        if not nested_error:
            fields[key] = values
        index = cursor

    return fields, diagnostics


def metadata_region(text):
    """Return the Markdown header region where issue metadata is valid."""
    _, body = split_frontmatter(text)
    match = re.search(r"^##\s", body, re.MULTILINE)
    return body[: match.start()] if match else body


def markdown_status(text):
    match = re.search(
        r"^\*\*Status:\s*([A-Za-z0-9_-]+)",
        metadata_region(text),
        re.IGNORECASE | re.MULTILINE,
    )
    status = match.group(1).lower() if match else "backlog"
    return status if status in LIFECYCLE_STATES else "backlog"


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
        "issue_id": path.stem,
        "source_path": source_path,
        "source_format": "markdown",
        "title": markdown_title(text),
        "lifecycle_state": markdown_status(text),
        "projection_status": markdown_status(text),
        "priority": markdown_priority(text),
        "blocked_by": markdown_blocked_by(text),
        "definition_readiness": None,
        "gate_state": None,
        "declared_next_command": None,
        "extensions": {},
        "diagnostics": [],
    }


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

    issue = _base_issue(path, project_root, text)
    frontmatter, _ = split_frontmatter(text)
    if frontmatter is None:
        if text.lstrip("\ufeff").startswith("---"):
            issue["diagnostics"].append(
                _malformed(
                    path.stem,
                    source_path,
                    "frontmatter opening delimiter has no closing delimiter",
                )
            )
        return issue

    fields, diagnostics = parse_frontmatter_subset(
        frontmatter, path.stem, source_path
    )
    issue["diagnostics"].extend(diagnostics)
    version = fields.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        return issue

    issue["source_format"] = f"frontmatter-{version}"
    declared_issue_id = fields.get("issue_id")
    if isinstance(declared_issue_id, str) and declared_issue_id:
        issue["issue_id"] = declared_issue_id
    canonical_state = fields.get("canonical_state")
    if canonical_state in LIFECYCLE_STATES:
        issue["lifecycle_state"] = canonical_state
    projection_status = fields.get("status")
    if isinstance(projection_status, str):
        issue["projection_status"] = projection_status
    priority = fields.get("priority")
    if isinstance(priority, str):
        issue["priority"] = priority.lower()
    depends_on = fields.get("depends_on")
    if isinstance(depends_on, list) and all(
        isinstance(dependency, str) for dependency in depends_on
    ):
        issue["blocked_by"] = list(depends_on)
    issue["definition_readiness"] = fields.get("definition_readiness")
    issue["gate_state"] = fields.get("gate_state")
    issue["declared_next_command"] = fields.get("next_command")
    issue["extensions"] = {
        key: value for key, value in fields.items() if key not in _CONTRACT_FIELDS
    }

    return issue
