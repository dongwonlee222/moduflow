#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


WORKER_RULES = [
    ("qa-reviewer", ["qa", "test", "verify", "verification", "regression", "acceptance verification"]),
    ("pm-strategist", ["pm", "acceptance", "criteria", "scope", "stakeholder", "opportunity"]),
    ("spec-architect", ["spec", "prd", "requirements", "architecture", "interface"]),
    ("roadmap-planner", ["roadmap", "priority", "prioritize", "queue", "milestone"]),
    ("ux-flow-worker", ["design", "ux", "prototype", "flow", "figma", "onboarding"]),
    ("data-reviewer", ["data", "metric", "analytics", "kpi", "benchmark", "report"]),
    ("release-manager", ["release", "deploy", "rollback", "upgrade", "publish", "docs"]),
    ("implementation-worker", ["implementation", "code", "script", "command", "api", "schema"]),
]

DEFAULT_WORKER = "implementation-worker"
SHARED_STATE_KEYWORDS = ["shared", "state", "migration", "schema", "config", "lock", "registry"]
CHECKBOX_RE = re.compile(r"^\s*-\s+\[(?P<status>[ xX])\]\s+(?P<text>.+?)\s*$")
METADATA_RE = re.compile(r"\s*\[(?P<key>files|globs|depends|shared_state):\s*(?P<value>[^\]]*)\]")


def split_csv(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_task_metadata(task_text):
    metadata = {"files": [], "globs": [], "depends": [], "shared_state": None}

    def collect(match):
        key = match.group("key")
        value = match.group("value").strip()
        if key in {"files", "globs", "depends"}:
            metadata[key] = split_csv(value)
        elif key == "shared_state":
            metadata[key] = value.lower() in {"1", "true", "yes", "y"}
        return ""

    clean_text = METADATA_RE.sub(collect, task_text).strip()
    return clean_text, metadata


def parse_tasks(tasks_path):
    tasks = []
    if not tasks_path.exists():
        raise FileNotFoundError(f"Missing tasks file: {tasks_path}")

    for line in tasks_path.read_text(encoding="utf-8").splitlines():
        match = CHECKBOX_RE.match(line)
        if not match:
            continue
        raw_text = match.group("text").strip()
        if not raw_text:
            continue
        text, metadata = parse_task_metadata(raw_text)
        tasks.append(
            {
                "text": text,
                "status": "done" if match.group("status").lower() == "x" else "ready",
                "expected_files": metadata["files"],
                "expected_globs": metadata["globs"],
                "dependencies": metadata["depends"],
                "declared_shared_state": metadata["shared_state"],
            }
        )
    if not tasks:
        raise ValueError(f"No checkbox tasks found in {tasks_path}")
    return tasks


def explicit_worker_prefix(task_text):
    prefix = task_text.split(":", 1)[0].strip().lower()
    aliases = {
        "pm": "pm-strategist",
        "product": "pm-strategist",
        "spec": "spec-architect",
        "roadmap": "roadmap-planner",
        "design": "ux-flow-worker",
        "ux": "ux-flow-worker",
        "data": "data-reviewer",
        "qa": "qa-reviewer",
        "release": "release-manager",
        "implementation": "implementation-worker",
        "code": "implementation-worker",
    }
    return aliases.get(prefix)


def assign_worker(task_text):
    explicit = explicit_worker_prefix(task_text)
    if explicit:
        return explicit
    normalized = task_text.lower()
    for worker, keywords in WORKER_RULES:
        if any(keyword in normalized for keyword in keywords):
            return worker
    return DEFAULT_WORKER


def task_has_shared_state_risk(task):
    if isinstance(task, str):
        normalized = task.lower()
        return any(keyword in normalized for keyword in SHARED_STATE_KEYWORDS)
    if task.get("declared_shared_state") is not None:
        return bool(task["declared_shared_state"])
    normalized = task["text"].lower()
    values = task.get("expected_files", []) + task.get("expected_globs", [])
    return any(keyword in normalized for keyword in SHARED_STATE_KEYWORDS) or any(
        any(keyword in value.lower() for keyword in SHARED_STATE_KEYWORDS)
        for value in values
    )


def worker_files(root):
    workers_root = Path(root).resolve() / "workers"
    if not workers_root.exists():
        return []
    return sorted(path.stem for path in workers_root.glob("*.md"))


def configured_workers():
    return sorted({worker for worker, _keywords in WORKER_RULES} | {DEFAULT_WORKER})


def dead_worker_files(root):
    configured = set(configured_workers())
    return [worker for worker in worker_files(root) if worker not in configured]


def overlapping_file_risks(planned_tasks):
    owners = {}
    risks = []
    for task in planned_tasks:
        for file_path in task["expected_files"]:
            if file_path in owners:
                risks.append(
                    f"{file_path} is expected by {owners[file_path]} and {task['id']}"
                )
            else:
                owners[file_path] = task["id"]
    return risks


def merge_order(planned_tasks):
    remaining = {task["id"]: task for task in planned_tasks}
    ordered = []
    while remaining:
        progressed = False
        for task_id, task in list(remaining.items()):
            dependencies = task.get("dependencies", [])
            if all(dependency in ordered or dependency not in remaining for dependency in dependencies):
                ordered.append(task_id)
                del remaining[task_id]
                progressed = True
        if not progressed:
            ordered.extend(sorted(remaining))
            break
    return ordered


def build_worker_plan(root, issue_id):
    project_root = Path(root).resolve()
    spec_root = project_root / "specs" / issue_id
    raw_tasks = parse_tasks(spec_root / "tasks.md")

    planned_tasks = []
    risks = []
    worker_groups = {}
    for index, task in enumerate(raw_tasks, start=1):
        task_id = f"T{index:02d}"
        worker = assign_worker(task["text"])
        shared_state_risk = task_has_shared_state_risk(task)
        if worker not in worker_groups:
            worker_groups[worker] = f"group-{len(worker_groups) + 1}"
        parallel_group = worker_groups[worker] if not shared_state_risk else "sequential"
        if shared_state_risk:
            risks.append(f"Task {index} touches shared state: {task['text']}")
        planned_tasks.append(
            {
                "id": task_id,
                "text": task["text"],
                "status": task["status"],
                "worker": worker,
                "worker_file": f"workers/{worker}.md",
                "parallel_group": parallel_group,
                "shared_state_risk": shared_state_risk,
                "expected_files": task["expected_files"],
                "expected_globs": task["expected_globs"],
                "dependencies": task["dependencies"],
                "isolation": {
                    "worktree": f"codex/{issue_id}-{task_id.lower()}",
                    "merge_after": task["dependencies"],
                },
            }
        )

    file_risks = overlapping_file_risks(planned_tasks)
    risks.extend(file_risks)
    unique_workers = {task["worker"] for task in planned_tasks if not task["shared_state_risk"]}
    eligible = len(unique_workers) >= 2 and not risks
    mode = "parallel-eligible" if eligible else "sequential"

    return {
        "schema": "moduflow.worker-plan.v1",
        "issue_id": issue_id,
        "project_root": str(project_root),
        "workers": {
            "configured": configured_workers(),
            "files": worker_files(project_root),
            "dead_workers": dead_worker_files(project_root),
        },
        "parallel": {
            "eligible": eligible,
            "mode": mode,
            "risks": risks,
            "merge_order": merge_order(planned_tasks),
            "fallback": "sequential" if not eligible else None,
            "criteria": [
                "separate worker domains",
                "non-overlapping expected files",
                "no shared-state risk",
                "dependency-aware merge order",
            ],
        },
        "tasks": planned_tasks,
        "next_command": f"product:execute {issue_id}",
    }


def render_worker_plan_markdown(plan):
    lines = [
        f"# Worker Plan: {plan['issue_id']}",
        "",
        f"Mode: `{plan['parallel']['mode']}`",
        f"Parallel eligible: `{str(plan['parallel']['eligible']).lower()}`",
        "",
        "## Tasks",
        "",
        "| ID | Worker | Group | Status | Files | Depends | Task |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for task in plan["tasks"]:
        files = ", ".join(task["expected_files"] + task["expected_globs"]) or "-"
        depends = ", ".join(task["dependencies"]) or "-"
        lines.append(
            f"| {task['id']} | `{task['worker']}` | `{task['parallel_group']}` | {task['status']} | {files} | {depends} | {task['text']} |"
        )

    lines.extend(["", "## Isolation", ""])
    for task in plan["tasks"]:
        lines.append(f"- {task['id']}: `{task['isolation']['worktree']}`")

    lines.extend(["", "## Merge Order", "", "- " + " → ".join(plan["parallel"]["merge_order"])])

    lines.extend(["", "## Worker Inventory", ""])
    if plan["workers"]["dead_workers"]:
        lines.extend(f"- Unrouted worker file: `workers/{worker}.md`" for worker in plan["workers"]["dead_workers"])
    else:
        lines.append("- All worker files are covered by routing rules.")

    lines.extend(["", "## Risks", ""])
    if plan["parallel"]["risks"]:
        lines.extend(f"- {risk}" for risk in plan["parallel"]["risks"])
    else:
        lines.append("- None.")

    lines.extend(["", "## Next Command", "", f"`{plan['next_command']}`", ""])
    return "\n".join(lines)


def write_worker_plan(root, issue_id):
    project_root = Path(root).resolve()
    spec_root = project_root / "specs" / issue_id
    plan = build_worker_plan(project_root, issue_id)
    spec_root.mkdir(parents=True, exist_ok=True)
    (spec_root / "worker-plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (spec_root / "worker-plan.md").write_text(render_worker_plan_markdown(plan), encoding="utf-8")
    return {
        "issue_id": issue_id,
        "written": ["worker-plan.json", "worker-plan.md"],
        "parallel": plan["parallel"],
    }


def main():
    parser = argparse.ArgumentParser(description="Generate a ModuFlow worker plan for an issue.")
    parser.add_argument("issue_id")
    parser.add_argument("--root", default=".")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    try:
        result = write_worker_plan(args.root, args.issue_id) if args.write else build_worker_plan(args.root, args.issue_id)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
