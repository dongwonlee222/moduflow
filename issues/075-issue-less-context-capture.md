# Issue 075: Issue-Less Context Capture

**Status: active** — created 2026-07-06, spec 2026-07-06 (v2 rescoped), plan 2026-07-06, started 2026-07-06.
**Priority: p1**

## Summary

Make issue-less work traceable for an AI-operated repo: a machine-checkable commit↔issue linkage convention, a repaired release gate, `product:promote` for existing records, human-Git-identity approval for no-issue declarations, and AI-first issue fields.

> Rescoped 2026-07-06 after a three-subagent panel review (human-tool benchmark, AI-native benchmark, adversarial review). The original "new capture tier + product:capture command" scope was dropped — see `specs/075-issue-less-context-capture/adversarial-review.md` and decision `2026-07-06-promote-and-linkage-over-new-capture-tier`.

## Source

- Type: user workflow feedback
- Link: local Codex session
- Date: 2026-07-06

## Opportunity

Users often investigate, discuss, verify, or make small operational changes before the work deserves an issue. The current issue-only model makes this feel too heavy, but untracked work can still become invisible. ModuFlow needs a lighter context layer with clear promotion rules.

## Scope

### In

- Commit↔issue linkage convention: branch `codex/<issue-id>-*` (normative) + commit trailer `Issue: <id>`.
- Repair `release_check`: explicit merge-base, error (not silent pass) on git failure, linkage verification on behavior-affecting paths including `commands/*.md`.
- `product:promote`: existing record (decision/inbox/memory/knowledge) → issue with automatic bidirectional links.
- Human-Git-identity validation for no-issue declarations; declarations listed in `human-review.ko.md`.
- AI-first issue template fields: Verification, Entry points, Scope fence.
- Normalize the four existing capture commands: shared frontmatter (incl. `retrieval_trigger`) + ADD/UPDATE/SUPERSEDE/NOOP write discipline.
- Release-count-based retention (archive unpromoted records after 2 releases).
- Dogfood with the 074 recovery case.

### Out

- New `product:capture` command or new context-type tier (v1 scope, dropped — existing commands are the capture layer).
- Real-time session threshold detection (belongs to `072-lifecycle-hooks-automation`; 075 provides the checker it will call).
- Staged severity config; wall-clock archival; commit-time blocking.
- Replacing Git-file issues as the canonical execution unit.
- Requiring every conversation turn to create a file.
- Building a database or external SaaS sync for context in this issue.

## Acceptance Criteria

- Behavior-affecting release changes must resolve to an issue via branch/trailer, or to a no-issue declaration authored/approved by a **human Git identity**; agent-authored declarations are rejected.
- `release_check` errors loudly on git failure and covers direct-to-main commits; the existing silent-pass holes are removed.
- `product:promote` converts records to issues with bidirectional links, files staying in place.
- Issue template carries Verification / Entry points / Scope fence.
- Status surfaces unpromoted-record count/age; 2-release retention archives the rest, queryably.
- The 074 case is documented against the v2 mechanisms.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/075-issue-less-context-capture/spec.md` (+ `spec.ko.md`; v2 rescoped 2026-07-06)
- [x] benchmark → `memory/evidence/2026-07-06-issue-less-context-benchmark.md`, `memory/evidence/2026-07-06-ai-native-context-benchmark.md`
- [x] adversarial spec review → `specs/075-issue-less-context-capture/adversarial-review.md`
- [x] plan → `specs/075-issue-less-context-capture/plan.md` (+ `tasks.md`; spec_consistency clean)
- [ ] execute → PR / commits
- [ ] review → review notes
- [ ] define linkage convention + repair release_check
- [ ] implement product:promote with bidirectional links
- [ ] human-identity validation for no-issue declarations
- [ ] AI-first issue template fields
- [ ] normalize four capture commands (frontmatter + write discipline)

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `074-sync-fetch-sandbox-handling`, `069-issue-dependency-priority-model`
- supersedes:
- related: `034-memory-capture-and-sync-workflow`, `040-automatic-memory-candidate-capture`, `072-lifecycle-hooks-automation` (session-time detection hands off to 072; 075 provides the linkage checker it calls)

## Sessions

- 2026-07-06: User observed that real work often happens without an issue and asked whether issue-less work is possible and enforceable.

## Links

- Decision (v2): `memory/decisions/2026-07-06-promote-and-linkage-over-new-capture-tier.md`
- Decision (v1, superseded): `memory/decisions/2026-07-06-use-issue-less-context-tiers.md`
- Benchmark (human tools): `memory/evidence/2026-07-06-issue-less-context-benchmark.md`
- Benchmark (AI-native): `memory/evidence/2026-07-06-ai-native-context-benchmark.md`
- Adversarial review: `specs/075-issue-less-context-capture/adversarial-review.md`
- Spec: `specs/075-issue-less-context-capture/spec.md`
- Status: `specs/075-issue-less-context-capture/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:execute 075-issue-less-context-capture`
