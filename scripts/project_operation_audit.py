#!/usr/bin/env python3
"""Audit project mutation surfaces against reviewed operation ownership."""

import argparse
import ast
import json
from pathlib import Path


SCHEMA = "moduflow.project-operation-audit.v1"
ENTRYPOINT_SCHEMA = "moduflow.project-operation-entrypoints.v1"
ALLOWED_SCOPES = frozenset(
    {"target-project", "portfolio-control", "package-maintenance"}
)
ALLOWED_OPERATIONS = frozenset({"read", "write", "execute", "publish", "none"})
ALLOWED_CLASSIFICATIONS = frozenset(
    {"guarded_boundary", "internal_guarded_helper", "package_maintenance"}
)
_FILE_MUTATIONS = frozenset(
    {"write_text", "write_bytes", "mkdir", "unlink", "rename", "rmdir", "touch"}
)
_GIT_WRITE_VERBS = frozenset(
    {"add", "commit", "fetch", "merge", "pull", "push", "rebase", "reset", "switch"}
)
_GH_WRITE_GROUPS = frozenset({"issue", "pr", "release", "workflow"})
_GH_WRITE_VERBS = frozenset(
    {"close", "comment", "create", "delete", "edit", "merge", "reopen", "review", "run"}
)
_NETWORK_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _command_values(node):
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    values = []
    for item in node.elts:
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            values.append(item.value)
        else:
            values.append(None)
    return values


def _mutation_kinds(function):
    kinds = set()
    for node in ast.walk(function):
        if isinstance(node, (ast.List, ast.Tuple)):
            command = _command_values(node)
            if len(command) >= 2 and command[0] == "git" and command[1] in _GIT_WRITE_VERBS:
                kinds.add(f"git:{command[1]}")
            if (
                len(command) >= 3
                and command[0] == "gh"
                and command[1] in _GH_WRITE_GROUPS
                and command[2] in _GH_WRITE_VERBS
            ):
                kinds.add(f"gh:{command[1]}:{command[2]}")
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in _FILE_MUTATIONS:
                kinds.add(node.func.attr)
            if (
                node.func.attr == "replace"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"
            ):
                kinds.add("os.replace")
        for keyword in node.keywords:
            if (
                keyword.arg == "method"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value in _NETWORK_WRITE_METHODS
            ):
                kinds.add(f"network:{keyword.value.value}")
    return sorted(kinds)


def _uses_guard(function):
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_project_capability"
        for node in ast.walk(function)
    )


def scan_scripts(root, *, errors=None):
    root = Path(root).resolve()
    errors = errors if errors is not None else []
    findings = []
    functions = {}
    for path in sorted((root / "scripts").glob("*.py")):
        module = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=module)
        except (OSError, SyntaxError, UnicodeError) as exc:
            errors.append(f"production source scan failed for {module}: {exc}")
            continue
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            functions[(module, node.name)] = {
                "line": node.lineno,
                "uses_guard": _uses_guard(node),
            }
            mutation_kinds = _mutation_kinds(node)
            if mutation_kinds:
                findings.append(
                    {
                        "module": module,
                        "function": node.name,
                        "line": node.lineno,
                        "mutation_kinds": mutation_kinds,
                    }
                )
    return findings, functions


def _load_entries(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != ENTRYPOINT_SCHEMA:
        raise ValueError(f"entrypoint schema must be {ENTRYPOINT_SCHEMA}")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("entrypoint entries must be a list")
    return entries


def _entry_errors(entry, index):
    prefix = f"entries[{index}]"
    errors = []
    if entry.get("scope") not in ALLOWED_SCOPES:
        errors.append(f"{prefix}.scope is unsupported: {entry.get('scope')!r}")
    if entry.get("operation") not in ALLOWED_OPERATIONS:
        errors.append(f"{prefix}.operation is unsupported: {entry.get('operation')!r}")
    if entry.get("classification") not in ALLOWED_CLASSIFICATIONS:
        errors.append(
            f"{prefix}.classification is unsupported: {entry.get('classification')!r}"
        )
    if not isinstance(entry.get("rationale"), str) or not entry["rationale"].strip():
        errors.append(f"{prefix}.rationale must be non-empty")
    if not isinstance(entry.get("module"), str) or not entry["module"].strip():
        errors.append(f"{prefix}.module must be non-empty")
    if not isinstance(entry.get("function"), str) or not entry["function"].strip():
        errors.append(f"{prefix}.function must be non-empty")
    if entry.get("scope") in {"target-project", "portfolio-control"}:
        if not isinstance(entry.get("guard_owner"), str) or not entry["guard_owner"].strip():
            errors.append(f"{prefix}.guard_owner must be non-empty")
    if entry.get("scope") == "package-maintenance" and entry.get("classification") != "package_maintenance":
        errors.append(f"{prefix} package maintenance requires package_maintenance classification")
    return errors


def inspect_project(root=".", entries_path=None):
    root = Path(root).resolve()
    scan_errors = []
    findings, functions = scan_scripts(root, errors=scan_errors)
    path = Path(entries_path or root / "config" / "project-operation-entrypoints.json")
    configuration_errors = list(scan_errors)
    try:
        entries = _load_entries(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        entries = []
        configuration_errors.append(f"entrypoint inventory is invalid: {exc}")

    for index, entry in enumerate(entries):
        configuration_errors.extend(_entry_errors(entry, index))

    entries_by_function = {}
    seen_exact = set()
    duplicate_entries = []
    for index, entry in enumerate(entries):
        key = (entry.get("module"), entry.get("function"))
        entries_by_function.setdefault(key, []).append(entry)
        exact = (*key, entry.get("mode"))
        if exact in seen_exact:
            duplicate_entries.append({"index": index, **entry})
        else:
            seen_exact.add(exact)

    unclassified = []
    classified = []
    for finding in findings:
        key = (finding["module"], finding["function"])
        matches = entries_by_function.get(key, [])
        if matches:
            classified.append({**finding, "entries": matches})
        else:
            unclassified.append(finding)

    stale_entries = [
        entry
        for entry in entries
        if (entry.get("module"), entry.get("function")) not in functions
    ]
    unguarded = []
    for entry in entries:
        if entry.get("scope") not in {"target-project", "portfolio-control"}:
            continue
        function_key = (entry.get("module"), entry.get("function"))
        if function_key not in functions:
            continue
        owner_key = (entry.get("module"), entry.get("guard_owner"))
        owner = functions.get(owner_key)
        if owner is None or not owner["uses_guard"]:
            unguarded.append(
                {
                    "module": entry.get("module"),
                    "function": entry.get("function"),
                    "mode": entry.get("mode"),
                    "guard_owner": entry.get("guard_owner"),
                }
            )

    errors = list(configuration_errors)
    errors.extend(
        f"unclassified mutation surface: {item['module']}:{item['function']}"
        for item in unclassified
    )
    errors.extend(
        f"unguarded mutation owner: {item['module']}:{item['guard_owner']}"
        for item in unguarded
    )
    errors.extend(
        f"stale mutation entry: {item.get('module')}:{item.get('function')}"
        for item in stale_entries
    )
    errors.extend(
        f"duplicate mutation entry: {item.get('module')}:{item.get('function')}:{item.get('mode')}"
        for item in duplicate_entries
    )
    return {
        "schema": SCHEMA,
        "project_root": str(root),
        "valid": not errors,
        "findings": findings,
        "classified": classified,
        "unclassified": unclassified,
        "unguarded": unguarded,
        "stale_entries": stale_entries,
        "duplicate_entries": duplicate_entries,
        "configuration_errors": configuration_errors,
        "errors": errors,
        "counts": {
            "findings": len(findings),
            "classified": len(classified),
            "unclassified": len(unclassified),
            "unguarded": len(unguarded),
            "stale": len(stale_entries),
            "duplicates": len(duplicate_entries),
            "configuration_errors": len(configuration_errors),
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--entries")
    args = parser.parse_args(argv)
    result = inspect_project(args.project_path, args.entries)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
