# Issue 037: Delegation Level Gate And Memory Context Graph

## Summary

Add a delegation level control gate to the workspace loop-state and extend the memory parser to support `depends_on` and `references` relationships, including a `--graph` CLI option to render a visual Mermaid graph of the memory context.

## Source

- Type: user feedback / product direction
- Link: conversation, 2026-06-27
- Date: 2026-06-27

## Lifecycle

- Phase: plan
- Created: 2026-06-27
- Started:
- Target End:
- Completed:
- Last Updated: 2026-06-27

## Opportunity

Based on the audit of ModuFlow 0.2.15 and Anthropic's AI Fluency Framework (Delegation principle), ModuFlow needs a explicit gate to control if a task should be fully automated or require human approval before execution. 
Additionally, to represent Neo4j-style context graphs, the local memory parser needs to parse dependencies and references, rendering them visually for users to navigate the design context.

## Scope

### In

- Add `delegation_level` (`full | review_required | manual`) to `workspace/loop-state.json`.
- Validate `delegation_level` in `scripts/project_loop.py` and enforce human-in-the-loop checks before executing tasks.
- Extend `scripts/project_memory.py` frontmatter parsing to include `depends_on` and `references` fields.
- Add a `--graph` CLI option in `scripts/project_memory.py` to output a Mermaid context diagram of local memory nodes and relations.

### Out

- Dynamic context prompt injection (deferred to Phase 2).
- Lint and security gates inside `release_check.py` (deferred to Phase 3).
- Code review discrepancy reports (deferred to Phase 3).

## Acceptance Criteria

- `workspace/loop-state.json` contains `delegation_level` (default: `"review_required"`).
- `project_loop.py` correctly parses and validates `delegation_level` values.
- `project_memory.py` parses `depends_on` and `references` relationship fields.
- Running `python3 scripts/project_memory.py . --graph` outputs a valid Mermaid flowchart of the memory context.
- Unit tests in `tests/test_project_loop.py` and `tests/test_project_memory.py` cover the new fields and options.
- The repository passes `python3 scripts/release_check.py .`.

## Workflow Tasks

- [x] spec -> captured in this issue
- [ ] plan -> approval of `implementation_plan.md`
- [ ] execute -> code changes for delegation and memory graph
- [ ] review -> validation and tests
- [ ] release -> release checks

## Related Issues

- follows_up: `034-memory-capture-and-sync-workflow`

## Sessions

- 2026-06-27: User requested implementation of the first phase of Neo4j Context Graph and Anthropic AI Fluency improvements.

## Links

- Status: `specs/037-delegation-level-gate-and-memory-context-graph/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:plan`
