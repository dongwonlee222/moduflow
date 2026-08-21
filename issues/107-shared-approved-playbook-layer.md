# Issue 107: Shared Approved Playbook Layer

**Status: backlog** — created 2026-08-19.
**Priority: p1**
**Blocked-by: `102-project-registry-and-resolver`, `106-korean-production-search-and-stable-ids`**

## Summary

Add an organization-level playbook layer that exposes only explicitly approved, generalized rules across projects while keeping every source project's raw records, issues, brand language, and local playbooks isolated.

## Source

- Type: user multi-project orchestration improvement request
- Link: local Codex attachment `pasted-text.txt`, 2026-08-19
- Owner / decision maker: Dongwon Lee
- Current phase: blocked

## Opportunity

Issue 085 correctly keeps production records and playbooks project-local and requires human approval before cross-project reuse. It does not define a separate shared canonical layer, redaction checks, promotion history, or retrieval contract for rules proven in more than one project.

## Scope

### In

- Define a separate shared-playbook schema and storage boundary owned by an explicitly configured organization workspace.
- Create promotion candidates from one or more project playbooks without copying raw records into the shared layer.
- Require explicit human approval and preserve approve/reject/hold history.
- Store source project IDs and source record/playbook IDs as provenance.
- Exclude or flag brand names, customer names, prices, campaign periods, and internal reporting language before approval.
- Return only approved shared rules to another project, after project-local approved playbooks and local production records.
- Support revocation and review dates without deleting provenance history.

### Out

- Federated search over project-local raw records.
- Automatic promotion or approval.
- A central database that replaces Git Markdown.
- Copying project-specific brand/campaign text into organization guidance.

## Acceptance Criteria

- Project B cannot read Project A raw records, issues, or local playbooks through the shared layer.
- An approved shared rule includes source project/record provenance, approver, approval date, review date, and redaction evidence.
- Candidate, rejected, held, revoked, or expired rules are never returned as authoritative guidance.
- Promotion containing project-specific names, prices, periods, or internal-report copy is blocked or requires an explicit, recorded redaction decision.
- Removing access to a source project does not erase the shared rule's provenance record, but does prevent raw-source traversal.
- Search order is project approved playbook, project production record, then organization approved playbook, with source type visible.
- Git Markdown remains canonical and all promotion history is auditable.

## Verification

- Two-project isolation, promotion, redaction, rejection, revocation, and expired-review fixtures.
- Korean project-specific term and price/date leakage fixtures.
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_production.py`
- `portfolio/projects.json`
- `templates/production/playbook.md`
- `.moduflow/humans.json`

## Scope Fence

Do not search source projects from another project, auto-approve candidates, or make a database canonical.

## Workflow Tasks

- [ ] spec → `specs/107-shared-approved-playbook-layer/spec.md`
- [ ] plan → `specs/107-shared-approved-playbook-layer/plan.md`
- [ ] execute → shared schema, candidate/redaction/approval flow, retrieval, audit, and tests
- [ ] review → `specs/107-shared-approved-playbook-layer/review.md`

## Related Issues

- blocks:
- blocked_by: `102-project-registry-and-resolver`, `106-korean-production-search-and-stable-ids`
- duplicates:
- follows_up: `085-project-production-records-and-playbooks`
- supersedes:
- related: `034-memory-capture-and-sync-workflow`, `075-issue-less-context-capture`, `090-project-knowledge-and-artifact-registry`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Source audit: `specs/102-project-registry-and-resolver/source-audit.md`

## Next Command

After Issues 102 and 106 are done: `product:spec 107-shared-approved-playbook-layer`.
