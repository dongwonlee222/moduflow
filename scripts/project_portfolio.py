#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path


PORTFOLIO_FILES = {
    "projects.json": {
        "schema": "moduflow.projects.v1",
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


def collect_project_statuses(registry_path):
    registry_path = Path(registry_path).resolve()
    registry = load_json(registry_path, {"projects": []})
    statuses = []
    for project in registry.get("projects", []):
        project_root = Path(project.get("path", "")).expanduser().resolve()
        state_path = project_root / ".moduflow" / "state.json"
        state = load_json(state_path, {})
        warnings = []
        if not state_path.exists():
            warnings.append("missing .moduflow/state.json")
        owner = project.get("owner") or profile_owner(project_root) or ""
        statuses.append(
            {
                "id": project.get("id", project_root.name),
                "name": project.get("name", project.get("id", project_root.name)),
                "path": str(project_root),
                "status": project.get("status", ""),
                "owner": owner,
                "phase": state.get("phase", "unknown"),
                "next_command": state.get("next_command", ""),
                "blockers": state.get("blockers", []),
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
        "| Project | Owner | Phase | Blockers | Next Command |",
        "| --- | --- | --- | --- | --- |",
    ]
    for status in statuses:
        lines.append(
            f"| {status['name']} | {status.get('owner', '')} | {status.get('phase', '')} | "
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


def main():
    parser = argparse.ArgumentParser(description="Plan, initialize, or render a ModuFlow portfolio workspace.")
    parser.add_argument("portfolio_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="Create missing portfolio workspace files.")
    parser.add_argument("--render", action="store_true", help="Render portfolio dashboard and weekly status from projects.json.")
    args = parser.parse_args()

    if args.render:
        result = write_dashboard(args.portfolio_path)
    else:
        result = build_portfolio_plan(args.portfolio_path, dry_run=not args.write)
        if args.write:
            result = apply_portfolio_plan(result)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
