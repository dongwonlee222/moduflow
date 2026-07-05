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

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.project_lifecycle import list_issues, _issue_status, _issue_title, ready_issues

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


def _server_version():
    try:
        plugin_json = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        return data.get("version", "0")
    except Exception:
        return "0"


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


def _rpc_error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _rpc_result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _tool_moduflow_status(root):
    from collections import Counter

    state_path = root / ".moduflow" / "state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return _text_result({"error": f"could not read .moduflow/state.json: {exc}"})

    counts = Counter(item["status"] for item in list_issues(root))
    payload = dict(state)
    if "schema" in payload:
        payload["state_schema"] = payload.pop("schema")
    payload["issue_counts"] = dict(counts)
    return _text_result(payload)


def _tool_moduflow_issues(root, arguments):
    status = arguments.get("status")
    items = list_issues(root)
    if status:
        items = [item for item in items if item["status"] == status]
    return _text_result({"issues": items})


def _tool_moduflow_issue_get(root, arguments):
    issue_id = arguments.get("id")
    if not issue_id:
        return None  # signals caller to raise a JSON-RPC -32602
    issues_dir = (Path(root) / "issues").resolve()
    path = (issues_dir / f"{issue_id}.md").resolve()
    # Containment: the id must name a file directly inside issues/ — absolute
    # paths and ../ traversal must not read arbitrary files through this tool.
    if path.parent != issues_dir or path.suffix != ".md":
        return _text_result({"error": "invalid issue id", "id": issue_id})
    if not path.is_file():
        return _text_result({"error": "issue not found", "id": issue_id})
    text = path.read_text(encoding="utf-8")
    return _text_result({
        "id": issue_id,
        "status": _issue_status(text),
        "title": _issue_title(text),
        "outcome": _outcome(text),
        "github": _github_link(text),
    })


def _tool_moduflow_ready(root):
    return _text_result({"ready": ready_issues(root)})


def _tool_moduflow_doctor(root):
    try:
        from scripts.project_doctor import inspect_project

        d = inspect_project(root, include_preflight=False)
        summary = {
            "initialized": d["moduflow"]["initialized"],
            "missing": d["moduflow"]["missing"],
            "lifecycle_drift": d["lifecycle"]["drift"],
            "schema_gates_valid": d["schema_gates"]["valid"],
            "installed_plugin": d.get("installed_plugin", {}),
            "recommendation": d.get("recommendation", []),
        }
        return _text_result(summary)
    except Exception as exc:
        return _text_result({"error": f"doctor inspection failed: {exc}"})


def handle_request(req, root):
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
            "serverInfo": {"name": "moduflow", "version": _server_version()},
        })

    if method == "ping":
        return _rpc_result(req_id, {})

    if method == "tools/list":
        return _rpc_result(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}

        if tool_name == "moduflow_status":
            return _rpc_result(req_id, _tool_moduflow_status(root))
        if tool_name == "moduflow_issues":
            return _rpc_result(req_id, _tool_moduflow_issues(root, arguments))
        if tool_name == "moduflow_issue_get":
            result = _tool_moduflow_issue_get(root, arguments)
            if result is None:
                if not has_id:
                    return None
                return _rpc_error(req_id, -32602, "Missing required argument 'id'")
            return _rpc_result(req_id, result)
        if tool_name == "moduflow_doctor":
            return _rpc_result(req_id, _tool_moduflow_doctor(root))
        if tool_name == "moduflow_ready":
            return _rpc_result(req_id, _tool_moduflow_ready(root))

        if not has_id:
            return None
        return _rpc_error(req_id, -32602, f"Unknown tool: {tool_name}")

    if not has_id:
        return None
    return _rpc_error(req_id, -32601, f"Method not found: {method}")


def _handle_line(line, root):
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
        return handle_request(req, root)
    except Exception as exc:
        # A persistent server must survive any single request — internal
        # errors become -32603 responses, never a process exit.
        req_id = req.get("id") if isinstance(req.get("id"), (str, int)) else None
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": f"internal error: {exc}"}}


def main():
    root = _resolve_root()
    for line in sys.stdin:
        response = _handle_line(line, root)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
