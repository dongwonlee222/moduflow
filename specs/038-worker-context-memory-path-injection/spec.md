# Spec: Worker Context Memory Path Injection

## Issue

`038-worker-context-memory-path-injection`

## Source Request

AI workers executing coding tasks should receive relevant past architectural decisions and design rules without blowing up the prompt context or violating context isolation guidelines.

## Problem

Full-text inlining of `memory/decisions/` inside LLM prompts leads to context window overload, attention drift, and higher token costs. We need a lightweight referencing mechanism.

## Goals

- Design a correlation helper in `scripts/worker_orchestrator.py` that identifies which memory files are relevant to the files/tasks in the worker plan.
- Dynamically append only the file paths, title, and short summary of these decisions to the subagent prompt.
- Advise the subagent explicitly to read the full files if they need to check the detailed logic.
- Keep prompt size lightweight and preserve context isolation rules.

## Non-Goals

- Inlining full text contents of memory directories.
- Implementing vector search / database indices in Phase 2.

## Proposed Changes & User Flows

### 1. Context Matching Logic
The correlation helper will:
1. Scan `memory/decisions/` (and other folders) to find approved decision records.
2. For each decision, read metadata fields like `references`, `depends_on`, `tags`, and `spec`.
3. If any task file path in the worker plan matches the referenced spec, issue, or directory of the decision, mark that decision as relevant.
4. If tags overlap with the task category or tags, mark it as relevant.

### 2. Prompt Assembly (Lightweight References)
Instead of inlining the full Markdown file body, the prompt builder in `worker_orchestrator.py` will append a `### Related Project Decisions` section to the subagent task configuration prompt:
```markdown
### Related Project Decisions

The following architectural decisions are relevant to this task. Read them using your tools if you need to consult their full logic:
- [YYYY-MM-DD-use-local-sqlite-cache](file:///Users/idong-won/projects/moduflow/memory/decisions/YYYY-MM-DD-use-local-sqlite-cache.md): Title of SQLite cache decision.
- [YYYY-MM-DD-git-canonical-memory](file:///Users/idong-won/projects/moduflow/memory/decisions/YYYY-MM-DD-git-canonical-memory.md): Title of git canonical memory decision.
```

## Acceptance Criteria

- `worker_orchestrator.py` scans `memory/decisions/` and correctly identifies decisions referencing files/specs touched by a task.
- Subagent prompts contain file paths and summaries, but never inline full file content.
- Unit tests verify correlation correctness and prompt structure.
