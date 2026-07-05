#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.project_sync import run_command

PROBE_FILENAME = ".moduflow-write-probe"


def _default_probe_write(git_dir):
    """Attempt a non-destructive local Git write. Never touches index.lock."""
    probe_path = git_dir / PROBE_FILENAME
    try:
        probe_path.write_text("probe", encoding="utf-8")
        probe_path.unlink()
        return True, ""
    except OSError as exc:
        return False, f"local .git write failed: {exc}"


def _github_api_available(root, runner):
    result = runner(["gh", "auth", "status"], root)
    return result.returncode == 0


def check_commit_capability(root, runner=None, probe_write=None):
    """Classify commit capability as local-git-write, github-api-commit, or blocked."""
    if runner is None:
        runner = run_command
    if probe_write is None:
        probe_write = _default_probe_write
    root = Path(root)
    git_dir = root / ".git"

    if not git_dir.exists():
        local_ok, local_reason = False, "not a git repository (.git missing)"
    else:
        local_ok, local_reason = probe_write(git_dir)

    if local_ok:
        return {
            "mode": "local-git-write",
            "ok": True,
            "local_git_write": True,
            "github_api_available": None,
            "reason": "",
            "recommendations": [],
        }

    github_ok = _github_api_available(root, runner)
    if github_ok:
        return {
            "mode": "github-api-commit",
            "ok": True,
            "local_git_write": False,
            "github_api_available": True,
            "reason": local_reason,
            "recommendations": [
                "Local Git write is blocked — use the GitHub API "
                "(gh api, or an MCP GitHub tool) to create/update the branch "
                "instead of local git add/commit/push.",
            ],
        }

    return {
        "mode": "blocked",
        "ok": False,
        "local_git_write": False,
        "github_api_available": False,
        "reason": local_reason,
        "recommendations": [
            "Neither local Git writes nor GitHub API access are available — "
            "ask the user to run the needed Git commands manually.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Classify local Git vs GitHub API commit capability.")
    parser.add_argument("root", nargs="?", default=".", help="Project root path")
    args = parser.parse_args()

    result = check_commit_capability(args.root)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
