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
