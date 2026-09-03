#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path

try:
    from scripts import project_artifact_registry, project_operation, project_registry
except ImportError:  # pragma: no cover - direct script execution fallback
    import project_artifact_registry
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

WORKSPACE_FILES = ("knowledge.md", "artifacts.md")


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
    for name in WORKSPACE_FILES:
        target = project_registry.canonical_child_path(context, "workspace", name)
        if not target.exists():
            writes.append(project_registry.canonical_relative_path(context, "workspace", name))
    return {
        "schema": "moduflow.knowledge-plan.v1",
        "project_root": str(project_root),
        "dry_run": dry_run,
        "writes": writes,
        "knowledge_root": str(knowledge_root),
        "project_context": json.loads(json.dumps(context)),
        "preserves_existing_files": True,
    }


def write_text_if_missing(path, content):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as output:
            output.write(content)
    except FileExistsError:
        return False
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
        project_context=project_context if project_context is not None else plan.get("project_context"),
    )
    project_operation.require_project_capability(context, "write")
    written = []
    preserved = []
    directories = [project_registry.canonical_child_path(context, "knowledge", name) for name in KNOWLEDGE_DIRS]
    files = [(project_registry.canonical_child_path(context, "knowledge", "index.md"), INDEX_CONTENT)]
    template_root = Path(__file__).resolve().parent.parent / "templates" / "workspace"
    files.extend((project_registry.canonical_child_path(context, "workspace", name),
                  (template_root / name).read_text(encoding="utf-8")) for name in WORKSPACE_FILES)
    plan.update(written=written, preserved=preserved, status="complete")
    try:
        for target in directories:
            (written if mkdir_if_missing(target) else preserved).append(target.relative_to(project_root).as_posix())
        for target, content in files:
            (written if write_text_if_missing(target, content) else preserved).append(target.relative_to(project_root).as_posix())
    except OSError:
        plan.update(status="partial", error_code="KNOWLEDGE_INITIALIZATION_FAILED",
                    failed_path=target.relative_to(project_root).as_posix())
    return plan


def artifact_body(kind, title, issue_id="", spec_path="", decision_supported="", *, created_on=None):
    today = created_on or date.today().isoformat()
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
    registry_entry=None,
):
    if kind not in KIND_TO_DIR:
        raise ValueError(f"Unsupported knowledge kind: {kind}")
    project_root = Path(path).resolve()
    context = project_registry.context_for_operation(
        project_root,
        project_context=project_context,
    )
    project_operation.require_project_capability(context, "write")
    if registry_entry is not None:
        plan = project_artifact_registry.plan_artifact_registration(
            project_root, registry_entry, issue_id=issue_id, project_context=context,
            new_knowledge={"kind": kind, "title": title, "spec_path": spec_path,
                           "decision_supported": decision_supported},
        )
        result = project_artifact_registry.apply_artifact_registration(project_root, plan, project_context=context)
        return {**result, "kind": kind, "path": plan._artifact_change["entry"]["local_path"],
                "preserves_existing_files": True}
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
        "registered": False,
    }


@project_operation.cli_denial_boundary
def main():
    parser = argparse.ArgumentParser(description="Plan, initialize, or create ModuFlow knowledge artifacts.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="Initialize missing files or apply an explicit registration.")
    parser.add_argument("--kind", choices=sorted(KIND_TO_DIR), help="Create a single knowledge artifact.")
    parser.add_argument("--title", default="", help="Title for a single knowledge artifact.")
    parser.add_argument("--issue-id", default="")
    parser.add_argument("--spec", default="")
    parser.add_argument("--decision-supported", default="")
    parser.add_argument("--inspect", action="store_true", help="Read the short knowledge home and registry metadata.")
    parser.add_argument("--query", default="", help="Filter registry metadata only.")
    parser.add_argument("--artifact-id", action="append", default=[], help="Select an exact stable artifact ID.")
    parser.add_argument("--shared-ref", help="Read one committed snapshot, without working-tree fallback.")
    parser.add_argument("--register", metavar="ENTRY_JSON", help="Preview a registration from a JSON metadata file.")
    parser.add_argument("--amend", action="store_true", help="Explicitly amend an existing registry record.")
    parser.add_argument("--read-sources", action="store_true", help="Read only sources selected with --artifact-id.")
    args = parser.parse_args()

    read_requested = bool(args.inspect or args.query or args.artifact_id or args.shared_ref or args.read_sources)
    if read_requested and (args.write or args.register or args.kind or args.amend):
        parser.error("Registry reads cannot be combined with creation or registration.")
    if args.read_sources and not args.artifact_id:
        parser.error("--read-sources requires explicit --artifact-id selections")
    if args.amend and not args.register:
        parser.error("--amend requires --register")
    if args.kind and not args.title:
        parser.error("--title is required when --kind is used")
    if args.register and not args.issue_id:
        parser.error("--register requires an existing --issue-id; initialize project prerequisites first")

    if read_requested or args.register:
        context = project_registry.context_for_operation(args.project_path)
        try:
            if args.register:
                entry = json.loads(Path(args.register).read_text(encoding="utf-8"),
                                   object_pairs_hook=project_artifact_registry._unique_object)
                new = None if not args.kind else {"kind": args.kind, "title": args.title,
                    "spec_path": args.spec, "decision_supported": args.decision_supported}
                plan = project_artifact_registry.plan_artifact_registration(args.project_path, entry,
                    issue_id=args.issue_id, project_context=context, new_knowledge=new, amend=args.amend)
                result = {**plan.to_public_dict(), "artifact_id": plan._artifact_change["entry"]["id"], "registered": False}
                if args.write:
                    result = project_artifact_registry.apply_artifact_registration(args.project_path, plan, project_context=context)
            else:
                options = {"project_context": context, "view": "shared" if args.shared_ref else "working",
                           "ref": args.shared_ref or "HEAD"}
                if args.read_sources:
                    result = project_artifact_registry.read_artifact_sources(args.project_path, args.artifact_id, **options)
                else:
                    result = project_artifact_registry.read_artifact_registry(args.project_path,
                        query=args.query, artifact_ids=args.artifact_id, **options)
        except (OSError, ValueError, TypeError):
            print(json.dumps({"schema": "moduflow.knowledge-error.v1", "error_code": "KNOWLEDGE_REQUEST_INVALID",
                "registered": False, "next_action": "Check metadata, owning issue and initialized transaction prerequisites; preview again."}))
            return 1
    elif args.kind:
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
    if result.get("status") in {"conflict", "denied", "rolled_back", "recovery_required", "partial"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
