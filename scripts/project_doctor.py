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

REQUIRED_PROFILE_PATHS = [
    ".moduflow/project-profile.md",
    ".moduflow/environments.json",
    ".moduflow/integrations.json",
]

CANDIDATE_PATHS = {
    "issues": ["issues", "docs/issues", "planning/issues", ".github/ISSUE_TEMPLATE"],
    "specs": ["specs", "docs/specs", "docs/prd", "prd", "requirements"],
    "workspace": ["workspace", "planning", "docs/planning", "product"],
    "reports": ["reports", "docs/reports"],
    "benchmarks": ["benchmarks", "benchmark", "docs/benchmarks"],
    "research": ["research", "docs/research"],
    "decisions": ["decisions", "docs/decisions", "adr", "docs/adr"],
    "data_notes": ["data-notes", "data_notes", "docs/data-notes", "analytics"],
}


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


def missing_profile_paths(root):
    missing = []
    for relative in REQUIRED_PROFILE_PATHS:
        if not (root / relative).exists():
            missing.append(relative)
    return missing


def discover_candidate_paths(root):
    candidates = {}
    for artifact_type, relative_paths in CANDIDATE_PATHS.items():
        matches = []
        for relative in relative_paths:
            if (root / relative).exists():
                matches.append(relative)
        if matches:
            candidates[artifact_type] = matches
    return candidates


def recommended_migration_mode(missing, candidates):
    if not missing:
        return None
    if candidates:
        return "mapped"
    return "overlay"


def inspect_project(path):
    requested = Path(path).resolve()
    detected_git_root = git_root(requested)
    project_root = detected_git_root or requested
    remote = git_remote(project_root) if detected_git_root else None
    gh_status = gh_auth_status(project_root)
    missing = missing_project_paths(project_root)
    missing_profile = missing_profile_paths(project_root)
    candidates = discover_candidate_paths(project_root)
    migration_mode = recommended_migration_mode(missing, candidates)

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
        "migration": {
            "recommended_mode": migration_mode,
            "candidates": candidates,
        },
        "profile": {
            "initialized": not missing_profile,
            "missing": missing_profile,
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
        if migration_mode == "mapped":
            result["recommendation"].append("Run product:migrate --mode mapped to plan a non-destructive migration.")
        else:
            result["recommendation"].append("Run product:migrate --mode overlay to add ModuFlow metadata without moving existing files.")
        result["recommendation"].append("Run product:start after migration planning if this is a new project.")
    else:
        result["recommendation"].append("Run product:status to inspect current work.")

    if missing_profile:
        result["recommendation"].append("Run product:profile --write to create project profile metadata.")

    return result


def main():
    result = inspect_project(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
