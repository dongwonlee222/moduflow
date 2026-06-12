#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


WORKER_RULES = [
    ("pm-strategist", ["pm", "acceptance", "criteria", "scope", "stakeholder", "opportunity"]),
    ("ux-flow-worker", ["design", "ux", "prototype", "flow", "figma", "onboarding"]),
    ("data-reviewer", ["data", "metric", "analytics", "kpi", "benchmark", "report"]),
    ("qa-reviewer", ["qa", "test", "verify", "verification", "regression", "acceptance"]),
    ("release-manager", ["release", "deploy", "rollback", "upgrade", "publish", "docs"]),
    ("implementation-worker", ["implementation", "code", "script", "command", "api", "schema"]),
]

DEFAULT_WORKER = "implementation-worker"
SHARED_STATE_KEYWORDS = ["shared", "state", "migration", "schema", "config", "lock", "registry"]
CHECKBOX_RE = re.compile(r"^\s*-\s+\[(?P<status>[ xX])\]\s+(?P<text>.+?)\s*$")


def parse_tasks(tasks_path):
    tasks = []
    if not tasks_path.exists():
        raise FileNotFoundError(f"Missing tasks file: {tasks_path}")

    for line in tasks_path.read_text(encoding="utf-8").splitlines():
        match = CHECKBOX_RE.match(line)
        if not match:
            continue
        text = match.group("text").strip()
        if not text:
            continue
        tasks.append(
            {
                "text": text,
                "status": "done" if match.group("status").lower() == "x" else "ready",
            }
        )
    if not tasks:
        raise ValueError(f"No checkbox tasks found in {tasks_path}")
    return tasks


def assign_worker(task_text):
    normalized = task_text.lower()
    for worker, keywords in WORKER_RULES:
        if any(keyword in normalized for keyword in keywords):
            return worker
    return DEFAULT_WORKER


def task_has_shared_state_risk(task_text):
    normalized = task_text.lower()
    return any(keyword in normalized for keyword in SHARED_STATE_KEYWORDS)


def build_worker_plan(root, issue_id):
    project_root = Path(root).resolve()
    spec_root = project_root / "specs" / issue_id
    raw_tasks = parse_tasks(spec_root / "tasks.md")

    planned_tasks = []
    risks = []
    worker_groups = {}
    for index, task in enumerate(raw_tasks, start=1):
        worker = assign_worker(task["text"])
        shared_state_risk = task_has_shared_state_risk(task["text"])
        if worker not in worker_groups:
            worker_groups[worker] = f"group-{len(worker_groups) + 1}"
        parallel_group = worker_groups[worker] if not shared_state_risk else "sequential"
        if shared_state_risk:
            risks.append(f"Task {index} touches shared state: {task['text']}")
        planned_tasks.append(
            {
                "id": f"T{index:02d}",
                "text": task["text"],
                "status": task["status"],
                "worker": worker,
                "worker_file": f"workers/{worker}.md",
                "parallel_group": parallel_group,
                "shared_state_risk": shared_state_risk,
            }
        )

    unique_workers = {task["worker"] for task in planned_tasks if not task["shared_state_risk"]}
    eligible = len(unique_workers) >= 2 and not risks
    mode = "parallel-eligible" if eligible else "sequential"

    return {
        "schema": "moduflow.worker-plan.v1",
        "issue_id": issue_id,
        "project_root": str(project_root),
        "parallel": {
            "eligible": eligible,
            "mode": mode,
            "risks": risks,
            "criteria": [
                "separate worker domains",
                "independent acceptance checks",
                "low shared-state risk",
                "clear merge order",
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
        "| ID | Worker | Group | Status | Task |",
        "| --- | --- | --- | --- | --- |",
    ]
    for task in plan["tasks"]:
        lines.append(
            f"| {task['id']} | `{task['worker']}` | `{task['parallel_group']}` | {task['status']} | {task['text']} |"
        )

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
