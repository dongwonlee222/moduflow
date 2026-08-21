#!/usr/bin/env python3
import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

try:
    from scripts import project_registry
except ImportError:  # pragma: no cover - direct script execution fallback
    import project_registry


PORTFOLIO_FILES = {
    "projects.json": {
        "schema": "moduflow.projects.v2",
        "projects": [],
    },
    "portfolio-dashboard.md": "# Portfolio Dashboard\n\nNo projects registered yet.\n",
    "portfolio-roadmap.md": "# Portfolio Roadmap\n\n## Now\n\n## Next\n\n## Later\n",
    "weekly-status.md": "# Weekly Status\n\nNo weekly status generated yet.\n",
}


def render_content(content):
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, indent=2) + "\n"


def build_portfolio_plan(path, dry_run=True):
    portfolio_root = Path(path).resolve()
    writes = []
    for relative in PORTFOLIO_FILES:
        if not (portfolio_root / relative).exists():
            writes.append(relative)
    return {
        "schema": "moduflow.portfolio-plan.v1",
        "portfolio_root": str(portfolio_root),
        "dry_run": dry_run,
        "writes": writes,
        "preserves_existing_files": True,
    }


def write_if_missing(path, content):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_content(content), encoding="utf-8")
    return True


def apply_portfolio_plan(plan):
    portfolio_root = Path(plan["portfolio_root"])
    written = []
    for relative, content in PORTFOLIO_FILES.items():
        if write_if_missing(portfolio_root / relative, content):
            written.append(relative)
    plan["written"] = written
    return plan


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def profile_owner(project_root):
    profile = project_root / ".moduflow" / "project-profile.md"
    if not profile.exists():
        return ""
    for line in profile.read_text(encoding="utf-8").splitlines():
        if line.strip().lower().startswith("- owner:"):
            return line.split(":", 1)[1].strip()
    return ""


def team_item_owner(item):
    return item.get("assignee") or item.get("owner") or item.get("locked_by") or "unassigned"


def format_team_items(items):
    if not items:
        return "none"
    return ", ".join(
        f"{team_item_owner(item)}: {item.get('issue_id', 'unknown')}"
        for item in items
    )


def collect_team_summary(workflow_dir):
    team_state_path = Path(workflow_dir) / "team-state.json"
    state = load_json(team_state_path, {"items": []})
    items = state.get("items", [])
    if not isinstance(items, list):
        items = []
    active = [item for item in items if item.get("status") == "active"]
    review = [item for item in items if item.get("status") in {"review", "approved"}]
    done = [item for item in items if item.get("status") in {"done", "archived"}]
    blocked = [item for item in items if item.get("status") == "blocked"]
    return {
        "active_count": len(active),
        "review_count": len(review),
        "done_count": len(done),
        "blocked_count": len(blocked),
        "active_text": format_team_items(active),
        "review_text": format_team_items(review),
        "done_text": format_team_items(done),
        "blocked_text": format_team_items(blocked),
    }


def collect_project_statuses(registry_path):
    registry_path = Path(registry_path).resolve()
    registry = project_registry.load_project_registry(registry_path)
    if not registry["valid"]:
        return [
            {
                "id": "registry",
                "name": "Project registry",
                "path": "",
                "status": "invalid",
                "owner": "",
                "phase": "unknown",
                "next_command": "product:doctor",
                "blockers": [],
                "team": collect_team_summary(Path("/__moduflow_missing_workflow__")),
                "registry_schema": registry.get("source_schema", ""),
                "resolution_status": "unresolved",
                "warnings": [
                    diagnostic["code"] for diagnostic in registry["diagnostics"]
                ],
            }
        ]
    statuses = []
    for project in registry["projects"]:
        context = project_registry.resolve_project(
            registry_path,
            explicit_project_id=project["id"],
        )
        warnings = list(context.get("warnings", []))
        if context["status"] != "resolved":
            statuses.append(
                {
                    "id": project["id"],
                    "name": project["name"],
                    "path": project["root"],
                    "status": project["status"],
                    "owner": project["owner"],
                    "phase": "unknown",
                    "next_command": "product:doctor",
                    "blockers": [],
                    "team": collect_team_summary(
                        Path("/__moduflow_missing_workflow__")
                    ),
                    "registry_schema": registry["source_schema"],
                    "resolution_status": context["status"],
                    "project_status": context["project_status"],
                    "policy_trust_scope": context["policy_trust_scope"],
                    "policy_inputs": context["policy_inputs"],
                    "capabilities": context["capabilities"],
                    "capability_reasons": context["capability_reasons"],
                    "warnings": warnings,
                }
            )
            continue
        project_root = Path(context["canonical_root"])
        state_path = project_root / ".moduflow" / "state.json"
        state = load_json(state_path, {})
        if not state_path.exists():
            warnings.append("missing .moduflow/state.json")
        owner = project["owner"] or profile_owner(project_root) or ""
        workflow_dir = project_registry.canonical_path(context, "workflow")
        team = collect_team_summary(workflow_dir)
        statuses.append(
            {
                "id": project["id"],
                "name": project["name"],
                "path": str(project_root),
                "status": project["status"],
                "owner": owner,
                "phase": state.get("phase", "unknown"),
                "next_command": state.get("next_command", ""),
                "blockers": state.get("blockers", []),
                "team": team,
                "registry_schema": registry["source_schema"],
                "resolution_status": context["status"],
                "project_status": context["project_status"],
                "policy_trust_scope": context["policy_trust_scope"],
                "policy_inputs": context["policy_inputs"],
                "capabilities": context["capabilities"],
                "capability_reasons": context["capability_reasons"],
                "warnings": warnings,
            }
        )
    return statuses


def blocker_text(blockers):
    if not blockers:
        return "none"
    return ", ".join(str(blocker) for blocker in blockers)


def render_dashboard(statuses):
    lines = [
        "# Portfolio Dashboard",
        "",
        f"Updated: {date.today().isoformat()}",
        "",
        "| Project | Owner | Phase | Active Work | Review | Blockers | Next Command |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for status in statuses:
        team = status.get("team", {})
        lines.append(
            f"| {status['name']} | {status.get('owner', '')} | {status.get('phase', '')} | "
            f"{team.get('active_text', 'none')} | {team.get('review_text', 'none')} | "
            f"{blocker_text(status.get('blockers', []))} | {status.get('next_command', '')} |"
        )
    lines.extend(["", "## Project Paths", ""])
    for status in statuses:
        lines.append(f"- `{status['id']}`: `{status['path']}`")
    warnings = [status for status in statuses if status.get("warnings")]
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for status in warnings:
            lines.append(f"- `{status['id']}`: {', '.join(status['warnings'])}")
    return "\n".join(lines) + "\n"


def render_weekly(statuses):
    lines = ["# Weekly Status", "", f"Updated: {date.today().isoformat()}", ""]
    for status in statuses:
        lines.extend(
            [
                f"## {status['name']}",
                "",
                f"- Owner: {status.get('owner', '')}",
                f"- Phase: {status.get('phase', '')}",
                f"- Active Work: {status.get('team', {}).get('active_text', 'none')}",
                f"- Review: {status.get('team', {}).get('review_text', 'none')}",
                f"- Done: {status.get('team', {}).get('done_text', 'none')}",
                f"- Blockers: {blocker_text(status.get('blockers', []))}",
                f"- Next: `{status.get('next_command', '')}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_dashboard(portfolio_root):
    portfolio_root = Path(portfolio_root).resolve()
    statuses = collect_project_statuses(portfolio_root / "projects.json")
    dashboard = render_dashboard(statuses)
    weekly = render_weekly(statuses)
    (portfolio_root / "portfolio-dashboard.md").write_text(dashboard, encoding="utf-8")
    (portfolio_root / "weekly-status.md").write_text(weekly, encoding="utf-8")
    return {
        "portfolio_root": str(portfolio_root),
        "project_count": len(statuses),
        "written": ["portfolio-dashboard.md", "weekly-status.md"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Plan, initialize, or render a ModuFlow portfolio workspace.")
    parser.add_argument("portfolio_path", nargs="?", default=".")
    operations = parser.add_mutually_exclusive_group()
    operations.add_argument("--write", action="store_true", help="Create missing portfolio workspace files.")
    operations.add_argument("--render", action="store_true", help="Render portfolio dashboard and weekly status from projects.json.")
    operations.add_argument("--resolve", help="Resolve a project from request text without writing.")
    operations.add_argument("--select", help="Explicitly record one registered project ID as recent.")
    args = parser.parse_args(argv)

    portfolio_root = Path(args.portfolio_path).resolve()
    registry_path = portfolio_root / "projects.json"
    if args.resolve is not None:
        result = project_registry.resolve_project(
            registry_path,
            request_text=args.resolve,
        )
    elif args.select is not None:
        try:
            result = project_registry.record_recent_selection(
                registry_path,
                args.select,
                datetime.now(timezone.utc).isoformat(),
            )
        except ValueError as exc:
            print(
                json.dumps(
                    {"status": "error", "message": str(exc)},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2
    elif args.render:
        result = write_dashboard(args.portfolio_path)
    else:
        result = build_portfolio_plan(args.portfolio_path, dry_run=not args.write)
        if args.write:
            result = apply_portfolio_plan(result)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
