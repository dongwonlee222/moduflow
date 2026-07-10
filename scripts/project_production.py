#!/usr/bin/env python3
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import project_memory
import linkage_check


RECORD_SCHEMA = "moduflow.production-record.v1"
PLAYBOOK_SCHEMA = "moduflow.playbook.v1"
RECORD_SECTIONS = (
    "Artifacts",
    "Source Inputs",
    "Decisions",
    "Failed Attempts",
    "Reusable Patterns",
    "Do Not Repeat",
    "Playbook Updates",
    "External Copy",
    "Internal Reporting Copy",
)
PLAYBOOK_SECTIONS = (
    "Reusable Patterns",
    "Do Not Repeat",
    "Approved Copy Blocks",
    "Approved Structures",
    "Evidence",
    "Revision History",
)
ARTIFACT_RE = re.compile(
    r"^-\s*\[(?P<label>[^]]+)]\((?P<target>[^)]+)\)\s*[—-]\s*"
    r"(?P<variant>[^·]+?)\s*·\s*(?P<audience>.+?)\s*$"
)
PLAYBOOK_UPDATE_RE = re.compile(
    r"^-\s*(?P<playbook_id>.+?)\s+(?:—|-)\s+(?P<state>\w[\w-]*)(?:\s+.*)?$"
)


class UsageError(ValueError):
    pass


class ReturningArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def _relative_path(project_root, path):
    root = Path(project_root).resolve()
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"artifact is outside project root: {resolved}") from exc


def _frontmatter_and_body(path):
    text = Path(path).read_text(encoding="utf-8")
    metadata, body = project_memory.parse_frontmatter(text)
    if not metadata:
        raise ValueError("missing frontmatter")
    return metadata, body.strip()


def _sections(body, required):
    lines = body.splitlines()
    positions = []
    for name in required:
        marker = f"## {name}"
        matches = [index for index, line in enumerate(lines) if line.strip() == marker]
        if not matches:
            raise ValueError(f"missing section: {name}")
        if len(matches) > 1:
            raise ValueError(f"duplicate section: {name}")
        positions.append(matches[0])
    if positions != sorted(positions):
        raise ValueError("required sections are out of order")
    result = {}
    for index, name in enumerate(required):
        start = positions[index] + 1
        end = positions[index + 1] if index + 1 < len(positions) else len(lines)
        result[name] = "\n".join(lines[start:end]).strip()
    return result


def _require_metadata(metadata, schema, required):
    if metadata.get("schema") != schema:
        raise ValueError(f"schema must be {schema}")
    missing = [name for name in required if not str(metadata.get(name, "")).strip()]
    if missing:
        raise ValueError(f"missing metadata: {', '.join(missing)}")


def _parse_artifacts(section):
    if section.strip() in {"", "None recorded", "Not applicable"}:
        return []
    artifacts = []
    for line in section.splitlines():
        if not line.strip():
            continue
        match = ARTIFACT_RE.match(line.strip())
        if not match:
            raise ValueError(f"invalid artifact entry: {line.strip()}")
        artifacts.append({key: value.strip() for key, value in match.groupdict().items()})
    return artifacts


def _parse_playbook_updates(section):
    if section.strip() in {"", "None recorded", "Not applicable"}:
        return []
    updates = []
    for line in section.splitlines():
        if not line.strip():
            continue
        match = PLAYBOOK_UPDATE_RE.match(line.strip())
        if not match:
            raise ValueError(f"invalid playbook update: {line.strip()}")
        updates.append({key: value.strip() for key, value in match.groupdict().items()})
    return updates


def parse_production_record(project_root, path):
    metadata, body = _frontmatter_and_body(path)
    _require_metadata(
        metadata,
        RECORD_SCHEMA,
        (
            "id",
            "kind",
            "title",
            "deliverable_type",
            "channel",
            "audiences",
            "lifecycle",
            "created",
            "updated",
            "retrieval_trigger",
        ),
    )
    if metadata["kind"] != "production_record":
        raise ValueError("kind must be production_record")
    sections = _sections(body, RECORD_SECTIONS)
    return {
        "id": metadata["id"],
        "kind": metadata["kind"],
        "title": metadata["title"],
        "path": _relative_path(project_root, path),
        "issue_id": metadata.get("issue_id", ""),
        "source_context": metadata.get("source_context", ""),
        "deliverable_type": metadata["deliverable_type"],
        "channel": metadata["channel"],
        "audiences": project_memory.parse_list_value(metadata["audiences"]),
        "variant": metadata.get("variant", ""),
        "lifecycle": metadata["lifecycle"],
        "owner": metadata.get("owner", ""),
        "created": metadata["created"],
        "updated": metadata["updated"],
        "playbook_refs": project_memory.parse_list_value(metadata.get("playbook_refs", "[]")),
        "retrieval_trigger": metadata["retrieval_trigger"],
        "sections": sections,
        "artifacts": _parse_artifacts(sections["Artifacts"]),
        "playbook_updates": _parse_playbook_updates(sections["Playbook Updates"]),
    }


def parse_playbook(project_root, path):
    metadata, body = _frontmatter_and_body(path)
    _require_metadata(
        metadata,
        PLAYBOOK_SCHEMA,
        (
            "id",
            "kind",
            "title",
            "audiences",
            "version",
            "status",
            "source_records",
            "review_after",
            "superseded_by",
            "created",
            "updated",
        ),
    )
    if metadata["kind"] != "playbook":
        raise ValueError("kind must be playbook")
    type_value = metadata.get("applies_to_types") or metadata.get("deliverable_type", "")
    channel_value = metadata.get("applies_to_channels") or metadata.get("channels", "")
    deliverable_types = project_memory.parse_list_value(type_value)
    if not deliverable_types and type_value:
        deliverable_types = [type_value]
    channels = project_memory.parse_list_value(channel_value)
    if not channels and channel_value:
        channels = [channel_value]
    if not deliverable_types:
        raise ValueError("missing metadata: applies_to_types")
    if not channels:
        raise ValueError("missing metadata: applies_to_channels")
    sections = _sections(body, PLAYBOOK_SECTIONS)
    return {
        "id": metadata["id"],
        "kind": metadata["kind"],
        "title": metadata["title"],
        "path": _relative_path(project_root, path),
        "deliverable_type": deliverable_types[0],
        "deliverable_types": deliverable_types,
        "channels": channels,
        "audiences": project_memory.parse_list_value(metadata["audiences"]),
        "version": metadata["version"],
        "status": metadata["status"],
        "approved_by": metadata.get("approved_by", ""),
        "approved_at": metadata.get("approved_at", ""),
        "source_records": project_memory.parse_list_value(metadata["source_records"]),
        "review_after": metadata["review_after"],
        "superseded_by": project_memory.parse_list_value(metadata["superseded_by"]),
        "created": metadata["created"],
        "updated": metadata["updated"],
        "sections": sections,
        "authoritative": metadata["status"] == "approved",
    }


def _list_artifacts(project_root, directory, parser):
    root = Path(project_root).resolve()
    target = root / directory
    if not target.exists():
        return []
    return [parser(root, path) for path in sorted(target.glob("*.md"))]


def list_production_records(project_root):
    return _list_artifacts(project_root, "memory/production-records", parse_production_record)


def list_playbooks(project_root):
    return _list_artifacts(project_root, "playbooks", parse_playbook)


def _configured_human_values(project_root):
    values = set()
    for identity in linkage_check.load_human_identities(project_root):
        if isinstance(identity, dict):
            values.update(
                value
                for value in (identity.get("name"), identity.get("email"))
                if isinstance(value, str) and value
            )
    return values


def _find_by_id(items, item_id, label):
    matches = [item for item in items if item["id"] == item_id]
    if not matches:
        raise ValueError(f"missing {label}: {item_id}")
    if len(matches) > 1:
        raise ValueError(f"duplicate {label}: {item_id}")
    return matches[0]


def _set_frontmatter_values(text, values):
    updated = text
    for key, value in values.items():
        pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
        if not pattern.search(updated):
            raise ValueError(f"missing metadata: {key}")
        updated = pattern.sub(f"{key}: {value}", updated, count=1)
    return updated


def _append_section_line(text, section, line):
    if line in text.splitlines():
        return text, False
    marker = f"## {section}"
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"missing section: {section}")
    next_section = text.find("\n## ", start + len(marker))
    end = len(text) if next_section < 0 else next_section
    prefix = text[:end].rstrip()
    suffix = text[end:]
    return f"{prefix}\n\n{line}\n{suffix.lstrip(chr(10))}", True


def decide_playbook_update(
    project_root,
    *,
    record_id,
    playbook_id,
    decision,
    approved_by,
    reason,
    decided_at,
):
    if decision not in {"approve", "reject", "defer"}:
        raise ValueError("decision must be approve, reject, or defer")
    if not approved_by or approved_by not in _configured_human_values(project_root):
        raise ValueError("approved_by must exactly match a configured human name or email")
    if not reason or not decided_at:
        raise ValueError("reason and decided_at are required")
    root = Path(project_root).resolve()
    record = _find_by_id(list_production_records(root), record_id, "source record")
    playbook = _find_by_id(list_playbooks(root), playbook_id, "playbook")
    if record_id not in playbook["source_records"]:
        raise ValueError(f"playbook source_records does not include {record_id}")

    if decision == "approve" and playbook["status"] == "approved":
        if playbook["approved_by"] == approved_by and playbook["approved_at"] == decided_at:
            return {
                "action": "noop",
                "status": "approved",
                "record_path": record["path"],
                "playbook_path": playbook["path"],
            }
        raise ValueError("playbook is already approved by a different human or date")

    state = {"approve": "approved", "reject": "rejected", "defer": "deferred"}[decision]
    audit_line = f"- {playbook_id} — {state} by {approved_by} on {decided_at}: {reason}"
    record_path = root / record["path"]
    record_text, changed = _append_section_line(
        record_path.read_text(encoding="utf-8"), "Playbook Updates", audit_line
    )
    if changed:
        record_path.write_text(record_text, encoding="utf-8")

    playbook_path = root / playbook["path"]
    if decision == "approve":
        playbook_text = playbook_path.read_text(encoding="utf-8")
        playbook_text = _set_frontmatter_values(
            playbook_text,
            {
                "status": "approved",
                "approved_by": approved_by,
                "approved_at": decided_at,
                "updated": decided_at,
            },
        )
        revision = f"- {decided_at} approved by {approved_by}: {reason}"
        playbook_text, _ = _append_section_line(playbook_text, "Revision History", revision)
        playbook_path.write_text(playbook_text, encoding="utf-8")

    return {
        "action": state,
        "status": "approved" if decision == "approve" else playbook["status"],
        "record_path": record["path"],
        "playbook_path": playbook["path"],
    }


def _positive_limit(limit):
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")


def _envelope(items, limit):
    _positive_limit(limit)
    total = len(items)
    kept = items[:limit]
    return {
        "items": kept,
        "truncated": total > limit,
        "dropped_count": max(0, total - limit),
        "total_matches": total,
    }


def _slug_equal(left, right):
    return project_memory.slugify(str(left)) == project_memory.slugify(str(right))


def _search_text(item):
    values = [item.get("id", ""), item.get("title", ""), item.get("retrieval_trigger", "")]
    values.extend(item.get("audiences", []))
    values.extend(item.get("channels", []))
    values.append(item.get("channel", ""))
    for name, content in item.get("sections", {}).items():
        values.extend((name, content))
    return "\n".join(str(value) for value in values).casefold()


def _item_types(item):
    return item.get("deliverable_types", [item.get("deliverable_type", "")])


def search_production(
    project_root,
    query,
    *,
    deliverable_type=None,
    channel=None,
    audience=None,
    issue_id=None,
    kind=None,
    limit=20,
):
    _positive_limit(limit)
    items = list_production_records(project_root) + list_playbooks(project_root)
    query_text = str(query or "").strip().casefold()
    matches = []
    for original in items:
        item = dict(original)
        item["authoritative"] = item["kind"] == "playbook" and item["status"] == "approved"
        item_channels = item.get("channels", [item.get("channel", "")])
        if query_text and query_text not in _search_text(item):
            continue
        if deliverable_type and not any(_slug_equal(value, deliverable_type) for value in _item_types(item)):
            continue
        if channel and not any(_slug_equal(value, channel) for value in item_channels):
            continue
        if audience and not any(_slug_equal(value, audience) for value in item.get("audiences", [])):
            continue
        if issue_id and item.get("issue_id") != issue_id:
            continue
        if kind and item.get("kind") != kind:
            continue
        matches.append(item)
    matches.sort(key=lambda item: item["id"])
    matches.sort(key=lambda item: item.get("updated", ""), reverse=True)
    return _envelope(matches, limit)


def retrieve_production_context(
    project_root,
    *,
    deliverable_type,
    channel,
    audiences,
    limit=5,
):
    _positive_limit(limit)
    requested_audiences = [project_memory.slugify(value) for value in audiences]
    ranked = []
    for original in list_playbooks(project_root) + list_production_records(project_root):
        if original["kind"] == "playbook" and original["status"] != "approved":
            continue
        item = dict(original)
        item_channels = item.get("channels", [item.get("channel", "")])
        if deliverable_type and not any(_slug_equal(value, deliverable_type) for value in _item_types(item)):
            continue
        if channel and not any(_slug_equal(value, channel) for value in item_channels):
            continue
        item_audiences = {project_memory.slugify(value) for value in item.get("audiences", [])}
        if requested_audiences and not all(value in item_audiences for value in requested_audiences):
            continue
        authoritative = item["kind"] == "playbook" and item["status"] == "approved"
        score = 100 if authoritative else 0
        score += 20 if any(_slug_equal(value, deliverable_type) for value in _item_types(item)) else 0
        score += 10 if any(_slug_equal(value, channel) for value in item_channels) else 0
        score += 5 * sum(value in item_audiences for value in requested_audiences)
        item["authoritative"] = authoritative
        item["score"] = score
        ranked.append(item)
    ranked.sort(
        key=lambda item: (
            -item["score"],
            -int(item.get("updated", "0000-00-00").replace("-", "") or 0),
            item["id"],
        )
    )
    return _envelope(ranked, limit)


def validate_production_project(project_root):
    root = Path(project_root).resolve()
    errors = []
    warnings = []
    record_paths = sorted((root / "memory" / "production-records").glob("*.md"))
    playbook_paths = sorted((root / "playbooks").glob("*.md"))
    if not record_paths and not playbook_paths:
        return {"errors": [], "warnings": []}

    records = []
    playbooks = []
    for path, parser, target in (
        *((path, parse_production_record, records) for path in record_paths),
        *((path, parse_playbook, playbooks) for path in playbook_paths),
    ):
        try:
            target.append(parser(root, path))
        except (OSError, ValueError) as exc:
            errors.append(f"{_relative_path(root, path)}: {exc}")

    def duplicates(items, key):
        seen = {}
        for item in items:
            value = key(item)
            if value in seen:
                errors.append(f"{item['path']}: duplicate production identity with {seen[value]}")
            else:
                seen[value] = item["path"]

    duplicates(records + playbooks, lambda item: (item["kind"], item["id"]))
    duplicates(records, _capture_key)
    record_ids = {record["id"] for record in records}
    playbook_ids = {playbook["id"] for playbook in playbooks}

    allowed_lifecycle = {"draft", "review", "approved", "published", "archived"}
    for record in records:
        prefix = record["path"]
        if record["lifecycle"] not in allowed_lifecycle:
            errors.append(f"{prefix}: invalid lifecycle: {record['lifecycle']}")
        if record["issue_id"]:
            if not (root / "issues" / f"{record['issue_id']}.md").exists():
                errors.append(f"{prefix}: dangling issue reference: {record['issue_id']}")
        elif not record.get("source_context"):
            errors.append(f"{prefix}: issue_id or source_context is required")
        if not record["artifacts"]:
            message = f"{prefix}: no artifact links registered"
            (errors if record["lifecycle"] in {"approved", "published"} else warnings).append(message)
        for artifact in record["artifacts"]:
            target = artifact["target"]
            if target.startswith("https://"):
                continue
            if "://" in target:
                errors.append(f"{prefix}: unsupported artifact URL: {target}")
                continue
            artifact_path = Path(target).expanduser()
            if artifact_path.is_absolute():
                warnings.append(f"{prefix}: absolute artifact path is not portable: {target}")
            elif not (root / artifact_path).exists():
                errors.append(f"{prefix}: missing artifact: {target}")
        for playbook_id in record["playbook_refs"]:
            if playbook_id not in playbook_ids:
                errors.append(f"{prefix}: dangling playbook reference: {playbook_id}")
        for update in record["playbook_updates"]:
            if update["playbook_id"] not in playbook_ids:
                errors.append(f"{prefix}: dangling playbook update: {update['playbook_id']}")
        for section in ("Decisions", "Failed Attempts", "Reusable Patterns", "Do Not Repeat"):
            if not record["sections"][section].strip():
                warnings.append(f"{prefix}: empty learning section: {section}")

    try:
        humans = _configured_human_values(root)
    except (OSError, ValueError) as exc:
        errors.append(f".moduflow/humans.json: {exc}")
        humans = set()
    for playbook in playbooks:
        prefix = playbook["path"]
        for record_id in playbook["source_records"]:
            if record_id not in record_ids:
                errors.append(f"{prefix}: dangling source record: {record_id}")
        if playbook["status"] == "approved":
            if playbook["approved_by"] not in humans:
                errors.append(f"{prefix}: approved_by must match a configured human")
            if not playbook["approved_at"]:
                errors.append(f"{prefix}: approved playbook requires approved_at")
        elif playbook["status"] == "candidate":
            if playbook["approved_by"] or playbook["approved_at"]:
                errors.append(f"{prefix}: candidate playbook cannot contain approval fields")
        else:
            errors.append(f"{prefix}: status must be candidate or approved")
        try:
            if date.fromisoformat(playbook["review_after"]) < date.today():
                warnings.append(f"{prefix}: review_after is stale: {playbook['review_after']}")
        except ValueError:
            errors.append(f"{prefix}: review_after must be an ISO date")
    return {"errors": errors, "warnings": warnings}


PRODUCTION_DIRS = ("memory/production-records", "playbooks")


def build_production_plan(project_root, dry_run=True):
    root = Path(project_root).resolve()
    return {
        "schema": "moduflow.production-plan.v1",
        "project_root": str(root),
        "dry_run": dry_run,
        "writes": [relative for relative in PRODUCTION_DIRS if not (root / relative).exists()],
        "preserves_existing_files": True,
    }


def apply_production_plan(plan):
    root = Path(plan["project_root"])
    written = []
    for relative in PRODUCTION_DIRS:
        target = root / relative
        if not target.exists():
            target.mkdir(parents=True)
            written.append(relative)
    result = dict(plan)
    result["written"] = written
    return result


def _format_list(values):
    return "[" + ", ".join(str(value) for value in values) + "]"


def _record_content(
    record_id,
    title,
    issue_id,
    source_context,
    deliverable_type,
    channel,
    audiences,
    lifecycle,
    retrieval_trigger,
    owner,
    variant,
    created,
):
    return f"""---
schema: {RECORD_SCHEMA}
id: {record_id}
kind: production_record
title: {title}
issue_id: {issue_id}
source_context: {source_context}
deliverable_type: {deliverable_type}
channel: {channel}
audiences: {_format_list(audiences)}
variant: {variant}
lifecycle: {lifecycle}
owner: {owner or 'unassigned'}
created: {created}
updated: {created}
playbook_refs: []
retrieval_trigger: {retrieval_trigger}
---

## Artifacts

None recorded

## Source Inputs

None recorded

## Decisions

None recorded

## Failed Attempts

None recorded

## Reusable Patterns

None recorded

## Do Not Repeat

None recorded

## Playbook Updates

None recorded

## External Copy

Not applicable

## Internal Reporting Copy

Not applicable
"""


def _capture_key(record):
    source = record.get("issue_id") or record.get("source_context", "")
    return tuple(
        project_memory.slugify(str(value))
        for value in (
            source,
            record.get("deliverable_type", ""),
            record.get("channel", ""),
            record.get("variant", ""),
            record.get("title", ""),
        )
    )


def create_production_record(
    project_root,
    *,
    title,
    deliverable_type,
    channel,
    audiences,
    lifecycle,
    retrieval_trigger,
    issue_id="",
    source_context="",
    owner="",
    variant="",
    created=None,
):
    if not issue_id and not source_context:
        raise ValueError("issue_id or source_context is required")
    root = Path(project_root).resolve()
    apply_production_plan(build_production_plan(root, dry_run=False))
    created = created or date.today().isoformat()
    base_record_id = f"{created}-{project_memory.slugify(title)}"

    def render(record_id):
        return _record_content(
            record_id,
            title,
            issue_id,
            source_context,
            deliverable_type,
            channel,
            audiences,
            lifecycle,
            retrieval_trigger,
            owner,
            variant,
            created,
        )

    candidate = {
        "issue_id": issue_id,
        "source_context": source_context,
        "deliverable_type": deliverable_type,
        "channel": channel,
        "variant": variant,
        "title": title,
    }
    for existing in list_production_records(root):
        if _capture_key(existing) == _capture_key(candidate):
            existing_path = root / existing["path"]
            action = (
                "noop"
                if existing_path.read_text(encoding="utf-8") == render(existing["id"])
                else "update_required"
            )
            return {"action": action, "id": existing["id"], "path": existing["path"]}
    record_id = base_record_id
    relative = f"memory/production-records/{record_id}.md"
    target = root / relative
    if target.exists():
        source_slug = project_memory.slugify(issue_id or source_context)
        record_id = f"{base_record_id}-{source_slug}"
        relative = f"memory/production-records/{record_id}.md"
        target = root / relative
        suffix = 2
        while target.exists():
            record_id = f"{base_record_id}-{source_slug}-{suffix}"
            relative = f"memory/production-records/{record_id}.md"
            target = root / relative
            suffix += 1
    content = render(record_id)
    target.write_text(content, encoding="utf-8")
    return {"action": "created", "id": record_id, "path": relative}


def _parser():
    parser = ReturningArgumentParser(description="Manage project-local production knowledge")
    parser.add_argument("project_root", nargs="?", default=".")
    operations = parser.add_mutually_exclusive_group(required=True)
    operations.add_argument("--init", action="store_true")
    operations.add_argument("--new-record", action="store_true")
    operations.add_argument("--search")
    operations.add_argument("--retrieve", action="store_true")
    operations.add_argument("--validate", action="store_true")
    operations.add_argument("--decide-playbook", choices=("approve", "reject", "defer"))
    parser.add_argument("--title")
    parser.add_argument("--issue-id", default="")
    parser.add_argument("--source-context", default="")
    parser.add_argument("--type", dest="deliverable_type")
    parser.add_argument("--channel")
    parser.add_argument("--audience", action="append", default=[])
    parser.add_argument("--lifecycle")
    parser.add_argument("--retrieval-trigger")
    parser.add_argument("--owner", default="")
    parser.add_argument("--variant", default="")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--record-id")
    parser.add_argument("--playbook-id")
    parser.add_argument("--approved-by")
    parser.add_argument("--reason")
    parser.add_argument("--decided-at")
    return parser


def main(argv=None):
    parser = _parser()
    try:
        args = parser.parse_args(argv)
        return_code = 0
        if args.init:
            result = apply_production_plan(build_production_plan(args.project_root, dry_run=False))
        elif args.new_record:
            required = {
                "title": args.title,
                "type": args.deliverable_type,
                "channel": args.channel,
                "audience": args.audience,
                "lifecycle": args.lifecycle,
                "retrieval_trigger": args.retrieval_trigger,
            }
            missing = [name for name, value in required.items() if not value]
            if not args.issue_id and not args.source_context:
                missing.append("issue-id or --source-context")
            if missing:
                parser.error("--new-record requires " + ", ".join(f"--{name}" for name in missing))
            result = create_production_record(
                args.project_root,
                title=args.title,
                issue_id=args.issue_id,
                source_context=args.source_context,
                deliverable_type=args.deliverable_type,
                channel=args.channel,
                audiences=args.audience,
                lifecycle=args.lifecycle,
                retrieval_trigger=args.retrieval_trigger,
                owner=args.owner,
                variant=args.variant,
            )
        elif args.search is not None:
            result = search_production(
                args.project_root,
                args.search,
                deliverable_type=args.deliverable_type,
                channel=args.channel,
                audience=args.audience[0] if args.audience else None,
                issue_id=args.issue_id or None,
                limit=args.limit,
            )
        elif args.retrieve:
            if not args.deliverable_type or not args.channel:
                parser.error("--retrieve requires --type and --channel")
            result = retrieve_production_context(
                args.project_root,
                deliverable_type=args.deliverable_type,
                channel=args.channel,
                audiences=args.audience,
                limit=args.limit,
            )
        elif args.validate:
            result = validate_production_project(args.project_root)
            return_code = 1 if result["errors"] else 0
        elif args.decide_playbook:
            required = {
                "record-id": args.record_id,
                "playbook-id": args.playbook_id,
                "approved-by": args.approved_by,
                "reason": args.reason,
                "decided-at": args.decided_at,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                parser.error(
                    "--decide-playbook requires " + ", ".join(f"--{name}" for name in missing)
                )
            result = decide_playbook_update(
                args.project_root,
                record_id=args.record_id,
                playbook_id=args.playbook_id,
                decision=args.decide_playbook,
                approved_by=args.approved_by,
                reason=args.reason,
                decided_at=args.decided_at,
            )
        else:
            raise ValueError("operation is not implemented")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return return_code
    except UsageError as exc:
        print(json.dumps({"usage_error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
