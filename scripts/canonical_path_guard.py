#!/usr/bin/env python3
"""Classify direct canonical-folder literals in production Python sources."""

import argparse
import ast
import json
import re
from pathlib import Path


SCHEMA = "moduflow.canonical-path-guard.v1"
CLASSIFICATION_SCHEMA = "moduflow.canonical-path-classifications.v1"
CANONICAL_ROLES = frozenset(
    {
        "issues",
        "specs",
        "workspace",
        "knowledge",
        "memory",
        "production-records",
        "playbooks",
        "workflow",
    }
)
CONTROL_PATHS = frozenset({".moduflow"})
ALLOWED_CLASSIFICATIONS = frozenset(
    {
        "canonical_default_declaration",
        "canonical_role_suffix",
        "project_control_path",
        "package_source_layout",
        "distribution_manifest",
        "test_fixture",
    }
)
_FRAGMENT_RE = re.compile(
    r"(?:^|/)(?:" + "|".join(re.escape(role) for role in sorted(CANONICAL_ROLES)) + r")/"
)


def _is_docstring(node, parents):
    parent = parents.get(node)
    if not isinstance(parent, ast.Expr):
        return False
    container = parents.get(parent)
    return isinstance(container, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))


def _literal_findings(module_path, source):
    tree = ast.parse(source, filename=module_path)
    parents = {
        child: node
        for node in ast.walk(tree)
        for child in ast.iter_child_nodes(node)
    }
    findings = {}

    def record(kind, literal, line):
        pattern = f"{kind}:{literal}"
        key = (module_path, pattern)
        finding = findings.setdefault(
            key,
            {
                "module": module_path,
                "pattern": pattern,
                "kind": kind,
                "literal": literal,
                "lines": [],
            },
        )
        finding["lines"].append(line)

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Div)
            and isinstance(node.right, ast.Constant)
            and isinstance(node.right.value, str)
            and node.right.value in CANONICAL_ROLES | CONTROL_PATHS
        ):
            record("join", node.right.value, node.lineno)
            continue
        if not (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and _FRAGMENT_RE.search(node.value)
            and (node.value.endswith("/") or "*" in node.value)
        ):
            continue
        if _is_docstring(node, parents):
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.BinOp) and parent.right is node:
            continue
        record("fragment", node.value, node.lineno)
    return sorted(findings.values(), key=lambda item: (item["module"], item["pattern"]))


def scan_scripts(root):
    root = Path(root).resolve()
    findings = []
    scripts_root = root / "scripts"
    for path in sorted(scripts_root.glob("*.py")):
        module_path = path.relative_to(root).as_posix()
        findings.extend(
            _literal_findings(module_path, path.read_text(encoding="utf-8"))
        )
    return findings


def _load_classifications(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != CLASSIFICATION_SCHEMA:
        raise ValueError(f"classification schema must be {CLASSIFICATION_SCHEMA}")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("classification entries must be a list")
    return entries


def _classification_error(finding, entry):
    classification = entry.get("classification")
    if classification not in ALLOWED_CLASSIFICATIONS:
        return f"unsupported classification: {classification!r}"
    if not isinstance(entry.get("rationale"), str) or not entry["rationale"].strip():
        return "classification rationale must be non-empty"
    if finding["literal"] in CONTROL_PATHS:
        if classification != "project_control_path":
            return ".moduflow joins require project_control_path"
        return None
    if finding["kind"] == "join" and classification not in {
        "package_source_layout",
        "test_fixture",
    }:
        return "runtime canonical-role joins cannot be allowlisted"
    return None


def inspect_project(root=".", classifications_path=None):
    root = Path(root).resolve()
    classifications_path = Path(classifications_path or root / "config" / "canonical-path-literals.json")
    findings = scan_scripts(root)
    entries = _load_classifications(classifications_path)
    by_key = {}
    duplicate_entries = []
    for index, entry in enumerate(entries):
        key = (entry.get("module"), entry.get("pattern"))
        if key in by_key:
            duplicate_entries.append({"index": index, **entry})
        else:
            by_key[key] = entry

    matched = set()
    unclassified = []
    prohibited = []
    for finding in findings:
        key = (finding["module"], finding["pattern"])
        entry = by_key.get(key)
        if entry is None:
            finding["status"] = "unclassified"
            unclassified.append(finding)
            continue
        matched.add(key)
        error = _classification_error(finding, entry)
        finding["classification"] = entry.get("classification")
        finding["rationale"] = entry.get("rationale")
        if error:
            finding["status"] = "prohibited"
            finding["error"] = error
            prohibited.append(finding)
        else:
            finding["status"] = "classified"

    stale_entries = [
        entry
        for key, entry in by_key.items()
        if key not in matched
    ]
    classified_count = sum(item["status"] == "classified" for item in findings)
    errors = []
    errors.extend(
        f"unclassified canonical path literal: {item['module']} {item['pattern']}"
        for item in unclassified
    )
    errors.extend(
        f"prohibited canonical path classification: {item['module']} {item['pattern']}: {item['error']}"
        for item in prohibited
    )
    errors.extend(
        f"stale canonical path classification: {item.get('module')} {item.get('pattern')}"
        for item in stale_entries
    )
    errors.extend("duplicate canonical path classification" for _item in duplicate_entries)
    result = {
        "schema": SCHEMA,
        "project_root": str(root),
        "valid": not (unclassified or prohibited or stale_entries or duplicate_entries),
        "findings": findings,
        "stale_entries": stale_entries,
        "duplicate_entries": duplicate_entries,
        "errors": errors,
        "counts": {
            "findings": len(findings),
            "classified": classified_count,
            "unclassified": len(unclassified),
            "prohibited": len(prohibited),
            "stale": len(stale_entries),
            "duplicates": len(duplicate_entries),
        },
    }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--classifications")
    args = parser.parse_args(argv)
    result = inspect_project(args.project_path, args.classifications)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
