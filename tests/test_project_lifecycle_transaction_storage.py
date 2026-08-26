import hashlib
import importlib
import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

storage = (
    importlib.import_module("project_lifecycle_transaction_storage")
    if importlib.util.find_spec("project_lifecycle_transaction_storage")
    else None
)


class PrivatePreimageStorageTests(unittest.TestCase):
    def scaffold(self, root):
        transactions = root / ".moduflow" / "transactions"
        transactions.mkdir(parents=True)
        transactions.chmod(0o700)
        return transactions

    def target(
        self,
        index=0,
        *,
        existed=True,
        before=b"before",
        after=b"after",
        relative_path=None,
    ):
        if not existed:
            before = b""
        if relative_path is None:
            relative_path = (
                "issues/BIZ-103.md"
                if index == 0
                else ".moduflow/evidence/BIZ-103.json"
            )
        return storage.StorageTarget(
            index=index,
            role="issue" if index == 0 else "evidence",
            relative_path=relative_path,
            existed=existed,
            before_sha256=(
                hashlib.sha256(before).hexdigest() if existed else "absent"
            ),
            after_sha256=hashlib.sha256(after).hexdigest(),
            after_size=len(after),
            changed=(not existed or before != after),
            _before_bytes=before,
            _after_bytes=after,
        )

    def test_stages_only_changed_targets_on_parent_device_without_canonical_changes(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "stage_proposed_targets", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            issue = root / "issues" / "BIZ-103.md"
            evidence = root / ".moduflow" / "evidence" / "BIZ-103.json"
            issue.parent.mkdir()
            evidence.parent.mkdir()
            issue.write_bytes(b"original issue")
            evidence.write_bytes(b"stable evidence")
            targets = (
                self.target(
                    0,
                    before=b"original issue",
                    after=b"proposed issue",
                ),
                self.target(
                    1,
                    before=b"stable evidence",
                    after=b"stable evidence",
                ),
            )
            canonical_before = {
                str(issue): issue.read_bytes(),
                str(evidence): evidence.read_bytes(),
            }

            with storage.private_transaction_workspace(root, "txn-stage") as workspace:
                records = entry(workspace, targets)

            expected_name = (
                ".moduflow-stage-"
                "1ab9bc12711f63f5dfa8ebecdcba60fe0b9c8abc7139da7dd68c364763ae52ef-"
                "000000"
            )
            staged = issue.parent / expected_name
            metadata = staged.stat()
            self.assertEqual(
                [(record.index, record.state) for record in records],
                [(0, "staged"), (1, "unchanged")],
            )
            self.assertEqual(records[0].relative_name, f"issues/{expected_name}")
            self.assertEqual(records[0].size, len(b"proposed issue"))
            self.assertEqual(
                records[0].sha256,
                "14e8f08b401307602bce8528cf7b53a9a65c1b9cc79555801506142acb0aaf2f",
            )
            self.assertEqual(records[0]._device, metadata.st_dev)
            self.assertEqual(records[0]._inode, metadata.st_ino)
            self.assertEqual(records[1].relative_name, "unchanged")
            self.assertEqual(records[1].size, 0)
            self.assertEqual(records[1].sha256, "unchanged")
            self.assertEqual(stat.S_IMODE(metadata.st_mode), 0o600)
            self.assertEqual(metadata.st_nlink, 1)
            self.assertEqual(metadata.st_dev, issue.parent.stat().st_dev)
            self.assertEqual(staged.read_bytes(), b"proposed issue")
            self.assertEqual(
                [path.name for path in issue.parent.glob(".moduflow-stage-*")],
                [expected_name],
            )
            self.assertEqual(
                {str(issue): issue.read_bytes(), str(evidence): evidence.read_bytes()},
                canonical_before,
            )

    def test_staging_rejects_missing_unsafe_or_conflicting_parent_without_mutation(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "stage_proposed_targets", None)
        self.assertIsNotNone(entry)
        scenarios = (
            ("missing", "missing/BIZ-103.md", "STORAGE_PATH_UNSAFE"),
            ("symlink", "unsafe/BIZ-103.md", "STORAGE_PATH_UNSAFE"),
            ("file", "blocked/BIZ-103.md", "STORAGE_PATH_UNSAFE"),
            ("conflict", "issues/BIZ-103.md", "STORAGE_CONFLICT"),
        )
        for scenario, relative_path, expected_code in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                issue = root / "issues" / "BIZ-103.md"
                issue.parent.mkdir()
                issue.write_bytes(b"original issue")
                marker = None
                if scenario == "symlink":
                    external = root / "external"
                    external.mkdir()
                    (root / "unsafe").symlink_to(external, target_is_directory=True)
                    marker = external
                elif scenario == "file":
                    marker = root / "blocked"
                    marker.write_bytes(b"not a directory")
                elif scenario == "conflict":
                    marker = issue.parent / (
                        ".moduflow-stage-"
                        "568aa77986863d528e19938f9546bd96dfa2e7f20d3d5bb7eafe7ede55a7bb1a-"
                        "000000"
                    )
                    marker.write_bytes(b"foreign stage")
                marker_before = marker.stat() if marker is not None else None
                marker_bytes = (
                    marker.read_bytes()
                    if marker is not None and marker.is_file()
                    else None
                )
                target = self.target(
                    0,
                    before=b"original issue",
                    after=b"proposed issue",
                    relative_path=relative_path,
                )

                with storage.private_transaction_workspace(
                    root,
                    f"txn-{scenario}",
                ) as workspace:
                    with mock.patch.object(storage.os, "mkdir") as make_directory:
                        with self.assertRaises(storage.LifecycleStorageError) as raised:
                            entry(workspace, (target,))
                    make_directory.assert_not_called()

                self.assertEqual(raised.exception.code, expected_code)
                self.assertEqual(issue.read_bytes(), b"original issue")
                if marker is not None:
                    marker_after = marker.stat()
                    self.assertEqual(marker_after.st_ino, marker_before.st_ino)
                    self.assertEqual(marker_after.st_mtime_ns, marker_before.st_mtime_ns)
                    if marker_bytes is not None:
                        self.assertEqual(marker.read_bytes(), marker_bytes)

    def test_staging_cleanup_removes_only_exact_owner_and_preserves_uncertainty(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "stage_proposed_targets", None)
        self.assertIsNotNone(entry)
        expected_name = (
            ".moduflow-stage-"
            "1ab9bc12711f63f5dfa8ebecdcba60fe0b9c8abc7139da7dd68c364763ae52ef-"
            "000000"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            issue = root / "issues" / "BIZ-103.md"
            issue.parent.mkdir()
            issue.write_bytes(b"original issue")
            target = self.target(
                0,
                before=b"original issue",
                after=b"proposed issue",
            )
            with storage.private_transaction_workspace(root, "txn-stage") as workspace:
                real_write = storage.os.write
                calls = []

                def fail_after_prefix(descriptor, payload):
                    calls.append(len(payload))
                    if len(calls) == 1:
                        return real_write(descriptor, bytes(payload[:3]))
                    raise OSError(5, "STAGE WRITE FAILURE")

                with mock.patch.object(
                    storage.os,
                    "write",
                    side_effect=fail_after_prefix,
                ):
                    with self.assertRaises(storage.LifecycleStorageError) as raised:
                        entry(workspace, (target,))
            self.assertEqual(raised.exception.code, "STORAGE_WRITE_FAILED")
            self.assertFalse((issue.parent / expected_name).exists())
            self.assertEqual(issue.read_bytes(), b"original issue")

        for failure, expected_code in (
            ("corrupt", "STORAGE_VERIFY_FAILED"),
            ("inode", "STORAGE_OWNER_MISMATCH"),
            ("mode-race", "STORAGE_OWNER_MISMATCH"),
            ("file-fsync", "STORAGE_DURABILITY_UNCERTAIN"),
            ("parent-fsync", "STORAGE_DURABILITY_UNCERTAIN"),
        ):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                issue = root / "issues" / "BIZ-103.md"
                issue.parent.mkdir()
                issue.write_bytes(b"original issue")
                target = self.target(
                    0,
                    before=b"original issue",
                    after=b"proposed issue",
                )
                with storage.private_transaction_workspace(
                    root,
                    "txn-stage",
                ) as workspace:
                    if failure == "corrupt":
                        real_write = storage.os.write

                        def corrupt_write(descriptor, payload):
                            return real_write(descriptor, b"x" * len(payload))

                        patcher = mock.patch.object(
                            storage.os,
                            "write",
                            side_effect=corrupt_write,
                        )
                    elif failure == "inode":
                        real_stat = storage.os.stat

                        def replaced_entry(path, *args, **kwargs):
                            metadata = real_stat(path, *args, **kwargs)
                            if path == expected_name and kwargs.get("dir_fd") is not None:
                                values = list(metadata)
                                values[1] = metadata.st_ino + 1
                                return os.stat_result(values)
                            return metadata

                        patcher = mock.patch.object(
                            storage.os,
                            "stat",
                            side_effect=replaced_entry,
                        )
                    elif failure == "mode-race":
                        real_fsync = storage.os.fsync

                        def change_mode_after_sync(descriptor):
                            result = real_fsync(descriptor)
                            (issue.parent / expected_name).chmod(0o644)
                            return result

                        patcher = mock.patch.object(
                            storage.os,
                            "fsync",
                            side_effect=change_mode_after_sync,
                        )
                    else:
                        real_fsync = storage.os.fsync
                        calls = []

                        def fail_selected_sync(descriptor):
                            calls.append(descriptor)
                            fail_at = 1 if failure == "file-fsync" else 2
                            if len(calls) == fail_at:
                                raise OSError(5, "STAGE SYNC FAILURE")
                            return real_fsync(descriptor)

                        patcher = mock.patch.object(
                            storage.os,
                            "fsync",
                            side_effect=fail_selected_sync,
                        )
                    with patcher:
                        with self.assertRaises(storage.LifecycleStorageError) as raised:
                            entry(workspace, (target,))
                self.assertEqual(raised.exception.code, expected_code)
                self.assertEqual(str(raised.exception), expected_code)
                self.assertTrue((issue.parent / expected_name).exists())
                self.assertEqual(issue.read_bytes(), b"original issue")

    def test_manifest_is_exact_canonical_redacted_immutable_and_hash_bound(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "finalize_recovery_manifest", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            issue = root / "issues" / "BIZ-103.md"
            evidence = root / ".moduflow" / "evidence" / "BIZ-103.json"
            stable = root / "roadmaps" / "product.md"
            issue.parent.mkdir()
            evidence.parent.mkdir()
            stable.parent.mkdir()
            issue.write_bytes(b"original issue")
            stable.write_bytes(b"stable roadmap")
            targets = (
                self.target(
                    0,
                    before=b"original issue",
                    after=b"proposed issue",
                ),
                self.target(
                    1,
                    existed=False,
                    after=b"new evidence",
                ),
                self.target(
                    2,
                    before=b"stable roadmap",
                    after=b"stable roadmap",
                    relative_path="roadmaps/product.md",
                ),
            )
            workspace_path = root / ".moduflow" / "transactions" / "txn-manifest"
            manifest_path = workspace_path / "recovery-manifest.json"

            with storage.private_transaction_workspace(
                root,
                "txn-manifest",
            ) as workspace:
                preimages = storage.store_preimages(workspace, targets)
                proposals = storage.stage_proposed_targets(workspace, targets)
                staged_metadata = {
                    proposal.index: (root / proposal.relative_name).stat()
                    for proposal in proposals
                    if proposal.state == "staged"
                }
                record = entry(workspace, targets, preimages, proposals)
                manifest_bytes = manifest_path.read_bytes()
                before = manifest_path.stat()
                with self.assertRaises(storage.LifecycleStorageError) as raised:
                    entry(workspace, targets, preimages, proposals)

            self.assertEqual(raised.exception.code, "STORAGE_CONFLICT")
            self.assertEqual(manifest_path.read_bytes(), manifest_bytes)
            self.assertEqual(manifest_path.stat().st_ino, before.st_ino)
            self.assertEqual(manifest_path.stat().st_mtime_ns, before.st_mtime_ns)
            expected = {
                "schema": "moduflow.lifecycle-transaction-recovery-manifest.v1",
                "transaction_id": "txn-manifest",
                "targets": [
                    {
                        "index": 0,
                        "role": "issue",
                        "relative_path": "issues/BIZ-103.md",
                        "existed": True,
                        "before_sha256": hashlib.sha256(b"original issue").hexdigest(),
                        "after_sha256": hashlib.sha256(b"proposed issue").hexdigest(),
                        "preimage": {
                            "state": "present",
                            "relative_name": "preimages/000000.bin",
                            "size": len(b"original issue"),
                            "sha256": hashlib.sha256(b"original issue").hexdigest(),
                        },
                        "proposed": {
                            "state": "staged",
                            "relative_name": proposals[0].relative_name,
                            "size": len(b"proposed issue"),
                            "sha256": hashlib.sha256(b"proposed issue").hexdigest(),
                            "device": staged_metadata[0].st_dev,
                            "inode": staged_metadata[0].st_ino,
                        },
                    },
                    {
                        "index": 1,
                        "role": "evidence",
                        "relative_path": ".moduflow/evidence/BIZ-103.json",
                        "existed": False,
                        "before_sha256": "absent",
                        "after_sha256": hashlib.sha256(b"new evidence").hexdigest(),
                        "preimage": {"state": "absent"},
                        "proposed": {
                            "state": "staged",
                            "relative_name": proposals[1].relative_name,
                            "size": len(b"new evidence"),
                            "sha256": hashlib.sha256(b"new evidence").hexdigest(),
                            "device": staged_metadata[1].st_dev,
                            "inode": staged_metadata[1].st_ino,
                        },
                    },
                    {
                        "index": 2,
                        "role": "evidence",
                        "relative_path": "roadmaps/product.md",
                        "existed": True,
                        "before_sha256": hashlib.sha256(b"stable roadmap").hexdigest(),
                        "after_sha256": hashlib.sha256(b"stable roadmap").hexdigest(),
                        "preimage": {
                            "state": "present",
                            "relative_name": "preimages/000002.bin",
                            "size": len(b"stable roadmap"),
                            "sha256": hashlib.sha256(b"stable roadmap").hexdigest(),
                        },
                        "proposed": {"state": "unchanged"},
                    },
                ],
            }
            expected_bytes = (
                json.dumps(
                    expected,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            )
            metadata = manifest_path.stat()
            self.assertEqual(manifest_bytes, expected_bytes)
            self.assertTrue(manifest_bytes.endswith(b"\n"))
            self.assertFalse(manifest_bytes.endswith(b"\n\n"))
            self.assertEqual(json.loads(manifest_bytes), expected)
            self.assertEqual(record.relative_name, "recovery-manifest.json")
            self.assertEqual(record.size, len(expected_bytes))
            self.assertEqual(record.sha256, hashlib.sha256(expected_bytes).hexdigest())
            self.assertEqual(record._device, metadata.st_dev)
            self.assertEqual(record._inode, metadata.st_ino)
            self.assertEqual(stat.S_IMODE(metadata.st_mode), 0o600)
            self.assertEqual(metadata.st_nlink, 1)
            rendered = manifest_bytes.decode("utf-8")
            for forbidden in (
                str(root),
                "original issue",
                "proposed issue",
                "new evidence",
                "stable roadmap",
                "actor",
                "source",
                "owner_token",
                '"pid"',
                "OS FAILURE",
            ):
                self.assertNotIn(forbidden, rendered)

    def test_manifest_rejects_unbound_records_before_creation(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "finalize_recovery_manifest", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            issue = root / "issues" / "BIZ-103.md"
            evidence = root / ".moduflow" / "evidence" / "BIZ-103.json"
            issue.parent.mkdir()
            evidence.parent.mkdir()
            issue.write_bytes(b"original issue")
            targets = (
                self.target(
                    0,
                    before=b"original issue",
                    after=b"proposed issue",
                ),
                self.target(1, existed=False, after=b"new evidence"),
            )
            workspace_path = root / ".moduflow" / "transactions" / "txn-invalid"
            manifest_path = workspace_path / "recovery-manifest.json"
            with storage.private_transaction_workspace(
                root,
                "txn-invalid",
            ) as workspace:
                preimages = storage.store_preimages(workspace, targets)
                proposals = storage.stage_proposed_targets(workspace, targets)
                invalid_contexts = (
                    (list(targets), preimages, proposals, "STORAGE_CONTEXT_INVALID"),
                    (targets, preimages[:1], proposals, "STORAGE_CONTEXT_INVALID"),
                    (
                        targets,
                        (replace(preimages[0], index=1), preimages[1]),
                        proposals,
                        "STORAGE_CONTEXT_INVALID",
                    ),
                    (
                        targets,
                        (replace(preimages[0], state="absent"), preimages[1]),
                        proposals,
                        "STORAGE_CONTEXT_INVALID",
                    ),
                    (
                        targets,
                        preimages,
                        (replace(proposals[0], state="unchanged"), proposals[1]),
                        "STORAGE_CONTEXT_INVALID",
                    ),
                    (
                        targets,
                        preimages,
                        (replace(proposals[0], size=1), proposals[1]),
                        "STORAGE_CONTEXT_INVALID",
                    ),
                    (
                        targets,
                        preimages,
                        (replace(proposals[0], _inode=proposals[0]._inode + 1), proposals[1]),
                        "STORAGE_OWNER_MISMATCH",
                    ),
                )
                for bad_targets, bad_preimages, bad_proposals, code in invalid_contexts:
                    with self.subTest(code=code, values=repr((bad_targets, bad_preimages, bad_proposals))):
                        with self.assertRaises(storage.LifecycleStorageError) as raised:
                            entry(
                                workspace,
                                bad_targets,
                                bad_preimages,
                                bad_proposals,
                            )
                        self.assertEqual(raised.exception.code, code)
                        self.assertFalse(manifest_path.exists())
                for preimage in preimages:
                    if preimage.state == "present":
                        self.assertEqual(
                            (workspace_path / preimage.relative_name).read_bytes(),
                            targets[preimage.index]._before_bytes,
                        )
                for proposal in proposals:
                    if proposal.state == "staged":
                        self.assertEqual(
                            (root / proposal.relative_name).read_bytes(),
                            targets[proposal.index]._after_bytes,
                        )
            self.assertEqual(issue.read_bytes(), b"original issue")
            self.assertFalse(evidence.exists())

    def test_manifest_rechecks_private_entry_identity_mode_and_bytes_before_sealing(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "finalize_recovery_manifest", None)
        self.assertIsNotNone(entry)
        for failure, expected_code in (
            ("mode", "STORAGE_OWNER_MISMATCH"),
            ("replacement-race", "STORAGE_OWNER_MISMATCH"),
            ("deleted", "STORAGE_OWNER_MISMATCH"),
            ("symlink", "STORAGE_OWNER_MISMATCH"),
            ("mutated", "STORAGE_VERIFY_FAILED"),
        ):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                issue = root / "issues" / "BIZ-103.md"
                issue.parent.mkdir()
                issue.write_bytes(b"original issue")
                target = self.target(
                    0,
                    before=b"original issue",
                    after=b"proposed issue",
                )
                workspace_path = root / ".moduflow" / "transactions" / "txn-recheck"
                manifest_path = workspace_path / "recovery-manifest.json"
                with storage.private_transaction_workspace(
                    root,
                    "txn-recheck",
                ) as workspace:
                    preimages = storage.store_preimages(workspace, (target,))
                    proposals = storage.stage_proposed_targets(workspace, (target,))
                    stage_path = root / proposals[0].relative_name
                    patcher = mock.patch.object(storage.os, "read", wraps=storage.os.read)
                    if failure == "mode":
                        stage_path.chmod(0o644)
                    elif failure == "replacement-race":
                        real_read = storage.os.read
                        replaced = []

                        def replace_after_read(descriptor, size):
                            payload = real_read(descriptor, size)
                            if (
                                not replaced
                                and os.fstat(descriptor).st_ino == proposals[0]._inode
                            ):
                                stage_path.unlink()
                                stage_path.write_bytes(b"proposed issue")
                                stage_path.chmod(0o600)
                                replaced.append(True)
                            return payload

                        patcher = mock.patch.object(
                            storage.os,
                            "read",
                            side_effect=replace_after_read,
                        )
                    elif failure == "deleted":
                        stage_path.unlink()
                    elif failure == "symlink":
                        external = root / "external-stage"
                        external.write_bytes(b"proposed issue")
                        stage_path.unlink()
                        stage_path.symlink_to(external)
                    else:
                        stage_path.write_bytes(b"mutated stage")
                    with patcher:
                        with self.assertRaises(storage.LifecycleStorageError) as raised:
                            entry(workspace, (target,), preimages, proposals)
                    self.assertEqual(raised.exception.code, expected_code)
                    self.assertFalse(manifest_path.exists())
                self.assertEqual(issue.read_bytes(), b"original issue")

    def test_manifest_cleanup_removes_exact_partial_but_preserves_uncertainty(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "finalize_recovery_manifest", None)
        self.assertIsNotNone(entry)
        for failure, expected_code, should_exist in (
            ("partial", "STORAGE_WRITE_FAILED", False),
            ("corrupt", "STORAGE_VERIFY_FAILED", True),
            ("inode", "STORAGE_OWNER_MISMATCH", True),
            ("mode-race", "STORAGE_OWNER_MISMATCH", True),
            ("file-fsync", "STORAGE_DURABILITY_UNCERTAIN", True),
            ("workspace-fsync", "STORAGE_DURABILITY_UNCERTAIN", True),
        ):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                issue = root / "issues" / "BIZ-103.md"
                issue.parent.mkdir()
                issue.write_bytes(b"original issue")
                target = self.target(
                    0,
                    before=b"original issue",
                    after=b"proposed issue",
                )
                workspace_path = root / ".moduflow" / "transactions" / "txn-manifest"
                manifest_path = workspace_path / "recovery-manifest.json"
                with storage.private_transaction_workspace(
                    root,
                    "txn-manifest",
                ) as workspace:
                    preimages = storage.store_preimages(workspace, (target,))
                    proposals = storage.stage_proposed_targets(workspace, (target,))
                    preimage_path = workspace_path / preimages[0].relative_name
                    stage_path = root / proposals[0].relative_name
                    private_before = {
                        str(preimage_path): preimage_path.read_bytes(),
                        str(stage_path): stage_path.read_bytes(),
                    }
                    if failure in {"partial", "corrupt"}:
                        real_write = storage.os.write
                        calls = []

                        def altered_write(descriptor, payload):
                            calls.append(len(payload))
                            if failure == "partial":
                                if len(calls) == 1:
                                    return real_write(descriptor, bytes(payload[:3]))
                                raise OSError(5, "MANIFEST WRITE FAILURE")
                            return real_write(descriptor, b"x" * len(payload))

                        patcher = mock.patch.object(
                            storage.os,
                            "write",
                            side_effect=altered_write,
                        )
                    elif failure == "inode":
                        real_stat = storage.os.stat

                        def replaced_entry(path, *args, **kwargs):
                            metadata = real_stat(path, *args, **kwargs)
                            if (
                                path == "recovery-manifest.json"
                                and kwargs.get("dir_fd") is not None
                            ):
                                values = list(metadata)
                                values[1] = metadata.st_ino + 1
                                return os.stat_result(values)
                            return metadata

                        patcher = mock.patch.object(
                            storage.os,
                            "stat",
                            side_effect=replaced_entry,
                        )
                    elif failure == "mode-race":
                        real_fsync = storage.os.fsync

                        def change_mode_after_sync(descriptor):
                            result = real_fsync(descriptor)
                            manifest_path.chmod(0o644)
                            return result

                        patcher = mock.patch.object(
                            storage.os,
                            "fsync",
                            side_effect=change_mode_after_sync,
                        )
                    else:
                        real_fsync = storage.os.fsync
                        calls = []

                        def fail_selected_sync(descriptor):
                            calls.append(descriptor)
                            fail_at = 1 if failure == "file-fsync" else 2
                            if len(calls) == fail_at:
                                raise OSError(5, "MANIFEST SYNC FAILURE")
                            return real_fsync(descriptor)

                        patcher = mock.patch.object(
                            storage.os,
                            "fsync",
                            side_effect=fail_selected_sync,
                        )
                    with patcher:
                        with self.assertRaises(storage.LifecycleStorageError) as raised:
                            entry(workspace, (target,), preimages, proposals)
                    self.assertEqual(raised.exception.code, expected_code)
                    self.assertEqual(str(raised.exception), expected_code)
                    self.assertEqual(manifest_path.exists(), should_exist)
                    self.assertEqual(
                        {
                            str(preimage_path): preimage_path.read_bytes(),
                            str(stage_path): stage_path.read_bytes(),
                        },
                        private_before,
                    )
                self.assertEqual(issue.read_bytes(), b"original issue")

    def test_journal_persistence_requires_exact_previous_digest_and_replaces_atomically(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "persist_serialized_journal", None)
        self.assertIsNotNone(entry)
        planned = b'{"phase":"planned"}\n'
        staged = b'{"phase":"staged"}\n'
        prepared = b'{"phase":"prepared"}\n'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            workspace_path = root / ".moduflow" / "transactions" / "txn-journal"
            journal_path = workspace_path / "journal.json"
            next_path = workspace_path / "journal.next"
            with storage.private_transaction_workspace(
                root,
                "txn-journal",
            ) as workspace:
                planned_digest = entry(
                    workspace,
                    planned,
                    expected_previous_sha256="absent",
                )
                self.assertEqual(
                    planned_digest,
                    "76eda423415751804910c8872a224a312413b5e231d23f959acf04082a6429a2",
                )
                self.assertEqual(journal_path.read_bytes(), planned)
                self.assertFalse(next_path.exists())
                staged_digest = entry(
                    workspace,
                    staged,
                    expected_previous_sha256=planned_digest,
                )
                prepared_digest = entry(
                    workspace,
                    prepared,
                    expected_previous_sha256=staged_digest,
                )
                metadata = journal_path.stat()
                self.assertEqual(journal_path.read_bytes(), prepared)
                self.assertEqual(
                    prepared_digest,
                    hashlib.sha256(prepared).hexdigest(),
                )
                self.assertEqual(stat.S_IMODE(metadata.st_mode), 0o600)
                self.assertEqual(metadata.st_nlink, 1)
                self.assertFalse(next_path.exists())
                for expected in ("absent", "0" * 64):
                    with self.subTest(expected=expected):
                        before = journal_path.stat()
                        with self.assertRaises(storage.LifecycleStorageError) as raised:
                            entry(
                                workspace,
                                b'{"phase":"unknown"}\n',
                                expected_previous_sha256=expected,
                            )
                        self.assertEqual(
                            raised.exception.code,
                            "STORAGE_JOURNAL_STATE_MISMATCH",
                        )
                        self.assertEqual(journal_path.read_bytes(), prepared)
                        self.assertEqual(journal_path.stat().st_ino, before.st_ino)
                        self.assertFalse(next_path.exists())
                journal_path.unlink()
                with self.assertRaises(storage.LifecycleStorageError) as raised:
                    entry(
                        workspace,
                        staged,
                        expected_previous_sha256=prepared_digest,
                    )
                self.assertEqual(
                    raised.exception.code,
                    "STORAGE_JOURNAL_STATE_MISMATCH",
                )
                self.assertFalse(next_path.exists())

    def test_journal_persistence_orders_verify_sync_replace_and_directory_sync(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "persist_serialized_journal", None)
        self.assertIsNotNone(entry)
        payload = b'{"phase":"planned"}\n'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            events = []
            replace_call = []
            synced_payload = []
            with storage.private_transaction_workspace(root, "txn-order") as workspace:
                real_write = storage.os.write
                real_read = storage.os.read
                real_fsync = storage.os.fsync
                real_replace = storage.os.replace

                def tracked_write(descriptor, value):
                    events.append("write")
                    return real_write(descriptor, value)

                def tracked_read(descriptor, size):
                    events.append("read")
                    return real_read(descriptor, size)

                def tracked_fsync(descriptor):
                    metadata = os.fstat(descriptor)
                    if stat.S_ISDIR(metadata.st_mode):
                        events.append("directory-fsync")
                    else:
                        events.append("file-fsync")
                        synced_payload.append(os.pread(descriptor, len(payload) + 1, 0))
                        self.assertEqual(stat.S_IMODE(metadata.st_mode), 0o600)
                        self.assertEqual(metadata.st_nlink, 1)
                    return real_fsync(descriptor)

                def tracked_replace(source, destination, **kwargs):
                    events.append("replace")
                    replace_call.append((source, destination, kwargs))
                    return real_replace(source, destination, **kwargs)

                with (
                    mock.patch.object(storage.os, "write", side_effect=tracked_write),
                    mock.patch.object(storage.os, "read", side_effect=tracked_read),
                    mock.patch.object(storage.os, "fsync", side_effect=tracked_fsync),
                    mock.patch.object(storage.os, "replace", side_effect=tracked_replace),
                ):
                    entry(
                        workspace,
                        payload,
                        expected_previous_sha256="absent",
                    )

                self.assertLess(events.index("write"), events.index("read"))
                self.assertLess(events.index("read"), events.index("file-fsync"))
                self.assertLess(events.index("file-fsync"), events.index("replace"))
                self.assertLess(events.index("replace"), events.index("directory-fsync"))
                self.assertEqual(synced_payload, [payload])
                self.assertEqual(
                    replace_call,
                    [
                        (
                            "journal.next",
                            "journal.json",
                            {
                                "src_dir_fd": workspace._workspace_fd,
                                "dst_dir_fd": workspace._workspace_fd,
                            },
                        )
                    ],
                )

    def test_journal_persistence_rejects_conflict_mutation_and_unknown_state_without_overwrite(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "persist_serialized_journal", None)
        self.assertIsNotNone(entry)
        planned = b'{"phase":"planned"}\n'
        staged = b'{"phase":"staged"}\n'

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            workspace_path = root / ".moduflow" / "transactions" / "txn-conflict"
            with storage.private_transaction_workspace(root, "txn-conflict") as workspace:
                next_path = workspace_path / "journal.next"
                next_path.write_bytes(b"foreign next")
                before = next_path.stat()
                with self.assertRaises(storage.LifecycleStorageError) as raised:
                    entry(
                        workspace,
                        planned,
                        expected_previous_sha256="absent",
                    )
                self.assertEqual(raised.exception.code, "STORAGE_CONFLICT")
                self.assertEqual(next_path.read_bytes(), b"foreign next")
                self.assertEqual(next_path.stat().st_ino, before.st_ino)

        for failure in ("mode", "hardlink"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                workspace_path = root / ".moduflow" / "transactions" / "txn-state"
                with storage.private_transaction_workspace(root, "txn-state") as workspace:
                    digest = entry(
                        workspace,
                        planned,
                        expected_previous_sha256="absent",
                    )
                    journal_path = workspace_path / "journal.json"
                    if failure == "mode":
                        journal_path.chmod(0o644)
                    else:
                        os.link(journal_path, workspace_path / "journal-link")
                    before = journal_path.stat()
                    with self.assertRaises(storage.LifecycleStorageError) as raised:
                        entry(
                            workspace,
                            staged,
                            expected_previous_sha256=digest,
                        )
                    self.assertEqual(
                        raised.exception.code,
                        "STORAGE_JOURNAL_STATE_MISMATCH",
                    )
                    self.assertEqual(journal_path.read_bytes(), planned)
                    self.assertEqual(journal_path.stat().st_ino, before.st_ino)
                    self.assertFalse((workspace_path / "journal.next").exists())

        for failure in ("deleted", "replaced", "symlink"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                workspace_path = root / ".moduflow" / "transactions" / "txn-race"
                journal_path = workspace_path / "journal.json"
                next_path = workspace_path / "journal.next"
                with storage.private_transaction_workspace(root, "txn-race") as workspace:
                    digest = entry(
                        workspace,
                        planned,
                        expected_previous_sha256="absent",
                    )
                    original_inode = journal_path.stat().st_ino
                    real_fsync = storage.os.fsync
                    changed = []

                    def mutate_after_temp_sync(descriptor):
                        result = real_fsync(descriptor)
                        if not changed and not stat.S_ISDIR(os.fstat(descriptor).st_mode):
                            journal_path.unlink()
                            if failure == "replaced":
                                journal_path.write_bytes(planned)
                                journal_path.chmod(0o600)
                            elif failure == "symlink":
                                external = root / "external-journal"
                                external.write_bytes(planned)
                                journal_path.symlink_to(external)
                            changed.append(True)
                        return result

                    with mock.patch.object(
                        storage.os,
                        "fsync",
                        side_effect=mutate_after_temp_sync,
                    ):
                        with self.assertRaises(storage.LifecycleStorageError) as raised:
                            entry(
                                workspace,
                                staged,
                                expected_previous_sha256=digest,
                            )
                    self.assertEqual(
                        raised.exception.code,
                        "STORAGE_JOURNAL_STATE_MISMATCH",
                    )
                    self.assertFalse(next_path.exists())
                    if failure == "deleted":
                        self.assertFalse(journal_path.exists())
                    elif failure == "replaced":
                        self.assertNotEqual(journal_path.stat().st_ino, original_inode)
                        self.assertEqual(journal_path.read_bytes(), planned)
                    else:
                        self.assertTrue(journal_path.is_symlink())

    def test_journal_persistence_cleans_exact_partial_but_preserves_durability_uncertainty(self):
        self.assertIsNotNone(storage)
        entry = getattr(storage, "persist_serialized_journal", None)
        self.assertIsNotNone(entry)
        payload = b'{"phase":"planned"}\n'
        for failure, expected_code, next_exists, journal_exists in (
            ("partial", "STORAGE_WRITE_FAILED", False, False),
            ("partial-cleanup-fsync", "STORAGE_DURABILITY_UNCERTAIN", False, False),
            ("corrupt", "STORAGE_VERIFY_FAILED", True, False),
            ("mode", "STORAGE_OWNER_MISMATCH", True, False),
            ("file-fsync", "STORAGE_DURABILITY_UNCERTAIN", True, False),
            ("replace", "STORAGE_WRITE_FAILED", False, False),
            ("result-identity", "STORAGE_DURABILITY_UNCERTAIN", False, True),
            ("directory-fsync", "STORAGE_DURABILITY_UNCERTAIN", False, True),
        ):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                workspace_path = root / ".moduflow" / "transactions" / "txn-failure"
                journal_path = workspace_path / "journal.json"
                next_path = workspace_path / "journal.next"
                with storage.private_transaction_workspace(
                    root,
                    "txn-failure",
                ) as workspace:
                    if failure in {"partial", "partial-cleanup-fsync", "corrupt"}:
                        real_write = storage.os.write
                        calls = []

                        def altered_write(descriptor, value):
                            calls.append(len(value))
                            if failure in {"partial", "partial-cleanup-fsync"}:
                                if len(calls) == 1:
                                    return real_write(descriptor, bytes(value[:3]))
                                raise OSError(5, "JOURNAL WRITE FAILURE")
                            return real_write(descriptor, b"x" * len(value))

                        if failure == "partial-cleanup-fsync":
                            patcher = mock.patch.multiple(
                                storage.os,
                                write=mock.Mock(side_effect=altered_write),
                                fsync=mock.Mock(
                                    side_effect=OSError(
                                        5,
                                        "JOURNAL CLEANUP SYNC FAILURE",
                                    )
                                ),
                            )
                        else:
                            patcher = mock.patch.object(
                                storage.os,
                                "write",
                                side_effect=altered_write,
                            )
                    elif failure in {"mode", "file-fsync", "directory-fsync"}:
                        real_fsync = storage.os.fsync
                        calls = []

                        def altered_fsync(descriptor):
                            calls.append(descriptor)
                            if failure == "mode" and len(calls) == 1:
                                result = real_fsync(descriptor)
                                next_path.chmod(0o644)
                                return result
                            if failure == "file-fsync" and len(calls) == 1:
                                raise OSError(5, "JOURNAL FILE SYNC FAILURE")
                            if failure == "directory-fsync" and len(calls) == 2:
                                raise OSError(5, "JOURNAL DIRECTORY SYNC FAILURE")
                            return real_fsync(descriptor)

                        patcher = mock.patch.object(
                            storage.os,
                            "fsync",
                            side_effect=altered_fsync,
                        )
                    elif failure == "replace":
                        patcher = mock.patch.object(
                            storage.os,
                            "replace",
                            side_effect=OSError(5, "JOURNAL REPLACE FAILURE"),
                        )
                    else:
                        real_replace = storage.os.replace

                        def replace_then_substitute(source, destination, **kwargs):
                            result = real_replace(source, destination, **kwargs)
                            journal_path.unlink()
                            journal_path.write_bytes(payload)
                            journal_path.chmod(0o600)
                            return result

                        patcher = mock.patch.object(
                            storage.os,
                            "replace",
                            side_effect=replace_then_substitute,
                        )
                    with patcher:
                        with self.assertRaises(storage.LifecycleStorageError) as raised:
                            entry(
                                workspace,
                                payload,
                                expected_previous_sha256="absent",
                            )
                    self.assertEqual(raised.exception.code, expected_code)
                    self.assertEqual(str(raised.exception), expected_code)
                    self.assertEqual(next_path.exists(), next_exists)
                    self.assertEqual(journal_path.exists(), journal_exists)
                    if journal_exists:
                        self.assertEqual(journal_path.read_bytes(), payload)

    def test_storage_target_is_detached_strict_and_side_effect_free(self):
        self.assertIsNotNone(storage)
        before = bytearray(b"before")
        after = bytearray(b"after")
        target = storage.StorageTarget(
            index=0,
            role="issue",
            relative_path="issues/BIZ-103.md",
            existed=True,
            before_sha256=hashlib.sha256(before).hexdigest(),
            after_sha256=hashlib.sha256(after).hexdigest(),
            after_size=len(after),
            changed=True,
            _before_bytes=before,
            _after_bytes=after,
        )
        before[:] = b"poison"
        after[:] = b"toxin"

        self.assertEqual(target._before_bytes, b"before")
        self.assertEqual(target._after_bytes, b"after")
        rendered = repr(target)
        self.assertNotIn("_before_bytes", rendered)
        self.assertNotIn("_after_bytes", rendered)
        self.assertNotIn("b'before'", rendered)
        self.assertNotIn("b'after'", rendered)

        invalid = (
            {"index": True},
            {"relative_path": "../escape"},
            {"before_sha256": "0" * 64},
            {"after_size": 999},
            {"changed": False},
        )
        with (
            mock.patch.object(storage.os, "open") as open_file,
            mock.patch.object(storage.os, "mkdir") as make_directory,
            mock.patch.object(storage.os, "fsync") as sync_file,
        ):
            for changes in invalid:
                with self.subTest(changes=changes):
                    with self.assertRaises(storage.LifecycleStorageError) as raised:
                        replace(target, **changes)
                    self.assertEqual(raised.exception.code, "STORAGE_CONTEXT_INVALID")
        open_file.assert_not_called()
        make_directory.assert_not_called()
        sync_file.assert_not_called()

    def test_workspace_stores_exact_preimages_with_restrictive_modes(self):
        self.assertIsNotNone(storage)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            targets = (
                self.target(0, existed=True, before=b"original issue"),
                self.target(1, existed=False, after=b"new evidence"),
            )

            with storage.private_transaction_workspace(root, "txn-123") as workspace:
                records = storage.store_preimages(workspace, targets)
                workspace_path = root / ".moduflow" / "transactions" / "txn-123"
                preimages = workspace_path / "preimages"
                self.assertEqual(stat.S_IMODE(workspace_path.stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE(preimages.stat().st_mode), 0o700)
                self.assertEqual(
                    stat.S_IMODE((preimages / "000000.bin").stat().st_mode),
                    0o600,
                )
                self.assertEqual(
                    (preimages / "000000.bin").read_bytes(),
                    b"original issue",
                )
                self.assertFalse((preimages / "000001.bin").exists())
                self.assertEqual(
                    [(record.index, record.state, record.relative_name) for record in records],
                    [
                        (0, "present", "preimages/000000.bin"),
                        (1, "absent", "absent"),
                    ],
                )
                self.assertFalse(hasattr(workspace, "root_fd"))
                self.assertNotIn(str(root), repr(workspace))

            self.assertTrue(workspace_path.is_dir())
            self.assertTrue((preimages / "000000.bin").is_file())

    def test_workspace_rejects_existing_and_unsafe_components_without_changes(self):
        self.assertIsNotNone(storage)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transactions = self.scaffold(root)
            existing = transactions / "txn-123"
            existing.mkdir()
            marker = existing / "marker"
            marker.write_bytes(b"private marker")
            before = marker.stat()

            with self.assertRaises(storage.LifecycleStorageError) as raised:
                with storage.private_transaction_workspace(root, "txn-123"):
                    self.fail("existing workspace must not be yielded")
            self.assertEqual(raised.exception.code, "STORAGE_CONFLICT")
            self.assertEqual(marker.read_bytes(), b"private marker")
            self.assertEqual(marker.stat().st_ino, before.st_ino)
            self.assertEqual(marker.stat().st_mtime_ns, before.st_mtime_ns)

        for component in (".moduflow", "transactions"):
            with self.subTest(component=component), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                if component == ".moduflow":
                    external = root / "external-control"
                    (external / "transactions").mkdir(parents=True)
                    (root / ".moduflow").symlink_to(
                        external,
                        target_is_directory=True,
                    )
                else:
                    control = root / ".moduflow"
                    control.mkdir()
                    external = root / "external-transactions"
                    external.mkdir()
                    (control / "transactions").symlink_to(
                        external,
                        target_is_directory=True,
                    )
                with self.assertRaises(storage.LifecycleStorageError) as raised:
                    with storage.private_transaction_workspace(root, "txn-123"):
                        self.fail("unsafe workspace must not be yielded")
                self.assertEqual(raised.exception.code, "STORAGE_PATH_UNSAFE")

    def test_partial_write_cleans_exact_owner_but_uncertainty_is_preserved(self):
        self.assertIsNotNone(storage)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            target = self.target(0, before=b"original issue")
            with storage.private_transaction_workspace(root, "txn-partial") as workspace:
                preimage = (
                    root
                    / ".moduflow"
                    / "transactions"
                    / "txn-partial"
                    / "preimages"
                    / "000000.bin"
                )
                real_write = storage.os.write
                calls = []

                def fail_after_prefix(descriptor, payload):
                    calls.append(len(payload))
                    if len(calls) == 1:
                        return real_write(descriptor, bytes(payload[:3]))
                    raise OSError(5, "PRIVATE WRITE FAILURE")

                with mock.patch.object(
                    storage.os,
                    "write",
                    side_effect=fail_after_prefix,
                ):
                    with self.assertRaises(storage.LifecycleStorageError) as raised:
                        storage.store_preimages(workspace, (target,))
                self.assertEqual(raised.exception.code, "STORAGE_WRITE_FAILED")
                self.assertNotIn("PRIVATE", str(raised.exception))
                self.assertFalse(preimage.exists())

        for failure in ("corrupt", "fsync"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                target = self.target(0, before=b"original issue")
                with storage.private_transaction_workspace(
                    root,
                    f"txn-{failure}",
                ) as workspace:
                    preimage = (
                        root
                        / ".moduflow"
                        / "transactions"
                        / f"txn-{failure}"
                        / "preimages"
                        / "000000.bin"
                    )
                    if failure == "corrupt":
                        real_write = storage.os.write

                        def corrupt_write(descriptor, payload):
                            return real_write(descriptor, b"x" * len(payload))

                        patcher = mock.patch.object(
                            storage.os,
                            "write",
                            side_effect=corrupt_write,
                        )
                        expected = "STORAGE_VERIFY_FAILED"
                    else:
                        patcher = mock.patch.object(
                            storage.os,
                            "fsync",
                            side_effect=OSError(5, "PRIVATE SYNC FAILURE"),
                        )
                        expected = "STORAGE_DURABILITY_UNCERTAIN"
                    with patcher:
                        with self.assertRaises(storage.LifecycleStorageError) as raised:
                            storage.store_preimages(workspace, (target,))
                    self.assertEqual(raised.exception.code, expected)
                    self.assertEqual(str(raised.exception), expected)
                    self.assertTrue(preimage.exists())


class CanonicalPreflightStorageTests(unittest.TestCase):
    def target(
        self,
        index,
        relative_path,
        *,
        existed=True,
        before=b"before",
        after=b"after",
        role="issue",
    ):
        if not existed:
            before = b""
        return storage.StorageTarget(
            index=index,
            role=role,
            relative_path=relative_path,
            existed=existed,
            before_sha256=(
                hashlib.sha256(before).hexdigest() if existed else "absent"
            ),
            after_sha256=hashlib.sha256(after).hexdigest(),
            after_size=len(after),
            changed=(not existed or before != after),
            _before_bytes=before,
            _after_bytes=after,
        )

    def scaffold(self, root):
        (root / "issues").mkdir()
        (root / "workspace" / "transactions").mkdir(parents=True)
        (root / "nested").mkdir()

    def test_verifies_present_absent_changed_and_unchanged_targets_once_without_mutation(self):
        entry = getattr(storage, "verify_canonical_preimages", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            issue = root / "issues" / "BIZ-103.md"
            stable = root / "nested" / "stable.md"
            evidence = root / "workspace" / "transactions" / "txn-103.json"
            issue.write_bytes(b"before")
            stable.write_bytes(b"stable")
            targets = (
                self.target(
                    0,
                    "issues/BIZ-103.md",
                    before=b"before",
                    after=b"after",
                ),
                self.target(
                    1,
                    "nested/stable.md",
                    before=b"stable",
                    after=b"stable",
                    role="dashboard",
                ),
                self.target(
                    2,
                    "workspace/transactions/txn-103.json",
                    existed=False,
                    after=b"evidence",
                    role="evidence",
                ),
            )
            before = (issue.read_bytes(), stable.read_bytes())
            real_open = storage.os.open
            opened_targets = []
            opened_flags = []

            def tracked_open(path, flags, *args, **kwargs):
                opened_flags.append(flags)
                if path in {"BIZ-103.md", "stable.md"}:
                    opened_targets.append(path)
                return real_open(path, flags, *args, **kwargs)

            with (
                mock.patch.object(storage.os, "open", side_effect=tracked_open),
                mock.patch.object(storage.os, "mkdir") as make_directory,
                mock.patch.object(storage.os, "write") as write_file,
                mock.patch.object(storage.os, "fsync") as sync_file,
                mock.patch.object(storage.os, "replace") as replace_file,
                mock.patch.object(storage.os, "unlink") as unlink_file,
            ):
                self.assertEqual(entry(root, targets), (0, 1, 2))

            no_follow = getattr(storage.os, "O_NOFOLLOW", 0)
            self.assertTrue(no_follow)
            self.assertTrue(all(flags & no_follow for flags in opened_flags))
            self.assertEqual(opened_targets, ["BIZ-103.md", "stable.md"])
            make_directory.assert_not_called()
            write_file.assert_not_called()
            sync_file.assert_not_called()
            replace_file.assert_not_called()
            unlink_file.assert_not_called()
            self.assertEqual((issue.read_bytes(), stable.read_bytes()), before)
            self.assertFalse(evidence.exists())

    def test_rejects_presence_bytes_type_and_parent_changes_with_first_target_index(self):
        entry = getattr(storage, "verify_canonical_preimages", None)
        self.assertIsNotNone(entry)
        scenarios = (
            "present-missing",
            "absent-present",
            "bytes-changed",
            "bytes-shortened",
            "bytes-expanded",
            "target-symlink",
            "target-directory",
            "parent-symlink",
            "parent-file",
        )
        for scenario in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                anchor = root / "issues" / "anchor.md"
                anchor.write_bytes(b"anchor")
                outside_file = root / "outside.md"
                outside_file.write_bytes(b"outside-file")
                outside_directory = root / "outside"
                outside_directory.mkdir()
                subject = root / "nested" / "subject.md"
                if scenario == "absent-present":
                    target = self.target(
                        1,
                        "nested/subject.md",
                        existed=False,
                    )
                    subject.write_bytes(b"foreign")
                else:
                    target = self.target(
                        1,
                        "nested/subject.md",
                        before=b"expected",
                    )
                    if scenario == "bytes-changed":
                        subject.write_bytes(b"changed!")
                    elif scenario == "bytes-shortened":
                        subject.write_bytes(b"short")
                    elif scenario == "bytes-expanded":
                        subject.write_bytes(b"expected-extra")
                    elif scenario == "target-symlink":
                        subject.symlink_to(outside_file)
                    elif scenario == "target-directory":
                        subject.mkdir()
                    elif scenario == "parent-symlink":
                        (root / "nested").rmdir()
                        (root / "nested").symlink_to(
                            outside_directory,
                            target_is_directory=True,
                        )
                    elif scenario == "parent-file":
                        (root / "nested").rmdir()
                        (root / "nested").write_bytes(b"blocked")
                targets = (
                    self.target(
                        0,
                        "issues/anchor.md",
                        before=b"anchor",
                        after=b"anchor",
                    ),
                    target,
                )

                with self.assertRaises(
                    storage.LifecycleCanonicalConflict
                ) as raised:
                    entry(root, targets)

                self.assertEqual(raised.exception.code, "CANONICAL_PREIMAGE_CONFLICT")
                self.assertEqual(raised.exception.target_index, 1)
                self.assertEqual(str(raised.exception), "CANONICAL_PREIMAGE_CONFLICT")
                self.assertEqual(
                    repr(raised.exception),
                    "LifecycleCanonicalConflict('CANONICAL_PREIMAGE_CONFLICT')",
                )
                self.assertEqual(anchor.read_bytes(), b"anchor")
                self.assertEqual(outside_file.read_bytes(), b"outside-file")
                self.assertTrue(outside_directory.is_dir())
                if scenario == "target-symlink":
                    self.assertTrue(subject.is_symlink())
                if scenario == "parent-symlink":
                    self.assertTrue((root / "nested").is_symlink())
                if scenario == "parent-file":
                    self.assertEqual((root / "nested").read_bytes(), b"blocked")

    def test_rejects_replacement_before_during_and_after_read_without_cleanup(self):
        entry = getattr(storage, "verify_canonical_preimages", None)
        self.assertIsNotNone(entry)
        for race_point in ("before-open", "during-read", "after-read"):
            with self.subTest(race_point=race_point), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.scaffold(root)
                issue = root / "issues" / "BIZ-103.md"
                replacement = root / "issues" / "replacement.md"
                issue.write_bytes(b"expected")
                replacement.write_bytes(b"foreign!")
                target = self.target(
                    0,
                    "issues/BIZ-103.md",
                    before=b"expected",
                )
                if race_point == "before-open":
                    real_open = storage.os.open

                    def raced_open(path, flags, *args, **kwargs):
                        if path == "BIZ-103.md" and replacement.exists():
                            replacement.replace(issue)
                        return real_open(path, flags, *args, **kwargs)

                    patcher = mock.patch.object(
                        storage.os,
                        "open",
                        side_effect=raced_open,
                    )
                elif race_point == "during-read":
                    real_read = storage.os.read
                    replaced = False

                    def raced_read(descriptor, size):
                        nonlocal replaced
                        if not replaced:
                            replaced = True
                            replacement.replace(issue)
                        return real_read(descriptor, size)

                    patcher = mock.patch.object(
                        storage.os,
                        "read",
                        side_effect=raced_read,
                    )
                else:
                    real_stat = storage.os.stat
                    final_stats = 0

                    def raced_stat(path, *args, **kwargs):
                        nonlocal final_stats
                        if (
                            path == "BIZ-103.md"
                            and kwargs.get("follow_symlinks") is False
                        ):
                            final_stats += 1
                            if final_stats == 2:
                                replacement.replace(issue)
                        return real_stat(path, *args, **kwargs)

                    patcher = mock.patch.object(
                        storage.os,
                        "stat",
                        side_effect=raced_stat,
                    )

                with patcher:
                    with self.assertRaises(
                        storage.LifecycleCanonicalConflict
                    ) as raised:
                        entry(root, (target,))

                self.assertEqual(raised.exception.code, "CANONICAL_PREIMAGE_CONFLICT")
                self.assertEqual(raised.exception.target_index, 0)
                self.assertEqual(issue.read_bytes(), b"foreign!")
                self.assertFalse(replacement.exists())

    def test_rejects_invalid_inputs_before_reads_and_redacts_filesystem_failures(self):
        entry = getattr(storage, "verify_canonical_preimages", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory(prefix="SECRET-ROOT-") as tmp:
            root = Path(tmp)
            self.scaffold(root)
            valid = self.target(
                0,
                "issues/SECRET-PATH.md",
                before=b"SECRET-BYTES",
            )
            gap = self.target(
                1,
                "issues/SECRET-PATH.md",
                before=b"SECRET-BYTES",
            )
            invalid_inputs = (
                (Path("relative-root"), (valid,)),
                (root, [valid]),
                (root, (gap,)),
                (root, ()),
            )
            with mock.patch.object(storage.os, "open") as open_file:
                for candidate_root, candidate_targets in invalid_inputs:
                    with self.assertRaises(storage.LifecycleStorageError) as raised:
                        entry(candidate_root, candidate_targets)
                    self.assertEqual(raised.exception.code, "STORAGE_CONTEXT_INVALID")
                open_file.assert_not_called()

            for invalid_index in (-1, True, "0"):
                with self.assertRaises(storage.LifecycleStorageError) as raised:
                    storage.LifecycleCanonicalConflict(invalid_index)
                self.assertEqual(raised.exception.code, "STORAGE_CONTEXT_INVALID")

            with mock.patch.object(
                storage.os,
                "open",
                side_effect=OSError(13, "SECRET-OS-ERROR"),
            ):
                with self.assertRaises(
                    storage.LifecycleCanonicalConflict
                ) as raised:
                    entry(root, (valid,))
            rendered = f"{raised.exception!s} {raised.exception!r}"
            self.assertEqual(raised.exception.target_index, 0)
            self.assertIsNone(raised.exception.__cause__)
            for secret in (
                "SECRET-PATH",
                "SECRET-BYTES",
                "SECRET-OS-ERROR",
                str(root),
            ):
                self.assertNotIn(secret, rendered)


class CanonicalApplyStorageTests(unittest.TestCase):
    def target(
        self,
        index,
        relative_path,
        *,
        existed=True,
        before=b"before",
        after=b"after",
        role="issue",
    ):
        if not existed:
            before = b""
        return storage.StorageTarget(
            index=index,
            role=role,
            relative_path=relative_path,
            existed=existed,
            before_sha256=(
                hashlib.sha256(before).hexdigest() if existed else "absent"
            ),
            after_sha256=hashlib.sha256(after).hexdigest(),
            after_size=len(after),
            changed=(not existed or before != after),
            _before_bytes=before,
            _after_bytes=after,
        )

    def scaffold(self, root):
        (root / "issues").mkdir()
        (root / "new").mkdir()
        (root / ".moduflow" / "transactions").mkdir(parents=True)

    def test_promotes_existing_and_absent_targets_with_descriptor_replace_and_0600_mode(self):
        entry = getattr(storage, "apply_staged_target", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            issue = root / "issues" / "BIZ-103.md"
            created = root / "new" / "created.json"
            unrelated = root / "issues" / "unrelated.md"
            issue.write_bytes(b"original issue")
            unrelated.write_bytes(b"untouched")
            targets = (
                self.target(
                    0,
                    "issues/BIZ-103.md",
                    before=b"original issue",
                    after=b"proposed issue",
                ),
                self.target(
                    1,
                    "new/created.json",
                    existed=False,
                    after=b"new file",
                    role="state",
                ),
            )
            with storage.private_transaction_workspace(
                root,
                "txn-apply-success",
            ) as workspace:
                preimages = storage.store_preimages(workspace, targets)
                proposals = storage.stage_proposed_targets(workspace, targets)
                storage.finalize_recovery_manifest(
                    workspace,
                    targets,
                    preimages,
                    proposals,
                )
                with (
                    mock.patch.object(
                        storage.os,
                        "replace",
                        wraps=storage.os.replace,
                    ) as replace_file,
                    mock.patch.object(
                        storage.os,
                        "fsync",
                        wraps=storage.os.fsync,
                    ) as sync_file,
                ):
                    self.assertEqual(entry(workspace, targets[0], proposals[0]), 0)
                    self.assertEqual(entry(workspace, targets[1], proposals[1]), 1)

                self.assertEqual(replace_file.call_count, 2)
                self.assertGreaterEqual(sync_file.call_count, 2)
                for call in replace_file.call_args_list:
                    self.assertIsInstance(call.kwargs["src_dir_fd"], int)
                    self.assertEqual(
                        call.kwargs["src_dir_fd"],
                        call.kwargs["dst_dir_fd"],
                    )
                for proposal in proposals:
                    self.assertFalse((root / proposal.relative_name).exists())

            self.assertEqual(issue.read_bytes(), b"proposed issue")
            self.assertEqual(created.read_bytes(), b"new file")
            self.assertEqual(stat.S_IMODE(issue.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(created.stat().st_mode), 0o600)
            self.assertEqual(unrelated.read_bytes(), b"untouched")

    def test_reverifies_unchanged_target_without_replace_or_sync(self):
        entry = getattr(storage, "verify_canonical_target", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            canonical = root / "issues" / "stable.md"
            canonical.write_bytes(b"stable")
            target = self.target(
                0,
                "issues/stable.md",
                before=b"stable",
                after=b"stable",
            )
            with storage.private_transaction_workspace(
                root,
                "txn-apply-unchanged",
            ) as workspace:
                proposals = storage.stage_proposed_targets(workspace, (target,))
                with (
                    mock.patch.object(storage.os, "replace") as replace_file,
                    mock.patch.object(storage.os, "fsync") as sync_file,
                ):
                    self.assertEqual(entry(workspace, target), 0)
                replace_file.assert_not_called()
                sync_file.assert_not_called()
                self.assertEqual(proposals[0].state, "unchanged")
            self.assertEqual(canonical.read_bytes(), b"stable")

    def test_rejects_invalid_or_unowned_proposals_before_canonical_replace(self):
        entry = getattr(storage, "apply_staged_target", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            issue = root / "issues" / "BIZ-103.md"
            issue.write_bytes(b"original issue")
            target = self.target(
                0,
                "issues/BIZ-103.md",
                before=b"original issue",
                after=b"proposed issue",
            )
            evidence = self.target(
                0,
                "new/evidence.json",
                existed=False,
                after=b"evidence",
                role="evidence",
            )
            stable = self.target(
                0,
                "issues/BIZ-103.md",
                before=b"original issue",
                after=b"original issue",
            )
            with storage.private_transaction_workspace(
                root,
                "txn-apply-invalid",
            ) as workspace:
                proposal = storage.stage_proposed_targets(workspace, (target,))[0]
                evidence_proposal = storage.stage_proposed_targets(
                    workspace,
                    (evidence,),
                )[0]
                unchanged = storage.StagedProposal(
                    index=0,
                    state="unchanged",
                    relative_name="unchanged",
                    size=0,
                    sha256="unchanged",
                    _device=-1,
                    _inode=-1,
                )
                invalid = (
                    (target, replace(proposal, index=False)),
                    (evidence, evidence_proposal),
                    (stable, unchanged),
                    (target, replace(proposal, index=1)),
                    (target, replace(proposal, state="unchanged")),
                    (target, replace(proposal, relative_name="wrong-stage")),
                    (target, replace(proposal, size=1)),
                    (target, replace(proposal, sha256="0" * 64)),
                    (target, replace(proposal, _device=-1)),
                    (target, replace(proposal, _device="device")),
                    (target, replace(proposal, _inode=-1)),
                    (target, replace(proposal, _inode=True)),
                )
                with mock.patch.object(storage.os, "replace") as replace_file:
                    for candidate_target, candidate_proposal in invalid:
                        with self.subTest(value=repr(candidate_proposal)):
                            with self.assertRaises(
                                storage.LifecycleStorageError
                            ) as raised:
                                entry(
                                    workspace,
                                    candidate_target,
                                    candidate_proposal,
                                )
                            self.assertEqual(
                                raised.exception.code,
                                "STORAGE_CONTEXT_INVALID",
                            )
                replace_file.assert_not_called()
                self.assertEqual(issue.read_bytes(), b"original issue")
                self.assertTrue((root / proposal.relative_name).is_file())

    def test_rejects_canonical_conflict_and_retains_staged_proposal(self):
        entry = getattr(storage, "apply_staged_target", None)
        self.assertIsNotNone(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.scaffold(root)
            issue = root / "issues" / "BIZ-103.md"
            issue.write_bytes(b"original issue")
            target = self.target(
                0,
                "issues/BIZ-103.md",
                before=b"original issue",
                after=b"proposed issue",
            )
            with storage.private_transaction_workspace(
                root,
                "txn-apply-conflict",
            ) as workspace:
                preimages = storage.store_preimages(workspace, (target,))
                proposals = storage.stage_proposed_targets(workspace, (target,))
                storage.finalize_recovery_manifest(
                    workspace,
                    (target,),
                    preimages,
                    proposals,
                )
                stage_path = root / proposals[0].relative_name
                issue.write_bytes(b"external edit")
                with mock.patch.object(storage.os, "replace") as replace_file:
                    with self.assertRaises(
                        storage.LifecycleCanonicalConflict
                    ) as raised:
                        entry(workspace, target, proposals[0])
                self.assertEqual(raised.exception.code, "CANONICAL_PREIMAGE_CONFLICT")
                self.assertEqual(raised.exception.target_index, 0)
                replace_file.assert_not_called()
                self.assertEqual(issue.read_bytes(), b"external edit")
                self.assertTrue(stage_path.is_file())

    def test_bounds_replace_and_parent_sync_failures_without_cleanup_or_retry(self):
        entry = getattr(storage, "apply_staged_target", None)
        self.assertIsNotNone(entry)
        for failure, expected_code in (
            ("replace", "STORAGE_REPLACE_FAILED"),
            ("parent-fsync", "STORAGE_DURABILITY_UNCERTAIN"),
        ):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory(
                prefix="SECRET-APPLY-ROOT-"
            ) as tmp:
                root = Path(tmp)
                self.scaffold(root)
                issue = root / "issues" / "SECRET-PATH.md"
                issue.write_bytes(b"SECRET-BEFORE")
                target = self.target(
                    0,
                    "issues/SECRET-PATH.md",
                    before=b"SECRET-BEFORE",
                    after=b"SECRET-AFTER",
                )
                workspace_path = (
                    root / ".moduflow" / "transactions" / f"txn-{failure}"
                )
                with storage.private_transaction_workspace(
                    root,
                    f"txn-{failure}",
                ) as workspace:
                    preimages = storage.store_preimages(workspace, (target,))
                    proposals = storage.stage_proposed_targets(workspace, (target,))
                    manifest = storage.finalize_recovery_manifest(
                        workspace,
                        (target,),
                        preimages,
                        proposals,
                    )
                    stage_path = root / proposals[0].relative_name
                    if failure == "replace":
                        patcher = mock.patch.object(
                            storage.os,
                            "replace",
                            side_effect=OSError(5, "SECRET REPLACE ERROR"),
                        )
                    else:
                        patcher = mock.patch.object(
                            storage.os,
                            "fsync",
                            side_effect=OSError(5, "SECRET FSYNC ERROR"),
                        )
                    with patcher as operation:
                        with self.assertRaises(
                            storage.LifecycleStorageError
                        ) as raised:
                            entry(workspace, target, proposals[0])
                    self.assertEqual(raised.exception.code, expected_code)
                    self.assertEqual(operation.call_count, 1)
                    rendered = f"{raised.exception!s} {raised.exception!r}"
                    for secret in (
                        str(root),
                        "SECRET-PATH",
                        "SECRET-BEFORE",
                        "SECRET-AFTER",
                        "SECRET REPLACE ERROR",
                        "SECRET FSYNC ERROR",
                        proposals[0].relative_name,
                        str(proposals[0]._device),
                        str(proposals[0]._inode),
                    ):
                        self.assertNotIn(secret, rendered)
                    self.assertTrue(workspace_path.is_dir())
                    self.assertTrue(
                        (workspace_path / "recovery-manifest.json").is_file()
                    )
                    self.assertEqual(
                        (workspace_path / preimages[0].relative_name).read_bytes(),
                        b"SECRET-BEFORE",
                    )
                    manifest_bytes = (
                        workspace_path / "recovery-manifest.json"
                    ).read_bytes()
                    self.assertEqual(
                        hashlib.sha256(manifest_bytes).hexdigest(),
                        manifest.sha256,
                    )
                    if failure == "replace":
                        self.assertEqual(issue.read_bytes(), b"SECRET-BEFORE")
                        self.assertTrue(stage_path.is_file())
                    else:
                        self.assertEqual(issue.read_bytes(), b"SECRET-AFTER")
                        self.assertFalse(stage_path.exists())


if __name__ == "__main__":
    unittest.main()
