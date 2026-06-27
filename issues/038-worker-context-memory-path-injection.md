# Issue 038: Worker Context Memory Path Injection

## Summary

Implement dynamic injection of relevant memory paths and short summaries into task worker prompts in `worker_orchestrator.py` during execution, respecting context isolation rules to avoid prompt bloat.

## Source

- Type: user feedback / product direction
- Link: conversation, 2026-06-27
- Date: 2026-06-27

## Lifecycle

- Phase: roadmap
- Created: 2026-06-27
- Started:
- Target End:
- Completed:
- Last Updated: 2026-06-27

## Opportunity

When worker agents execute code tasks, they need access to relevant architectural rules and past decisions (e.g., in `memory/decisions/`). 
However, inlining full decision texts violates context isolation guidelines, causing context window bloat and attention drift. 
We need a helper in `scripts/worker_orchestrator.py` to identify relevant decisions and inject only their file paths, references, or short summaries into the prompt.

## Scope

### In

- Design a correlation helper that matches active tasks to related files in `memory/decisions/`.
- Inject only the file paths, references, or high-level summaries of these decisions into the prompt context for subagents.
- Ensure the prompt advises the agent to read these files explicitly using tools if they need the full text.

### Out

- Inlining full text contents of entire decision directories.

## Acceptance Criteria

- `worker_orchestrator.py` dynamically appends relevant memory references/paths to the generated task prompt.
- Subagent prompts instruct the agent on which past decisions/rules to consult.
- Context isolation rules are preserved (no full-text inlining).
- Unit tests verify prompt assembly behavior.

## Workflow Tasks

- [x] spec -> capture details of context mapping
- [x] plan -> implementation plan for memory injection
- [x] execute -> prompt building changes
- [x] review -> verify with tests
- [x] release -> release checks

## Related Issues

- follows_up: `037-delegation-level-gate-and-memory-context-graph`

## Sessions

- 2026-06-27: User requested setting up downstream issues for the remaining phases.

## Links

- Status: `specs/038-worker-context-memory-path-injection/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
