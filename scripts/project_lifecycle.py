#!/usr/bin/env python3
"""Artifact lifecycle sync (048).

Canonical lifecycle and dependencies come from the shared issue schema model,
which preserves Markdown `**Status:**` / `**Blocked-by:**` compatibility. This
module projects that model into lifecycle views (.moduflow/state.json + the
dashboard's Active Issue section) and detects drift by consensus. It does NOT
write back to issue files (canonical source is human-authored).
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path

try:
    from scripts.project_issue_schema import (
        evaluate_project,
        markdown_blocked_by,
        markdown_priority,
        markdown_status,
        markdown_title,
        metadata_region,
    )
except ModuleNotFoundError:
    from project_issue_schema import (
        evaluate_project,
        markdown_blocked_by,
        markdown_priority,
        markdown_status,
        markdown_title,
        metadata_region,
    )


_READY_BLOCKING_DIAGNOSTICS = {
    "ISSUE_SCHEMA_MALFORMED",
    "ISSUE_SCHEMA_UNSUPPORTED",
    "ISSUE_DUPLICATE_FIELD",
    "ISSUE_STATE_PROJECTION_MISMATCH",
    "ISSUE_DEPENDENCY_PROJECTION_MISMATCH",
    "ISSUE_AUX_STATUS_INVALID",
    "ISSUE_DEPENDENCY_UNMET",
    "ISSUE_DEPENDENCY_DANGLING",
    "ISSUE_DEPENDENCY_CYCLE",
}
_LIFECYCLE_SCHEMA_DIAGNOSTICS = {
    "ISSUE_SCHEMA_MALFORMED",
    "ISSUE_SCHEMA_UNSUPPORTED",
    "ISSUE_DUPLICATE_FIELD",
    "ISSUE_STATE_PROJECTION_MISMATCH",
    "ISSUE_DEPENDENCY_PROJECTION_MISMATCH",
    "ISSUE_AUX_STATUS_INVALID",
}


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def _issue_status(text):
    return markdown_status(text)


def _metadata_region(text):
    """Header region before the first '## ' section — metadata lines live
    there by convention (048/069). Restricting parsing here keeps body prose
    that QUOTES the syntax (e.g. a session note explaining the convention)
    from being misread as metadata."""
    return metadata_region(text)


def _issue_priority(text):
    return markdown_priority(text)


def _issue_blocked_by(text):
    return markdown_blocked_by(text)


def _lifecycle_state_from_evaluation(evaluation):
    issues = {
        issue["issue_id"]: issue.get("lifecycle_state")
        for issue in evaluation["issues"]
    }
    pick = lambda state: [
        issue_id for issue_id, lifecycle in issues.items() if lifecycle == state
    ]
    return {
        "issues": issues,
        "active": pick("active"),
        "done": pick("done"),
        "backlog": pick("backlog"),
        "superseded": pick("superseded"),
    }


def lifecycle_state(root):
    """Canonical lifecycle map projected from the shared issue model."""
    root = Path(root).resolve()
    return _lifecycle_state_from_evaluation(evaluate_project(root))


def _issue_title(text):
    return markdown_title(text)


def _compatibility_items(evaluation):
    return sorted(
        [
            {
                "id": issue["issue_id"],
                "status": issue.get("lifecycle_state"),
                "title": issue.get("title") or "",
                "priority": issue.get("priority"),
                "blocked_by": list(issue.get("blocked_by") or []),
            }
            for issue in evaluation["issues"]
        ],
        key=lambda item: item["id"],
    )


def list_issues(root):
    """Compatibility records for every issues/*.md file, sorted by id."""
    root = Path(root).resolve()
    return _compatibility_items(evaluate_project(root))


def ready_issues(root):
    """Startable backlog issues, priority-sorted (p0 first, then id).

    Structural spec/plan/review readiness is deliberately not required here.
    Shared schema, lifecycle projection, and dependency hard errors exclude an
    issue; satisfied dependencies allow it into this backward-compatible queue.
    """
    root = Path(root).resolve()
    evaluation = evaluate_project(root)
    items = _compatibility_items(evaluation)
    blocked_ids = {
        issue["issue_id"]
        for issue in evaluation["issues"]
        if any(
            diagnostic.get("severity") == "error"
            and diagnostic.get("code") in _READY_BLOCKING_DIAGNOSTICS
            for diagnostic in issue.get("diagnostics", [])
        )
    }
    ready = [
        i for i in items
        if i["status"] == "backlog"
        and i["id"] not in blocked_ids
    ]
    return sorted(ready, key=lambda i: (i["priority"], i["id"]))


def infer_phase(root, issue_id):
    if not issue_id:
        return "select"
    d = Path(root).resolve() / "specs" / issue_id
    if (d / "tasks.md").exists():
        return "execute"
    if (d / "plan.md").exists():
        return "plan"
    if (d / "spec.md").exists():
        return "spec"
    return "select"


def _section_body(text, header):
    """Body between '## <header>' and the next '## ' (or end)."""
    m = re.search(r"^##\s+" + re.escape(header) + r"\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s+", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def _format_schema_diagnostic(diagnostic):
    return (
        f"{diagnostic['code']} [{diagnostic.get('source_path') or 'unknown source'}]: "
        f"{diagnostic.get('message') or 'Issue schema drift.'} "
        f"Recommendation: {diagnostic.get('recommendation') or 'Run product:doctor.'}"
    )


def _dependency_drift_from_evaluation(evaluation):
    """Translate shared diagnostics to the lifecycle drift compatibility form."""
    drift = []
    issues = evaluation["issues"]
    status_by_id = {
        issue["issue_id"]: issue.get("lifecycle_state") for issue in issues
    }
    reported_schema = set()
    reported_cycles = set()

    for issue in issues:
        issue_id = issue["issue_id"]
        lifecycle = issue.get("lifecycle_state")
        for diagnostic in issue.get("diagnostics", []):
            code = diagnostic.get("code")
            if (
                diagnostic.get("severity") == "error"
                and code in _LIFECYCLE_SCHEMA_DIAGNOSTICS
            ):
                key = (
                    code,
                    diagnostic.get("source_path"),
                    diagnostic.get("message"),
                )
                if key not in reported_schema:
                    reported_schema.add(key)
                    drift.append(_format_schema_diagnostic(diagnostic))
                continue

            if code == "ISSUE_DEPENDENCY_DANGLING":
                if lifecycle not in ("done", "superseded"):
                    drift.append(
                        "blocked_by references unknown issue "
                        f"'{diagnostic.get('current')}' in {issue_id}"
                    )
                continue

            if code == "ISSUE_DEPENDENCY_UNMET" and lifecycle == "active":
                dependency, _, blocker_status = str(
                    diagnostic.get("current") or ""
                ).partition(": ")
                drift.append(
                    f"active issue {issue_id} has unmet blocker '{dependency}' "
                    f"(status: {blocker_status or 'unknown'})"
                )
                continue

            if code != "ISSUE_DEPENDENCY_CYCLE":
                continue
            members = tuple(
                sorted(
                    member.strip()
                    for member in str(diagnostic.get("current") or "").split(",")
                    if member.strip()
                )
            )
            cycle_path = tuple(diagnostic.get("cycle_path") or ())
            cycle_key = cycle_path or ("members", *members)
            if (
                members
                and cycle_key not in reported_cycles
                and all(
                    status_by_id.get(member) not in ("done", "superseded")
                    for member in members
                )
            ):
                reported_cycles.add(cycle_key)
                if cycle_path:
                    drift.append(f"dependency cycle: {' -> '.join(cycle_path)}")
                else:
                    drift.append(
                        "dependency cycle members: "
                        f"{diagnostic.get('current') or ', '.join(members)}"
                    )

    return drift


def _dependency_drift(root):
    return _dependency_drift_from_evaluation(
        evaluate_project(Path(root).resolve())
    )


def lifecycle_drift(root):
    """Consensus drift: disagreements among issue files, state.json, dashboard.md.
    Returns [] when sources agree. Pure read."""
    root = Path(root).resolve()
    evaluation = evaluate_project(root)
    ls = _lifecycle_state_from_evaluation(evaluation)
    drift = []
    drift.extend(_dependency_drift_from_evaluation(evaluation))
    active = ls["active"]
    if len(active) > 1:
        drift.append(f"multiple active issues in issue files: {active}")
    issue_active = active[0] if len(active) == 1 else ""

    state = read_json(root / ".moduflow" / "state.json") or {}
    state_active = (state.get("active_issue") or "").strip()
    if state_active != issue_active:
        drift.append(
            f".moduflow/state.json active_issue '{state_active}' != issue-file active '{issue_active}'"
        )

    dash = root / "workspace" / "dashboard.md"
    if dash.exists():
        dtext = dash.read_text(encoding="utf-8")
        active_body = _section_body(dtext, "Active Issue")
        for did in ls["done"]:
            if did in active_body:
                drift.append(f"dashboard Active Issue section still lists done issue {did}")
        if issue_active:
            if issue_active not in active_body:
                drift.append(f"dashboard Active Issue section omits active issue {issue_active}")
            if re.search(r"none active", active_body, re.I):
                drift.append(f"dashboard Active Issue says 'None active' but issue files have active {issue_active}")
        elif re.search(r"`0\d\d-[a-z0-9-]+`\s*\(phase", active_body):
            drift.append("dashboard Active Issue names an active issue but issue files have none")
    return drift


def sync_lifecycle(root):
    """Single propagation point: issue Status -> .moduflow/state.json + dashboard
    Active Issue section. Idempotent. Touches only structured fields/sections."""
    root = Path(root).resolve()
    ls = lifecycle_state(root)
    active = ls["active"][0] if len(ls["active"]) == 1 else ""
    phase = infer_phase(root, active)

    # state.json — no prose; safe to set lifecycle fields, preserve the rest.
    sp = root / ".moduflow" / "state.json"
    state = read_json(sp) or {"schema": "moduflow.state.v1"}
    state.setdefault("schema", "moduflow.state.v1")
    state["active_issue"] = active
    state["phase"] = phase
    state.setdefault("active_goal", "")
    if not active:
        state["next_command"] = "product:status"
    else:
        state.setdefault("next_command", "product:status")
    state.setdefault("blockers", [])
    state["updated_at"] = date.today().isoformat()
    if sp.parent.exists():
        sp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # dashboard.md — regenerate ONLY the Active Issue section body; preserve prose.
    dash = root / "workspace" / "dashboard.md"
    changed_dashboard = False
    if dash.exists():
        dtext = dash.read_text(encoding="utf-8")
        if active:
            new_section = (
                f"## Active Issue\n\n- `{active}` (phase: {phase}). "
                f"Canonical: `issues/{active}.md`.\n\n"
            )
        else:
            new_section = (
                "## Active Issue\n\n- None active. "
                "Run `product:status` to pick the next issue.\n\n"
            )
        # Replace the whole header+body block with a fixed form → idempotent.
        pattern = re.compile(r"^##\s+Active Issue\s*$.*?(?=^##\s|\Z)", re.M | re.S)
        if pattern.search(dtext):
            new_text = pattern.sub(lambda _m: new_section, dtext)
            if new_text != dtext:
                dash.write_text(new_text, encoding="utf-8")
                changed_dashboard = True

    return {"active": active, "phase": phase, "dashboard_updated": changed_dashboard}


def main():
    parser = argparse.ArgumentParser(description="ModuFlow artifact lifecycle sync (048).")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--state", action="store_true", help="Print canonical lifecycle_state JSON.")
    parser.add_argument("--drift", action="store_true", help="Print lifecycle drift report (consensus).")
    parser.add_argument("--sync", action="store_true", help="Propagate issue Status to state.json + dashboard.")
    parser.add_argument("--issues", action="store_true", help="Print list_issues(root) JSON.")
    parser.add_argument("--ready", action="store_true", help="Print ready_issues(root) JSON.")
    args = parser.parse_args()

    if args.issues:
        print(json.dumps(list_issues(args.project_path), ensure_ascii=False, indent=2))
        return 0
    if args.ready:
        print(json.dumps(ready_issues(args.project_path), ensure_ascii=False, indent=2))
        return 0
    if args.sync:
        print(json.dumps(sync_lifecycle(args.project_path), ensure_ascii=False, indent=2))
        return 0
    if args.drift:
        print(json.dumps(lifecycle_drift(args.project_path), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(lifecycle_state(args.project_path), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
