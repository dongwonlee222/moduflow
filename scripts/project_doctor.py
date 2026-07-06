#!/usr/bin/env python3
import argparse
import importlib.util
import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
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

REQUIRED_MEMORY_PATHS = [
    "memory",
    "memory/index.md",
    "memory/deliverables",
    "memory/decisions",
    "memory/evidence",
    "memory/meetings",
    "memory/releases",
    "memory/notes",
    "memory/references",
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


def load_project_memory():
    path = Path(__file__).resolve().parent / "project_memory.py"
    spec = importlib.util.spec_from_file_location("project_memory", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project_lifecycle():
    path = Path(__file__).resolve().parent / "project_lifecycle.py"
    spec = importlib.util.spec_from_file_location("project_lifecycle", path)
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


def local_project_root(path):
    current = Path(path).resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / ".moduflow" / "config.json").exists():
            return candidate
    return current


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


def missing_memory_paths(root):
    missing = []
    for relative in REQUIRED_MEMORY_PATHS:
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


def mode_guidance(mode):
    guidance = {
        "lightweight": {
            "label": "가벼운 프로젝트 설정",
            "message": "프로젝트 설정이 가볍고 정상입니다.",
            "details": "commands, scripts, skills, templates 같은 도구 폴더는 플러그인에 남고 프로젝트에는 PM 산출물과 상태만 있습니다.",
            "action": "product:status",
        },
        "dogfooding": {
            "label": "모두플로 도구 저장소",
            "message": "모두플로 도구 저장소라 폴더가 많은 것이 정상입니다.",
            "details": "commands, scripts, skills, templates, adapters, vendor 같은 내부 개발/런타임 폴더가 이 저장소에 함께 있습니다.",
            "action": "product:status",
        },
        "heavy": {
            "label": "정리 권장 프로젝트 설정",
            "message": "프로젝트 안에 도구 폴더가 있어 정리를 권장합니다.",
            "details": "normal target projects should keep PM artifacts and state only; move commands, scripts, skills, and templates back to the ModuFlow plugin/source package.",
            "action": "product:migrate --mode overlay",
        },
    }
    return guidance.get(
        mode,
        {
            "label": "프로젝트 설정 확인 필요",
            "message": "프로젝트 설정 상태를 확인해야 합니다.",
            "details": "Run product:doctor for diagnostics.",
            "action": "product:doctor",
        },
    )


def skipped_preflight_status():
    return {
        "available": None,
        "authenticated": None,
        "detail": "preflight skipped",
    }


def installed_plugin_staleness(project_root, home=None):
    """Soft check: is the installed ModuFlow plugin copy behind this repo's version?"""
    home = Path(home) if home is not None else Path.home()
    empty = {"checked": False, "stale": [], "recommendations": []}

    plugin_manifest_path = Path(project_root) / ".claude-plugin" / "plugin.json"
    try:
        manifest = json.loads(plugin_manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return empty
    # Only the moduflow source repo's own version is comparable to the
    # installed moduflow copies — any other plugin's manifest must not
    # produce a spurious staleness warning.
    if manifest.get("name") != "moduflow":
        return empty
    repo_version = manifest.get("version")
    if not repo_version:
        return empty

    stale = []
    recommendations = []

    installed_plugins_path = home / ".claude" / "plugins" / "installed_plugins.json"
    try:
        if installed_plugins_path.exists():
            data = json.loads(installed_plugins_path.read_text(encoding="utf-8"))
            entries = data.get("plugins", {}).get("moduflow@moduflow", [])
            for entry in entries:
                installed_version = entry.get("version")
                if installed_version and installed_version != repo_version:
                    stale.append(
                        {"host": "claude-code", "installed": installed_version, "repo": repo_version}
                    )
                    recommendations.append(
                        "claude plugin marketplace update moduflow && claude plugin update moduflow@moduflow"
                    )
    except Exception:
        pass

    codex_cache_dir = home / ".codex" / "plugins" / "cache" / "personal" / "moduflow"
    try:
        if codex_cache_dir.exists():
            versions = [d.name for d in codex_cache_dir.iterdir() if d.is_dir()]
            if versions and not any(name.split("+")[0] == repo_version for name in versions):

                def _numeric_base(name):
                    try:
                        return tuple(int(part) for part in name.split("+")[0].split("."))
                    except ValueError:
                        return (-1,)

                newest = max(versions, key=_numeric_base)
                stale.append({"host": "codex", "installed": newest, "repo": repo_version})
                recommendations.append("python3 scripts/register_codex_personal_marketplace.py .")
    except Exception:
        pass

    return {"checked": True, "stale": stale, "recommendations": recommendations}


def check_hook_log(root):
    """Parse .moduflow/logs/hooks.log and return recent warnings.

    Format: <iso-ts> <hook> <level:warn|error> <message>
    Returns: list of warning dicts with hook, level, timestamp, message
    Filters: last 7 days, capped at 20 most recent

    Absent file or zero recent entries: return empty list (silent)
    Unparseable lines: include with a malformed note
    """
    warnings = []
    log_path = root / ".moduflow" / "logs" / "hooks.log"

    if not log_path.exists():
        return warnings

    try:
        content = log_path.read_text(encoding="utf-8")
    except Exception:
        return warnings

    if not content.strip():
        return warnings

    # Calculate cutoff: last 7 days
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)

    lines = content.splitlines()
    recent_entries = []

    for line in lines:
        if not line.strip():
            continue

        parts = line.split(None, 3)  # Split on whitespace, max 4 parts

        if len(parts) < 4:
            # Malformed line: include with a note
            recent_entries.append({
                "hook": "unknown",
                "level": "warn",
                "timestamp": None,
                "message": f"malformed hook log entry: {line}",
                "malformed": True,
            })
            continue

        iso_ts_str, hook, level, message = parts

        # Try to parse ISO timestamp
        try:
            # Handle both with/without microseconds
            if "." in iso_ts_str:
                ts = datetime.fromisoformat(iso_ts_str.replace("Z", "+00:00"))
            else:
                ts = datetime.fromisoformat(iso_ts_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            # Unparseable timestamp: include with a note
            recent_entries.append({
                "hook": hook,
                "level": level,
                "timestamp": None,
                "message": message,
                "malformed": True,
                "note": f"unparseable timestamp: {iso_ts_str}",
            })
            continue

        # Check if within 7-day window
        if ts >= cutoff:
            recent_entries.append({
                "hook": hook,
                "level": level,
                "timestamp": iso_ts_str,
                "message": message,
            })

    # Sort by timestamp descending (most recent first) and cap at 20
    recent_entries.sort(
        key=lambda x: x.get("timestamp") or "",
        reverse=True
    )

    # Return the 20 most recent
    return recent_entries[:20]


def inspect_project(path, include_preflight=True):
    requested = Path(path).resolve()
    if include_preflight:
        detected_git_root = git_root(requested)
        project_root = detected_git_root or requested
        remote = git_remote(project_root) if detected_git_root else None
        gh_status = gh_auth_status(project_root)
    else:
        detected_git_root = None
        project_root = local_project_root(requested)
        remote = None
        gh_status = skipped_preflight_status()

    missing = missing_project_paths(project_root)
    missing_profile = missing_profile_paths(project_root)
    missing_knowledge = missing_knowledge_paths(project_root)
    missing_memory = missing_memory_paths(project_root)
    try:
        isolated_memory = load_project_memory().isolated_memory_entries(project_root) if not missing_memory else []
    except Exception:
        isolated_memory = []
    try:
        lifecycle_drift = load_project_lifecycle().lifecycle_drift(project_root)
    except Exception:
        lifecycle_drift = []
    try:
        plugin_staleness = installed_plugin_staleness(project_root)
    except Exception:
        plugin_staleness = {"checked": False, "stale": [], "recommendations": []}
    try:
        hook_log_warnings = check_hook_log(project_root)
    except Exception:
        hook_log_warnings = []
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
    branch = current_branch(project_root) if include_preflight and detected_git_root else None

    mode = detect_mode(project_root)
    result = {
        "requested_path": str(requested),
        "project_root": str(project_root),
        "mode": mode,
        "mode_guidance": mode_guidance(mode),
        "preflight": {
            "enabled": include_preflight,
            "skipped": [] if include_preflight else ["git", "github_cli"],
        },
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
        "memory": {
            "initialized": not missing_memory,
            "missing": missing_memory,
            "isolated": isolated_memory,  # soft hint only — never affects exit code
        },
        "lifecycle": {
            "drift": lifecycle_drift,  # 048: issue files vs state.json/dashboard
        },
        "installed_plugin": plugin_staleness,  # soft hint only — never affects exit code
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
        "hooks": {
            "warnings": hook_log_warnings,
        },
        "recommendation": [],
    }

    if not include_preflight:
        result["recommendation"].append("Run product:doctor with preflight when GitHub sync or Git state checks are needed.")
    elif not result["git"]["is_repo"]:
        result["recommendation"].append("Run git init or choose an existing Git project before GitHub Spec Kit-style execution.")
    elif not remote:
        result["recommendation"].append("Add a GitHub origin if issues, PRs, and releases should sync with GitHub.")

    if include_preflight and not gh_status["available"]:
        result["recommendation"].append("Install GitHub CLI if GitHub issue/PR sync is needed.")
    elif include_preflight and not gh_status["authenticated"]:
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

    if missing_memory:
        result["recommendation"].append("Run product:memory --write to create portable project memory structure.")

    if missing_workflow:
        result["recommendation"].append("Run product:handoff --write to create team workflow artifacts.")

    if isolated_memory:
        result["recommendation"].append(
            f"hint: {len(isolated_memory)} isolated memory entries (no relationships or issue_id) — "
            "run product:memory --list-ids and link real nodes (043). Informational, not required."
        )

    if lifecycle_drift:
        result["recommendation"].append(
            f"lifecycle drift: {len(lifecycle_drift)} disagreement(s) between issue files and "
            "derived views — run `python3 scripts/project_lifecycle.py . --sync` (048)."
        )

    if loop_state and branch and branch not in {"main", "master"}:
        active_issue_id = loop_state.get("active_issue_id")
        if active_issue_id and not project_loop.branch_matches_issue(branch, active_issue_id):
            result["recommendation"].append("Current branch does not match active issue; switch branches or update workspace/loop-state.json git_binding.")

    if loop_errors:
        result["recommendation"].append("Run product:loop or product:doctor after fixing loop-state references.")

    if schema_gates.get("errors"):
        result["recommendation"].append("schema gate failed; fix linked artifacts, state drift, or next_command before release.")

    if hook_log_warnings:
        result["recommendation"].append(
            f"hook health: {len(hook_log_warnings)} lifecycle hook event(s) logged in last 7 days (warnings/errors) — "
            "review .moduflow/logs/hooks.log for details."
        )

    result["recommendation"].extend(plugin_staleness["recommendations"])

    return result


def main():
    parser = argparse.ArgumentParser(description="Inspect ModuFlow project setup.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        help="Skip Git and GitHub CLI preflight checks for local-only validation.",
    )
    args = parser.parse_args()
    result = inspect_project(args.project_path, include_preflight=not args.no_preflight)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    moduflow = result.get("moduflow", {})
    # Gate: a project is healthy only when ModuFlow is initialized with no missing
    # required artifacts. Returning a real exit code makes project_doctor an
    # actual gate inside release_check instead of an always-pass no-op.
    return 0 if moduflow.get("initialized") and not moduflow.get("missing") else 1


if __name__ == "__main__":
    raise SystemExit(main())
