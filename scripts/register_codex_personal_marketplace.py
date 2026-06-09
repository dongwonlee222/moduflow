#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


PLUGIN_NAME = "moduflow"


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


def ensure_marketplace_entry(marketplace_path: Path) -> None:
    marketplace = read_json(marketplace_path)
    marketplace.setdefault("name", "personal")
    marketplace.setdefault("interface", {"displayName": "Personal"})
    marketplace.setdefault("plugins", [])

    entry = {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_NAME}",
        },
        "policy": {
            "installation": "AVAILABLE",
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


def main() -> int:
    source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    home = Path.home()
    link = home / "plugins" / PLUGIN_NAME
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"

    ensure_plugin_link(source, link)
    ensure_marketplace_entry(marketplace_path)

    print(f"Linked plugin: {link} -> {source}")
    print(f"Updated marketplace: {marketplace_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

