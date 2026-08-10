#!/usr/bin/env python3
"""Download only the approved Spec Kit command snapshots after hash verification."""

import argparse
import hashlib
import os
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


class SpecKitSyncError(ValueError):
    """A safe-to-display synchronization failure."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f"{code}: {message}")


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


def sync_templates(package_root, downloader, *, write=False):
    """Validate all four downloads before optionally replacing any destination files."""
    package_root = Path(package_root).resolve()
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
        records = [
            {
                "function": function,
                "path": f"vendor/spec-kit/0.16.1/commands/{function}.md",
                "sha256": EXPECTED_HASHES[function],
            }
            for function in ALLOWED_PATHS
        ]
        if write:
            destination = package_root / "vendor" / "spec-kit" / "0.16.1" / "commands"
            if destination.exists() and {
                path.name for path in destination.iterdir()
            } - {f"{function}.md" for function in ALLOWED_PATHS}:
                raise SpecKitSyncError("invalid_destination", "destination has unapproved templates")
            destination.mkdir(parents=True, exist_ok=True)
            for function, staged in downloaded.items():
                os.replace(staged, destination / f"{function}.md")
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
