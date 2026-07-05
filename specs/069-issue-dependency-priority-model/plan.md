# Plan: Issue Dependency & Priority Model

Issue: `069-issue-dependency-priority-model`
Spec: `specs/069-issue-dependency-priority-model/spec.md`
Next: `product:execute 069-issue-dependency-priority-model`

## Global Constraints

- Canonical metadata = inline bold lines in issue files (048 convention). No frontmatter, no side files, no `blocks` storage.
- All additions to `list_issues` payloads are additive — existing key set and ordering guarantees unchanged.
- Drift additions ride the existing `lifecycle_drift` return list (strings) — no new gate plumbing.
- Cycle check scope: only issues whose status is not done/superseded.
- MCP server changes limited to: one new TOOLS entry + one dispatch branch; no protocol changes.

## Streams

### Stream A — Lifecycle parsers + ready + drift (`scripts/project_lifecycle.py`)

Interfaces (produced): `_issue_priority(text) -> "p0".."p3"`, `_issue_blocked_by(text) -> list[str]`, `list_issues` items `+{priority, blocked_by}`, `ready_issues(root) -> list[item]`, `--ready` CLI, drift entries `"blocked_by references unknown issue ..."` / `"dependency cycle: ..."`.
- Priority regex: `\*\*Priority:\s*(p[0-3])` (case-insensitive on the word, normalize lower); anything else ⇒ p2.
- Blocked-by regex: `\*\*Blocked-by:\s*([^*]+)\*\*` → split on commas, strip whitespace/backticks, drop empties.
- Cycle detection: simple DFS over the blocked_by graph restricted to open issues.

### Stream B — MCP tool (`scripts/mcp_server.py`)

Interfaces (consumed): `ready_issues` import. Produced: `moduflow_ready` tool (no args) returning `{"ready": [...]}`.

### Stream C — Template + docs + dogfood

- `templates/issues/issue.md`: canonical Status line replaces the `## Lifecycle` phase block; add commented-style optional Priority/Blocked-by lines.
- `commands/product-issue.md`, `commands/product-status.md` per spec Req 8.
- Backfill `Priority` on issues `070`-`073` per spec Req 9 (edit only the line under Status; no other changes).
- `scripts/release_check.py`: add the new test module.

### Stream D — Tests (`tests/test_issue_dependencies.py` + 2 cases in `tests/test_mcp_server.py`)

Fixture tempdir project. Cases: priority parse (explicit, absent→p2, invalid→p2); blocked_by parse (multi, backticked, absent); ready excludes blocked / includes after done / superseded satisfies; sort p0<p1<p2<p3 then id; dangling ref drift; 2-cycle drift; done↔done reference NOT flagged; `--ready` via function; MCP: `moduflow_ready` payload schema + `moduflow_issues` items carry new keys.

## Task right-sizing

A (core) → B (thin) → D alongside A/B (TDD) → C last. One reviewable diff.

## Gates

RED→GREEN on new module; full discover; `release_check.py .`; smoke: `python3 scripts/project_lifecycle.py . --ready` on this repo shows 070/071 (p1) before 072/073 (p2).

## Rollback

Additive throughout; revert the diff. Backfilled Priority lines are inert if the code reverts (unknown bold lines are ignored by all parsers).
