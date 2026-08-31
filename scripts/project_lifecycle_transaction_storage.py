#!/usr/bin/env python3
"""Private durable storage primitives for Issue 103 lifecycle transactions."""

from contextlib import contextmanager
from dataclasses import dataclass, field
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import secrets
import stat


_LOGICAL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PREIMAGES_NAME = "preimages"
_RECOVERY_MANIFEST_NAME = "recovery-manifest.json"
_RECOVERY_MANIFEST_SCHEMA = "moduflow.lifecycle-transaction-recovery-manifest.v1"
_JOURNAL_NAME = "journal.json"
_JOURNAL_NEXT_NAME = "journal.next"
_LOCK_NAME = "lifecycle.lock"
_PREIMAGE_ENTRY = re.compile(r"^[0-9]{6}\.bin$")
_RECOVERY_STORAGE_CODES = frozenset({
    "RECOVERY_DISCOVERY_UNSAFE",
    "RECOVERY_WORKSPACE_UNSAFE",
    "RECOVERY_CONTROL_FILE_UNSAFE",
    "RECOVERY_MANIFEST_MISSING",
    "RECOVERY_MANIFEST_INVALID",
    "RECOVERY_MANIFEST_MISMATCH",
    "RECOVERY_PAYLOAD_MISSING",
    "RECOVERY_PAYLOAD_INVALID",
    "RECOVERY_PAYLOAD_MISMATCH",
})


class LifecycleStorageError(RuntimeError):
    """Stable private-storage failure without paths or payload values."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


class LifecycleCanonicalConflict(RuntimeError):
    """Stable canonical-preimage conflict without paths or payloads."""

    def __init__(self, target_index):
        if (
            not isinstance(target_index, int)
            or isinstance(target_index, bool)
            or target_index < 0
        ):
            _storage_context_failure()
        self.code = "CANONICAL_PREIMAGE_CONFLICT"
        self.target_index = target_index
        super().__init__(self.code)


class LifecycleRecoveryStorageError(RuntimeError):
    """Stable read-only recovery failure without paths or payload values."""

    def __init__(self, code):
        if code not in _RECOVERY_STORAGE_CODES:
            code = "RECOVERY_WORKSPACE_UNSAFE"
        self.code = code
        super().__init__(code)


def _storage_context_failure():
    raise LifecycleStorageError("STORAGE_CONTEXT_INVALID")


def _safe_relative_path(value):
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or value.startswith("/")
        or PureWindowsPath(value).is_absolute()
    ):
        return False
    parts = PurePosixPath(value).parts
    return (
        bool(parts)
        and parts[0] != ".git"
        and all(part not in {"", ".", ".."} for part in parts)
    )


@dataclass(frozen=True)
class StorageTarget:
    index: int
    role: str
    relative_path: str
    existed: bool
    before_sha256: str
    after_sha256: str
    after_size: int
    changed: bool
    _before_bytes: bytes = field(repr=False, compare=False)
    _after_bytes: bytes = field(repr=False, compare=False)

    def __post_init__(self):
        try:
            before_bytes = bytes(self._before_bytes)
            after_bytes = bytes(self._after_bytes)
        except (TypeError, ValueError) as exc:
            raise LifecycleStorageError("STORAGE_CONTEXT_INVALID") from exc
        valid_before = (
            isinstance(self.existed, bool)
            and (
                (
                    self.existed
                    and isinstance(self.before_sha256, str)
                    and _SHA256.fullmatch(self.before_sha256)
                    and hashlib.sha256(before_bytes).hexdigest()
                    == self.before_sha256
                )
                or (
                    not self.existed
                    and self.before_sha256 == "absent"
                    and before_bytes == b""
                )
            )
        )
        valid_after = (
            isinstance(self.after_sha256, str)
            and _SHA256.fullmatch(self.after_sha256)
            and hashlib.sha256(after_bytes).hexdigest() == self.after_sha256
            and isinstance(self.after_size, int)
            and not isinstance(self.after_size, bool)
            and self.after_size == len(after_bytes)
        )
        expected_changed = not self.existed or before_bytes != after_bytes
        if (
            not isinstance(self.index, int)
            or isinstance(self.index, bool)
            or self.index < 0
            or not isinstance(self.role, str)
            or not _LOGICAL_NAME.fullmatch(self.role)
            or not _safe_relative_path(self.relative_path)
            or not valid_before
            or not valid_after
            or not isinstance(self.changed, bool)
            or self.changed != expected_changed
        ):
            _storage_context_failure()
        object.__setattr__(self, "_before_bytes", before_bytes)
        object.__setattr__(self, "_after_bytes", after_bytes)


@dataclass(frozen=True)
class RecoveryTarget:
    index: int
    role: str
    relative_path: str
    existed: bool
    before_sha256: str
    after_sha256: str
    after_size: int
    changed: bool

    def __post_init__(self):
        expected_changed = (
            not self.existed or self.before_sha256 != self.after_sha256
        )
        valid_before = (
            isinstance(self.existed, bool)
            and (
                (
                    self.existed
                    and isinstance(self.before_sha256, str)
                    and _SHA256.fullmatch(self.before_sha256)
                )
                or (not self.existed and self.before_sha256 == "absent")
            )
        )
        if (
            not isinstance(self.index, int)
            or isinstance(self.index, bool)
            or self.index < 0
            or not isinstance(self.role, str)
            or not _LOGICAL_NAME.fullmatch(self.role)
            or not _safe_relative_path(self.relative_path)
            or not valid_before
            or not isinstance(self.after_sha256, str)
            or not _SHA256.fullmatch(self.after_sha256)
            or not isinstance(self.after_size, int)
            or isinstance(self.after_size, bool)
            or self.after_size < 0
            or not isinstance(self.changed, bool)
            or self.changed != expected_changed
        ):
            raise LifecycleRecoveryStorageError(
                "RECOVERY_MANIFEST_MISMATCH"
            )


@dataclass(frozen=True)
class _RecoveredBeforeTarget:
    index: int
    role: str
    relative_path: str
    existed: bool
    before_sha256: str
    after_sha256: str
    after_size: int
    changed: bool
    _before_bytes: bytes = field(repr=False, compare=False)


@dataclass(frozen=True)
class StoredPreimage:
    index: int
    state: str
    relative_name: str
    size: int
    sha256: str
    _device: int = field(repr=False, compare=False)
    _inode: int = field(repr=False, compare=False)


@dataclass(frozen=True)
class StagedProposal:
    index: int
    state: str
    relative_name: str
    size: int
    sha256: str
    _device: int = field(repr=False, compare=False)
    _inode: int = field(repr=False, compare=False)


@dataclass(frozen=True)
class RecoveryManifest:
    relative_name: str
    size: int
    sha256: str
    _device: int = field(repr=False, compare=False)
    _inode: int = field(repr=False, compare=False)


@dataclass(frozen=True)
class _RecoveredMaterials:
    storage_targets: tuple[StorageTarget, ...] = field(repr=False, compare=False)
    preimages: tuple[StoredPreimage, ...] = field(repr=False, compare=False)
    staged_proposals: tuple[StagedProposal | None, ...] = field(
        repr=False,
        compare=False,
    )
    recovery_manifest: RecoveryManifest = field(repr=False, compare=False)


@dataclass(frozen=True)
class _JournalState:
    state: str
    sha256: str
    _device: int = field(repr=False, compare=False)
    _inode: int = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivateTransactionWorkspace:
    transaction_id: str
    _root_fd: int = field(repr=False, compare=False)
    _transactions_fd: int = field(repr=False, compare=False)
    _workspace_fd: int = field(repr=False, compare=False)
    _preimages_fd: int = field(repr=False, compare=False)


@dataclass(frozen=True)
class _PrivateCleanupWorkspace:
    transaction_id: str
    _root_fd: int = field(repr=False, compare=False)
    _transactions_fd: int = field(repr=False, compare=False)
    _workspace_fd: int = field(repr=False, compare=False)
    _preimages_fd: int | None = field(repr=False, compare=False)


@dataclass(frozen=True)
class _RecoveryFileSnapshot:
    state: str
    size: int
    sha256: str
    _bytes: bytes = field(repr=False, compare=False)
    _device: int = field(repr=False, compare=False)
    _inode: int = field(repr=False, compare=False)


@dataclass(frozen=True)
class _RecoveryControlSnapshot:
    journal: _RecoveryFileSnapshot
    journal_next: _RecoveryFileSnapshot
    recovery_manifest: _RecoveryFileSnapshot
    _workspace_entries: tuple[str, ...] = field(repr=False, compare=False)
    _preimage_entries: tuple[str, ...] = field(repr=False, compare=False)


@dataclass(frozen=True)
class _RecoveryDirectorySnapshot:
    _device: int = field(repr=False, compare=False)
    _inode: int = field(repr=False, compare=False)
    _mode: int = field(repr=False, compare=False)


@dataclass(frozen=True)
class _RecoveryCleanupInventory:
    _workspace_directory: _RecoveryDirectorySnapshot = field(
        repr=False,
        compare=False,
    )
    _preimages_directory: _RecoveryDirectorySnapshot = field(
        repr=False,
        compare=False,
    )
    _control_snapshot: _RecoveryControlSnapshot = field(
        repr=False,
        compare=False,
    )
    _recovery_targets: tuple[RecoveryTarget, ...] = field(
        repr=False,
        compare=False,
    )
    _preimages: tuple[StoredPreimage, ...] = field(
        repr=False,
        compare=False,
    )
    _staged_proposals: tuple[StagedProposal | None, ...] = field(
        repr=False,
        compare=False,
    )
    _recovery_manifest: RecoveryManifest | None = field(
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class _CleanupResumeInventory:
    remainder_kind: str
    _workspace_directory: _RecoveryDirectorySnapshot = field(
        repr=False,
        compare=False,
    )
    _preimages_directory: _RecoveryDirectorySnapshot | None = field(
        repr=False,
        compare=False,
    )
    _control_snapshot: _RecoveryControlSnapshot = field(
        repr=False,
        compare=False,
    )
    _recovery_targets: tuple[RecoveryTarget, ...] = field(
        repr=False,
        compare=False,
    )


_ABSENT_RECOVERY_FILE = _RecoveryFileSnapshot(
    state="absent",
    size=0,
    sha256="absent",
    _bytes=b"",
    _device=-1,
    _inode=-1,
)


def _directory_flags():
    return (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )


def _close_descriptors(*descriptors):
    for descriptor in descriptors:
        if descriptor is None:
            continue
        try:
            os.close(descriptor)
        except OSError:
            pass


def _validate_workspace_input(canonical_root, transaction_id):
    try:
        root = Path(canonical_root)
    except (TypeError, ValueError) as exc:
        raise LifecycleStorageError("STORAGE_CONTEXT_INVALID") from exc
    if (
        not root.is_absolute()
        or not isinstance(transaction_id, str)
        or not _LOGICAL_NAME.fullmatch(transaction_id)
    ):
        _storage_context_failure()
    return root


@contextmanager
def private_transaction_workspace(canonical_root, transaction_id):
    """Yield one new descriptor-backed workspace and leave it durable."""
    root = _validate_workspace_input(canonical_root, transaction_id)
    root_fd = None
    control_fd = None
    transactions_fd = None
    workspace_fd = None
    preimages_fd = None
    flags = _directory_flags()
    try:
        try:
            root_fd = os.open(root, flags)
            control_fd = os.open(".moduflow", flags, dir_fd=root_fd)
            transactions_fd = os.open("transactions", flags, dir_fd=control_fd)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_PATH_UNSAFE") from exc
        try:
            os.mkdir(transaction_id, mode=0o700, dir_fd=transactions_fd)
        except FileExistsError as exc:
            raise LifecycleStorageError("STORAGE_CONFLICT") from exc
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_CREATE_FAILED") from exc
        try:
            workspace_fd = os.open(transaction_id, flags, dir_fd=transactions_fd)
            if not stat.S_ISDIR(os.fstat(workspace_fd).st_mode):
                raise OSError(errno.ENOTDIR, "workspace is not a directory")
            os.fchmod(workspace_fd, 0o700)
            os.fsync(transactions_fd)
            os.mkdir(_PREIMAGES_NAME, mode=0o700, dir_fd=workspace_fd)
            preimages_fd = os.open(_PREIMAGES_NAME, flags, dir_fd=workspace_fd)
            if not stat.S_ISDIR(os.fstat(preimages_fd).st_mode):
                raise OSError(errno.ENOTDIR, "preimages is not a directory")
            os.fchmod(preimages_fd, 0o700)
            os.fsync(workspace_fd)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        yield _PrivateTransactionWorkspace(
            transaction_id=transaction_id,
            _root_fd=root_fd,
            _transactions_fd=transactions_fd,
            _workspace_fd=workspace_fd,
            _preimages_fd=preimages_fd,
        )
    finally:
        _close_descriptors(
            preimages_fd,
            workspace_fd,
            transactions_fd,
            control_fd,
            root_fd,
        )


def _read_complete(descriptor, expected_size):
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks = []
    remaining = expected_size + 1
    while remaining:
        chunk = os.read(descriptor, min(64 * 1024, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recovery_root(canonical_root):
    try:
        root = Path(canonical_root)
    except (TypeError, ValueError) as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_DISCOVERY_UNSAFE"
        ) from exc
    if not root.is_absolute():
        raise LifecycleRecoveryStorageError("RECOVERY_DISCOVERY_UNSAFE")
    return root


def _open_recovery_transactions(canonical_root):
    root = _recovery_root(canonical_root)
    root_fd = None
    control_fd = None
    transactions_fd = None
    flags = _directory_flags()
    try:
        root_fd = os.open(root, flags)
        control_fd = os.open(".moduflow", flags, dir_fd=root_fd)
        transactions_fd = os.open("transactions", flags, dir_fd=control_fd)
        opened = os.fstat(transactions_fd)
        if not stat.S_ISDIR(opened.st_mode):
            raise OSError(errno.ENOTDIR, "transactions is not a directory")
        result = transactions_fd
        transactions_fd = None
        return result
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_DISCOVERY_UNSAFE"
        ) from exc
    finally:
        _close_descriptors(transactions_fd, control_fd, root_fd)


def _private_directory_metadata(metadata):
    return (
        stat.S_ISDIR(metadata.st_mode)
        and stat.S_IMODE(metadata.st_mode) == 0o700
    )


def _same_directory_metadata(first, second):
    return (
        _private_directory_metadata(first)
        and _private_directory_metadata(second)
        and first.st_dev == second.st_dev
        and first.st_ino == second.st_ino
    )


def _validate_lock_entry(transactions_fd):
    try:
        metadata = os.stat(
            _LOCK_NAME,
            dir_fd=transactions_fd,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_DISCOVERY_UNSAFE"
        ) from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or metadata.st_nlink != 1
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_DISCOVERY_UNSAFE")


def discover_recovery_workspaces(canonical_root, transaction_id=""):
    """Return deterministic existing transaction IDs without mutation."""
    if (
        not isinstance(transaction_id, str)
        or (transaction_id and not _LOGICAL_NAME.fullmatch(transaction_id))
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_DISCOVERY_UNSAFE")
    transactions_fd = _open_recovery_transactions(canonical_root)
    if transactions_fd is None:
        return ()
    try:
        try:
            entries = tuple(sorted(os.listdir(transactions_fd)))
        except OSError as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_DISCOVERY_UNSAFE"
            ) from exc
        identifiers = []
        for name in entries:
            if name == _LOCK_NAME:
                _validate_lock_entry(transactions_fd)
                continue
            if not _LOGICAL_NAME.fullmatch(name):
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_DISCOVERY_UNSAFE"
                )
            try:
                metadata = os.stat(
                    name,
                    dir_fd=transactions_fd,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_DISCOVERY_UNSAFE"
                ) from exc
            if not _private_directory_metadata(metadata):
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_DISCOVERY_UNSAFE"
                )
            identifiers.append(name)
        selected = tuple(identifiers)
        if transaction_id:
            return (transaction_id,) if transaction_id in selected else ()
        return selected
    finally:
        _close_descriptors(transactions_fd)


def _open_existing_private_directory(parent_fd, name):
    descriptor = None
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if not _private_directory_metadata(before):
            raise OSError(errno.ENOTDIR, "private directory is unsafe")
        descriptor = os.open(name, _directory_flags(), dir_fd=parent_fd)
        opened = os.fstat(descriptor)
        after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if (
            not _same_directory_metadata(before, opened)
            or not _same_directory_metadata(before, after)
        ):
            raise OSError(errno.EINVAL, "private directory changed")
        result = descriptor
        descriptor = None
        return result
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_WORKSPACE_UNSAFE"
        ) from exc
    finally:
        _close_descriptors(descriptor)


@contextmanager
def reopen_transaction_workspace(canonical_root, transaction_id):
    """Yield one existing descriptor-backed workspace without repair."""
    try:
        root = _validate_workspace_input(canonical_root, transaction_id)
    except LifecycleStorageError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_WORKSPACE_UNSAFE"
        ) from exc
    root_fd = None
    control_fd = None
    transactions_fd = None
    workspace_fd = None
    preimages_fd = None
    flags = _directory_flags()
    try:
        try:
            root_fd = os.open(root, flags)
            control_fd = os.open(".moduflow", flags, dir_fd=root_fd)
            transactions_fd = os.open("transactions", flags, dir_fd=control_fd)
        except OSError as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_WORKSPACE_UNSAFE"
            ) from exc
        workspace_fd = _open_existing_private_directory(
            transactions_fd,
            transaction_id,
        )
        preimages_fd = _open_existing_private_directory(
            workspace_fd,
            _PREIMAGES_NAME,
        )
        yield _PrivateTransactionWorkspace(
            transaction_id=transaction_id,
            _root_fd=root_fd,
            _transactions_fd=transactions_fd,
            _workspace_fd=workspace_fd,
            _preimages_fd=preimages_fd,
        )
    finally:
        _close_descriptors(
            preimages_fd,
            workspace_fd,
            transactions_fd,
            control_fd,
            root_fd,
        )


@contextmanager
def reopen_cleanup_workspace(canonical_root, transaction_id):
    """Yield one existing cleanup workspace while allowing removed preimages."""
    try:
        root = _validate_workspace_input(canonical_root, transaction_id)
    except LifecycleStorageError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_WORKSPACE_UNSAFE"
        ) from exc
    root_fd = None
    control_fd = None
    transactions_fd = None
    workspace_fd = None
    preimages_fd = None
    flags = _directory_flags()
    try:
        try:
            root_fd = os.open(root, flags)
            control_fd = os.open(".moduflow", flags, dir_fd=root_fd)
            transactions_fd = os.open("transactions", flags, dir_fd=control_fd)
        except OSError as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_WORKSPACE_UNSAFE"
            ) from exc
        workspace_fd = _open_existing_private_directory(
            transactions_fd,
            transaction_id,
        )
        try:
            preimages_fd = _open_existing_private_directory(
                workspace_fd,
                _PREIMAGES_NAME,
            )
        except LifecycleRecoveryStorageError as exc:
            try:
                os.stat(
                    _PREIMAGES_NAME,
                    dir_fd=workspace_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                preimages_fd = None
            except OSError as stat_error:
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_WORKSPACE_UNSAFE"
                ) from stat_error
            else:
                raise exc
        yield _PrivateCleanupWorkspace(
            transaction_id=transaction_id,
            _root_fd=root_fd,
            _transactions_fd=transactions_fd,
            _workspace_fd=workspace_fd,
            _preimages_fd=preimages_fd,
        )
    finally:
        _close_descriptors(
            preimages_fd,
            workspace_fd,
            transactions_fd,
            control_fd,
            root_fd,
        )


def _read_recovery_file(parent_fd, name):
    descriptor = None
    try:
        try:
            before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return _ABSENT_RECOVERY_FILE
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_nlink != 1
        ):
            raise OSError(errno.EINVAL, "recovery file is unsafe")
        descriptor = os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        opened = os.fstat(descriptor)
        payload = _read_complete(descriptor, before.st_size)
        after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        final_opened = os.fstat(descriptor)
        if (
            len(payload) != before.st_size
            or not _journal_metadata_matches(opened, before)
            or not _journal_metadata_matches(after, before)
            or not _journal_metadata_matches(final_opened, before)
        ):
            raise OSError(errno.EINVAL, "recovery file changed")
        return _RecoveryFileSnapshot(
            state="present",
            size=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            _bytes=payload,
            _device=before.st_dev,
            _inode=before.st_ino,
        )
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        ) from exc
    finally:
        _close_descriptors(descriptor)


def read_recovery_control_snapshot(workspace):
    """Read fixed control files and private inventories without writes."""
    if not isinstance(workspace, _PrivateTransactionWorkspace):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    try:
        workspace_entries = tuple(sorted(os.listdir(workspace._workspace_fd)))
        preimage_entries = tuple(sorted(os.listdir(workspace._preimages_fd)))
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        ) from exc
    allowed = {
        _PREIMAGES_NAME,
        _RECOVERY_MANIFEST_NAME,
        _JOURNAL_NAME,
        _JOURNAL_NEXT_NAME,
    }
    if any(name not in allowed for name in workspace_entries) or any(
        not _PREIMAGE_ENTRY.fullmatch(name) for name in preimage_entries
    ):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )
    try:
        preimages_entry = os.stat(
            _PREIMAGES_NAME,
            dir_fd=workspace._workspace_fd,
            follow_symlinks=False,
        )
        opened_preimages = os.fstat(workspace._preimages_fd)
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        ) from exc
    if not _same_directory_metadata(preimages_entry, opened_preimages):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )
    return _RecoveryControlSnapshot(
        journal=_read_recovery_file(workspace._workspace_fd, _JOURNAL_NAME),
        journal_next=_read_recovery_file(
            workspace._workspace_fd,
            _JOURNAL_NEXT_NAME,
        ),
        recovery_manifest=_read_recovery_file(
            workspace._workspace_fd,
            _RECOVERY_MANIFEST_NAME,
        ),
        _workspace_entries=workspace_entries,
        _preimage_entries=preimage_entries,
    )


def read_cleanup_control_snapshot(workspace):
    """Read one cleanup remainder without requiring a preimages directory."""
    if not isinstance(workspace, _PrivateCleanupWorkspace):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    try:
        workspace_entries = tuple(sorted(os.listdir(workspace._workspace_fd)))
        preimage_entries = (
            tuple(sorted(os.listdir(workspace._preimages_fd)))
            if workspace._preimages_fd is not None
            else ()
        )
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        ) from exc
    allowed = {
        _PREIMAGES_NAME,
        _RECOVERY_MANIFEST_NAME,
        _JOURNAL_NAME,
        _JOURNAL_NEXT_NAME,
    }
    if any(name not in allowed for name in workspace_entries) or any(
        not _PREIMAGE_ENTRY.fullmatch(name) for name in preimage_entries
    ):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )
    has_preimages = _PREIMAGES_NAME in workspace_entries
    if has_preimages != (workspace._preimages_fd is not None):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )
    if workspace._preimages_fd is not None:
        try:
            preimages_entry = os.stat(
                _PREIMAGES_NAME,
                dir_fd=workspace._workspace_fd,
                follow_symlinks=False,
            )
            opened_preimages = os.fstat(workspace._preimages_fd)
        except OSError as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_CONTROL_FILE_UNSAFE"
            ) from exc
        if not _same_directory_metadata(preimages_entry, opened_preimages):
            raise LifecycleRecoveryStorageError(
                "RECOVERY_CONTROL_FILE_UNSAFE"
            )
    return _RecoveryControlSnapshot(
        journal=_read_recovery_file(workspace._workspace_fd, _JOURNAL_NAME),
        journal_next=_read_recovery_file(
            workspace._workspace_fd,
            _JOURNAL_NEXT_NAME,
        ),
        recovery_manifest=_read_recovery_file(
            workspace._workspace_fd,
            _RECOVERY_MANIFEST_NAME,
        ),
        _workspace_entries=workspace_entries,
        _preimage_entries=preimage_entries,
    )


def _owned_regular_metadata(metadata, expected):
    return (
        stat.S_ISREG(metadata.st_mode)
        and metadata.st_nlink == 1
        and metadata.st_dev == expected.st_dev
        and metadata.st_ino == expected.st_ino
    )


def _cleanup_owned_regular(parent_fd, name, metadata, expected_bytes):
    descriptor = None
    read_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        current = os.stat(
            name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        if not _owned_regular_metadata(current, metadata):
            return False
        descriptor = os.open(name, read_flags, dir_fd=parent_fd)
        opened = os.fstat(descriptor)
        if not _owned_regular_metadata(opened, metadata):
            return False
        stored = _read_complete(descriptor, len(expected_bytes))
        if not secrets.compare_digest(stored, expected_bytes):
            return False
        current = os.stat(
            name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        if not _owned_regular_metadata(current, metadata):
            return False
        os.unlink(name, dir_fd=parent_fd)
        return True
    except OSError:
        return False
    finally:
        _close_descriptors(descriptor)


def _cleanup_owned_preimage(workspace, name, metadata, expected_bytes):
    return _cleanup_owned_regular(
        workspace._preimages_fd,
        name,
        metadata,
        expected_bytes,
    )


def _write_preimage(workspace, target):
    name = f"{target.index:06d}.bin"
    flags = (
        os.O_CREAT
        | os.O_EXCL
        | os.O_RDWR
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = None
    metadata = None
    written = 0
    try:
        try:
            descriptor = os.open(
                name,
                flags,
                mode=0o600,
                dir_fd=workspace._preimages_fd,
            )
        except FileExistsError as exc:
            raise LifecycleStorageError("STORAGE_CONFLICT") from exc
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_CREATE_FAILED") from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise OSError(errno.EINVAL, "preimage is not privately owned")
            os.fchmod(descriptor, 0o600)
        except OSError as exc:
            if metadata is None or not _cleanup_owned_preimage(
                workspace,
                name,
                metadata,
                b"",
            ):
                raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
            raise LifecycleStorageError("STORAGE_CREATE_FAILED") from exc
        try:
            while written < len(target._before_bytes):
                count = os.write(descriptor, target._before_bytes[written:])
                if count <= 0 or count > len(target._before_bytes) - written:
                    raise OSError(errno.EIO, "preimage write failed")
                written += count
        except OSError as exc:
            if not _cleanup_owned_preimage(
                workspace,
                name,
                metadata,
                target._before_bytes[:written],
            ):
                raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
            raise LifecycleStorageError("STORAGE_WRITE_FAILED") from exc
        try:
            stored = _read_complete(descriptor, len(target._before_bytes))
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED") from exc
        if (
            len(stored) != len(target._before_bytes)
            or hashlib.sha256(stored).hexdigest() != target.before_sha256
            or not secrets.compare_digest(stored, target._before_bytes)
        ):
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED")
        try:
            os.fsync(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        return StoredPreimage(
            index=target.index,
            state="present",
            relative_name=f"preimages/{name}",
            size=len(stored),
            sha256=target.before_sha256,
            _device=metadata.st_dev,
            _inode=metadata.st_ino,
        )
    finally:
        _close_descriptors(descriptor)


def _validated_storage_targets(storage_targets):
    if (
        not isinstance(storage_targets, tuple)
        or not storage_targets
        or not all(
            isinstance(target, StorageTarget) for target in storage_targets
        )
        or [target.index for target in storage_targets]
        != list(range(len(storage_targets)))
    ):
        _storage_context_failure()
    return storage_targets


def _canonical_conflict(target):
    raise LifecycleCanonicalConflict(target.index) from None


def _same_regular_entry(metadata, expected, expected_size):
    return (
        stat.S_ISREG(metadata.st_mode)
        and metadata.st_dev == expected.st_dev
        and metadata.st_ino == expected.st_ino
        and metadata.st_size == expected_size
    )


def _read_bounded_canonical(descriptor, expected_size):
    chunks = []
    remaining = expected_size + 1
    while remaining:
        chunk = os.read(descriptor, min(64 * 1024, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _open_canonical_parent(root_fd, target):
    parent_fd = os.dup(root_fd)
    try:
        for component in PurePosixPath(target.relative_path).parts[:-1]:
            next_fd = os.open(component, _directory_flags(), dir_fd=parent_fd)
            _close_descriptors(parent_fd)
            parent_fd = next_fd
        metadata = os.fstat(parent_fd)
        if not stat.S_ISDIR(metadata.st_mode):
            raise OSError(errno.ENOTDIR, "canonical parent is not a directory")
        return parent_fd
    except OSError:
        _close_descriptors(parent_fd)
        raise


def _verify_canonical_entry(
    parent_fd,
    target,
    *,
    existed,
    expected_bytes,
    expected_sha256,
    expected_mode=None,
    failure,
):
    descriptor = None
    name = PurePosixPath(target.relative_path).name
    try:
        try:
            initial = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            if existed:
                failure()
            return target.index
        except OSError:
            failure()

        if not existed or not stat.S_ISREG(initial.st_mode):
            failure()
        read_flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(name, read_flags, dir_fd=parent_fd)
            opened = os.fstat(descriptor)
            if not _same_regular_entry(
                opened,
                initial,
                len(expected_bytes),
            ):
                failure()
            current_bytes = _read_bounded_canonical(
                descriptor,
                len(expected_bytes),
            )
            final = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except (LifecycleCanonicalConflict, LifecycleStorageError):
            raise
        except OSError:
            failure()
        if (
            not _same_regular_entry(
                final,
                opened,
                len(expected_bytes),
            )
            or len(current_bytes) != len(expected_bytes)
            or hashlib.sha256(current_bytes).hexdigest() != expected_sha256
            or not secrets.compare_digest(current_bytes, expected_bytes)
            or (
                expected_mode is not None
                and (
                    stat.S_IMODE(initial.st_mode) != expected_mode
                    or stat.S_IMODE(opened.st_mode) != expected_mode
                    or stat.S_IMODE(final.st_mode) != expected_mode
                    or initial.st_nlink != 1
                    or opened.st_nlink != 1
                    or final.st_nlink != 1
                )
            )
        ):
            failure()
        return target.index
    finally:
        _close_descriptors(descriptor)


def _verify_canonical_preimage(root_fd, target):
    parent_fd = None
    try:
        parent_fd = _open_canonical_parent(root_fd, target)
        return _verify_canonical_entry(
            parent_fd,
            target,
            existed=target.existed,
            expected_bytes=target._before_bytes,
            expected_sha256=target.before_sha256,
            failure=lambda: _canonical_conflict(target),
        )
    except LifecycleCanonicalConflict:
        raise
    except OSError:
        _canonical_conflict(target)
    finally:
        _close_descriptors(parent_fd)


def verify_canonical_preimages(canonical_root, storage_targets) -> tuple[int, ...]:
    """Return ordered indexes whose current canonical state matches exactly."""
    try:
        root = Path(canonical_root)
    except (TypeError, ValueError) as exc:
        raise LifecycleStorageError("STORAGE_CONTEXT_INVALID") from exc
    targets = _validated_storage_targets(storage_targets)
    if not root.is_absolute():
        _storage_context_failure()

    root_fd = None
    try:
        try:
            root_fd = os.open(root, _directory_flags())
        except OSError:
            _canonical_conflict(targets[0])
        return tuple(
            _verify_canonical_preimage(root_fd, target)
            for target in targets
        )
    finally:
        _close_descriptors(root_fd)


def store_preimages(workspace, storage_targets):
    """Durably store exact originals and return detached recovery records."""
    if not isinstance(workspace, _PrivateTransactionWorkspace):
        _storage_context_failure()
    targets = _validated_storage_targets(storage_targets)
    records = []
    for target in targets:
        if not target.existed:
            records.append(
                StoredPreimage(
                    index=target.index,
                    state="absent",
                    relative_name="absent",
                    size=0,
                    sha256="absent",
                    _device=-1,
                    _inode=-1,
                )
            )
            continue
        records.append(_write_preimage(workspace, target))
    try:
        os.fsync(workspace._preimages_fd)
    except OSError as exc:
        raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
    return tuple(records)


def _open_target_parent(workspace, target):
    parent_fd = None
    try:
        parent_fd = os.dup(workspace._root_fd)
        for component in PurePosixPath(target.relative_path).parts[:-1]:
            next_fd = os.open(component, _directory_flags(), dir_fd=parent_fd)
            _close_descriptors(parent_fd)
            parent_fd = next_fd
        metadata = os.fstat(parent_fd)
        if not stat.S_ISDIR(metadata.st_mode):
            raise OSError(errno.ENOTDIR, "target parent is not a directory")
        return parent_fd, metadata
    except OSError as exc:
        _close_descriptors(parent_fd)
        raise LifecycleStorageError("STORAGE_PATH_UNSAFE") from exc


def _staging_names(workspace, target):
    digest = hashlib.sha256(workspace.transaction_id.encode("utf-8")).hexdigest()
    basename = f".moduflow-stage-{digest}-{target.index:06d}"
    parent = PurePosixPath(target.relative_path).parent
    relative_name = (
        basename
        if parent == PurePosixPath(".")
        else (parent / basename).as_posix()
    )
    return basename, relative_name


def _write_staged_proposal(workspace, target):
    parent_fd = None
    descriptor = None
    metadata = None
    written = 0
    name, relative_name = _staging_names(workspace, target)
    flags = (
        os.O_CREAT
        | os.O_EXCL
        | os.O_RDWR
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        parent_fd, parent_metadata = _open_target_parent(workspace, target)
        try:
            descriptor = os.open(name, flags, mode=0o600, dir_fd=parent_fd)
        except FileExistsError as exc:
            raise LifecycleStorageError("STORAGE_CONFLICT") from exc
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_CREATE_FAILED") from exc
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or metadata.st_dev != parent_metadata.st_dev
            ):
                raise OSError(errno.EINVAL, "stage is not privately owned")
            os.fchmod(descriptor, 0o600)
        except OSError as exc:
            if metadata is None or not _cleanup_owned_regular(
                parent_fd,
                name,
                metadata,
                b"",
            ):
                raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
            raise LifecycleStorageError("STORAGE_CREATE_FAILED") from exc
        try:
            while written < len(target._after_bytes):
                count = os.write(descriptor, target._after_bytes[written:])
                if count <= 0 or count > len(target._after_bytes) - written:
                    raise OSError(errno.EIO, "stage write failed")
                written += count
        except OSError as exc:
            if not _cleanup_owned_regular(
                parent_fd,
                name,
                metadata,
                target._after_bytes[:written],
            ):
                raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
            raise LifecycleStorageError("STORAGE_WRITE_FAILED") from exc
        try:
            stored = _read_complete(descriptor, target.after_size)
            opened = os.fstat(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED") from exc
        if (
            len(stored) != target.after_size
            or hashlib.sha256(stored).hexdigest() != target.after_sha256
            or not secrets.compare_digest(stored, target._after_bytes)
        ):
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED")
        if not _owned_regular_metadata(opened, metadata):
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH")
        try:
            os.fsync(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        try:
            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
        if (
            not _owned_regular_metadata(current, metadata)
            or stat.S_IMODE(current.st_mode) != 0o600
        ):
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH")
        try:
            os.fsync(parent_fd)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        return StagedProposal(
            index=target.index,
            state="staged",
            relative_name=relative_name,
            size=len(stored),
            sha256=target.after_sha256,
            _device=metadata.st_dev,
            _inode=metadata.st_ino,
        )
    finally:
        _close_descriptors(descriptor, parent_fd)


def stage_proposed_targets(workspace, storage_targets):
    """Return immutable verified same-filesystem staging records."""
    if not isinstance(workspace, _PrivateTransactionWorkspace):
        _storage_context_failure()
    targets = _validated_storage_targets(storage_targets)
    records = []
    for target in targets:
        if not target.changed:
            records.append(
                StagedProposal(
                    index=target.index,
                    state="unchanged",
                    relative_name="unchanged",
                    size=0,
                    sha256="unchanged",
                    _device=-1,
                    _inode=-1,
                )
            )
            continue
        records.append(_write_staged_proposal(workspace, target))
    return tuple(records)


def _validated_recovery_records(storage_targets, preimages, staged_proposals):
    targets = _validated_storage_targets(storage_targets)
    if (
        not isinstance(preimages, tuple)
        or not isinstance(staged_proposals, tuple)
        or len(preimages) != len(targets)
        or len(staged_proposals) != len(targets)
        or not all(isinstance(record, StoredPreimage) for record in preimages)
        or not all(
            isinstance(record, StagedProposal) for record in staged_proposals
        )
    ):
        _storage_context_failure()
    for target, preimage, proposal in zip(
        targets,
        preimages,
        staged_proposals,
    ):
        if preimage.index != target.index or proposal.index != target.index:
            _storage_context_failure()
        if target.existed:
            if (
                preimage.state != "present"
                or preimage.relative_name != f"preimages/{target.index:06d}.bin"
                or preimage.size != len(target._before_bytes)
                or preimage.sha256 != target.before_sha256
                or preimage._device < 0
                or preimage._inode < 0
            ):
                _storage_context_failure()
        elif (
            preimage.state != "absent"
            or preimage.relative_name != "absent"
            or preimage.size != 0
            or preimage.sha256 != "absent"
            or preimage._device != -1
            or preimage._inode != -1
        ):
            _storage_context_failure()
        if target.changed:
            if (
                proposal.state != "staged"
                or proposal.size != target.after_size
                or proposal.sha256 != target.after_sha256
                or proposal._device < 0
                or proposal._inode < 0
            ):
                _storage_context_failure()
        elif (
            proposal.state != "unchanged"
            or proposal.relative_name != "unchanged"
            or proposal.size != 0
            or proposal.sha256 != "unchanged"
            or proposal._device != -1
            or proposal._inode != -1
        ):
            _storage_context_failure()
    return targets, preimages, staged_proposals


def _verify_recorded_file(
    parent_fd,
    name,
    *,
    expected_device,
    expected_inode,
    expected_bytes,
    expected_sha256,
):
    descriptor = None
    read_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        try:
            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            descriptor = os.open(name, read_flags, dir_fd=parent_fd)
            opened = os.fstat(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc

        def matches_record(metadata):
            return (
                stat.S_ISREG(metadata.st_mode)
                and stat.S_IMODE(metadata.st_mode) == 0o600
                and metadata.st_nlink == 1
                and metadata.st_dev == expected_device
                and metadata.st_ino == expected_inode
            )

        if not matches_record(current) or not matches_record(opened):
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH")
        try:
            stored = _read_complete(descriptor, len(expected_bytes))
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED") from exc
        if (
            len(stored) != len(expected_bytes)
            or hashlib.sha256(stored).hexdigest() != expected_sha256
            or not secrets.compare_digest(stored, expected_bytes)
        ):
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED")
        try:
            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            opened = os.fstat(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
        if not matches_record(current) or not matches_record(opened):
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH")
    finally:
        _close_descriptors(descriptor)


def _target_has_expected_role(target, *, evidence):
    return (
        target.role == "evidence"
        if evidence
        else target.role != "evidence"
    )


def _validated_apply_context(
    workspace,
    target,
    proposal,
    *,
    evidence,
):
    def valid_non_negative_integer(value):
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value >= 0
        )

    if (
        not isinstance(evidence, bool)
        or not isinstance(workspace, _PrivateTransactionWorkspace)
        or not isinstance(target, StorageTarget)
        or not isinstance(proposal, StagedProposal)
        or not _target_has_expected_role(target, evidence=evidence)
        or not target.changed
        or not valid_non_negative_integer(proposal.index)
        or proposal.index != target.index
        or proposal.state != "staged"
        or not valid_non_negative_integer(proposal.size)
        or proposal.size != target.after_size
        or not isinstance(proposal.sha256, str)
        or proposal.sha256 != target.after_sha256
        or not valid_non_negative_integer(proposal._device)
        or not valid_non_negative_integer(proposal._inode)
    ):
        _storage_context_failure()
    stage_name, relative_name = _staging_names(workspace, target)
    if proposal.relative_name != relative_name:
        _storage_context_failure()
    return stage_name


def _storage_verify_failure():
    raise LifecycleStorageError("STORAGE_VERIFY_FAILED") from None


def verify_canonical_target(workspace, target) -> int:
    """Prove one canonical target still equals its immutable preimage."""
    if (
        not isinstance(workspace, _PrivateTransactionWorkspace)
        or not isinstance(target, StorageTarget)
    ):
        _storage_context_failure()
    return _verify_canonical_preimage(workspace._root_fd, target)


def _apply_staged_changed_target(
    workspace,
    target,
    staged_proposal,
    *,
    evidence,
):
    stage_name = _validated_apply_context(
        workspace,
        target,
        staged_proposal,
        evidence=evidence,
    )
    parent_fd = None
    try:
        parent_fd, parent_metadata = _open_target_parent(workspace, target)
        if staged_proposal._device != parent_metadata.st_dev:
            _storage_context_failure()
        _verify_canonical_entry(
            parent_fd,
            target,
            existed=target.existed,
            expected_bytes=target._before_bytes,
            expected_sha256=target.before_sha256,
            failure=lambda: _canonical_conflict(target),
        )
        _verify_recorded_file(
            parent_fd,
            stage_name,
            expected_device=staged_proposal._device,
            expected_inode=staged_proposal._inode,
            expected_bytes=target._after_bytes,
            expected_sha256=target.after_sha256,
        )
        try:
            os.replace(
                stage_name,
                PurePosixPath(target.relative_path).name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_REPLACE_FAILED") from exc
        try:
            os.fsync(parent_fd)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        _verify_canonical_entry(
            parent_fd,
            target,
            existed=True,
            expected_bytes=target._after_bytes,
            expected_sha256=target.after_sha256,
            expected_mode=0o600,
            failure=_storage_verify_failure,
        )
        return target.index
    finally:
        _close_descriptors(parent_fd)


def apply_staged_target(workspace, target, staged_proposal) -> int:
    """Promote one verified ordinary proposal and return its target index."""
    return _apply_staged_changed_target(
        workspace,
        target,
        staged_proposal,
        evidence=False,
    )


def finalize_staged_evidence(workspace, target, staged_proposal) -> int:
    """Promote one verified final evidence proposal and return its index."""
    return _apply_staged_changed_target(
        workspace,
        target,
        staged_proposal,
        evidence=True,
    )


class _CanonicalStateMismatch(RuntimeError):
    pass


def _canonical_state_mismatch():
    raise _CanonicalStateMismatch from None


def _canonical_entry_matches(
    parent_fd,
    target,
    *,
    existed,
    expected_bytes,
    expected_sha256,
    expected_mode=None,
):
    try:
        _verify_canonical_entry(
            parent_fd,
            target,
            existed=existed,
            expected_bytes=expected_bytes,
            expected_sha256=expected_sha256,
            expected_mode=expected_mode,
            failure=_canonical_state_mismatch,
        )
    except _CanonicalStateMismatch:
        return False
    return True


def _classify_changed_target(workspace, target, *, evidence) -> str:
    if (
        not isinstance(evidence, bool)
        or not isinstance(workspace, _PrivateTransactionWorkspace)
        or not isinstance(target, StorageTarget)
        or not target.changed
        or not _target_has_expected_role(target, evidence=evidence)
    ):
        _storage_context_failure()
    parent_fd = None
    try:
        parent_fd, _metadata = _open_target_parent(workspace, target)
        if _canonical_entry_matches(
            parent_fd,
            target,
            existed=target.existed,
            expected_bytes=target._before_bytes,
            expected_sha256=target.before_sha256,
        ):
            return "before"
        if _canonical_entry_matches(
            parent_fd,
            target,
            existed=True,
            expected_bytes=target._after_bytes,
            expected_sha256=target.after_sha256,
            expected_mode=0o600,
        ):
            return "after"
        raise LifecycleStorageError("STORAGE_CANONICAL_STATE_UNKNOWN")
    except LifecycleStorageError as exc:
        if exc.code in {
            "STORAGE_CONTEXT_INVALID",
            "STORAGE_CANONICAL_STATE_UNKNOWN",
        }:
            raise
        raise LifecycleStorageError("STORAGE_CANONICAL_STATE_UNKNOWN") from None
    finally:
        _close_descriptors(parent_fd)


def classify_canonical_target(workspace, target) -> str:
    """Return exact ordinary 'before' or 'after'; reject unknown state."""
    return _classify_changed_target(
        workspace,
        target,
        evidence=False,
    )


def classify_finalized_evidence(workspace, target) -> str:
    """Return exact evidence 'before' or 'after'; reject unknown state."""
    return _classify_changed_target(
        workspace,
        target,
        evidence=True,
    )


def classify_recovered_target(workspace, target) -> str:
    """Classify a rehydrated target, including an already-restored stage loss."""
    if isinstance(target, StorageTarget):
        return _classify_changed_target(
            workspace,
            target,
            evidence=target.role == "evidence",
        )
    if (
        not isinstance(workspace, _PrivateTransactionWorkspace)
        or not isinstance(target, _RecoveredBeforeTarget)
        or not target.changed
    ):
        _storage_context_failure()
    parent_fd = None
    try:
        parent_fd, _metadata = _open_target_parent(workspace, target)
        if _canonical_entry_matches(
            parent_fd,
            target,
            existed=target.existed,
            expected_bytes=target._before_bytes,
            expected_sha256=target.before_sha256,
        ):
            return "before"
        raise LifecycleStorageError("STORAGE_CANONICAL_STATE_UNKNOWN")
    except LifecycleStorageError:
        raise
    except OSError as exc:
        raise LifecycleStorageError(
            "STORAGE_CANONICAL_STATE_UNKNOWN"
        ) from exc
    finally:
        _close_descriptors(parent_fd)


def _valid_non_negative_integer(value):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
    )


def _validated_rollback_context(
    workspace,
    target,
    preimage,
    *,
    evidence,
):
    if (
        not isinstance(evidence, bool)
        or not isinstance(workspace, _PrivateTransactionWorkspace)
        or not isinstance(target, StorageTarget)
        or not isinstance(preimage, StoredPreimage)
        or not target.changed
        or not _target_has_expected_role(target, evidence=evidence)
        or not _valid_non_negative_integer(preimage.index)
        or preimage.index != target.index
    ):
        _storage_context_failure()
    if target.existed:
        if (
            preimage.state != "present"
            or preimage.relative_name != f"preimages/{target.index:06d}.bin"
            or not _valid_non_negative_integer(preimage.size)
            or preimage.size != len(target._before_bytes)
            or preimage.sha256 != target.before_sha256
            or not _valid_non_negative_integer(preimage._device)
            or not _valid_non_negative_integer(preimage._inode)
        ):
            _storage_context_failure()
    elif (
        preimage.state != "absent"
        or preimage.relative_name != "absent"
        or not _valid_non_negative_integer(preimage.size)
        or preimage.size != 0
        or preimage.sha256 != "absent"
        or not isinstance(preimage._device, int)
        or isinstance(preimage._device, bool)
        or preimage._device != -1
        or not isinstance(preimage._inode, int)
        or isinstance(preimage._inode, bool)
        or preimage._inode != -1
    ):
        _storage_context_failure()
    return preimage


def _rollback_name(workspace, target):
    digest = hashlib.sha256(workspace.transaction_id.encode("utf-8")).hexdigest()
    return f".moduflow-rollback-{digest}-{target.index:06d}"


def _write_rollback_stage(parent_fd, workspace, target):
    name = _rollback_name(workspace, target)
    descriptor = None
    offset = 0
    try:
        flags = (
            os.O_CREAT
            | os.O_EXCL
            | os.O_RDWR
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(name, flags, 0o600, dir_fd=parent_fd)
            os.fchmod(descriptor, 0o600)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_WRITE_FAILED") from exc
        try:
            while offset < len(target._before_bytes):
                written = os.write(descriptor, target._before_bytes[offset:])
                if written <= 0:
                    raise OSError(errno.EIO, "rollback stage write failed")
                offset += written
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_WRITE_FAILED") from exc
        try:
            os.fsync(descriptor)
            metadata = os.fstat(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        _verify_recorded_file(
            parent_fd,
            name,
            expected_device=metadata.st_dev,
            expected_inode=metadata.st_ino,
            expected_bytes=target._before_bytes,
            expected_sha256=target.before_sha256,
        )
        return name
    finally:
        _close_descriptors(descriptor)


def _require_exact_after(parent_fd, target):
    if not _canonical_entry_matches(
        parent_fd,
        target,
        existed=True,
        expected_bytes=target._after_bytes,
        expected_sha256=target.after_sha256,
        expected_mode=0o600,
    ):
        raise LifecycleStorageError("STORAGE_CANONICAL_STATE_UNKNOWN")


def _require_exact_before(parent_fd, target):
    if not _canonical_entry_matches(
        parent_fd,
        target,
        existed=target.existed,
        expected_bytes=target._before_bytes,
        expected_sha256=target.before_sha256,
        expected_mode=0o600 if target.existed else None,
    ):
        raise LifecycleStorageError("STORAGE_VERIFY_FAILED")


def _rollback_changed_target(
    workspace,
    target,
    preimage,
    *,
    evidence,
):
    _validated_rollback_context(
        workspace,
        target,
        preimage,
        evidence=evidence,
    )
    parent_fd = None
    try:
        parent_fd, _parent_metadata = _open_target_parent(workspace, target)
        if target.existed:
            _verify_recorded_file(
                workspace._preimages_fd,
                f"{target.index:06d}.bin",
                expected_device=preimage._device,
                expected_inode=preimage._inode,
                expected_bytes=target._before_bytes,
                expected_sha256=target.before_sha256,
            )
            rollback_name = _write_rollback_stage(
                parent_fd,
                workspace,
                target,
            )
            _require_exact_after(parent_fd, target)
            try:
                os.replace(
                    rollback_name,
                    PurePosixPath(target.relative_path).name,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                )
            except OSError as exc:
                raise LifecycleStorageError("STORAGE_REPLACE_FAILED") from exc
        else:
            _require_exact_after(parent_fd, target)
            try:
                os.unlink(
                    PurePosixPath(target.relative_path).name,
                    dir_fd=parent_fd,
                )
            except OSError as exc:
                raise LifecycleStorageError("STORAGE_REMOVE_FAILED") from exc
        try:
            os.fsync(parent_fd)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        _require_exact_before(parent_fd, target)
        return target.index
    finally:
        _close_descriptors(parent_fd)


def rollback_canonical_target(workspace, target, preimage) -> int:
    """Restore one exact ordinary after-state target to its before state."""
    return _rollback_changed_target(
        workspace,
        target,
        preimage,
        evidence=False,
    )


def rollback_finalized_evidence(workspace, target, preimage) -> int:
    """Restore one exact evidence after-state target to its before state."""
    return _rollback_changed_target(
        workspace,
        target,
        preimage,
        evidence=True,
    )


def _verify_recovery_inputs(workspace, targets, preimages, staged_proposals):
    for target, preimage, proposal in zip(
        targets,
        preimages,
        staged_proposals,
    ):
        if preimage.state == "present":
            _verify_recorded_file(
                workspace._preimages_fd,
                f"{target.index:06d}.bin",
                expected_device=preimage._device,
                expected_inode=preimage._inode,
                expected_bytes=target._before_bytes,
                expected_sha256=target.before_sha256,
            )
        if proposal.state == "staged":
            parent_fd = None
            try:
                parent_fd, parent_metadata = _open_target_parent(workspace, target)
                expected_name, expected_relative_name = _staging_names(
                    workspace,
                    target,
                )
                if (
                    proposal.relative_name != expected_relative_name
                    or proposal._device != parent_metadata.st_dev
                ):
                    _storage_context_failure()
                _verify_recorded_file(
                    parent_fd,
                    expected_name,
                    expected_device=proposal._device,
                    expected_inode=proposal._inode,
                    expected_bytes=target._after_bytes,
                    expected_sha256=target.after_sha256,
                )
            finally:
                _close_descriptors(parent_fd)


def _recovery_manifest_bytes(workspace, targets, preimages, staged_proposals):
    records = []
    for target, preimage, proposal in zip(
        targets,
        preimages,
        staged_proposals,
    ):
        preimage_value = {"state": "absent"}
        if preimage.state == "present":
            preimage_value = {
                "state": "present",
                "relative_name": preimage.relative_name,
                "size": preimage.size,
                "sha256": preimage.sha256,
            }
        proposal_value = {"state": "unchanged"}
        if proposal.state == "staged":
            proposal_value = {
                "state": "staged",
                "relative_name": proposal.relative_name,
                "size": proposal.size,
                "sha256": proposal.sha256,
                "device": proposal._device,
                "inode": proposal._inode,
            }
        records.append(
            {
                "index": target.index,
                "role": target.role,
                "relative_path": target.relative_path,
                "existed": target.existed,
                "before_sha256": target.before_sha256,
                "after_sha256": target.after_sha256,
                "preimage": preimage_value,
                "proposed": proposal_value,
            }
        )
    manifest = {
        "schema": _RECOVERY_MANIFEST_SCHEMA,
        "transaction_id": workspace.transaction_id,
        "targets": records,
    }
    return (
        json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _write_recovery_manifest(workspace, manifest_bytes):
    descriptor = None
    metadata = None
    written = 0
    flags = (
        os.O_CREAT
        | os.O_EXCL
        | os.O_RDWR
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        try:
            descriptor = os.open(
                _RECOVERY_MANIFEST_NAME,
                flags,
                mode=0o600,
                dir_fd=workspace._workspace_fd,
            )
        except FileExistsError as exc:
            raise LifecycleStorageError("STORAGE_CONFLICT") from exc
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_CREATE_FAILED") from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise OSError(errno.EINVAL, "manifest is not privately owned")
            os.fchmod(descriptor, 0o600)
        except OSError as exc:
            if metadata is None or not _cleanup_owned_regular(
                workspace._workspace_fd,
                _RECOVERY_MANIFEST_NAME,
                metadata,
                b"",
            ):
                raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
            raise LifecycleStorageError("STORAGE_CREATE_FAILED") from exc
        try:
            while written < len(manifest_bytes):
                count = os.write(descriptor, manifest_bytes[written:])
                if count <= 0 or count > len(manifest_bytes) - written:
                    raise OSError(errno.EIO, "manifest write failed")
                written += count
        except OSError as exc:
            if not _cleanup_owned_regular(
                workspace._workspace_fd,
                _RECOVERY_MANIFEST_NAME,
                metadata,
                manifest_bytes[:written],
            ):
                raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
            raise LifecycleStorageError("STORAGE_WRITE_FAILED") from exc
        try:
            stored = _read_complete(descriptor, len(manifest_bytes))
            opened = os.fstat(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED") from exc
        digest = hashlib.sha256(manifest_bytes).hexdigest()
        if (
            len(stored) != len(manifest_bytes)
            or hashlib.sha256(stored).hexdigest() != digest
            or not secrets.compare_digest(stored, manifest_bytes)
        ):
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED")
        if not _owned_regular_metadata(opened, metadata):
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH")
        try:
            os.fsync(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        try:
            current = os.stat(
                _RECOVERY_MANIFEST_NAME,
                dir_fd=workspace._workspace_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
        if (
            not _owned_regular_metadata(current, metadata)
            or stat.S_IMODE(current.st_mode) != 0o600
        ):
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH")
        try:
            os.fsync(workspace._workspace_fd)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        return RecoveryManifest(
            relative_name=_RECOVERY_MANIFEST_NAME,
            size=len(stored),
            sha256=digest,
            _device=metadata.st_dev,
            _inode=metadata.st_ino,
        )
    finally:
        _close_descriptors(descriptor)


def finalize_recovery_manifest(
    workspace,
    storage_targets,
    preimages,
    staged_proposals,
):
    """Create one immutable synchronized recovery manifest."""
    if not isinstance(workspace, _PrivateTransactionWorkspace):
        _storage_context_failure()
    targets, preimage_records, proposal_records = _validated_recovery_records(
        storage_targets,
        preimages,
        staged_proposals,
    )
    _verify_recovery_inputs(
        workspace,
        targets,
        preimage_records,
        proposal_records,
    )
    manifest_bytes = _recovery_manifest_bytes(
        workspace,
        targets,
        preimage_records,
        proposal_records,
    )
    return _write_recovery_manifest(workspace, manifest_bytes)


def _validated_recovery_targets(recovery_targets):
    if (
        not isinstance(recovery_targets, tuple)
        or not recovery_targets
        or not all(
            isinstance(target, RecoveryTarget) for target in recovery_targets
        )
        or [target.index for target in recovery_targets]
        != list(range(len(recovery_targets)))
    ):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_MANIFEST_MISMATCH"
        )
    return recovery_targets


def _require_manifest_keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise LifecycleRecoveryStorageError("RECOVERY_MANIFEST_INVALID")


def _parse_recovery_manifest(
    workspace,
    targets,
    manifest_snapshot,
    expected_manifest_sha256,
):
    if manifest_snapshot.state != "present":
        raise LifecycleRecoveryStorageError("RECOVERY_MANIFEST_MISSING")
    if (
        not isinstance(expected_manifest_sha256, str)
        or not _SHA256.fullmatch(expected_manifest_sha256)
        or manifest_snapshot.sha256 != expected_manifest_sha256
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_MANIFEST_MISMATCH")
    try:
        manifest = json.loads(manifest_snapshot._bytes.decode("utf-8"))
    except (AttributeError, TypeError, ValueError, UnicodeError):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_MANIFEST_INVALID"
        ) from None
    _require_manifest_keys(manifest, ("schema", "transaction_id", "targets"))
    if (
        manifest["schema"] != _RECOVERY_MANIFEST_SCHEMA
        or manifest["transaction_id"] != workspace.transaction_id
        or not isinstance(manifest["targets"], list)
        or len(manifest["targets"]) != len(targets)
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_MANIFEST_MISMATCH")
    canonical = (
        json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    if not secrets.compare_digest(canonical, manifest_snapshot._bytes):
        raise LifecycleRecoveryStorageError("RECOVERY_MANIFEST_INVALID")
    return tuple(manifest["targets"])


def _read_recovery_payload(
    parent_fd,
    name,
    *,
    expected_size,
    expected_sha256,
    expected_device=None,
    expected_inode=None,
):
    descriptor = None
    try:
        try:
            before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_MISSING"
            ) from None
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_nlink != 1
            or (
                expected_device is not None
                and before.st_dev != expected_device
            )
            or (
                expected_inode is not None
                and before.st_ino != expected_inode
            )
        ):
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            )
        descriptor = os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        opened = os.fstat(descriptor)
        payload = _read_complete(descriptor, expected_size)
        after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        final_opened = os.fstat(descriptor)
        same_entry = all(
            _journal_metadata_matches(metadata, before)
            for metadata in (opened, after, final_opened)
        )
        if not same_entry:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            )
        if (
            len(payload) != expected_size
            or hashlib.sha256(payload).hexdigest() != expected_sha256
        ):
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_MISMATCH"
            )
        return payload, before
    except LifecycleRecoveryStorageError:
        raise
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_PAYLOAD_INVALID"
        ) from exc
    finally:
        _close_descriptors(descriptor)


def _manifest_target_record(target, record):
    _require_manifest_keys(
        record,
        (
            "index",
            "role",
            "relative_path",
            "existed",
            "before_sha256",
            "after_sha256",
            "preimage",
            "proposed",
        ),
    )
    expected = {
        "index": target.index,
        "role": target.role,
        "relative_path": target.relative_path,
        "existed": target.existed,
        "before_sha256": target.before_sha256,
        "after_sha256": target.after_sha256,
    }
    if any(record[key] != value for key, value in expected.items()):
        raise LifecycleRecoveryStorageError("RECOVERY_MANIFEST_MISMATCH")
    return record["preimage"], record["proposed"]


def _load_recovered_preimage(workspace, target, record):
    if not target.existed:
        if record != {"state": "absent"}:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_MANIFEST_MISMATCH"
            )
        return (
            b"",
            StoredPreimage(
                index=target.index,
                state="absent",
                relative_name="absent",
                size=0,
                sha256="absent",
                _device=-1,
                _inode=-1,
            ),
        )
    _require_manifest_keys(
        record,
        ("state", "relative_name", "size", "sha256"),
    )
    expected_name = f"preimages/{target.index:06d}.bin"
    if (
        record["state"] != "present"
        or record["relative_name"] != expected_name
        or not isinstance(record["size"], int)
        or isinstance(record["size"], bool)
        or record["size"] < 0
        or record["sha256"] != target.before_sha256
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_MANIFEST_MISMATCH")
    payload, metadata = _read_recovery_payload(
        workspace._preimages_fd,
        f"{target.index:06d}.bin",
        expected_size=record["size"],
        expected_sha256=target.before_sha256,
    )
    return (
        payload,
        StoredPreimage(
            index=target.index,
            state="present",
            relative_name=expected_name,
            size=len(payload),
            sha256=target.before_sha256,
            _device=metadata.st_dev,
            _inode=metadata.st_ino,
        ),
    )


def _load_recovered_proposal(
    workspace,
    target,
    record,
    before_bytes,
    *,
    allow_consumed,
):
    if not target.changed:
        if record != {"state": "unchanged"}:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_MANIFEST_MISMATCH"
            )
        if len(before_bytes) != target.after_size:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_MISMATCH"
            )
        return (
            before_bytes,
            StagedProposal(
                index=target.index,
                state="unchanged",
                relative_name="unchanged",
                size=0,
                sha256="unchanged",
                _device=-1,
                _inode=-1,
            ),
        )
    _require_manifest_keys(
        record,
        (
            "state",
            "relative_name",
            "size",
            "sha256",
            "device",
            "inode",
        ),
    )
    parent_fd = None
    try:
        parent_fd, parent_metadata = _open_target_parent(workspace, target)
        stage_name, relative_name = _staging_names(workspace, target)
        if (
            record["state"] != "staged"
            or record["relative_name"] != relative_name
            or record["size"] != target.after_size
            or record["sha256"] != target.after_sha256
            or not isinstance(record["device"], int)
            or isinstance(record["device"], bool)
            or not isinstance(record["inode"], int)
            or isinstance(record["inode"], bool)
            or record["device"] != parent_metadata.st_dev
        ):
            raise LifecycleRecoveryStorageError(
                "RECOVERY_MANIFEST_MISMATCH"
            )
        try:
            payload, metadata = _read_recovery_payload(
                parent_fd,
                stage_name,
                expected_size=target.after_size,
                expected_sha256=target.after_sha256,
                expected_device=record["device"],
                expected_inode=record["inode"],
            )
        except LifecycleRecoveryStorageError as exc:
            if exc.code != "RECOVERY_PAYLOAD_MISSING":
                raise
            if not allow_consumed:
                raise
            try:
                payload, _canonical_metadata = _read_recovery_payload(
                    parent_fd,
                    PurePosixPath(target.relative_path).name,
                    expected_size=target.after_size,
                    expected_sha256=target.after_sha256,
                )
            except LifecycleRecoveryStorageError:
                if _canonical_entry_matches(
                    parent_fd,
                    target,
                    existed=target.existed,
                    expected_bytes=before_bytes,
                    expected_sha256=target.before_sha256,
                ):
                    return None, None
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_PAYLOAD_MISSING"
                ) from None
            return payload, None
        return (
            payload,
            StagedProposal(
                index=target.index,
                state="staged",
                relative_name=relative_name,
                size=len(payload),
                sha256=target.after_sha256,
                _device=metadata.st_dev,
                _inode=metadata.st_ino,
            ),
        )
    except LifecycleStorageError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_PAYLOAD_INVALID"
        ) from exc
    finally:
        _close_descriptors(parent_fd)


def _verify_recovery_stage_inventory(workspace, targets, *, allow_missing=False):
    digest = hashlib.sha256(workspace.transaction_id.encode("utf-8")).hexdigest()
    prefix = f".moduflow-stage-{digest}-"
    parents = {}
    for target in targets:
        parent_key = PurePosixPath(target.relative_path).parent.as_posix()
        if parent_key not in parents:
            parents[parent_key] = [target, set()]
        if target.changed:
            stage_name, _relative_name = _staging_names(workspace, target)
            parents[parent_key][1].add(stage_name)
    for representative, expected_names in parents.values():
        parent_fd = None
        try:
            parent_fd, _metadata = _open_target_parent(
                workspace,
                representative,
            )
            current_names = {
                name for name in os.listdir(parent_fd) if name.startswith(prefix)
            }
        except (OSError, LifecycleStorageError) as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        finally:
            _close_descriptors(parent_fd)
        if (
            (not allow_missing and current_names != expected_names)
            or (allow_missing and not current_names.issubset(expected_names))
        ):
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_MISMATCH"
            )


def load_recovery_materials(
    workspace,
    recovery_targets,
    manifest_snapshot,
    expected_manifest_sha256,
    *,
    recoverable_missing_indexes=(),
):
    """Rehydrate exact manifest-bound recovery inputs without writes."""
    if not isinstance(workspace, _PrivateTransactionWorkspace):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    targets = _validated_recovery_targets(recovery_targets)
    if (
        not isinstance(recoverable_missing_indexes, tuple)
        or any(
            not isinstance(index, int)
            or isinstance(index, bool)
            or index < 0
            or index >= len(targets)
            or not targets[index].changed
            for index in recoverable_missing_indexes
        )
        or len(recoverable_missing_indexes)
        != len(set(recoverable_missing_indexes))
    ):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_MANIFEST_MISMATCH"
        )
    recoverable_missing = frozenset(recoverable_missing_indexes)
    records = _parse_recovery_manifest(
        workspace,
        targets,
        manifest_snapshot,
        expected_manifest_sha256,
    )
    _verify_recovery_stage_inventory(workspace, targets, allow_missing=True)
    storage_targets = []
    preimages = []
    proposals = []
    expected_preimage_entries = []
    for target, record in zip(targets, records):
        preimage_record, proposal_record = _manifest_target_record(
            target,
            record,
        )
        before_bytes, preimage = _load_recovered_preimage(
            workspace,
            target,
            preimage_record,
        )
        after_bytes, proposal = _load_recovered_proposal(
            workspace,
            target,
            proposal_record,
            before_bytes,
            allow_consumed=target.index in recoverable_missing,
        )
        target_type = (
            StorageTarget
            if after_bytes is not None
            else _RecoveredBeforeTarget
        )
        target_values = {
            "index": target.index,
            "role": target.role,
            "relative_path": target.relative_path,
            "existed": target.existed,
            "before_sha256": target.before_sha256,
            "after_sha256": target.after_sha256,
            "after_size": target.after_size,
            "changed": target.changed,
            "_before_bytes": before_bytes,
        }
        if after_bytes is not None:
            target_values["_after_bytes"] = after_bytes
        storage_targets.append(
            target_type(
                **target_values,
            )
        )
        preimages.append(preimage)
        proposals.append(proposal)
        if target.existed:
            expected_preimage_entries.append(f"{target.index:06d}.bin")
    if tuple(expected_preimage_entries) != tuple(
        sorted(os.listdir(workspace._preimages_fd))
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_PAYLOAD_MISMATCH")
    return _RecoveredMaterials(
        storage_targets=tuple(storage_targets),
        preimages=tuple(preimages),
        staged_proposals=tuple(proposals),
        recovery_manifest=RecoveryManifest(
            relative_name=_RECOVERY_MANIFEST_NAME,
            size=manifest_snapshot.size,
            sha256=manifest_snapshot.sha256,
            _device=manifest_snapshot._device,
            _inode=manifest_snapshot._inode,
        ),
    )


def verify_recovery_canonical_before(workspace, recovery_targets):
    """Prove journal-only targets remain at exact canonical before-state."""
    if not isinstance(workspace, _PrivateTransactionWorkspace):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    targets = _validated_recovery_targets(recovery_targets)
    verified = []
    for target in targets:
        parent_fd = None
        descriptor = None
        try:
            parent_fd, _parent_metadata = _open_target_parent(workspace, target)
            name = PurePosixPath(target.relative_path).name
            try:
                initial = os.stat(
                    name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                if target.existed:
                    raise LifecycleRecoveryStorageError(
                        "RECOVERY_PAYLOAD_MISMATCH"
                    ) from None
                verified.append(target.index)
                continue
            if not target.existed or not stat.S_ISREG(initial.st_mode):
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_PAYLOAD_MISMATCH"
                )
            descriptor = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_fd,
            )
            opened = os.fstat(descriptor)
            digest = hashlib.sha256()
            while True:
                chunk = os.read(descriptor, 64 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
            final = os.stat(
                name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
            final_opened = os.fstat(descriptor)
            stable = all(
                stat.S_ISREG(metadata.st_mode)
                and metadata.st_dev == initial.st_dev
                and metadata.st_ino == initial.st_ino
                and metadata.st_size == initial.st_size
                for metadata in (opened, final, final_opened)
            )
            if not stable or digest.hexdigest() != target.before_sha256:
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_PAYLOAD_MISMATCH"
                )
            verified.append(target.index)
        except LifecycleRecoveryStorageError:
            raise
        except (OSError, LifecycleStorageError) as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        finally:
            _close_descriptors(descriptor, parent_fd)
    return tuple(verified)


def verify_cleanup_canonical_state(workspace, recovery_targets, *, after):
    """Prove journal-only canonical before/after state for cleanup resume."""
    if (
        not isinstance(workspace, _PrivateCleanupWorkspace)
        or not isinstance(after, bool)
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    targets = _validated_recovery_targets(recovery_targets)
    verified = []
    for target in targets:
        parent_fd = None
        descriptor = None
        try:
            parent_fd, _parent_metadata = _open_target_parent(workspace, target)
            name = PurePosixPath(target.relative_path).name
            expected_hash = target.after_sha256 if after else target.before_sha256
            expected_absent = not after and not target.existed
            try:
                initial = os.stat(
                    name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                if not expected_absent:
                    raise LifecycleRecoveryStorageError(
                        "RECOVERY_PAYLOAD_MISMATCH"
                    ) from None
                verified.append(target.index)
                continue
            if expected_absent or not stat.S_ISREG(initial.st_mode):
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_PAYLOAD_MISMATCH"
                )
            descriptor = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_fd,
            )
            opened = os.fstat(descriptor)
            digest = hashlib.sha256()
            size = 0
            while True:
                chunk = os.read(descriptor, 64 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                size += len(chunk)
            final = os.stat(
                name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
            final_opened = os.fstat(descriptor)
            stable = all(
                stat.S_ISREG(metadata.st_mode)
                and metadata.st_dev == initial.st_dev
                and metadata.st_ino == initial.st_ino
                and metadata.st_size == initial.st_size
                for metadata in (opened, final, final_opened)
            )
            if (
                not stable
                or digest.hexdigest() != expected_hash
                or (after and size != target.after_size)
            ):
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_PAYLOAD_MISMATCH"
                )
            verified.append(target.index)
        except LifecycleRecoveryStorageError:
            raise
        except (OSError, LifecycleStorageError) as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        finally:
            _close_descriptors(descriptor, parent_fd)
    return tuple(verified)


def discard_recovered_journal_next(workspace, snapshot):
    """Discard only the exact verified abandoned journal successor."""
    if (
        not isinstance(workspace, _PrivateTransactionWorkspace)
        or not isinstance(snapshot, _RecoveryFileSnapshot)
        or snapshot.state != "present"
    ):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )
    current = _read_recovery_file(
        workspace._workspace_fd,
        _JOURNAL_NEXT_NAME,
    )
    if (
        current.state != "present"
        or current.size != snapshot.size
        or current.sha256 != snapshot.sha256
        or current._device != snapshot._device
        or current._inode != snapshot._inode
        or not secrets.compare_digest(current._bytes, snapshot._bytes)
    ):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )
    try:
        os.unlink(_JOURNAL_NEXT_NAME, dir_fd=workspace._workspace_fd)
        os.fsync(workspace._workspace_fd)
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        ) from exc


def verify_unbound_recovery_inventory(
    workspace,
    recovery_targets,
    control_snapshot,
):
    """Verify present unbound payloads without returning recovery authority."""
    if not isinstance(workspace, _PrivateTransactionWorkspace):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    targets = _validated_recovery_targets(recovery_targets)
    if not isinstance(control_snapshot, _RecoveryControlSnapshot):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )
    if control_snapshot.recovery_manifest.state == "present":
        load_recovery_materials(
            workspace,
            targets,
            control_snapshot.recovery_manifest,
            control_snapshot.recovery_manifest.sha256,
        )
        return

    expected_preimage_names = {
        f"{target.index:06d}.bin"
        for target in targets
        if target.existed
    }
    current_preimage_names = set(control_snapshot._preimage_entries)
    if not current_preimage_names.issubset(expected_preimage_names):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_PAYLOAD_MISMATCH"
        )
    for name in current_preimage_names:
        index = int(name[:6])
        target = targets[index]
        try:
            metadata = os.stat(
                name,
                dir_fd=workspace._preimages_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        _read_recovery_payload(
            workspace._preimages_fd,
            name,
            expected_size=metadata.st_size,
            expected_sha256=target.before_sha256,
        )

    _verify_recovery_stage_inventory(
        workspace,
        targets,
        allow_missing=True,
    )
    digest = hashlib.sha256(workspace.transaction_id.encode("utf-8")).hexdigest()
    prefix = f".moduflow-stage-{digest}-"
    inspected_parents = set()
    for target in targets:
        parent_key = PurePosixPath(target.relative_path).parent.as_posix()
        if parent_key in inspected_parents:
            continue
        inspected_parents.add(parent_key)
        parent_fd = None
        try:
            parent_fd, parent_metadata = _open_target_parent(workspace, target)
            stage_names = tuple(
                name
                for name in os.listdir(parent_fd)
                if name.startswith(prefix)
            )
            for stage_name in stage_names:
                try:
                    index = int(stage_name[-6:])
                    selected = targets[index]
                except (IndexError, TypeError, ValueError):
                    raise LifecycleRecoveryStorageError(
                        "RECOVERY_PAYLOAD_MISMATCH"
                    ) from None
                expected_name, _relative_name = _staging_names(
                    workspace,
                    selected,
                )
                if stage_name != expected_name or not selected.changed:
                    raise LifecycleRecoveryStorageError(
                        "RECOVERY_PAYLOAD_MISMATCH"
                    )
                _read_recovery_payload(
                    parent_fd,
                    stage_name,
                    expected_size=selected.after_size,
                    expected_sha256=selected.after_sha256,
                    expected_device=parent_metadata.st_dev,
                )
        except (OSError, LifecycleStorageError) as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        finally:
            _close_descriptors(parent_fd)


def _recovery_directory_snapshot(metadata):
    if not _private_directory_metadata(metadata):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    return _RecoveryDirectorySnapshot(
        _device=metadata.st_dev,
        _inode=metadata.st_ino,
        _mode=stat.S_IMODE(metadata.st_mode),
    )


def _cleanup_directory_snapshots(workspace):
    if not isinstance(workspace, _PrivateTransactionWorkspace):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    try:
        workspace_entry = os.stat(
            workspace.transaction_id,
            dir_fd=workspace._transactions_fd,
            follow_symlinks=False,
        )
        workspace_opened = os.fstat(workspace._workspace_fd)
        preimages_entry = os.stat(
            _PREIMAGES_NAME,
            dir_fd=workspace._workspace_fd,
            follow_symlinks=False,
        )
        preimages_opened = os.fstat(workspace._preimages_fd)
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_WORKSPACE_UNSAFE"
        ) from exc
    if (
        not _same_directory_metadata(workspace_entry, workspace_opened)
        or not _same_directory_metadata(preimages_entry, preimages_opened)
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    return (
        _recovery_directory_snapshot(workspace_opened),
        _recovery_directory_snapshot(preimages_opened),
    )


def _same_cleanup_directory(first, second):
    return (
        isinstance(first, _RecoveryDirectorySnapshot)
        and isinstance(second, _RecoveryDirectorySnapshot)
        and first._device == second._device
        and first._inode == second._inode
        and first._mode == second._mode
    )


def _same_recovery_file_snapshot(first, second):
    return (
        isinstance(first, _RecoveryFileSnapshot)
        and isinstance(second, _RecoveryFileSnapshot)
        and first.state == second.state
        and first.size == second.size
        and first.sha256 == second.sha256
        and first._device == second._device
        and first._inode == second._inode
        and secrets.compare_digest(first._bytes, second._bytes)
    )


def _same_cleanup_control_snapshot(first, second):
    return (
        isinstance(first, _RecoveryControlSnapshot)
        and isinstance(second, _RecoveryControlSnapshot)
        and _same_recovery_file_snapshot(first.journal, second.journal)
        and _same_recovery_file_snapshot(
            first.journal_next,
            second.journal_next,
        )
        and _same_recovery_file_snapshot(
            first.recovery_manifest,
            second.recovery_manifest,
        )
        and first._workspace_entries == second._workspace_entries
        and first._preimage_entries == second._preimage_entries
    )


def _load_unbound_cleanup_materials(workspace, targets, control_snapshot):
    verify_unbound_recovery_inventory(
        workspace,
        targets,
        control_snapshot,
    )
    preimage_entries = set(control_snapshot._preimage_entries)
    preimages = []
    staged_proposals = []
    for target in targets:
        preimage_name = f"{target.index:06d}.bin"
        if target.existed and preimage_name in preimage_entries:
            try:
                metadata = os.stat(
                    preimage_name,
                    dir_fd=workspace._preimages_fd,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_PAYLOAD_INVALID"
                ) from exc
            payload, metadata = _read_recovery_payload(
                workspace._preimages_fd,
                preimage_name,
                expected_size=metadata.st_size,
                expected_sha256=target.before_sha256,
            )
            preimages.append(
                StoredPreimage(
                    index=target.index,
                    state="present",
                    relative_name=f"preimages/{preimage_name}",
                    size=len(payload),
                    sha256=target.before_sha256,
                    _device=metadata.st_dev,
                    _inode=metadata.st_ino,
                )
            )
        else:
            preimages.append(
                StoredPreimage(
                    index=target.index,
                    state="absent",
                    relative_name="absent",
                    size=0,
                    sha256="absent",
                    _device=-1,
                    _inode=-1,
                )
            )

        if not target.changed:
            staged_proposals.append(
                StagedProposal(
                    index=target.index,
                    state="unchanged",
                    relative_name="unchanged",
                    size=0,
                    sha256="unchanged",
                    _device=-1,
                    _inode=-1,
                )
            )
            continue
        parent_fd = None
        try:
            parent_fd, parent_metadata = _open_target_parent(
                workspace,
                target,
            )
            stage_name, relative_name = _staging_names(workspace, target)
            try:
                stage_metadata = os.stat(
                    stage_name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                staged_proposals.append(None)
                continue
            payload, stage_metadata = _read_recovery_payload(
                parent_fd,
                stage_name,
                expected_size=target.after_size,
                expected_sha256=target.after_sha256,
                expected_device=parent_metadata.st_dev,
            )
            staged_proposals.append(
                StagedProposal(
                    index=target.index,
                    state="staged",
                    relative_name=relative_name,
                    size=len(payload),
                    sha256=target.after_sha256,
                    _device=stage_metadata.st_dev,
                    _inode=stage_metadata.st_ino,
                )
            )
        except (OSError, LifecycleStorageError) as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        finally:
            _close_descriptors(parent_fd)
    return tuple(preimages), tuple(staged_proposals)


def _verify_exact_cleanup_preimages(workspace, preimages):
    if not isinstance(preimages, tuple):
        raise LifecycleRecoveryStorageError("RECOVERY_PAYLOAD_INVALID")
    for preimage in preimages:
        if not isinstance(preimage, StoredPreimage):
            raise LifecycleRecoveryStorageError("RECOVERY_PAYLOAD_INVALID")
        if preimage.state == "absent":
            continue
        name = f"{preimage.index:06d}.bin"
        _payload, metadata = _read_recovery_payload(
            workspace._preimages_fd,
            name,
            expected_size=preimage.size,
            expected_sha256=preimage.sha256,
            expected_device=preimage._device,
            expected_inode=preimage._inode,
        )
        if (
            metadata.st_dev != preimage._device
            or metadata.st_ino != preimage._inode
        ):
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            )


def _verify_exact_cleanup_stages(workspace, targets, staged_proposals):
    if (
        not isinstance(staged_proposals, tuple)
        or len(staged_proposals) != len(targets)
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_PAYLOAD_INVALID")
    expected_by_parent = {}
    for target, proposal in zip(targets, staged_proposals):
        parent_key = PurePosixPath(target.relative_path).parent.as_posix()
        expected_by_parent.setdefault(parent_key, [target, set()])
        if proposal is not None and proposal.state == "staged":
            stage_name, _relative_name = _staging_names(workspace, target)
            expected_by_parent[parent_key][1].add(stage_name)
    digest = hashlib.sha256(workspace.transaction_id.encode("utf-8")).hexdigest()
    prefix = f".moduflow-stage-{digest}-"
    for representative, expected_names in expected_by_parent.values():
        parent_fd = None
        try:
            parent_fd, _parent_metadata = _open_target_parent(
                workspace,
                representative,
            )
            current_names = {
                name for name in os.listdir(parent_fd) if name.startswith(prefix)
            }
            if current_names != expected_names:
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_PAYLOAD_MISMATCH"
                )
        except LifecycleRecoveryStorageError:
            raise
        except (OSError, LifecycleStorageError) as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        finally:
            _close_descriptors(parent_fd)

    for target, proposal in zip(targets, staged_proposals):
        if proposal is None or proposal.state != "staged":
            continue
        parent_fd = None
        try:
            parent_fd, _parent_metadata = _open_target_parent(
                workspace,
                target,
            )
            stage_name, _relative_name = _staging_names(workspace, target)
            _payload, metadata = _read_recovery_payload(
                parent_fd,
                stage_name,
                expected_size=proposal.size,
                expected_sha256=proposal.sha256,
                expected_device=proposal._device,
                expected_inode=proposal._inode,
            )
            if (
                metadata.st_dev != proposal._device
                or metadata.st_ino != proposal._inode
            ):
                raise LifecycleRecoveryStorageError(
                    "RECOVERY_PAYLOAD_INVALID"
                )
        except (OSError, LifecycleStorageError) as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        finally:
            _close_descriptors(parent_fd)


def verify_recovery_cleanup_inventory(
    workspace,
    recovery_targets,
    control_snapshot,
    *,
    recoverable_missing_indexes=(),
):
    """Return one private read-only proof of the exact cleanup inventory."""
    if (
        not isinstance(workspace, _PrivateTransactionWorkspace)
        or not isinstance(control_snapshot, _RecoveryControlSnapshot)
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    targets = _validated_recovery_targets(recovery_targets)
    directories_before = _cleanup_directory_snapshots(workspace)
    current_control = read_recovery_control_snapshot(workspace)
    if not _same_cleanup_control_snapshot(current_control, control_snapshot):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )

    manifest = None
    if current_control.recovery_manifest.state == "present":
        materials = load_recovery_materials(
            workspace,
            targets,
            current_control.recovery_manifest,
            current_control.recovery_manifest.sha256,
            recoverable_missing_indexes=recoverable_missing_indexes,
        )
        preimages = materials.preimages
        staged_proposals = materials.staged_proposals
        manifest = materials.recovery_manifest
    else:
        if recoverable_missing_indexes:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_MANIFEST_MISMATCH"
            )
        preimages, staged_proposals = _load_unbound_cleanup_materials(
            workspace,
            targets,
            current_control,
        )

    if (
        len(preimages) != len(targets)
        or len(staged_proposals) != len(targets)
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_PAYLOAD_INVALID")
    _verify_exact_cleanup_preimages(workspace, preimages)
    _verify_exact_cleanup_stages(workspace, targets, staged_proposals)
    final_control = read_recovery_control_snapshot(workspace)
    directories_after = _cleanup_directory_snapshots(workspace)
    if (
        not _same_cleanup_control_snapshot(final_control, current_control)
        or not _same_cleanup_directory(
            directories_before[0],
            directories_after[0],
        )
        or not _same_cleanup_directory(
            directories_before[1],
            directories_after[1],
        )
    ):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )
    return _RecoveryCleanupInventory(
        _workspace_directory=directories_after[0],
        _preimages_directory=directories_after[1],
        _control_snapshot=final_control,
        _recovery_targets=targets,
        _preimages=preimages,
        _staged_proposals=staged_proposals,
        _recovery_manifest=manifest,
    )


def _cleanup_resume_directory_snapshots(workspace):
    if not isinstance(workspace, _PrivateCleanupWorkspace):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    try:
        workspace_entry = os.stat(
            workspace.transaction_id,
            dir_fd=workspace._transactions_fd,
            follow_symlinks=False,
        )
        workspace_opened = os.fstat(workspace._workspace_fd)
    except OSError as exc:
        raise LifecycleRecoveryStorageError(
            "RECOVERY_WORKSPACE_UNSAFE"
        ) from exc
    if not _same_directory_metadata(workspace_entry, workspace_opened):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    preimages = None
    if workspace._preimages_fd is not None:
        try:
            preimages_entry = os.stat(
                _PREIMAGES_NAME,
                dir_fd=workspace._workspace_fd,
                follow_symlinks=False,
            )
            preimages_opened = os.fstat(workspace._preimages_fd)
        except OSError as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_WORKSPACE_UNSAFE"
            ) from exc
        if not _same_directory_metadata(preimages_entry, preimages_opened):
            raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
        preimages = _recovery_directory_snapshot(preimages_opened)
    return _recovery_directory_snapshot(workspace_opened), preimages


def _verify_cleanup_payload_subsets(workspace, targets, control_snapshot):
    expected_preimages = {
        f"{target.index:06d}.bin": target
        for target in targets
        if target.existed
    }
    current_preimages = set(control_snapshot._preimage_entries)
    if not current_preimages.issubset(expected_preimages):
        raise LifecycleRecoveryStorageError("RECOVERY_PAYLOAD_MISMATCH")
    if current_preimages and workspace._preimages_fd is None:
        raise LifecycleRecoveryStorageError("RECOVERY_PAYLOAD_INVALID")
    for name in current_preimages:
        target = expected_preimages[name]
        try:
            metadata = os.stat(
                name,
                dir_fd=workspace._preimages_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        _read_recovery_payload(
            workspace._preimages_fd,
            name,
            expected_size=metadata.st_size,
            expected_sha256=target.before_sha256,
        )

    digest = hashlib.sha256(workspace.transaction_id.encode("utf-8")).hexdigest()
    prefix = f".moduflow-stage-{digest}-"
    expected_stages = {}
    parents = {}
    for target in targets:
        parent_key = PurePosixPath(target.relative_path).parent.as_posix()
        parents.setdefault(parent_key, target)
        if target.changed:
            stage_name, _relative_name = _staging_names(workspace, target)
            expected_stages[(parent_key, stage_name)] = target
    present_stages = []
    for parent_key, representative in parents.items():
        parent_fd = None
        try:
            parent_fd, parent_metadata = _open_target_parent(
                workspace,
                representative,
            )
            names = {
                name for name in os.listdir(parent_fd) if name.startswith(prefix)
            }
            for name in names:
                target = expected_stages.get((parent_key, name))
                if target is None:
                    raise LifecycleRecoveryStorageError(
                        "RECOVERY_PAYLOAD_MISMATCH"
                    )
                _read_recovery_payload(
                    parent_fd,
                    name,
                    expected_size=target.after_size,
                    expected_sha256=target.after_sha256,
                    expected_device=parent_metadata.st_dev,
                )
                present_stages.append((parent_key, name))
        except LifecycleRecoveryStorageError:
            raise
        except (OSError, LifecycleStorageError) as exc:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_INVALID"
            ) from exc
        finally:
            _close_descriptors(parent_fd)
    return current_preimages, tuple(sorted(present_stages))


def verify_cleanup_resume_inventory(
    workspace,
    recovery_targets,
    control_snapshot,
    *,
    terminal_kind,
):
    """Classify only an exact ordered cleanup remainder without mutation."""
    if (
        not isinstance(workspace, _PrivateCleanupWorkspace)
        or not isinstance(control_snapshot, _RecoveryControlSnapshot)
        or terminal_kind not in {"complete", "rolled-back", "pre-journal-orphan"}
    ):
        raise LifecycleRecoveryStorageError("RECOVERY_WORKSPACE_UNSAFE")
    directories_before = _cleanup_resume_directory_snapshots(workspace)
    current = read_cleanup_control_snapshot(workspace)
    if not _same_cleanup_control_snapshot(current, control_snapshot):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )

    if current.journal.state == "absent" and current.journal_next.state == "absent":
        if current._workspace_entries or workspace._preimages_fd is not None:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_CONTROL_FILE_UNSAFE"
            )
        return _CleanupResumeInventory(
            remainder_kind="empty-workspace",
            _workspace_directory=directories_before[0],
            _preimages_directory=None,
            _control_snapshot=current,
            _recovery_targets=(),
        )

    targets = _validated_recovery_targets(recovery_targets)

    if terminal_kind == "pre-journal-orphan":
        if (
            current.journal.state != "absent"
            or current.journal_next.state != "present"
        ):
            raise LifecycleRecoveryStorageError(
                "RECOVERY_CONTROL_FILE_UNSAFE"
            )
    elif current.journal.state != "present":
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )

    if current.recovery_manifest.state == "present":
        _parse_recovery_manifest(
            workspace,
            targets,
            current.recovery_manifest,
            current.recovery_manifest.sha256,
        )
    preimages, stages = _verify_cleanup_payload_subsets(
        workspace,
        targets,
        current,
    )
    expected_preimages = {
        f"{target.index:06d}.bin" for target in targets if target.existed
    }
    has_preimages_directory = workspace._preimages_fd is not None
    has_manifest = current.recovery_manifest.state == "present"
    if terminal_kind != "pre-journal-orphan":
        if not has_manifest and (has_preimages_directory or stages):
            raise LifecycleRecoveryStorageError(
                "RECOVERY_CONTROL_FILE_UNSAFE"
            )
        if not has_preimages_directory and stages:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_MISMATCH"
            )
        if preimages != expected_preimages and stages:
            raise LifecycleRecoveryStorageError(
                "RECOVERY_PAYLOAD_MISMATCH"
            )
    remainder_kind = (
        "terminal-full"
        if has_manifest
        and has_preimages_directory
        and preimages == expected_preimages
        else "terminal-private-suffix"
        if has_manifest
        else "terminal-control-suffix"
    )
    final = read_cleanup_control_snapshot(workspace)
    directories_after = _cleanup_resume_directory_snapshots(workspace)
    if (
        not _same_cleanup_control_snapshot(final, current)
        or not _same_cleanup_directory(
            directories_before[0],
            directories_after[0],
        )
        or (
            directories_before[1] is None
            and directories_after[1] is not None
        )
        or (
            directories_before[1] is not None
            and not _same_cleanup_directory(
                directories_before[1],
                directories_after[1],
            )
        )
    ):
        raise LifecycleRecoveryStorageError(
            "RECOVERY_CONTROL_FILE_UNSAFE"
        )
    return _CleanupResumeInventory(
        remainder_kind=remainder_kind,
        _workspace_directory=directories_after[0],
        _preimages_directory=directories_after[1],
        _control_snapshot=final,
        _recovery_targets=targets,
    )


def _journal_context(workspace, journal_bytes, expected_previous_sha256):
    if (
        not isinstance(workspace, _PrivateTransactionWorkspace)
        or not isinstance(journal_bytes, bytes)
        or not journal_bytes
        or (
            expected_previous_sha256 != "absent"
            and (
                not isinstance(expected_previous_sha256, str)
                or not _SHA256.fullmatch(expected_previous_sha256)
            )
        )
    ):
        _storage_context_failure()
    return journal_bytes


def _journal_metadata_matches(metadata, expected):
    return (
        stat.S_ISREG(metadata.st_mode)
        and stat.S_IMODE(metadata.st_mode) == 0o600
        and metadata.st_nlink == 1
        and metadata.st_dev == expected.st_dev
        and metadata.st_ino == expected.st_ino
    )


def _current_journal_state(workspace):
    descriptor = None
    read_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        try:
            current = os.stat(
                _JOURNAL_NAME,
                dir_fd=workspace._workspace_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return _JournalState(
                state="absent",
                sha256="absent",
                _device=-1,
                _inode=-1,
            )
        except OSError as exc:
            raise LifecycleStorageError(
                "STORAGE_JOURNAL_STATE_MISMATCH"
            ) from exc
        if (
            not stat.S_ISREG(current.st_mode)
            or stat.S_IMODE(current.st_mode) != 0o600
            or current.st_nlink != 1
        ):
            raise LifecycleStorageError("STORAGE_JOURNAL_STATE_MISMATCH")
        try:
            descriptor = os.open(
                _JOURNAL_NAME,
                read_flags,
                dir_fd=workspace._workspace_fd,
            )
            opened = os.fstat(descriptor)
        except OSError as exc:
            raise LifecycleStorageError(
                "STORAGE_JOURNAL_STATE_MISMATCH"
            ) from exc
        if not _journal_metadata_matches(opened, current):
            raise LifecycleStorageError("STORAGE_JOURNAL_STATE_MISMATCH")
        digest = hashlib.sha256()
        try:
            while True:
                chunk = os.read(descriptor, 64 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
            final_entry = os.stat(
                _JOURNAL_NAME,
                dir_fd=workspace._workspace_fd,
                follow_symlinks=False,
            )
            final_opened = os.fstat(descriptor)
        except OSError as exc:
            raise LifecycleStorageError(
                "STORAGE_JOURNAL_STATE_MISMATCH"
            ) from exc
        if (
            not _journal_metadata_matches(final_entry, current)
            or not _journal_metadata_matches(final_opened, current)
        ):
            raise LifecycleStorageError("STORAGE_JOURNAL_STATE_MISMATCH")
        return _JournalState(
            state="present",
            sha256=digest.hexdigest(),
            _device=current.st_dev,
            _inode=current.st_ino,
        )
    finally:
        _close_descriptors(descriptor)


def _same_journal_state(current, expected):
    return (
        current.state == expected.state
        and current.sha256 == expected.sha256
        and current._device == expected._device
        and current._inode == expected._inode
    )


def _cleanup_journal_next(workspace, metadata, expected_bytes):
    if not _cleanup_owned_regular(
        workspace._workspace_fd,
        _JOURNAL_NEXT_NAME,
        metadata,
        expected_bytes,
    ):
        raise LifecycleStorageError("STORAGE_OWNER_MISMATCH")
    try:
        os.fsync(workspace._workspace_fd)
    except OSError as exc:
        raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc


def _write_journal_next(workspace, journal_bytes):
    descriptor = None
    metadata = None
    written = 0
    flags = (
        os.O_CREAT
        | os.O_EXCL
        | os.O_RDWR
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        try:
            descriptor = os.open(
                _JOURNAL_NEXT_NAME,
                flags,
                mode=0o600,
                dir_fd=workspace._workspace_fd,
            )
        except FileExistsError as exc:
            raise LifecycleStorageError("STORAGE_CONFLICT") from exc
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_CREATE_FAILED") from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise OSError(errno.EINVAL, "journal next is not privately owned")
            os.fchmod(descriptor, 0o600)
            metadata = os.fstat(descriptor)
        except OSError as exc:
            if metadata is None:
                raise LifecycleStorageError("STORAGE_OWNER_MISMATCH") from exc
            try:
                _cleanup_journal_next(workspace, metadata, b"")
            except LifecycleStorageError as cleanup_error:
                raise cleanup_error from exc
            raise LifecycleStorageError("STORAGE_CREATE_FAILED") from exc
        try:
            while written < len(journal_bytes):
                count = os.write(descriptor, journal_bytes[written:])
                if count <= 0 or count > len(journal_bytes) - written:
                    raise OSError(errno.EIO, "journal write failed")
                written += count
        except OSError as exc:
            try:
                _cleanup_journal_next(
                    workspace,
                    metadata,
                    journal_bytes[:written],
                )
            except LifecycleStorageError as cleanup_error:
                raise cleanup_error from exc
            raise LifecycleStorageError("STORAGE_WRITE_FAILED") from exc
        try:
            stored = _read_complete(descriptor, len(journal_bytes))
            opened = os.fstat(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED") from exc
        digest = hashlib.sha256(journal_bytes).hexdigest()
        if (
            len(stored) != len(journal_bytes)
            or hashlib.sha256(stored).hexdigest() != digest
            or not secrets.compare_digest(stored, journal_bytes)
        ):
            raise LifecycleStorageError("STORAGE_VERIFY_FAILED")
        if not _journal_metadata_matches(opened, metadata):
            raise LifecycleStorageError("STORAGE_OWNER_MISMATCH")
        try:
            os.fsync(descriptor)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        return metadata, digest
    finally:
        _close_descriptors(descriptor)


def persist_serialized_journal(
    workspace,
    journal_bytes,
    *,
    expected_previous_sha256,
):
    """Atomically persist exact validated bytes and return their SHA-256."""
    payload = _journal_context(
        workspace,
        journal_bytes,
        expected_previous_sha256,
    )
    previous = _current_journal_state(workspace)
    if previous.sha256 != expected_previous_sha256:
        raise LifecycleStorageError("STORAGE_JOURNAL_STATE_MISMATCH")
    next_metadata, digest = _write_journal_next(workspace, payload)
    try:
        _verify_recorded_file(
            workspace._workspace_fd,
            _JOURNAL_NEXT_NAME,
            expected_device=next_metadata.st_dev,
            expected_inode=next_metadata.st_ino,
            expected_bytes=payload,
            expected_sha256=digest,
        )
        try:
            current = _current_journal_state(workspace)
        except LifecycleStorageError as exc:
            try:
                _cleanup_journal_next(workspace, next_metadata, payload)
            except LifecycleStorageError as cleanup_error:
                raise cleanup_error from exc
            raise
        if not _same_journal_state(current, previous):
            _cleanup_journal_next(workspace, next_metadata, payload)
            raise LifecycleStorageError("STORAGE_JOURNAL_STATE_MISMATCH")
        try:
            os.replace(
                _JOURNAL_NEXT_NAME,
                _JOURNAL_NAME,
                src_dir_fd=workspace._workspace_fd,
                dst_dir_fd=workspace._workspace_fd,
            )
        except OSError as exc:
            try:
                unchanged = _same_journal_state(
                    _current_journal_state(workspace),
                    previous,
                )
            except LifecycleStorageError:
                unchanged = False
            if unchanged:
                try:
                    _cleanup_journal_next(
                        workspace,
                        next_metadata,
                        payload,
                    )
                except LifecycleStorageError as cleanup_error:
                    raise cleanup_error from exc
                raise LifecycleStorageError("STORAGE_WRITE_FAILED") from exc
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        try:
            _verify_recorded_file(
                workspace._workspace_fd,
                _JOURNAL_NAME,
                expected_device=next_metadata.st_dev,
                expected_inode=next_metadata.st_ino,
                expected_bytes=payload,
                expected_sha256=digest,
            )
        except LifecycleStorageError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        try:
            os.fsync(workspace._workspace_fd)
        except OSError as exc:
            raise LifecycleStorageError("STORAGE_DURABILITY_UNCERTAIN") from exc
        return digest
    except LifecycleStorageError:
        raise
