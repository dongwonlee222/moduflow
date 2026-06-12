#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import sys
from pathlib import Path


PLUGIN_NAME = "moduflow"
MARKETPLACE_NAME = "personal"


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
    if manifest.get("version") != version:
        manifest["version"] = version
        write_json(codex_manifest_path, manifest)
    return version


def copy_plugin_cache(source: Path, home: Path, version: str) -> Path:
    destination = home / ".codex" / "plugins" / "cache" / MARKETPLACE_NAME / PLUGIN_NAME / version
    if destination.exists():
        shutil.rmtree(destination)
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc")
    shutil.copytree(source, destination, ignore=ignore)
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

    ensure_plugin_link(source, user_link)
    ensure_marketplace_entry(marketplace_path, installation_policy)
    codex_local_link = ensure_codex_local_link(source, home)
    cache_path = copy_plugin_cache(source, home, version)
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
