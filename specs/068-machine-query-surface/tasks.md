# Tasks: Machine Query Surface

Issue: `068-machine-query-surface`
Plan: `specs/068-machine-query-surface/plan.md`

## Stream A — Issue listing in lifecycle

- [ ] `list_issues(root)` + `--issues` CLI flag (JSON)

## Stream B — MCP server rewrite

- [ ] Persistent stdio JSON-RPC loop (initialize/initialized/tools/list/tools/call/ping)
- [ ] Root resolution: `MODUFLOW_ROOT` → cwd
- [ ] Tools: status / issues / issue_get / doctor summary
- [ ] Error codes -32700/-32601/-32602; notifications silent; loop survives bad input

## Stream C — Registration + docs

- [ ] `.mcp.json` registration with `${CLAUDE_PLUGIN_ROOT}`
- [ ] `docs/host-adapter-guidance.md` MCP-first read guidance
- [ ] `commands/product-status.md` MCP note
- [ ] `scripts/release_check.py` test-module list

## Stream D — Tests

- [ ] Handshake / list / call cases per plan
- [ ] Filter + unknown-id + malformed-input cases
- [ ] `list_issues` + `--issues` coverage

## Verification

- [ ] RED → GREEN on `tests.test_mcp_server`
- [ ] `python3 -m unittest discover -s tests`
- [ ] `python3 scripts/release_check.py .`
- [ ] Manual stdio smoke (initialize + tools/list)

## Next

`product:execute 068-machine-query-surface`
