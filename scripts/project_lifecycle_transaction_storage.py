#!/usr/bin/env python3
"""Private durable storage primitives for Issue 103 lifecycle transactions."""

from contextlib import contextmanager
from dataclasses import dataclass, field
import errno
import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import secrets
import stat


_LOGICAL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PREIMAGES_NAME = "preimages"


class LifecycleStorageError(RuntimeError):
    """Stable private-storage failure without paths or payload values."""

    def __init__(self, code):
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
        if not _owned_regular_metadata(current, metadata):
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
