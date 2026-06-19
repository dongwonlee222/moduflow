#!/usr/bin/env python3
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_PROJECT_PATHS = [
    ".moduflow/config.json",
    ".moduflow/state.json",
]

REQUIRED_PROFILE_PATHS = [
    ".moduflow/project-profile.md",
    ".moduflow/environments.json",
    ".moduflow/integrations.json",
]

REQUIRED_KNOWLEDGE_PATHS = [
    "knowledge",
    "knowledge/index.md",
    "knowledge/decisions",
    "knowledge/benchmarks",
    "knowledge/reports",
    "knowledge/research",
    "knowledge/data-notes",
    "knowledge/references",
]

REQUIRED_WORKFLOW_PATHS = [
    "workflow/review-gates.md",
    "workflow/approval-policy.md",
    "workflow/release-policy.md",
    "workflow/handoff.md",
    "workflow/risks.md",
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


def load_project_validator():
    path = Path(__file__).resolve().parent / "validate_project_artifacts.py"
    spec = importlib.util.spec_from_file_location("validate_project_artifacts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project_loop():
    path = Path(__file__).resolve().parent / "project_loop.py"
    spec = importlib.util.spec_from_file_location("project_loop", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def read_config_paths(root):
    config_path = root / ".moduflow" / "config.json"
    if not config_path.exists():
        return {}
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return config.get("paths", {}) if isinstance(config.get("paths", {}), dict) else {}


def project_paths(root):
    paths = read_config_paths(root)
    issues = paths.get("issues", "issues")
    specs = paths.get("specs", "specs")
    workspace = paths.get("workspace", "workspace")
    return REQUIRED_PROJECT_PATHS + [
        issues,
        specs,
        f"{workspace}/inbox.md",
        f"{workspace}/opportunities.md",
        f"{workspace}/roadmap.md",
        f"{workspace}/dashboard.md",
    ]


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


def current_branch(path):
    result = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], path)
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
    for relative in project_paths(root):
        if not (root / relative).exists():
            missing.append(relative)
    return missing


def missing_profile_paths(root):
    missing = []
    for relative in REQUIRED_PROFILE_PATHS:
        if not (root / relative).exists():
            missing.append(relative)
    return missing


def missing_knowledge_paths(root):
    missing = []
    for relative in REQUIRED_KNOWLEDGE_PATHS:
        if not (root / relative).exists():
            missing.append(relative)
    return missing


def missing_workflow_paths(root):
    missing = []
    for relative in REQUIRED_WORKFLOW_PATHS:
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


def detect_mode(root):
    manifest_path = root / ".claude-plugin" / "plugin.json"
    if manifest_path.exists() and (root / "vendor.lock.json").exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if data.get("name") == "moduflow":
                return "dogfooding"
        except Exception:
            pass

    legacy_dirs = ["commands", "skills", "scripts", "templates"]
    for d in legacy_dirs:
        dir_path = root / d
        if dir_path.is_dir() and any(dir_path.iterdir()):
            return "heavy"

    return "lightweight"


def inspect_project(path):
    requested = Path(path).resolve()
    detected_git_root = git_root(requested)
    project_root = detected_git_root or requested
    remote = git_remote(project_root) if detected_git_root else None
    gh_status = gh_auth_status(project_root)
    missing = missing_project_paths(project_root)
    missing_profile = missing_profile_paths(project_root)
    missing_knowledge = missing_knowledge_paths(project_root)
    missing_workflow = missing_workflow_paths(project_root)
    candidates = discover_candidate_paths(project_root)
    migration_mode = recommended_migration_mode(missing, candidates)
    project_loop = load_project_loop()
    project_validator = load_project_validator()
    schema_gates = project_validator.validate_project(project_root)
    loop_errors = project_loop.validate_loop_state(project_root)
    loop_state_exists = (project_root / "workspace" / "loop-state.json").exists()
    loop_state = project_loop.load_loop_state(project_root) if loop_state_exists else None
    git_binding = loop_state.get("git_binding") if loop_state else None
    branch = current_branch(project_root) if detected_git_root else None

    result = {
        "requested_path": str(requested),
        "project_root": str(project_root),
        "mode": detect_mode(project_root),
        "git": {
            "is_repo": detected_git_root is not None,
            "root": str(detected_git_root) if detected_git_root else None,
            "origin": remote,
            "branch": branch,
        },
        "git_binding": {
            "declared": git_binding,
            "errors": loop_errors,
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
        "knowledge": {
            "initialized": not missing_knowledge,
            "missing": missing_knowledge,
        },
        "workflow": {
            "initialized": not missing_workflow,
            "missing": missing_workflow,
        },
        "loop": {
            "initialized": loop_state_exists,
            "errors": loop_errors,
        },
        "schema_gates": {
            "valid": schema_gates.get("valid", False),
            "errors": schema_gates.get("errors", []),
            "warnings": schema_gates.get("warnings", []),
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

    if missing_knowledge:
        result["recommendation"].append("Run product:knowledge --write to create knowledge evidence structure.")

    if missing_workflow:
        result["recommendation"].append("Run product:handoff --write to create team workflow artifacts.")

    if loop_state and branch and branch not in {"main", "master"}:
        active_issue_id = loop_state.get("active_issue_id")
        if active_issue_id and not project_loop.branch_matches_issue(branch, active_issue_id):
            result["recommendation"].append("Current branch does not match active issue; switch branches or update workspace/loop-state.json git_binding.")

    if loop_errors:
        result["recommendation"].append("Run product:loop or product:doctor after fixing loop-state references.")

    if schema_gates.get("errors"):
        result["recommendation"].append("schema gate failed; fix linked artifacts, state drift, or next_command before release.")

    return result


def main():
    result = inspect_project(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    moduflow = result.get("moduflow", {})
    # Gate: a project is healthy only when ModuFlow is initialized with no missing
    # required artifacts. Returning a real exit code makes project_doctor an
    # actual gate inside release_check instead of an always-pass no-op.
    return 0 if moduflow.get("initialized") and not moduflow.get("missing") else 1


if __name__ == "__main__":
    raise SystemExit(main())
