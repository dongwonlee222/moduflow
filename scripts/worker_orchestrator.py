#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from scripts import project_operation, project_registry
except ImportError:  # pragma: no cover - direct script execution fallback
    import project_operation
    import project_registry


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

# Cognitive demand levels. Keep these semantic first: the host agent reads this
# and picks the best available model on its platform.
# deep     -> most capable reasoning model (complex trade-offs, architecture)
# balanced -> standard production model (coding, review, UX)
# fast     -> lightest/fastest model (checklists, summaries, sorting)
#
# Current OpenAI example, if the GPT-5.6 family is available:
# deep     -> gpt-5.6-sol; use high/xhigh, or max/pro only for quality-first gates
# balanced -> gpt-5.6-terra; start at medium reasoning and tune with evals
# fast     -> gpt-5.6-luna; use low/none for latency or high-volume work
WORKER_COGNITIVE_DEMAND = {
    "spec-architect":        "deep",
    "pm-strategist":         "deep",
    "implementation-worker": "balanced",
    "qa-reviewer":           "balanced",
    "ux-flow-worker":        "balanced",
    "release-manager":       "fast",
    "roadmap-planner":       "fast",
    "data-reviewer":         "fast",
}

COGNITIVE_DEMAND_GUIDANCE = {
    "deep": (
        "use your most capable reasoning model. If using OpenAI GPT-5.6, "
        "prefer gpt-5.6-sol; reserve max reasoning or pro mode for the "
        "hardest quality-first gates after comparison against xhigh/high."
    ),
    "balanced": (
        "use your standard production model. If using OpenAI GPT-5.6, "
        "prefer gpt-5.6-terra with medium reasoning as the starting point, "
        "then compare one level lower on representative tasks."
    ),
    "fast": (
        "use your lightest, fastest model. If using OpenAI GPT-5.6, "
        "prefer gpt-5.6-luna with low or no reasoning for latency-sensitive "
        "or high-volume work."
    ),
}
CHECKBOX_RE = re.compile(r"^\s*-\s+\[(?P<status>[ xX])\]\s+(?P<text>.+?)\s*$")
# A task moved to another issue keeps its line so numbering and every
# `[depends:]` reference stay valid (C5). It is not work anyone can pick up
# here, so it must not be offered as dispatchable.
DEFERRED_RE = re.compile(r"^\[deferred\s*(?:\u2192|->)\s*(?P<target>[^\]]+)\]\s*")
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
        deferral = DEFERRED_RE.match(text)
        deferred_to = None
        if deferral:
            deferred_to = deferral.group("target").strip()
            text = text[deferral.end():].strip()
        if match.group("status").lower() == "x":
            status = "done"
        elif deferred_to:
            status = "deferred"
        else:
            status = "ready"
        tasks.append(
            {
                "text": text,
                "status": status,
                "deferred_to": deferred_to,
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


def dispatchable_now(planned_tasks):
    """Which tasks can start together right now, given what is already done.

    `merge_order` answers "in what order", which reads as a queue and invites
    doing one thing at a time. Eligibility is not fixed at planning time: it
    changes every time a task completes and unblocks its dependents. This
    answers "what can run together at this moment" so the window is visible
    without a human noticing it.
    """
    done = {task["id"] for task in planned_tasks if task.get("status") == "done"}
    deferred = [
        task["id"] for task in planned_tasks if task.get("status") == "deferred"
    ]
    open_tasks = [
        task
        for task in planned_tasks
        if task.get("status") not in ("done", "deferred")
    ]
    ready = [
        task
        for task in open_tasks
        if all(dependency in done for dependency in task.get("dependencies", []))
    ]
    selected, claimed = [], set()
    for task in ready:
        files = set(task.get("expected_files", [])) | set(task.get("expected_globs", []))
        if files & claimed:
            continue
        if selected and not files:
            # A task that declares no boundary cannot be proven disjoint.
            continue
        selected.append(task["id"])
        claimed |= files
    return {
        "ready": [task["id"] for task in ready],
        "dispatchable": selected,
        "blocked": [
            task["id"]
            for task in open_tasks
            if task["id"] not in {t["id"] for t in ready}
        ],
        # Reported, never silently dropped: a reader has to be able to tell a
        # task that moved elsewhere from one that simply is not ready.
        "deferred": deferred,
    }


def find_related_memories(
    project_root,
    expected_files,
    issue_id,
    *,
    project_context=None,
):
    project_root = Path(project_root).resolve()
    context = project_registry.context_for_operation(
        project_root,
        project_context=project_context,
    )
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("project_memory", project_root / "scripts/project_memory.py")
        project_memory = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(project_memory)
    except Exception:
        return []

    related = []
    for memory_file in project_memory.iter_memory_files(
        project_root,
        project_context=context,
    ):
        try:
            text = memory_file.read_text(encoding="utf-8")
            metadata, _ = project_memory.parse_frontmatter(text)
        except Exception:
            continue

        entry_id = metadata.get("id") or memory_file.stem
        title = metadata.get("title") or entry_id
        summary = metadata.get("summary") or ""

        depends_on = project_memory.parse_list_value(metadata.get("depends_on", "[]"))
        references = project_memory.parse_list_value(metadata.get("references", "[]"))
        supersedes = project_memory.parse_list_value(metadata.get("supersedes", "[]"))
        source_artifacts = project_memory.parse_list_value(metadata.get("source_artifacts", "[]"))
        spec_link = metadata.get("spec") or ""
        issue_link = metadata.get("issue_id") or ""

        is_relevant = False
        if issue_link and issue_id in issue_link:
            is_relevant = True

        for f in expected_files:
            if any(f in ref or ref in f for ref in references):
                is_relevant = True
            if any(f in art or art in f for art in source_artifacts):
                is_relevant = True
            if spec_link and (f in spec_link or spec_link in f):
                is_relevant = True

        if is_relevant:
            rel_path = str(memory_file.relative_to(project_root))
            related.append({
                "id": entry_id,
                "title": title,
                "path": rel_path,
                "summary": summary
            })

    return sorted(related, key=lambda x: x["id"])


def assemble_prompt_context(project_root, related_memories):
    if not related_memories:
        return ""

    lines = [
        "",
        "### Related Project Decisions",
        "",
        "The following past architectural decisions/rules are relevant to your task.",
        "Please use your tools to read the full file contents if you need details:",
    ]
    for mem in related_memories:
        lines.append(f"- [{mem['title']}](file:///{Path(project_root).resolve()}/{mem['path']}): {mem['summary']}")
    lines.append("")
    return "\n".join(lines)


def build_worker_plan(root, issue_id, *, project_context=None):
    project_root = Path(root).resolve()
    context = project_registry.context_for_operation(
        project_root,
        project_context=project_context,
    )
    spec_root = project_registry.canonical_child_path(context, "specs", issue_id)
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
        expected_files_str = ", ".join(task["expected_files"]) if task["expected_files"] else "none"
        related_mems = find_related_memories(
            project_root,
            task["expected_files"],
            issue_id,
            project_context=context,
        )
        context_block = assemble_prompt_context(project_root, related_mems)
        demand = WORKER_COGNITIVE_DEMAND.get(worker, "balanced")
        prompt = (
            f"Implement task: {task['text']}\n"
            f"Expected files: {expected_files_str}\n"
            f"Cognitive demand: {demand} — "
            + COGNITIVE_DEMAND_GUIDANCE.get(demand, COGNITIVE_DEMAND_GUIDANCE["balanced"])
        )
        if context_block:
            prompt += context_block

        planned_tasks.append(
            {
                "id": task_id,
                "text": task["text"],
                "status": task["status"],
                "deferred_to": task.get("deferred_to"),
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
                "subagent": {
                    "TypeName": "self",
                    "Role": f"ModuFlow {worker}",
                    "CognitiveDemand": WORKER_COGNITIVE_DEMAND.get(worker, "balanced"),
                    "Workspace": "share",
                    "Prompt": prompt,
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
            "now": dispatchable_now(planned_tasks),
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

    now = plan["parallel"].get("now") or {}
    dispatchable = now.get("dispatchable") or []
    by_id = {task["id"]: task for task in plan["tasks"]}
    lines.extend(["", "## Dispatchable Now", ""])
    if dispatchable:
        for task_id in dispatchable:
            files = ", ".join(by_id[task_id].get("expected_files", [])) or "-"
            lines.append(f"- `{task_id}` — {files}")
        if len(dispatchable) > 1:
            lines.append("")
            lines.append(
                "These declare no overlapping files and can start together. "
                "Eligibility changes as tasks complete; re-read this section after each one."
            )
    elif now.get("blocked"):
        lines.append("- None. Every remaining task is blocked or overlaps a started one.")
    else:
        lines.append("- None. No task is waiting to start.")
    deferred = now.get("deferred") or []
    if deferred:
        lines.append("")
        for task_id in deferred:
            target = by_id[task_id].get("deferred_to") or "another issue"
            lines.append(f"- `{task_id}` is deferred to `{target}`, not startable here.")
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


def write_worker_plan(root, issue_id, *, project_context=None):
    project_root = Path(root).resolve()
    context = project_registry.context_for_operation(
        project_root,
        project_context=project_context,
    )
    project_operation.require_project_capability(context, "write")
    spec_root = project_registry.canonical_child_path(context, "specs", issue_id)
    plan = build_worker_plan(
        project_root,
        issue_id,
        project_context=context,
    )
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


@project_operation.cli_denial_boundary
def main():
    parser = argparse.ArgumentParser(description="Generate a ModuFlow worker plan for an issue.")
    parser.add_argument("issue_id")
    parser.add_argument("--root", default=".")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    try:
        result = write_worker_plan(args.root, args.issue_id) if args.write else build_worker_plan(args.root, args.issue_id)
    except project_operation.ProjectOperationDenied:
        raise
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
