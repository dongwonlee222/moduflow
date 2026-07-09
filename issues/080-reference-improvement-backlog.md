# Issue 080: Reference Improvement Backlog

**Status: reviewed** — created 2026-07-09, started 2026-07-09, reviewed 2026-07-09.
**Priority: p2**

## Summary

Capture improvement ideas discovered while using reference repositories, such as `webn77/ai-native-backoffice-ui`, into a separate reference-improvement backlog so those ideas do not disappear or pollute the main product issue queue.

## Source

- Type: user product direction
- Link: local Codex session
- Date: 2026-07-09

## Opportunity

During real product work, agents often discover improvements for reference repositories, templates, or upstream examples. Those ideas are valuable, but they are not always part of the current product issue. ModuFlow needs a lightweight place to preserve them with source context and optional promotion into a real issue later.

## Scope

### In

- A reference-improvement backlog artifact, likely under `workspace/`, `memory/`, or a new lightweight project-local location.
- Fields for source repo, observed gap, suggested improvement, originating issue/spec, priority, and promotion status.
- Guidance for capturing suggestions found during `product:design`, `product:prototype`, `product:plan`, `product:execute`, or `product:review`.
- Promotion path into a normal ModuFlow issue when the improvement becomes actionable.

### Out

- Automatically opening issues in external GitHub repositories.
- Mutating reference repositories without explicit user approval.
- Replacing `memory/evidence` or `workspace/roadmap.md`.
- Building a cross-repo dashboard in v1.

## Acceptance Criteria

- Reference improvement ideas can be captured without creating a normal execution issue immediately.
- Each record links back to the ModuFlow issue/spec/session that discovered it.
- Records can be promoted into `issues/*.md` when the user chooses to act.
- `product:status` or `product:loop` can surface pending reference improvements as optional context without blocking active work.
- Validation passes.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `commands/product-memory.md`
- `commands/product-inbox.md`
- `commands/product-promote.md`
- `commands/product-status.md`
- `commands/product-loop.md`
- `scripts/project_memory.py`
- `scripts/project_promote.py`
- `workspace/`
- `memory/`

## Scope Fence

Do NOT touch (files, behaviors, or decisions out of bounds for this issue).

- Do not create remote GitHub issues automatically.
- Do not make reference backlog entries part of release blocking.
- Do not add external storage.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/080-reference-improvement-backlog/spec.md`
- [x] plan → `specs/080-reference-improvement-backlog/plan.md`
- [x] execute → PR / commits
- [x] review → `specs/080-reference-improvement-backlog/review.md`

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `075-issue-less-context-capture`
- supersedes:
- related: `034-memory-capture-and-sync-workflow`, `040-automatic-memory-candidate-capture`, `076-product-context-interview-and-readiness-loop`

## Sessions

- 2026-07-09: User requested a loop for capturing reference repo improvement candidates discovered during modu-biz work, including examples like `webn77/ai-native-backoffice-ui`.

## Links

- Spec: `specs/080-reference-improvement-backlog/spec.md`
- Status: `specs/080-reference-improvement-backlog/status.md`
- Sessions: `sessions/080-reference-improvement-backlog/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:pr 080-reference-improvement-backlog`
