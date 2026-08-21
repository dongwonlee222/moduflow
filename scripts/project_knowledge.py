#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path

try:
    from scripts import project_operation, project_registry
except ImportError:  # pragma: no cover - direct script execution fallback
    import project_operation
    import project_registry


KNOWLEDGE_DIRS = [
    "decisions",
    "benchmarks",
    "reports",
    "research",
    "data-notes",
    "references",
]

KIND_TO_DIR = {
    "decision": "decisions",
    "benchmark": "benchmarks",
    "report": "reports",
    "research": "research",
    "data-note": "data-notes",
    "reference": "references",
}

INDEX_CONTENT = """# Knowledge Index

## Decisions

## Benchmarks

## Reports

## Research

## Data Notes

## References
"""


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def build_knowledge_plan(path, dry_run=True, *, project_context=None):
    project_root = Path(path).resolve()
    context = project_registry.context_for_operation(
        project_root,
        project_context=project_context,
    )
    knowledge_root = project_registry.canonical_path(context, "knowledge")
    writes = []
    for relative in ["index.md", *KNOWLEDGE_DIRS]:
        target = project_registry.canonical_child_path(context, "knowledge", relative)
        if not target.exists():
            writes.append(project_registry.canonical_relative_path(context, "knowledge", relative))
    return {
        "schema": "moduflow.knowledge-plan.v1",
        "project_root": str(project_root),
        "dry_run": dry_run,
        "writes": writes,
        "knowledge_root": str(knowledge_root),
        "preserves_existing_files": True,
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


def apply_knowledge_plan(plan, *, project_context=None):
    project_root = Path(plan["project_root"]).resolve()
    context = project_registry.context_for_operation(
        project_root,
        project_context=project_context,
    )
    project_operation.require_project_capability(context, "write")
    knowledge_root = Path(plan["knowledge_root"])
    written = []
    for relative in KNOWLEDGE_DIRS:
        target = knowledge_root / relative
        if mkdir_if_missing(target):
            written.append(target.relative_to(project_root).as_posix())
    index = knowledge_root / "index.md"
    if write_text_if_missing(index, INDEX_CONTENT):
        written.append(index.relative_to(project_root).as_posix())
    plan["written"] = written
    return plan


def artifact_body(kind, title, issue_id="", spec_path="", decision_supported=""):
    today = date.today().isoformat()
    return f"""---
kind: {kind}
title: {title}
issue_id: {issue_id}
spec: {spec_path}
decision_supported: {decision_supported}
date: {today}
confidence: medium
---

# {title}

## Summary

Capture the key evidence and why it matters.

## Evidence

- Source:
- Observation:
- Caveat:

## Decision Link

- Issue: {issue_id}
- Spec: {spec_path}
- Decision supported: {decision_supported}

## Next Action

- Review this artifact during `product:evidence`.
"""


def create_knowledge_artifact(
    path,
    kind,
    title,
    issue_id="",
    spec_path="",
    decision_supported="",
    *,
    project_context=None,
):
    if kind not in KIND_TO_DIR:
        raise ValueError(f"Unsupported knowledge kind: {kind}")
    project_root = Path(path).resolve()
    context = project_registry.context_for_operation(
        project_root,
        project_context=project_context,
    )
    project_operation.require_project_capability(context, "write")
    target_dir = project_registry.canonical_child_path(
        context,
        "knowledge",
        KIND_TO_DIR[kind],
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{date.today().isoformat()}-{slugify(title)}.md"
    target = target_dir / filename
    if target.exists():
        raise FileExistsError(str(target))
    target.write_text(
        artifact_body(kind, title, issue_id=issue_id, spec_path=spec_path, decision_supported=decision_supported),
        encoding="utf-8",
    )
    return {
        "kind": kind,
        "path": str(target.relative_to(project_root)),
        "preserves_existing_files": True,
    }


@project_operation.cli_denial_boundary
def main():
    parser = argparse.ArgumentParser(description="Plan, initialize, or create ModuFlow knowledge artifacts.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="Create missing knowledge folders and index.")
    parser.add_argument("--kind", choices=sorted(KIND_TO_DIR), help="Create a single knowledge artifact.")
    parser.add_argument("--title", default="", help="Title for a single knowledge artifact.")
    parser.add_argument("--issue-id", default="")
    parser.add_argument("--spec", default="")
    parser.add_argument("--decision-supported", default="")
    args = parser.parse_args()

    if args.kind:
        if not args.title:
            parser.error("--title is required when --kind is used")
        result = create_knowledge_artifact(
            args.project_path,
            args.kind,
            args.title,
            issue_id=args.issue_id,
            spec_path=args.spec,
            decision_supported=args.decision_supported,
        )
    else:
        result = build_knowledge_plan(args.project_path, dry_run=not args.write)
        if args.write:
            result = apply_knowledge_plan(result)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
