#!/usr/bin/env python3
"""Audit project mutation surfaces against reviewed operation ownership."""

import argparse
import ast
import json
from pathlib import Path


SCHEMA = "moduflow.project-operation-audit.v1"
ENTRYPOINT_SCHEMA = "moduflow.project-operation-entrypoints.v1"
ALLOWED_SCOPES = frozenset(
    {"target-project", "portfolio-control", "package-maintenance", "external-control"}
)
ALLOWED_OPERATIONS = frozenset({"read", "write", "execute", "publish", "none"})
ALLOWED_CLASSIFICATIONS = frozenset(
    {
        "guarded_boundary",
        "internal_guarded_helper",
        "package_maintenance",
        "external_control",
    }
)
_FILE_MUTATIONS = frozenset(
    {
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rename",
        "rmdir",
        "touch",
        "symlink_to",
        "hardlink_to",
    }
)
_OS_MUTATIONS = frozenset(
    {
        "link",
        "makedirs",
        "mkdir",
        "remove",
        "removedirs",
        "rename",
        "replace",
        "rmdir",
        "symlink",
        "unlink",
    }
)
_SHUTIL_MUTATIONS = frozenset(
    {"copy", "copy2", "copyfile", "copytree", "move", "rmtree"}
)
_GIT_WRITE_VERBS = frozenset(
    {"add", "commit", "fetch", "merge", "pull", "push", "rebase", "reset", "switch"}
)
_GH_WRITE_GROUPS = frozenset({"issue", "pr", "release", "workflow"})
_GH_WRITE_VERBS = frozenset(
    {"close", "comment", "create", "delete", "edit", "merge", "reopen", "review", "run"}
)
_NETWORK_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_TEMPFILE_CREATORS = frozenset(
    {
        "NamedTemporaryFile",
        "SpooledTemporaryFile",
        "TemporaryDirectory",
        "TemporaryFile",
        "mkdtemp",
        "mkstemp",
    }
)
_OS_OPEN_WRITE_FLAGS = frozenset(
    {"O_APPEND", "O_CREAT", "O_EXCL", "O_RDWR", "O_TRUNC", "O_WRONLY"}
)
_DYNAMIC_VALUE = object()


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


def _call_name(call):
    node = call.func if isinstance(call, ast.Call) else call
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _command_kind(node):
    command = _command_values(node)
    if len(command) >= 2 and command[0] == "git" and command[1] in _GIT_WRITE_VERBS:
        return f"git:{command[1]}"
    if (
        len(command) >= 3
        and command[0] == "gh"
        and command[1] in _GH_WRITE_GROUPS
        and command[2] in _GH_WRITE_VERBS
    ):
        return f"gh:{command[1]}:{command[2]}"
    return ""


def _network_method(node):
    name = _call_name(node)
    if name.endswith(".Request") or name == "Request":
        method = ""
        data_supplied = len(node.args) >= 2
        for keyword in node.keywords:
            if keyword.arg == "data":
                data_supplied = True
            if (
                keyword.arg == "method"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ):
                method = keyword.value.value.upper()
        if not method and data_supplied:
            method = "POST"
        return method if method in _NETWORK_WRITE_METHODS else ""
    tail = name.rsplit(".", 1)[-1].upper()
    return tail if tail in _NETWORK_WRITE_METHODS else ""


def _keyword_or_positional(call, keyword_name, position):
    for keyword in call.keywords:
        if keyword.arg == keyword_name:
            return keyword.value
    return call.args[position] if len(call.args) > position else None


def _node_position(node):
    return (getattr(node, "lineno", -1), getattr(node, "col_offset", -1))


def _resolve_local_value(node, assignments, before_position, seen=None):
    seen = set(seen or ())
    while isinstance(node, ast.Name) and node.id in assignments:
        if node.id in seen:
            return _DYNAMIC_VALUE
        seen.add(node.id)
        candidates = [
            item
            for item in assignments[node.id]
            if item["position"] < before_position
        ]
        if not candidates:
            return node
        if len(candidates) != 1 or candidates[0]["augmented"]:
            return _DYNAMIC_VALUE
        assignment = candidates[0]
        node = assignment["value"]
        before_position = assignment["position"]
    return node


def _open_mutation_kind(call, name, assignments):
    if name == "os.open":
        flags = _keyword_or_positional(call, "flags", 1)
        if flags is None:
            return "os.open:dynamic"
        flags = _resolve_local_value(
            flags,
            assignments,
            _node_position(call),
        )
        if flags is _DYNAMIC_VALUE:
            return "os.open:dynamic"
        flag_names = {
            node.attr
            for node in ast.walk(flags)
            if isinstance(node, ast.Attribute)
        }
        flag_names.update(
            node.id
            for node in ast.walk(flags)
            if isinstance(node, ast.Name) and node.id.startswith("O_")
        )
        if flag_names & _OS_OPEN_WRITE_FLAGS:
            return "os.open:create"
        if flag_names:
            return ""
        if isinstance(flags, ast.Constant) and flags.value == 0:
            return ""
        return "os.open:dynamic"
    if name != "open" and not name.endswith(".open"):
        return ""
    position = 1 if name == "open" else 0
    mode = _keyword_or_positional(call, "mode", position)
    if mode is None:
        return ""
    mode = _resolve_local_value(
        mode,
        assignments,
        _node_position(call),
    )
    if mode is _DYNAMIC_VALUE:
        return "open:dynamic"
    if not isinstance(mode, ast.Constant) or not isinstance(mode.value, str):
        return "open:dynamic"
    value = mode.value
    if not any(marker in value for marker in ("w", "a", "x", "+")):
        return ""
    marker = next((item for item in ("w", "a", "x", "+") if item in value), "+")
    return f"open:{marker}"


def _scope_nodes(function):
    nodes = []
    pending = [
        node
        for node in reversed(function.body)
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    while pending:
        node = pending.pop()
        nodes.append(node)
        children = []
        for child in ast.iter_child_nodes(node):
            if isinstance(
                child,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                continue
            children.append(child)
        pending.extend(reversed(children))
    return nodes


def _mutation_events(function):
    events = []
    nodes = _scope_nodes(function)
    assignments = {}
    for node in nodes:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(
                        {
                            "position": _node_position(node),
                            "value": node.value,
                            "augmented": False,
                        }
                    )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                assignments.setdefault(node.target.id, []).append(
                    {
                        "position": _node_position(node),
                        "value": node.value,
                        "augmented": False,
                    }
                )
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            assignments.setdefault(node.target.id, []).append(
                {
                    "position": _node_position(node),
                    "value": node.value,
                    "augmented": True,
                }
            )
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        call_kinds = set()
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in _FILE_MUTATIONS:
                call_kinds.add(node.func.attr)
        name = _call_name(node)
        if name.startswith("os.") and name.rsplit(".", 1)[-1] in _OS_MUTATIONS:
            call_kinds.add(name)
        if name.startswith("shutil.") and name.rsplit(".", 1)[-1] in _SHUTIL_MUTATIONS:
            call_kinds.add(name)
        open_kind = _open_mutation_kind(node, name, assignments)
        if open_kind:
            call_kinds.add(open_kind)
        if name.startswith("tempfile.") and name.rsplit(".", 1)[-1] in _TEMPFILE_CREATORS:
            call_kinds.add(name)
        method = _network_method(node)
        if method:
            call_kinds.add(f"network:{method}")
        for argument in node.args:
            kind = _command_kind(argument)
            if not kind and isinstance(argument, ast.Name):
                resolved = _resolve_local_value(
                    argument,
                    assignments,
                    _node_position(node),
                )
                if resolved is not _DYNAMIC_VALUE:
                    kind = _command_kind(resolved)
            if kind:
                call_kinds.add(kind)
        for kind in sorted(call_kinds):
            events.append({"kind": kind, "line": node.lineno, "node": node})
    return events


def _guard_operations(call):
    if _call_name(call).rsplit(".", 1)[-1] != "require_project_capability":
        return set()
    if len(call.args) < 2:
        return set()
    return {
        node.value
        for node in ast.walk(call.args[1])
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value in ALLOWED_OPERATIONS
    }


def _statement_blocks(function):
    blocks = {}
    parents = {}
    for parent in ast.walk(function):
        for _field, value in ast.iter_fields(parent):
            if isinstance(value, ast.AST):
                parents[id(value)] = parent
            elif isinstance(value, list):
                statement_items = [item for item in value if isinstance(item, ast.stmt)]
                if statement_items and len(statement_items) == len(value):
                    block = id(value)
                    for index, item in enumerate(value):
                        blocks[id(item)] = (block, index)
                for item in value:
                    if isinstance(item, ast.AST):
                        parents[id(item)] = parent
    return blocks, parents


def _innermost_statement(node, blocks, parents):
    current = node
    while current is not None:
        if id(current) in blocks:
            return current
        current = parents.get(id(current))
    return None


def _statement_chain(node, blocks, parents):
    chain = []
    current = node
    while current is not None:
        if id(current) in blocks:
            chain.append(current)
        current = parents.get(id(current))
    return chain


def _dominates(guard, target, blocks, parents):
    guard_statement = _innermost_statement(guard, blocks, parents)
    if guard_statement is None:
        return False
    guard_block, guard_index = blocks[id(guard_statement)]
    return any(
        blocks[id(statement)][0] == guard_block
        and guard_index < blocks[id(statement)][1]
        for statement in _statement_chain(target, blocks, parents)
    )


def _function_metadata(function):
    blocks, parents = _statement_blocks(function)
    guards = []
    calls = []
    references = []
    for node in _scope_nodes(function):
        if isinstance(node, ast.Call):
            operations = _guard_operations(node)
            if operations:
                guards.append({"line": node.lineno, "operations": operations, "node": node})
            name = _call_name(node).rsplit(".", 1)[-1]
            if name:
                calls.append({"name": name, "line": node.lineno, "node": node})
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            references.append({"name": node.id, "line": node.lineno, "node": node})
    mutations = _mutation_events(function)
    return {
        "line": function.lineno,
        "guards": guards,
        "calls": calls,
        "references": references,
        "mutations": mutations,
        "blocks": blocks,
        "parents": parents,
    }


def _iter_functions(nodes, prefix=""):
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_name = f"{prefix}{node.name}"
            yield function_name, node
            yield from _iter_functions(
                node.body,
                f"{function_name}.<locals>.",
            )
        elif isinstance(node, ast.ClassDef):
            yield from _iter_functions(node.body, f"{prefix}{node.name}.")


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
        for function_name, node in _iter_functions(tree.body):
            metadata = _function_metadata(node)
            functions[(module, function_name)] = metadata
            mutation_kinds = sorted({event["kind"] for event in metadata["mutations"]})
            if mutation_kinds:
                findings.append(
                    {
                        "module": module,
                        "function": function_name,
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
    if entry.get("scope") == "external-control" and entry.get("classification") != "external_control":
        errors.append(f"{prefix} external control requires external_control classification")
    if entry.get("scope") == "external-control" and entry.get("operation") != "publish":
        errors.append(f"{prefix} external control requires publish operation")
    return errors


def _function_reaches(functions, module, start_name, target_name, seen=None):
    if start_name == target_name:
        return True
    seen = set(seen or ())
    if start_name in seen:
        return False
    seen.add(start_name)
    metadata = functions.get((module, start_name))
    if metadata is None:
        return False
    for call in metadata["calls"]:
        called = call["name"]
        if called == target_name or _function_reaches(
            functions,
            module,
            called,
            target_name,
            seen,
        ):
            return True
    return False


def _guard_targets(entry, functions, owner):
    module = entry.get("module")
    function_name = entry.get("function")
    owner_name = entry.get("guard_owner")
    if function_name == owner_name:
        return [event["node"] for event in owner["mutations"]]

    targets = []
    function_leaf = str(function_name).rsplit(".", 1)[-1]
    for call in owner["calls"]:
        if call["name"] in {function_name, function_leaf} or _function_reaches(
            functions,
            module,
            call["name"],
            function_name,
        ):
            targets.append(call["node"])
    targets.extend(
        reference["node"]
        for reference in owner["references"]
        if reference["name"] in {function_name, function_leaf}
    )
    return targets


def _entry_is_guarded(entry, functions, owner):
    targets = _guard_targets(entry, functions, owner)
    if not targets:
        return False, "guard owner does not reach mutation helper"
    operation = entry.get("operation")
    matching_guards = [
        guard for guard in owner["guards"] if operation in guard["operations"]
    ]
    if not matching_guards:
        return False, f"guard does not declare {operation} operation"
    for target in targets:
        if not any(
            _dominates(
                guard["node"],
                target,
                owner["blocks"],
                owner["parents"],
            )
            for guard in matching_guards
        ):
            return False, "guard does not dominate mutation path"
    return True, ""


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
            if any(entry.get("scope") == "external-control" for entry in matches):
                non_network = [
                    kind
                    for kind in finding["mutation_kinds"]
                    if not kind.startswith("network:")
                ]
                if non_network:
                    configuration_errors.append(
                        "external-control classification must be network-only: "
                        f"{finding['module']}:{finding['function']} has "
                        + ", ".join(non_network)
                    )
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
        guarded, reason = (
            _entry_is_guarded(entry, functions, owner)
            if owner is not None
            else (False, "guard owner is missing")
        )
        if not guarded:
            unguarded.append(
                {
                    "module": entry.get("module"),
                    "function": entry.get("function"),
                    "mode": entry.get("mode"),
                    "guard_owner": entry.get("guard_owner"),
                    "reason": reason,
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
