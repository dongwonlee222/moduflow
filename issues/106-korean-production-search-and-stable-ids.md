# Issue 106: Korean Production Search and Stable IDs

**Status: backlog** — created 2026-08-19.
**Priority: p1**
**Blocked-by:**

## Summary

Make project production knowledge reliably searchable with Korean multi-token queries and generate stable, meaningful, collision-resistant IDs for Korean-titled records and playbooks.

## Source

- Type: user multi-project orchestration improvement request
- Link: local Codex attachment `pasted-text.txt`, 2026-08-19
- Owner / decision maker: Dongwon Lee
- Current phase: backlog

## Opportunity

Issue 085 shipped project-local record/playbook search, but the current text matcher depends too heavily on contiguous phrases and ASCII slug fragments. Queries such as `스플래시 배너` can miss records containing both terms separately, and Korean titles can collapse to IDs such as `ev`.

## Scope

### In

- Normalize Unicode, spacing, punctuation, and case before token matching.
- Support explicit AND/OR multi-token search without requiring a vector database.
- Weight title, retrieval triggers, failed attempts, and `Do Not Repeat` above generic body matches.
- Add recency and approved-playbook ranking without treating candidates as approved rules.
- Return match reasons for every result.
- Generate deterministic IDs from an explicit English alias when present, otherwise from project ID, issue ID, record type, date, and a stable short hash/counter.
- Detect and resolve collisions without changing an existing record's ID.

### Out

- Semantic embeddings or a mandatory vector database.
- Cross-project raw record search.
- Translating Korean titles automatically through an external service.
- Relaxing the Production Record schema; Issue 101 owns schema discoverability.

## Acceptance Criteria

- `스플래시 배너` finds a record where the terms occur in separate fields and explains both matches.
- AND and OR behavior is explicit, deterministic, and covered by Korean punctuation/spacing fixtures.
- Approved playbooks rank ahead of equivalent candidate rules, while project records remain visible as evidence.
- A Korean-only title never produces `untitled` or a one-token incidental ASCII ID.
- Repeating ID generation for the same source identity returns the same ID; a different source cannot collide silently.
- Existing record IDs remain valid and are not rewritten automatically.
- Search remains strictly within the selected project unless Issue 107 supplies approved shared-playbook results.

## Verification

- Korean multi-token, normalization, punctuation, ranking, and explanation fixtures.
- Korean-only title, mixed Korean/English title, repeated generation, and collision fixtures.
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_production.py`
- `templates/production/record.md`
- `templates/production/playbook.md`
- `tests/fixtures/production-project/`

## Scope Fence

Do not add cross-project raw search, mandatory embeddings, automatic translation, or destructive ID migration.

## Workflow Tasks

- [ ] spec → `specs/106-korean-production-search-and-stable-ids/spec.md`
- [ ] plan → `specs/106-korean-production-search-and-stable-ids/plan.md`
- [ ] execute → tokenizer, scoring, explanations, stable IDs, compatibility, and tests
- [ ] review → `specs/106-korean-production-search-and-stable-ids/review.md`

## Related Issues

- blocks: `107-shared-approved-playbook-layer`
- blocked_by:
- duplicates:
- follows_up: `085-project-production-records-and-playbooks`
- supersedes:
- related: `101-production-record-schema-friction`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Source audit: `specs/102-project-registry-and-resolver/source-audit.md`

## Next Command

`product:spec 106-korean-production-search-and-stable-ids`
