#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path


MEMORY_DIRS = [
    "memory/deliverables",
    "memory/decisions",
    "memory/evidence",
    "memory/meetings",
    "memory/releases",
    "memory/notes",
    "memory/references",
]

KIND_TO_DIR = {
    "deliverable": "memory/deliverables",
    "decision": "memory/decisions",
    "evidence": "memory/evidence",
    "meeting": "memory/meetings",
    "release": "memory/releases",
    "note": "memory/notes",
    "reference": "memory/references",
}

INDEX_CONTENT = """# Project Memory

Portable project-local memory for deliverables, decisions, evidence, meetings, releases, notes, and references.

## Deliverables

## Decisions

## Evidence

## Meetings

## Releases

## Notes

## References
"""


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def build_memory_plan(path, dry_run=True):
    project_root = Path(path).resolve()
    writes = []
    for relative in ["memory/index.md", *MEMORY_DIRS]:
        if not (project_root / relative).exists():
            writes.append(relative)
    return {
        "schema": "moduflow.memory-plan.v1",
        "project_root": str(project_root),
        "dry_run": dry_run,
        "writes": writes,
        "preserves_existing_files": True,
        "portable": True,
    }


def write_text_if_missing(path, content):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def mkdir_if_missing(path):
    if path.exists():
        return False
    path.mkdir(parents=True, exist_ok=True)
    return True


def apply_memory_plan(plan):
    project_root = Path(plan["project_root"])
    written = []
    for relative in MEMORY_DIRS:
        if mkdir_if_missing(project_root / relative):
            written.append(relative)
    if write_text_if_missing(project_root / "memory" / "index.md", INDEX_CONTENT):
        written.append("memory/index.md")
    plan["written"] = written
    return plan


def format_list(values):
    if not values:
        return "[]"
    return "[" + ", ".join(str(value) for value in values) + "]"


def frontmatter_value(value):
    return "" if value is None else str(value).replace("\n", " ").strip()


def entry_body(
    kind,
    title,
    entry_id,
    issue_id="",
    spec_path="",
    summary="",
    rationale="",
    evidence="",
    alternatives="",
    owner="",
    reversal_conditions="",
    tags=None,
):
    today = date.today().isoformat()
    return f"""---
id: {entry_id}
kind: {kind}
title: {frontmatter_value(title)}
issue_id: {frontmatter_value(issue_id)}
spec: {frontmatter_value(spec_path)}
owner: {frontmatter_value(owner)}
date: {today}
tags: {format_list(tags or [])}
summary: {frontmatter_value(summary)}
rationale: {frontmatter_value(rationale)}
evidence: {frontmatter_value(evidence)}
alternatives: {frontmatter_value(alternatives)}
reversal_conditions: {frontmatter_value(reversal_conditions)}
confidence: medium
---

# {title}

## Summary

{summary or "Capture the durable project memory and why it matters."}

## Rationale

{rationale or "-"}

## Evidence

{evidence or "-"}

## Alternatives

{alternatives or "-"}

## Links

- Issue: {issue_id}
- Spec: {spec_path}

## Reversal Conditions

{reversal_conditions or "-"}
"""


def create_memory_entry(
    path,
    kind,
    title,
    issue_id="",
    spec_path="",
    summary="",
    rationale="",
    evidence="",
    alternatives="",
    owner="",
    reversal_conditions="",
    tags=None,
):
    if kind not in KIND_TO_DIR:
        raise ValueError(f"Unsupported memory kind: {kind}")
    project_root = Path(path).resolve()
    target_dir = project_root / KIND_TO_DIR[kind]
    target_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    base_id = f"{today}-{slugify(title)}"
    entry_id = base_id
    suffix = 2
    while (target_dir / f"{entry_id}.md").exists():
        entry_id = f"{base_id}-{suffix}"
        suffix += 1
    target = target_dir / f"{entry_id}.md"
    target.write_text(
        entry_body(
            kind,
            title,
            entry_id,
            issue_id=issue_id,
            spec_path=spec_path,
            summary=summary,
            rationale=rationale,
            evidence=evidence,
            alternatives=alternatives,
            owner=owner,
            reversal_conditions=reversal_conditions,
            tags=tags or [],
        ),
        encoding="utf-8",
    )
    return {
        "id": entry_id,
        "kind": kind,
        "path": str(target.relative_to(project_root)),
        "portable": True,
    }


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    meta_text = parts[0].split("\n", 1)[1]
    metadata = {}
    for line in meta_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, parts[1]


def iter_memory_files(root):
    memory_root = Path(root).resolve() / "memory"
    if not memory_root.exists():
        return []
    return sorted(path for path in memory_root.glob("*/*.md") if path.is_file())


def search_memory_entries(path, query="", kind="", issue_id="", spec_path="", tag="", limit=20):
    project_root = Path(path).resolve()
    tokens = [token.lower() for token in query.split() if token.strip()]
    hits = []
    for memory_file in iter_memory_files(project_root):
        text = memory_file.read_text(encoding="utf-8")
        metadata, content = parse_frontmatter(text)
        haystack = text.lower()
        if tokens and not all(token in haystack for token in tokens):
            continue
        if kind and metadata.get("kind") != kind:
            continue
        if issue_id and metadata.get("issue_id") != issue_id:
            continue
        if spec_path and metadata.get("spec") != spec_path:
            continue
        if tag and tag not in metadata.get("tags", ""):
            continue
        hits.append(
            {
                "id": metadata.get("id") or memory_file.stem,
                "kind": metadata.get("kind", ""),
                "title": metadata.get("title", ""),
                "path": str(memory_file.relative_to(project_root)),
                "summary": metadata.get("summary", ""),
                "tags": metadata.get("tags", "[]"),
                "score": len(tokens),
                "content": content.strip(),
            }
        )
        if len(hits) >= limit:
            break
    return hits


def get_memory_entry(path, entry_id):
    project_root = Path(path).resolve()
    for memory_file in iter_memory_files(project_root):
        text = memory_file.read_text(encoding="utf-8")
        metadata, content = parse_frontmatter(text)
        found_id = metadata.get("id") or memory_file.stem
        if found_id == entry_id:
            return {
                "id": found_id,
                "kind": metadata.get("kind", ""),
                "title": metadata.get("title", ""),
                "path": str(memory_file.relative_to(project_root)),
                "metadata": metadata,
                "content": content.strip(),
            }
    return None


def main():
    parser = argparse.ArgumentParser(description="Plan, initialize, write, search, or get ModuFlow project memory.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="Create missing memory folders and index.")
    parser.add_argument("--kind", choices=sorted(KIND_TO_DIR), help="Create a single memory entry.")
    parser.add_argument("--title", default="", help="Title for a single memory entry.")
    parser.add_argument("--issue-id", default="")
    parser.add_argument("--spec", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--rationale", default="")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--alternatives", default="")
    parser.add_argument("--owner", default="")
    parser.add_argument("--reversal-conditions", default="")
    parser.add_argument("--tags", default="", help="Comma-separated tags.")
    parser.add_argument("--search", default="", help="Search project memory entries.")
    parser.add_argument("--get", default="", help="Get one memory entry by id.")
    args = parser.parse_args()

    if args.get:
        result = get_memory_entry(args.project_path, args.get)
    elif args.search:
        result = search_memory_entries(args.project_path, args.search, kind=args.kind or "")
    elif args.kind:
        if not args.title:
            parser.error("--title is required when --kind is used")
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        result = create_memory_entry(
            args.project_path,
            args.kind,
            args.title,
            issue_id=args.issue_id,
            spec_path=args.spec,
            summary=args.summary,
            rationale=args.rationale,
            evidence=args.evidence,
            alternatives=args.alternatives,
            owner=args.owner,
            reversal_conditions=args.reversal_conditions,
            tags=tags,
        )
    else:
        result = build_memory_plan(args.project_path, dry_run=not args.write)
        if args.write:
            result = apply_memory_plan(result)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
