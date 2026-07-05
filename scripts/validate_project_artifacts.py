#!/usr/bin/env python3
import importlib.util
import json
import re
import sys
from pathlib import Path


REQUIRED_PATHS = [
    ".moduflow/config.json",
    ".moduflow/state.json",
]

OPTIONAL_CAPABILITY_PATHS = {
    "profile": [
        ".moduflow/project-profile.md",
        ".moduflow/environments.json",
        ".moduflow/integrations.json",
    ],
    "knowledge": [
        "knowledge/index.md",
        "knowledge/decisions",
        "knowledge/benchmarks",
        "knowledge/reports",
        "knowledge/research",
        "knowledge/data-notes",
        "knowledge/references",
    ],
    "memory": [
        "memory/index.md",
        "memory/deliverables",
        "memory/decisions",
        "memory/evidence",
        "memory/meetings",
        "memory/releases",
        "memory/notes",
        "memory/references",
    ],
    "workflow": [
        "workflow/review-gates.md",
        "workflow/approval-policy.md",
        "workflow/release-policy.md",
        "workflow/handoff.md",
        "workflow/risks.md",
    ],
}

JSON_FILES = [
    ".moduflow/config.json",
    ".moduflow/state.json",
]

OPTIONAL_JSON_FILES = [
    ".moduflow/environments.json",
    ".moduflow/integrations.json",
    "workflow/team-state.json",
]


def load_project_loop():
    path = Path(__file__).resolve().parent / "project_loop.py"
    spec = importlib.util.spec_from_file_location("project_loop", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project_lifecycle():
    path = Path(__file__).resolve().parent / "project_lifecycle.py"
    spec = importlib.util.spec_from_file_location("project_lifecycle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LINK_RE = re.compile(r"`(?P<path>[^`]+)`")


def read_text_if_exists(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def artifact_paths(root, errors):
    paths = read_config_paths(root, errors)
    return {
        "issues": paths.get("issues", "issues"),
        "specs": paths.get("specs", "specs"),
        "workspace": paths.get("workspace", "workspace"),
    }


def active_loop_state(root, project_loop):
    path = root / "workspace" / "loop-state.json"
    if not path.exists():
        return None
    return project_loop.load_loop_state(root)


def linked_artifacts(issue_text):
    linked = []
    for match in LINK_RE.finditer(issue_text):
        value = match.group("path").strip()
        if any(ch in value for ch in "<>{}"):
            continue  # placeholder path (e.g. specs/<id>/{spec,plan,tasks}.md), not a real link
        if value.startswith("specs/") or value.startswith("workspace/") or value.startswith("memory/"):
            linked.append(value)
    return linked


def iter_memory_markdown(root):
    memory_root = root / "memory"
    if not memory_root.exists():
        return []
    return sorted(path for path in memory_root.glob("*/*.md") if path.is_file())


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}
    meta_text = parts[0].split("\n", 1)[1]
    metadata = {}
    for line in meta_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def parse_list_value(value):
    value = (value or "").strip()
    if not value.startswith("[") or not value.endswith("]"):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip() for item in inner.split(",") if item.strip()]


def validate_memory_links(root, errors):
    for memory_file in iter_memory_markdown(root):
        metadata = parse_frontmatter(memory_file.read_text(encoding="utf-8"))
        relative_memory = str(memory_file.relative_to(root))
        for linked in parse_list_value(metadata.get("source_artifacts", "[]")):
            if linked and not (root / linked).exists():
                errors.append(f"{relative_memory}: broken source_artifacts link: {linked}")
        if "memory/.candidates/" in relative_memory and metadata.get("status") != "candidate":
            errors.append(f"{relative_memory}: candidate memory must have status: candidate")


def validate_team_workflow_state(root, errors):
    team_state_path = root / "workflow" / "team-state.json"
    if not team_state_path.exists():
        return
    state = read_json(team_state_path, errors)
    if not state:
        return
    if state.get("schema") != "moduflow.team-state.v1":
        errors.append("workflow/team-state.json: schema must be moduflow.team-state.v1")
        return
    items = state.get("items")
    if not isinstance(items, list):
        errors.append("workflow/team-state.json: items must be a list")
        return
    for item in items:
        issue_id = item.get("issue_id")
        status = item.get("status")
        if not issue_id:
            errors.append("workflow/team-state.json: item missing issue_id")
            continue
        if not (root / "issues" / f"{issue_id}.md").exists():
            errors.append(f"workflow/team-state.json: item references missing issue {issue_id}")
        if status == "active" and not item.get("branch"):
            errors.append(f"workflow/team-state.json: active state for {issue_id} requires branch")
        if status == "active" and not (item.get("assignee") or item.get("locked_by")):
            errors.append(f"workflow/team-state.json: active state for {issue_id} requires assignee or locked_by")
        if status == "review" and not (item.get("reviewer") and item.get("pr")):
            errors.append(f"workflow/team-state.json: review state requires reviewer and pr for {issue_id}")


def validate_active_issue_links(root, issue_id, errors):
    issue_file = root / "issues" / f"{issue_id}.md"
    if not issue_file.exists():
        return
    issue_text = issue_file.read_text(encoding="utf-8")
    for relative in linked_artifacts(issue_text):
        if not (root / relative).exists():
            errors.append(f"issues/{issue_id}.md: linked artifact missing: {relative}")


def validate_active_state_views(root, active_issue_id, next_command, errors):
    # 048: lifecycle canonical is the issue file Status; .moduflow/state.json is the
    # live summary. The dashboard must mention the active issue. (next_command is NOT
    # checked here — the dashboard's "## Next Command" is fixed to product:status by a
    # separate rule; coupling it to state.next_command was the retired loop-state gate.
    # roadmap.md is a narrative roadmap, not an active-issue tracker — not gated.)
    if not active_issue_id:
        return
    dashboard = root / "workspace" / "dashboard.md"
    dashboard_text = read_text_if_exists(dashboard)
    if dashboard.exists() and active_issue_id not in dashboard_text:
        errors.append(f"workspace/dashboard.md: missing active_issue_id {active_issue_id}")


def validate_next_command_matches_phase(root, loop_state, project_loop, errors):
    if not loop_state:
        return
    active_issue_id = loop_state.get("active_issue_id")
    if not active_issue_id:
        return
    phase = project_loop.infer_issue_phase(root, active_issue_id)
    expected = project_loop.recommend_next_command(active_issue_id, phase)
    actual = loop_state.get("next_command")
    if actual != expected:
        errors.append(f"workspace/loop-state.json: next_command {actual} should be {expected}")


def validate_schema_gates(root, project_loop, errors):
    # 048: gate keys off .moduflow/state.json (live summary), not loop-state.json
    # (retired/dormant — frozen at issue 040, a prior goal). loop-state's
    # next_command/phase coupling is no longer a lifecycle gate.
    state = read_json(root / ".moduflow" / "state.json", errors)
    if not state:
        return
    active_issue_id = (state.get("active_issue") or "").strip()
    if active_issue_id:
        validate_active_issue_links(root, active_issue_id, errors)
    validate_active_state_views(root, active_issue_id, state.get("next_command"), errors)
    # 048: lifecycle drift gate — issue files (canonical) must agree with the
    # derived views. Run `python3 scripts/project_lifecycle.py <root> --sync` to fix.
    try:
        for d in load_project_lifecycle().lifecycle_drift(root):
            errors.append(f"lifecycle drift: {d} (run project_lifecycle.py --sync)")
    except Exception:
        pass


def read_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: invalid JSON ({exc})")
        return None


def read_config_paths(root, errors):
    config_path = root / ".moduflow" / "config.json"
    if not config_path.exists():
        return {}
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    paths = config.get("paths", {})
    return paths if isinstance(paths, dict) else {}


def required_paths(root, errors):
    paths = read_config_paths(root, errors)
    issues = paths.get("issues", "issues")
    specs = paths.get("specs", "specs")
    workspace = paths.get("workspace", "workspace")
    return REQUIRED_PATHS + [
        issues,
        specs,
        f"{workspace}/inbox.md",
        f"{workspace}/opportunities.md",
        f"{workspace}/roadmap.md",
        f"{workspace}/dashboard.md",
    ]


def validate_project(path):
    root = Path(path).resolve()
    errors = []
    warnings = []

    for relative in required_paths(root, errors):
        if not (root / relative).exists():
            errors.append(f"Missing required project artifact: {relative}")

    for capability, paths in OPTIONAL_CAPABILITY_PATHS.items():
        missing = [relative for relative in paths if not (root / relative).exists()]
        if missing:
            warnings.append(
                f"Optional project capability not initialized: {capability} ({', '.join(missing)})"
            )

    parsed = {}
    for relative in JSON_FILES + OPTIONAL_JSON_FILES:
        target = root / relative
        if target.exists():
            parsed[relative] = read_json(target, errors)

    config = parsed.get(".moduflow/config.json")
    if config and config.get("schema") != "moduflow.config.v1":
        errors.append(".moduflow/config.json: schema must be moduflow.config.v1")

    state = parsed.get(".moduflow/state.json")
    if state:
        if state.get("schema") != "moduflow.state.v1":
            errors.append(".moduflow/state.json: schema must be moduflow.state.v1")
        if "phase" not in state:
            errors.append(".moduflow/state.json: missing phase")
        if "next_command" not in state:
            errors.append(".moduflow/state.json: missing next_command")

    project_loop = load_project_loop()
    errors.extend(project_loop.validate_loop_state(root))
    validate_schema_gates(root, project_loop, errors)
    validate_memory_links(root, errors)
    validate_team_workflow_state(root, errors)

    return {
        "schema": "moduflow.project-validation.v1",
        "project_root": str(root),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    result = validate_project(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
