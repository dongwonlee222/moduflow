# Plan: Machine Query Surface

Issue: `068-machine-query-surface`
Spec: `specs/068-machine-query-surface/spec.md`
Next: `product:execute 068-machine-query-surface`

## Global Constraints

- Python stdlib only; no MCP SDK dependency.
- All tools read-only — no file writes, no subprocess, no git/gh calls from the server.
- `handle_request(req, root)` is pure (same input → same output; root passed explicitly) so tests never spawn the server process.
- Issue parsing lives in `project_lifecycle.py` only; the server imports, never re-implements.
- Responses to requests always echo `id`; notifications never produce output.

## Streams

### Stream A — `project_lifecycle.py` issue listing

Interfaces (produced): `list_issues(root) -> list[{id, status, title}]`; CLI `--issues` printing that as JSON.
- Reuse `_issue_status`; title = first `# ` heading text (strip `Issue:`/`Issue NNN:` prefix, backticks).
- Sorted by id.

### Stream B — `scripts/mcp_server.py` rewrite

Interfaces (consumed): `project_lifecycle.list_issues/_issue_status`, `project_doctor.inspect_project`, `.moduflow/state.json`.
Interfaces (produced): persistent stdio loop; `handle_request(req, root)`; `TOOLS` schema table.
- Root: `MODUFLOW_ROOT` env → else `Path.cwd()`.
- initialize/initialized/tools/list/tools/call/ping per spec Req 1; JSON-RPC error codes -32700/-32601/-32602.
- Tool payloads: JSON string inside MCP text content, `schema: moduflow.mcp.v1`.
- Doctor tool calls `inspect_project(root, include_preflight=False)` and projects a summary dict (initialized, drift, schema_gates.valid, installed_plugin, recommendation).

### Stream C — Registration + docs + gate

- `.mcp.json`: register the server with `${CLAUDE_PLUGIN_ROOT}` path.
- `docs/host-adapter-guidance.md` Default Order: prefer MCP tools for routine reads when the server is connected; Bash CLI stays the fallback.
- `commands/product-status.md`: note the MCP alternative for step-free reads.
- `scripts/release_check.py`: add `tests.test_mcp_server` to the module list.

### Stream D — Tests (`tests/test_mcp_server.py`)

Fixture: tempdir project with `.moduflow/state.json`, 3 issue files (backlog/active/done, one with a `- GitHub:` link).
Cases: initialize handshake shape; initialized-notification silence; tools/list; issues no-filter + status-filter; issue_get known/unknown; status counts; doctor summary (monkeypatch or fixture-tolerant); malformed JSON line → -32700 and loop survives (test the line-handler function); unknown tool error; `list_issues` unit test + `--issues` CLI smoke via function call.

## Task right-sizing

A (small, land first — B depends on it) → B (core) → D alongside B (TDD) → C last. One reviewable diff.

## Gates

- RED → GREEN on `tests.test_mcp_server`
- `python3 -m unittest discover -s tests`
- `python3 scripts/release_check.py .`
- Manual smoke: `echo` an initialize + tools/list line pair into `python3 scripts/mcp_server.py` from the repo root and see two JSON-RPC responses.

## Rollback

Revert the server/lifecycle/test changes and empty `.mcp.json` back to `{}`. Additive otherwise.
