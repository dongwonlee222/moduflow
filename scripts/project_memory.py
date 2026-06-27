#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path


MEMORY_DIRS = [
    "memory/.candidates",
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
    source_event="",
    source_artifacts=None,
    review_after="",
    supersedes=None,
    superseded_by=None,
    depends_on=None,
    references=None,
    storage_policy="local",
    mirror_targets=None,
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
source_event: {frontmatter_value(source_event)}
source_artifacts: {format_list(source_artifacts or [])}
review_after: {frontmatter_value(review_after)}
supersedes: {format_list(supersedes or [])}
superseded_by: {format_list(superseded_by or [])}
depends_on: {format_list(depends_on or [])}
references: {format_list(references or [])}
storage_policy: {frontmatter_value(storage_policy)}
mirror_targets: {format_list(mirror_targets or [])}
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


def candidate_body(**kwargs):
    body = entry_body(**kwargs)
    return body.replace(
        f"id: {kwargs['entry_id']}\n",
        f"id: {kwargs['entry_id']}\nstatus: candidate\n",
        1,
    )


def create_memory_entry(
    path,
    kind,
    title,
    issue_id="",
    spec_path="",
    source_event="",
    source_artifacts=None,
    review_after="",
    supersedes=None,
    superseded_by=None,
    depends_on=None,
    references=None,
    storage_policy="local",
    mirror_targets=None,
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
            source_event=source_event,
            source_artifacts=source_artifacts or [],
            review_after=review_after,
            supersedes=supersedes or [],
            superseded_by=superseded_by or [],
            depends_on=depends_on or [],
            references=references or [],
            storage_policy=storage_policy,
            mirror_targets=mirror_targets or [],
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


def create_memory_candidate(
    path,
    kind,
    title,
    issue_id="",
    spec_path="",
    source_event="",
    source_artifacts=None,
    review_after="",
    supersedes=None,
    depends_on=None,
    references=None,
    storage_policy="local",
    mirror_targets=None,
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
    target_dir = project_root / "memory" / ".candidates"
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
        candidate_body(
            kind=kind,
            title=title,
            entry_id=entry_id,
            issue_id=issue_id,
            spec_path=spec_path,
            source_event=source_event,
            source_artifacts=source_artifacts or [],
            review_after=review_after,
            supersedes=supersedes or [],
            superseded_by=[],
            depends_on=depends_on or [],
            references=references or [],
            storage_policy=storage_policy,
            mirror_targets=mirror_targets or [],
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
        "status": "candidate",
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


def parse_list_value(value):
    value = value.strip()
    if not value.startswith("[") or not value.endswith("]"):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip() for item in inner.split(",") if item.strip()]


def iter_memory_files(root):
    memory_root = Path(root).resolve() / "memory"
    if not memory_root.exists():
        return []
    return sorted(path for path in memory_root.glob("*/*.md") if path.is_file())


def iter_candidate_files(root):
    candidate_root = Path(root).resolve() / "memory" / ".candidates"
    if not candidate_root.exists():
        return []
    return sorted(path for path in candidate_root.glob("*.md") if path.is_file())


def list_memory_candidates(path):
    project_root = Path(path).resolve()
    candidates = []
    import time
    now = time.time()
    day_seconds = 24 * 3600
    stale_threshold = 14 * day_seconds

    for candidate_file in iter_candidate_files(project_root):
        # 14-day automatic stale pruning based on file mtime
        mtime = candidate_file.stat().st_mtime
        if now - mtime > stale_threshold:
            try:
                candidate_file.unlink()
            except Exception:
                pass
            continue

        try:
            text = candidate_file.read_text(encoding="utf-8")
            metadata, _ = parse_frontmatter(text)
            candidates.append(
                {
                    "id": metadata.get("id") or candidate_file.stem,
                    "kind": metadata.get("kind", ""),
                    "title": metadata.get("title", ""),
                    "path": str(candidate_file.relative_to(project_root)),
                    "summary": metadata.get("summary", ""),
                    "status": metadata.get("status", "candidate"),
                }
            )
        except Exception:
            pass
    return candidates


def approve_memory_candidate(path, candidate_id):
    project_root = Path(path).resolve()
    for candidate_file in iter_candidate_files(project_root):
        try:
            text = candidate_file.read_text(encoding="utf-8")
            metadata, _ = parse_frontmatter(text)
            found_id = metadata.get("id") or candidate_file.stem
            if found_id != candidate_id:
                continue
            kind = metadata.get("kind", "")
            if kind not in KIND_TO_DIR:
                raise ValueError(f"Unsupported memory kind: {kind}")
            target_dir = project_root / KIND_TO_DIR[kind]
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / candidate_file.name
            approved_text = text.replace("status: candidate\n", "status: approved\n", 1)
            # Fallback if newline is different
            if "status: approved" not in approved_text:
                approved_text = text.replace("status: candidate", "status: approved", 1)
            target.write_text(approved_text, encoding="utf-8")
            candidate_file.unlink()
            return {
                "id": found_id,
                "kind": kind,
                "status": "approved",
                "path": str(target.relative_to(project_root)),
                "portable": True,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to approve candidate: {e}")
    return None


def reject_memory_candidate(path, candidate_id):
    project_root = Path(path).resolve()
    for candidate_file in iter_candidate_files(project_root):
        try:
            text = candidate_file.read_text(encoding="utf-8")
            metadata, _ = parse_frontmatter(text)
            found_id = metadata.get("id") or candidate_file.stem
            if found_id == candidate_id:
                candidate_file.unlink()
                return {
                    "id": found_id,
                    "status": "rejected",
                    "deleted": True
                }
        except Exception:
            pass
    return None


def capture_to_memory_candidate(path, kind, source_file, title=None, tags=None):
    if kind not in KIND_TO_DIR:
        raise ValueError(f"Unsupported memory kind: {kind}")
    project_root = Path(path).resolve()
    src_path = Path(source_file).resolve()
    if not src_path.exists():
        # Try relative to project_root if absolute doesn't exist
        src_path = project_root / source_file
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")

    text = src_path.read_text(encoding="utf-8", errors="ignore")
    metadata, content = parse_frontmatter(text)

    # Resolve title
    final_title = title or metadata.get("title")
    if not final_title:
        # Try to find first markdown header
        for line in text.splitlines():
            if line.strip().startswith("# "):
                final_title = line.strip()[2:].strip()
                break
        if not final_title:
            final_title = src_path.stem.replace("-", " ").replace("_", " ").title()

    # Extract tags
    final_tags = tags or []
    if "tags" in metadata:
        meta_tags = metadata["tags"]
        if isinstance(meta_tags, list):
            final_tags.extend(meta_tags)
        elif isinstance(meta_tags, str):
            final_tags.extend(parse_list_value(meta_tags))

    # Resolve other fields
    summary = metadata.get("summary", "")
    if not summary and content:
        # Take first 3 lines of content as summary
        summary = "\n".join(content.strip().splitlines()[:3])

    evidence_text = metadata.get("evidence", "")
    if not evidence_text and kind == "evidence":
        evidence_text = content.strip()

    rationale_text = metadata.get("rationale", "")
    if not rationale_text and kind == "decision":
        rationale_text = content.strip()

    return create_memory_candidate(
        path=project_root,
        kind=kind,
        title=final_title,
        issue_id=metadata.get("issue_id", ""),
        spec_path=metadata.get("spec", ""),
        source_event=metadata.get("source_event", "manual_capture"),
        source_artifacts=[str(src_path.relative_to(project_root))] if src_path.is_relative_to(project_root) else [str(src_path)],
        review_after=metadata.get("review_after", ""),
        supersedes=parse_list_value(metadata.get("supersedes", "")) if isinstance(metadata.get("supersedes"), str) else metadata.get("supersedes"),
        depends_on=parse_list_value(metadata.get("depends_on", "")) if isinstance(metadata.get("depends_on"), str) else metadata.get("depends_on"),
        references=parse_list_value(metadata.get("references", "")) if isinstance(metadata.get("references"), str) else metadata.get("references"),
        storage_policy=metadata.get("storage_policy", "canonical_git"),
        mirror_targets=parse_list_value(metadata.get("mirror_targets", "")) if isinstance(metadata.get("mirror_targets"), str) else metadata.get("mirror_targets"),
        summary=summary,
        rationale=rationale_text,
        evidence=evidence_text,
        alternatives=metadata.get("alternatives", ""),
        owner=metadata.get("owner", ""),
        reversal_conditions=metadata.get("reversal_conditions", ""),
        tags=final_tags
    )


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
        match_reasons = []
        for token in tokens:
            if token in haystack:
                match_reasons.append(f"query: {token}")
        if kind:
            match_reasons.append(f"kind: {kind}")
        if issue_id:
            match_reasons.append(f"issue_id: {issue_id}")
        if spec_path:
            match_reasons.append(f"spec: {spec_path}")
        if tag:
            match_reasons.append(f"tag: {tag}")
        hits.append(
            {
                "id": metadata.get("id") or memory_file.stem,
                "kind": metadata.get("kind", ""),
                "title": metadata.get("title", ""),
                "path": str(memory_file.relative_to(project_root)),
                "summary": metadata.get("summary", ""),
                "tags": metadata.get("tags", "[]"),
                "match_reasons": match_reasons,
                "source_artifacts": parse_list_value(metadata.get("source_artifacts", "[]")),
                "issue_id": metadata.get("issue_id", ""),
                "spec": metadata.get("spec", ""),
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


def memory_export_guidance(target):
    target = (target or "").strip() or "local"
    warnings = [
        "Repo-local Markdown remains canonical.",
        "External indexes and mirrors must be rebuildable from memory/.",
    ]
    if target == "google-drive":
        warnings.append("Do not treat Google Drive as the source of truth.")
        warnings.append("Avoid syncing .git/ through Google Drive conflict handling.")
    return {
        "schema": "moduflow.memory-export-guidance.v1",
        "target": target,
        "canonical": "memory/",
        "mode": "mirror/export",
        "recommended_sources": ["memory/", "specs/", "issues/", "workspace/", "business/", "reports/"],
        "warnings": warnings,
    }


def generate_memory_graph(root):
    project_root = Path(root).resolve()
    nodes = {}
    edges = []

    for memory_file in iter_memory_files(project_root):
        try:
            text = memory_file.read_text(encoding="utf-8")
            metadata, _ = parse_frontmatter(text)
        except Exception:
            continue

        entry_id = metadata.get("id") or memory_file.stem
        kind = metadata.get("kind", "note")
        title = metadata.get("title") or entry_id

        nodes[entry_id] = {
            "title": title,
            "kind": kind,
        }

        # Parse relationships
        supersedes = parse_list_value(metadata.get("supersedes", "[]"))
        depends_on = parse_list_value(metadata.get("depends_on", "[]"))
        references = parse_list_value(metadata.get("references", "[]"))

        for target in supersedes:
            edges.append((entry_id, target, "supersedes"))
        for target in depends_on:
            edges.append((entry_id, target, "depends_on"))
        for target in references:
            edges.append((entry_id, target, "references"))

    # Render Mermaid
    lines = ["flowchart TD"]

    # Define classes for styling
    lines.append("    classDef decision fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;")
    lines.append("    classDef release fill:#fff3e0,stroke:#ff9800,stroke-width:2px;")
    lines.append("    classDef spec fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;")
    lines.append("    classDef note fill:#f5f5f5,stroke:#757575,stroke-width:1px;")

    # Declare nodes
    for entry_id, info in sorted(nodes.items()):
        node_var = entry_id.replace("-", "_").replace(".", "_")
        escaped_title = info["title"].replace('"', '\\"')
        lines.append(f'    {node_var}["{escaped_title} ({entry_id})"]')
        # Assign class
        kind = info["kind"]
        if kind in {"decision", "release", "spec", "note"}:
            lines.append(f"    class {node_var} {kind};")

    # Declare edges
    for source, target, label in edges:
        source_var = source.replace("-", "_").replace(".", "_")
        target_var = target.replace("-", "_").replace(".", "_")
        # Check if target exists in nodes to avoid broken graph references
        if target not in nodes:
            lines.append(f'    {target_var}["{target}"]')
        lines.append(f"    {source_var} -->|{label}| {target_var}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Plan, initialize, write, search, or get ModuFlow project memory.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="Create missing memory folders and index.")
    parser.add_argument("--candidate", action="store_true", help="Create a reviewable memory candidate.")
    parser.add_argument("--list-candidates", action="store_true", help="List reviewable memory candidates.")
    parser.add_argument("--approve", default="", help="Approve a memory candidate by id.")
    parser.add_argument("--reject", default="", help="Reject a memory candidate by id.")
    parser.add_argument("--capture", action="store_true", help="Capture a source document to candidate memory.")
    parser.add_argument("--source", default="", help="Source file for capture.")
    parser.add_argument("--kind", choices=sorted(KIND_TO_DIR), help="Create a single memory entry.")
    parser.add_argument("--title", default="", help="Title for a single memory entry.")
    parser.add_argument("--issue-id", default="")
    parser.add_argument("--spec", default="")
    parser.add_argument("--source-event", default="")
    parser.add_argument("--source-artifacts", default="", help="Comma-separated source artifact links.")
    parser.add_argument("--review-after", default="")
    parser.add_argument("--supersedes", default="", help="Comma-separated superseded memory ids.")
    parser.add_argument("--storage-policy", default="local")
    parser.add_argument("--mirror-targets", default="", help="Comma-separated mirror/export targets.")
    parser.add_argument("--depends-on", default="", help="Comma-separated depends_on memory ids.")
    parser.add_argument("--references", default="", help="Comma-separated references memory ids.")
    parser.add_argument("--graph", action="store_true", help="Render a visual Mermaid chart of the memory context.")
    parser.add_argument("--summary", default="")
    parser.add_argument("--rationale", default="")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--alternatives", default="")
    parser.add_argument("--owner", default="")
    parser.add_argument("--reversal-conditions", default="")
    parser.add_argument("--tags", default="", help="Comma-separated tags.")
    parser.add_argument("--search", default="", help="Search project memory entries.")
    parser.add_argument("--get", default="", help="Get one memory entry by id.")
    parser.add_argument("--export-guidance", default="", help="Return mirror/export guidance for a target.")
    args = parser.parse_args()

    if args.graph:
        print(generate_memory_graph(args.project_path))
        return 0

    if args.get:
        result = get_memory_entry(args.project_path, args.get)
    elif args.search:
        result = search_memory_entries(args.project_path, args.search, kind=args.kind or "")
    elif args.export_guidance:
        result = memory_export_guidance(args.export_guidance)
    elif args.list_candidates:
        result = list_memory_candidates(args.project_path)
    elif args.approve:
        result = approve_memory_candidate(args.project_path, args.approve)
    elif args.reject:
        result = reject_memory_candidate(args.project_path, args.reject)
    elif args.capture:
        if not args.kind or not args.source:
            parser.error("--capture requires --kind and --source")
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        result = capture_to_memory_candidate(
            args.project_path,
            args.kind,
            args.source,
            title=args.title or None,
            tags=tags
        )
    elif args.candidate:
        if not args.kind or not args.title:
            parser.error("--candidate requires --kind and --title")
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        source_artifacts = [item.strip() for item in args.source_artifacts.split(",") if item.strip()]
        supersedes = [item.strip() for item in args.supersedes.split(",") if item.strip()]
        depends_on = [item.strip() for item in args.depends_on.split(",") if item.strip()]
        references = [item.strip() for item in args.references.split(",") if item.strip()]
        mirror_targets = [item.strip() for item in args.mirror_targets.split(",") if item.strip()]
        result = create_memory_candidate(
            args.project_path,
            args.kind,
            args.title,
            issue_id=args.issue_id,
            spec_path=args.spec,
            source_event=args.source_event,
            source_artifacts=source_artifacts,
            review_after=args.review_after,
            supersedes=supersedes,
            depends_on=depends_on,
            references=references,
            storage_policy=args.storage_policy,
            mirror_targets=mirror_targets,
            summary=args.summary,
            rationale=args.rationale,
            evidence=args.evidence,
            alternatives=args.alternatives,
            owner=args.owner,
            reversal_conditions=args.reversal_conditions,
            tags=tags,
        )
    elif args.kind:
        if not args.title:
            parser.error("--title is required when --kind is used")
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        source_artifacts = [item.strip() for item in args.source_artifacts.split(",") if item.strip()]
        supersedes = [item.strip() for item in args.supersedes.split(",") if item.strip()]
        depends_on = [item.strip() for item in args.depends_on.split(",") if item.strip()]
        references = [item.strip() for item in args.references.split(",") if item.strip()]
        mirror_targets = [item.strip() for item in args.mirror_targets.split(",") if item.strip()]
        result = create_memory_entry(
            args.project_path,
            args.kind,
            args.title,
            issue_id=args.issue_id,
            spec_path=args.spec,
            source_event=args.source_event,
            source_artifacts=source_artifacts,
            review_after=args.review_after,
            supersedes=supersedes,
            depends_on=depends_on,
            references=references,
            storage_policy=args.storage_policy,
            mirror_targets=mirror_targets,
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
