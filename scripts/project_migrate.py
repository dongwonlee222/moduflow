#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import project_doctor


DEFAULT_PATHS = {
    "issues": "issues",
    "specs": "specs",
    "workspace": "workspace",
    "knowledge": "knowledge",
    "memory": "memory",
    "workflow": "workflow",
    "profile": ".moduflow/project-profile.md",
    "environments": ".moduflow/environments.json",
    "integrations": ".moduflow/integrations.json",
}

MINIMAL_PM_DIRECTORIES = ["issues", "specs", "knowledge", "memory", "workflow"]

WORKSPACE_FILES = {
    "inbox.md": "# Inbox\n\n",
    "opportunities.md": "# Opportunities\n\n",
    "roadmap.md": "# Roadmap\n\n",
    "dashboard.md": "# Dashboard\n\n",
    "goal.md": "# Goal\n\n## Objective\n\nTBD\n\n## Status\n\nactive\n\n## Next Command\n\n`product:loop`\n",
}


def first_candidate(candidates, key, fallback):
    values = candidates.get(key, [])
    return values[0] if values else fallback


def build_config(project_root, mode, candidates):
    paths = dict(DEFAULT_PATHS)
    if mode == "mapped":
        paths["issues"] = first_candidate(candidates, "issues", paths["issues"])
        paths["specs"] = first_candidate(candidates, "specs", paths["specs"])
        paths["workspace"] = first_candidate(candidates, "workspace", paths["workspace"])
        knowledge_candidates = []
        for key in ["reports", "benchmarks", "research", "decisions", "data_notes"]:
            knowledge_candidates.extend(candidates.get(key, []))
        if knowledge_candidates:
            paths["knowledge"] = "knowledge"

    remote = project_doctor.git_remote(project_root) or ""
    return {
        "schema": "moduflow.config.v1",
        "project_name": project_root.name,
        "migration": {
            "mode": mode,
            "migrated_at": date.today().isoformat(),
            "source_candidates": candidates,
        },
        "git": {
            "required": True,
            "github_sync": "optional",
            "issue_source": "git-files",
            "remote": remote,
        },
        "paths": paths,
        "commands": {
            "start": "product:start",
            "status": "product:status",
            "doctor": "product:doctor",
            "migrate": "product:migrate",
            "profile": "product:profile",
        },
    }


def build_state():
    return {
        "schema": "moduflow.state.v1",
        "phase": "migrated",
        "active_issue": None,
        "last_command": "product:migrate",
        "next_command": "product:status",
        "blockers": [],
        "updated_at": date.today().isoformat(),
    }


def build_loop_state(project_root):
    today = date.today().isoformat()
    return {
        "schema": "moduflow.loop-state.v2",
        "loop_id": f"{project_root.name}-{today}",
        "goal_id": None,
        "objective": "",
        "issue_ids": [],
        "active_issue_id": None,
        "phase": "goal",
        "mode": "recommend",
        "status": "active",
        "next_command": "product:goal",
        "attempts": {
            "command": "product:goal",
            "count": 0,
            "max": 3,
            "last_changed_at": today,
        },
        "blocker": None,
        "last_action": "initialized lightweight ModuFlow project structure",
        "last_verification": None,
        "updated_at": today,
        "git_binding": {
            "mode": "git-files",
            "branch": None,
            "base_branch": None,
            "commits": [],
            "pull_request": None,
            "release": None,
            "execution_backend": {
                "type": "manual",
                "status": "not_selected",
                "reason": "",
                "session": None,
            },
        },
    }


def planned_writes(project_root, config):
    workspace_path = project_root / config["paths"]["workspace"]
    writes = []
    for relative in [".moduflow/config.json", ".moduflow/state.json"]:
        if not (project_root / relative).exists():
            writes.append(relative)
    for key in MINIMAL_PM_DIRECTORIES:
        relative = config["paths"].get(key, key)
        if not (project_root / relative).exists():
            writes.append(relative)
    for filename in WORKSPACE_FILES:
        target = workspace_path / filename
        if not target.exists():
            writes.append(str(target.relative_to(project_root)))
    loop_state = workspace_path / "loop-state.json"
    if not loop_state.exists():
        writes.append(str(loop_state.relative_to(project_root)))
    return writes


def build_migration_plan(path, mode="mapped", dry_run=True):
    requested = Path(path).resolve()
    detected_git_root = project_doctor.git_root(requested)
    project_root = detected_git_root or requested
    candidates = project_doctor.discover_candidate_paths(project_root)
    config = build_config(project_root, mode, candidates)
    return {
        "schema": "moduflow.migration-plan.v1",
        "project_root": str(project_root),
        "mode": mode,
        "dry_run": dry_run,
        "candidates": candidates,
        "config": config,
        "state": build_state(),
        "loop_state": build_loop_state(project_root),
        "writes": planned_writes(project_root, config),
        "preserves_existing_files": True,
    }


def write_json_if_missing(path, payload):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def write_text_if_missing(path, content):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def write_dir_if_missing(path):
    if path.exists():
        return False
    path.mkdir(parents=True, exist_ok=True)
    return True


def apply_migration_plan(plan):
    project_root = Path(plan["project_root"])
    written = []
    if write_json_if_missing(project_root / ".moduflow" / "config.json", plan["config"]):
        written.append(".moduflow/config.json")
    if write_json_if_missing(project_root / ".moduflow" / "state.json", plan["state"]):
        written.append(".moduflow/state.json")

    for key in MINIMAL_PM_DIRECTORIES:
        relative = plan["config"]["paths"].get(key, key)
        if write_dir_if_missing(project_root / relative):
            written.append(relative)

    workspace_path = project_root / plan["config"]["paths"]["workspace"]
    for filename, content in WORKSPACE_FILES.items():
        target = workspace_path / filename
        if write_text_if_missing(target, content):
            written.append(str(target.relative_to(project_root)))
    loop_state_path = workspace_path / "loop-state.json"
    if write_json_if_missing(loop_state_path, plan["loop_state"]):
        written.append(str(loop_state_path.relative_to(project_root)))

    plan["written"] = written
    return plan


def main():
    parser = argparse.ArgumentParser(description="Plan or apply a non-destructive ModuFlow project migration.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--mode", choices=["overlay", "mapped", "canonical"], default="mapped")
    parser.add_argument("--write", action="store_true", help="Write missing ModuFlow metadata and index files.")
    args = parser.parse_args()

    if args.mode == "canonical" and args.write:
        print("canonical mode is planning-only in this version; it will not move files.", file=sys.stderr)
        return 2

    plan = build_migration_plan(args.project_path, mode=args.mode, dry_run=not args.write)
    if args.write:
        plan = apply_migration_plan(plan)

    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
