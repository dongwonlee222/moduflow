#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.project_sync import run_command
from scripts.project_repository_identity import (
    inspect_repository_identity,
    operation_decision,
)

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


def _resolve_git_dir(root):
    """Return the directory Git uses for repository-local state."""
    git_entry = root / ".git"
    if not git_entry.exists():
        return None, "not a git repository (.git missing)"
    if git_entry.is_dir():
        return git_entry, ""

    try:
        marker = git_entry.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return None, f"cannot read .git worktree pointer: {exc}"
    prefix = "gitdir:"
    if not marker.lower().startswith(prefix):
        return None, "invalid .git worktree pointer"
    target = marker[len(prefix) :].strip()
    if not target:
        return None, "invalid .git worktree pointer: missing gitdir"
    git_dir = Path(target)
    if not git_dir.is_absolute():
        git_dir = git_entry.parent / git_dir
    return git_dir.resolve(), ""


def _github_api_available(root, runner):
    result = runner(["gh", "auth", "status"], root)
    return result.returncode == 0


def check_commit_capability(root, runner=None, probe_write=None, operation="commit"):
    """Classify commit capability as local-git-write, github-api-commit, or blocked."""
    if runner is None:
        runner = run_command
    if probe_write is None:
        probe_write = _default_probe_write
    root = Path(root)
    identity = None

    if (root / ".moduflow" / "config.json").is_file():
        identity = inspect_repository_identity(root, runner=runner)
        decision = operation_decision(identity, operation)
        if not decision["allowed"]:
            reason = "; ".join(
                item.get("message", item.get("code", "identity denied"))
                for item in decision["reasons"]
            )
            return {
                "mode": "identity-blocked",
                "ok": False,
                "local_git_write": False,
                "github_api_available": False,
                "reason": reason,
                "recommendations": [
                    "Fix or explicitly migrate canonical repository identity before Git/GitHub writes."
                ],
                "repository_identity": decision,
            }

    git_dir, resolve_reason = _resolve_git_dir(root)

    if git_dir is None:
        local_ok, local_reason = False, resolve_reason
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

    if identity is not None:
        fallback_decision = operation_decision(identity, "github_api_commit")
        if not fallback_decision["allowed"]:
            return {
                "mode": "blocked",
                "ok": False,
                "local_git_write": False,
                "github_api_available": False,
                "reason": local_reason,
                "recommendations": [
                    "GitHub API fallback is unavailable because canonical repository "
                    "identity does not allow github_write."
                ],
                "repository_identity": fallback_decision,
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
    parser.add_argument("--operation", choices=["commit", "push"], default="commit")
    args = parser.parse_args()

    result = check_commit_capability(args.root, operation=args.operation)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
