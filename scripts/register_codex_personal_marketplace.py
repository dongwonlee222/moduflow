#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts import runtime_provenance, validate_moduflow, linkage_check
except ImportError:
    import runtime_provenance
    import validate_moduflow
    import linkage_check


PLUGIN_NAME = "moduflow"
MARKETPLACE_NAME = "personal"
PLUGIN_CACHE_EXCLUDES = (
    ".git",
    "__pycache__",
    ".pytest_cache",
    "*.pyc",
)
TOP_LEVEL_CACHE_EXCLUDES = {"issues", "specs", "tests", "sessions"}
RUNTIME_TEST_FIXTURES = (
    "tests/fixtures/issue-schema/BIZ-033.md",
    "tests/fixtures/issue-schema/BIZ-038.md",
    "tests/fixtures/issue-schema/BIZ-039.md",
    "tests/fixtures/issue-schema/BIZ-040.md",
    "tests/fixtures/issue-schema/legacy-markdown.md",
    "tests/fixtures/project-registry/projects-v1.json",
    "tests/fixtures/project-registry/projects-v2.json",
    "tests/fixtures/project-registry/projects-v2-alias-collision.json",
    "tests/fixtures/capability-routing/cases.json",
    "tests/fixtures/spec-kit-selective-validation/cases.json",
    "tests/fixtures/spec-kit-selective-validation/results/clarify.json",
    "tests/fixtures/spec-kit-selective-validation/results/analyze.json",
    "tests/fixtures/spec-kit-selective-validation/results/checklist.json",
    "tests/fixtures/spec-kit-selective-validation/results/converge.json",
)
RUNTIME_EVIDENCE_FILES = (
    "specs/098-speckit-selective-validation-adapter/pilot-report.md",
    "specs/098-speckit-selective-validation-adapter/status.md",
)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {
            "name": "personal",
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def ensure_plugin_link(source: Path, link: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        current = Path(os.readlink(link))
        if current == source:
            return
        link.unlink()
    elif link.exists():
        raise RuntimeError(f"{link} exists and is not a symlink; refusing to overwrite")
    link.symlink_to(source)


def ensure_marketplace_entry(marketplace_path: Path, installation_policy: str = "INSTALLED_BY_DEFAULT") -> None:
    marketplace = read_json(marketplace_path)
    marketplace.setdefault("name", MARKETPLACE_NAME)
    marketplace.setdefault("interface", {"displayName": "Personal"})
    marketplace.setdefault("plugins", [])

    entry = {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_NAME}",
        },
        "policy": {
            "installation": installation_policy,
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }

    plugins = marketplace["plugins"]
    for index, plugin in enumerate(plugins):
        if plugin.get("name") == PLUGIN_NAME:
            plugins[index] = entry
            break
    else:
        plugins.append(entry)

    write_json(marketplace_path, marketplace)


def canonical_base(source: Path) -> str:
    """Resolve the plugin base version from the single source of truth.

    `.claude-plugin/plugin.json` is canonical. When it is absent (e.g. in
    tests), fall back to the base of the Codex manifest version.
    """
    claude_manifest = read_json(source / ".claude-plugin" / "plugin.json")
    version = claude_manifest.get("version")
    if isinstance(version, str) and version:
        return version
    codex_version = read_json(source / ".codex-plugin" / "plugin.json").get("version", "")
    return codex_version.split("+", 1)[0]


def plugin_version(source: Path) -> str:
    base = canonical_base(source)
    if not base:
        raise RuntimeError("Unable to determine plugin base version")
    codex_manifest_path = source / ".codex-plugin" / "plugin.json"
    manifest = read_json(codex_manifest_path)
    existing = manifest.get("version", "")
    # Preserve any existing Codex build suffix (e.g. "+codex.<timestamp>")
    # so the resulting version stays deterministic, but sync the base.
    suffix = existing.split("+", 1)[1] if "+" in existing else ""
    version = f"{base}+{suffix}" if suffix else base
    return version


def build_package_provenance(source, payload_root, *, version, installed_at, runner):
    sources = {"package_version": "distribution_manifest", "installed_at": "installer_clock",
               "payload_sha256": "prepared_payload"}
    reasons = {}
    revision, dirty = None, None
    if not (Path(source) / ".git").exists():
        reasons.update(source_commit="source_not_git_checkout", source_dirty="source_not_git_checkout")
    else:
        for field, args in (("source_commit", ["git", "rev-parse", "HEAD"]),
                            ("source_dirty", ["git", "status", "--porcelain", "--untracked-files=normal"])):
            try:
                outcome = runner(args, source, timeout=5)
                code = outcome["returncode"] if isinstance(outcome, dict) else outcome.returncode
                output = outcome.get("stdout", "") if isinstance(outcome, dict) else outcome.stdout
                if code != 0 or not isinstance(output, str):
                    reasons[field] = "source_git_observation_failed"
                elif field == "source_commit":
                    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", output.strip()):
                        revision = output.strip()
                        sources[field] = "git_head"
                    else:
                        reasons[field] = "source_git_revision_invalid"
                else:
                    dirty = bool(output.strip())
                    sources[field] = "git_status"
            except (OSError, ValueError, TypeError, AttributeError, KeyError) as exc:
                reasons[field] = f"source_git_observation_failed:{type(exc).__name__}"
    return {"schema": runtime_provenance.RECEIPT_SCHEMA, "package_version": version,
            "source_commit": revision, "source_dirty": dirty, "installed_at": installed_at,
            "payload_sha256": runtime_provenance.package_payload_sha256(payload_root),
            "provenance_source": sources, "unavailable_reasons": reasons}


def write_package_provenance(staging_root, receipt):
    staging_root = Path(staging_root)
    fd, name = tempfile.mkstemp(prefix=".receipt-", dir=staging_root)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(receipt, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, staging_root / runtime_provenance.RECEIPT_NAME)
        directory_fd = os.open(staging_root, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def copy_plugin_cache(source: Path, home: Path, version: str, *, runner=None, installed_at=None) -> Path:
    source = source.resolve()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][a-zA-Z0-9.+-]+)?", version):
        raise ValueError("invalid package version path")
    if version.split("+", 1)[0] != canonical_base(source).split("+", 1)[0]:
        raise ValueError("distribution version must match canonical source base")
    cache_root = Path(home).resolve()
    for segment in (".codex", "plugins", "cache", MARKETPLACE_NAME, PLUGIN_NAME):
        cache_root = cache_root / segment
        if cache_root.is_symlink():
            raise RuntimeError("PACKAGE_DESTINATION_CONFLICT: cache ancestor is a symlink")
    destination = cache_root / version
    if destination.is_symlink() or destination.resolve().is_relative_to(source):
        raise RuntimeError("PACKAGE_DESTINATION_CONFLICT: unsafe cache destination")
    cache_root.mkdir(parents=True, exist_ok=True)
    base_ignore = shutil.ignore_patterns(*PLUGIN_CACHE_EXCLUDES)

    def ignore(directory, names):
        ignored = set(base_ignore(directory, names))
        if Path(directory).resolve() == source:
            ignored.update(name for name in names if name in TOP_LEVEL_CACHE_EXCLUDES)
            ignored.add(runtime_provenance.RECEIPT_NAME)
        return ignored

    stage = Path(tempfile.mkdtemp(prefix=".prepare-", dir=cache_root))
    try:
        shutil.copytree(source, stage, ignore=ignore, dirs_exist_ok=True, symlinks=True)
        # Reject links before any prepared-manifest write can follow them outside staging.
        runtime_provenance.package_payload_sha256(stage)
        for relative_path in (*RUNTIME_TEST_FIXTURES, *RUNTIME_EVIDENCE_FILES):
            source_file = source / relative_path
            if not source_file.is_file():
                continue
            destination_file = stage / relative_path
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination_file, follow_symlinks=False)
        codex_manifest = read_json(stage / ".codex-plugin/plugin.json")
        codex_manifest.update(name=PLUGIN_NAME, version=version)
        write_json(stage / ".codex-plugin/plugin.json", codex_manifest)
        receipt = build_package_provenance(source, stage, version=version,
            installed_at=installed_at or datetime.now(timezone.utc).isoformat(),
            runner=runner or linkage_check.run_command)
        write_package_provenance(stage, receipt)
        validation = validate_moduflow.validate_moduflow(stage, mode="installed")
        if not validation["valid"]:
            raise RuntimeError("PACKAGE_VALIDATION_FAILED: " + "; ".join(validation["errors"]))
        if destination.exists():
            existing = runtime_provenance.inspect_package(destination)
            existing_validation = validate_moduflow.validate_moduflow(destination, mode="installed")
            same_identity = all(existing.get(key) == receipt[key] for key in
                                ("package_version", "payload_sha256", "source_commit", "source_dirty"))
            if not existing_validation["valid"] or existing["receipt_state"] != "valid" or not same_identity:
                raise RuntimeError("PACKAGE_DESTINATION_CONFLICT: existing package differs")
            return destination
        # Rename publishes only a fully prepared package; no existing cache is removed.
        stage.rename(destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return destination


def ensure_codex_local_link(source: Path, home: Path) -> Path:
    link = home / ".codex" / "plugins" / "local" / PLUGIN_NAME
    ensure_plugin_link(source, link)
    return link


def ensure_codex_plugin_enabled(config_path: Path) -> None:
    section = f'[plugins."{PLUGIN_NAME}@{MARKETPLACE_NAME}"]'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config_path.write_text(f"{section}\nenabled = true\n", encoding="utf-8")
        return

    text = config_path.read_text(encoding="utf-8")
    if section not in text:
        suffix = "" if text.endswith("\n") else "\n"
        config_path.write_text(f"{text}{suffix}\n{section}\nenabled = true\n", encoding="utf-8")
        return

    lines = text.splitlines()
    in_section = False
    enabled_seen = False
    output = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_section and not enabled_seen:
                output.append("enabled = true")
            in_section = stripped == section
            enabled_seen = False
        if in_section and stripped.startswith("enabled"):
            output.append("enabled = true")
            enabled_seen = True
            continue
        output.append(line)
    if in_section and not enabled_seen:
        output.append("enabled = true")
    config_path.write_text("\n".join(output) + "\n", encoding="utf-8")


def install_codex_personal_plugin(source: Path, home: Path, installation_policy: str = "INSTALLED_BY_DEFAULT") -> dict:
    version = plugin_version(source)
    user_link = home / "plugins" / PLUGIN_NAME
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
    config_path = home / ".codex" / "config.toml"

    cache_path = copy_plugin_cache(source, home, version)
    ensure_plugin_link(source, user_link)
    ensure_marketplace_entry(marketplace_path, installation_policy)
    codex_local_link = ensure_codex_local_link(source, home)
    ensure_codex_plugin_enabled(config_path)

    return {
        "plugin": f"{PLUGIN_NAME}@{MARKETPLACE_NAME}",
        "version": version,
        "source": str(source),
        "user_link": str(user_link),
        "codex_local_link": str(codex_local_link),
        "marketplace": str(marketplace_path),
        "cache": str(cache_path),
        "config": str(config_path),
        "installation_policy": installation_policy,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Register and install ModuFlow in the Codex personal marketplace.")
    parser.add_argument("source", nargs="?", default=".", help="ModuFlow source package path")
    parser.add_argument(
        "--policy",
        choices=["AVAILABLE", "INSTALLED_BY_DEFAULT"],
        default="INSTALLED_BY_DEFAULT",
        help="Codex marketplace installation policy",
    )
    args = parser.parse_args()

    source = Path(args.source).resolve()
    home = Path.home()
    result = install_codex_personal_plugin(source, home, args.policy)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
