# Spec: Issue Dependency & Priority Model

Issue: `069-issue-dependency-priority-model`

## Problem

Issue files carry only a flat `Status:` line. Execution order, blockers, and priority live in prose — no query can answer "what can I safely start now", parallel workers have no collision-safe pick, and the dashboard queue is hand-ordered.

## Goals

- Additive, git-diffable metadata on `issues/*.md`: `Priority` and `Blocked-by`.
- A ready-work computation: backlog issues whose blockers are all satisfied, priority-sorted.
- Exposure on CLI (`--ready` JSON), in `list_issues` payloads (MCP `moduflow_issues` inherits), and as a dedicated MCP tool `moduflow_ready`.
- Dependency integrity as drift-gate errors (cycles, dangling references).

## Non-Goals

- No `blocks` storage — canonical is `Blocked-by` only; inverses are derived (dual storage would drift).
- No estimates/complexity fields (deferred per issue Scope Out).
- No atomic claim primitive (single-operator reality; revisit with real concurrency).
- No retro-backfill obligation for done/superseded issues — fields are meaningful on open work.

## Requirements

1. **Format** (mirrors the 048 Status convention, one per line, directly after/near the Status line):
   - `**Priority: p0|p1|p2|p3**` — absent ⇒ `p2` (default).
   - `**Blocked-by: <id>, <id>**` — comma-separated issue file stems; absent ⇒ no blockers.
2. **Parsers** in `project_lifecycle.py` (`_issue_priority(text)`, `_issue_blocked_by(text)`), same regex style as `_issue_status`; invalid priority word ⇒ `p2`.
3. **`list_issues(root)`** items gain `priority` and `blocked_by` keys (additive; existing consumers unaffected).
4. **`ready_issues(root)`**: backlog issues where every `blocked_by` id has status `done` or `superseded` ⇒ ready. Sort: priority (`p0` first) then id. CLI: `--ready` prints JSON.
5. **Drift gate**: `lifecycle_drift(root)` additionally reports (a) `blocked_by` referencing a nonexistent issue id, (b) dependency cycles among non-done issues. Both are errors (fail release_check via the existing drift wiring).
6. **MCP**: new read-only tool `moduflow_ready` returning the ready list (payload `schema: moduflow.mcp.v1`); `moduflow_issues` passes the new fields through automatically.
7. **Template fix (latent-defect repair)**: `templates/issues/issue.md` still uses the pre-048 `## Lifecycle / Phase:` block with no canonical Status line — replace with the canonical `**Status: backlog**` line plus optional `**Priority: p2**` / `**Blocked-by:**` lines, so newly-templated issues stop reproducing the drift class `066` migrated away.
8. **Docs**: `commands/product-issue.md` documents the two fields; `commands/product-status.md` queue guidance renders ready vs blocked (`⏸` blocked with blocker ids, ready sorted by priority).
9. **Dogfood**: set `Priority` on the open backlog issues (`070` p1, `071` p1, `072` p2, `073` p2) and `Blocked-by` where true (none currently block each other — leave absent), demonstrating defaults stay valid.

## Acceptance Criteria

- Issue with `Blocked-by` on a non-done issue is excluded from `ready_issues`; flipping the blocker to done includes it; a `superseded` blocker also satisfies.
- Priority sort: p0 before p1 before unset(p2) before p3; ties by id.
- Dangling `Blocked-by` ref and a 2-node cycle each produce a drift entry (and thus fail release_check on a fixture).
- `python3 scripts/project_lifecycle.py . --ready` prints a JSON array.
- `moduflow_ready` MCP tool returns the same list with the schema key; `moduflow_issues` items carry `priority`/`blocked_by`.
- Template contains the canonical Status line and no `## Lifecycle` phase block.
- Module tests pass; full suite passes; `python3 scripts/release_check.py .` passes on this repo.

## Risks

- Cycle detection over statuses must not flag historical done↔done references — scope cycle check to issues not yet done/superseded.

## Alternatives Considered

- YAML frontmatter for metadata: rejected — house convention (048) is inline bold lines; frontmatter would create two metadata systems.
- Storing `blocks` inverses: rejected (drift risk).

## Next Command

`product:plan 069-issue-dependency-priority-model`
