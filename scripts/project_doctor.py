#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_PROJECT_PATHS = [
    ".moduflow/config.json",
    ".moduflow/state.json",
    "issues",
    "specs",
    "workspace/inbox.md",
    "workspace/opportunities.md",
    "workspace/roadmap.md",
    "workspace/dashboard.md",
]


def run(args, cwd):
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return None
    return result


def git_root(path):
    result = run(["git", "rev-parse", "--show-toplevel"], path)
    if result and result.returncode == 0:
        return Path(result.stdout.strip())
    return None


def git_remote(path):
    result = run(["git", "remote", "get-url", "origin"], path)
    if result and result.returncode == 0:
        return result.stdout.strip()
    return None


def gh_auth_status(path):
    if shutil.which("gh") is None:
        return {"available": False, "authenticated": False, "detail": "gh not found"}
    result = run(["gh", "auth", "status"], path)
    if result is None:
        return {"available": False, "authenticated": False, "detail": "gh not found"}
    detail = (result.stdout + result.stderr).strip()
    return {
        "available": True,
        "authenticated": result.returncode == 0,
        "detail": detail.splitlines()[0] if detail else "",
    }


def missing_project_paths(root):
    missing = []
    for relative in REQUIRED_PROJECT_PATHS:
        if not (root / relative).exists():
            missing.append(relative)
    return missing


def main():
    requested = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    detected_git_root = git_root(requested)
    project_root = detected_git_root or requested
    remote = git_remote(project_root) if detected_git_root else None
    gh_status = gh_auth_status(project_root)
    missing = missing_project_paths(project_root)

    result = {
        "requested_path": str(requested),
        "project_root": str(project_root),
        "git": {
            "is_repo": detected_git_root is not None,
            "root": str(detected_git_root) if detected_git_root else None,
            "origin": remote,
        },
        "github_cli": gh_status,
        "moduflow": {
            "initialized": not missing,
            "missing": missing,
        },
        "recommendation": [],
    }

    if not result["git"]["is_repo"]:
        result["recommendation"].append("Run git init or choose an existing Git project before GitHub Spec Kit-style execution.")
    elif not remote:
        result["recommendation"].append("Add a GitHub origin if issues, PRs, and releases should sync with GitHub.")

    if not gh_status["available"]:
        result["recommendation"].append("Install GitHub CLI if GitHub issue/PR sync is needed.")
    elif not gh_status["authenticated"]:
        result["recommendation"].append("Run gh auth login if GitHub issue/PR sync is needed.")

    if missing:
        result["recommendation"].append("Run product:start to initialize ModuFlow project artifacts.")
    else:
        result["recommendation"].append("Run product:status to inspect current work.")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

