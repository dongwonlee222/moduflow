#!/usr/bin/env python3
"""Pure lifecycle transaction contract and deterministic identity helpers.

This module deliberately performs no filesystem, process, network, Git, or
remote-system operations. Transaction planning and persistence are layered on
top of this contract in later Issue 103 tasks.
"""

from dataclasses import dataclass, field, replace
from datetime import date
import hashlib
import json
from collections.abc import Mapping
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from types import MappingProxyType

import project_issue_schema
import project_registry
from project_lifecycle import (
    render_dashboard_projection,
    render_issue_index,
    render_issue_transition,
    render_roadmap_projection,
    render_state_projection,
)
from project_loop import render_loop_projection


PLAN_SCHEMA = "moduflow.lifecycle-transaction-plan.v1"
RESULT_SCHEMA = "moduflow.lifecycle-transaction.v1"

_ACTIONS = frozenset({
    "start",
    "update",
    "pause",
    "resume",
    "complete",
    "reconcile",
    "production-version",
})
_LIFECYCLES = frozenset({"backlog", "active", "done"})
_ACTION_TARGETS = {
    "start": "active",
    "pause": "active",
    "resume": "active",
    "complete": "done",
}
_SEMANTIC_VERSION = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_LOGICAL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")

_TARGET_RECORD_KEYS = frozenset({
    "role",
    "relative_path",
    "existed",
    "before_sha256",
    "after_sha256",
    "after_bytes",
    "changed",
    "validation_rules",
    "apply_order",
    "rollback_order",
})
_PLAN_KEYS = frozenset({
    "schema",
    "transaction_id",
    "idempotency_key",
    "project_id",
    "canonical_root",
    "issue_id",
    "action",
    "target_lifecycle",
    "targets",
})
_RESULT_KEYS = frozenset({
    "schema",
    "transaction_id",
    "idempotency_key",
    "status",
    "project_id",
    "canonical_root",
    "issue_id",
    "action",
    "target_lifecycle",
    "targets",
    "projected_validation",
    "post_apply_validation",
    "failed_stage",
    "error_code",
    "rollback_status",
    "verified_target_count",
    "next_command",
    "actor",
    "source_event",
    "created_at",
    "started_at",
    "completed_at",
})
_TERMINAL_STATUSES = frozenset({
    "applied",
    "noop",
    "denied",
    "conflict",
    "rolled_back",
    "recovery_required",
})
_VALIDATION_SUMMARY_KEYS = frozenset({"valid", "rule_ids", "error_codes"})
_PLAN_TEXT_FIELDS = (
    "transaction_id",
    "idempotency_key",
    "project_id",
    "canonical_root",
    "issue_id",
)
_RESULT_TEXT_FIELDS = _PLAN_TEXT_FIELDS + (
    "failed_stage",
    "error_code",
    "rollback_status",
    "next_command",
    "actor",
    "source_event",
    "created_at",
    "started_at",
    "completed_at",
)


@dataclass(frozen=True)
class LifecycleIntent:
    issue_id: str
    action: str
    actor: str
    source_event: str
    target_lifecycle: str | None = None
    next_command: str = ""
    idempotency_key: str = ""
    expected_issue_sha256: str = ""
    loop_blocker: str = ""
    roadmap_change: dict | None = None
    production_change: dict | None = None
    require_issue_index: bool = False


@dataclass(frozen=True)
class PlannedTarget:
    """One selected artifact with private immutable preimage and proposal bytes."""

    role: str
    relative_path: str
    existed: bool
    before_sha256: str
    after_sha256: str
    after_size: int
    changed: bool
    validation_rules: tuple[str, ...]
    apply_order: int
    rollback_order: int
    _before_bytes: bytes = field(repr=False)
    _after_bytes: bytes = field(repr=False)

    def to_public_dict(self):
        return {
            "role": self.role,
            "relative_path": self.relative_path,
            "existed": self.existed,
            "before_sha256": self.before_sha256,
            "after_sha256": self.after_sha256,
            "after_bytes": self.after_size,
            "changed": self.changed,
            "validation_rules": list(self.validation_rules),
            "apply_order": self.apply_order,
            "rollback_order": self.rollback_order,
        }


@dataclass(frozen=True)
class LifecycleTransactionPlan:
    """Detached immutable plan with an exact redacted public representation."""

    schema: str
    transaction_id: str
    idempotency_key: str
    project_id: str
    canonical_root: str
    issue_id: str
    action: str
    target_lifecycle: str | None
    targets: tuple[PlannedTarget, ...]
    _project_context: Mapping = field(repr=False, compare=False)

    def __post_init__(self):
        if not isinstance(self.targets, tuple) or not all(
            isinstance(target, PlannedTarget) for target in self.targets
        ):
            raise TypeError("targets must be a tuple of PlannedTarget values")
        if not isinstance(self._project_context, Mapping):
            raise TypeError("project context must be a mapping")
        object.__setattr__(
            self,
            "_project_context",
            _freeze_json_value(self._project_context),
        )

    def to_public_dict(self):
        return serialize_transaction_plan(
            {
                "schema": self.schema,
                "transaction_id": self.transaction_id,
                "idempotency_key": self.idempotency_key,
                "project_id": self.project_id,
                "canonical_root": self.canonical_root,
                "issue_id": self.issue_id,
                "action": self.action,
                "target_lifecycle": self.target_lifecycle,
                "targets": [target.to_public_dict() for target in self.targets],
            }
        )


class LifecyclePlanError(ValueError):
    """Bounded planner failure that never includes artifact or absolute-path data."""

    def __init__(self, code, *, role="", relative_path=""):
        self.code = code
        self.role = role
        self.relative_path = relative_path
        fields = [code]
        if role:
            fields.append(f"role={role}")
        if relative_path:
            fields.append(f"path={relative_path}")
        super().__init__("; ".join(fields))


def canonical_json_bytes(value):
    """Return canonical UTF-8 JSON bytes for deterministic hashing."""
    return json.dumps(
        _json_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _freeze_json_value(value):
    """Recursively detach and freeze JSON-compatible semantic input."""
    if isinstance(value, Mapping):
        frozen = {}
        for key, child in value.items():
            if not isinstance(key, str):
                raise TypeError("semantic change keys must be strings")
            frozen[key] = _freeze_json_value(child)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_value(child) for child in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError("semantic change values must be JSON-compatible")


def _json_value(value):
    """Return a detached JSON-compatible equivalent of frozen semantic data."""
    if isinstance(value, Mapping):
        return {key: _json_value(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_value(child) for child in value]
    return value


def target_sha256(contents):
    """Return the SHA-256 digest for one target's byte content."""
    if not isinstance(contents, bytes):
        raise TypeError("target contents must be bytes")
    return hashlib.sha256(contents).hexdigest()


def normalize_lifecycle_intent(intent):
    """Validate and return a canonical, immutable lifecycle intent."""
    if not isinstance(intent, LifecycleIntent):
        raise TypeError("intent must be LifecycleIntent")
    action = str(intent.action or "").strip().lower()
    if action not in _ACTIONS:
        raise ValueError("Unsupported lifecycle action")
    if not str(intent.issue_id or "").strip():
        raise ValueError("Lifecycle intent requires issue_id")
    if not str(intent.actor or "").strip():
        raise ValueError("Lifecycle intent requires actor")
    if not str(intent.source_event or "").strip():
        raise ValueError("Lifecycle intent requires source_event")

    supplied_target = intent.target_lifecycle
    if supplied_target is not None:
        supplied_target = str(supplied_target).strip().lower()
        if supplied_target not in _LIFECYCLES:
            raise ValueError("Unsupported target lifecycle")
    fixed_target = _ACTION_TARGETS.get(action)
    if fixed_target and supplied_target not in (None, fixed_target):
        raise ValueError(f"{action} must target {fixed_target}")
    if action == "production-version" and supplied_target is not None:
        raise ValueError(f"{action} may not set target lifecycle")

    production_change = intent.production_change
    if action == "production-version":
        if not isinstance(production_change, Mapping) or not production_change.get("version"):
            raise ValueError("production-version requires production_change.version")
        version = str(production_change["version"]).strip()
        if not _SEMANTIC_VERSION.fullmatch(version):
            raise ValueError("production-version requires a semantic version")
        production_change = {**production_change, "version": version}
    elif production_change is not None:
        raise ValueError("production_change is only valid for production-version")
    if intent.roadmap_change is not None and not isinstance(intent.roadmap_change, Mapping):
        raise ValueError("roadmap_change must be a dictionary")

    return replace(
        intent,
        issue_id=str(intent.issue_id).strip(),
        action=action,
        actor=str(intent.actor).strip(),
        source_event=str(intent.source_event).strip(),
        target_lifecycle=fixed_target or supplied_target,
        loop_blocker=str(intent.loop_blocker or "").strip(),
        roadmap_change=(
            _freeze_json_value(intent.roadmap_change)
            if intent.roadmap_change is not None
            else None
        ),
        production_change=(
            _freeze_json_value(production_change)
            if production_change is not None
            else None
        ),
    )


def _semantic_identity(project_context, intent):
    normalized = normalize_lifecycle_intent(intent)
    if not isinstance(project_context, dict):
        raise TypeError("project_context must be a dictionary")
    canonical_root = project_context.get("canonical_root")
    if not isinstance(canonical_root, str) or not canonical_root:
        raise ValueError("project_context requires canonical_root")
    return {
        "project_id": project_context.get("project_id") or "explicit-root",
        "canonical_root": canonical_root,
        "issue_id": normalized.issue_id,
        "action": normalized.action,
        "target_lifecycle": normalized.target_lifecycle,
        "source_event": normalized.source_event,
        "loop_blocker": normalized.loop_blocker,
        "roadmap_change": normalized.roadmap_change,
        "production_change": normalized.production_change,
    }


def derive_idempotency_key(project_context, intent):
    """Derive a semantic key that excludes clocks and temporary paths."""
    return hashlib.sha256(canonical_json_bytes(_semantic_identity(project_context, intent))).hexdigest()


def derive_transaction_id(project_context, intent):
    """Derive a stable, readable transaction ID from the idempotency key."""
    key = derive_idempotency_key(project_context, intent)
    identity = {"schema": RESULT_SCHEMA, "idempotency_key": key}
    return "txn-" + hashlib.sha256(canonical_json_bytes(identity)).hexdigest()[:32]


def assert_idempotency_key_matches(project_context, idempotency_key, intent):
    """Reject a supplied key unless it represents this exact normalized intent."""
    expected = derive_idempotency_key(project_context, intent)
    if idempotency_key != expected:
        raise ValueError("IDEMPOTENCY_KEY_CONFLICT")
    return expected


def _assert_exact_keys(record, expected_keys, label):
    if not isinstance(record, dict):
        raise TypeError(f"{label} must be a dictionary")
    unknown = sorted(set(record) - expected_keys)
    missing = sorted(expected_keys - set(record))
    if unknown:
        raise ValueError(f"Unknown {label} keys: {', '.join(unknown)}")
    if missing:
        raise ValueError(f"Missing {label} keys: {', '.join(missing)}")


def _serialized_targets(targets):
    if not isinstance(targets, list):
        raise TypeError("targets must be a list")
    serialized = []
    for target in targets:
        _assert_exact_keys(target, _TARGET_RECORD_KEYS, "transaction target")
        relative_path = target["relative_path"]
        if (
            not isinstance(relative_path, str)
            or not relative_path
            or "\\" in relative_path
            or relative_path.startswith("/")
            or PureWindowsPath(relative_path).is_absolute()
            or any(part in {"", ".", ".."} for part in PurePosixPath(relative_path).parts)
        ):
            raise ValueError("relative_path must be a project-relative logical path")
        if not isinstance(target["role"], str) or not _LOGICAL_NAME.fullmatch(target["role"]):
            raise ValueError("role must be a logical identifier")
        for name in ("before_sha256", "after_sha256"):
            value = target[name]
            if value != "absent" and (
                not isinstance(value, str) or not _SHA256.fullmatch(value)
            ):
                raise ValueError(f"{name} must be a SHA-256 hash or absent")
        if not isinstance(target["existed"], bool) or not isinstance(target["changed"], bool):
            raise ValueError("target existence and change flags must be booleans")
        if (
            not isinstance(target["after_bytes"], int)
            or isinstance(target["after_bytes"], bool)
            or target["after_bytes"] < 0
        ):
            raise ValueError("after_bytes must be a non-negative integer")
        for name in ("apply_order", "rollback_order"):
            if (
                not isinstance(target[name], int)
                or isinstance(target[name], bool)
                or target[name] < 0
            ):
                raise ValueError(f"{name} must be a non-negative integer")
        rules = target["validation_rules"]
        if (
            not isinstance(rules, list)
            or not all(isinstance(rule, str) and _LOGICAL_NAME.fullmatch(rule) for rule in rules)
        ):
            raise ValueError("validation_rules must be logical rule identifiers")
        serialized.append({**target, "validation_rules": list(rules)})
    return serialized


def _serialized_validation_summary(summary):
    if not isinstance(summary, dict):
        raise TypeError("validation summary must be a dictionary")
    unknown = sorted(set(summary) - _VALIDATION_SUMMARY_KEYS)
    if unknown:
        raise ValueError("validation summary keys must be valid, rule_ids, or error_codes")
    if not isinstance(summary.get("valid"), bool):
        raise ValueError("validation summary requires boolean valid")
    serialized = {"valid": summary["valid"]}
    for name in ("rule_ids", "error_codes"):
        if name not in summary:
            continue
        values = summary[name]
        if (
            not isinstance(values, list)
            or not all(isinstance(value, str) and _LOGICAL_NAME.fullmatch(value) for value in values)
        ):
            raise ValueError(f"validation summary {name} must be logical identifiers")
        serialized[name] = list(values)
    return serialized


def _serialized_text_fields(record, fields):
    serialized = {}
    for field in fields:
        value = record[field]
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")
        serialized[field] = value
    return serialized


def _serialized_action_and_lifecycle(record):
    action = record["action"]
    if not isinstance(action, str) or action not in _ACTIONS:
        raise ValueError("Unsupported lifecycle action")
    target_lifecycle = record["target_lifecycle"]
    if target_lifecycle is not None and (
        not isinstance(target_lifecycle, str) or target_lifecycle not in _LIFECYCLES
    ):
        raise ValueError("Unsupported target lifecycle")
    return {"action": action, "target_lifecycle": target_lifecycle}


def serialize_transaction_plan(plan):
    """Return a strict, redacted plan envelope with logical paths and hashes only."""
    _assert_exact_keys(plan, _PLAN_KEYS, "transaction plan")
    if plan["schema"] != PLAN_SCHEMA:
        raise ValueError("Unsupported transaction plan schema")
    return {
        "schema": PLAN_SCHEMA,
        **_serialized_text_fields(plan, _PLAN_TEXT_FIELDS),
        **_serialized_action_and_lifecycle(plan),
        "targets": _serialized_targets(plan["targets"]),
    }


def serialize_transaction_result(result):
    """Return a strict, redacted result envelope with logical paths and hashes only."""
    _assert_exact_keys(result, _RESULT_KEYS, "transaction result")
    if result["schema"] != RESULT_SCHEMA:
        raise ValueError("Unsupported transaction result schema")
    status = result["status"]
    if not isinstance(status, str) or status not in _TERMINAL_STATUSES:
        raise ValueError("Unsupported transaction status")
    if status not in {"applied", "noop"} and (
        not result["failed_stage"] or not result["error_code"]
    ):
        raise ValueError("Non-success transaction results require failed_stage and error_code")
    verified_target_count = result["verified_target_count"]
    if (
        not isinstance(verified_target_count, int)
        or isinstance(verified_target_count, bool)
        or verified_target_count < 0
    ):
        raise ValueError("verified_target_count must be a non-negative integer")
    return {
        "schema": RESULT_SCHEMA,
        **_serialized_text_fields(result, _RESULT_TEXT_FIELDS),
        "status": status,
        **_serialized_action_and_lifecycle(result),
        "targets": _serialized_targets(result["targets"]),
        "projected_validation": _serialized_validation_summary(
            result["projected_validation"]
        ),
        "post_apply_validation": _serialized_validation_summary(
            result["post_apply_validation"]
        ),
        "verified_target_count": verified_target_count,
    }


def _planning_date(clock):
    value = clock() if callable(clock) else clock
    if value is None:
        value = date.today()
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _safe_planning_child(root, context, role, *parts):
    paths = context.get("paths") if isinstance(context, Mapping) else None
    relative_paths = (
        context.get("relative_paths") if isinstance(context, Mapping) else None
    )
    if not isinstance(paths, Mapping) or not isinstance(relative_paths, Mapping):
        raise LifecyclePlanError("PLAN_CONTEXT_INVALID", role=role)
    configured = paths.get(role)
    relative_root = relative_paths.get(role)
    if not isinstance(configured, str) or not isinstance(relative_root, str):
        raise LifecyclePlanError("PLAN_CONTEXT_INVALID", role=role)

    configured_path = Path(os.path.abspath(configured))
    try:
        configured_path.relative_to(root)
    except ValueError as exc:
        raise LifecyclePlanError("PLAN_PATH_ESCAPE", role=role) from exc

    role_path = Path(relative_root)
    if role_path.is_absolute() or any(part == ".." for part in role_path.parts):
        raise LifecyclePlanError("PLAN_PATH_ESCAPE", role=role)
    clean_parts = []
    for part in parts:
        child = Path(str(part))
        if child.is_absolute() or len(child.parts) != 1 or child.name in {"", ".", ".."}:
            raise LifecyclePlanError("PLAN_PATH_ESCAPE", role=role)
        clean_parts.append(child.name)
    candidate = root / role_path / Path(*clean_parts)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise LifecyclePlanError("PLAN_PATH_ESCAPE", role=role) from exc
    return candidate


def _read_planning_source(path, root, role, *, required):
    path = Path(path)
    try:
        relative_path = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise LifecyclePlanError("PLAN_PATH_ESCAPE", role=role) from exc

    current = root
    for part in Path(relative_path).parts:
        current = current / part
        try:
            if current.is_symlink():
                raise LifecyclePlanError(
                    "PLAN_TARGET_SYMLINK",
                    role=role,
                    relative_path=relative_path,
                )
        except OSError as exc:
            raise LifecyclePlanError(
                "PLAN_TARGET_UNREADABLE",
                role=role,
                relative_path=relative_path,
            ) from exc

    if not os.path.lexists(path):
        if required:
            raise LifecyclePlanError(
                "PLAN_TARGET_MISSING",
                role=role,
                relative_path=relative_path,
            )
        return False, b""
    try:
        if not path.is_file():
            raise LifecyclePlanError(
                "PLAN_TARGET_NOT_REGULAR",
                role=role,
                relative_path=relative_path,
            )
        return True, path.read_bytes()
    except LifecyclePlanError:
        raise
    except OSError as exc:
        raise LifecyclePlanError(
            "PLAN_TARGET_UNREADABLE",
            role=role,
            relative_path=relative_path,
        ) from exc


def _project_relative(root, path):
    return Path(path).relative_to(root).as_posix()


def _render_planning_target(role, relative_path, renderer, *args, **kwargs):
    try:
        return renderer(*args, **kwargs)
    except Exception as exc:
        raise LifecyclePlanError(
            "PLAN_RENDER_INVALID",
            role=role,
            relative_path=relative_path,
        ) from exc


def _projected_issue_status(issue_bytes, fallback):
    text = issue_bytes.decode("utf-8")
    match = re.search(r"^\*\*Status:\s*([^*]+)\*\*", text, re.M)
    return match.group(1).strip() if match else fallback


def _projected_issue_index_records(root, context, issue_path, issue_after):
    issues_root = _safe_planning_child(root, context, "issues")
    records = []
    for path in sorted(issues_root.glob("*.md")):
        if path == issue_path:
            source = issue_after
        else:
            _existed, source = _read_planning_source(
                path,
                root,
                "issue",
                required=True,
            )
        issue = project_issue_schema.parse_issue(
            path,
            root,
            source_text=source.decode("utf-8"),
        )
        issue_id = issue["issue_id"]
        records.append(
            {
                "id": issue_id,
                "status": issue["lifecycle_state"],
                "title": issue["title"] or issue_id,
            }
        )
    return records


def _planned_target(role, relative_path, existed, before_bytes, after_bytes, rules, order, total):
    return PlannedTarget(
        role=role,
        relative_path=relative_path,
        existed=existed,
        before_sha256=target_sha256(before_bytes) if existed else "absent",
        after_sha256=target_sha256(after_bytes),
        after_size=len(after_bytes),
        changed=(not existed or before_bytes != after_bytes),
        validation_rules=tuple(rules),
        apply_order=order,
        rollback_order=total - order - 1,
        _before_bytes=before_bytes,
        _after_bytes=after_bytes,
    )


def plan_lifecycle_transaction(
    project_root,
    intent: LifecycleIntent,
    *,
    project_context=None,
    clock=None,
):
    """Compute one immutable lifecycle transaction plan without filesystem writes."""
    root = Path(project_root).resolve()
    try:
        context = project_registry.context_for_operation(
            root,
            project_context=project_context,
        )
    except (OSError, TypeError, ValueError) as exc:
        raise LifecyclePlanError("PLAN_CONTEXT_INVALID") from exc
    normalized = normalize_lifecycle_intent(intent)
    idempotency_key = normalized.idempotency_key or derive_idempotency_key(
        context, normalized
    )
    if normalized.idempotency_key:
        assert_idempotency_key_matches(context, idempotency_key, normalized)
    transaction_id = derive_transaction_id(context, normalized)
    changed_on = _planning_date(clock)

    issue_path = _safe_planning_child(
        root, context, "issues", f"{normalized.issue_id}.md"
    )
    state_path = root / ".moduflow" / "state.json"
    loop_path = _safe_planning_child(
        root, context, "workspace", "loop-state.json"
    )
    dashboard_path = _safe_planning_child(
        root, context, "workspace", "dashboard.md"
    )
    issue_existed, issue_before = _read_planning_source(
        issue_path, root, "issue", required=True
    )
    state_existed, state_before = _read_planning_source(
        state_path, root, "state", required=True
    )
    loop_existed, loop_before = _read_planning_source(
        loop_path, root, "loop", required=True
    )
    dashboard_existed, dashboard_before = _read_planning_source(
        dashboard_path, root, "dashboard", required=True
    )

    issue_relative = _project_relative(root, issue_path)
    issue_after = _render_planning_target(
        "issue",
        issue_relative,
        render_issue_transition,
        issue_before,
        normalized.target_lifecycle,
        changed_on=changed_on,
    )
    projected_status = _render_planning_target(
        "issue",
        issue_relative,
        _projected_issue_status,
        issue_after,
        normalized.target_lifecycle or "backlog",
    )
    issue_active = normalized.issue_id if projected_status == "active" else ""
    phase = "execute" if projected_status == "active" else "select"
    next_command = normalized.next_command or (
        f"product:execute {normalized.issue_id}"
        if projected_status == "active"
        else "product:status"
    )
    state_after = _render_planning_target(
        "state",
        _project_relative(root, state_path),
        render_state_projection,
        state_before,
        active_issue=issue_active,
        phase=phase,
        next_command=next_command,
        changed_on=changed_on,
    )
    loop_after = _render_planning_target(
        "loop",
        _project_relative(root, loop_path),
        render_loop_projection,
        loop_before,
        issue_id=normalized.issue_id,
        action=normalized.action,
        next_command=next_command,
        blocker=normalized.loop_blocker,
        changed_on=changed_on,
        target_lifecycle=projected_status,
    )
    dashboard_after = _render_planning_target(
        "dashboard",
        _project_relative(root, dashboard_path),
        render_dashboard_projection,
        dashboard_before,
        active_issue=issue_active,
        phase=phase,
        source_path=issue_relative,
    )

    selected = [
        (
            "issue", issue_relative, issue_existed, issue_before, issue_after,
            ("issue-schema", "lifecycle"),
        ),
        (
            "state", _project_relative(root, state_path), state_existed, state_before,
            state_after, ("state-schema", "lifecycle"),
        ),
        (
            "loop", _project_relative(root, loop_path), loop_existed, loop_before,
            loop_after, ("loop-state-schema", "lifecycle"),
        ),
        (
            "dashboard", _project_relative(root, dashboard_path), dashboard_existed,
            dashboard_before, dashboard_after, ("dashboard-projection",),
        ),
    ]

    issue_index_path = _safe_planning_child(
        root, context, "workspace", "issue-index.json"
    )
    if os.path.lexists(issue_index_path) or normalized.require_issue_index:
        existed, before = _read_planning_source(
            issue_index_path, root, "issue-index", required=False
        )
        index_records = _render_planning_target(
            "issue-index",
            _project_relative(root, issue_index_path),
            _projected_issue_index_records,
            root,
            context,
            issue_path,
            issue_after,
        )
        after = _render_planning_target(
            "issue-index",
            _project_relative(root, issue_index_path),
            render_issue_index,
            index_records,
        )
        selected.append(
            (
                "issue-index", _project_relative(root, issue_index_path), existed,
                before, after, ("issue-index-schema",),
            )
        )

    if normalized.roadmap_change is not None:
        roadmap_path = _safe_planning_child(
            root, context, "workspace", "roadmap.md"
        )
        existed, before = _read_planning_source(
            roadmap_path, root, "roadmap", required=True
        )
        change = normalized.roadmap_change
        after = _render_planning_target(
            "roadmap",
            _project_relative(root, roadmap_path),
            render_roadmap_projection,
            before,
            issue_id=normalized.issue_id,
            priority=change.get("priority", "p2"),
            dependencies=change.get("dependencies", ()),
            release_order=change.get("release_order"),
        )
        selected.append(
            (
                "roadmap", _project_relative(root, roadmap_path), existed, before,
                after, ("roadmap-projection",),
            )
        )

    if normalized.production_change is not None:
        change = normalized.production_change
        record_id = str(change.get("record_id") or normalized.issue_id)
        production_path = _safe_planning_child(
            root, context, "production_records", f"{record_id}.md"
        )
        existed, before = _read_planning_source(
            production_path,
            root,
            "production-record",
            required=False,
        )
        content = change.get("content", "")
        after = content if isinstance(content, bytes) else str(content).encode("utf-8")
        selected.append(
            (
                "production-record", _project_relative(root, production_path), existed,
                before, after, ("production-record-schema",),
            )
        )

    target_total = len(selected) + 1
    targets = tuple(
        _planned_target(*target, order=index, total=target_total)
        for index, target in enumerate(selected)
    )
    evidence_path = _safe_planning_child(
        root, context, "workspace", "transactions", f"{transaction_id}.json"
    )
    evidence_existed, evidence_before = _read_planning_source(
        evidence_path,
        root,
        "evidence",
        required=False,
    )
    evidence_after = (
        json.dumps(
            {
                "schema": "moduflow.lifecycle-transaction-evidence.v1",
                "transaction_id": transaction_id,
                "targets": [target.to_public_dict() for target in targets],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")
    evidence = _planned_target(
        "evidence",
        _project_relative(root, evidence_path),
        evidence_existed,
        evidence_before,
        evidence_after,
        ("transaction-evidence-schema",),
        len(targets),
        target_total,
    )
    return LifecycleTransactionPlan(
        schema=PLAN_SCHEMA,
        transaction_id=transaction_id,
        idempotency_key=idempotency_key,
        project_id=context.get("project_id") or "explicit-root",
        canonical_root=str(root),
        issue_id=normalized.issue_id,
        action=normalized.action,
        target_lifecycle=normalized.target_lifecycle,
        targets=targets + (evidence,),
        _project_context=context,
    )
