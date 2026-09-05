# Tasks: Execution Planner and Backend Boundary

Issue: `112-execution-planner-and-backend-boundary`
Plan: `specs/112-execution-planner-and-backend-boundary/plan.md`
Status: planned — awaiting the Stream C interface review before execute

Boundaries use the bracket notation `commands/product-plan.md` documents, which
is the only form `worker_orchestrator.METADATA_RE` reads. This file is also the
dogfood fixture for the gates this issue builds: running the routing on issue
112 must return `ok` once Stream A lands.

## Stream A — Selection and refusal

- [ ] Port Gate 1 and Gate 2 from the evidence prototype into a standalone routing module with its RED/GREEN tests [files: scripts/execution_routing.py, tests/test_execution_routing.py]
- [ ] Add typed gaps carrying a kind of no_boundary, unreadable_notation or dangling_dependency [files: scripts/execution_routing.py] [depends: T01]
- [ ] Add notation fixtures covering the pipe form used by specs 103, 109 and 110 and assert it reports unreadable_notation [files: tests/fixtures/execution-routing/pipe-notation-tasks.md, tests/test_execution_routing.py] [depends: T02]

## Stream B — Routing decision

- [ ] Port Gate 3 with fnmatch path containment and assert inline is a success result [files: scripts/execution_routing.py, tests/test_execution_routing.py] [depends: T01]

## Stream C — Host adapter boundary

- [ ] Design and document the host adapter interface for review before any mapping code [files: docs/superpowers/specs/2026-09-05-issue-112-host-adapter-interface.md] [depends: T04]
- [ ] Implement the adapter and move the codex worktree prefix and model-name prompt text out of the routing result [files: scripts/execution_host_adapter.py] [depends: T05]
- [ ] Prove one routing result maps to Claude Code, Codex and Copilot with no canonical artifact change [files: tests/test_execution_host_adapter.py, tests/fixtures/execution-routing/hosts.json] [depends: T06]

## Stream D — Canonical artifact ownership

- [ ] Detect and report canonical versus Superpowers completion divergence without auto-resolving it [files: scripts/execution_routing.py, tests/test_execution_routing.py] [depends: T02]

## Stream E — Integration and verification

- [ ] Consume the routing result in the worker plan builder, refuse to write on a non-ok status, and emit a relative project root [files: scripts/worker_orchestrator.py] [depends: T04, T06] [shared_state: true]
- [ ] Update the existing worker orchestration tests that assume every checkbox becomes a worker task [files: tests/test_worker_orchestration.py] [depends: T09]
- [ ] Update the worker, execute and Superpowers bridge documents to describe refusal as a normal outcome [files: commands/product-workers.md, commands/product-execute.md, skills/superpowers-execution-bridge/SKILL.md] [depends: T09]
- [ ] Re-run the corpus and this issue's own dogfood check, then record the verdict distribution as evidence [files: specs/112-execution-planner-and-backend-boundary/status.md] [depends: T03, T07, T08, T10, T11]

## Required Gates

- [ ] `python3 -m unittest discover -s tests` green with the new suites present.
- [ ] Corpus behaviour holds: 029 plans, 001 refuses, 023 is not_applicable.
- [ ] Stream C interface reviewed before its mapping code was written.
- [ ] `python3 scripts/release_check.py .` reports 14 of 14.
- [ ] Running the routing on issue 112 itself returns `ok`.

## Next Command

`product:workers 112-execution-planner-and-backend-boundary`
