# Plan: Memory Relationship Capture at Write Time

Issue: `043-memory-relationship-capture-prompts`
Spec: `specs/043-memory-relationship-capture-prompts/spec.md` · Next: `product:execute 043`

## Changes

1. **`list_memory_ids(root, kind="")`** in `project_memory.py` — thin wrapper over `search_memory_entries(root, query="", kind=kind)` returning `[{id, kind, title}]`. Add `--list-ids` flag (optional `--kind` filter) → prints JSON, exit 0.
2. **`isolated_memory_entries(root)`** in `project_memory.py` — return entries whose `supersedes`/`depends_on`/`references` are all empty **and** `issue_id` is empty. Pure read; reuses `iter_memory_files` + `parse_frontmatter` + `parse_list_value`.
3. **`project_doctor.py` soft hint** — load `project_memory` (same importlib pattern as `load_project_validator`), call `isolated_memory_entries`, add `result["memory"]["isolated"]` (count + ids) and a `recommendation` line when > 0. **Exit code unchanged** (`moduflow.initialized` only) → stays exit 0. release_check safe.
4. **Command docs** `product-memory.md` + `product-knowledge.md` — add a "relationship capture" step: run `--list-ids`, then pass chosen `--supersedes/--depends-on/--references` and `--issue-id`. State explicitly: present options, never auto-link (042 anti-goal).

## Tests (`tests/test_project_memory.py` + doctor)

- `list_memory_ids` returns all entries; `--kind` filters.
- `isolated_memory_entries`: an entry with no links + no issue_id is flagged; one with `issue_id` or a relationship is not.
- doctor hint present when isolated > 0, and `inspect_project` still yields exit-0 conditions (assert the isolated hint does not flip `moduflow.initialized`).

## Gates

- `python3 -m unittest tests.test_project_memory` + doctor test pass.
- `python3 scripts/release_check.py` exit 0 (the hint must not break the gate — the whole point).
- Commit + push via `github-evmodu`; mark 043 done; sync state/dashboard/goal.

## Out of scope (confirmed)

- Auto-inference; `input()` prompts; new relationship fields; fcose; portfolio dashboard.
