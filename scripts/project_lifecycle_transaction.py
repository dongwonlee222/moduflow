#!/usr/bin/env python3
"""Pure lifecycle transaction contract and deterministic identity helpers.

This module deliberately performs no filesystem, process, network, Git, or
remote-system operations. Transaction planning and persistence are layered on
top of this contract in later Issue 103 tasks.
"""

from dataclasses import dataclass, replace
import hashlib
import json
from collections.abc import Mapping
from pathlib import PurePosixPath, PureWindowsPath
import re
from types import MappingProxyType


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


def serialize_transaction_plan(plan):
    """Return a strict, redacted plan envelope with logical paths and hashes only."""
    _assert_exact_keys(plan, _PLAN_KEYS, "transaction plan")
    if plan["schema"] != PLAN_SCHEMA:
        raise ValueError("Unsupported transaction plan schema")
    return {**plan, "targets": _serialized_targets(plan["targets"])}


def serialize_transaction_result(result):
    """Return a strict, redacted result envelope with logical paths and hashes only."""
    _assert_exact_keys(result, _RESULT_KEYS, "transaction result")
    if result["schema"] != RESULT_SCHEMA:
        raise ValueError("Unsupported transaction result schema")
    if result["status"] not in _TERMINAL_STATUSES:
        raise ValueError("Unsupported transaction status")
    if result["status"] not in {"applied", "noop"} and (
        not result["failed_stage"] or not result["error_code"]
    ):
        raise ValueError("Non-success transaction results require failed_stage and error_code")
    return {
        **result,
        "targets": _serialized_targets(result["targets"]),
        "projected_validation": _serialized_validation_summary(
            result["projected_validation"]
        ),
        "post_apply_validation": _serialized_validation_summary(
            result["post_apply_validation"]
        ),
    }
