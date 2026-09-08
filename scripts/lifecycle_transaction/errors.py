"""Issue 103's exception types, and the code sets each one validates against.

Moved out of `project_lifecycle_transaction.py` on 2026-09-08 (issue 153).
**Nothing here changed** — this is the block that was lines 711-989, byte for
byte, plus this docstring and the imports it needs.

Why these first: measured over the module's 208 top-level symbols, the six most
referenced are all exceptions — `LifecycleProjectedValidationError` (46 call
sites), `LifecycleRecoveryStateError` (44), `LifecyclePlanError` (38),
`LifecycleRecoveryLockError` (37), `LifecycleJournalError` (31),
`LifecycleLockError` (30). They reference nothing else in the module, so moving
them carries no risk and pulls 226 references into one file.

`project_lifecycle_transaction` re-exports every name here, so no caller
changes.
"""
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


# 153: these five moved with the exceptions because the exceptions call them.
#
# I had claimed the exception classes "reference nothing else in the module".
# That was an inference, not the measurement — `LifecyclePostApplyValidationError`
# calls `_frozen_validation_summary`, which calls `_serialized_validation_summary`,
# which needs `_VALIDATION_SUMMARY_KEYS` and `_LOGICAL_NAME`. The chain closes
# here; nothing below reaches back into the parent module.
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_LOGICAL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_VALIDATION_SUMMARY_KEYS = frozenset({"valid", "rule_ids", "error_codes"})
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


class LifecycleProductionVersionConflict(RuntimeError):
    """Stable production-version classification failure without record data."""

    def __init__(self, code="PRODUCTION_VERSION_CONFLICT"):
        if code not in {
            "PRODUCTION_VERSION_CONFLICT",
            "PRODUCTION_VERSION_SCAN_UNSAFE",
        }:
            code = "PRODUCTION_VERSION_SCAN_UNSAFE"
        self.code = code
        super().__init__(code)


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


_RECOVERY_STATE_CODES = frozenset({
    "RECOVERY_STATE_AMBIGUOUS",
    "RECOVERY_STATE_CANONICAL_UNKNOWN",
    "RECOVERY_STATE_PROGRESS_INVALID",
    "RECOVERY_STATE_JOURNAL_PERSIST_FAILED",
})


class LifecycleRecoveryStateError(RuntimeError):
    """Stable recovery-state failure without canonical or private values."""

    def __init__(self, code):
        if code not in _RECOVERY_STATE_CODES:
            code = "RECOVERY_STATE_AMBIGUOUS"
        self.code = code
        super().__init__(code)


_RECOVERY_CLEANUP_CODES = frozenset({
    "RECOVERY_CLEANUP_INELIGIBLE",
    "RECOVERY_CLEANUP_CANONICAL_UNPROVEN",
    "RECOVERY_CLEANUP_INVENTORY_UNSAFE",
    "RECOVERY_CLEANUP_REPLACED",
    "RECOVERY_CLEANUP_DELETE_FAILED",
    "RECOVERY_CLEANUP_DURABILITY_UNCERTAIN",
    "RECOVERY_CLEANUP_REMAINDER_UNSAFE",
})


class LifecycleRecoveryCleanupError(RuntimeError):
    """Stable cleanup-proof failure without private inventory details."""

    def __init__(self, code):
        if code not in _RECOVERY_CLEANUP_CODES:
            code = "RECOVERY_CLEANUP_INELIGIBLE"
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
