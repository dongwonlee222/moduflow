# Issue 104: Project-Aware Natural-Language Request Orchestrator

**Status: backlog** — created 2026-08-19.
**Priority: p0**
**Blocked-by: `102-project-registry-and-resolver`, `103-atomic-lifecycle-state-transaction`**

## Summary

Connect ModuFlow's existing single natural-language entry point to project resolution, duplicate-aware issue routing, project production context, capability routing, verified output handoff, and atomic lifecycle updates.

## Source

- Type: user multi-project orchestration improvement request
- Link: local Codex attachment `pasted-text.txt`, 2026-08-19
- Owner / decision maker: Dongwon Lee
- Current phase: blocked

## Opportunity

Issues 020, 022, 076, and 097 already provide simple aliases, intake-to-goal routing, fast-path shaping, and a tested capability contract. The missing follow-up is one project-aware production request pipeline that always runs those capabilities in the safe order and returns one auditable routing result.

## Scope

### In

- Reuse `/moduflow` and natural-language aliases as the single public entry point; do not add a competing command unless the spec proves it necessary.
- Emit `moduflow.request-routing.v1` with request ID, resolved project, routing action, issue link/candidate, production context, capability handoff, current stage, output artifact, and next command.
- Resolve the project before reading project data or proposing writes.
- Search only the selected project's issues, approved playbooks, production records, and then approved shared playbooks.
- Attach revisions, resizes, compressions, and copy edits to the existing issue/record version when applicable.
- Invoke at most the capability selected by Issue 097 and pass only scoped context, prohibitions, and expected output artifact.
- Validate the output, then commit canonical/derived state through Issue 103's transaction.

### Out

- Replacing the router or capability adapters delivered by Issue 097.
- Cross-project raw record search.
- Automatic execution when project resolution is ambiguous or capability permission is not allowed.
- Creating a new issue for every production revision.

## Acceptance Criteria

- One natural-language production request returns the complete request-routing contract through the existing ModuFlow entry point.
- Ambiguous project resolution asks one question and performs zero writes or specialist calls beforehand.
- High-confidence overlap attaches to the existing issue; only a new independent deliverable produces a new issue candidate.
- Capability routing records adapter ID, reason, permission, availability, issue ID, and output artifact without false execution claims.
- Project A requests cannot expose Project B raw issues, records, brand copy, or local playbooks.
- A successful output passes artifact-specific verification when configured and atomically updates the linked issue/state views and Production Record.
- Existing intake, shaping, and capability-routing regression suites remain green.

## Verification

- Existing-campaign revision, new-project deliverable, ambiguous-project, unavailable-capability, and state-write-failure scenarios from the source request.
- Project A/B isolation fixtures in Korean and English.
- `python3 scripts/release_check.py .`

## Entry Points

- `commands/moduflow.md`
- `skills/index/SKILL.md`
- `skills/pm-execution-router/SKILL.md`
- `scripts/project_intake.py`
- `scripts/capability_routing.py`
- `scripts/project_production.py`

## Scope Fence

Do not create a second public entry point by default, scan unregistered projects, or bypass permission and human-approval gates.

## Workflow Tasks

- [ ] spec → `specs/104-project-aware-natural-language-request-orchestrator/spec.md`
- [ ] plan → `specs/104-project-aware-natural-language-request-orchestrator/plan.md`
- [ ] execute → request contract, project/context pipeline, handoff, transaction integration, and tests
- [ ] review → `specs/104-project-aware-natural-language-request-orchestrator/review.md`

## Related Issues

- blocks: `108-production-approval-and-verification-gates`
- blocked_by: `102-project-registry-and-resolver`, `103-atomic-lifecycle-state-transaction`
- duplicates:
- follows_up: `020-user-facing-simple-loop-ux`, `022-intake-to-goal-graph`, `076-product-context-interview-and-readiness-loop`, `097-single-entry-capability-routing-contract`
- supersedes:
- related: `075-issue-less-context-capture`, `085-project-production-records-and-playbooks`, `086-project-aware-production-library-dashboard`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Source audit: `specs/102-project-registry-and-resolver/source-audit.md`

## Next Command

After Issues 102 and 103 are done: `product:spec 104-project-aware-natural-language-request-orchestrator`.
