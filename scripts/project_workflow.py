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
    args = parser.parse_args()

    if args.record:
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
