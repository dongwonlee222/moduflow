"""Synthetic package evidence, deliberately separate from full distributions."""
import json
from pathlib import Path


def make_package(root, *, version="0.0.1", receipt=None):
    root = Path(root)
    manifest = root / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"name": "moduflow", "version": version}), encoding="utf-8")
    if receipt is not None:
        (root / ".moduflow-package.json").write_text(json.dumps(receipt), encoding="utf-8")
    return root


def receipt_for(version="0.0.1"):
    return {
        "schema": "moduflow.package-provenance.v1",
        "package_version": version,
        "source_commit": "a" * 40,
        "source_dirty": False,
        "installed_at": "2026-09-02T00:00:00Z",
        "payload_sha256": "b" * 64,
        "provenance_source": {key: "test-fixture" for key in (
            "package_version", "source_commit", "source_dirty", "installed_at", "payload_sha256")},
        "unavailable_reasons": {},
    }
