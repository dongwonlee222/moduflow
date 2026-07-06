#!/usr/bin/env python3
"""Promote a capture record (decision/inbox/memory/knowledge) into an issue.

Issue 075 (B2). Records never move: promotion writes `promoted_to` into the
record frontmatter in place and `Promoted-from` into the new issue's Source.
Pure file operations — no git calls.

Usage:
    python3 scripts/project_promote.py <project-path> --record <record.md> \
        [--issue-id <id>] [--date YYYY-MM-DD] [--write]
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

TODO_MARKER = "TODO(blocking-execution)"
TEMPLATE_RELATIVE = Path("templates") / "issues" / "issue.md"


def parse_frontmatter(text):
    """Parse simple YAML frontmatter between --- fences.

    Returns (frontmatter dict, fence_open_line_idx, fence_close_line_idx, body)
    or (None, None, None, text) when the file has no frontmatter. Only handles
    `key: value` lines and inline `[a, b]` lists — the record contract (075
    Global Constraint 8) needs nothing more. Stdlib only, no external deps.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, None, None, text
    close = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            close = idx
            break
    if close is None:
        return None, None, None, text
    data = {}
    for raw in lines[1:close]:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", raw)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            items = [part.strip().strip("'\"") for part in inner.split(",")] if inner else []
            data[key] = [item for item in items if item]
        else:
            data[key] = value.strip("'\"")
    body = "\n".join(lines[close + 1:])
    return data, 0, close, body


def kebab_case(title):
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return slug or "untitled"


def next_issue_number(issues_dir):
    highest = 0
    if issues_dir.is_dir():
        for path in issues_dir.glob("*.md"):
            match = re.match(r"^(\d+)", path.stem)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def _record_title(frontmatter, body):
    title = frontmatter.get("title")
    if title:
        return title
    match = re.search(r"^#\s+(.+)$", body, re.M)
    if match:
        return match.group(1).strip()
    return "Untitled Record"


def _as_bullets(value):
    """Normalize a frontmatter value (string or list) to bullet lines."""
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def derive_sections(frontmatter):
    """Derive the three AI-first issue sections from record fields.

    Missing derivations become a TODO(blocking-execution) bullet — a promoted
    issue must never ship hollow sections silently.
    """
    verification = _as_bullets(frontmatter.get("verification"))
    if not verification:
        verification = [f"{TODO_MARKER}: define the commands the executor runs to self-check"]

    entry_points = _as_bullets(frontmatter.get("entry_points"))
    if not entry_points:
        entry_points = [f"`{item}`" for item in _as_bullets(frontmatter.get("source_artifacts"))]
    if not entry_points:
        entry_points = [f"{TODO_MARKER}: list the starting files/components"]

    scope_fence = _as_bullets(frontmatter.get("scope_fence"))
    if not scope_fence:
        # A decision's rationale seeds the fence: it states what the decision
        # protects, i.e. what this issue must not silently overturn.
        rationale = frontmatter.get("rationale")
        if isinstance(rationale, str) and rationale.strip():
            scope_fence = [f"Do not overturn the promoted record's rationale: {rationale.strip()}"]
        reversal = frontmatter.get("reversal_conditions")
        if isinstance(reversal, str) and reversal.strip():
            scope_fence.append(f"Reversal only under recorded conditions: {reversal.strip()}")
    if not scope_fence:
        scope_fence = [f"{TODO_MARKER}: mark files/behaviors out of bounds"]

    return {
        "verification": verification,
        "entry_points": entry_points,
        "scope_fence": scope_fence,
    }


def _fill(template, mapping):
    def replace(match):
        return mapping.get(match.group(1), match.group(0))
    return re.sub(r"\{\{(\w+)\}\}", replace, template)


def render_issue(template_text, issue_id, frontmatter, body, record_ref, created, source_date, sections):
    title = _record_title(frontmatter, body)
    summary = frontmatter.get("summary") or f"{TODO_MARKER}: summarize the promoted record"
    rationale = frontmatter.get("rationale")
    opportunity = rationale.strip() if isinstance(rationale, str) and rationale.strip() else summary
    mapping = {
        "issue_id": issue_id,
        "issue_slug": issue_id,
        "title": title,
        "created_date": created,
        "summary": summary,
        "source_type": "promoted record",
        "source_link": f"`{record_ref}`",
        "date": source_date,
        "opportunity": opportunity,
        "in_scope": f"{TODO_MARKER}: define in-scope work",
        "out_of_scope": f"{TODO_MARKER}: define out-of-scope work",
        "acceptance_criteria": f"{TODO_MARKER}: define verifiable acceptance criteria",
        "verification_commands": "\n- ".join(sections["verification"]),
        "entry_points": "\n- ".join(sections["entry_points"]),
        "scope_fence": "\n- ".join(sections["scope_fence"]),
        "session_log": f"{created}: promoted from `{record_ref}`",
    }
    rendered = _fill(template_text, mapping)
    promoted_from = frontmatter.get("id") or record_ref
    rendered = rendered.replace(
        f"- Date: {source_date}",
        f"- Date: {source_date}\n- Promoted-from: `{promoted_from}`",
        1,
    )
    return rendered


def updated_record_text(text, close_idx, issue_id):
    """Insert `promoted_to: <issue-id>` into the frontmatter in place.

    Placed after `superseded_by` when present, else at the end of the
    frontmatter. Every other byte of the file is preserved.
    """
    lines = text.split("\n")
    insert_at = close_idx
    for idx in range(1, close_idx):
        if re.match(r"^superseded_by:", lines[idx]):
            insert_at = idx + 1
            break
    lines.insert(insert_at, f"promoted_to: {issue_id}")
    return "\n".join(lines)


def build_promotion_plan(project_root, record_path, issue_id=None, date_override=None, today=None):
    """Compute the promotion plan. Returns a dict with ok/errors and, when ok,
    the planned issue path/content and record update."""
    root = Path(project_root).resolve()
    record = Path(record_path)
    if not record.is_absolute():
        record = root / record
    if record.exists():
        record = record.resolve()
    plan = {
        "ok": True,
        "errors": [],
        "project": str(root),
        "record": str(record),
    }
    if not record.is_file():
        plan["ok"] = False
        plan["errors"].append(f"record not found: {record}")
        return plan

    text = record.read_text(encoding="utf-8")
    frontmatter, open_idx, close_idx, body = parse_frontmatter(text)
    if frontmatter is None:
        plan["ok"] = False
        plan["errors"].append("record has no YAML frontmatter (--- fences required); refusing to promote")
        return plan

    promoted_to = frontmatter.get("promoted_to")
    if isinstance(promoted_to, list):
        promoted_to = ", ".join(promoted_to)
    if promoted_to and str(promoted_to).strip():
        plan["ok"] = False
        plan["errors"].append(f"record already promoted (promoted_to: {promoted_to}); refusing to promote twice")
        return plan

    issues_dir = root / "issues"
    title = _record_title(frontmatter, body)
    slug = kebab_case(title)
    if issue_id:
        if re.fullmatch(r"\d+", issue_id):
            full_id = f"{int(issue_id):03d}-{slug}"
        else:
            full_id = issue_id
    else:
        full_id = f"{next_issue_number(issues_dir):03d}-{slug}"

    issue_path = issues_dir / f"{full_id}.md"
    if issue_path.exists():
        plan["ok"] = False
        plan["errors"].append(f"issue file already exists: {issue_path}; refusing to overwrite")
        return plan

    template_path = root / TEMPLATE_RELATIVE
    if not template_path.is_file():
        # Fall back to the template bundled with this script's repo.
        template_path = Path(__file__).resolve().parent.parent / TEMPLATE_RELATIVE
    if not template_path.is_file():
        plan["ok"] = False
        plan["errors"].append(f"issue template not found: {TEMPLATE_RELATIVE}")
        return plan

    created = today or date.today().isoformat()
    source_date = date_override or frontmatter.get("date") or created
    try:
        record_ref = str(record.relative_to(root))
    except ValueError:
        record_ref = str(record)

    sections = derive_sections(frontmatter)
    issue_text = render_issue(
        template_path.read_text(encoding="utf-8"),
        full_id, frontmatter, body, record_ref, created, source_date, sections,
    )

    plan.update({
        "record": record_ref,
        "kind": frontmatter.get("kind"),
        "title": title,
        "issue_id": full_id,
        "issue_path": str(issue_path),
        "issue_content": issue_text,
        "record_frontmatter_insert": f"promoted_to: {full_id}",
        "updated_record_text": updated_record_text(text, close_idx, full_id),
        "sections": sections,
        "promoted_from": frontmatter.get("id") or record_ref,
    })
    return plan


def apply_promotion_plan(plan):
    """Write the issue file and update the record in place. Plan must be ok."""
    if not plan["ok"]:
        raise ValueError("refusing to apply a failed promotion plan: " + "; ".join(plan["errors"]))
    issue_path = Path(plan["issue_path"])
    issue_path.parent.mkdir(parents=True, exist_ok=True)
    issue_path.write_text(plan["issue_content"], encoding="utf-8")
    record_path = Path(plan["project"]) / plan["record"] if not Path(plan["record"]).is_absolute() else Path(plan["record"])
    record_path.write_text(plan["updated_record_text"], encoding="utf-8")
    return {
        "ok": True,
        "issue_path": str(issue_path),
        "record": str(record_path),
        "issue_id": plan["issue_id"],
    }


def _plan_view(plan, dry_run):
    view = {k: v for k, v in plan.items() if k not in ("issue_content", "updated_record_text")}
    view["dry_run"] = dry_run
    return view


def main(argv=None):
    parser = argparse.ArgumentParser(description="Promote a capture record into an issue (075).")
    parser.add_argument("project", help="project root path")
    parser.add_argument("--record", required=True, help="path to the record .md (absolute or project-relative)")
    parser.add_argument("--issue-id", help="explicit issue id (number or full id); default: next NNN + title slug")
    parser.add_argument("--date", help="source date for the issue Source section (default: record date)")
    parser.add_argument("--write", action="store_true", help="apply the plan (default: dry-run)")
    args = parser.parse_args(argv)

    plan = build_promotion_plan(args.project, args.record, issue_id=args.issue_id, date_override=args.date)
    if not plan["ok"]:
        print(json.dumps(_plan_view(plan, dry_run=not args.write), indent=2, ensure_ascii=False))
        return 1
    if not args.write:
        print(json.dumps(_plan_view(plan, dry_run=True), indent=2, ensure_ascii=False))
        return 0
    result = apply_promotion_plan(plan)
    result["record_frontmatter_insert"] = plan["record_frontmatter_insert"]
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
