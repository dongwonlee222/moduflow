#!/usr/bin/env python3
"""Capture reference repo/template improvement candidates.

Issue 080. This writes only to the current ModuFlow project. It never opens
external GitHub issues or mutates reference repositories.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


BACKLOG_RELATIVE = Path("workspace") / "reference-improvements.md"
DEFAULT_STATUS = "candidate"
DEFAULT_PRIORITY = "p2"


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or "untitled"


def build_entry(
    *,
    title,
    source,
    gap,
    recommendation,
    issue_id,
    today=None,
    priority=DEFAULT_PRIORITY,
    status=DEFAULT_STATUS,
    promotion_target="",
):
    created = today or date.today().isoformat()
    clean_issue = issue_id.strip()
    return {
        "id": f"ref-{created}-{slugify(title)}",
        "title": title.strip(),
        "status": status.strip() or DEFAULT_STATUS,
        "priority": priority.strip() or DEFAULT_PRIORITY,
        "source_reference": source.strip(),
        "origin_issue": clean_issue,
        "origin_spec": f"specs/{clean_issue}/spec.md" if clean_issue else "",
        "observed_gap": gap.strip(),
        "suggested_improvement": recommendation.strip(),
        "promotion_target": promotion_target.strip(),
        "created": created,
    }


def render_entry_markdown(entry):
    promotion = entry["promotion_target"] or ""
    return (
        f"### {entry['title']}\n\n"
        f"- ID: `{entry['id']}`\n"
        f"- Status: {entry['status']}\n"
        f"- Priority: {entry['priority']}\n"
        f"- Source reference: `{entry['source_reference']}`\n"
        f"- Origin issue: `{entry['origin_issue']}`\n"
        f"- Origin spec: `{entry['origin_spec']}`\n"
        f"- Promotion target: `{promotion}`\n"
        f"- Created: {entry['created']}\n\n"
        f"**Observed gap**: {entry['observed_gap']}\n\n"
        f"**Suggested improvement**: {entry['suggested_improvement']}\n"
    )


def initial_backlog_text():
    return """# Reference Improvements

Project-local backlog for improvement candidates discovered while using reference repositories, templates, or upstream examples. These records are optional context, not active execution scope or release blockers.

## Status Values

| Status | Meaning |
| --- | --- |
| candidate | Captured for later triage |
| accepted | Worth turning into work, but not yet promoted |
| promoted | Converted into a normal ModuFlow issue |
| closed | No longer useful or intentionally declined |

## Entries

"""


def _is_duplicate(existing_text, entry):
    title_line = f"### {entry['title']}"
    source_line = f"- Source reference: `{entry['source_reference']}`"
    blocks = existing_text.split("\n### ")
    for idx, block in enumerate(blocks):
        text = block if idx == 0 else "### " + block
        if title_line in text and source_line in text:
            return True
    return False


def write_entry(root, entry):
    root = Path(root)
    path = root / BACKLOG_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = initial_backlog_text()

    if _is_duplicate(existing, entry):
        return {
            "path": path,
            "written": False,
            "duplicate": True,
            "entry": entry,
        }

    separator = "" if existing.endswith("\n\n") else "\n\n"
    path.write_text(existing + separator + render_entry_markdown(entry) + "\n", encoding="utf-8")
    return {
        "path": path,
        "written": True,
        "duplicate": False,
        "entry": entry,
    }


def _json_ready(result):
    payload = dict(result)
    if "path" in payload:
        payload["path"] = str(payload["path"])
    return payload


def build_parser():
    parser = argparse.ArgumentParser(description="Capture a reference improvement candidate")
    parser.add_argument("project_path")
    parser.add_argument("--title", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--gap", required=True)
    parser.add_argument("--recommendation", required=True)
    parser.add_argument("--issue-id", required=True)
    parser.add_argument("--priority", default=DEFAULT_PRIORITY)
    parser.add_argument("--status", default=DEFAULT_STATUS)
    parser.add_argument("--promotion-target", default="")
    parser.add_argument("--date", default=None)
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.project_path)
    entry = build_entry(
        title=args.title,
        source=args.source,
        gap=args.gap,
        recommendation=args.recommendation,
        issue_id=args.issue_id,
        today=args.date,
        priority=args.priority,
        status=args.status,
        promotion_target=args.promotion_target,
    )
    if args.write:
        result = write_entry(root, entry)
    else:
        result = {
            "path": root / BACKLOG_RELATIVE,
            "written": False,
            "duplicate": False,
            "entry": entry,
        }
    print(json.dumps(_json_ready(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
