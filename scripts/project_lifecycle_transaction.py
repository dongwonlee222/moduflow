#!/usr/bin/env python3
"""Pure lifecycle transaction contract and deterministic identity helpers.

This module deliberately performs no filesystem, process, network, Git, or
remote-system operations. Transaction planning and persistence are layered on
top of this contract in later Issue 103 tasks.
"""

from dataclasses import dataclass, replace
import hashlib
import json
import re


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
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


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
        if not isinstance(production_change, dict) or not production_change.get("version"):
            raise ValueError("production-version requires production_change.version")
        version = str(production_change["version"]).strip()
        if not _SEMANTIC_VERSION.fullmatch(version):
            raise ValueError("production-version requires a semantic version")
        production_change = {**production_change, "version": version}
    elif production_change is not None:
        raise ValueError("production_change is only valid for production-version")
    if intent.roadmap_change is not None and not isinstance(intent.roadmap_change, dict):
        raise ValueError("roadmap_change must be a dictionary")

    return replace(
        intent,
        issue_id=str(intent.issue_id).strip(),
        action=action,
        actor=str(intent.actor).strip(),
        source_event=str(intent.source_event).strip(),
        target_lifecycle=fixed_target or supplied_target,
        production_change=production_change,
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
        serialized.append(dict(target))
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
    return {**result, "targets": _serialized_targets(result["targets"])}
