# Issue: `068-machine-query-surface`

**Status: backlog** — created 2026-07-05.

## Outcome

Agents (ModuFlow's own subagents and third-party tools) query and mutate ModuFlow state through a structured machine interface — a real MCP server (list/get/update-status/ready tools) and `--json` flags on the read-side `product:*` scripts — instead of parsing Korean ASCII dashboards or triggering Bash-approval prompts for pure reads.

## Why

Benchmark (knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md): two independent research passes converged here. `.mcp.json` registers nothing and `scripts/mcp_server.py` is a 2-tool stub, while beads (`bd ready --json`), Task Master (36 MCP tools), and Backlog.md all treat JSON/MCP as the primary agent interface. `product:status`/`product:doctor` — the hottest read paths — each cost a Bash approval prompt today. This is also the prerequisite for `069`'s ready-work query being agent-consumable.

## Scope

### In

- Grow `scripts/mcp_server.py` into a real stdio MCP server registered in `.mcp.json` (`${CLAUDE_PLUGIN_ROOT}` paths): tools for issue list (id/status/title), issue get, status summary, doctor summary — read-only first.
- `--json` output flags on `project_sync.py`-style read scripts that lack them.
- Version the tool contract (schema field in responses) so third parties can build against it.

### Out

- Mutating MCP tools (issue create/status change) — second phase, after read surface proves out.
- No web UI / kanban (deferred per benchmark).

## Acceptance Criteria

- `.mcp.json` registers the server; tools appear in a Claude Code session without Bash prompts.
- Issue list/get/status/doctor tools return structured JSON with a schema version.
- Tests cover each tool against a fixture project.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `069-issue-dependency-priority-model` (ready query rides this surface)
- related: `027-reduce-approval-popup-friction` (same friction theme, pre-MCP era)

## Sessions

- 2026-07-05: Registered from the competitive-gap benchmark (priority 1 of 5).

## Links

- Benchmark: `knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md`

## Next Command

`/product:status`
