# Issue 075: Issue-Less Context Capture

**Status: backlog** — created 2026-07-06.
**Priority: p1**

## Summary

Add a first-class issue-less context workflow so ModuFlow can track sessions, inbox items, notes, and decisions without forcing every piece of work into an issue too early.

## Source

- Type: user workflow feedback
- Link: local Codex session
- Date: 2026-07-06

## Opportunity

Users often investigate, discuss, verify, or make small operational changes before the work deserves an issue. The current issue-only model makes this feel too heavy, but untracked work can still become invisible. ModuFlow needs a lighter context layer with clear promotion rules.

## Scope

### In

- Define context types: `session`, `inbox`, `note`, `decision`, `issue`.
- Define promotion gates from issue-less context to issue.
- Add or document commands such as `product:note`, `product:decision`, `product:session`, and `product:promote`.
- Add validation or release-check guidance so code-changing work cannot remain silently issue-less.
- Dogfood with the 074 recovery case.

### Out

- Replacing Git-file issues as the canonical execution unit.
- Requiring every conversation turn to create a file.
- Building a database or external SaaS sync for context in this issue.

## Acceptance Criteria

- ModuFlow can capture durable context without an issue when work is exploratory or low-risk.
- A clear rule says when issue-less context must be promoted to an issue.
- Code, command behavior, or policy changes require either an issue or an explicit approved issue-less context record.
- Status/doctor/release guidance can surface issue-less context that needs promotion.
- The 074 case is documented as an example of promotion recovery.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [ ] spec → `specs/075-issue-less-context-capture/spec.md`
- [ ] plan → `specs/075-issue-less-context-capture/plan.md`
- [ ] execute → PR / commits
- [ ] review → review notes
- [ ] design context type schema
- [ ] define promotion gates
- [ ] update status/doctor/release guidance

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `074-sync-fetch-sandbox-handling`, `069-issue-dependency-priority-model`
- supersedes:
- related: `034-memory-capture-and-sync-workflow`, `040-automatic-memory-candidate-capture`

## Sessions

- 2026-07-06: User observed that real work often happens without an issue and asked whether issue-less work is possible and enforceable.

## Links

- Decision: `memory/decisions/2026-07-06-use-issue-less-context-tiers.md`
- Spec: `specs/075-issue-less-context-capture/spec.md`
- Status: `specs/075-issue-less-context-capture/status.md`
- Sessions: `sessions/075-issue-less-context-capture/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:spec 075-issue-less-context-capture`
