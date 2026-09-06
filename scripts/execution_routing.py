#!/usr/bin/env python3
"""Issue 112 — the execution-routing gates, host-neutral and write-free.

  gate 1  semantic filter    keep unchecked, non-deferred implementation work
  gate 2  boundary check     every survivor needs a boundary and real deps
  gate 3  routing decision   exactly one of inline | superpowers-sdd

Ported from `specs/112-execution-planner-and-backend-boundary/evidence/`, whose
prototype was run against all 55 specs on 2026-09-05. The shipped regexes and
metadata parser are imported rather than copied so this module cannot drift
from what `worker_orchestrator` actually reads.

Each selected task carries `cognitive_demand` and `isolation` — intent the host
adapter needs, in words that name no model and no worktree. Mapping them to a
host is `scripts/execution_host_adapter.py`, never this module.

Nothing here writes: `written` is always []. Gate 2 fails closed at plan level
(spec §6.2) — one gap refuses the whole plan, so the caller has nothing to
persist and no partial plan can read as a complete one.
"""
import fnmatch
import re
from pathlib import Path

try:
    from scripts.worker_orchestrator import (
        CHECKBOX_RE,
        DEFERRED_RE,
        WORKER_COGNITIVE_DEMAND,
        assign_worker,
        parse_task_metadata,
        task_has_shared_state_risk,
    )
except ImportError:  # pragma: no cover - direct script execution fallback
    from worker_orchestrator import (
        CHECKBOX_RE,
        DEFERRED_RE,
        WORKER_COGNITIVE_DEMAND,
        assign_worker,
        parse_task_metadata,
        task_has_shared_state_risk,
    )


ROUTING_SCHEMA = "moduflow.execution-routing.v1"

# Sections whose checkboxes are gates, evidence or findings rather than work.
# Grounded in the corpus: "Required Gates" alone holds 34 checkboxes, e.g.
# "All 13 Issue 102 acceptance criteria have test or status evidence."
#
# Matched whole, never as a substring. Substring matching on `verification` was
# measured to swallow four real test-writing tasks under
# "Stream 3 — Tests + verification (gate)". Gate 1 is deliberately conservative:
# anything it is unsure about falls through to Gate 2, which refuses work with
# no usable boundary anyway. New names belong in this set (spec §14 keeps the
# growth path here rather than in a branch).
NON_IMPLEMENTATION_SECTIONS = frozenset(
    {
        "required gates",
        "gates recap",
        "acceptance coverage",
        "acceptance criteria",
        "verification",
        "verification per task",
        "converge findings (auto)",
        "next",
        "next command",
    }
)
STREAM_PREFIX_RE = re.compile(r"^stream\s+\S+\s*[—–-]\s*")

# The pipe form specs 103, 109 and 110 authored — `| Files: …` — which
# METADATA_RE does not match. Detected only to name the gap correctly, never
# parsed: reading it here would silently bless a second boundary notation.
PIPE_BOUNDARY_RE = re.compile(r"\|\s*(?:files|globs)\s*:", re.IGNORECASE)

GAP_NO_BOUNDARY = "no_boundary"
GAP_UNREADABLE_NOTATION = "unreadable_notation"
GAP_DANGLING_DEPENDENCY = "dangling_dependency"


def _is_non_implementation_section(section):
    normalized = " ".join(section.strip().lower().split())
    if not normalized:
        return False
    normalized = STREAM_PREFIX_RE.sub("", normalized)
    return normalized in NON_IMPLEMENTATION_SECTIONS


def _gap(task_id, kind, message):
    """A gap is addressed to one task and says which fix it needs (§6.2)."""
    return {"task_id": task_id, "kind": kind, "message": message}


def scan_tasks(tasks_path):
    """What `parse_tasks` returns, plus the source section and a stable id.

    Ids are positional in the source and assigned before any filtering, so a
    `[depends: T01]` written by a human keeps pointing at the same line no
    matter what later gates drop.
    """
    tasks = []
    section = ""
    index = 0
    for line in Path(tasks_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            section = line.lstrip("#").strip()
            continue
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
        index += 1
        tasks.append(
            {
                "id": f"T{index:02d}",
                "text": text,
                "status": status,
                "section": section,
                "deferred_to": deferred_to,
                "expected_files": metadata["files"],
                "expected_globs": metadata["globs"],
                "dependencies": metadata["depends"],
                "declared_shared_state": metadata["shared_state"],
            }
        )
    return tasks


def gate1_executable(tasks):
    """Unchecked, not deferred, and not under a gate/evidence section."""
    return [
        task
        for task in tasks
        if task["status"] == "ready"
        and not _is_non_implementation_section(task["section"])
    ]


def _boundary_gap(task):
    if task["expected_files"] or task["expected_globs"]:
        return None
    if PIPE_BOUNDARY_RE.search(task["text"]):
        # The author did write a boundary. Reporting this as "declares no
        # boundary" sends them looking for something already in the file.
        return _gap(
            task["id"],
            GAP_UNREADABLE_NOTATION,
            f"{task['id']} declares its boundary in the `| Files: …` form, which the "
            f"parser does not read; rewrite it as `[files: …]`",
        )
    return _gap(task["id"], GAP_NO_BOUNDARY, f"{task['id']} declares no file or glob boundary")


def gate2_gaps(executable, all_tasks):
    """Every survivor needs a boundary, and every dependency must be real.

    A dependency on an already-completed task is satisfied, not a gap — that is
    what shipped `dispatchable_now` does (spec §5), and the opposite rule would
    make a spec degrade to `needs_plan` as its own work progresses. A dependency
    is a gap only when it points at nothing, or at work that moved elsewhere.
    """
    executable_ids = {task["id"] for task in executable}
    done_ids = {task["id"] for task in all_tasks if task["status"] == "done"}
    deferred = {
        task["id"]: task["deferred_to"]
        for task in all_tasks
        if task["status"] == "deferred"
    }
    gaps = []
    for task in executable:
        boundary_gap = _boundary_gap(task)
        if boundary_gap:
            gaps.append(boundary_gap)
        for dependency in task["dependencies"]:
            if dependency in executable_ids or dependency in done_ids:
                continue
            if dependency in deferred:
                detail = f"which moved to {deferred[dependency]}"
            else:
                detail = "which does not exist"
            gaps.append(
                _gap(
                    task["id"],
                    GAP_DANGLING_DEPENDENCY,
                    f"{task['id']} depends on {dependency}, {detail}",
                )
            )
    return gaps


def _boundary(task):
    return set(task["expected_files"]) | set(task["expected_globs"])


def _is_pattern(entry):
    return any(character in entry for character in "*?[")


def _collision(task_a, task_b):
    """Whether two declared boundaries can touch the same file.

    Raw string comparison is not enough: `scripts/*` and
    `scripts/validate_a.py` are different strings and the same file. Measured
    on specs/027, where that comparison sent two parallel workers at one file.
    """
    for left, right in ((task_a, task_b), (task_b, task_a)):
        for entry in _boundary(left):
            for other in _boundary(right):
                if entry == other:
                    return entry
                if _is_pattern(other) and fnmatch.fnmatch(entry, other):
                    return f"{entry} falls under {other}"
    return None


def gate3_backend(executable):
    """Exactly one backend, with the reason that chose it.

    `inline` is a normal success, not a fallback: current guidance warns that
    simple, sequential, single-file and shared-context work should be done
    directly rather than delegated
    (`knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`,
    line 39).
    """
    if len(executable) == 1:
        return "inline", "single task; nothing to divide"
    shared = [task["id"] for task in executable if task_has_shared_state_risk(task)]
    if shared:
        return "inline", f"shared state touched by {', '.join(shared)}"
    for position, task in enumerate(executable):
        for other in executable[position + 1:]:
            hit = _collision(task, other)
            if hit:
                return "inline", f"{task['id']} and {other['id']} collide: {hit}"
    return (
        "superpowers-sdd",
        f"{len(executable)} tasks with disjoint boundaries and no shared state",
    )


def _cognitive_demand(task):
    """How hard the work is, said without naming a model (host adapter design).

    `WORKER_COGNITIVE_DEMAND` is a role-to-demand table with no host in it, so
    the mapping is intent and belongs upstream of any host. Imported rather than
    copied for the same reason the parser is: two tables would drift, and the
    one in `worker_orchestrator` is the one that has been in use.
    """
    return WORKER_COGNITIVE_DEMAND.get(assign_worker(task["text"]), "balanced")


def _isolation_requirement(task, backend):
    """Whether the work needs its own workspace — not how one is made.

    `isolated` does not name a worktree; that is the adapter's job. Today this
    is implied only by the worktree string existing in `worker_orchestrator`,
    which is why a `codex/` prefix leaked into every plan (spec §8).

    Written per task even though gate 3 already forces `inline` whenever any
    task declares shared state, so the two clauses cannot presently disagree.
    The design puts the field on the task, and a later gate 3 that isolates only
    the risky tasks must not need this line rewritten.
    """
    if backend == "inline" or task_has_shared_state_risk(task):
        return "shared"
    return "isolated"


def _with_intent(task, backend):
    """A new dict, so gate 1 stays a filter and its survivors stay untouched."""
    return {
        **task,
        "cognitive_demand": _cognitive_demand(task),
        "isolation": _isolation_requirement(task, backend),
    }


def build_routing(tasks, project_root="."):
    """One host-neutral routing result. Never writes, never claims dispatch.

    `project_root` is accepted so callers pass the root they scanned, but the
    emitted value is always repository-relative (§7). Measured 2026-09-05: 9 of
    the 10 committed `worker-plan.json` files name an absolute directory that
    does not exist on this machine, so the routing result addresses the project
    it was invoked on as `.` rather than carrying one machine's layout.
    """
    del project_root
    base = {
        "schema": ROUTING_SCHEMA,
        "project_root": ".",
        "written": [],
        # Explicit rather than omitted, so "ModuFlow did not run this" is
        # assertable in a test instead of merely implied (§7).
        "dispatched": False,
        "executed_by": None,
    }

    executable = gate1_executable(tasks)
    if not executable:
        return {
            **base,
            "status": "not_applicable",
            "backend": None,
            "routing_reason": "no unfinished implementation task in this spec",
            "gaps": [],
            "tasks": [],
            "next_command": "product:status",
        }

    gaps = gate2_gaps(executable, tasks)
    if gaps:
        return {
            **base,
            "status": "needs_plan",
            "backend": None,
            "routing_reason": "refused: executable work has no usable boundary",
            "gaps": gaps,
            "tasks": [],
            "next_command": "product:plan",
        }

    backend, reason = gate3_backend(executable)
    return {
        **base,
        "status": "ok",
        "backend": backend,
        "routing_reason": reason,
        "gaps": [],
        # Intent only. `cognitive_demand` and `isolation` are what
        # `scripts/execution_host_adapter.py` needs; neither names a model or a
        # worktree, so adding a host still changes no canonical artifact.
        "tasks": [_with_intent(task, backend) for task in executable],
        "next_command": f"product:execute ({backend})",
    }
