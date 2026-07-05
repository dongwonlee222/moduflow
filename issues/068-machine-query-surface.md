# Issue: `068-machine-query-surface`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.

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

## Workflow Tasks

- [x] spec → `specs/068-machine-query-surface/spec.md`
- [x] plan → `specs/068-machine-query-surface/plan.md`
- [x] execute → `scripts/mcp_server.py`, `scripts/project_lifecycle.py`, `.mcp.json`, `tests/test_mcp_server.py`, `docs/host-adapter-guidance.md`, `commands/product-status.md`, `scripts/release_check.py`

## Sessions

- 2026-07-05: Registered from the competitive-gap benchmark (priority 1 of 5).
- 2026-07-05: Executed. Spec/plan authored in main loop (old stub judged unsalvageable: single-shot, read retired loop-state.json, wrong root when installed, unregistered; its mutating decompose_goal tool dropped per Non-Goals). Implementation subagent (TDD, 16 tests RED→GREEN, no-sub-delegation clause) delivered a persistent stdio JSON-RPC server with 4 read-only tools (status/issues/issue_get/doctor summary), `list_issues`+`--issues` in project_lifecycle, `.mcp.json` registration via `${CLAUDE_PLUGIN_ROOT}`. Independent verification: SPEC fail + QUALITY fail with reproduced findings — path traversal in issue_get leaking arbitrary file fields (absolute + `../` both), process crash on valid-JSON-non-object stdin lines, status payload schema clobbered by state.json's own schema key, `_issue_title` duplicated against the plan's single-source constraint. All fixed in main loop with 5 regression tests (containment check, -32600/-32603 guards, schema-last + state_schema rename, import from lifecycle, list_issues dir-skip hardening). Final: 21 module tests, 248 full suite, release_check valid, stdio smoke shows crash-line survival.

## Links

- Benchmark: `knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md`

## Next Command

`/product:status`
