# Spec: Machine Query Surface

Issue: `068-machine-query-surface`

## Problem

Agents have no structured way to query ModuFlow state. `.mcp.json` registers nothing; the existing `scripts/mcp_server.py` is a non-compliant single-shot stub that reads the retired `loop-state.json`, anchors to the plugin directory instead of the project, and was never registered. Reads therefore go through Bash script invocations (approval prompts) or parsing human-oriented ASCII dashboards.

## Users

- ModuFlow's own subagents and host agents (Claude Code sessions) needing state without approval friction.
- Third-party tooling wanting a stable contract.

## Goals

- A protocol-compliant, persistent stdio MCP server exposing read-only tools: status, issue list (with status filter), issue get, doctor summary.
- Registered in `.mcp.json` via `${CLAUDE_PLUGIN_ROOT}` so installed plugins resolve their scripts.
- Structured JSON everywhere, each payload carrying `"schema": "moduflow.mcp.v1"`.
- The same issue-list capability available on the CLI: `project_lifecycle.py --issues` (JSON).

## Non-Goals

- No mutating tools (issue create/status change) — explicit second phase per the issue's Scope Out.
- No goal-decomposition tool in v1 — the stub's `moduflow_decompose_goal` is mutating; dropped from the server (the stub was never registered, so nothing consumed it).
- No network transport; stdio only.

## Requirements

1. **Protocol**: JSON-RPC 2.0 over newline-delimited stdio, persistent loop. Handles `initialize` (returns protocol version + server info + capabilities.tools), `notifications/initialized` (no response), `tools/list`, `tools/call`, `ping`. Unknown method → `-32601`; malformed JSON → `-32700`; bad params → `-32602`. Notifications (no `id`) never get responses.
2. **Project root resolution**: the target project is the server's working directory (`Path.cwd()`), overridable via `MODUFLOW_ROOT` env var. Never the plugin/script directory (installed-plugin cache contains no `issues/`).
3. **Tools** (all read-only):
   - `moduflow_status`: from `.moduflow/state.json` (canonical since 048) + issue counts by status.
   - `moduflow_issues`: `[{id, status, title}]`, optional `status` filter arg.
   - `moduflow_issue_get`: single issue — id, status, title, outcome text, links, github url if present.
   - `moduflow_doctor`: `project_doctor.inspect_project(root, include_preflight=False)` summary (moduflow initialized, lifecycle drift, schema gates, installed_plugin staleness, recommendations).
4. **Tool results**: MCP content array with one `{"type": "text", "text": <json-string>}` item whose text is a JSON object including `"schema": "moduflow.mcp.v1"`.
5. **Shared logic**: issue listing implemented once in `project_lifecycle.py` (new `list_issues(root)` + `--issues` CLI flag printing JSON); the MCP server imports it — no duplicated parsing.
6. **Registration**: `.mcp.json` gains `{"mcpServers": {"moduflow": {"command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/mcp_server.py"]}}}`.
7. Testable without subprocess: request handling is a pure function `handle_request(req, root) -> response|None`.

## Acceptance Criteria

- `initialize` → result with `protocolVersion`, `serverInfo.name == "moduflow"`, tools capability; `notifications/initialized` → no response.
- `tools/list` → the four tools with JSON schemas.
- `moduflow_issues` with `{"status": "backlog"}` returns only backlog issues; without filter returns all; payload carries `schema: moduflow.mcp.v1`.
- `moduflow_issue_get` on a known id returns status/title/outcome/github url; unknown id → tool error content (not a crash).
- `moduflow_status` reflects `.moduflow/state.json` (not loop-state.json) and issue counts.
- `python3 scripts/project_lifecycle.py . --issues` prints a JSON array of `{id, status, title}`.
- Malformed JSON line → `-32700` response; unknown tool → error result; server loop continues after both.
- `python3 -m unittest tests.test_mcp_server -v` passes; full suite passes; `python3 scripts/release_check.py .` passes.

## Risks

- MCP protocol drift across Claude Code versions — mitigated by conservative core method set (initialize/list/call/ping) and a versioned payload schema.
- cwd assumption wrong in some hosts — mitigated by `MODUFLOW_ROOT` override.

## Alternatives Considered

- Keep the single-shot stub shape: rejected — cannot complete the MCP handshake, so it never appears as tools.
- Node-based server: rejected — repo is Python/stdlib-only by constitution-in-practice.
- Exposing doctor's FULL output: trimmed to a summary to keep token cost low; full detail stays on the CLI.

## Next Command

`product:plan 068-machine-query-surface`
