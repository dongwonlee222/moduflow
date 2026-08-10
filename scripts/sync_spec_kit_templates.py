#!/usr/bin/env python3
"""Download only the approved Spec Kit command snapshots after hash verification."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path


APPROVED_SHA = "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"
ALLOWED_PATHS = {
    "clarify": "templates/commands/clarify.md",
    "analyze": "templates/commands/analyze.md",
    "checklist": "templates/commands/checklist.md",
    "converge": "templates/commands/converge.md",
}
EXPECTED_HASHES = {
    "clarify": "9fce9b3dfe037b67f52486df112f89377ff6c0c598698131cde65cec610b5bba",
    "analyze": "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
    "checklist": "0a862264b9b358138d6049590d42b392ee4dadb69d32811d460620f077924d4e",
    "converge": "aafba511dea42334373c7ffb9f58e2fb6d82889ea94ec86c1367dbb6a531ca36",
}
FALLBACKS = {
    "clarify": "moduflow_short_clarification",
    "analyze": "scripts/spec_consistency.py",
    "checklist": "moduflow_acceptance_readiness",
    "converge": "scripts/project_converge.py --report-only",
}


class SpecKitSyncError(ValueError):
    """A safe-to-display synchronization failure."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f"{code}: {message}")


def _safe_package_path(package_root, *parts):
    root = Path(package_root).resolve()
    candidate = root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise SpecKitSyncError("unsafe_path", "Spec Kit destination must not contain symlinks")
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise SpecKitSyncError("unsafe_path", "Spec Kit destination escapes package root") from exc
    return candidate


def _manifest_payload():
    return {
        "schema": "moduflow.spec-kit-manifest.v1",
        "source": {
            "repository": "github/spec-kit",
            "version": "0.16.1",
            "sha": APPROVED_SHA,
        },
        "functions": {
            function: {
                "template": f"commands/{function}.md",
                "sha256": EXPECTED_HASHES[function],
                "fallback": FALLBACKS[function],
            }
            for function in ALLOWED_PATHS
        },
    }


def _validate_staged_version(version_root):
    manifest_path = version_root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecKitSyncError("invalid_snapshot", "staged manifest cannot be read") from exc
    if manifest != _manifest_payload():
        raise SpecKitSyncError("invalid_snapshot", "staged manifest is not approved")
    expected_paths = {"manifest.json"} | {
        f"commands/{function}.md" for function in ALLOWED_PATHS
    }
    actual_paths = {
        path.relative_to(version_root).as_posix()
        for path in version_root.rglob("*")
        if path.is_file()
    }
    if actual_paths != expected_paths:
        raise SpecKitSyncError("invalid_snapshot", "staged snapshot does not contain exactly approved files")
    for function in ALLOWED_PATHS:
        content = (version_root / "commands" / f"{function}.md").read_bytes()
        if hashlib.sha256(content).hexdigest() != EXPECTED_HASHES[function]:
            raise SpecKitSyncError("hash_mismatch", "staged template hash did not match")


def _remove_tree(path):
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.exists():
        shutil.rmtree(path)


def fetch_snapshot(downloader, function):
    source_path = ALLOWED_PATHS[function]
    url = f"https://raw.githubusercontent.com/github/spec-kit/{APPROVED_SHA}/{source_path}"
    try:
        content = downloader(url)
    except OSError as exc:
        raise SpecKitSyncError("download_failed", "approved template download failed") from exc
    if not isinstance(content, bytes):
        raise SpecKitSyncError("download_failed", "approved template download was not bytes")
    return content


def sync_templates(package_root, downloader, *, write=False, replacer=None):
    """Validate all four downloads before optionally replacing any destination files."""
    package_root = Path(package_root).resolve()
    version_root = _safe_package_path(
        package_root, "vendor", "spec-kit", "0.16.1"
    )
    _safe_package_path(package_root, "vendor", "spec-kit", "0.16.1", "commands")
    replacer = os.replace if replacer is None else replacer
    downloaded = {}
    with tempfile.TemporaryDirectory() as temporary:
        staging = Path(temporary)
        for function in ALLOWED_PATHS:
            content = fetch_snapshot(downloader, function)
            actual = hashlib.sha256(content).hexdigest()
            if actual != EXPECTED_HASHES[function]:
                raise SpecKitSyncError("hash_mismatch", "approved template hash did not match")
            path = staging / f"{function}.md"
            path.write_bytes(content)
            downloaded[function] = path
        if set(downloaded) != set(ALLOWED_PATHS):
            raise SpecKitSyncError("invalid_snapshot", "snapshot does not contain exactly four templates")
        staged_version = staging / "0.16.1"
        staged_commands = staged_version / "commands"
        staged_commands.mkdir(parents=True)
        (staged_version / "manifest.json").write_text(
            json.dumps(_manifest_payload(), indent=2) + "\n", encoding="utf-8"
        )
        for function, source in downloaded.items():
            shutil.copyfile(source, staged_commands / f"{function}.md")
        _validate_staged_version(staged_version)
        records = [
            {
                "function": function,
                "path": f"vendor/spec-kit/0.16.1/commands/{function}.md",
                "sha256": EXPECTED_HASHES[function],
            }
            for function in ALLOWED_PATHS
        ]
        if write:
            version_parent = _safe_package_path(package_root, "vendor", "spec-kit")
            version_parent.mkdir(parents=True, exist_ok=True)
            version_root = _safe_package_path(
                package_root, "vendor", "spec-kit", "0.16.1"
            )
            _safe_package_path(package_root, "vendor", "spec-kit", "0.16.1", "commands")
            with tempfile.TemporaryDirectory(prefix=".spec-kit-sync-", dir=version_parent) as transaction:
                transaction_root = Path(transaction)
                pending = transaction_root / "0.16.1"
                shutil.copytree(staged_version, pending)
                _validate_staged_version(pending)
                backup = transaction_root / "previous-0.16.1"
                had_previous = version_root.exists()
                try:
                    if had_previous:
                        replacer(version_root, backup)
                    replacer(pending, version_root)
                except Exception as exc:
                    try:
                        if backup.exists():
                            _remove_tree(version_root)
                            os.replace(backup, version_root)
                        elif not had_previous:
                            _remove_tree(version_root)
                    except OSError as rollback_exc:
                        raise SpecKitSyncError(
                            "rollback_failed", "could not restore the prior Spec Kit snapshot"
                        ) from rollback_exc
                    raise SpecKitSyncError(
                        "commit_failed", "could not replace the Spec Kit snapshot"
                    ) from exc
                _remove_tree(backup)
    return records


def _urlopen_downloader(url):
    from urllib.request import urlopen

    with urlopen(url) as response:
        return response.read()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync pinned Spec Kit command templates")
    parser.add_argument("package_root", nargs="?", default=".")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    records = sync_templates(args.package_root, _urlopen_downloader, write=args.write)
    for record in records:
        print(f"{record['function']}: {record['sha256']} {record['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
