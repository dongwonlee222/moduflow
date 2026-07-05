#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.project_sync import run_command

PREFIX_RE = re.compile(r"^([a-zA-Z]+)(\([^)]*\))?(!)?:")

# On a 0.x project this repo bumps patch for both feat and fix, matching its
# own pre-existing history (0.2.11 -> 0.2.15, all patch), reserving minor for
# a deliberate, manually-declared milestone rather than every feature.
MINOR_TYPES = set()
PATCH_TYPES = {"feat", "fix"}


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


def check_bump_applied(root, runner=None):
    """Gate: HEAD's commit type implies a bump but plugin.json version didn't move.

    Compares only the HEAD commit against its parent, matching the documented
    workflow where the version bump is staged into the same commit as the
    issue's completion commit (see docs/host-adapter-guidance.md).
    """
    if runner is None:
        runner = run_command
    root = Path(root)
    plugin_rel = ".claude-plugin/plugin.json"

    count_result = runner(["git", "rev-list", "--count", "HEAD"], root)
    try:
        commit_count = int(count_result.stdout.strip())
    except (ValueError, AttributeError):
        return {"ok": True, "errors": []}
    if commit_count < 2:
        return {"ok": True, "errors": []}

    message_result = runner(["git", "log", "-1", "--pretty=%B", "HEAD"], root)
    level = classify_bump(message_result.stdout)
    if level == "none":
        return {"ok": True, "errors": []}

    current_result = runner(["git", "show", f"HEAD:{plugin_rel}"], root)
    prior_result = runner(["git", "show", f"HEAD~1:{plugin_rel}"], root)
    try:
        current_version = json.loads(current_result.stdout)["version"]
        prior_version = json.loads(prior_result.stdout)["version"]
    except (ValueError, KeyError, TypeError):
        return {"ok": True, "errors": []}

    if current_version == prior_version:
        return {
            "ok": False,
            "errors": [
                f"HEAD commit classifies as a '{level}' bump but {plugin_rel}'s version "
                f"is unchanged ({current_version}) — run scripts/version_bump.py before committing."
            ],
        }
    return {"ok": True, "errors": []}


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
