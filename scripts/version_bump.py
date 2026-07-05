#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

PREFIX_RE = re.compile(r"^([a-zA-Z]+)(\([^)]*\))?(!)?:")

MINOR_TYPES = {"feat"}
PATCH_TYPES = {"fix"}


def classify_bump(commit_message):
    first_line = commit_message.splitlines()[0] if commit_message else ""
    m = PREFIX_RE.match(first_line)

    if "BREAKING CHANGE:" in commit_message:
        return "major"
    if not m:
        return "none"

    commit_type, _scope, bang = m.group(1), m.group(2), m.group(3)
    if bang:
        return "major"
    if commit_type in MINOR_TYPES:
        return "minor"
    if commit_type in PATCH_TYPES:
        return "patch"
    return "none"


def bump_version(version_str, level):
    if level == "none":
        return version_str

    major, minor, patch = (int(part) for part in version_str.split("."))
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown bump level: {level}")


def apply_bump(plugin_json_path, commit_message):
    plugin_json_path = Path(plugin_json_path)
    data = json.loads(plugin_json_path.read_text(encoding="utf-8"))

    level = classify_bump(commit_message)
    new_version = bump_version(data["version"], level)

    if new_version != data["version"]:
        data["version"] = new_version
        plugin_json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    return new_version


def main():
    parser = argparse.ArgumentParser(description="Classify a commit message and bump plugin.json's version.")
    parser.add_argument("plugin_json_path", nargs="?", default=".claude-plugin/plugin.json")
    parser.add_argument("commit_message", help="Commit message to classify (first line + optional footer).")
    args = parser.parse_args()

    new_version = apply_bump(args.plugin_json_path, args.commit_message)
    print(new_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
