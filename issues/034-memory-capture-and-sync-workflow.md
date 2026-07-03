# Issue 034: Memory Capture And Sync Workflow

## Summary

Design and implement a clearer long-term memory capture workflow so ModuFlow can propose, approve, store, retrieve, and optionally mirror project memories without mixing them with full deliverable artifacts.

## Source

- Type: user feedback / product direction
- Link: conversation, 2026-06-26
- Date: 2026-06-26

## Lifecycle

- Phase: done
- Created: 2026-06-26
- Started: 2026-06-26
- Target End:
- Completed: 2026-07-03
- Last Updated: 2026-07-03

## Opportunity

ModuFlow 0.2.12 has a portable `memory/` prototype, but the user experience is still too manual. Users need to understand when memories are saved, what triggers a save, how memories differ from deliverables, and whether downloaded ModuFlow installations can use the same flow. They also need a practical path for Google Drive or similar tools without making external storage the source of truth.

Current best practice from adjacent memory tools suggests three useful directions:

- Local-first, plain-text project memory remains portable and inspectable.
- Automatic capture should create reviewable candidates, not silently persist every conversation.
- External systems such as Google Drive, vector indexes, MCP servers, or hosted memory APIs should act as mirrors, search indexes, or adapters rather than replacing Git-tracked project artifacts.

## Scope

### In

- Define the memory lifecycle: candidate, approved, stored, retrieved, stale, superseded, archived.
- Add a capture-candidate flow for durable events such as completed specs, completed plans, business documents, releases, decisions, evidence reviews, and failed approaches worth remembering.
- Keep full deliverables separate from memory entries: deliverables stay in `specs/`, `business/`, `reports/`, or `workspace/`; memory stores summary, rationale, links, tags, and review conditions.
- Define user-facing triggers for manual, suggested, and workflow-generated memory capture.
- Extend the memory schema with fields needed for artifact links, source event, supersedes/superseded_by, review_after, storage_policy, and mirror targets.
- Define retrieval flow for `product:evidence`, `product:status`, and future session-start briefs.
- Design external mirror/export adapters for Google Drive, GitHub Wiki, Obsidian folders, or rclone-backed cloud storage while keeping repo-local Markdown as the canonical source.
- Compare and borrow relevant patterns from projectmem, Basic Memory, mem0, and Supermemory without adding unnecessary infrastructure to v1.

### Out

- Capturing every chat message automatically.
- Making Google Drive, vector DBs, hosted memory APIs, or MCP indexes the canonical source of truth.
- Importing private personal memories into company/project repos automatically.
- Building a full hosted sync service in this issue.
- Replacing existing issues, specs, roadmap, or deliverable artifacts.

## Acceptance Criteria

- A spec defines memory capture triggers, candidate approval, storage, retrieval, stale/supersede handling, and external mirror/export policy.
- Downloaded ModuFlow users can initialize and use memory capture with only local project files.
- Memory entries and deliverables have a clear separation of responsibilities and links between them.
- Workflow-generated memory candidates are reviewable before permanent storage.
- `product:evidence` and/or `product:memory --search` can explain why a memory was returned and link back to the source artifact.
- Google Drive or similar external storage is documented as a mirror/export option, not as the canonical memory store.
- Doctor or validation checks can detect missing memory structure and obvious broken memory links.

## Workflow Tasks

Every artifact-producing step is a tracked task here - never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec -> `specs/034-memory-capture-and-sync-workflow/spec.md`
- [x] plan -> `specs/034-memory-capture-and-sync-workflow/plan.md`
- [x] execute -> PR / commits
- [x] review -> `specs/034-memory-capture-and-sync-workflow/review.md`
- [x] research -> compare projectmem, Basic Memory, mem0, Supermemory, and cloud sync patterns
- [x] design -> memory candidate queue and approval UX
- [x] design -> external mirror/export policy
- [x] validation -> schema and link checks for memory entries

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `030-project-memory-layer`, `033-business-document-workflow`
- supersedes:
- related: `024-artifact-schema-and-doctor-gates`, `029-antigravity-artifact-sync-connector`

## Research Notes

- projectmem: local-first memory and judgment layer with typed events, session brief, stale-memory detection, and MCP integration.
- Basic Memory: plain Markdown as the shared source for humans and LLMs, with local/cloud paths using the same files.
- mem0: simple add/search memory API surface and long-term conversational memory patterns.
- Supermemory: local or hosted memory engine with connectors such as Google Drive, Gmail, Notion, and GitHub; useful as an adapter reference, not a source-of-truth replacement.
- rclone / Google Drive sync: useful for mirroring Markdown and deliverable exports, but Git should remain canonical for project state and memory provenance.

## Sessions

- 2026-06-26: User asked whether downloaded ModuFlow users can use memory, whether Google Drive or other methods can store/access memory, and requested a review of save/retrieve flow plus GitHub/open-source examples.
- 2026-06-26: Tested the current manual memory flow by saving the team-memory decision to `memory/decisions/2026-06-26-use-git-canonical-memory-with-optional-adapters.md` and retrieving it with `project_memory.py --search` / `--get`.
- 2026-06-26: Wrote detailed implementation plan for candidate storage, approval, enriched retrieval, validation, and PM-friendly command documentation.
- 2026-06-26: Implemented local-first memory candidates, approval, enriched search metadata, export guidance, memory link validation, and PM-friendly command docs.

## Links

- Spec: `specs/034-memory-capture-and-sync-workflow/spec.md`
- Status: `specs/034-memory-capture-and-sync-workflow/status.md`
- Review: `specs/034-memory-capture-and-sync-workflow/review.md`
- Review Handoff: `specs/034-memory-capture-and-sync-workflow/review-handoff.md`
- PR Handoff: `specs/034-memory-capture-and-sync-workflow/pr.md`
- Draft PR: `https://github.com/dongwonlee222/moduflow/pull/5`
- Sessions: `sessions/034-memory-capture-and-sync-workflow/`
- Roadmap: `workspace/roadmap.md`
- projectmem: `https://github.com/riponcm/projectmem`
- Basic Memory: `https://github.com/basicmachines-co/basic-memory`
- mem0: `https://github.com/mem0ai/mem0`
- Supermemory: `https://github.com/supermemoryai/supermemory`

## Next Command

`/product:release 034-memory-capture-and-sync-workflow` after human approval.
