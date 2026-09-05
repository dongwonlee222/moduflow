"""Issue 112 prototype — execution-routing gates, simulated outside the repo.

Reuses the shipped regexes and metadata parser from worker_orchestrator so the
simulation reflects real parsing behaviour; adds only what Issue 112 owns:

  gate 1  semantic filter    keep unchecked, non-deferred, implementation work
  gate 2  boundary check     every survivor needs a file/glob and resolvable deps
  gate 3  routing decision   exactly one of inline | superpowers-sdd

Fail-closed at plan level (benchmark line 68): if any surviving task lacks a
boundary the whole plan is refused, nothing is written, and the caller is sent
back to product:plan.

Nothing here writes to the repository. `written` is always [].
"""
import fnmatch
import re
import sys
from pathlib import Path

# specs/<issue>/evidence/ -> repository root. Resolved from this file's own
# location so the evidence runs from any clone; the absolute project_root this
# prototype exists to remove must not reappear here.
REPO_DEFAULT = Path(__file__).resolve().parents[3]
if str(REPO_DEFAULT) not in sys.path:
    sys.path.insert(0, str(REPO_DEFAULT))

from scripts.worker_orchestrator import (  # noqa: E402
    CHECKBOX_RE,
    DEFERRED_RE,
    parse_task_metadata,
    task_has_shared_state_risk,
)

# Sections whose checkboxes are gates, evidence or findings rather than work.
# Grounded in the real corpus: "Required Gates" alone holds 34 checkboxes, e.g.
# "All 13 Issue 102 acceptance criteria have test or status evidence."
#
# Matched whole, never as a substring. Substring matching swallowed four real
# test-writing tasks under "Stream 3 — Tests + verification (gate)". Gate 1 is
# deliberately conservative: anything it is unsure about falls through to
# Gate 2, which refuses work that has no usable boundary anyway.
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


def _is_non_implementation_section(section):
    normalized = " ".join(section.strip().lower().split())
    if not normalized:
        return False
    normalized = STREAM_PREFIX_RE.sub("", normalized)
    return normalized in NON_IMPLEMENTATION_SECTIONS


def scan_tasks(tasks_path):
    """Same tasks parse_tasks returns, plus the source section and a stable id.

    Ids are positional in the source and are assigned before any filtering, so
    a `[depends: T01]` written by a human keeps pointing at the same line no
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
    """Unchecked, not deferred, and not sitting under a gate/evidence section."""
    return [
        task
        for task in tasks
        if task["status"] == "ready"
        and not _is_non_implementation_section(task["section"])
    ]


def gate2_gaps(executable, all_tasks):
    """Every survivor needs a boundary, and every dependency must be real.

    A dependency on an already-completed task is satisfied, not a gap — that is
    what shipped `dispatchable_now` does (w_o.py:246), and the opposite rule
    would make a spec degrade to `needs_plan` as its own work progresses.
    A dependency is only a gap when it points at nothing, or at work that moved
    to another issue.
    """
    executable_ids = {task["id"] for task in executable}
    done_ids = {task["id"] for task in all_tasks if task["status"] == "done"}
    deferred = {task["id"]: task["deferred_to"] for task in all_tasks
                if task["status"] == "deferred"}
    gaps = []
    for task in executable:
        if not task["expected_files"] and not task["expected_globs"]:
            gaps.append(f"{task['id']} declares no file or glob boundary")
        for dependency in task["dependencies"]:
            if dependency in executable_ids or dependency in done_ids:
                continue
            if dependency in deferred:
                gaps.append(
                    f"{task['id']} depends on {dependency}, which moved to "
                    f"{deferred[dependency]}"
                )
            else:
                gaps.append(f"{task['id']} depends on {dependency}, which does not exist")
    return gaps


def _boundary(task):
    return set(task["expected_files"]) | set(task["expected_globs"])


def _is_pattern(entry):
    return any(ch in entry for ch in "*?[")


def _collision(task_a, task_b):
    """Whether two declared boundaries can touch the same file.

    Raw string comparison is not enough: `scripts/*` and
    `scripts/validate_a.py` are different strings and the same file.
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

    inline is a normal success, not a fallback: Anthropic's own guidance warns
    that simple, sequential, single-file and shared-context work should be done
    directly rather than delegated (benchmark line 39).
    """
    if len(executable) == 1:
        return "inline", "single task; nothing to divide"
    shared = [task["id"] for task in executable if task_has_shared_state_risk(task)]
    if shared:
        return "inline", f"shared state touched by {', '.join(shared)}"
    for i, task in enumerate(executable):
        for other in executable[i + 1:]:
            hit = _collision(task, other)
            if hit:
                return "inline", f"{task['id']} and {other['id']} collide: {hit}"
    return (
        "superpowers-sdd",
        f"{len(executable)} tasks with disjoint boundaries and no shared state",
    )


def build_routing(tasks, project_root):
    """One host-neutral routing result. Never writes, never claims dispatch."""
    project_root = Path(project_root).resolve()
    base = {
        "schema": "moduflow.execution-routing.v1-prototype",
        "project_root": ".",
        "written": [],
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
        "tasks": executable,
        "next_command": f"product:execute ({backend})",
    }
