# Issue: `040-automatic-memory-candidate-capture`

## Goal

Automatically capture development decisions, benchmarks, research sessions, and release metadata into a temporary `memory/.candidates/` directory, and provide a workflow to approve them into durable project memory.

## Scope

- **Release Trigger**: Integrate with `product:release` (or `project_workflow.py` completion state) to automatically generate a memory candidate summarizing the completed issue, changes, and verification.
- **Research / Benchmark Trigger**: Provide a hook or command parameter (`project_memory.py --capture`) to parse research/evidence artifacts and create a memory candidate.
- **Candidate Lifecycle**:
  - Save pending candidates as YAML-frontmatter Markdown files in `memory/.candidates/`.
  - Provide a command to list candidates (`product:memory --candidates`).
  - Provide a command to approve and promote a candidate (`product:memory --approve <candidate-id>`).
  - Automatically clean up rejected or stale candidates.

## Workflow Tasks

- [x] spec -> define criteria for automated capture and approval CLI options
- [x] plan -> implementation plan for CLI hooks and lifecycle management
- [x] execute -> code changes in project_memory.py and project_workflow.py
- [x] review -> validation of auto-capture on release and research
- [x] release -> verify integration and deploy

## Related Issues

- `030-project-memory-layer` (Dependency / Foundation)
- `038-worker-context-memory-path-injection` (Downstream consumer of approved memory)
- `039-automated-review-checklists-and-safety-lint-gates` (Upstream review workflow)
