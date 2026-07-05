#!/usr/bin/env python3
"""Artifact lifecycle sync (048).

Canonical lifecycle source = each issue file's `**Status:**` line. This module
reads that canonical state, propagates it to the derived views (.moduflow/state.json
+ the dashboard's Active Issue section), and detects drift by consensus across
sources. It does NOT write back to issue files (canonical is human-authored).
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def _issue_status(text):
    m = re.search(r"\*\*Status:\s*([A-Za-z0-9-]+)", text)
    word = (m.group(1).lower() if m else "backlog")
    if word.startswith("superseded"):
        return "superseded"
    if word in ("done", "active", "backlog"):
        return word
    return "backlog"


def _metadata_region(text):
    """Header region before the first '## ' section — metadata lines live
    there by convention (048/069). Restricting parsing here keeps body prose
    that QUOTES the syntax (e.g. a session note explaining the convention)
    from being misread as metadata."""
    m = re.search(r"^##\s", text, re.M)
    return text[:m.start()] if m else text


def _issue_priority(text):
    m = re.search(r"^\*\*Priority:\s*(p[0-3])\b", _metadata_region(text), re.I | re.M)
    if not m:
        return "p2"
    return m.group(1).lower()


def _issue_blocked_by(text):
    m = re.search(r"^\*\*Blocked-by:\s*([^*\n]+)\*\*", _metadata_region(text), re.M)
    if not m:
        return []
    parts = m.group(1).split(",")
    result = []
    for part in parts:
        cleaned = part.strip().strip("`").strip()
        if cleaned:
            result.append(cleaned)
    return result


def lifecycle_state(root):
    """Canonical lifecycle map from issues/*.md Status lines."""
    root = Path(root).resolve()
    issues_dir = root / "issues"
    issues = {}
    if issues_dir.is_dir():
        for f in sorted(issues_dir.glob("*.md")):
            issues[f.stem] = _issue_status(f.read_text(encoding="utf-8"))
    pick = lambda s: [i for i, st in issues.items() if st == s]
    return {
        "issues": issues,
        "active": pick("active"),
        "done": pick("done"),
        "backlog": pick("backlog"),
        "superseded": pick("superseded"),
    }


def _issue_title(text):
    for line in text.splitlines():
        if line.startswith("# "):
            heading = line[2:].strip()
            if ":" in heading:
                heading = heading.split(":", 1)[1].strip()
            return heading.strip("`").strip()
    return ""


def list_issues(root):
    """[{id, status, title}] for every issues/*.md, sorted by id."""
    root = Path(root).resolve()
    issues_dir = root / "issues"
    items = []
    if issues_dir.is_dir():
        for f in sorted(issues_dir.glob("*.md")):
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            items.append({
                "id": f.stem,
                "status": _issue_status(text),
                "title": _issue_title(text),
                "priority": _issue_priority(text),
                "blocked_by": _issue_blocked_by(text),
            })
    return items


def ready_issues(root):
    """Backlog issues whose blockers are all done/superseded, priority-sorted
    (p0 first, then id). An unknown blocked_by id excludes the issue (its
    status is unresolvable) — the drift gate separately reports the dangling
    reference."""
    items = list_issues(root)
    status_map = {i["id"]: i["status"] for i in items}
    ready = [
        i for i in items
        if i["status"] == "backlog"
        and all(status_map.get(b) in ("done", "superseded") for b in i["blocked_by"])
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


def _dependency_drift(root):
    """Dangling blocked_by references and dependency cycles. Scope: only
    issues whose status is not done/superseded participate in the cycle
    graph (historical done<->done references must never flag — spec Risk)."""
    drift = []
    items = list_issues(root)
    by_id = {i["id"]: i for i in items}

    for item in items:
        if item["status"] in ("done", "superseded"):
            continue
        for b in item["blocked_by"]:
            if b not in by_id:
                drift.append(f"blocked_by references unknown issue '{b}' in {item['id']}")

    # An active issue whose blocker is not yet satisfied means work is being
    # executed on top of an unfinished dependency — surface it (069 review
    # finding: this state previously produced zero signal anywhere).
    for item in items:
        if item["status"] != "active":
            continue
        for b in item["blocked_by"]:
            blocker_status = by_id.get(b, {}).get("status")
            if blocker_status in ("done", "superseded") or blocker_status is None:
                continue  # satisfied, or dangling (already reported above)
            drift.append(
                f"active issue {item['id']} has unmet blocker '{b}' (status: {blocker_status})"
            )

    # Cycle detection over open-issue -> open-blocked_by edges only.
    # Iterative DFS with an explicit stack — the recursive version crashed
    # with RecursionError on ~2000-node dependency chains (069 review finding).
    open_ids = {i["id"] for i in items if i["status"] not in ("done", "superseded")}
    graph = {i: [b for b in by_id[i]["blocked_by"] if b in open_ids] for i in open_ids}

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {i: WHITE for i in open_ids}
    reported_cycles = set()

    for start in sorted(open_ids):
        if color[start] != WHITE:
            continue
        color[start] = GRAY
        path = [start]
        stack = [(start, iter(graph.get(start, [])))]
        while stack:
            node, edges = stack[-1]
            descended = False
            for nxt in edges:
                if color.get(nxt) == GRAY:
                    cycle_start = path.index(nxt)
                    cycle_path = path[cycle_start:] + [nxt]
                    key = tuple(sorted(set(cycle_path)))
                    if key not in reported_cycles:
                        reported_cycles.add(key)
                        drift.append(f"dependency cycle: {' -> '.join(cycle_path)}")
                elif color.get(nxt) == WHITE:
                    color[nxt] = GRAY
                    path.append(nxt)
                    stack.append((nxt, iter(graph.get(nxt, []))))
                    descended = True
                    break
            if not descended:
                stack.pop()
                path.pop()
                color[node] = BLACK

    return drift


def lifecycle_drift(root):
    """Consensus drift: disagreements among issue files, state.json, dashboard.md.
    Returns [] when sources agree. Pure read."""
    root = Path(root).resolve()
    ls = lifecycle_state(root)
    drift = []
    drift.extend(_dependency_drift(root))
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
