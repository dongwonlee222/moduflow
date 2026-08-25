import hashlib
import importlib
import importlib.util
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

    def target(self, index=0, *, existed=True, before=b"before", after=b"after"):
        if not existed:
            before = b""
        return storage.StorageTarget(
            index=index,
            role="issue" if index == 0 else "evidence",
            relative_path=(
                "issues/BIZ-103.md"
                if index == 0
                else ".moduflow/evidence/BIZ-103.json"
            ),
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


if __name__ == "__main__":
    unittest.main()
