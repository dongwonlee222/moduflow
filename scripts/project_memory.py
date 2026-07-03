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
    lines = meta_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            # YAML block list: collect following indented "- item" lines.
            items = []
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith("- "):
                item = lines[j].lstrip()[2:].strip().strip('"').strip("'")
                if item:
                    items.append(item)
                j += 1
            if items:
                metadata[key] = "[" + ", ".join(items) + "]"
                i = j
                continue
        metadata[key] = value
        i += 1
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


def list_memory_ids(path, kind=""):
    """All memory entries as link candidates: [{id, kind, title}].
    For relationship capture at write time — present real ids, never auto-link (043)."""
    entries = search_memory_entries(path, query="", kind=kind, limit=10_000)
    return [{"id": e["id"], "kind": e["kind"], "title": e["title"]} for e in entries]


def isolated_memory_entries(path):
    """Memory entries with no supersedes/depends_on/references AND no issue_id.
    A soft signal of graph gaps — informational, never an error (043)."""
    project_root = Path(path).resolve()
    isolated = []
    for memory_file in iter_memory_files(project_root):
        try:
            metadata, _ = parse_frontmatter(memory_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        has_rel = any(parse_list_value(metadata.get(rel, "[]"))
                      for rel in ("supersedes", "depends_on", "references"))
        has_issue = bool((metadata.get("issue_id") or "").strip())
        if not has_rel and not has_issue:
            isolated.append({
                "id": metadata.get("id") or memory_file.stem,
                "kind": metadata.get("kind", ""),
                "title": metadata.get("title", ""),
            })
    return isolated


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


def _normalize_target(target):
    target = target.strip()
    if not target:
        return None
    if target.startswith("http://") or target.startswith("https://"):
        return None
    if "/" in target or target.endswith(".md"):
        target = Path(target).name
        if target.endswith(".md"):
            target = target[:-3]
    return target


def _collect_graph(root):
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
        nodes[entry_id] = {
            "title": metadata.get("title") or entry_id,
            "kind": metadata.get("kind", "note"),
            "file": str(memory_file.relative_to(project_root)),
            "issue_id": (metadata.get("issue_id") or "").strip(),
        }
        for rel in ("supersedes", "depends_on", "references"):
            for target in parse_list_value(metadata.get(rel, "[]")):
                norm = _normalize_target(target)
                if norm:
                    edges.append((entry_id, norm, rel))
    return nodes, edges


def generate_memory_graph(root):
    nodes, edges = _collect_graph(root)

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


DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ModuFlow Decision Graph</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"></script>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 24px; background: #fff; color: #1a1a1a; }
  h1 { font-size: 20px; font-weight: 500; margin: 0 0 4px; }
  .sub { font-size: 13px; color: #888; margin: 0 0 16px; }
  .legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; margin-bottom: 12px; align-items: center; color: #555; }
  .legend span { display: flex; align-items: center; gap: 6px; }
  .sw { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  #cy { width: 100%; height: 600px; border: 1px solid #ddd; border-radius: 12px; }
  #info { margin-top: 12px; min-height: 48px; padding: 12px 16px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
  #info a { color: #2a78d6; }
  code { font-size: 13px; color: #888; }
  @media (prefers-color-scheme: dark) {
    body { background: #1a1a19; color: #e8e8e3; }
    .legend { color: #aaa; }
    #cy, #info { border-color: #333; }
  }
</style>
</head>
<body>
<h1>ModuFlow Decision Graph</h1>
<p class="sub">__NODE_COUNT__ nodes · __EDGE_COUNT__ edges · generated from memory/ frontmatter</p>
<div class="legend">
  <span><span class="sw" style="background:#378ADD"></span>decision</span>
  <span><span class="sw" style="background:#888780"></span>evidence</span>
  <span><span class="sw" style="background:#1D9E75"></span>deliverable</span>
  <span><span class="sw" style="background:#D85A30"></span>note</span>
  <span>&#9472;&#9472; supersedes</span>
  <span>&#9476;&#9476; references / depends_on</span>
</div>
<div id="cy"></div>
<div id="info">노드를 클릭하면 소스 파일 경로가 표시됩니다. 드래그로 이동, 휠로 줌.</div>
<script>
const ELEMENTS = __ELEMENTS_JSON__;
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
const C = {
  decision:    dark ? {f:'#0C447C',s:'#85B7EB',t:'#E6F1FB'} : {f:'#E6F1FB',s:'#185FA5',t:'#0C447C'},
  evidence:    dark ? {f:'#444441',s:'#B4B2A9',t:'#F1EFE8'} : {f:'#F1EFE8',s:'#5F5E5A',t:'#444441'},
  deliverable: dark ? {f:'#085041',s:'#5DCAA5',t:'#E1F5EE'} : {f:'#E1F5EE',s:'#0F6E56',t:'#085041'},
  note:        dark ? {f:'#712B13',s:'#F0997B',t:'#FAECE7'} : {f:'#FAECE7',s:'#993C1D',t:'#712B13'}
};
const edge = '#888780';
const ks = k => [{selector:'node[kind="'+k+'"]', style:{'background-color':C[k].f,'border-color':C[k].s,'color':C[k].t}}];
const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: ELEMENTS,
  style: [
    {selector:'node', style:{'shape':'round-rectangle','width':'150px','height':'46px','border-width':1.5,'label':'data(label)','text-valign':'center','text-halign':'center','text-wrap':'wrap','text-max-width':'134px','font-size':'12px','font-weight':500}},
    ...ks('decision'), ...ks('evidence'), ...ks('deliverable'), ...ks('note'),
    {selector:'node:selected', style:{'border-width':4}},
    {selector:'edge', style:{'width':1.8,'line-color':edge,'target-arrow-color':edge,'target-arrow-shape':'triangle','curve-style':'bezier','opacity':0.75,'label':'data(rel)','font-size':'10px','color':'#888780','text-rotation':'autorotate','text-margin-y':-8}},
    {selector:'edge[rel="references"]', style:{'line-style':'dashed'}},
    {selector:'edge[rel="depends_on"]', style:{'line-style':'dashed'}}
  ],
  layout: {name:'cose', animate:false, padding:40, nodeRepulsion:18000, idealEdgeLength:130, nodeOverlap:40, componentSpacing:170, numIter:2000, randomize:true},
  wheelSensitivity: 0.2, minZoom: 0.3, maxZoom: 2.5
});
const info = document.getElementById('info');
cy.on('tap','node', evt => {
  const d = evt.target.data();
  info.innerHTML = '<b>'+d.full+'</b><br><a href="'+d.href+'"><code>'+d.file+'</code></a>';
});
</script>
</body>
</html>
"""


def _memory_elements(root):
    """Build Cytoscape elements for the memory graph. Shared by the standalone
    dashboard (042) and the two-tab project view (045)."""
    nodes, edges = _collect_graph(root)
    node_ids = set(nodes)
    elements = []
    for entry_id, info in sorted(nodes.items()):
        file_path = info.get("file", "")
        href = file_path[len("memory/"):] if file_path.startswith("memory/") else file_path
        elements.append({"data": {
            "id": entry_id,
            "label": info["title"],
            "kind": info["kind"],
            "full": info["title"],
            "file": file_path,
            "href": href,
            "panelhref": f"mem-{entry_id}.html",
            "issue": info.get("issue_id", ""),
        }})
    edge_count = 0
    for idx, (src, tgt, rel) in enumerate(edges):
        if tgt not in node_ids:
            continue
        elements.append({"data": {"id": f"e{idx}", "source": src, "target": tgt, "rel": rel}})
        edge_count += 1
    return elements, len(nodes), edge_count


def render_dashboard_html(root):
    elements, node_count, edge_count = _memory_elements(root)
    return (
        DASHBOARD_TEMPLATE
        .replace("__NODE_COUNT__", str(node_count))
        .replace("__EDGE_COUNT__", str(edge_count))
        .replace("__ELEMENTS_JSON__", json.dumps(elements, ensure_ascii=False, indent=2))
    )


# --- Issue graph + project view (045) --------------------------------------

ISSUE_STATUS_COLORS = {
    # bucket: (fill, stroke, text) — light theme; dark handled in CSS-neutral text
    "done":       {"f": "#E1F5EE", "s": "#0F6E56", "t": "#085041"},
    "active":     {"f": "#DCEBFB", "s": "#2A78D6", "t": "#16467E"},
    "backlog":    {"f": "#ECEBE6", "s": "#888780", "t": "#4A4944"},
    "superseded": {"f": "#FAECE7", "s": "#993C1D", "t": "#712B13"},
}
MEMORY_KIND_ICON = {
    "decision": "\U0001F4A1",     # 💡
    "evidence": "\U0001F4CE",     # 📎
    "deliverable": "\U0001F4E6",  # 📦
    "release": "\U0001F680",      # 🚀
    "meeting": "\U0001F5E3",      # 🗣
    "note": "\U0001F4DD",         # 📝
    "reference": "\U0001F517",    # 🔗
}


def _issue_status_bucket(status_word):
    w = (status_word or "").lower()
    if w.startswith("superseded"):
        return "superseded"
    if w in ("done", "active", "backlog", "blocked", "review"):
        return w
    return "backlog"


def _resolve_num_to_issue(num, valid_ids):
    for vid in valid_ids:
        if vid == num or vid.startswith(num + "-"):
            return vid
    return None


def _issue_linked_memory(root):
    """Map issue_id -> [{id,title,kind,file}] from memory frontmatter. Sparse by design."""
    project_root = Path(root).resolve()
    mapping = {}
    for memory_file in iter_memory_files(project_root):
        try:
            metadata, _ = parse_frontmatter(memory_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        issue_id = (metadata.get("issue_id") or "").strip()
        if not issue_id:
            continue
        mapping.setdefault(issue_id, []).append({
            "id": metadata.get("id") or memory_file.stem,
            "title": metadata.get("title") or memory_file.stem,
            "kind": metadata.get("kind", "note"),
            "file": str(memory_file.relative_to(project_root)),
        })
    return mapping


def _related_refs(text, self_id, valid_ids):
    """Issue ids referenced in the `## Related` / `## Related Issues` section only
    (not anywhere in the body), excluding self and unknown ids."""
    m = re.search(r"^##\s+Related.*$", text, re.M)
    if not m:
        return set()
    section = text[m.end():]
    nxt = re.search(r"^##\s+", section, re.M)
    if nxt:
        section = section[:nxt.start()]
    refs = set()
    for mm in re.finditer(r"`([0-9]{3}-[a-z0-9-]+)`", section):
        rid = mm.group(1)
        if rid != self_id and rid in valid_ids:
            refs.add(rid)
    return refs


def _collect_issue_graph(root):
    """Nodes = issues (status-colored). Edges: `supersedes` (solid) from status
    lines + prose, and `related` (dashed, toggleable) from the `## Related` section.
    Related edges are undirected-deduped and exclude pairs already joined by supersedes."""
    project_root = Path(root).resolve()
    issues_dir = project_root / "issues"
    nodes = {}
    edges = []
    if not issues_dir.is_dir():
        return nodes, edges
    raw = {}
    for issue_file in sorted(issues_dir.glob("*.md")):
        raw[issue_file.stem] = issue_file.read_text(encoding="utf-8")
    valid_ids = set(raw)
    for issue_id, text in raw.items():
        title = issue_id
        m_title = re.search(r"^#\s+(.+)$", text, re.M)
        if m_title:
            title = re.sub(r"^Issue:\s*", "", m_title.group(1).strip())
            title = title.replace("`", "").strip()
        m_status = re.search(r"\*\*Status:\s*([A-Za-z0-9-]+)", text)
        status_word = m_status.group(1) if m_status else "backlog"
        m_goal = re.search(r"goal `([^`]+)`", text)
        goal = m_goal.group(1) if m_goal else "(기타)"
        nodes[issue_id] = {"title": title, "status": _issue_status_bucket(status_word), "goal": goal}
        # supersedes prose: "Supersedes `NNN-...`"
        for m in re.finditer(r"[Ss]upersedes\s+`([0-9]{3}-[a-z0-9-]+)`", text):
            edges.append((issue_id, m.group(1), "supersedes"))
        # status "superseded-by-NNN" → reversed: NNN supersedes this issue
        mb = re.match(r"superseded-by-(\d+)", status_word.lower())
        if mb:
            tgt = _resolve_num_to_issue(mb.group(1), valid_ids)
            if tgt:
                edges.append((tgt, issue_id, "supersedes"))
    edges = list(dict.fromkeys(
        (s, t, r) for (s, t, r) in edges if s in valid_ids and t in valid_ids
    ))
    # related edges (dashed, toggleable): from the Related section, undirected,
    # excluding pairs already joined by a supersedes edge.
    sup_pairs = {frozenset((s, t)) for (s, t, _r) in edges}
    related_pairs = set()
    for issue_id, text in raw.items():
        for rid in _related_refs(text, issue_id, valid_ids):
            pair = frozenset((issue_id, rid))
            if pair not in sup_pairs:
                related_pairs.add(pair)
    for pair in sorted(related_pairs, key=lambda p: sorted(p)):
        a, b = sorted(pair)
        edges.append((a, b, "related"))
    return nodes, edges


def _issue_number(issue_id):
    m = re.match(r"^(\d+)", issue_id or "")
    return int(m.group(1)) if m else None


def _parse_next_command(text):
    m = re.search(r"^##\s+Next Command\s*$", text, re.M)
    if not m:
        return ""
    section = text[m.end():]
    nxt = re.search(r"^##\s+", section, re.M)
    if nxt:
        section = section[:nxt.start()]
    m_cmd = re.search(r"`([^`]+)`", section)
    if m_cmd:
        return m_cmd.group(1).strip()
    for line in section.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("- ").strip()
    return ""


def _issue_artifact_coverage(root, issue_id):
    root = Path(root).resolve()
    spec_dir = root / "specs" / issue_id
    issue_file = root / "issues" / f"{issue_id}.md"
    return {
        "issue": issue_file.is_file(),
        "spec": (spec_dir / "spec.md").is_file(),
        "spec_ko": (spec_dir / "spec.ko.md").is_file(),
        "plan": (spec_dir / "plan.md").is_file(),
        "plan_ko": (spec_dir / "plan.ko.md").is_file(),
        "tasks": (spec_dir / "tasks.md").is_file(),
        "tasks_ko": (spec_dir / "tasks.ko.md").is_file(),
        "status": (spec_dir / "status.md").is_file(),
        "review": (spec_dir / "review.md").is_file(),
        "pr": (spec_dir / "pr.md").is_file(),
        "release": (spec_dir / "release.md").is_file(),
        "human_review_ko": (spec_dir / "human-review.ko.md").is_file(),
    }


def _issue_phase_from_coverage(coverage):
    if coverage.get("release"):
        return "release"
    if coverage.get("pr"):
        return "pr"
    if coverage.get("review"):
        return "review"
    if coverage.get("tasks") or coverage.get("plan"):
        return "execute"
    if coverage.get("spec"):
        return "plan"
    return "spec"


def _issue_attention_flags(status, next_command, coverage):
    flags = []
    if not coverage.get("spec"):
        flags.append("missing_spec")
    if coverage.get("spec") and not coverage.get("plan"):
        flags.append("missing_plan")
    if not next_command:
        flags.append("no_next")
    if not coverage.get("review"):
        flags.append("no_review")
    if not coverage.get("pr"):
        flags.append("no_pr")
    if not (coverage.get("spec_ko") or coverage.get("plan_ko") or coverage.get("tasks_ko") or coverage.get("human_review_ko")):
        flags.append("no_ko")
    if status == "blocked":
        flags.append("blocked")
    return flags


def _issue_updated(text):
    dates = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text or "")
    return dates[-1] if dates else ""


def _collect_issue_table(root):
    project_root = Path(root).resolve()
    issues_dir = project_root / "issues"
    if not issues_dir.is_dir():
        return []
    graph_nodes, graph_edges = _collect_issue_graph(project_root)
    linked = _issue_linked_memory(project_root)
    relation_counts = {}
    for src, tgt, _rel in graph_edges:
        relation_counts[src] = relation_counts.get(src, 0) + 1
        relation_counts[tgt] = relation_counts.get(tgt, 0) + 1
    rows = []
    for issue_file in sorted(issues_dir.glob("*.md")):
        issue_id = issue_file.stem
        text = issue_file.read_text(encoding="utf-8")
        info = graph_nodes.get(issue_id, {})
        coverage = _issue_artifact_coverage(project_root, issue_id)
        status = info.get("status", "backlog")
        next_command = _parse_next_command(text)
        rows.append({
            "id": issue_id,
            "number": _issue_number(issue_id),
            "title": info.get("title", issue_id),
            "status": status,
            "goal": info.get("goal", "(기타)"),
            "phase": _issue_phase_from_coverage(coverage),
            "next_command": next_command,
            "href": f"issue-{issue_id}.html",
            "artifact_coverage": coverage,
            "linked_memory_count": len(linked.get(issue_id, [])),
            "relationship_count": relation_counts.get(issue_id, 0),
            "attention_flags": _issue_attention_flags(status, next_command, coverage),
            "updated": _issue_updated(text),
        })
    return rows


def _issue_elements(root):
    nodes, edges = _collect_issue_graph(root)
    linked = _issue_linked_memory(root)
    # Group issues by goal → compound "goal box" parents, children placed in
    # number order inside each box (preset layout). This is the "flow" the user
    # asked for: structural grouping by goal, not a force-directed hairball.
    groups = {}
    for iid in sorted(nodes):
        groups.setdefault(nodes[iid]["goal"], []).append(iid)
    goal_order = sorted(g for g in groups if g != "(기타)") + (["(기타)"] if "(기타)" in groups else [])
    COLW, ROWH, PERROW, BAND = 175, 96, 6, 70
    elements = []
    y = 0
    for goal in goal_order:
        ids = groups[goal]
        pid = "goal:" + goal
        elements.append({"data": {"id": pid, "label": goal, "isgoal": True}})
        last_row = 0
        for i, iid in enumerate(ids):
            col, row = i % PERROW, i // PERROW
            last_row = row
            info = nodes[iid]
            mem = linked.get(iid, [])
            display = iid.replace("-", " ")  # spaces let the label wrap inside the box
            elements.append({
                "data": {
                    "id": iid,
                    "parent": pid,
                    "title": iid,
                    "label": display,
                    "labelbase": display,
                    "status": info["status"],
                    "memcount": len(mem),
                    "href": f"issue-{iid}.html",
                    "memory": [{"id": e["id"], "title": e["title"], "kind": e["kind"], "file": e["file"]} for e in mem],
                },
                "position": {"x": col * COLW, "y": y + row * ROWH},
            })
        y += (last_row + 1) * ROWH + BAND
    for idx, (s, t, rel) in enumerate(edges):
        elements.append({"data": {"id": f"ie{idx}", "source": s, "target": t, "rel": rel}})
    return elements, len(nodes), len(edges)


PROJECT_VIEW_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ModuFlow 프로젝트 뷰</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"></script>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #fff; color: #1a1a1a; }
  h1 { font-size: 19px; font-weight: 500; margin: 0 0 12px; }
  .tabs { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }
  .tab { padding: 6px 14px; border: 1px solid #ccc; border-radius: 8px; background: #f5f5f3; cursor: pointer; font-size: 14px; }
  .tab.on { background: #2a78d6; color: #fff; border-color: #2a78d6; }
  .toggle { margin-left: auto; font-size: 13px; color: #555; display: flex; align-items: center; gap: 6px; cursor: pointer; }
  .legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: 13px; margin-bottom: 10px; color: #555; align-items: center; }
  .legend span { display: flex; align-items: center; gap: 6px; }
  .sw { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  .cy { width: 100%; height: 600px; border: 1px solid #ddd; border-radius: 12px; }
  .db { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
  .dbbar { display: grid; grid-template-columns: minmax(180px, 1fr) auto auto; gap: 8px; align-items: center; padding: 10px; border-bottom: 1px solid #ddd; background: #fafaf8; }
  .dbbar input, .dbbar select { font: inherit; font-size: 13px; padding: 7px 9px; border: 1px solid #ccc; border-radius: 6px; background: #fff; color: inherit; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip { font: inherit; font-size: 12px; padding: 6px 9px; border: 1px solid #ccc; border-radius: 999px; background: #fff; cursor: pointer; }
  .chip.on { border-color: #2a78d6; background: #dcebfb; color: #16467e; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 9px 10px; border-bottom: 1px solid #eee; text-align: left; vertical-align: top; }
  th { font-size: 12px; color: #666; background: #f5f5f3; font-weight: 600; }
  tr.issue-row { cursor: pointer; }
  tr.issue-row:hover { background: #f8fbff; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
  .badge { display: inline-block; min-width: 18px; text-align: center; padding: 2px 5px; margin: 0 2px 2px 0; border-radius: 5px; border: 1px solid #ccc; font-size: 11px; color: #555; }
  .badge.missing { color: #aaa; border-style: dashed; }
  .flag { display: inline-block; padding: 2px 6px; margin: 0 3px 3px 0; border-radius: 999px; background: #faece7; color: #712b13; font-size: 11px; white-space: nowrap; }
  .empty { padding: 24px; text-align: center; color: #888; }
  .hidden { display: none; }
  #info { margin-top: 12px; min-height: 56px; padding: 12px 16px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; line-height: 1.7; }
  #info a { color: #2a78d6; cursor: pointer; }
  #info .mem { display: block; }
  code { font-size: 13px; color: #888; }
  @media (prefers-color-scheme: dark) {
    body { background: #1a1a19; color: #e8e8e3; }
    .tab { background: #2a2a28; border-color: #444; color: #ddd; }
    .legend, .toggle { color: #aaa; }
    .cy, .db, #info { border-color: #333; }
    .dbbar, th { background: #232321; border-color: #333; }
    .dbbar input, .dbbar select, .chip { background: #2a2a28; border-color: #444; color: #ddd; }
    td, th { border-bottom-color: #333; }
    tr.issue-row:hover { background: #202a33; }
    .chip.on { background: #16467e; color: #dcebfb; }
  }
</style>
</head>
<body>
<h1>ModuFlow 프로젝트 뷰</h1>
<div class="tabs">
  <div class="tab" id="tab-db">이슈 DB</div>
  <div class="tab" id="tab-issues">이슈 그래프</div>
  <div class="tab" id="tab-memory">지식 그래프</div>
  <label class="toggle"><input type="checkbox" id="rel-toggle" checked> 관계선 표시</label>
  <label class="toggle" style="margin-left:0"><input type="checkbox" id="badge-toggle" checked> 🧠 지식 배지 표시</label>
</div>
<div class="legend" id="legend-issues">
  <span><span class="sw" style="background:#2A78D6"></span>active</span>
  <span><span class="sw" style="background:#0F6E56"></span>done</span>
  <span><span class="sw" style="background:#888780"></span>backlog</span>
  <span><span class="sw" style="background:#993C1D"></span>superseded</span>
  <span><span class="sw" style="background:transparent;border:2px solid #E8590C"></span>현재 진행</span>
  <span>&#9472;&#9472; supersedes</span>
</div>
<div class="legend hidden" id="legend-memory">
  <span><span class="sw" style="background:#378ADD"></span>decision</span>
  <span><span class="sw" style="background:#888780"></span>evidence</span>
  <span><span class="sw" style="background:#1D9E75"></span>deliverable</span>
  <span><span class="sw" style="background:#D85A30"></span>note</span>
</div>
<div id="issue-db" class="db"></div>
<div id="cy-issues" class="cy hidden"></div>
<div id="cy-memory" class="cy hidden"></div>
<div id="info">이슈 DB에서 작업 상태를 훑거나, 그래프 탭에서 관계를 확인합니다.</div>
<script>
const ISSUE_ROWS = __ISSUE_ROWS__;
const ISSUE_ELEMENTS = __ISSUE_ELEMENTS__;
const MEMORY_ELEMENTS = __MEMORY_ELEMENTS__;
const KIND_ICON = {decision:'\\u{1F4A1}', evidence:'\\u{1F4CE}', deliverable:'\\u{1F4E6}', release:'\\u{1F680}', meeting:'\\u{1F5E3}', note:'\\u{1F4DD}', reference:'\\u{1F517}'};
const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const IC = {
  done:       dark ? {f:'#085041',s:'#5DCAA5',t:'#E1F5EE'} : {f:'#E1F5EE',s:'#0F6E56',t:'#085041'},
  active:     dark ? {f:'#16467E',s:'#7FB2EE',t:'#DCEBFB'} : {f:'#DCEBFB',s:'#2A78D6',t:'#16467E'},
  backlog:    dark ? {f:'#3A3A36',s:'#9A998F',t:'#E8E8E3'} : {f:'#ECEBE6',s:'#888780',t:'#4A4944'},
  superseded: dark ? {f:'#712B13',s:'#F0997B',t:'#FAECE7'} : {f:'#FAECE7',s:'#993C1D',t:'#712B13'}
};
const MC = {
  decision:    dark ? {f:'#0B3D66',s:'#378ADD',t:'#D6E9FB'} : {f:'#D6E9FB',s:'#1F6FBF',t:'#0B3D66'},
  evidence:    dark ? {f:'#3A3A36',s:'#9A998F',t:'#E8E8E3'} : {f:'#ECEBE6',s:'#888780',t:'#4A4944'},
  deliverable: dark ? {f:'#085041',s:'#5DCAA5',t:'#E1F5EE'} : {f:'#E1F5EE',s:'#0F6E56',t:'#085041'},
  note:        dark ? {f:'#712B13',s:'#F0997B',t:'#FAECE7'} : {f:'#FAECE7',s:'#993C1D',t:'#712B13'}
};
const edgeCol = '#888780';
const info = document.getElementById('info');
function esc(s){ return (s||'').replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

const isc = k => [{selector:'node[status="'+k+'"]', style:{'background-color':IC[k].f,'border-color':IC[k].s,'color':IC[k].t}}];
const cyIssues = cytoscape({
  container: document.getElementById('cy-issues'),
  elements: ISSUE_ELEMENTS,
  style: [
    {selector:'node[status]', style:{'shape':'round-rectangle','width':'140px','height':'label','padding':'10px','border-width':1.5,'label':'data(label)','text-valign':'center','text-halign':'center','text-wrap':'wrap','text-max-width':'124px','font-size':'11px','font-weight':500,'transition-property':'border-width, opacity, background-color','transition-duration':'160ms'}},
    {selector:':parent', style:{'shape':'round-rectangle','background-opacity':0.05,'background-color':'#888780','border-width':1,'border-style':'dashed','border-color':'#aaa','label':'data(label)','text-valign':'top','text-halign':'center','font-size':'13px','font-weight':600,'color':'#999','text-margin-y':-2,'padding':'16px'}},
    ...isc('done'), ...isc('active'), ...isc('backlog'), ...isc('superseded'),
    {selector:'node.hover', style:{'border-width':3}},
    {selector:'node.grabbed', style:{'border-width':4,'opacity':0.9}},
    {selector:'node.dropped', style:{'border-width':6}},
    {selector:'node.current', style:{'border-width':5,'border-color':'#E8590C'}},
    {selector:'node:selected', style:{'border-width':4}},
    {selector:'edge', style:{'width':1.8,'line-color':edgeCol,'target-arrow-color':edgeCol,'target-arrow-shape':'triangle','curve-style':'bezier','opacity':0.8,'label':'data(rel)','font-size':'10px','color':edgeCol,'text-rotation':'autorotate','text-margin-y':-8}},
    {selector:'edge[rel="related"]', style:{'line-style':'dashed','line-color':'#bbb','width':1,'opacity':0.4,'target-arrow-shape':'none','label':'','curve-style':'haystack'}}
  ],
  layout: {name:'preset', padding:30, fit:true},
  wheelSensitivity: 0.2, minZoom: 0.2, maxZoom: 2.5
});
const ksc = k => [{selector:'node[kind="'+k+'"]', style:{'background-color':MC[k].f,'border-color':MC[k].s,'color':MC[k].t}}];
const cyMemory = cytoscape({
  container: document.getElementById('cy-memory'),
  elements: MEMORY_ELEMENTS,
  style: [
    {selector:'node', style:{'shape':'round-rectangle','width':'150px','height':'46px','border-width':1.5,'label':'data(label)','text-valign':'center','text-halign':'center','text-wrap':'wrap','text-max-width':'134px','font-size':'12px','font-weight':500,'transition-property':'border-width, opacity, background-color','transition-duration':'160ms'}},
    ...ksc('decision'), ...ksc('evidence'), ...ksc('deliverable'), ...ksc('note'),
    {selector:'node.hover', style:{'border-width':3}},
    {selector:'node.grabbed', style:{'border-width':4,'opacity':0.9}},
    {selector:'node.dropped', style:{'border-width':6}},
    {selector:'node:selected', style:{'border-width':4}},
    {selector:'edge', style:{'width':1.8,'line-color':edgeCol,'target-arrow-color':edgeCol,'target-arrow-shape':'triangle','curve-style':'bezier','opacity':0.75,'label':'data(rel)','font-size':'10px','color':edgeCol,'text-rotation':'autorotate','text-margin-y':-8}},
    {selector:'edge[rel="references"]', style:{'line-style':'dashed'}},
    {selector:'edge[rel="depends_on"]', style:{'line-style':'dashed'}}
  ],
  layout: {name:'cose', animate:false, padding:40, nodeRepulsion:18000, idealEdgeLength:130, nodeOverlap:40, componentSpacing:170, numIter:2000, randomize:true},
  wheelSensitivity: 0.2, minZoom: 0.3, maxZoom: 2.5
});

function applyBadge(on){
  cyIssues.nodes('[status]').forEach(n=>{
    const c = n.data('memcount') || 0;
    n.data('label', (on && c>0) ? n.data('labelbase')+'  \\u{1F9E0}'+c : n.data('labelbase'));
  });
}
document.getElementById('badge-toggle').addEventListener('change', e=> applyBadge(e.target.checked));
applyBadge(true);
document.getElementById('rel-toggle').addEventListener('change', e=>{
  cyIssues.edges('[rel="related"]').style('display', e.target.checked ? 'element' : 'none');
});
// Highlight the currently-active issue so it stands out at a glance.
const activeNodes = cyIssues.nodes('[status="active"]');
activeNodes.addClass('current');

cyIssues.on('tap','node', evt=>{
  const d = evt.target.data();
  let html = '<b>'+esc(d.title)+'</b> &nbsp; <a href="'+d.href+'">상세 열기 \\u2192</a><br><span style="color:#888">상태: '+esc(d.status)+'</span>';
  const mem = d.memory || [];
  if(mem.length){
    html += '<br><span style="color:#888">\\u2014 연결된 지식 ('+mem.length+') \\u2014</span>';
    mem.forEach(m=>{
      const icon = KIND_ICON[m.kind] || '\\u{1F4DD}';
      html += '<span class="mem">'+icon+' <a onclick="gotoMemory(\\''+m.id+'\\')">'+esc(m.title)+'</a></span>';
    });
  } else {
    html += '<br><span style="color:#aaa">연결된 지식 없음 (memory issue_id 미설정 \\u2014 043에서 보강)</span>';
  }
  info.innerHTML = html;
});
cyMemory.on('tap','node', evt=>{
  const d = evt.target.data();
  let html = '<b>'+esc(d.full)+'</b> &nbsp; <a href="'+d.panelhref+'">상세 열기 \\u2192</a>'
           + '<br><a href="'+d.href+'"><code>'+esc(d.file)+'</code></a>';
  if(d.issue){ html += '<br><span class="mem">\\u2196 출처 이슈: <a onclick="gotoIssue(\\''+d.issue+'\\')">'+esc(d.issue)+'</a></span>'; }
  info.innerHTML = html;
});

// Light motion: smooth border/opacity transitions on hover + grab (no physics).
function wireMotion(cy){
  cy.on('mouseover','node', e=> e.target.addClass('hover'));
  cy.on('mouseout','node', e=> e.target.removeClass('hover'));
  cy.on('grab','node', e=> e.target.addClass('grabbed'));
  cy.on('free','node', e=>{
    const n = e.target;
    n.removeClass('grabbed');
    n.stop(true).animate({style:{'border-width':6}}, {duration:100, easing:'ease-out',
      complete:()=> n.animate({style:{'border-width':1.5}}, {duration:280, easing:'ease-in-out',
        complete:()=> n.removeStyle('border-width')})});  // pop on drop, then ease back
  });
}
wireMotion(cyIssues); wireMotion(cyMemory);

const FLAG_LABELS = {
  missing_spec:'spec 없음', missing_plan:'plan 없음', no_next:'다음 없음',
  no_review:'review 없음', no_pr:'PR 없음', no_ko:'한글 없음', blocked:'막힘'
};
const STATUS_VIEW = {
  all: row => true,
  active: row => row.status === 'active',
  review: row => row.status === 'review' || row.attention_flags.includes('no_review') || row.attention_flags.includes('no_pr'),
  blocked: row => row.status === 'blocked' || row.attention_flags.includes('blocked'),
  missing: row => row.attention_flags.length > 0,
  done: row => row.status === 'done'
};
let issueDbState = {view:'all', q:'', sort:'number', group:'status'};

function artifactBadges(row){
  const c = row.artifact_coverage || {};
  const pairs = [['I','issue'],['S','spec'],['KO','spec_ko'],['P','plan'],['T','tasks'],['R','review'],['PR','pr'],['Rel','release']];
  return pairs.map(([label,key]) => '<span class="badge '+(c[key]?'':'missing')+'">'+(c[key]?label:'-')+'</span>').join('');
}
function flagBadges(row){
  const flags = row.attention_flags || [];
  if(!flags.length) return '<span style="color:#aaa">-</span>';
  return flags.map(f => '<span class="flag">'+esc(FLAG_LABELS[f] || f)+'</span>').join('');
}
function compareRows(a,b){
  const s = issueDbState.sort;
  if(s === 'status') return (a.status||'').localeCompare(b.status||'') || ((a.number||0)-(b.number||0));
  if(s === 'memory') return (b.linked_memory_count||0) - (a.linked_memory_count||0) || ((a.number||0)-(b.number||0));
  if(s === 'updated') return (b.updated||'').localeCompare(a.updated||'') || ((a.number||0)-(b.number||0));
  return ((a.number||999999)-(b.number||999999)) || (a.id||'').localeCompare(b.id||'');
}
function filteredRows(){
  const q = issueDbState.q.toLowerCase();
  return ISSUE_ROWS.filter(row => {
    const text = [row.id, row.title, row.next_command, row.goal].join(' ').toLowerCase();
    return (!q || text.includes(q)) && (STATUS_VIEW[issueDbState.view] || STATUS_VIEW.all)(row);
  }).sort(compareRows);
}
function groupedRows(rows){
  if(issueDbState.group === 'none') return [{label:'', rows}];
  const key = issueDbState.group === 'goal' ? 'goal' : 'status';
  const groups = [];
  const by = {};
  rows.forEach(row => {
    const label = row[key] || '(없음)';
    if(!by[label]){ by[label] = {label, rows: []}; groups.push(by[label]); }
    by[label].rows.push(row);
  });
  return groups;
}
function renderIssueTable(focusSearch=false){
  const rows = filteredRows();
  const body = rows.length ? groupedRows(rows).map(group => (
    (group.label ? `<tr><th colspan="8">${esc(group.label)} · ${group.rows.length}</th></tr>` : '') +
    group.rows.map(row => `
    <tr class="issue-row" onclick="location.href='${esc(row.href)}'">
      <td class="mono">${esc(String(row.number || ''))}</td>
      <td><a href="${esc(row.href)}">${esc(row.title || row.id)}</a><br><code>${esc(row.id)}</code></td>
      <td>${esc(row.status || '')}</td>
      <td>${esc(row.phase || '')}</td>
      <td><code>${esc(row.next_command || '')}</code></td>
      <td>${artifactBadges(row)}</td>
      <td>${flagBadges(row)}</td>
      <td class="mono">${esc(String(row.linked_memory_count || 0))}</td>
    </tr>`).join('')
  )).join('') : '<tr><td class="empty" colspan="8">검색 결과 없음</td></tr>';
  document.getElementById('issue-db').innerHTML = `
    <div class="dbbar">
      <input id="issue-search" placeholder="Search issue id, title, next command" value="${esc(issueDbState.q)}">
      <div class="chips">
        <button class="chip" data-view="all">전체</button>
        <button class="chip" data-view="active">진행중</button>
        <button class="chip" data-view="review">리뷰필요</button>
        <button class="chip" data-view="blocked">막힘</button>
        <button class="chip" data-view="missing">누락있음</button>
        <button class="chip" data-view="done">완료</button>
      </div>
      <select id="issue-sort">
        <option value="number">이슈 번호</option>
        <option value="updated">최근 업데이트</option>
        <option value="status">상태</option>
        <option value="memory">메모리 수</option>
      </select>
      <select id="issue-group">
        <option value="status">상태별</option>
        <option value="goal">Goal별</option>
        <option value="none">없음</option>
      </select>
    </div>
    <table>
      <thead><tr><th>ID</th><th>Issue</th><th>Status</th><th>Phase</th><th>Next</th><th>Artifacts</th><th>Flags</th><th>Memory</th></tr></thead>
      <tbody>${body}</tbody>
    </table>`;
  document.getElementById('issue-search').addEventListener('input', e=>{ issueDbState.q = e.target.value; renderIssueTable(true); });
  document.querySelectorAll('[data-view]').forEach(btn=>{
    btn.classList.toggle('on', btn.dataset.view === issueDbState.view);
    btn.addEventListener('click', ()=>{ issueDbState.view = btn.dataset.view; renderIssueTable(); });
  });
  document.getElementById('issue-sort').value = issueDbState.sort;
  document.getElementById('issue-sort').addEventListener('change', e=>{ issueDbState.sort = e.target.value; renderIssueTable(); });
  document.getElementById('issue-group').value = issueDbState.group;
  document.getElementById('issue-group').addEventListener('change', e=>{ issueDbState.group = e.target.value; renderIssueTable(); });
  if(focusSearch){
    const search = document.getElementById('issue-search');
    search.focus();
    search.setSelectionRange(search.value.length, search.value.length);
  }
}
renderIssueTable();

function showTab(which){
  const db = which==='issue-db';
  const issues = which==='issues';
  const memory = which==='memory';
  document.getElementById('issue-db').classList.toggle('hidden', !db);
  document.getElementById('cy-issues').classList.toggle('hidden', !issues);
  document.getElementById('cy-memory').classList.toggle('hidden', !memory);
  document.getElementById('legend-issues').classList.toggle('hidden', !issues);
  document.getElementById('legend-memory').classList.toggle('hidden', !memory);
  document.getElementById('tab-db').classList.toggle('on', db);
  document.getElementById('tab-issues').classList.toggle('on', issues);
  document.getElementById('tab-memory').classList.toggle('on', memory);
  document.getElementById('rel-toggle').closest('label').classList.toggle('hidden', !issues);
  document.getElementById('badge-toggle').closest('label').classList.toggle('hidden', !issues);
  if(db){
    if(location.hash !== '#issue-db') location.hash = 'issue-db';
    return;
  }
  const cy = issues ? cyIssues : cyMemory;
  cy.resize();
  if(issues && activeNodes.nonempty()){
    cyIssues.fit(undefined, 40);
    cyIssues.animate({center:{eles: activeNodes}, zoom: 1.15}, {duration: 650});
  } else {
    cy.fit(undefined, 40);
  }
  if(location.hash !== (issues?'#issues':'#memory')) location.hash = issues?'issues':'memory';
}
document.getElementById('tab-db').addEventListener('click', ()=>showTab('issue-db'));
document.getElementById('tab-issues').addEventListener('click', ()=>showTab('issues'));
document.getElementById('tab-memory').addEventListener('click', ()=>showTab('memory'));
function gotoMemory(id){ showTab('memory'); const n=cyMemory.getElementById(id); if(n){ cyMemory.elements().unselect(); n.select(); cyMemory.center(n);} }
function gotoIssue(id){ showTab('issues'); const n=cyIssues.getElementById(id); if(n){ cyIssues.elements().unselect(); n.select(); cyIssues.center(n);} }
window.gotoMemory = gotoMemory; window.gotoIssue = gotoIssue;

showTab(location.hash === '#memory' ? 'memory' : (location.hash === '#issues' ? 'issues' : 'issue-db'));
</script>
</body>
</html>
"""


def render_project_view(root):
    issue_elements, _i_n, _i_e = _issue_elements(root)
    memory_elements, _m_n, _m_e = _memory_elements(root)
    issue_rows = _collect_issue_table(root)
    return (
        PROJECT_VIEW_TEMPLATE
        .replace("__ISSUE_ROWS__", json.dumps(issue_rows, ensure_ascii=False, indent=2))
        .replace("__ISSUE_ELEMENTS__", json.dumps(issue_elements, ensure_ascii=False, indent=2))
        .replace("__MEMORY_ELEMENTS__", json.dumps(memory_elements, ensure_ascii=False, indent=2))
    )


# --- Issue artifact drill-down panel (047) ---------------------------------
# Render path note: unlike the 042 dashboard (classic <script src> Cytoscape),
# this panel loads `marked` (classic) for Markdown and `mermaid` (ESM import)
# for diagrams. Both are pinned CDN libs; Python only collects + assembles.
# Decision rationale: see specs/047-issue-artifact-drilldown/plan.md (reverses
# spec Alternatives #4 because Goal #4 needs Mermaid rendered inside the panel).

SPEC_ARTIFACT_ORDER = ["spec.md", "plan.md", "tasks.md", "status.md"]
ARTIFACT_LABELS = {
    "issue": "Issue",
    "spec.md": "Spec",
    "plan.md": "Plan",
    "tasks.md": "Tasks",
    "status.md": "Status",
}

ISSUE_PANEL_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ModuFlow · __ISSUE_ID__</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0 auto; max-width: 820px; padding: 24px; background: #fff; color: #1a1a1a; line-height: 1.6; }
  h1 { font-size: 20px; font-weight: 500; margin: 0 0 4px; }
  .sub { font-size: 13px; color: #888; margin: 0 0 20px; }
  .artifact { border: 1px solid #ddd; border-radius: 12px; padding: 8px 20px 16px; margin-bottom: 18px; }
  .artifact > h2.label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: #888; margin: 12px 0 4px; }
  .md h1 { font-size: 19px; } .md h2 { font-size: 16px; } .md h3 { font-size: 14px; }
  .md code { font-size: 13px; background: rgba(135,131,120,0.15); padding: 1px 5px; border-radius: 4px; }
  .md pre { background: rgba(135,131,120,0.12); padding: 12px 14px; border-radius: 8px; overflow-x: auto; }
  .md pre code { background: none; padding: 0; }
  .md a { color: #2a78d6; }
  .md table { border-collapse: collapse; font-size: 14px; } .md th, .md td { border: 1px solid #ddd; padding: 6px 10px; }
  .mermaid { text-align: center; margin: 12px 0; }
  .empty { border: 1px dashed #ccc; border-radius: 12px; padding: 24px; color: #888; text-align: center; }
  @media (prefers-color-scheme: dark) {
    body { background: #1a1a19; color: #e8e8e3; }
    .artifact, .empty { border-color: #333; }
    .md a { color: #5aa0e8; }
    .md th, .md td { border-color: #333; }
  }
</style>
</head>
<body>
<h1>__PANEL_TITLE__</h1>
<p class="sub">__PANEL_SUB__</p>
<div id="langtoggle" style="margin-bottom:14px;"></div>
<div id="artifacts"></div>
<div id="linked"></div>
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";
const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
mermaid.initialize({ startOnLoad: false, theme: dark ? 'dark' : 'default', securityLevel: 'loose' });
const ARTIFACTS = __ARTIFACTS_JSON__;
const LINKED = __LINKED_JSON__;
const KIND_ICON = {decision:'\\u{1F4A1}', evidence:'\\u{1F4CE}', deliverable:'\\u{1F4E6}', release:'\\u{1F680}', meeting:'\\u{1F5E3}', note:'\\u{1F4DD}', reference:'\\u{1F517}'};
const root = document.getElementById('artifacts');
const hasKo = ARTIFACTS.some(a => a.ko);
let lang = 'en';  // English is canonical; Korean is a reading aid (049)

async function renderArtifacts() {
  root.innerHTML = '';
  if (!ARTIFACTS.length) {
    root.innerHTML = '<div class="empty">No artifacts yet for <code>__ISSUE_ID__</code>. Nothing has been written under <code>specs/__ISSUE_ID__/</code> or <code>issues/</code>.</div>';
    return;
  }
  for (const a of ARTIFACTS) {
    if (lang === 'ko' && !a.ko) continue;  // 한글 모드: 한글본 있는 산출물만 (영문 안 섞음)
    const sec = document.createElement('section');
    sec.className = 'artifact';
    const h = document.createElement('h2');
    h.className = 'label';
    h.textContent = a.label;
    sec.appendChild(h);
    const body = document.createElement('div');
    body.className = 'md';
    body.innerHTML = marked.parse(lang === 'ko' ? a.ko : a.md);  // EN: all artifacts; KO: only ones with a sidecar
    sec.appendChild(body);
    root.appendChild(sec);
  }
  root.querySelectorAll('code.language-mermaid').forEach(code => {
    const div = document.createElement('div');
    div.className = 'mermaid';
    div.textContent = code.textContent;
    const pre = code.closest('pre');
    (pre || code).replaceWith(div);
  });
  await mermaid.run({ querySelector: '.mermaid' });
}

if (hasKo) {
  const wrap = document.getElementById('langtoggle');
  const mk = (id, text) => { const b = document.createElement('button'); b.id = id; b.textContent = text;
    b.style.cssText = 'padding:5px 14px;margin-right:6px;border:1px solid #ccc;border-radius:8px;cursor:pointer;font-size:13px;'; return b; };
  const en = mk('lang-en', 'English'), ko = mk('lang-ko', '한글');
  const paint = () => {
    en.style.background = lang === 'en' ? '#2a78d6' : 'transparent'; en.style.color = lang === 'en' ? '#fff' : 'inherit';
    ko.style.background = lang === 'ko' ? '#2a78d6' : 'transparent'; ko.style.color = lang === 'ko' ? '#fff' : 'inherit';
  };
  en.onclick = async () => { lang = 'en'; paint(); await renderArtifacts(); };
  ko.onclick = async () => { lang = 'ko'; paint(); await renderArtifacts(); };
  wrap.appendChild(en); wrap.appendChild(ko); paint();
}
await renderArtifacts();
if (LINKED.length) {
  const sec = document.createElement('section');
  sec.className = 'artifact';
  const h = document.createElement('h2');
  h.className = 'label';
  h.textContent = '연결된 지식 (' + LINKED.length + ')';
  sec.appendChild(h);
  const ul = document.createElement('div');
  ul.className = 'md';
  ul.innerHTML = LINKED.map(m =>
    '<p>' + (KIND_ICON[m.kind] || '\\u{1F4DD}') + ' <a href="' + m.file.replace(/^memory\\//,'') + '">' +
    m.title.replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])) + '</a> <code>' + m.kind + '</code></p>'
  ).join('');
  sec.appendChild(ul);
  document.getElementById('linked').appendChild(sec);
}
</script>
</body>
</html>
"""


def _resolve_issue_slug(root, issue_id):
    root = Path(root).resolve()
    issue_id = issue_id.strip()
    if (root / "specs" / issue_id).is_dir():
        return issue_id
    if (root / "issues" / f"{issue_id}.md").is_file():
        return issue_id
    num = issue_id.split("-")[0]
    specs_dir = root / "specs"
    if specs_dir.is_dir():
        for d in sorted(specs_dir.iterdir()):
            if d.is_dir() and (d.name == num or d.name.startswith(num + "-")):
                return d.name
    issues_dir = root / "issues"
    if issues_dir.is_dir():
        for f in sorted(issues_dir.glob("*.md")):
            if f.stem == num or f.stem.startswith(num + "-"):
                return f.stem
    return issue_id


def _ko_sidecar(path):
    """Korean reading sidecar `<name>.ko.md` next to `<name>.md` (049). None if absent."""
    if not path.name.endswith(".md"):
        return None
    ko = path.parent / (path.name[:-3] + ".ko.md")
    return ko.read_text(encoding="utf-8") if ko.is_file() else None


def _collect_issue_artifacts(root, issue_id):
    root = Path(root).resolve()
    slug = _resolve_issue_slug(root, issue_id)
    artifacts = []
    issue_file = root / "issues" / f"{slug}.md"
    if issue_file.is_file():
        artifacts.append({"name": "issue", "label": "Issue",
                          "md": issue_file.read_text(encoding="utf-8"), "ko": _ko_sidecar(issue_file)})
    spec_dir = root / "specs" / slug
    if spec_dir.is_dir():
        seen = set()
        for fname in SPEC_ARTIFACT_ORDER:
            f = spec_dir / fname
            if f.is_file():
                seen.add(fname)
                artifacts.append({"name": fname, "label": ARTIFACT_LABELS.get(fname, fname),
                                  "md": f.read_text(encoding="utf-8"), "ko": _ko_sidecar(f)})
        for f in sorted(spec_dir.glob("*.md")):
            if f.name in seen or f.name.endswith(".ko.md"):  # .ko.md is a sidecar, not its own artifact
                continue
            artifacts.append({"name": f.name, "label": f.stem.replace("-", " ").title(),
                              "md": f.read_text(encoding="utf-8"), "ko": _ko_sidecar(f)})
    return slug, artifacts


def render_issue_panel(root, issue_id):
    slug, artifacts = _collect_issue_artifacts(root, issue_id)
    linked = _issue_linked_memory(root).get(slug, [])
    # Escape "</" so a literal </script> inside Markdown can't end the module script.
    artifacts_json = json.dumps(artifacts, ensure_ascii=False).replace("</", "<\\/")
    linked_json = json.dumps(linked, ensure_ascii=False).replace("</", "<\\/")
    return (
        ISSUE_PANEL_TEMPLATE
        .replace("__PANEL_TITLE__", f"Issue {slug}")
        .replace("__PANEL_SUB__", f"{len(artifacts)} artifact(s) · issues/ + specs/{slug}/ · derived view")
        .replace("__ISSUE_ID__", slug)
        .replace("__ARTIFACTS_JSON__", artifacts_json)
        .replace("__LINKED_JSON__", linked_json)
    )


def render_memory_panel(root, mem_id):
    entry = get_memory_entry(root, mem_id)
    if not entry:
        title, sub, artifacts = mem_id, "no such memory entry", []
    else:
        kind = entry.get("kind", "memory")
        meta = entry.get("metadata", {})
        date = meta.get("date", "") or meta.get("created", "")
        label = kind + ((" · " + date) if date else "")
        artifacts = [{"name": "memory", "label": label, "md": entry["content"]}]
        title = entry.get("title") or mem_id
        sub = f"{kind} · {entry['path']} · derived view"
    artifacts_json = json.dumps(artifacts, ensure_ascii=False).replace("</", "<\\/")
    return (
        ISSUE_PANEL_TEMPLATE
        .replace("__PANEL_TITLE__", title)
        .replace("__PANEL_SUB__", sub)
        .replace("__ISSUE_ID__", mem_id)
        .replace("__ARTIFACTS_JSON__", artifacts_json)
        .replace("__LINKED_JSON__", "[]")
    )


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
    parser.add_argument("--dashboard", action="store_true", help="Generate an interactive Cytoscape dashboard HTML at memory/dashboard.html.")
    parser.add_argument("--issue", default="", help="Generate a single-issue artifact drill-down panel at memory/issue-<id>.html.")
    parser.add_argument("--summary", default="")
    parser.add_argument("--rationale", default="")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--alternatives", default="")
    parser.add_argument("--owner", default="")
    parser.add_argument("--reversal-conditions", default="")
    parser.add_argument("--tags", default="", help="Comma-separated tags.")
    parser.add_argument("--search", default="", help="Search project memory entries.")
    parser.add_argument("--list-ids", action="store_true", help="List existing memory ids/kinds/titles as relationship link candidates.")
    parser.add_argument("--get", default="", help="Get one memory entry by id.")
    parser.add_argument("--export-guidance", default="", help="Return mirror/export guidance for a target.")
    args = parser.parse_args()

    if args.graph:
        print(generate_memory_graph(args.project_path))
        return 0

    if args.dashboard:
        out_dir = Path(args.project_path).resolve() / "memory"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "dashboard.html"
        out_path.write_text(render_project_view(args.project_path), encoding="utf-8")
        # Zero-backend: pre-generate each issue's + memory entry's panel so the
        # graph's "상세 열기" links resolve without a server.
        issue_nodes, _ = _collect_issue_graph(args.project_path)
        for iid in issue_nodes:
            (out_dir / f"issue-{iid}.html").write_text(
                render_issue_panel(args.project_path, iid), encoding="utf-8")
        mem_nodes, _ = _collect_graph(args.project_path)
        for mid in mem_nodes:
            (out_dir / f"mem-{mid}.html").write_text(
                render_memory_panel(args.project_path, mid), encoding="utf-8")
        print(str(out_path))
        print(f"  + {len(issue_nodes)} issue panel(s), {len(mem_nodes)} memory panel(s)")
        return 0

    if args.list_ids:
        print(json.dumps(list_memory_ids(args.project_path, kind=args.kind or ""),
                         ensure_ascii=False, indent=2))
        return 0

    if args.issue:
        slug = _resolve_issue_slug(args.project_path, args.issue)
        html = render_issue_panel(args.project_path, args.issue)
        out_dir = Path(args.project_path).resolve() / "memory"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"issue-{slug}.html"
        out_path.write_text(html, encoding="utf-8")
        print(str(out_path))
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
