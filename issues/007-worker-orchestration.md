# Issue 007: Worker Orchestration

## Summary

Make worker assignment and parallel execution decisions explicit so ModuFlow can safely route issue work to PM, design, data, implementation, QA, and release workers.

## Source

- Type: product direction
- Link: user conversation
- Date: 2026-06-11

## Opportunity

ModuFlow already documents Superpowers-style execution, but users need a concrete worker plan that explains which tasks can run in parallel, which must stay sequential, and which worker owns each check.

## Scope

### In

- Add a worker orchestration command.
- Generate worker plans from issue task files.
- Detect basic parallel eligibility and shared-state risk.
- Write worker plan JSON and Markdown artifacts per issue.
- Connect worker planning to `product:execute`.

### Out

- Hosted worker runtime.
- Automatic remote agent spawning.
- Provider-specific subagent APIs.

## Acceptance Criteria

- Users can run a script to generate a worker plan for an issue.
- The plan assigns tasks to known ModuFlow workers.
- The plan marks parallel-eligible work separately from sequential/shared-state work.
- The generated plan is stored under the issue spec folder.

## Links

- Spec: `specs/007-worker-orchestration/spec.md`
- Status: `specs/007-worker-orchestration/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 007-worker-orchestration`
