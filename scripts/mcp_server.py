#!/usr/bin/env python3
"""ModuFlow MCP server (068).

Protocol-compliant, persistent, read-only stdio MCP server. Exposes issue
list/get, status, and doctor summary tools so agents can query ModuFlow state
without Bash-approval-gated script invocations. All tools are read-only: no
file writes, no subprocess, no git/gh calls from this module.
"""
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    from scripts import project_registry, runtime_provenance
except ImportError:  # pragma: no cover - direct script execution fallback
    import project_registry
    import runtime_provenance

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.project_issue_schema import (
    evaluate_project,
    validate_issue_id,
)
from scripts.project_lifecycle import _READY_BLOCKING_DIAGNOSTICS

SCHEMA = "moduflow.mcp.v1"
PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "moduflow_status",
        "description": "ModuFlow 프로젝트의 현재 상태(.moduflow/state.json)와 이슈 상태별 개수를 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "moduflow_issues",
        "description": "이슈 목록을 조회합니다. status로 필터링할 수 있습니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "backlog | active | done | superseded",
                },
            },
        },
    },
    {
        "name": "moduflow_issue_get",
        "description": "단일 이슈의 상태/제목/Outcome/GitHub 링크를 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "이슈 파일명 stem (예: 068-machine-query-surface)",
                },
            },
            "required": ["id"],
        },
    },
    {
        "name": "moduflow_doctor",
        "description": "프로젝트 초기화/lifecycle drift/schema gate 상태 요약을 조회합니다 (preflight 없이).",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "moduflow_ready",
        "description": "차단되지 않은(blocked_by 충족) backlog 이슈를 priority 순으로 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]

_GITHUB_LINK_RE = re.compile(r"^-\s*GitHub:\s*(\S+)\s*$", re.MULTILINE)


def _resolve_root():
    env = os.environ.get("MODUFLOW_ROOT")
    return Path(env).resolve() if env else Path.cwd()


def _text_result(payload):
    # SCHEMA last so a payload's own "schema" key (e.g. state.json's
    # moduflow.state.v1) cannot clobber the tool-contract version.
    payload = {**payload, "schema": SCHEMA}
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}


def _runtime_snapshot(snapshot=None):
    return snapshot if snapshot is not None else runtime_provenance.capture_runtime(
        Path(__file__).resolve().parent.parent, runtime_kind="mcp_process")


def _server_version(runtime_snapshot=None):
    return _runtime_snapshot(runtime_snapshot).get("package_version") or "0"


def _links_section(text):
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "## Links"), None)
    if start is None:
        return ""
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return "\n".join(lines[start + 1:end])


def _github_link(text):
    m = _GITHUB_LINK_RE.search(_links_section(text))
    return m.group(1) if m else None


def _outcome(text):
    lines = text.splitlines()
    collected = []
    in_outcome = False
    for line in lines:
        if line.strip() == "## Outcome":
            in_outcome = True
            continue
        if in_outcome:
            if line.startswith("## "):
                break
            collected.append(line)
    return "\n".join(collected).strip()


def _issue_payload(issue):
    """Project one evaluated issue without changing the MCP v1 envelope."""
    return {
        "id": issue["issue_id"],
        "status": issue.get("lifecycle_state") or "unknown",
        "title": issue.get("title") or "",
        "priority": issue.get("priority"),
        "blocked_by": list(issue.get("blocked_by") or []),
        "normalized_schema": issue.get("schema"),
        "readiness": issue.get("readiness"),
        "recommended_next_command": issue.get("recommended_next_command"),
        "diagnostic_codes": sorted({
            diagnostic.get("code")
            for diagnostic in issue.get("diagnostics", [])
            if diagnostic.get("code")
        }),
    }


def _evaluated_items(root, *, project_context=None):
    context = project_context or project_registry.project_context_for_root(root)
    evaluation = evaluate_project(
        Path(root).resolve(), project_paths=context["relative_paths"]
    )
    return evaluation, sorted(
        (_issue_payload(issue) for issue in evaluation["issues"]),
        key=lambda item: item["id"],
    )


def _ready_items(evaluation):
    blocked_ids = {
        issue["issue_id"]
        for issue in evaluation["issues"]
        if any(
            diagnostic.get("code") in _READY_BLOCKING_DIAGNOSTICS
            and (
                diagnostic.get("severity") == "error"
                or diagnostic.get("code") == "ISSUE_DEPENDENCY_UNMET"
            )
            for diagnostic in issue.get("diagnostics", [])
        )
    }
    items = [
        _issue_payload(issue)
        for issue in evaluation["issues"]
        if issue.get("lifecycle_state") == "backlog"
        and issue["issue_id"] not in blocked_ids
    ]
    return sorted(
        items,
        key=lambda item: (item.get("priority") or "p9", item["id"]),
    )


def _rpc_error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _rpc_result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _tool_moduflow_status(root, *, project_context=None, runtime_snapshot=None):
    from collections import Counter

    state_path = root / ".moduflow" / "state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return _text_result({"error": f"could not read .moduflow/state.json: {exc}",
                             "runtime_provenance": _runtime_snapshot(runtime_snapshot)})

    _evaluation, items = _evaluated_items(
        root, project_context=project_context
    )
    counts = Counter(item["status"] for item in items)
    payload = dict(state)
    if "schema" in payload:
        payload["state_schema"] = payload.pop("schema")
    payload["issue_counts"] = dict(counts)
    payload["runtime_provenance"] = _runtime_snapshot(runtime_snapshot)
    return _text_result(payload)


def _tool_moduflow_issues(root, arguments, *, project_context=None):
    status = arguments.get("status")
    _evaluation, items = _evaluated_items(
        root, project_context=project_context
    )
    if status:
        items = [item for item in items if item["status"] == status]
    return _text_result({"issues": items})


def _tool_moduflow_issue_get(root, arguments, *, project_context=None):
    issue_id = arguments.get("id")
    if not issue_id:
        return None  # signals caller to raise a JSON-RPC -32602
    if not validate_issue_id(issue_id):
        return _text_result({"error": "invalid issue id", "id": issue_id})
    context = project_context or project_registry.project_context_for_root(root)
    evaluation, _items = _evaluated_items(root, project_context=context)
    project_root = Path(root).resolve()
    project_paths = context["relative_paths"]
    lexical_source = (
        Path(project_paths["issues"]) / f"{issue_id}.md"
    ).as_posix()
    evaluated = next(
        (
            issue for issue in evaluation["issues"]
            if issue.get("issue_id") == issue_id
        ),
        None,
    )
    if evaluated is None:
        evaluated = next(
            (
                issue for issue in evaluation["issues"]
                if issue.get("source_path") == lexical_source
            ),
            None,
        )
    if evaluated is None:
        return _text_result({"error": "issue not found", "id": issue_id})
    text = ""
    source_is_safe = (
        evaluated.get("source_format") not in {"blocked", "unreadable"}
        and not any(
            str(diagnostic.get("code") or "").startswith("ISSUE_SOURCE_")
            for diagnostic in evaluated.get("diagnostics", [])
        )
    )
    if source_is_safe:
        try:
            issues_dir = (project_root / project_paths["issues"]).resolve()
            issues_dir.relative_to(project_root)
            source = (project_root / evaluated["source_path"]).resolve()
            source.relative_to(issues_dir)
            if source.is_file():
                text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError):
            text = ""
    return _text_result({
        **_issue_payload(evaluated),
        "outcome": _outcome(text),
        "github": _github_link(text),
    })


def _tool_moduflow_ready(root, *, project_context=None):
    evaluation, _items = _evaluated_items(
        root, project_context=project_context
    )
    return _text_result({"ready": _ready_items(evaluation)})


def _tool_moduflow_doctor(root, *, project_context=None, runtime_snapshot=None):
    try:
        from scripts.project_doctor import inspect_project

        d = inspect_project(
            root,
            include_preflight=False,
            project_context=project_context,
            runtime_snapshot=_runtime_snapshot(runtime_snapshot),
        )
        summary = {
            "initialized": d["moduflow"]["initialized"],
            "missing": d["moduflow"]["missing"],
            "lifecycle_drift": d["lifecycle"]["drift"],
            "schema_gates_valid": d["schema_gates"]["valid"],
            "installed_plugin": d.get("installed_plugin", {}),
            "recommendation": d.get("recommendation", []),
            "runtime_provenance": d["runtime_provenance"],
            "validation_role": d["validation_role"],
            "error_codes": d["error_codes"],
        }
        return _text_result(summary)
    except Exception as exc:
        return _text_result({"error": f"doctor inspection failed: {exc}",
                             "runtime_provenance": _runtime_snapshot(runtime_snapshot)})


def handle_request(req, root, *, project_context=None, runtime_snapshot=None):
    """Pure request handler: same input -> same output. Returns a response
    dict, or None for notifications (no id / notifications/* methods)."""
    method = req.get("method")
    req_id = req.get("id")
    has_id = "id" in req
    params = req.get("params") or {}

    if isinstance(method, str) and method.startswith("notifications/"):
        return None

    if method == "initialize":
        return _rpc_result(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "moduflow", "version": _server_version(runtime_snapshot)},
        })

    if method == "ping":
        return _rpc_result(req_id, {})

    if method == "tools/list":
        return _rpc_result(req_id, {"tools": TOOLS})

    if method == "tools/call":
        role = runtime_provenance.inspect_validation_target(root, requested_role="project")
        if not role["valid"]:
            return _rpc_result(req_id, _text_result({**role, "error": "target is not a project",
                "runtime_provenance": _runtime_snapshot(runtime_snapshot)}))
        context = project_context or project_registry.project_context_for_root(root)
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}

        if tool_name == "moduflow_status":
            return _rpc_result(
                req_id,
                _tool_moduflow_status(root, project_context=context, runtime_snapshot=runtime_snapshot),
            )
        if tool_name == "moduflow_issues":
            return _rpc_result(
                req_id,
                _tool_moduflow_issues(
                    root, arguments, project_context=context
                ),
            )
        if tool_name == "moduflow_issue_get":
            result = _tool_moduflow_issue_get(
                root, arguments, project_context=context
            )
            if result is None:
                if not has_id:
                    return None
                return _rpc_error(req_id, -32602, "Missing required argument 'id'")
            return _rpc_result(req_id, result)
        if tool_name == "moduflow_doctor":
            return _rpc_result(
                req_id,
                _tool_moduflow_doctor(root, project_context=context, runtime_snapshot=runtime_snapshot),
            )
        if tool_name == "moduflow_ready":
            return _rpc_result(
                req_id,
                _tool_moduflow_ready(root, project_context=context),
            )

        if not has_id:
            return None
        return _rpc_error(req_id, -32602, f"Unknown tool: {tool_name}")

    if not has_id:
        return None
    return _rpc_error(req_id, -32601, f"Method not found: {method}")


def _handle_line(line, root, *, runtime_snapshot=None):
    """Parse one newline-delimited JSON-RPC request line and dispatch it.
    Malformed JSON -> a -32700 parse-error response (id null); otherwise
    delegates to handle_request (which may itself return None)."""
    line = line.strip()
    if not line:
        return None
    try:
        req = json.loads(line)
    except Exception:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
    if not isinstance(req, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid request: not an object"}}
    try:
        return handle_request(req, root, runtime_snapshot=runtime_snapshot)
    except Exception as exc:
        # A persistent server must survive any single request — internal
        # errors become -32603 responses, never a process exit.
        req_id = req.get("id") if isinstance(req.get("id"), (str, int)) else None
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": f"internal error: {exc}"}}


def main():
    root = _resolve_root()
    snapshot = runtime_provenance.capture_runtime(Path(__file__).resolve().parent.parent,
        runtime_kind="mcp_process", observed_at=datetime.now(timezone.utc).isoformat())
    for line in sys.stdin:
        response = _handle_line(line, root, runtime_snapshot=snapshot)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
