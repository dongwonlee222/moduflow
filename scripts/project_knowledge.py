#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path


KNOWLEDGE_DIRS = [
    "knowledge/decisions",
    "knowledge/benchmarks",
    "knowledge/reports",
    "knowledge/research",
    "knowledge/data-notes",
    "knowledge/references",
]

KIND_TO_DIR = {
    "decision": "knowledge/decisions",
    "benchmark": "knowledge/benchmarks",
    "report": "knowledge/reports",
    "research": "knowledge/research",
    "data-note": "knowledge/data-notes",
    "reference": "knowledge/references",
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


def build_knowledge_plan(path, dry_run=True):
    project_root = Path(path).resolve()
    writes = []
    for relative in ["knowledge/index.md", *KNOWLEDGE_DIRS]:
        if not (project_root / relative).exists():
            writes.append(relative)
    return {
        "schema": "moduflow.knowledge-plan.v1",
        "project_root": str(project_root),
        "dry_run": dry_run,
        "writes": writes,
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


def apply_knowledge_plan(plan):
    project_root = Path(plan["project_root"])
    written = []
    for relative in KNOWLEDGE_DIRS:
        if mkdir_if_missing(project_root / relative):
            written.append(relative)
    if write_text_if_missing(project_root / "knowledge" / "index.md", INDEX_CONTENT):
        written.append("knowledge/index.md")
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


def create_knowledge_artifact(path, kind, title, issue_id="", spec_path="", decision_supported=""):
    if kind not in KIND_TO_DIR:
        raise ValueError(f"Unsupported knowledge kind: {kind}")
    project_root = Path(path).resolve()
    target_dir = project_root / KIND_TO_DIR[kind]
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
