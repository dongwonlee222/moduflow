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

# Cognitive demand levels. Semantic only: how hard the work is, said without
# naming a model.
# deep     -> hardest reasoning (complex trade-offs, architecture)
# balanced -> standard production work (coding, review, UX)
# fast     -> lightest work (checklists, summaries, sorting)
#
# Which model and which effort level each tier maps to is host vocabulary and
# lives in `scripts/execution_host_adapter.py` (issue 112 §8). The concrete
# model names that used to be listed here reached every task prompt on every
# host through `COGNITIVE_DEMAND_GUIDANCE`; they are now in `CodexAdapter`,
# where they are true.
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

WORKER_PLAN_SCHEMA = "moduflow.worker-plan.v1"

# The host is configured, never guessed. Decision:
# `memory/decisions/2026-09-06-the-host-is-configured-with-a-per-run-override-never-guessed.md`.
# A guess that lands on the wrong host writes a wrong value into a canonical
# artifact silently — the defect this issue exists to remove — and a guess that
# lands on a registered name passes a gate that was supposed to refuse.
DEFAULT_EXECUTION_HOST = "claude-code"

CHECKBOX_RE = re.compile(r"^\s*-\s+\[(?P<status>[ xX])\]\s+(?P<text>.+?)\s*$")
# A task moved to another issue keeps its line so numbering and every
# `[depends:]` reference stay valid (C5). It is not work anyone can pick up
# here, so it must not be offered as dispatchable.
DEFERRED_RE = re.compile(r"^\[deferred\s*(?:\u2192|->)\s*(?P<target>[^\]]+)\]\s*")
METADATA_RE = re.compile(r"\s*\[(?P<key>files|globs|depends|shared_state):\s*(?P<value>[^\]]*)\]")


_SIBLINGS = {}


def _sibling(name):
    """Import a script that sits next to this one, at call time.

    `execution_routing` imports this module for the parser and the worker
    tables, so importing it back at module level would be circular. Deferring
    the import to the first call dissolves that, and loading by path keeps the
    pair together when `scripts/` is not on `sys.path`.
    """
    if name in _SIBLINGS:
        return _SIBLINGS[name]
    import importlib

    try:
        module = importlib.import_module(f"scripts.{name}")
    except ImportError:
        import importlib.util

        path = Path(__file__).resolve().parent / f"{name}.py"
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    _SIBLINGS[name] = module
    return module


def configured_host(root, override=None):
    """Which execution host this plan is being built for.

    Read from `.moduflow/config.json` as `execution.host`, defaulting to
    `claude-code`; any invocation may override it. Never inferred from the
    environment or the running process — see `DEFAULT_EXECUTION_HOST`.

    Never raises. A project without the key is every project today, and a
    throwing read here would break `product:workers` everywhere for a field
    nobody has written yet. An unknown *name* is a different matter and is
    refused by the adapter registry, which is the one place that decides it.
    """
    if override is not None:
        return override
    path = Path(root).resolve() / ".moduflow" / "config.json"
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return DEFAULT_EXECUTION_HOST
    execution = config.get("execution") if isinstance(config, dict) else None
    host = execution.get("host") if isinstance(execution, dict) else None
    if isinstance(host, str) and host.strip():
        return host.strip()
    return DEFAULT_EXECUTION_HOST


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


def dispatchable_now(planned_tasks, *, completed=(), deferred_elsewhere=()):
    """Which tasks can start together right now, given what is already done.

    `merge_order` answers "in what order", which reads as a queue and invites
    doing one thing at a time. Eligibility is not fixed at planning time: it
    changes every time a task completes and unblocks its dependents. This
    answers "what can run together at this moment" so the window is visible
    without a human noticing it.

    `completed` and `deferred_elsewhere` carry ids that are no longer in the
    list at all. Since issue 112 the caller passes only the tasks Gate 1 kept,
    so the done and deferred lines of `tasks.md` are gone by the time this runs
    — and without them every dependency on finished work would read as blocked.
    Spec §5 is explicit that a dependency on a completed task is satisfied, and
    Gate 2 was built to agree with this function.
    """
    done = {task["id"] for task in planned_tasks if task.get("status") == "done"}
    done |= set(completed)
    deferred = [
        task["id"] for task in planned_tasks if task.get("status") == "deferred"
    ]
    deferred += [
        task_id for task_id in deferred_elsewhere if task_id not in deferred
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


def assemble_prompt_context(related_memories):
    """The related-decision block, addressed by repository-relative path.

    The link used to be an absolute `file:///` URL. That put one machine's
    filesystem layout inside every task prompt in a Git-tracked artifact — the
    same defect §7 names for `project_root`, one level down and harder to see.
    """
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
        lines.append(f"- [{mem['title']}]({mem['path']}): {mem['summary']}")
    lines.append("")
    return "\n".join(lines)


def build_worker_plan(root, issue_id, *, project_context=None, host=None):
    """The worker plan, built from the routing gates rather than from checkboxes.

    Three things changed here in issue 112 T09 and each removes a way the old
    plan could look authoritative while being wrong:

    * the tasks are the ones `execution_routing` selected, so a `done`, a
      deferred and a Required-Gates checkbox never become work again — 514 of
      640 generated worker tasks were already `done` when this was measured;
    * a non-`ok` routing status is carried out to the caller instead of being
      turned into a plan, and `write_worker_plan` persists nothing on it;
    * every host-specific value — the branch prefix, the model name, the
      subagent record's shape — comes from the adapter for the configured host
      rather than from a `codex/` literal that was written on every host.

    Task ids are the ones the source file gave them and are never renumbered,
    so a human-written `[depends: T01]` still points at the same line after
    Gate 1 drops the tasks around it.
    """
    project_root = Path(root).resolve()
    context = project_registry.context_for_operation(
        project_root,
        project_context=project_context,
    )
    routing_module = _sibling("execution_routing")
    adapters = _sibling("execution_host_adapter")

    # Resolved before anything is read or built: an unregistered host refuses
    # here, and a refusal that happens after the work is a refusal nobody
    # believes. `UnregisteredHostError` propagates on purpose — there is no
    # generic adapter (decision 2026-09-06).
    host_id = configured_host(project_root, host)
    adapter = adapters.adapter_for(host_id)

    spec_root = project_registry.canonical_child_path(context, "specs", issue_id)
    tasks_path = spec_root / "tasks.md"
    if not tasks_path.exists():
        raise FileNotFoundError(f"Missing tasks file: {tasks_path}")

    scanned = routing_module.scan_tasks(tasks_path)
    routing = routing_module.build_routing(scanned, project_root, issue_id=issue_id)

    completed = [task["id"] for task in scanned if task["status"] == "done"]
    deferred = [
        {"id": task["id"], "deferred_to": task["deferred_to"]}
        for task in scanned
        if task["status"] == "deferred"
    ]

    planned_tasks = []
    risks = []
    worker_groups = {}
    for task in routing["tasks"]:
        task_id = task["id"]
        # Worker-role assignment stays this module's job; the routing result
        # carries how hard the work is, not who does it.
        worker = assign_worker(task["text"])
        shared_state_risk = task_has_shared_state_risk(task)
        if worker not in worker_groups:
            worker_groups[worker] = f"group-{len(worker_groups) + 1}"
        parallel_group = worker_groups[worker] if not shared_state_risk else "sequential"
        if shared_state_risk:
            risks.append(f"Task {task_id} touches shared state: {task['text']}")
        related_mems = find_related_memories(
            project_root,
            task["expected_files"],
            issue_id,
            project_context=context,
        )
        demand = task.get("cognitive_demand") or WORKER_COGNITIVE_DEMAND.get(worker, "balanced")
        requirement = task.get("isolation") or ("shared" if shared_state_risk else "isolated")
        # What the adapter is handed: the routing task, the worker role it does
        # not carry, and ModuFlow's own prompt context. No host value goes in
        # and none is invented here.
        adapter_task = {
            **task,
            "worker": worker,
            "cognitive_demand": demand,
            "isolation": requirement,
            "prompt_context": assemble_prompt_context(related_mems),
        }

        planned_tasks.append(
            {
                "id": task_id,
                "text": task["text"],
                "status": task["status"],
                "section": task.get("section", ""),
                "worker": worker,
                "worker_file": f"workers/{worker}.md",
                "parallel_group": parallel_group,
                "shared_state_risk": shared_state_risk,
                "expected_files": task["expected_files"],
                "expected_globs": task["expected_globs"],
                "dependencies": task["dependencies"],
                "cognitive_demand": demand,
                "isolation_requirement": requirement,
                "isolation": adapter.isolation(issue_id, task_id, requirement),
                "model": adapter.model(demand),
                "subagent": adapter.dispatch(adapter_task, routing),
            }
        )

    risks.extend(overlapping_file_risks(planned_tasks))
    # One routing decision, not two (§6.3). `risks` stays the detail — which
    # file, which task — but it no longer decides anything: Gate 3 does, and it
    # sees strictly more than this list does, since its collision check is path
    # containment rather than string equality.
    eligible = routing["backend"] == "superpowers-sdd"
    mode = "parallel-eligible" if eligible else "sequential"

    return {
        "schema": WORKER_PLAN_SCHEMA,
        "issue_id": issue_id,
        # Repository-relative (§7). Nine of the ten committed worker plans name
        # an absolute directory that does not exist on this machine.
        "project_root": routing["project_root"],
        # The file says which host it was built for. Without this the plan is
        # wrong about its own provenance, which is the design doc's complaint.
        "host": host_id,
        "status": routing["status"],
        "backend": routing["backend"],
        "routing_reason": routing["routing_reason"],
        "gaps": routing["gaps"],
        # Reported, never resolved (§9): a canonical task and a linked
        # Superpowers document disagreeing does not refuse a plan.
        "divergences": routing["divergences"],
        "dispatched": routing["dispatched"],
        "executed_by": routing["executed_by"],
        "deferred": deferred,
        "workers": {
            "configured": configured_workers(),
            "files": worker_files(project_root),
            "dead_workers": dead_worker_files(project_root),
        },
        "parallel": {
            "eligible": eligible,
            "mode": mode,
            "backend": routing["backend"],
            "routing_reason": routing["routing_reason"],
            "risks": risks,
            "merge_order": merge_order(planned_tasks),
            "now": dispatchable_now(
                planned_tasks,
                completed=completed,
                deferred_elsewhere=[entry["id"] for entry in deferred],
            ),
            "fallback": "sequential" if not eligible else None,
            "criteria": [
                "separate worker domains",
                "non-overlapping expected files",
                "no shared-state risk",
                "dependency-aware merge order",
            ],
        },
        "tasks": planned_tasks,
        "next_command": (
            f"product:execute {issue_id}"
            if routing["status"] == "ok"
            else routing["next_command"]
        ),
    }


def render_isolation_line(task):
    """One line per task, in the host's own words.

    A host that cannot honour `isolated` says so here. Rendering a blank would
    be the silent downgrade the adapter design's Known Limit forbids: the
    reader would see a plan that is not the plan they asked for.
    """
    record = task.get("isolation") or {}
    requirement = record.get("requirement") or task.get("isolation_requirement") or "shared"
    if not record.get("honoured", True):
        detail = record.get("detail") or "this host provides no such control"
        return f"- {task['id']}: `{requirement}` not honoured — {detail}"
    mechanism = record.get("mechanism") or "unspecified"
    line = f"- {task['id']}: `{requirement}` via `{mechanism}`"
    if record.get("workspace"):
        line += f" — `{record['workspace']}`"
    if record.get("detail"):
        line += f" ({record['detail']})"
    return line


def render_refusal_markdown(plan):
    """What a refusal looks like when someone renders one anyway.

    `write_worker_plan` never persists this — a refusal writes no file (§6.2) —
    but `build_worker_plan` returns non-`ok` results and a caller may render
    one. A refusal that renders as an empty plan reads as a plan.
    """
    lines = [
        f"# Worker Plan: {plan['issue_id']}",
        "",
        f"Status: `{plan['status']}` — no worker plan was written.",
        f"Host: `{plan['host']}`",
        f"Reason: {plan['routing_reason']}",
        "",
    ]
    if plan.get("gaps"):
        lines.extend(["## Gaps", ""])
        lines.extend(f"- `{gap['task_id']}` ({gap['kind']}): {gap['message']}" for gap in plan["gaps"])
        lines.append("")
    lines.extend(["## Next Command", "", f"`{plan['next_command']}`", ""])
    return "\n".join(lines)


def render_worker_plan_markdown(plan):
    if plan.get("status") not in (None, "ok"):
        return render_refusal_markdown(plan)
    lines = [
        f"# Worker Plan: {plan['issue_id']}",
        "",
        f"Host: `{plan.get('host', DEFAULT_EXECUTION_HOST)}`",
        f"Backend: `{plan['parallel'].get('backend')}` — {plan['parallel'].get('routing_reason', '')}",
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
        lines.append(render_isolation_line(task))

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
        targets = {entry["id"]: entry.get("deferred_to") for entry in plan.get("deferred") or []}
        lines.append("")
        for task_id in deferred:
            target = targets.get(task_id) or (by_id.get(task_id) or {}).get("deferred_to") or "another issue"
            lines.append(f"- `{task_id}` is deferred to `{target}`, not startable here.")
    lines.extend(["", "## Merge Order", "", "- " + " → ".join(plan["parallel"]["merge_order"])])

    if plan.get("divergences"):
        # §9: the canonical artifact wins and the disagreement is reported.
        lines.extend(["", "## Divergences", ""])
        lines.extend(f"- {finding['message']}" for finding in plan["divergences"])

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


def write_worker_plan(root, issue_id, *, project_context=None, host=None):
    """Persist the plan, or persist nothing and say why.

    Gate 2 fails closed at plan level (§6.2): one gap refuses the whole plan, so
    there is nothing partial to write and no half-plan that could read as a
    complete one. `not_applicable` writes nothing either — a finished spec is
    not a failure, and the two are reported as the different events they are.
    A stale plan from a previous run is left exactly as it was; overwriting it
    with a refusal would destroy the last thing that was true.
    """
    project_root = Path(root).resolve()
    context = project_registry.context_for_operation(
        project_root,
        project_context=project_context,
    )
    # Authorization first, before any read, build or host resolution. There is a
    # test asserting `build_worker_plan` is never reached on an archived
    # project.
    project_operation.require_project_capability(context, "write")
    spec_root = project_registry.canonical_child_path(context, "specs", issue_id)
    plan = build_worker_plan(
        project_root,
        issue_id,
        project_context=context,
        host=host,
    )
    if plan["status"] != "ok":
        return {
            "issue_id": issue_id,
            "host": plan["host"],
            "status": plan["status"],
            "backend": plan["backend"],
            "routing_reason": plan["routing_reason"],
            "gaps": plan["gaps"],
            "divergences": plan["divergences"],
            "written": [],
            "next_command": plan["next_command"],
        }
    spec_root.mkdir(parents=True, exist_ok=True)
    (spec_root / "worker-plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (spec_root / "worker-plan.md").write_text(render_worker_plan_markdown(plan), encoding="utf-8")
    return {
        "issue_id": issue_id,
        "host": plan["host"],
        "status": plan["status"],
        "backend": plan["backend"],
        "routing_reason": plan["routing_reason"],
        "gaps": plan["gaps"],
        "divergences": plan["divergences"],
        "written": ["worker-plan.json", "worker-plan.md"],
        "parallel": plan["parallel"],
        "next_command": plan["next_command"],
    }


@project_operation.cli_denial_boundary
def main():
    parser = argparse.ArgumentParser(description="Generate a ModuFlow worker plan for an issue.")
    parser.add_argument("issue_id")
    parser.add_argument("--root", default=".")
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--host",
        default=None,
        help=(
            "execution host for this run; overrides `execution.host` in "
            ".moduflow/config.json, which defaults to claude-code"
        ),
    )
    args = parser.parse_args()

    try:
        result = (
            write_worker_plan(args.root, args.issue_id, host=args.host)
            if args.write
            else build_worker_plan(args.root, args.issue_id, host=args.host)
        )
    except project_operation.ProjectOperationDenied:
        raise
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
