#!/usr/bin/env python3
"""Lifecycle transaction contracts, planning, and private projection helpers.

Planning reads canonical sources, and projected validation may use ephemeral
private roots. Canonical replacement and recovery remain separate boundaries.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
import errno
import hashlib
import json
from collections.abc import Mapping
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import secrets
import stat
from types import MappingProxyType

import project_issue_schema
import project_lifecycle_transaction_storage as transaction_storage
import project_operation
import project_registry
import validate_project_artifacts
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
EVIDENCE_SCHEMA = "moduflow.lifecycle-transaction-evidence.v1"
JOURNAL_SCHEMA = "moduflow.lifecycle-transaction-journal.v1"
LOCK_SCHEMA = "moduflow.lifecycle-transaction-lock.v1"

_LOCK_NAME = "lifecycle.lock"
_MAX_LOCK_BYTES = 4096
_LOCK_TOKEN = re.compile(r"^[0-9a-f]{32}$")
_LOCK_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)

_JOURNAL_PHASES = frozenset({
    "planned",
    "staged",
    "prepared",
    "applying",
    "post-validating",
    "finalizing",
    "rolling-back",
    "complete",
    "rolled-back",
    "recovery-required",
})
_JOURNAL_KEYS = frozenset({
    "schema",
    "transaction_id",
    "idempotency_key",
    "phase",
    "targets",
    "recovery_manifest_sha256",
    "applied_target_indexes",
    "rollback_target_indexes",
    "created_at",
    "updated_at",
})
_JOURNAL_TRANSITIONS = {
    "planned": frozenset({"staged", "rolled-back", "recovery-required"}),
    "staged": frozenset({"prepared", "rolled-back", "recovery-required"}),
    "prepared": frozenset({"applying", "rolling-back", "recovery-required"}),
    "applying": frozenset({
        "applying", "post-validating", "rolling-back", "recovery-required"
    }),
    "post-validating": frozenset({
        "finalizing", "rolling-back", "recovery-required"
    }),
    "finalizing": frozenset({
        "finalizing", "complete", "rolling-back", "recovery-required"
    }),
    "rolling-back": frozenset({
        "rolling-back", "rolled-back", "recovery-required"
    }),
    "complete": frozenset(),
    "rolled-back": frozenset(),
    "recovery-required": frozenset(),
}
_JOURNAL_RECOVERY_TRANSITIONS = frozenset({"rolling-back", "finalizing"})

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
_APPLY_FAULT_STAGES = frozenset({
    "after-plan",
    "after-replay-classification",
    "after-projected-validation",
    "before-private-apply",
    "after-private-complete",
})
_PUBLIC_FAILED_STAGES = frozenset({
    "authorization",
    "replay",
    "projected-validation",
    "preflight",
    "lock",
    "apply",
    "post-apply-validation",
    "finalizing",
    "rollback",
    "recovery",
})
_PUBLIC_ROLLBACK_STATUSES = frozenset({
    "not-required",
    "verified",
    "required",
})
_VALIDATION_SUMMARY_KEYS = frozenset({"valid", "rule_ids", "error_codes"})
_PROJECTED_VALIDATION_RULE_IDS = (
    "project-artifacts",
    "issue-schema",
    "lifecycle-consensus",
    "production-records",
)
_POST_APPLY_VALIDATION_RULE_IDS = (
    "canonical-targets",
    *_PROJECTED_VALIDATION_RULE_IDS,
)
_PROJECTED_CONTROL_FILES = (
    "config.json",
    "state.json",
    "project-profile.md",
    "environments.json",
    "integrations.json",
    "humans.json",
)
_PROJECTED_COPY_BUFFER_SIZE = 64 * 1024
_PROJECTED_POLICY_FIELDS = (
    "project_status",
    "trust_scope",
    "capabilities",
    "capability_reasons",
    "policy_inputs",
    "policy_trust_scope",
)
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
_EVIDENCE_RESULT_FIELDS = (
    "transaction_id",
    "idempotency_key",
    "status",
    "project_id",
    "issue_id",
    "action",
    "target_lifecycle",
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
)
_COMPLETED_EVIDENCE_KEYS = frozenset({
    "schema",
    *_EVIDENCE_RESULT_FIELDS,
    "targets",
    "projected_validation",
    "post_apply_validation",
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

    def __post_init__(self):
        if not isinstance(self.validation_rules, (list, tuple)):
            raise TypeError("validation_rules must be a list or tuple")
        if not isinstance(self._before_bytes, (bytes, bytearray, memoryview)) or not isinstance(
            self._after_bytes,
            (bytes, bytearray, memoryview),
        ):
            raise TypeError("private target content must be bytes-like")
        try:
            validation_rules = tuple(self.validation_rules)
            before_bytes = bytes(self._before_bytes)
            after_bytes = bytes(self._after_bytes)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "validation_rules and private target content must be immutable values"
            ) from exc
        if not all(isinstance(rule, str) for rule in validation_rules):
            raise TypeError("validation_rules must contain strings")
        object.__setattr__(self, "validation_rules", validation_rules)
        object.__setattr__(self, "_before_bytes", before_bytes)
        object.__setattr__(self, "_after_bytes", after_bytes)

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


@dataclass(frozen=True)
class _ProjectedState:
    root: Path
    context: dict = field(repr=False, compare=False)


@dataclass(frozen=True)
class _LifecycleLockOwner:
    transaction_id: str
    pid: int
    acquired_at: str
    owner_token: str
    _owner_bytes: bytes = field(repr=False, compare=False)
    _device: int = field(repr=False, compare=False)
    _inode: int = field(repr=False, compare=False)


@dataclass(frozen=True)
class _RecoverySubject:
    transaction_id: str
    project_id: str
    _root: Path = field(repr=False, compare=False)
    _project_context: Mapping = field(repr=False, compare=False)

    def __post_init__(self):
        if not isinstance(self._project_context, Mapping):
            raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
        object.__setattr__(
            self,
            "_project_context",
            _freeze_json_value(self._project_context),
        )


@dataclass(frozen=True)
class _RecoveryLockSnapshot:
    _pid: int = field(repr=False, compare=False)
    _bytes: bytes = field(repr=False, compare=False)
    _device: int = field(repr=False, compare=False)
    _inode: int = field(repr=False, compare=False)
    _size: int = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivatePreimageState:
    storage_targets: tuple[transaction_storage.StorageTarget, ...]
    preimages: tuple[transaction_storage.StoredPreimage, ...]
    _workspace: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivateStagedState:
    storage_targets: tuple[transaction_storage.StorageTarget, ...]
    preimages: tuple[transaction_storage.StoredPreimage, ...]
    staged_proposals: tuple[transaction_storage.StagedProposal, ...]
    recovery_manifest: transaction_storage.RecoveryManifest
    _workspace: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivatePreparedState:
    storage_targets: tuple[transaction_storage.StorageTarget, ...]
    preimages: tuple[transaction_storage.StoredPreimage, ...]
    staged_proposals: tuple[transaction_storage.StagedProposal, ...]
    recovery_manifest: transaction_storage.RecoveryManifest
    journal_sha256: str
    created_at: str
    _workspace: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivateAppliedState:
    storage_targets: tuple[transaction_storage.StorageTarget, ...]
    preimages: tuple[transaction_storage.StoredPreimage, ...]
    staged_proposals: tuple[transaction_storage.StagedProposal, ...]
    recovery_manifest: transaction_storage.RecoveryManifest
    applied_target_indexes: tuple[int, ...]
    journal_sha256: str
    created_at: str
    _workspace: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivatePostValidatedState:
    storage_targets: tuple[transaction_storage.StorageTarget, ...]
    preimages: tuple[transaction_storage.StoredPreimage, ...]
    staged_proposals: tuple[transaction_storage.StagedProposal, ...]
    recovery_manifest: transaction_storage.RecoveryManifest
    applied_target_indexes: tuple[int, ...]
    post_apply_validation: object = field(repr=False, compare=False)
    verified_target_count: int
    journal_sha256: str
    created_at: str
    _workspace: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivateCompletedState:
    storage_targets: tuple[transaction_storage.StorageTarget, ...] = field(
        repr=False,
        compare=False,
    )
    preimages: tuple[transaction_storage.StoredPreimage, ...] = field(
        repr=False,
        compare=False,
    )
    staged_proposals: tuple[transaction_storage.StagedProposal, ...] = field(
        repr=False,
        compare=False,
    )
    recovery_manifest: transaction_storage.RecoveryManifest = field(
        repr=False,
        compare=False,
    )
    applied_target_indexes: tuple[int, ...]
    projected_validation: object = field(repr=False, compare=False)
    post_apply_validation: object = field(repr=False, compare=False)
    transaction_result: object = field(repr=False, compare=False)
    verified_target_count: int
    journal_sha256: str
    created_at: str
    completed_at: str
    _workspace: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivateCompletionInput:
    intent: LifecycleIntent = field(repr=False, compare=False)
    next_command: str = field(repr=False, compare=False)
    projected_validation: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class _RecoveredJournalState:
    transaction_id: str
    journal: object = field(repr=False, compare=False)
    journal_sha256: str
    journal_next: object = field(repr=False, compare=False)
    journal_next_sha256: str
    authority: str
    _control_snapshot: object = field(repr=False, compare=False)
    _workspace: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class _RecoveredTransactionState:
    journal_state: _RecoveredJournalState = field(repr=False, compare=False)
    storage_targets: tuple = field(repr=False, compare=False)
    preimages: tuple = field(repr=False, compare=False)
    staged_proposals: tuple = field(repr=False, compare=False)
    recovery_manifest: object = field(repr=False, compare=False)
    _workspace: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivateEvidenceBinding:
    plan: LifecycleTransactionPlan = field(repr=False, compare=False)
    transaction_result: object = field(repr=False, compare=False)
    evidence_bytes: bytes = field(repr=False, compare=False)
    completed_at: str


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


class LifecycleProjectedValidationError(RuntimeError):
    """Stable projected-validation boundary error without private paths."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


class LifecycleJournalError(ValueError):
    """Stable journal contract failure without record values or private paths."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


_RECOVERY_READ_CODES = frozenset({
    "RECOVERY_JOURNAL_MISSING",
    "RECOVERY_JOURNAL_INVALID",
    "RECOVERY_JOURNAL_NEXT_INVALID",
    "RECOVERY_JOURNAL_NEXT_CONFLICT",
})


class LifecycleRecoveryReadError(RuntimeError):
    """Stable restart-journal read failure without rejected values."""

    def __init__(self, code):
        if code not in _RECOVERY_READ_CODES:
            code = "RECOVERY_JOURNAL_INVALID"
        self.code = code
        super().__init__(code)


_REPLAY_ERROR_CODES = frozenset({
    "REPLAY_EVIDENCE_CONFLICT",
    "REPLAY_CANONICAL_DRIFT",
})


class LifecycleReplayConflict(RuntimeError):
    """Stable completed-replay conflict without rejected values."""

    def __init__(self, code):
        if code not in _REPLAY_ERROR_CODES:
            raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
        self.code = code
        super().__init__(code)


class LifecyclePostApplyValidationError(RuntimeError):
    """Stable post-apply validation failure with a redacted summary."""

    def __init__(self, code, post_apply_validation):
        if code not in {
            "POST_APPLY_VALIDATION_INVALID",
            "POST_APPLY_VALIDATION_FAILED",
        }:
            raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
        summary = _frozen_validation_summary(post_apply_validation)
        if summary["valid"]:
            raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
        self.code = code
        self.post_apply_validation = summary
        super().__init__(code)


_FINALIZATION_ERROR_CODES = frozenset({
    "FINALIZATION_INPUT_INVALID",
    "FINALIZATION_EVIDENCE_ALREADY_PRESENT",
    "FINALIZATION_POST_APPLY_MISMATCH",
    "FINALIZATION_TARGET_MISMATCH",
})


class LifecycleFinalizationError(RuntimeError):
    """Stable private finalization failure without rejected values."""

    def __init__(self, code):
        if code not in _FINALIZATION_ERROR_CODES:
            raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
        self.code = code
        super().__init__(code)


_ROLLBACK_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _validated_rollback_signal_progress(
    original_error_code,
    applied_target_indexes,
    rollback_target_indexes,
    journal_sha256,
    *,
    rollback_error_code=None,
):
    codes = (original_error_code,)
    if rollback_error_code is not None:
        codes += (rollback_error_code,)
    valid_indexes = (
        isinstance(applied_target_indexes, tuple)
        and isinstance(rollback_target_indexes, tuple)
        and all(
            isinstance(index, int)
            and not isinstance(index, bool)
            and index >= 0
            for index in applied_target_indexes + rollback_target_indexes
        )
        and len(applied_target_indexes) == len(set(applied_target_indexes))
        and applied_target_indexes == tuple(sorted(applied_target_indexes))
        and rollback_target_indexes
        == tuple(reversed(applied_target_indexes))[:len(rollback_target_indexes)]
    )
    if (
        not all(
            isinstance(code, str) and _ROLLBACK_ERROR_CODE.fullmatch(code)
            for code in codes
        )
        or not valid_indexes
        or not isinstance(journal_sha256, str)
        or not _SHA256.fullmatch(journal_sha256)
    ):
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")


class LifecycleApplyRolledBack(RuntimeError):
    """Private successful-rollback signal with safe detached progress."""

    def __init__(
        self,
        *,
        original_error_code,
        applied_target_indexes,
        rollback_target_indexes,
        journal_sha256,
        post_apply_validation=None,
    ):
        _validated_rollback_signal_progress(
            original_error_code,
            applied_target_indexes,
            rollback_target_indexes,
            journal_sha256,
        )
        self.code = "TRANSACTION_ROLLED_BACK"
        self.original_error_code = original_error_code
        self.applied_target_indexes = tuple(applied_target_indexes)
        self.rollback_target_indexes = tuple(rollback_target_indexes)
        self.journal_sha256 = journal_sha256
        self.post_apply_validation = _optional_post_apply_validation(
            post_apply_validation
        )
        super().__init__(self.code)


class LifecycleRecoveryRequired(RuntimeError):
    """Private indeterminate-rollback signal with safe detached progress."""

    def __init__(
        self,
        *,
        original_error_code,
        rollback_error_code,
        applied_target_indexes,
        rollback_target_indexes,
        journal_sha256,
        post_apply_validation=None,
    ):
        _validated_rollback_signal_progress(
            original_error_code,
            applied_target_indexes,
            rollback_target_indexes,
            journal_sha256,
            rollback_error_code=rollback_error_code,
        )
        self.code = "TRANSACTION_RECOVERY_REQUIRED"
        self.original_error_code = original_error_code
        self.rollback_error_code = rollback_error_code
        self.applied_target_indexes = tuple(applied_target_indexes)
        self.rollback_target_indexes = tuple(rollback_target_indexes)
        self.journal_sha256 = journal_sha256
        self.post_apply_validation = _optional_post_apply_validation(
            post_apply_validation
        )
        super().__init__(self.code)


class LifecycleLockError(RuntimeError):
    """Stable lifecycle-lock failure without paths or owner-record values."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


_RECOVERY_LOCK_CODES = frozenset({
    "RECOVERY_LOCK_LIVE",
    "RECOVERY_LOCK_INVALID",
    "RECOVERY_LOCK_FOREIGN",
    "RECOVERY_LOCK_UNCERTAIN",
    "RECOVERY_LOCK_REPLACED",
    "RECOVERY_LOCK_RECLAIM_FAILED",
})


class LifecycleRecoveryLockError(RuntimeError):
    """Stable recovery-lock failure without private owner details."""

    def __init__(self, code):
        if code not in _RECOVERY_LOCK_CODES:
            code = "RECOVERY_LOCK_INVALID"
        self.code = code
        super().__init__(code)


def validate_journal_phase_transition(
    current_phase: str,
    next_phase: str,
    *,
    recovery: bool = False,
) -> None:
    """Reject an illegal journal transition without side effects."""
    if (
        not isinstance(current_phase, str)
        or not isinstance(next_phase, str)
        or current_phase not in _JOURNAL_PHASES
        or next_phase not in _JOURNAL_PHASES
    ):
        raise LifecycleJournalError("JOURNAL_PHASE_INVALID")
    if not isinstance(recovery, bool):
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
    allowed = _JOURNAL_TRANSITIONS[current_phase]
    if current_phase == "recovery-required" and recovery:
        allowed = _JOURNAL_RECOVERY_TRANSITIONS
    if next_phase not in allowed:
        raise LifecycleJournalError("JOURNAL_TRANSITION_INVALID")


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


def _frozen_validation_summary(summary):
    if not isinstance(summary, Mapping):
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
    try:
        candidate = {
            "valid": summary["valid"],
            "rule_ids": list(summary.get("rule_ids", ())),
            "error_codes": list(summary.get("error_codes", ())),
        }
        if set(summary) != set(candidate):
            raise ValueError("summary keys")
        serialized = _serialized_validation_summary(candidate)
    except (KeyError, TypeError, ValueError) as exc:
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID") from exc
    return MappingProxyType(
        {
            "valid": serialized["valid"],
            "rule_ids": tuple(serialized.get("rule_ids", ())),
            "error_codes": tuple(serialized.get("error_codes", ())),
        }
    )


def _optional_post_apply_validation(summary):
    if summary is None:
        return None
    frozen = _frozen_validation_summary(summary)
    if frozen["valid"] and (
        frozen["rule_ids"] != _POST_APPLY_VALIDATION_RULE_IDS
        or frozen["error_codes"]
    ):
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
    return frozen


def _summarize_validation_result(
    validation_result,
    *,
    rule_ids,
    contract_error,
    project_error,
    issue_error,
    drift_error,
):
    if not isinstance(validation_result, Mapping):
        return _serialized_validation_summary(
            {
                "valid": False,
                "rule_ids": list(rule_ids),
                "error_codes": [contract_error],
            }
        )
    valid = validation_result.get("valid")
    errors = validation_result.get("errors")
    issue_schema = validation_result.get("issue_schema")
    lifecycle_drift = validation_result.get("lifecycle_drift")
    issue_error_count = (
        issue_schema.get("errors")
        if isinstance(issue_schema, Mapping)
        else None
    )
    contract_valid = (
        validation_result.get("schema") == "moduflow.project-validation.v1"
        and isinstance(valid, bool)
        and isinstance(errors, list)
        and all(isinstance(error, str) for error in errors)
        and isinstance(issue_error_count, int)
        and not isinstance(issue_error_count, bool)
        and issue_error_count >= 0
        and isinstance(lifecycle_drift, list)
        and all(isinstance(drift, str) for drift in lifecycle_drift)
        and valid == (
            not errors
            and issue_error_count == 0
            and not lifecycle_drift
        )
    )
    if not contract_valid:
        return _serialized_validation_summary(
            {
                "valid": False,
                "rule_ids": list(rule_ids),
                "error_codes": [contract_error],
            }
        )

    error_codes = []
    if errors:
        error_codes.append(project_error)
    if issue_error_count:
        error_codes.append(issue_error)
    if lifecycle_drift:
        error_codes.append(drift_error)
    return _serialized_validation_summary(
        {
            "valid": valid,
            "rule_ids": list(rule_ids),
            "error_codes": error_codes,
        }
    )


def _projected_validation_contract_failure():
    return _summarize_validation_result(
        None,
        rule_ids=_PROJECTED_VALIDATION_RULE_IDS,
        contract_error="PROJECTED_VALIDATION_CONTRACT_INVALID",
        project_error="PROJECTED_PROJECT_INVALID",
        issue_error="PROJECTED_ISSUE_SCHEMA_INVALID",
        drift_error="PROJECTED_LIFECYCLE_DRIFT",
    )


def _summarize_projected_validation(validation_result):
    return _summarize_validation_result(
        validation_result,
        rule_ids=_PROJECTED_VALIDATION_RULE_IDS,
        contract_error="PROJECTED_VALIDATION_CONTRACT_INVALID",
        project_error="PROJECTED_PROJECT_INVALID",
        issue_error="PROJECTED_ISSUE_SCHEMA_INVALID",
        drift_error="PROJECTED_LIFECYCLE_DRIFT",
    )


def _summarize_post_apply_validation(validation_result):
    return _summarize_validation_result(
        validation_result,
        rule_ids=_POST_APPLY_VALIDATION_RULE_IDS,
        contract_error="POST_APPLY_VALIDATION_CONTRACT_INVALID",
        project_error="POST_APPLY_PROJECT_INVALID",
        issue_error="POST_APPLY_ISSUE_SCHEMA_INVALID",
        drift_error="POST_APPLY_LIFECYCLE_DRIFT",
    )


def _post_apply_failure_summary(error_code):
    if (
        not isinstance(error_code, str)
        or error_code not in {
            "POST_APPLY_TARGET_MISMATCH",
            "POST_APPLY_TARGET_UNPROVEN",
            "POST_APPLY_VALIDATION_FAILED",
        }
    ):
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
    return _serialized_validation_summary(
        {
            "valid": False,
            "rule_ids": list(_POST_APPLY_VALIDATION_RULE_IDS),
            "error_codes": [error_code],
        }
    )


def _writable_projected_plan_context(plan):
    if not isinstance(plan, LifecycleTransactionPlan):
        raise TypeError("plan must be a LifecycleTransactionPlan")
    try:
        if (
            not isinstance(plan.transaction_id, str)
            or not _LOGICAL_NAME.fullmatch(plan.transaction_id)
        ):
            raise ValueError("transaction ID must be logical")
        context = _json_value(plan._project_context)
        root = Path(plan.canonical_root).resolve()
        context = project_registry.context_for_operation(
            root,
            project_context=context,
        )
    except (OSError, TypeError, ValueError) as exc:
        raise LifecycleProjectedValidationError(
            "PROJECTED_CONTEXT_INVALID"
        ) from exc
    project_operation.require_project_capability(context, "write")
    return root, context


def _authorized_recovery_subject(
    project_root,
    transaction_id,
    *,
    project_context=None,
):
    """Resolve one explicit recovery identity and require write capability."""
    try:
        if (
            not isinstance(transaction_id, str)
            or not _LOGICAL_NAME.fullmatch(transaction_id)
        ):
            raise ValueError("transaction ID must be logical")
        root = Path(project_root).resolve()
        context = project_registry.context_for_operation(
            root,
            project_context=project_context,
        )
    except (OSError, TypeError, ValueError) as exc:
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID") from exc
    project_operation.require_project_capability(context, "write")
    project_id = context.get("project_id") or "explicit-root"
    if not isinstance(project_id, str) or not project_id:
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
    return _RecoverySubject(
        transaction_id=transaction_id,
        project_id=project_id,
        _root=root,
        _project_context=context,
    )


def _projected_target_parts(relative_path):
    if (
        not isinstance(relative_path, str)
        or not relative_path
        or "\\" in relative_path
        or relative_path.startswith("/")
        or PureWindowsPath(relative_path).is_absolute()
    ):
        raise LifecycleProjectedValidationError("PROJECTED_TARGET_INVALID")
    parts = tuple(relative_path.split("/"))
    if (
        not parts
        or parts[0] == ".git"
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise LifecycleProjectedValidationError("PROJECTED_TARGET_INVALID")
    return parts


def _validated_projected_targets(plan):
    if not isinstance(plan, LifecycleTransactionPlan):
        raise TypeError("plan must be a LifecycleTransactionPlan")
    seen = set()
    validated = []
    try:
        for target in plan.targets:
            if not isinstance(target, PlannedTarget):
                raise ValueError("target type")
            parts = _projected_target_parts(target.relative_path)
            if parts in seen:
                raise ValueError("duplicate target")
            if (
                not isinstance(target.after_size, int)
                or isinstance(target.after_size, bool)
                or target.after_size != len(target._after_bytes)
                or not isinstance(target.after_sha256, str)
                or not _SHA256.fullmatch(target.after_sha256)
                or target.after_sha256 != target_sha256(target._after_bytes)
            ):
                raise ValueError("target projection metadata")
            seen.add(parts)
            validated.append((target, parts))
    except LifecycleProjectedValidationError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise LifecycleProjectedValidationError(
            "PROJECTED_TARGET_INVALID"
        ) from exc
    return tuple(validated)


def _projected_project_context(plan, projected_root):
    try:
        source = _json_value(plan._project_context)
        root = Path(projected_root).resolve()
        relative_paths = dict(source.get("relative_paths") or {})
        if set(relative_paths) != set(project_registry.CANONICAL_PATH_DEFAULTS):
            raise ValueError("projected context roles")
        paths = {}
        for role in project_registry.CANONICAL_PATH_DEFAULTS:
            parts = _projected_target_parts(relative_paths[role])
            candidate = root.joinpath(*parts)
            candidate.relative_to(root)
            paths[role] = str(candidate)
        context = {
            "schema": source.get("schema") or "moduflow.project-resolution.v1",
            "status": "resolved",
            "project_id": plan.project_id,
            "canonical_root": str(root),
            "relative_paths": relative_paths,
            "paths": paths,
        }
        for field_name in _PROJECTED_POLICY_FIELDS:
            if field_name in source:
                context[field_name] = source[field_name]
        return project_registry.context_for_operation(
            root,
            project_context=context,
        )
    except LifecycleProjectedValidationError as exc:
        raise LifecycleProjectedValidationError(
            "PROJECTED_CONTEXT_INVALID"
        ) from exc
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise LifecycleProjectedValidationError(
            "PROJECTED_CONTEXT_INVALID"
        ) from exc


def _projected_copy_roots(context):
    relative_paths = (
        context.get("relative_paths") if isinstance(context, Mapping) else None
    )
    if not isinstance(relative_paths, Mapping):
        raise LifecycleProjectedValidationError("PROJECTED_CONTEXT_INVALID")
    candidates = set()
    try:
        for role in project_registry.CANONICAL_PATH_DEFAULTS:
            relative = relative_paths[role]
            if (
                not isinstance(relative, str)
                or not relative
                or relative == "."
                or "\\" in relative
                or relative.startswith("/")
                or PureWindowsPath(relative).is_absolute()
            ):
                raise ValueError("unsafe projected role root")
            parts = PurePosixPath(relative).parts
            if (
                not parts
                or parts[0] in {".git", ".moduflow"}
                or any(part in {"", ".", ".."} for part in parts)
            ):
                raise ValueError("unsafe projected role root")
            candidates.add(tuple(parts))
    except (KeyError, TypeError, ValueError) as exc:
        raise LifecycleProjectedValidationError(
            "PROJECTED_CONTEXT_INVALID"
        ) from exc

    selected = []
    for candidate in sorted(candidates, key=lambda parts: (len(parts), parts)):
        if any(candidate[:len(parent)] == parent for parent in selected):
            continue
        selected.append(candidate)
    return tuple(sorted(selected))


def _projected_source_metadata(parent_fd, name, *, missing_ok=False):
    try:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise LifecycleProjectedValidationError("PROJECTED_COPY_FAILED")
    except OSError as exc:
        raise LifecycleProjectedValidationError("PROJECTED_COPY_FAILED") from exc


def _open_projected_source_directory(root_fd, parts):
    current_fd = os.dup(root_fd)
    try:
        for part in parts:
            metadata = _projected_source_metadata(
                current_fd,
                part,
                missing_ok=True,
            )
            if metadata is None:
                os.close(current_fd)
                return None
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                raise LifecycleProjectedValidationError("PROJECTED_SOURCE_UNSAFE")
            next_fd = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current_fd,
            )
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except LifecycleProjectedValidationError:
        try:
            os.close(current_fd)
        except OSError:
            pass
        raise
    except OSError as exc:
        try:
            os.close(current_fd)
        except OSError:
            pass
        raise LifecycleProjectedValidationError("PROJECTED_COPY_FAILED") from exc


def _open_projected_destination_directory(root_fd, parts):
    current_fd = os.dup(root_fd)
    try:
        for part in parts:
            try:
                os.mkdir(part, mode=0o700, dir_fd=current_fd)
            except FileExistsError:
                pass
            metadata = _projected_source_metadata(current_fd, part)
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                raise LifecycleProjectedValidationError("PROJECTED_COPY_FAILED")
            next_fd = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current_fd,
            )
            os.fchmod(next_fd, 0o700)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except LifecycleProjectedValidationError:
        try:
            os.close(current_fd)
        except OSError:
            pass
        raise
    except OSError as exc:
        try:
            os.close(current_fd)
        except OSError:
            pass
        raise LifecycleProjectedValidationError("PROJECTED_COPY_FAILED") from exc


def _copy_projected_regular_file(source_parent_fd, destination_parent_fd, name):
    source_fd = None
    destination_fd = None
    try:
        source_fd = os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=source_parent_fd,
        )
        if not stat.S_ISREG(os.fstat(source_fd).st_mode):
            raise LifecycleProjectedValidationError("PROJECTED_SOURCE_UNSAFE")
        destination_fd = os.open(
            name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            mode=0o600,
            dir_fd=destination_parent_fd,
        )
        os.fchmod(destination_fd, 0o600)
        while True:
            chunk = os.read(source_fd, _PROJECTED_COPY_BUFFER_SIZE)
            if not chunk:
                break
            view = memoryview(chunk)
            while view:
                written = os.write(destination_fd, view)
                if written <= 0:
                    raise OSError(errno.EIO, "projected copy write failed")
                view = view[written:]
    except LifecycleProjectedValidationError:
        raise
    except OSError as exc:
        raise LifecycleProjectedValidationError("PROJECTED_COPY_FAILED") from exc
    finally:
        for descriptor in (destination_fd, source_fd):
            if descriptor is None:
                continue
            try:
                os.close(descriptor)
            except OSError:
                pass


def _copy_projected_directory(source_fd, destination_fd):
    try:
        names = sorted(os.listdir(source_fd))
    except OSError as exc:
        raise LifecycleProjectedValidationError("PROJECTED_COPY_FAILED") from exc
    for name in names:
        metadata = _projected_source_metadata(source_fd, name)
        if stat.S_ISLNK(metadata.st_mode):
            raise LifecycleProjectedValidationError("PROJECTED_SOURCE_UNSAFE")
        if stat.S_ISREG(metadata.st_mode):
            _copy_projected_regular_file(source_fd, destination_fd, name)
            continue
        if not stat.S_ISDIR(metadata.st_mode):
            raise LifecycleProjectedValidationError("PROJECTED_SOURCE_UNSAFE")
        source_child_fd = None
        destination_child_fd = None
        try:
            source_child_fd = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=source_fd,
            )
            os.mkdir(name, mode=0o700, dir_fd=destination_fd)
            destination_child_fd = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=destination_fd,
            )
            os.fchmod(destination_child_fd, 0o700)
            _copy_projected_directory(source_child_fd, destination_child_fd)
        except LifecycleProjectedValidationError:
            raise
        except OSError as exc:
            raise LifecycleProjectedValidationError("PROJECTED_COPY_FAILED") from exc
        finally:
            for descriptor in (destination_child_fd, source_child_fd):
                if descriptor is None:
                    continue
                try:
                    os.close(descriptor)
                except OSError:
                    pass


def _populate_private_projected_root(root_fd, control_fd, projected_fd, context):
    destination_control_fd = _open_projected_destination_directory(
        projected_fd,
        (".moduflow",),
    )
    try:
        for name in _PROJECTED_CONTROL_FILES:
            metadata = _projected_source_metadata(control_fd, name, missing_ok=True)
            if metadata is None:
                continue
            if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                raise LifecycleProjectedValidationError("PROJECTED_SOURCE_UNSAFE")
            _copy_projected_regular_file(control_fd, destination_control_fd, name)
    finally:
        os.close(destination_control_fd)

    for parts in _projected_copy_roots(context):
        source_fd = _open_projected_source_directory(root_fd, parts)
        if source_fd is None:
            continue
        destination_fd = None
        try:
            destination_fd = _open_projected_destination_directory(
                projected_fd,
                parts,
            )
            _copy_projected_directory(source_fd, destination_fd)
        finally:
            if destination_fd is not None:
                os.close(destination_fd)
            os.close(source_fd)


def _remove_projected_contents(directory_fd):
    for name in sorted(os.listdir(directory_fd)):
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
            child_fd = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            try:
                _remove_projected_contents(child_fd)
            finally:
                os.close(child_fd)
            os.rmdir(name, dir_fd=directory_fd)
        else:
            os.unlink(name, dir_fd=directory_fd)


@contextmanager
def _projected_root_descriptor(canonical_root, projected_root):
    root = Path(canonical_root).resolve()
    projected = Path(projected_root)
    if projected.parent != root / ".moduflow":
        raise LifecycleProjectedValidationError("PROJECTED_CONTEXT_INVALID")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    root_fd = None
    control_fd = None
    projected_fd = None
    try:
        root_fd = os.open(root, flags)
        control_fd = os.open(".moduflow", flags, dir_fd=root_fd)
        projected_fd = os.open(projected.name, flags, dir_fd=control_fd)
        yield projected_fd
    except LifecycleProjectedValidationError:
        raise
    except OSError as exc:
        raise LifecycleProjectedValidationError(
            "PROJECTED_OVERLAY_FAILED"
        ) from exc
    finally:
        for descriptor in (projected_fd, control_fd, root_fd):
            if descriptor is None:
                continue
            try:
                os.close(descriptor)
            except OSError:
                pass


def _open_projected_target_parent(projected_fd, parts):
    try:
        current_fd = os.dup(projected_fd)
    except OSError as exc:
        raise LifecycleProjectedValidationError(
            "PROJECTED_OVERLAY_FAILED"
        ) from exc
    try:
        for part in parts:
            try:
                os.mkdir(part, mode=0o700, dir_fd=current_fd)
            except FileExistsError:
                pass
            metadata = os.stat(
                part,
                dir_fd=current_fd,
                follow_symlinks=False,
            )
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(
                metadata.st_mode
            ):
                raise LifecycleProjectedValidationError(
                    "PROJECTED_TARGET_UNSAFE"
                )
            next_fd = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current_fd,
            )
            os.fchmod(next_fd, 0o700)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except LifecycleProjectedValidationError:
        try:
            os.close(current_fd)
        except OSError:
            pass
        raise
    except OSError as exc:
        try:
            os.close(current_fd)
        except OSError:
            pass
        raise LifecycleProjectedValidationError(
            "PROJECTED_OVERLAY_FAILED"
        ) from exc


def _overlay_projected_target(projected_fd, target, parts):
    parent_fd = None
    target_fd = None
    try:
        parent_fd = _open_projected_target_parent(projected_fd, parts[:-1])
        name = parts[-1]
        try:
            metadata = os.stat(
                name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            metadata = None
        if metadata is not None and (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
        ):
            raise LifecycleProjectedValidationError(
                "PROJECTED_TARGET_UNSAFE"
            )
        flags = (
            os.O_RDWR
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        if metadata is None:
            flags |= os.O_CREAT | os.O_EXCL
        target_fd = os.open(
            name,
            flags,
            mode=0o600,
            dir_fd=parent_fd,
        )
        if not stat.S_ISREG(os.fstat(target_fd).st_mode):
            raise LifecycleProjectedValidationError(
                "PROJECTED_TARGET_UNSAFE"
            )
        os.ftruncate(target_fd, 0)
        os.fchmod(target_fd, 0o600)
        remaining = memoryview(target._after_bytes)
        while remaining:
            written = os.write(target_fd, remaining)
            if written <= 0:
                raise OSError(errno.EIO, "projected overlay write failed")
            remaining = remaining[written:]
        os.lseek(target_fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        stored_size = 0
        while True:
            chunk = os.read(target_fd, _PROJECTED_COPY_BUFFER_SIZE)
            if not chunk:
                break
            stored_size += len(chunk)
            digest.update(chunk)
        if (
            stored_size != target.after_size
            or digest.hexdigest() != target.after_sha256
        ):
            raise OSError(
                errno.EIO,
                "projected overlay verification failed",
            )
    except LifecycleProjectedValidationError:
        raise
    except OSError as exc:
        raise LifecycleProjectedValidationError(
            "PROJECTED_OVERLAY_FAILED"
        ) from exc
    finally:
        for descriptor in (target_fd, parent_fd):
            if descriptor is None:
                continue
            try:
                os.close(descriptor)
            except OSError:
                pass


def _lock_timestamp(clock):
    value = clock() if callable(clock) else clock
    if value is None:
        value = datetime.now(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    elif hasattr(value, "isoformat"):
        value = value.isoformat()
    else:
        value = str(value)
    if not _LOCK_TIMESTAMP.fullmatch(value):
        raise LifecycleLockError("LOCK_CONTEXT_INVALID")
    return value


def _journal_timestamp(clock):
    try:
        value = clock() if callable(clock) else clock
        if value is None:
            value = datetime.now(timezone.utc)
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            value = value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        elif hasattr(value, "isoformat"):
            value = value.isoformat()
        else:
            value = str(value)
    except Exception as exc:
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID") from exc
    if not isinstance(value, str) or not _LOCK_TIMESTAMP.fullmatch(value):
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
    return value


def _journal_timestamps(clock, count=3):
    if (
        not isinstance(count, int)
        or isinstance(count, bool)
        or count <= 0
    ):
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
    return tuple(_journal_timestamp(clock) for _index in range(count))


def _lock_owner_values(plan, *, clock, pid, token_factory):
    owner_pid = os.getpid() if pid is None else pid
    if (
        not isinstance(owner_pid, int)
        or isinstance(owner_pid, bool)
        or owner_pid <= 0
    ):
        raise LifecycleLockError("LOCK_CONTEXT_INVALID")
    if token_factory is None:
        token = secrets.token_hex(16)
    elif callable(token_factory):
        token = token_factory()
    else:
        raise LifecycleLockError("LOCK_CONTEXT_INVALID")
    if not isinstance(token, str) or not _LOCK_TOKEN.fullmatch(token):
        raise LifecycleLockError("LOCK_CONTEXT_INVALID")
    acquired_at = _lock_timestamp(clock)
    record = {
        "schema": LOCK_SCHEMA,
        "transaction_id": plan.transaction_id,
        "pid": owner_pid,
        "acquired_at": acquired_at,
        "owner_token": token,
    }
    return owner_pid, acquired_at, token, canonical_json_bytes(record) + b"\n"


def _open_lock_directory(root):
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    root_fd = None
    control_fd = None
    transactions_fd = None
    try:
        try:
            root_fd = os.open(root, directory_flags)
            control_fd = os.open(
                ".moduflow",
                directory_flags,
                dir_fd=root_fd,
            )
        except OSError as exc:
            raise LifecycleLockError("LOCK_PATH_UNSAFE") from exc
        try:
            os.mkdir("transactions", mode=0o700, dir_fd=control_fd)
        except FileExistsError:
            pass
        except OSError as exc:
            raise LifecycleLockError("LOCK_CREATE_FAILED") from exc
        try:
            transactions_fd = os.open(
                "transactions",
                directory_flags,
                dir_fd=control_fd,
            )
            if not stat.S_ISDIR(os.fstat(transactions_fd).st_mode):
                raise OSError(errno.ENOTDIR, "transaction control is not a directory")
            os.fchmod(transactions_fd, 0o700)
        except OSError as exc:
            raise LifecycleLockError("LOCK_PATH_UNSAFE") from exc
        result = transactions_fd
        transactions_fd = None
        return result
    finally:
        for descriptor in (transactions_fd, control_fd, root_fd):
            if descriptor is None:
                continue
            try:
                os.close(descriptor)
            except OSError:
                pass


def _write_lock_bytes(lock_fd, owner_bytes):
    remaining = memoryview(owner_bytes)
    while remaining:
        written = os.write(lock_fd, remaining)
        if written <= 0:
            raise OSError(errno.EIO, "lock owner write failed")
        remaining = remaining[written:]


def _same_lock_inode(transactions_fd, metadata):
    try:
        current = os.stat(
            _LOCK_NAME,
            dir_fd=transactions_fd,
            follow_symlinks=False,
        )
    except OSError:
        return False
    return (
        stat.S_ISREG(current.st_mode)
        and current.st_dev == metadata.st_dev
        and current.st_ino == metadata.st_ino
    )


def _cleanup_created_lock(transactions_fd, metadata):
    if not _same_lock_inode(transactions_fd, metadata):
        return
    try:
        os.unlink(_LOCK_NAME, dir_fd=transactions_fd)
    except OSError:
        pass


def _acquire_lifecycle_lock(
    transactions_fd,
    plan,
    owner_values,
):
    owner_pid, acquired_at, token, owner_bytes = owner_values
    flags = (
        os.O_CREAT
        | os.O_EXCL
        | os.O_WRONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    lock_fd = None
    metadata = None
    try:
        try:
            lock_fd = os.open(
                _LOCK_NAME,
                flags,
                mode=0o600,
                dir_fd=transactions_fd,
            )
        except FileExistsError as exc:
            raise LifecycleLockError("LOCK_HELD") from exc
        except OSError as exc:
            raise LifecycleLockError("LOCK_CREATE_FAILED") from exc
        try:
            metadata = os.fstat(lock_fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise OSError(errno.EINVAL, "lock is not regular")
            os.fchmod(lock_fd, 0o600)
            _write_lock_bytes(lock_fd, owner_bytes)
        except OSError as exc:
            if metadata is not None:
                _cleanup_created_lock(transactions_fd, metadata)
            raise LifecycleLockError("LOCK_CREATE_FAILED") from exc
        return _LifecycleLockOwner(
            transaction_id=plan.transaction_id,
            pid=owner_pid,
            acquired_at=acquired_at,
            owner_token=token,
            _owner_bytes=owner_bytes,
            _device=metadata.st_dev,
            _inode=metadata.st_ino,
        )
    finally:
        if lock_fd is not None:
            try:
                os.close(lock_fd)
            except OSError:
                pass


def _lock_metadata_matches(owner, metadata):
    return (
        stat.S_ISREG(metadata.st_mode)
        and metadata.st_dev == owner._device
        and metadata.st_ino == owner._inode
    )


def _read_complete_lock(lock_fd, expected_size):
    chunks = []
    remaining = expected_size + 1
    while remaining:
        chunk = os.read(lock_fd, min(4096, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _release_lifecycle_lock(transactions_fd, owner):
    lock_fd = None
    read_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        try:
            metadata = os.stat(
                _LOCK_NAME,
                dir_fd=transactions_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError as exc:
            raise LifecycleLockError("LOCK_OWNER_MISMATCH") from exc
        except OSError as exc:
            raise LifecycleLockError("LOCK_RELEASE_FAILED") from exc
        if not _lock_metadata_matches(owner, metadata):
            raise LifecycleLockError("LOCK_OWNER_MISMATCH")
        try:
            lock_fd = os.open(
                _LOCK_NAME,
                read_flags,
                dir_fd=transactions_fd,
            )
            opened = os.fstat(lock_fd)
            if not _lock_metadata_matches(owner, opened):
                raise LifecycleLockError("LOCK_OWNER_MISMATCH")
            stored = _read_complete_lock(lock_fd, len(owner._owner_bytes))
        except LifecycleLockError:
            raise
        except OSError as exc:
            raise LifecycleLockError("LOCK_RELEASE_FAILED") from exc
        if not secrets.compare_digest(stored, owner._owner_bytes):
            raise LifecycleLockError("LOCK_OWNER_MISMATCH")
        try:
            current = os.stat(
                _LOCK_NAME,
                dir_fd=transactions_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError as exc:
            raise LifecycleLockError("LOCK_OWNER_MISMATCH") from exc
        except OSError as exc:
            raise LifecycleLockError("LOCK_RELEASE_FAILED") from exc
        if not _lock_metadata_matches(owner, current):
            raise LifecycleLockError("LOCK_OWNER_MISMATCH")
        try:
            os.unlink(_LOCK_NAME, dir_fd=transactions_fd)
        except OSError as exc:
            raise LifecycleLockError("LOCK_RELEASE_FAILED") from exc
    finally:
        if lock_fd is not None:
            try:
                os.close(lock_fd)
            except OSError:
                pass


def _open_recovery_lock_directory(subject):
    if not isinstance(subject, _RecoverySubject):
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    root_fd = None
    control_fd = None
    transactions_fd = None
    try:
        root_fd = os.open(subject._root, flags)
        control_fd = os.open(".moduflow", flags, dir_fd=root_fd)
        transactions_fd = os.open("transactions", flags, dir_fd=control_fd)
        metadata = os.fstat(transactions_fd)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o700
        ):
            raise OSError(errno.EINVAL, "unsafe recovery lock directory")
        result = transactions_fd
        transactions_fd = None
        return result
    except LifecycleRecoveryLockError:
        raise
    except OSError as exc:
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID") from exc
    finally:
        for descriptor in (transactions_fd, control_fd, root_fd):
            if descriptor is None:
                continue
            try:
                os.close(descriptor)
            except OSError:
                pass


def _recovery_lock_metadata_matches(current, expected):
    return (
        stat.S_ISREG(current.st_mode)
        and stat.S_IMODE(current.st_mode) == 0o600
        and current.st_nlink == 1
        and current.st_dev == expected.st_dev
        and current.st_ino == expected.st_ino
        and current.st_size == expected.st_size
    )


def _read_recovery_lock_snapshot(transactions_fd, transaction_id):
    descriptor = None
    try:
        try:
            before = os.stat(
                _LOCK_NAME,
                dir_fd=transactions_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return None
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_nlink != 1
            or before.st_size <= 0
            or before.st_size > _MAX_LOCK_BYTES
        ):
            raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
        descriptor = os.open(
            _LOCK_NAME,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=transactions_fd,
        )
        opened = os.fstat(descriptor)
        payload = _read_complete_lock(descriptor, before.st_size)
        after = os.stat(
            _LOCK_NAME,
            dir_fd=transactions_fd,
            follow_symlinks=False,
        )
        final_opened = os.fstat(descriptor)
        if (
            not _recovery_lock_metadata_matches(opened, before)
            or not _recovery_lock_metadata_matches(after, before)
            or not _recovery_lock_metadata_matches(final_opened, before)
            or len(payload) != before.st_size
        ):
            raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
        try:
            record = json.loads(payload.decode("utf-8"))
        except (TypeError, ValueError, UnicodeError):
            raise LifecycleRecoveryLockError(
                "RECOVERY_LOCK_INVALID"
            ) from None
        expected_keys = {
            "schema",
            "transaction_id",
            "pid",
            "acquired_at",
            "owner_token",
        }
        if not isinstance(record, dict) or set(record) != expected_keys:
            raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
        canonical = canonical_json_bytes(record) + b"\n"
        if not secrets.compare_digest(canonical, payload):
            raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
        if (
            record["schema"] != LOCK_SCHEMA
            or not isinstance(record["transaction_id"], str)
            or not _LOGICAL_NAME.fullmatch(record["transaction_id"])
            or not isinstance(record["pid"], int)
            or isinstance(record["pid"], bool)
            or record["pid"] <= 0
            or not isinstance(record["acquired_at"], str)
            or not _LOCK_TIMESTAMP.fullmatch(record["acquired_at"])
            or not isinstance(record["owner_token"], str)
            or not _LOCK_TOKEN.fullmatch(record["owner_token"])
        ):
            raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
        if record["transaction_id"] != transaction_id:
            raise LifecycleRecoveryLockError("RECOVERY_LOCK_FOREIGN")
        return _RecoveryLockSnapshot(
            _pid=record["pid"],
            _bytes=payload,
            _device=before.st_dev,
            _inode=before.st_ino,
            _size=before.st_size,
        )
    except LifecycleRecoveryLockError:
        raise
    except OSError as exc:
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID") from exc
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _reclaim_stale_recovery_lock(
    transactions_fd,
    subject,
    snapshot,
    pid_probe,
):
    try:
        pid_probe(snapshot._pid, 0)
    except OSError as exc:
        if exc.errno != errno.ESRCH:
            raise LifecycleRecoveryLockError(
                "RECOVERY_LOCK_UNCERTAIN"
            ) from None
    except Exception:
        raise LifecycleRecoveryLockError(
            "RECOVERY_LOCK_UNCERTAIN"
        ) from None
    else:
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_LIVE")

    try:
        current = _read_recovery_lock_snapshot(
            transactions_fd,
            subject.transaction_id,
        )
    except LifecycleRecoveryLockError:
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_REPLACED") from None
    if (
        current is None
        or current._device != snapshot._device
        or current._inode != snapshot._inode
        or current._size != snapshot._size
        or not secrets.compare_digest(current._bytes, snapshot._bytes)
    ):
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_REPLACED")
    try:
        os.unlink(_LOCK_NAME, dir_fd=transactions_fd)
    except FileNotFoundError:
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_REPLACED") from None
    except OSError as exc:
        raise LifecycleRecoveryLockError(
            "RECOVERY_LOCK_RECLAIM_FAILED"
        ) from exc
    try:
        os.fsync(transactions_fd)
    except OSError as exc:
        raise LifecycleRecoveryLockError(
            "RECOVERY_LOCK_RECLAIM_FAILED"
        ) from exc


@contextmanager
def _exclusive_recovery_lock(
    subject,
    *,
    clock=None,
    pid=None,
    token_factory=None,
    pid_probe=None,
):
    """Reclaim only one proven stale owner, then yield a fresh recovery lock."""
    if not isinstance(subject, _RecoverySubject):
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
    probe = os.kill if pid_probe is None else pid_probe
    if not callable(probe):
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID")
    try:
        owner_values = _lock_owner_values(
            subject,
            clock=clock,
            pid=pid,
            token_factory=token_factory,
        )
    except LifecycleLockError as exc:
        raise LifecycleRecoveryLockError("RECOVERY_LOCK_INVALID") from exc
    transactions_fd = _open_recovery_lock_directory(subject)
    try:
        existing = _read_recovery_lock_snapshot(
            transactions_fd,
            subject.transaction_id,
        )
        if existing is not None:
            _reclaim_stale_recovery_lock(
                transactions_fd,
                subject,
                existing,
                probe,
            )
        try:
            owner = _acquire_lifecycle_lock(
                transactions_fd,
                subject,
                owner_values,
            )
        except LifecycleLockError as exc:
            code = (
                "RECOVERY_LOCK_LIVE"
                if exc.code == "LOCK_HELD"
                else "RECOVERY_LOCK_RECLAIM_FAILED"
            )
            raise LifecycleRecoveryLockError(code) from exc
        try:
            yield owner
        except BaseException as body_error:
            try:
                _release_lifecycle_lock(transactions_fd, owner)
            except LifecycleLockError as release_error:
                raise LifecycleRecoveryLockError(
                    "RECOVERY_LOCK_RECLAIM_FAILED"
                ) from release_error
            raise
        else:
            try:
                _release_lifecycle_lock(transactions_fd, owner)
            except LifecycleLockError as exc:
                raise LifecycleRecoveryLockError(
                    "RECOVERY_LOCK_RECLAIM_FAILED"
                ) from exc
    finally:
        try:
            os.close(transactions_fd)
        except OSError:
            pass


@contextmanager
def _exclusive_lifecycle_lock(
    plan: LifecycleTransactionPlan,
    *,
    clock=None,
    pid=None,
    token_factory=None,
):
    """Yield one private lock owner and remove only its unchanged lock."""
    if not isinstance(plan, LifecycleTransactionPlan):
        raise TypeError("plan must be a LifecycleTransactionPlan")
    try:
        root, _context = _writable_projected_plan_context(plan)
    except project_operation.ProjectOperationDenied:
        raise
    except LifecycleProjectedValidationError as exc:
        raise LifecycleLockError("LOCK_CONTEXT_INVALID") from exc
    owner_values = _lock_owner_values(
        plan,
        clock=clock,
        pid=pid,
        token_factory=token_factory,
    )
    transactions_fd = _open_lock_directory(root)
    try:
        owner = _acquire_lifecycle_lock(
            transactions_fd,
            plan,
            owner_values,
        )
        try:
            yield owner
        except BaseException as body_error:
            try:
                _release_lifecycle_lock(transactions_fd, owner)
            except LifecycleLockError as release_error:
                raise release_error from body_error
            raise
        else:
            _release_lifecycle_lock(transactions_fd, owner)
    finally:
        try:
            os.close(transactions_fd)
        except OSError:
            pass


def _storage_targets_from_plan(plan):
    return tuple(
        transaction_storage.StorageTarget(
            index=index,
            role=target.role,
            relative_path=target.relative_path,
            existed=target.existed,
            before_sha256=target.before_sha256,
            after_sha256=target.after_sha256,
            after_size=target.after_size,
            changed=target.changed,
            _before_bytes=target._before_bytes,
            _after_bytes=target._after_bytes,
        )
        for index, target in enumerate(plan.targets)
    )


def _serialized_journal_bytes(
    plan,
    phase,
    *,
    created_at,
    updated_at,
    recovery_manifest_sha256,
    applied_target_indexes=(),
    rollback_target_indexes=(),
):
    snapshot = serialize_transaction_journal(
        {
            "schema": JOURNAL_SCHEMA,
            "transaction_id": plan.transaction_id,
            "idempotency_key": plan.idempotency_key,
            "phase": phase,
            "targets": [target.to_public_dict() for target in plan.targets],
            "recovery_manifest_sha256": recovery_manifest_sha256,
            "applied_target_indexes": list(applied_target_indexes),
            "rollback_target_indexes": list(rollback_target_indexes),
            "created_at": created_at,
            "updated_at": updated_at,
        }
    )
    return canonical_json_bytes(snapshot) + b"\n"


@contextmanager
def _private_preimage_workspace(
    plan: LifecycleTransactionPlan,
    *,
    lock_clock=None,
    lock_pid=None,
    lock_token_factory=None,
):
    """Yield verified private preimages under write authorization and B1b lock."""
    if not isinstance(plan, LifecycleTransactionPlan):
        raise TypeError("plan must be a LifecycleTransactionPlan")
    root, _context = _writable_projected_plan_context(plan)
    storage_targets = _storage_targets_from_plan(plan)
    with _exclusive_lifecycle_lock(
        plan,
        clock=lock_clock,
        pid=lock_pid,
        token_factory=lock_token_factory,
    ):
        with transaction_storage.private_transaction_workspace(
            root,
            plan.transaction_id,
        ) as workspace:
            preimages = transaction_storage.store_preimages(
                workspace,
                storage_targets,
            )
            yield _PrivatePreimageState(
                storage_targets=storage_targets,
                preimages=preimages,
                _workspace=workspace,
            )


@contextmanager
def _private_staged_workspace(
    plan: LifecycleTransactionPlan,
    *,
    lock_clock=None,
    lock_pid=None,
    lock_token_factory=None,
):
    """Yield verified private recovery inputs without changing canonical targets."""
    with _private_preimage_workspace(
        plan,
        lock_clock=lock_clock,
        lock_pid=lock_pid,
        lock_token_factory=lock_token_factory,
    ) as preimage_state:
        staged_proposals = transaction_storage.stage_proposed_targets(
            preimage_state._workspace,
            preimage_state.storage_targets,
        )
        recovery_manifest = transaction_storage.finalize_recovery_manifest(
            preimage_state._workspace,
            preimage_state.storage_targets,
            preimage_state.preimages,
            staged_proposals,
        )
        yield _PrivateStagedState(
            storage_targets=preimage_state.storage_targets,
            preimages=preimage_state.preimages,
            staged_proposals=staged_proposals,
            recovery_manifest=recovery_manifest,
            _workspace=preimage_state._workspace,
        )


@contextmanager
def _private_prepared_workspace(
    plan: LifecycleTransactionPlan,
    *,
    journal_clock=None,
    lock_clock=None,
    lock_pid=None,
    lock_token_factory=None,
):
    """Persist planned through prepared recovery state without canonical writes."""
    if not isinstance(plan, LifecycleTransactionPlan):
        raise TypeError("plan must be a LifecycleTransactionPlan")
    root, _context = _writable_projected_plan_context(plan)
    storage_targets = _storage_targets_from_plan(plan)
    planned_at, staged_at, prepared_at = _journal_timestamps(journal_clock)
    validate_journal_phase_transition("planned", "staged")
    validate_journal_phase_transition("staged", "prepared")
    planned_bytes = _serialized_journal_bytes(
        plan,
        "planned",
        created_at=planned_at,
        updated_at=planned_at,
        recovery_manifest_sha256="absent",
    )

    with _exclusive_lifecycle_lock(
        plan,
        clock=lock_clock,
        pid=lock_pid,
        token_factory=lock_token_factory,
    ):
        transaction_storage.verify_canonical_preimages(root, storage_targets)
        with transaction_storage.private_transaction_workspace(
            root,
            plan.transaction_id,
        ) as workspace:
            planned_sha256 = transaction_storage.persist_serialized_journal(
                workspace,
                planned_bytes,
                expected_previous_sha256="absent",
            )
            preimages = transaction_storage.store_preimages(
                workspace,
                storage_targets,
            )
            staged_proposals = transaction_storage.stage_proposed_targets(
                workspace,
                storage_targets,
            )
            recovery_manifest = transaction_storage.finalize_recovery_manifest(
                workspace,
                storage_targets,
                preimages,
                staged_proposals,
            )
            staged_bytes = _serialized_journal_bytes(
                plan,
                "staged",
                created_at=planned_at,
                updated_at=staged_at,
                recovery_manifest_sha256="absent",
            )
            staged_sha256 = transaction_storage.persist_serialized_journal(
                workspace,
                staged_bytes,
                expected_previous_sha256=planned_sha256,
            )
            prepared_bytes = _serialized_journal_bytes(
                plan,
                "prepared",
                created_at=planned_at,
                updated_at=prepared_at,
                recovery_manifest_sha256=recovery_manifest.sha256,
            )
            prepared_sha256 = transaction_storage.persist_serialized_journal(
                workspace,
                prepared_bytes,
                expected_previous_sha256=staged_sha256,
            )
            yield _PrivatePreparedState(
                storage_targets=storage_targets,
                preimages=preimages,
                staged_proposals=staged_proposals,
                recovery_manifest=recovery_manifest,
                journal_sha256=prepared_sha256,
                created_at=planned_at,
                _workspace=workspace,
            )


def _persist_progress_journal(
    prepared,
    plan,
    *,
    phase,
    updated_at,
    applied_target_indexes,
    rollback_target_indexes,
    expected_previous_sha256,
):
    journal_bytes = _serialized_journal_bytes(
        plan,
        phase,
        created_at=prepared.created_at,
        updated_at=updated_at,
        recovery_manifest_sha256=prepared.recovery_manifest.sha256,
        applied_target_indexes=applied_target_indexes,
        rollback_target_indexes=rollback_target_indexes,
    )
    return transaction_storage.persist_serialized_journal(
        prepared._workspace,
        journal_bytes,
        expected_previous_sha256=expected_previous_sha256,
    )


def _apply_prepared_targets(
    prepared,
    plan,
    timestamps,
    successful_indexes,
    journal_state,
):
    journal_state["sha256"] = _persist_progress_journal(
        prepared,
        plan,
        phase="applying",
        updated_at=timestamps[3],
        applied_target_indexes=(),
        rollback_target_indexes=(),
        expected_previous_sha256=journal_state["sha256"],
    )
    for target, proposal in zip(
        prepared.storage_targets,
        prepared.staged_proposals,
    ):
        if target.role == "evidence":
            break
        if not target.changed:
            transaction_storage.verify_canonical_target(
                prepared._workspace,
                target,
            )
            continue
        index = transaction_storage.apply_staged_target(
            prepared._workspace,
            target,
            proposal,
        )
        successful_indexes.append(index)
        journal_state["sha256"] = _persist_progress_journal(
            prepared,
            plan,
            phase="applying",
            updated_at=timestamps[3 + len(successful_indexes)],
            applied_target_indexes=tuple(successful_indexes),
            rollback_target_indexes=(),
            expected_previous_sha256=journal_state["sha256"],
        )
    changed_count = sum(
        target.changed and target.role != "evidence"
        for target in prepared.storage_targets
    )
    journal_state["sha256"] = _persist_progress_journal(
        prepared,
        plan,
        phase="post-validating",
        updated_at=timestamps[4 + changed_count],
        applied_target_indexes=tuple(successful_indexes),
        rollback_target_indexes=(),
        expected_previous_sha256=journal_state["sha256"],
    )
    return _PrivateAppliedState(
        storage_targets=prepared.storage_targets,
        preimages=prepared.preimages,
        staged_proposals=prepared.staged_proposals,
        recovery_manifest=prepared.recovery_manifest,
        applied_target_indexes=tuple(successful_indexes),
        journal_sha256=journal_state["sha256"],
        created_at=prepared.created_at,
        _workspace=prepared._workspace,
    )


def _verify_post_apply_targets(applied_state):
    verified = 0
    try:
        for target in applied_state.storage_targets:
            if target.role == "evidence" or not target.changed:
                transaction_storage.verify_canonical_target(
                    applied_state._workspace,
                    target,
                )
            else:
                state = transaction_storage.classify_canonical_target(
                    applied_state._workspace,
                    target,
                )
                if state != "after":
                    raise LifecyclePostApplyValidationError(
                        "POST_APPLY_VALIDATION_INVALID",
                        _post_apply_failure_summary(
                            "POST_APPLY_TARGET_MISMATCH"
                        ),
                    )
            verified += 1
    except LifecyclePostApplyValidationError:
        raise
    except (
        transaction_storage.LifecycleCanonicalConflict,
        transaction_storage.LifecycleStorageError,
    ) as exc:
        raise LifecyclePostApplyValidationError(
            "POST_APPLY_VALIDATION_FAILED",
            _post_apply_failure_summary("POST_APPLY_TARGET_UNPROVEN"),
        ) from exc
    return verified


def _post_validate_applied_state(
    applied_state,
    plan,
    canonical_root,
    canonical_context,
):
    verified_target_count = _verify_post_apply_targets(applied_state)
    try:
        validation_result = validate_project_artifacts.validate_project(
            canonical_root,
            project_context=canonical_context,
        )
    except Exception as exc:
        raise LifecyclePostApplyValidationError(
            "POST_APPLY_VALIDATION_FAILED",
            _post_apply_failure_summary("POST_APPLY_VALIDATION_FAILED"),
        ) from exc
    summary = _summarize_post_apply_validation(validation_result)
    if not summary["valid"]:
        raise LifecyclePostApplyValidationError(
            "POST_APPLY_VALIDATION_INVALID",
            summary,
        )
    return _PrivatePostValidatedState(
        storage_targets=applied_state.storage_targets,
        preimages=applied_state.preimages,
        staged_proposals=applied_state.staged_proposals,
        recovery_manifest=applied_state.recovery_manifest,
        applied_target_indexes=applied_state.applied_target_indexes,
        post_apply_validation=_frozen_validation_summary(summary),
        verified_target_count=verified_target_count,
        journal_sha256=applied_state.journal_sha256,
        created_at=applied_state.created_at,
        _workspace=applied_state._workspace,
    )


def _classify_changed_target(workspace, target):
    if target.role == "evidence":
        return transaction_storage.classify_finalized_evidence(
            workspace,
            target,
        )
    return transaction_storage.classify_canonical_target(
        workspace,
        target,
    )


def _rollback_changed_target(workspace, target, preimage):
    if target.role == "evidence":
        return transaction_storage.rollback_finalized_evidence(
            workspace,
            target,
            preimage,
        )
    return transaction_storage.rollback_canonical_target(
        workspace,
        target,
        preimage,
    )


def _verify_complete_after_state(state):
    verified = 0
    for target in state.storage_targets:
        if target.changed:
            if _classify_changed_target(state._workspace, target) != "after":
                raise LifecycleFinalizationError(
                    "FINALIZATION_TARGET_MISMATCH"
                )
        else:
            transaction_storage.verify_canonical_target(
                state._workspace,
                target,
            )
        verified += 1
    return verified


def _finalize_post_validated_state(
    state,
    prepared,
    plan,
    binding,
    completion_input,
    timestamps,
    successful_indexes,
    journal_state,
):
    if (
        dict(state.post_apply_validation)
        != dict(_successful_post_apply_summary())
    ):
        raise LifecycleFinalizationError(
            "FINALIZATION_POST_APPLY_MISMATCH"
        )
    n = len(successful_indexes)
    journal_state["finalization_started"] = True
    journal_state["sha256"] = _persist_progress_journal(
        prepared,
        plan,
        phase="finalizing",
        updated_at=timestamps[5 + n],
        applied_target_indexes=tuple(successful_indexes),
        rollback_target_indexes=(),
        expected_previous_sha256=journal_state["sha256"],
    )
    evidence = prepared.storage_targets[-1]
    proposal = prepared.staged_proposals[-1]
    index = transaction_storage.finalize_staged_evidence(
        prepared._workspace,
        evidence,
        proposal,
    )
    successful_indexes.append(index)
    journal_state["sha256"] = _persist_progress_journal(
        prepared,
        plan,
        phase="finalizing",
        updated_at=timestamps[6 + n],
        applied_target_indexes=tuple(successful_indexes),
        rollback_target_indexes=(),
        expected_previous_sha256=journal_state["sha256"],
    )
    verified = _verify_complete_after_state(state)
    journal_state["sha256"] = _persist_progress_journal(
        prepared,
        plan,
        phase="complete",
        updated_at=timestamps[7 + n],
        applied_target_indexes=tuple(successful_indexes),
        rollback_target_indexes=(),
        expected_previous_sha256=journal_state["sha256"],
    )
    return _PrivateCompletedState(
        storage_targets=state.storage_targets,
        preimages=state.preimages,
        staged_proposals=state.staged_proposals,
        recovery_manifest=state.recovery_manifest,
        applied_target_indexes=tuple(successful_indexes),
        projected_validation=completion_input.projected_validation,
        post_apply_validation=state.post_apply_validation,
        transaction_result=binding.transaction_result,
        verified_target_count=verified,
        journal_sha256=journal_state["sha256"],
        created_at=state.created_at,
        completed_at=binding.completed_at,
        _workspace=state._workspace,
    )


def _reconciled_rollback_prefix(prepared, successful_indexes):
    changed = tuple(
        (target, preimage)
        for target, preimage in zip(
            prepared.storage_targets,
            prepared.preimages,
        )
        if target.changed
    )
    states = tuple(
        _classify_changed_target(
            prepared._workspace,
            target,
        )
        for target, _preimage in changed
    )
    after_positions = tuple(
        position
        for position, state in enumerate(states)
        if state == "after"
    )
    prefix_length = max(
        len(successful_indexes),
        (after_positions[-1] + 1) if after_positions else 0,
    )
    expected_successful = tuple(
        target.index
        for target, _preimage in changed[:len(successful_indexes)]
    )
    if (
        tuple(successful_indexes) != expected_successful
        or any(state != "before" for state in states[prefix_length:])
    ):
        raise transaction_storage.LifecycleStorageError(
            "STORAGE_CANONICAL_STATE_UNKNOWN"
        )
    return tuple(
        (target, preimage, states[position])
        for position, (target, preimage) in enumerate(changed[:prefix_length])
    )


def _verify_complete_rollback(prepared):
    verified = 0
    for target in prepared.storage_targets:
        if target.changed:
            state = _classify_changed_target(
                prepared._workspace,
                target,
            )
            if state != "before":
                raise transaction_storage.LifecycleStorageError(
                    "STORAGE_VERIFY_FAILED"
                )
        else:
            transaction_storage.verify_canonical_target(
                prepared._workspace,
                target,
            )
        verified += 1
    return verified


def _rollback_failed_apply(
    prepared,
    plan,
    original_error,
    successful_indexes,
    latest_sha256,
    timestamps,
    rollback_timestamp_index,
    post_apply_validation=None,
):
    confirmed_applied = tuple(successful_indexes)
    confirmed_rollback = []
    if post_apply_validation is None:
        post_apply_validation = getattr(
            original_error,
            "post_apply_validation",
            None,
        )
    rollback_failure_types = (
        transaction_storage.LifecycleCanonicalConflict,
        transaction_storage.LifecycleStorageError,
        LifecycleJournalError,
    )
    try:
        prefix = _reconciled_rollback_prefix(prepared, successful_indexes)
        confirmed_applied = tuple(
            target.index for target, _preimage, _state in prefix
        )
        latest_sha256 = _persist_progress_journal(
            prepared,
            plan,
            phase="rolling-back",
            updated_at=timestamps[rollback_timestamp_index],
            applied_target_indexes=confirmed_applied,
            rollback_target_indexes=(),
            expected_previous_sha256=latest_sha256,
        )
        for target, preimage, state in reversed(prefix):
            if state == "after":
                _rollback_changed_target(
                    prepared._workspace,
                    target,
                    preimage,
                )
            confirmed_rollback.append(target.index)
            latest_sha256 = _persist_progress_journal(
                prepared,
                plan,
                phase="rolling-back",
                updated_at=(
                    timestamps[
                        rollback_timestamp_index
                        + len(confirmed_rollback)
                    ]
                ),
                applied_target_indexes=confirmed_applied,
                rollback_target_indexes=tuple(confirmed_rollback),
                expected_previous_sha256=latest_sha256,
            )
        _verify_complete_rollback(prepared)
        latest_sha256 = _persist_progress_journal(
            prepared,
            plan,
            phase="rolled-back",
            updated_at=timestamps[
                rollback_timestamp_index
                + len(confirmed_rollback)
                + 1
            ],
            applied_target_indexes=confirmed_applied,
            rollback_target_indexes=tuple(confirmed_rollback),
            expected_previous_sha256=latest_sha256,
        )
    except rollback_failure_types as rollback_error:
        try:
            latest_sha256 = _persist_progress_journal(
                prepared,
                plan,
                phase="recovery-required",
                updated_at=timestamps[-1],
                applied_target_indexes=confirmed_applied,
                rollback_target_indexes=tuple(confirmed_rollback),
                expected_previous_sha256=latest_sha256,
            )
        except rollback_failure_types:
            pass
        raise LifecycleRecoveryRequired(
            original_error_code=original_error.code,
            rollback_error_code=rollback_error.code,
            applied_target_indexes=confirmed_applied,
            rollback_target_indexes=tuple(confirmed_rollback),
            journal_sha256=latest_sha256,
            post_apply_validation=post_apply_validation,
        ) from rollback_error
    raise LifecycleApplyRolledBack(
        original_error_code=original_error.code,
        applied_target_indexes=confirmed_applied,
        rollback_target_indexes=tuple(confirmed_rollback),
        journal_sha256=latest_sha256,
        post_apply_validation=post_apply_validation,
    ) from original_error


@contextmanager
def _private_applied_workspace(
    plan: LifecycleTransactionPlan,
    *,
    completion_input,
    journal_clock=None,
    lock_clock=None,
    lock_pid=None,
    lock_token_factory=None,
):
    """Complete one private lifecycle transaction under the existing lock."""
    if not isinstance(plan, LifecycleTransactionPlan):
        raise TypeError("plan must be a LifecycleTransactionPlan")
    changed_count = sum(
        target.changed and target.role != "evidence"
        for target in plan.targets
    )
    timestamps = _journal_timestamps(
        journal_clock,
        11 + 2 * changed_count,
    )
    if not isinstance(completion_input, _PrivateCompletionInput):
        raise LifecycleFinalizationError(
            "FINALIZATION_INPUT_INVALID"
        )
    completion_input = _prepare_completion_input(
        plan,
        completion_input.intent,
        completion_input.next_command,
        completion_input.projected_validation,
    )
    binding = _bind_success_evidence(plan, completion_input, timestamps)
    rebound_plan = binding.plan
    canonical_root, canonical_context = _writable_projected_plan_context(
        rebound_plan
    )
    storage_targets = _storage_targets_from_plan(rebound_plan)
    changed_ordinary = tuple(
        target.index
        for target in storage_targets
        if target.changed and target.role != "evidence"
    )
    changed_targets = tuple(
        target.index
        for target in storage_targets
        if target.changed
    )
    validate_journal_phase_transition("prepared", "applying")
    for _index in changed_ordinary:
        validate_journal_phase_transition("applying", "applying")
    validate_journal_phase_transition("applying", "post-validating")
    validate_journal_phase_transition("post-validating", "finalizing")
    validate_journal_phase_transition("finalizing", "finalizing")
    validate_journal_phase_transition("finalizing", "complete")
    for phase in ("prepared", "applying", "post-validating", "finalizing"):
        validate_journal_phase_transition(phase, "rolling-back")
        validate_journal_phase_transition(phase, "recovery-required")
    for _index in changed_targets:
        validate_journal_phase_transition("rolling-back", "rolling-back")
    validate_journal_phase_transition("rolling-back", "rolled-back")
    validate_journal_phase_transition("rolling-back", "recovery-required")
    prepared_clock = iter(timestamps[:3])

    with _private_prepared_workspace(
        rebound_plan,
        journal_clock=lambda: next(prepared_clock),
        lock_clock=lock_clock,
        lock_pid=lock_pid,
        lock_token_factory=lock_token_factory,
    ) as prepared:
        successful_indexes = []
        post_validated_state = None
        journal_state = {
            "sha256": prepared.journal_sha256,
            "finalization_started": False,
        }
        try:
            applied_state = _apply_prepared_targets(
                prepared,
                rebound_plan,
                timestamps,
                successful_indexes,
                journal_state,
            )
            post_validated_state = _post_validate_applied_state(
                applied_state,
                rebound_plan,
                canonical_root,
                canonical_context,
            )
            completed_state = _finalize_post_validated_state(
                post_validated_state,
                prepared,
                rebound_plan,
                binding,
                completion_input,
                timestamps,
                successful_indexes,
                journal_state,
            )
        except (
            transaction_storage.LifecycleCanonicalConflict,
            transaction_storage.LifecycleStorageError,
            LifecycleFinalizationError,
            LifecycleJournalError,
            LifecyclePostApplyValidationError,
        ) as original_error:
            _rollback_failed_apply(
                prepared,
                rebound_plan,
                original_error,
                tuple(successful_indexes),
                journal_state["sha256"],
                timestamps,
                (
                    7 + changed_count
                    if journal_state["finalization_started"]
                    else 5 + changed_count
                ),
                post_apply_validation=(
                    post_validated_state.post_apply_validation
                    if post_validated_state is not None
                    else None
                ),
            )
        yield completed_state


@contextmanager
def _private_projected_root(plan):
    root, context = _writable_projected_plan_context(plan)
    read_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    directory_flags = (
        read_flags
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    root_fd = None
    control_fd = None
    projected_fd = None
    projected_name = ""
    try:
        try:
            root_fd = os.open(root, directory_flags)
            control_fd = os.open(
                ".moduflow",
                directory_flags,
                dir_fd=root_fd,
            )
            for _attempt in range(16):
                candidate = (
                    f".{plan.transaction_id}-projected-"
                    f"{secrets.token_hex(8)}"
                )
                try:
                    os.mkdir(candidate, mode=0o700, dir_fd=control_fd)
                except FileExistsError:
                    continue
                projected_name = candidate
                break
            if not projected_name:
                raise LifecycleProjectedValidationError(
                    "PROJECTED_ROOT_UNAVAILABLE"
                )
            projected_fd = os.open(
                projected_name,
                directory_flags,
                dir_fd=control_fd,
            )
            os.fchmod(projected_fd, 0o700)
        except LifecycleProjectedValidationError:
            raise
        except OSError as exc:
            raise LifecycleProjectedValidationError(
                "PROJECTED_ROOT_UNAVAILABLE"
            ) from exc

        _populate_private_projected_root(
            root_fd,
            control_fd,
            projected_fd,
            context,
        )
        yield root / ".moduflow" / projected_name
    finally:
        cleanup_error = None
        if projected_fd is not None:
            try:
                _remove_projected_contents(projected_fd)
            except OSError as exc:
                cleanup_error = exc
            finally:
                try:
                    os.close(projected_fd)
                except OSError:
                    pass
        if projected_name and control_fd is not None:
            try:
                os.rmdir(projected_name, dir_fd=control_fd)
            except OSError as exc:
                if cleanup_error is None:
                    cleanup_error = exc
        for descriptor in (control_fd, root_fd):
            if descriptor is None:
                continue
            try:
                os.close(descriptor)
            except OSError:
                pass
        if cleanup_error is not None:
            raise LifecycleProjectedValidationError(
                "PROJECTED_ROOT_CLEANUP_FAILED"
            ) from cleanup_error


@contextmanager
def _private_projected_state(plan):
    canonical_root, _context = _writable_projected_plan_context(plan)
    targets = _validated_projected_targets(plan)
    with _private_projected_root(plan) as projected_root:
        with _projected_root_descriptor(
            canonical_root,
            projected_root,
        ) as projected_fd:
            for target, parts in targets:
                _overlay_projected_target(projected_fd, target, parts)
        projected_context = _projected_project_context(plan, projected_root)
        yield _ProjectedState(
            root=Path(projected_root).resolve(),
            context=projected_context,
        )


def validate_projected_transaction(plan: LifecycleTransactionPlan) -> dict:
    """Validate one private projected state without replacing canonical targets."""
    if not isinstance(plan, LifecycleTransactionPlan):
        raise TypeError("plan must be a LifecycleTransactionPlan")
    try:
        with _private_projected_state(plan) as projected:
            validation_result = validate_project_artifacts.validate_project(
                projected.root,
                project_context=projected.context,
            )
            return _summarize_projected_validation(validation_result)
    except (
        project_operation.ProjectOperationDenied,
        LifecycleProjectedValidationError,
    ):
        raise
    except Exception as exc:
        raise LifecycleProjectedValidationError(
            "PROJECTED_VALIDATION_FAILED"
        ) from exc


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


def _journal_record_failure():
    raise LifecycleJournalError("JOURNAL_RECORD_INVALID")


def _journal_progress_failure():
    raise LifecycleJournalError("JOURNAL_PROGRESS_INVALID")


def _serialized_journal_targets(targets):
    try:
        serialized = _serialized_targets(targets)
    except (TypeError, ValueError, KeyError):
        _journal_record_failure()
    if not serialized:
        _journal_record_failure()
    total = len(serialized)
    if any(
        target["apply_order"] != index
        or target["rollback_order"] != total - index - 1
        for index, target in enumerate(serialized)
    ):
        _journal_record_failure()
    if serialized[-1]["role"] != "evidence" or any(
        target["role"] == "evidence" for target in serialized[:-1]
    ):
        _journal_record_failure()
    return serialized


def _serialized_journal_indexes(indexes, target_count):
    if (
        not isinstance(indexes, list)
        or any(
            not isinstance(index, int)
            or isinstance(index, bool)
            or index < 0
            or index >= target_count
            for index in indexes
        )
        or len(indexes) != len(set(indexes))
    ):
        _journal_progress_failure()
    return list(indexes)


def _validate_journal_progress(
    phase,
    targets,
    manifest_sha256,
    applied_indexes,
    rollback_indexes,
):
    changed_indexes = [
        index for index, target in enumerate(targets) if target["changed"]
    ]
    canonical_changed_indexes = [
        index
        for index, target in enumerate(targets)
        if target["changed"] and target["role"] != "evidence"
    ]
    if applied_indexes != changed_indexes[:len(applied_indexes)]:
        _journal_progress_failure()
    reverse_applied = list(reversed(applied_indexes))
    if rollback_indexes != reverse_applied[:len(rollback_indexes)]:
        _journal_progress_failure()

    manifest_required = {
        "prepared",
        "applying",
        "post-validating",
        "finalizing",
        "rolling-back",
        "complete",
    }
    if phase in {"planned", "staged"} and manifest_sha256 != "absent":
        _journal_progress_failure()
    if phase in manifest_required and manifest_sha256 == "absent":
        _journal_progress_failure()
    if (
        phase in {"recovery-required", "rolled-back"}
        and (applied_indexes or rollback_indexes)
        and manifest_sha256 == "absent"
    ):
        _journal_progress_failure()

    if phase in {"planned", "staged", "prepared"} and (
        applied_indexes or rollback_indexes
    ):
        _journal_progress_failure()
    if phase == "applying" and (
        rollback_indexes
        or applied_indexes != canonical_changed_indexes[:len(applied_indexes)]
    ):
        _journal_progress_failure()
    if phase == "post-validating" and (
        applied_indexes != canonical_changed_indexes or rollback_indexes
    ):
        _journal_progress_failure()
    if phase == "finalizing" and (
        applied_indexes not in (canonical_changed_indexes, changed_indexes)
        or rollback_indexes
    ):
        _journal_progress_failure()
    if phase == "complete" and (
        applied_indexes != changed_indexes or rollback_indexes
    ):
        _journal_progress_failure()
    if phase == "rolled-back" and rollback_indexes != reverse_applied:
        _journal_progress_failure()


def serialize_transaction_journal(journal: dict) -> dict:
    """Validate and return a detached redacted journal snapshot."""
    try:
        _assert_exact_keys(journal, _JOURNAL_KEYS, "transaction journal")
    except (TypeError, ValueError):
        _journal_record_failure()
    if journal["schema"] != JOURNAL_SCHEMA:
        raise LifecycleJournalError("JOURNAL_SCHEMA_UNSUPPORTED")
    phase = journal["phase"]
    if not isinstance(phase, str) or phase not in _JOURNAL_PHASES:
        raise LifecycleJournalError("JOURNAL_PHASE_INVALID")

    text_fields = {}
    for field in (
        "transaction_id",
        "idempotency_key",
        "created_at",
        "updated_at",
    ):
        value = journal[field]
        if not isinstance(value, str) or not value:
            _journal_record_failure()
        text_fields[field] = value

    manifest_sha256 = journal["recovery_manifest_sha256"]
    if manifest_sha256 != "absent" and (
        not isinstance(manifest_sha256, str)
        or not _SHA256.fullmatch(manifest_sha256)
    ):
        _journal_record_failure()
    targets = _serialized_journal_targets(journal["targets"])
    applied_indexes = _serialized_journal_indexes(
        journal["applied_target_indexes"],
        len(targets),
    )
    rollback_indexes = _serialized_journal_indexes(
        journal["rollback_target_indexes"],
        len(targets),
    )
    _validate_journal_progress(
        phase,
        targets,
        manifest_sha256,
        applied_indexes,
        rollback_indexes,
    )
    return {
        "schema": JOURNAL_SCHEMA,
        "transaction_id": text_fields["transaction_id"],
        "idempotency_key": text_fields["idempotency_key"],
        "phase": phase,
        "targets": targets,
        "recovery_manifest_sha256": manifest_sha256,
        "applied_target_indexes": applied_indexes,
        "rollback_target_indexes": rollback_indexes,
        "created_at": text_fields["created_at"],
        "updated_at": text_fields["updated_at"],
    }


def _load_exact_recovery_journal(snapshot, transaction_id, error_code):
    if snapshot.state != "present":
        return None
    try:
        decoded = json.loads(snapshot._bytes.decode("utf-8"))
        serialized = serialize_transaction_journal(decoded)
        if canonical_json_bytes(serialized) + b"\n" != snapshot._bytes:
            raise ValueError("journal bytes are not canonical")
        if serialized["transaction_id"] != transaction_id:
            raise ValueError("journal identity does not match workspace")
        return _freeze_json_value(serialized)
    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeError,
        LifecycleJournalError,
    ):
        raise LifecycleRecoveryReadError(error_code) from None


def _journal_progress_is_monotonic(current, successor, field):
    current_values = tuple(current[field])
    successor_values = tuple(successor[field])
    return (
        len(successor_values) >= len(current_values)
        and successor_values[:len(current_values)] == current_values
    )


def _validate_recovery_journal_successor(current, successor):
    identity_fields = (
        "schema",
        "transaction_id",
        "idempotency_key",
        "targets",
        "created_at",
    )
    try:
        if any(current[field] != successor[field] for field in identity_fields):
            raise ValueError("journal identity changed")
        validate_journal_phase_transition(
            current["phase"],
            successor["phase"],
            recovery=current["phase"] == "recovery-required",
        )
        manifest_changed = (
            current["recovery_manifest_sha256"]
            != successor["recovery_manifest_sha256"]
        )
        manifest_binding_transition = (
            current["phase"] == "staged"
            and successor["phase"] == "prepared"
            and current["recovery_manifest_sha256"] == "absent"
            and successor["recovery_manifest_sha256"] != "absent"
        )
        if manifest_changed and not manifest_binding_transition:
            raise ValueError("journal manifest changed")
        if not _journal_progress_is_monotonic(
            current,
            successor,
            "applied_target_indexes",
        ) or not _journal_progress_is_monotonic(
            current,
            successor,
            "rollback_target_indexes",
        ):
            raise ValueError("journal progress regressed")
    except (KeyError, TypeError, ValueError, LifecycleJournalError):
        raise LifecycleRecoveryReadError(
            "RECOVERY_JOURNAL_NEXT_CONFLICT"
        ) from None


def _load_recovered_journal_state(transaction_id, control, workspace):
    current = _load_exact_recovery_journal(
        control.journal,
        transaction_id,
        "RECOVERY_JOURNAL_INVALID",
    )
    successor = _load_exact_recovery_journal(
        control.journal_next,
        transaction_id,
        "RECOVERY_JOURNAL_NEXT_INVALID",
    )
    if current is None:
        if successor is None:
            raise LifecycleRecoveryReadError("RECOVERY_JOURNAL_MISSING")
        if successor["phase"] != "planned":
            raise LifecycleRecoveryReadError(
                "RECOVERY_JOURNAL_NEXT_CONFLICT"
            )
        return _RecoveredJournalState(
            transaction_id=transaction_id,
            journal=successor,
            journal_sha256="absent",
            journal_next=successor,
            journal_next_sha256=control.journal_next.sha256,
            authority="pre-journal-orphan",
            _control_snapshot=control,
            _workspace=workspace,
        )
    if successor is not None:
        _validate_recovery_journal_successor(current, successor)
    return _RecoveredJournalState(
        transaction_id=transaction_id,
        journal=current,
        journal_sha256=control.journal.sha256,
        journal_next=successor,
        journal_next_sha256=(
            control.journal_next.sha256
            if successor is not None
            else "absent"
        ),
        authority="current",
        _control_snapshot=control,
        _workspace=workspace,
    )


@contextmanager
def _private_recovered_journal_workspace(canonical_root, transaction_id):
    discovered = transaction_storage.discover_recovery_workspaces(
        canonical_root,
        transaction_id,
    )
    if discovered != (transaction_id,):
        raise LifecycleRecoveryReadError("RECOVERY_JOURNAL_MISSING")
    with transaction_storage.reopen_transaction_workspace(
        canonical_root,
        transaction_id,
    ) as workspace:
        control = transaction_storage.read_recovery_control_snapshot(workspace)
        yield _load_recovered_journal_state(
            transaction_id,
            control,
            workspace,
        )


def _recovery_targets_from_journal(journal):
    try:
        return tuple(
            transaction_storage.RecoveryTarget(
                index=index,
                role=target["role"],
                relative_path=target["relative_path"],
                existed=target["existed"],
                before_sha256=target["before_sha256"],
                after_sha256=target["after_sha256"],
                after_size=target["after_bytes"],
                changed=target["changed"],
            )
            for index, target in enumerate(journal["targets"])
        )
    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
        transaction_storage.LifecycleRecoveryStorageError,
    ):
        raise LifecycleRecoveryReadError(
            "RECOVERY_JOURNAL_INVALID"
        ) from None


@contextmanager
def _private_recovered_transaction_workspace(canonical_root, transaction_id):
    with _private_recovered_journal_workspace(
        canonical_root,
        transaction_id,
    ) as journal_state:
        expected_manifest = journal_state.journal[
            "recovery_manifest_sha256"
        ]
        recovery_targets = _recovery_targets_from_journal(
            journal_state.journal
        )
        if expected_manifest == "absent":
            transaction_storage.verify_unbound_recovery_inventory(
                journal_state._workspace,
                recovery_targets,
                journal_state._control_snapshot,
            )
            yield _RecoveredTransactionState(
                journal_state=journal_state,
                storage_targets=(),
                preimages=(),
                staged_proposals=(),
                recovery_manifest=None,
                _workspace=journal_state._workspace,
            )
            return
        materials = transaction_storage.load_recovery_materials(
            journal_state._workspace,
            recovery_targets,
            journal_state._control_snapshot.recovery_manifest,
            expected_manifest,
        )
        yield _RecoveredTransactionState(
            journal_state=journal_state,
            storage_targets=materials.storage_targets,
            preimages=materials.preimages,
            staged_proposals=materials.staged_proposals,
            recovery_manifest=materials.recovery_manifest,
            _workspace=journal_state._workspace,
        )


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


def serialize_transaction_evidence(result: dict) -> dict:
    """Return detached redacted evidence from one strict result candidate."""
    serialized = serialize_transaction_result(result)
    targets = serialized["targets"]
    if (
        not targets
        or targets[-1]["role"] != "evidence"
        or any(target["role"] == "evidence" for target in targets[:-1])
    ):
        raise ValueError("Transaction evidence target layout invalid")
    return {
        "schema": EVIDENCE_SCHEMA,
        **{
            field: serialized[field]
            for field in _EVIDENCE_RESULT_FIELDS
        },
        "targets": targets[:-1],
        "projected_validation": serialized["projected_validation"],
        "post_apply_validation": serialized["post_apply_validation"],
    }


def render_transaction_evidence(result: dict) -> bytes:
    """Return deterministic UTF-8 evidence JSON with one trailing newline."""
    evidence = serialize_transaction_evidence(result)
    return (
        json.dumps(
            evidence,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ).encode("utf-8")
        + b"\n"
    )


def _completed_replay_result(plan, intent):
    """Return strict noop for one exact completed transaction, or None."""
    if not isinstance(plan, LifecycleTransactionPlan):
        raise TypeError("plan must be a LifecycleTransactionPlan")
    normalized = normalize_lifecycle_intent(intent)
    try:
        evidence_target = plan.targets[-1]
        if evidence_target.role != "evidence":
            raise ValueError("evidence target")
        if not evidence_target.existed:
            return None
        if (
            evidence_target.before_sha256
            != target_sha256(evidence_target._before_bytes)
        ):
            raise ValueError("evidence hash")
        evidence = json.loads(evidence_target._before_bytes.decode("utf-8"))
        _assert_exact_keys(
            evidence,
            _COMPLETED_EVIDENCE_KEYS,
            "completed transaction evidence",
        )
        if (
            evidence["schema"] != EVIDENCE_SCHEMA
            or evidence["status"] != "applied"
            or evidence["failed_stage"]
            or evidence["error_code"]
            or evidence["rollback_status"] != "not-required"
        ):
            raise ValueError("evidence state")
        expected_identity = {
            "transaction_id": plan.transaction_id,
            "idempotency_key": plan.idempotency_key,
            "project_id": plan.project_id,
            "issue_id": plan.issue_id,
            "action": plan.action,
            "target_lifecycle": plan.target_lifecycle,
            "source_event": normalized.source_event,
        }
        if any(
            evidence[key] != value
            for key, value in expected_identity.items()
        ):
            raise ValueError("evidence identity")
        ordinary = evidence["targets"]
        if (
            not isinstance(ordinary, list)
            or len(ordinary) != len(plan.targets) - 1
        ):
            raise ValueError("target count")
        serialized_ordinary = _serialized_targets(ordinary)
        for planned, recorded in zip(
            plan.targets[:-1],
            serialized_ordinary,
        ):
            expected_layout = (
                planned.role == recorded["role"]
                and planned.relative_path == recorded["relative_path"]
                and planned.validation_rules
                == tuple(recorded["validation_rules"])
                and planned.apply_order == recorded["apply_order"]
                and planned.rollback_order == recorded["rollback_order"]
                and recorded["existed"]
                == (recorded["before_sha256"] != "absent")
                and recorded["changed"]
                == (
                    not recorded["existed"]
                    or recorded["before_sha256"]
                    != recorded["after_sha256"]
                )
            )
            if not expected_layout:
                raise ValueError("target layout")
            if (
                not planned.existed
                or planned.before_sha256 != recorded["after_sha256"]
            ):
                raise LifecycleReplayConflict(
                    "REPLAY_CANONICAL_DRIFT"
                )
        projected = _serialized_validation_summary(
            evidence["projected_validation"]
        )
        post_apply = _serialized_validation_summary(
            evidence["post_apply_validation"]
        )
        if (
            not projected["valid"]
            or projected.get("rule_ids")
            != list(_PROJECTED_VALIDATION_RULE_IDS)
            or projected.get("error_codes") != []
            or not post_apply["valid"]
            or post_apply.get("rule_ids")
            != list(_POST_APPLY_VALIDATION_RULE_IDS)
            or post_apply.get("error_codes") != []
            or evidence["verified_target_count"] != len(plan.targets)
        ):
            raise ValueError("completion proof")
        evidence_sha256 = target_sha256(evidence_target._before_bytes)
        self_target = {
            "role": "evidence",
            "relative_path": evidence_target.relative_path,
            "existed": True,
            "before_sha256": evidence_sha256,
            "after_sha256": evidence_sha256,
            "after_bytes": len(evidence_target._before_bytes),
            "changed": False,
            "validation_rules": list(evidence_target.validation_rules),
            "apply_order": evidence_target.apply_order,
            "rollback_order": evidence_target.rollback_order,
        }
        return serialize_transaction_result({
            "schema": RESULT_SCHEMA,
            "transaction_id": evidence["transaction_id"],
            "idempotency_key": evidence["idempotency_key"],
            "status": "noop",
            "project_id": evidence["project_id"],
            "canonical_root": plan.canonical_root,
            "issue_id": evidence["issue_id"],
            "action": evidence["action"],
            "target_lifecycle": evidence["target_lifecycle"],
            "targets": serialized_ordinary + [self_target],
            "projected_validation": projected,
            "post_apply_validation": post_apply,
            "failed_stage": "",
            "error_code": "",
            "rollback_status": "not-required",
            "verified_target_count": evidence["verified_target_count"],
            "next_command": evidence["next_command"],
            "actor": evidence["actor"],
            "source_event": evidence["source_event"],
            "created_at": evidence["created_at"],
            "started_at": evidence["started_at"],
            "completed_at": evidence["completed_at"],
        })
    except LifecycleReplayConflict:
        raise
    except (
        AttributeError,
        IndexError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeError,
    ):
        raise LifecycleReplayConflict(
            "REPLAY_EVIDENCE_CONFLICT"
        ) from None


def _emit_apply_fault(fault_injector, stage):
    if stage not in _APPLY_FAULT_STAGES:
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
    if fault_injector is None:
        return
    if not callable(fault_injector):
        raise TypeError("fault_injector must be callable or None")
    fault_injector(stage)


def _public_failure_summary(rule_ids, error_code):
    return _serialized_validation_summary({
        "valid": False,
        "rule_ids": list(rule_ids),
        "error_codes": [error_code],
    })


def _public_failure_result(
    plan,
    intent,
    *,
    status,
    failed_stage,
    error_code,
    rollback_status,
    completed_at,
    projected_validation,
    post_apply_validation,
    verified_target_count=0,
    targets=None,
):
    if not isinstance(plan, LifecycleTransactionPlan):
        raise TypeError("plan must be a LifecycleTransactionPlan")
    normalized = normalize_lifecycle_intent(intent)
    if (
        status not in {
            "denied",
            "conflict",
            "rolled_back",
            "recovery_required",
        }
        or failed_stage not in _PUBLIC_FAILED_STAGES
        or rollback_status not in _PUBLIC_ROLLBACK_STATUSES
        or not isinstance(error_code, str)
        or not _ROLLBACK_ERROR_CODE.fullmatch(error_code)
    ):
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
    return serialize_transaction_result({
        "schema": RESULT_SCHEMA,
        "transaction_id": plan.transaction_id,
        "idempotency_key": plan.idempotency_key,
        "status": status,
        "project_id": plan.project_id,
        "canonical_root": plan.canonical_root,
        "issue_id": plan.issue_id,
        "action": plan.action,
        "target_lifecycle": plan.target_lifecycle,
        "targets": (
            [target.to_public_dict() for target in plan.targets]
            if targets is None
            else _serialized_targets(targets)
        ),
        "projected_validation": projected_validation,
        "post_apply_validation": post_apply_validation,
        "failed_stage": failed_stage,
        "error_code": error_code,
        "rollback_status": rollback_status,
        "verified_target_count": verified_target_count,
        "next_command": _planned_next_command(plan),
        "actor": normalized.actor,
        "source_event": normalized.source_event,
        "created_at": completed_at,
        "started_at": "",
        "completed_at": completed_at,
    })


def _public_failure_stage(error_code):
    if not isinstance(error_code, str):
        raise LifecycleJournalError("JOURNAL_RECORD_INVALID")
    if error_code.startswith("POST_APPLY_"):
        return "post-apply-validation"
    if error_code.startswith("FINALIZATION_"):
        return "finalizing"
    if error_code.startswith("CANONICAL_"):
        return "preflight"
    if error_code.startswith("LOCK_"):
        return "lock"
    if error_code.startswith("STORAGE_"):
        return "apply"
    if error_code.startswith("JOURNAL_"):
        return "apply"
    raise LifecycleJournalError("JOURNAL_RECORD_INVALID")


def _planned_next_command(plan):
    try:
        if not isinstance(plan, LifecycleTransactionPlan):
            raise TypeError("plan")
        selected = {}
        for role in ("state", "loop"):
            targets = tuple(
                target for target in plan.targets if target.role == role
            )
            if len(targets) != 1:
                raise ValueError("target layout")
            payload = json.loads(targets[0]._after_bytes.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("target payload")
            value = payload.get("next_command")
            if not isinstance(value, str) or not value.strip():
                raise ValueError("next command")
            selected[role] = value.strip()
        if selected["state"] != selected["loop"]:
            raise ValueError("next command mismatch")
        return selected["state"]
    except LifecycleFinalizationError:
        raise
    except (AttributeError, TypeError, ValueError, UnicodeError):
        raise LifecycleFinalizationError(
            "FINALIZATION_INPUT_INVALID"
        ) from None


def _prepare_completion_input(
    plan,
    intent,
    next_command,
    projected_validation,
):
    try:
        if not isinstance(plan, LifecycleTransactionPlan):
            raise TypeError("plan")
        normalized = normalize_lifecycle_intent(intent)
        context = _json_value(plan._project_context)
        resolved_next = str(next_command or "").strip()
        summary = _frozen_validation_summary(projected_validation)
        matches = (
            summary["valid"]
            and summary["rule_ids"] == _PROJECTED_VALIDATION_RULE_IDS
            and summary["error_codes"] == ()
            and resolved_next == _planned_next_command(plan)
            and normalized.issue_id == plan.issue_id
            and normalized.action == plan.action
            and normalized.target_lifecycle == plan.target_lifecycle
            and derive_idempotency_key(context, normalized)
            == plan.idempotency_key
            and derive_transaction_id(context, normalized)
            == plan.transaction_id
        )
        if not matches:
            raise ValueError("mismatch")
    except (LifecycleFinalizationError, LifecycleJournalError):
        raise LifecycleFinalizationError(
            "FINALIZATION_INPUT_INVALID"
        ) from None
    except (AttributeError, TypeError, ValueError, UnicodeError):
        raise LifecycleFinalizationError(
            "FINALIZATION_INPUT_INVALID"
        ) from None
    return _PrivateCompletionInput(
        intent=normalized,
        next_command=resolved_next,
        projected_validation=summary,
    )


def _successful_post_apply_summary():
    return _frozen_validation_summary({
        "valid": True,
        "rule_ids": list(_POST_APPLY_VALIDATION_RULE_IDS),
        "error_codes": [],
    })


def _successful_result_candidate(plan, completion_input, timestamps, n):
    return {
        "schema": RESULT_SCHEMA,
        "transaction_id": plan.transaction_id,
        "idempotency_key": plan.idempotency_key,
        "status": "applied",
        "project_id": plan.project_id,
        "canonical_root": plan.canonical_root,
        "issue_id": plan.issue_id,
        "action": plan.action,
        "target_lifecycle": plan.target_lifecycle,
        "targets": [target.to_public_dict() for target in plan.targets],
        "projected_validation": _json_value(
            completion_input.projected_validation
        ),
        "post_apply_validation": _json_value(
            _successful_post_apply_summary()
        ),
        "failed_stage": "",
        "error_code": "",
        "rollback_status": "not-required",
        "verified_target_count": len(plan.targets),
        "next_command": completion_input.next_command,
        "actor": completion_input.intent.actor,
        "source_event": completion_input.intent.source_event,
        "created_at": timestamps[0],
        "started_at": timestamps[3],
        "completed_at": timestamps[7 + n],
    }


def _bind_success_evidence(plan, completion_input, timestamps):
    try:
        if (
            not isinstance(plan, LifecycleTransactionPlan)
            or not isinstance(completion_input, _PrivateCompletionInput)
        ):
            raise ValueError("input")
        completion_input = _prepare_completion_input(
            plan,
            completion_input.intent,
            completion_input.next_command,
            completion_input.projected_validation,
        )
        n = sum(
            target.changed and target.role != "evidence"
            for target in plan.targets
        )
        if not isinstance(timestamps, tuple) or len(timestamps) != 11 + 2 * n:
            raise ValueError("timestamps")
        for value in timestamps:
            _journal_timestamp(value)
        provisional = _successful_result_candidate(
            plan,
            completion_input,
            timestamps,
            n,
        )
        evidence_bytes = render_transaction_evidence(provisional)
        evidence = plan.targets[-1]
        rebound_evidence = replace(
            evidence,
            after_sha256=target_sha256(evidence_bytes),
            after_size=len(evidence_bytes),
            changed=(
                not evidence.existed
                or evidence._before_bytes != evidence_bytes
            ),
            _after_bytes=evidence_bytes,
        )
        if rebound_evidence.role != "evidence" or not rebound_evidence.changed:
            raise LifecycleFinalizationError(
                "FINALIZATION_EVIDENCE_ALREADY_PRESENT"
            )
        rebound_plan = replace(
            plan,
            targets=plan.targets[:-1] + (rebound_evidence,),
        )
        rebound_result = {
            **provisional,
            "targets": [
                target.to_public_dict()
                for target in rebound_plan.targets
            ],
        }
        serialized = serialize_transaction_result(rebound_result)
        if render_transaction_evidence(serialized) != evidence_bytes:
            raise ValueError("self-reference")
    except LifecycleFinalizationError:
        raise
    except (
        IndexError,
        KeyError,
        LifecycleJournalError,
        TypeError,
        ValueError,
    ):
        raise LifecycleFinalizationError(
            "FINALIZATION_INPUT_INVALID"
        ) from None
    return _PrivateEvidenceBinding(
        plan=rebound_plan,
        transaction_result=_freeze_json_value(serialized),
        evidence_bytes=evidence_bytes,
        completed_at=serialized["completed_at"],
    )


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
    expected_role_path = (root / role_path).resolve(strict=False)
    if configured_path.resolve(strict=False) != expected_role_path:
        raise LifecyclePlanError("PLAN_CONTEXT_INVALID", role=role)
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


def _missing_planning_source(role, relative_path, required):
    if required:
        raise LifecyclePlanError(
            "PLAN_TARGET_MISSING",
            role=role,
            relative_path=relative_path,
        )
    return False, b""


def _descriptor_open_error(
    exc,
    parent_fd,
    name,
    role,
    relative_path,
    required,
    *,
    expect_directory,
):
    if exc.errno == errno.ENOENT:
        return _missing_planning_source(role, relative_path, required)
    try:
        metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        metadata = None
    if metadata is not None and stat.S_ISLNK(metadata.st_mode):
        raise LifecyclePlanError(
            "PLAN_TARGET_SYMLINK",
            role=role,
            relative_path=relative_path,
        ) from exc
    if metadata is not None and (
        (expect_directory and not stat.S_ISDIR(metadata.st_mode))
        or (not expect_directory and not stat.S_ISREG(metadata.st_mode))
    ):
        raise LifecyclePlanError(
            "PLAN_TARGET_NOT_REGULAR",
            role=role,
            relative_path=relative_path,
        ) from exc
    raise LifecyclePlanError(
        "PLAN_TARGET_UNREADABLE",
        role=role,
        relative_path=relative_path,
    ) from exc


def _read_regular_file_no_follow(path, root, role, *, required):
    """Read one project-relative regular file through no-follow descriptors."""
    path = Path(path)
    try:
        relative_path = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise LifecyclePlanError("PLAN_PATH_ESCAPE", role=role) from exc

    parts = Path(relative_path).parts
    open_fds = []
    read_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_flags = read_flags | no_follow | getattr(os, "O_DIRECTORY", 0)
    try:
        try:
            parent_fd = os.open(root, directory_flags)
        except OSError as exc:
            raise LifecyclePlanError(
                "PLAN_TARGET_UNREADABLE",
                role=role,
                relative_path=relative_path,
            ) from exc
        open_fds.append(parent_fd)

        for part in parts[:-1]:
            try:
                child_fd = os.open(
                    part,
                    directory_flags,
                    dir_fd=parent_fd,
                )
            except OSError as exc:
                return _descriptor_open_error(
                    exc,
                    parent_fd,
                    part,
                    role,
                    relative_path,
                    required,
                    expect_directory=True,
                )
            open_fds.append(child_fd)
            parent_fd = child_fd

        try:
            file_fd = os.open(
                parts[-1],
                read_flags | no_follow,
                dir_fd=parent_fd,
            )
        except OSError as exc:
            return _descriptor_open_error(
                exc,
                parent_fd,
                parts[-1],
                role,
                relative_path,
                required,
                expect_directory=False,
            )
        open_fds.append(file_fd)

        try:
            metadata = os.fstat(file_fd)
        except OSError as exc:
            raise LifecyclePlanError(
                "PLAN_TARGET_UNREADABLE",
                role=role,
                relative_path=relative_path,
            ) from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise LifecyclePlanError(
                "PLAN_TARGET_NOT_REGULAR",
                role=role,
                relative_path=relative_path,
            )
        chunks = []
        while True:
            try:
                chunk = os.read(file_fd, 64 * 1024)
            except OSError as exc:
                raise LifecyclePlanError(
                    "PLAN_TARGET_UNREADABLE",
                    role=role,
                    relative_path=relative_path,
                ) from exc
            if not chunk:
                break
            chunks.append(chunk)
        return True, b"".join(chunks)
    finally:
        for descriptor in reversed(open_fds):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _read_planning_source(path, root, role, *, required):
    return _read_regular_file_no_follow(
        path,
        root,
        role,
        required=required,
    )


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
    issue_index_existed, issue_index_before = _read_planning_source(
        issue_index_path, root, "issue-index", required=False
    )
    if issue_index_existed or normalized.require_issue_index:
        existed, before = issue_index_existed, issue_index_before
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


def apply_lifecycle_transaction(
    project_root,
    intent: LifecycleIntent,
    *,
    project_context=None,
    clock=None,
    fault_injector=None,
):
    """Apply one lifecycle transaction or return its completed replay."""
    normalized = normalize_lifecycle_intent(intent)
    plan = plan_lifecycle_transaction(
        project_root,
        normalized,
        project_context=project_context,
        clock=clock,
    )
    _emit_apply_fault(fault_injector, "after-plan")
    projected = _public_failure_summary(
        _PROJECTED_VALIDATION_RULE_IDS,
        "PROJECTED_VALIDATION_NOT_RUN",
    )
    post_apply = _public_failure_summary(
        _POST_APPLY_VALIDATION_RULE_IDS,
        "POST_APPLY_VALIDATION_NOT_RUN",
    )
    try:
        _writable_projected_plan_context(plan)
    except project_operation.ProjectOperationDenied as exc:
        denial_code = exc.decision.get("reason_code")
        if (
            not isinstance(denial_code, str)
            or not _ROLLBACK_ERROR_CODE.fullmatch(denial_code)
        ):
            raise LifecycleJournalError(
                "JOURNAL_RECORD_INVALID"
            ) from None
        return _public_failure_result(
            plan,
            normalized,
            status="denied",
            failed_stage="authorization",
            error_code=denial_code,
            rollback_status="not-required",
            completed_at=_journal_timestamp(clock),
            projected_validation=projected,
            post_apply_validation=post_apply,
        )
    try:
        replay = _completed_replay_result(plan, normalized)
    except LifecycleReplayConflict as exc:
        return _public_failure_result(
            plan,
            normalized,
            status="conflict",
            failed_stage="replay",
            error_code=exc.code,
            rollback_status="not-required",
            completed_at=_journal_timestamp(clock),
            projected_validation=projected,
            post_apply_validation=post_apply,
        )
    _emit_apply_fault(fault_injector, "after-replay-classification")
    if replay is not None:
        return replay
    try:
        projected = validate_projected_transaction(plan)
    except LifecycleProjectedValidationError as exc:
        return _public_failure_result(
            plan,
            normalized,
            status="conflict",
            failed_stage="projected-validation",
            error_code=exc.code,
            rollback_status="not-required",
            completed_at=_journal_timestamp(clock),
            projected_validation=_public_failure_summary(
                _PROJECTED_VALIDATION_RULE_IDS,
                exc.code,
            ),
            post_apply_validation=post_apply,
        )
    if not projected["valid"]:
        return _public_failure_result(
            plan,
            normalized,
            status="conflict",
            failed_stage="projected-validation",
            error_code="PROJECTED_VALIDATION_INVALID",
            rollback_status="not-required",
            completed_at=_journal_timestamp(clock),
            projected_validation=projected,
            post_apply_validation=post_apply,
        )
    _emit_apply_fault(fault_injector, "after-projected-validation")
    completion = _prepare_completion_input(
        plan,
        normalized,
        _planned_next_command(plan),
        projected,
    )
    _emit_apply_fault(fault_injector, "before-private-apply")
    completed_result = None
    try:
        with _private_applied_workspace(
            plan,
            completion_input=completion,
            journal_clock=clock,
            lock_clock=clock,
        ) as completed:
            completed_result = serialize_transaction_result(
                _json_value(completed.transaction_result)
            )
            _emit_apply_fault(fault_injector, "after-private-complete")
            result = completed_result
    except transaction_storage.LifecycleCanonicalConflict as exc:
        return _public_failure_result(
            plan,
            normalized,
            status="conflict",
            failed_stage="preflight",
            error_code=exc.code,
            rollback_status="not-required",
            completed_at=_journal_timestamp(clock),
            projected_validation=projected,
            post_apply_validation=post_apply,
        )
    except LifecycleLockError as exc:
        status = (
            "conflict"
            if exc.code == "LOCK_HELD"
            else "recovery_required"
        )
        lock_projected = (
            completed_result["projected_validation"]
            if completed_result is not None
            else projected
        )
        lock_post_apply = (
            completed_result["post_apply_validation"]
            if completed_result is not None
            else post_apply
        )
        return _public_failure_result(
            plan,
            normalized,
            status=status,
            failed_stage="lock",
            error_code=exc.code,
            rollback_status=(
                "not-required"
                if status == "conflict"
                else "required"
            ),
            completed_at=_journal_timestamp(clock),
            projected_validation=lock_projected,
            post_apply_validation=lock_post_apply,
            verified_target_count=(
                completed_result["verified_target_count"]
                if completed_result is not None
                else 0
            ),
            targets=(
                completed_result["targets"]
                if completed_result is not None
                else None
            ),
        )
    except LifecycleApplyRolledBack as exc:
        post_summary = (
            _json_value(exc.post_apply_validation)
            if exc.post_apply_validation is not None
            else _public_failure_summary(
                _POST_APPLY_VALIDATION_RULE_IDS,
                exc.original_error_code,
            )
        )
        return _public_failure_result(
            plan,
            normalized,
            status="rolled_back",
            failed_stage=_public_failure_stage(
                exc.original_error_code
            ),
            error_code=exc.original_error_code,
            rollback_status="verified",
            completed_at=_journal_timestamp(clock),
            projected_validation=projected,
            post_apply_validation=post_summary,
            verified_target_count=len(plan.targets),
        )
    except LifecycleRecoveryRequired as exc:
        post_summary = (
            _json_value(exc.post_apply_validation)
            if exc.post_apply_validation is not None
            else _public_failure_summary(
                _POST_APPLY_VALIDATION_RULE_IDS,
                exc.original_error_code,
            )
        )
        return _public_failure_result(
            plan,
            normalized,
            status="recovery_required",
            failed_stage="rollback",
            error_code=exc.code,
            rollback_status="required",
            completed_at=_journal_timestamp(clock),
            projected_validation=projected,
            post_apply_validation=post_summary,
        )
    except transaction_storage.LifecycleStorageError as exc:
        return _public_failure_result(
            plan,
            normalized,
            status="recovery_required",
            failed_stage="recovery",
            error_code=exc.code,
            rollback_status="required",
            completed_at=_journal_timestamp(clock),
            projected_validation=projected,
            post_apply_validation=post_apply,
        )
    return result
