"""Synthetic package evidence, deliberately separate from full distributions."""
import json
import shutil
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


def make_distribution(root, *, version="0.2.0"):
    from scripts.validate_moduflow import REQUIRED_FILES, SOURCE_ONLY_REQUIRED_FILES
    root = Path(root)
    source = Path(__file__).resolve().parents[1]
    for name in REQUIRED_FILES:
        if name not in SOURCE_ONLY_REQUIRED_FILES:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, target)
    # Runtime imports include helpers beyond the required-entrypoint inventory.
    shutil.copytree(source / "scripts", root / "scripts", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    make_package(root, version=version)
    codex = root / ".codex-plugin/plugin.json"
    codex.parent.mkdir(exist_ok=True)
    codex.write_text(json.dumps({"name": "moduflow", "version": version + "+codex.test"}))
    return root
