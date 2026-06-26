#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path


VALID_STATES = {
    "draft",
    "ready-for-review",
    "approved",
    "in-progress",
    "blocked",
    "released",
    "done",
    "archived",
}

TEAM_STATE_SCHEMA = "moduflow.team-state.v1"
TEAM_STATUSES = {
    "proposed",
    "ready",
    "active",
    "blocked",
    "review",
    "approved",
    "done",
    "archived",
}

WORKFLOW_FILES = {
    "workflow/review-gates.md": """# Review Gates

## States

- draft
- ready-for-review
- approved
- in-progress
- blocked
- released
- archived

## Roles

- owner
- reviewer
- implementer
- approver
- stakeholder
""",
    "workflow/approval-policy.md": """# Approval Policy

## Default Rule

Work should show owner, reviewer, approver, current state, blockers, and next command before release.
""",
    "workflow/release-policy.md": """# Release Policy

## Default Rule

Release notes should include linked issue/spec, test evidence, rollback notes, and post-release checks.
""",
    "workflow/handoff.md": "# Handoff\n\n## Open Handoffs\n\n",
    "workflow/risks.md": "# Risks\n\n## Active Risks\n\n",
}


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def build_workflow_plan(path, dry_run=True):
    project_root = Path(path).resolve()
    writes = []
    for relative in WORKFLOW_FILES:
        if not (project_root / relative).exists():
            writes.append(relative)
    return {
        "schema": "moduflow.workflow-plan.v1",
        "project_root": str(project_root),
        "dry_run": dry_run,
        "writes": writes,
        "states": sorted(VALID_STATES),
        "preserves_existing_files": True,
    }


def write_text_if_missing(path, content):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def team_state_path(root):
    return Path(root).resolve() / "workflow" / "team-state.json"


def default_team_state():
    return {
        "schema": TEAM_STATE_SCHEMA,
        "items": [],
    }


def load_team_state(path):
    target = team_state_path(path)
    if not target.exists():
        return default_team_state()
    try:
        state = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return default_team_state()
    if state.get("schema") != TEAM_STATE_SCHEMA or not isinstance(state.get("items"), list):
        return default_team_state()
    return state


def write_team_state(path, state):
    target = team_state_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def recommend_issue_branch(issue_id):
    return f"codex/{issue_id}"


def next_command_for_status(issue_id, status):
    if status == "review":
        return f"product:review {issue_id}"
    if status == "approved":
        return f"product:release {issue_id}"
    if status in {"done", "archived"}:
        return "product:status"
    return f"product:execute {issue_id}"


def normalize_team_item(item):
    status = item.get("status") or "ready"
    if status not in TEAM_STATUSES:
        status = "ready"
    issue_id = item.get("issue_id") or ""
    normalized = {
        "issue_id": issue_id,
        "owner": item.get("owner") or "",
        "assignee": item.get("assignee") or "",
        "reviewer": item.get("reviewer") or "",
        "status": status,
        "branch": item.get("branch") or "",
        "pr": item.get("pr") or "",
        "lock_state": item.get("lock_state") or "none",
        "locked_by": item.get("locked_by") or "",
        "blocker": item.get("blocker") or "",
        "last_handoff": item.get("last_handoff") or "",
        "next_command": item.get("next_command") or next_command_for_status(issue_id, status),
        "updated_at": item.get("updated_at") or date.today().isoformat(),
    }
    return normalized


def upsert_team_item(path, updates):
    state = load_team_state(path)
    issue_id = updates["issue_id"]
    items = [normalize_team_item(item) for item in state.get("items", [])]
    for index, item in enumerate(items):
        if item["issue_id"] == issue_id:
            merged = dict(item)
            merged.update(
                {
                    key: value
                    for key, value in updates.items()
                    if value is not None and value != ""
                }
            )
            items[index] = normalize_team_item(merged)
            break
    else:
        items.append(normalize_team_item(updates))
    state["items"] = items
    write_team_state(path, state)
    return next(item for item in items if item["issue_id"] == issue_id)


def start_issue_work(path, issue_id, assignee, owner="", reviewer="", branch=None):
    branch = branch or recommend_issue_branch(issue_id)
    return upsert_team_item(
        path,
        {
            "issue_id": issue_id,
            "owner": owner,
            "assignee": assignee,
            "reviewer": reviewer,
            "status": "active",
            "branch": branch,
            "lock_state": "active",
            "locked_by": assignee,
            "last_handoff": f"{assignee} started work on {branch}",
            "next_command": f"product:execute {issue_id}",
            "updated_at": date.today().isoformat(),
        },
    )


def record_pr_state(path, issue_id, pr, reviewer="", status="review"):
    lock_state = "released" if status in {"done", "archived"} else "active"
    return upsert_team_item(
        path,
        {
            "issue_id": issue_id,
            "reviewer": reviewer,
            "status": status,
            "pr": pr,
            "lock_state": lock_state,
            "last_handoff": f"PR ready for review: {pr}",
            "next_command": next_command_for_status(issue_id, status),
            "updated_at": date.today().isoformat(),
        },
    )


def render_team_status(path):
    state = load_team_state(path)
    items = [normalize_team_item(item) for item in state.get("items", [])]
    groups = [
        ("Active", {"active"}),
        ("Review", {"review", "approved"}),
        ("Blocked", {"blocked"}),
        ("Ready", {"proposed", "ready"}),
        ("Done", {"done", "archived"}),
    ]
    lines = ["# Team Status", ""]
    for title, statuses in groups:
        grouped = [item for item in items if item["status"] in statuses]
        lines.extend([f"## {title}", ""])
        if not grouped:
            lines.extend(["- None.", ""])
            continue
        for item in grouped:
            owner = item["assignee"] or item["owner"] or "unassigned"
            branch = item["branch"] or "no-branch"
            pr = f" PR: {item['pr']}." if item["pr"] else ""
            blocker = f" Blocker: {item['blocker']}." if item["blocker"] else ""
            lines.append(f"- `{item['issue_id']}`: {owner}, `{branch}`.{pr}{blocker} Next: `{item['next_command']}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def suggest_completion_memory(path, issue_id, title, summary, source_artifacts=None):
    source_artifacts = source_artifacts or [f"issues/{issue_id}.md"]
    return {
        "entry_id": f"{date.today().isoformat()}-{slugify(issue_id)}-completion",
        "title": title,
        "summary": summary,
        "kind": "decision",
        "tags": ["team-workflow", "issue-completion", issue_id],
        "source_event": "issue_completed",
        "source_artifacts": source_artifacts,
        "storage_policy": "canonical_git",
        "mirror_targets": [],
    }


def apply_workflow_plan(plan):
    project_root = Path(plan["project_root"])
    written = []
    for relative, content in WORKFLOW_FILES.items():
        if write_text_if_missing(project_root / relative, content):
            written.append(relative)
    plan["written"] = written
    return plan


def workflow_record_body(issue_id, state, owner, reviewers, approver, blocker, next_command):
    if state not in VALID_STATES:
        raise ValueError(f"Unsupported workflow state: {state}")
    reviewer_text = ", ".join(reviewers)
    today = date.today().isoformat()
    return f"""---
issue_id: {issue_id}
state: {state}
owner: {owner}
reviewers: {reviewer_text}
approver: {approver}
blocker: {blocker}
next_command: {next_command}
date: {today}
---

# Workflow Record: {issue_id}

## Review

- State: {state}
- Owner: {owner}
- Reviewers: {reviewer_text}
- Approver: {approver}

## Blockers

- {blocker}

## Next Command

`{next_command}`
"""


def create_workflow_record(path, issue_id, state, owner, reviewers=None, approver="", blocker="", next_command=""):
    reviewers = reviewers or []
    project_root = Path(path).resolve()
    target_dir = project_root / "workflow" / "records"
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{date.today().isoformat()}-{slugify(issue_id)}-{slugify(state)}.md"
    target = target_dir / filename
    if target.exists():
        raise FileExistsError(str(target))
    target.write_text(
        workflow_record_body(issue_id, state, owner, reviewers, approver, blocker, next_command),
        encoding="utf-8",
    )
    return {
        "schema": "moduflow.workflow-record.v1",
        "path": str(target.relative_to(project_root)),
        "state": state,
        "preserves_existing_files": True,
    }


def main():
    parser = argparse.ArgumentParser(description="Plan, initialize, or create ModuFlow team workflow artifacts.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="Create missing workflow files.")
    parser.add_argument("--record", action="store_true", help="Create a workflow record.")
    parser.add_argument("--issue-id", default="")
    parser.add_argument("--state", choices=sorted(VALID_STATES), default="draft")
    parser.add_argument("--owner", default="")
    parser.add_argument("--reviewers", default="")
    parser.add_argument("--approver", default="")
    parser.add_argument("--blocker", default="")
    parser.add_argument("--next-command", default="")
    parser.add_argument("--start", action="store_true", help="Record an issue as actively started by an assignee.")
    parser.add_argument("--assignee", default="")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--pr-state", action="store_true", help="Record PR review state for an issue.")
    parser.add_argument("--pr", default="")
    parser.add_argument("--team-status", action="store_true", help="Render PM-friendly team status.")
    args = parser.parse_args()

    if args.team_status:
        print(render_team_status(args.project_path), end="")
        return 0
    if args.start:
        result = start_issue_work(
            args.project_path,
            issue_id=args.issue_id,
            assignee=args.assignee,
            owner=args.owner,
            reviewer=args.reviewer,
            branch=args.branch or None,
        )
    elif args.pr_state:
        team_status = args.state if args.state in TEAM_STATUSES else "review"
        result = record_pr_state(
            args.project_path,
            issue_id=args.issue_id,
            pr=args.pr,
            reviewer=args.reviewer,
            status=team_status,
        )
    elif args.record:
        reviewers = [value.strip() for value in args.reviewers.split(",") if value.strip()]
        result = create_workflow_record(
            args.project_path,
            issue_id=args.issue_id,
            state=args.state,
            owner=args.owner,
            reviewers=reviewers,
            approver=args.approver,
            blocker=args.blocker,
            next_command=args.next_command,
        )
    else:
        result = build_workflow_plan(args.project_path, dry_run=not args.write)
        if args.write:
            result = apply_workflow_plan(result)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
