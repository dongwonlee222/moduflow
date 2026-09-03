# Issue 090: Project Knowledge and Artifact Registry

**Status: done** — created 2026-07-16; started 2026-09-03; done 2026-09-03.
**Priority: p1**

## Summary

Make `workspace/knowledge.md` a structured project wiki and add `workspace/artifacts.md` as the canonical registry for reports, local files, Google Sheets, related issues, periods, and draft/final state.

## Source

- Type: user product direction
- Link: local Codex session, 2026-07-16
- Owner / decision maker: Dongwon Lee
- Current phase: complete. PR #47 merged as 8869afa; 0.3.57 published/installed after explicit 2026-09-03 approval. Full tests, merged-source CI, release gates, installed validation and fresh CLI/MCP passed. Canonical completion retains 111 active; actual company adoption and fresh host prompt-skill loading remain separate. See specs/090-project-knowledge-and-artifact-registry/release.md.

## Problem

Analysis knowledge and deliverable links become scattered across sessions, issue logs, local paths, and Google Sheets. Teams need a stable place for metric definitions, recurring sources, interpretation caveats, final reports, and the exact artifact considered final.

## Product Decision

- `workspace/knowledge.md` is the curated project wiki for definitions, analytical rules, recurring sources, interpretation traps, and durable conclusions.
- `workspace/artifacts.md` is the canonical human-readable registry for project materials.
- Dashboard and search views derive from these files; they do not become a second source of truth.
- Existing memory entries and decision records are linked, not duplicated.
- Domain caveats such as “external ScalarData population is not identical to the internal KPI population” must be expressible as durable interpretation knowledge with evidence and scope.

## Scope

### In

- A structured `workspace/knowledge.md` template covering metric definitions, analysis criteria, recurring data sources, Google Sheet/report links, final conclusions, and interpretation caveats.
- A structured `workspace/artifacts.md` registry with document name, purpose, local path, external link, related issue, reference period, lifecycle state, owner, and last updated date.
- Stable IDs and validation for artifact entries and links.
- `product:knowledge` initialization, inspection, and update guidance.
- Migration guidance for existing knowledge, reports, memory, and scattered workspace links.
- Dashboard-ready parsing without duplicating canonical content.

### Out

- Uploading local files to Google Drive automatically.
- Copying sensitive originals into the repository.
- Replacing detailed reports, Sheets, issues, memory entries, or decision records.
- Building the dashboard UI in this issue.

### Discovery and Handoff Requirements — 2026-09-02 Planning Draft

- Extend the existing scope with a stable material ID, one-line purpose, when-to-read guidance, as-of date/reference period, draft/approved/superseded state, owner, optional original locators and related issue IDs.
- Read the short project wiki/catalog first, then only explicitly selected originals; do not copy source bodies or company data into shared Git/plugin assets.
- Distinguish a missing required link from an unavailable optional private original, and separate metadata validity, freshness, source availability and committed-share readiness.
- Diagnose stale, broken, uncommitted and dirty sources; a local file cannot rescue a missing source in a committed snapshot used by another worktree.
- Register a saved result with its catalog entry and owning-issue backlink through a bounded extension of existing transaction ownership; do not assume Issue 103 already covers arbitrary output paths.
- Expose the same project-scoped stable ID/original/state read contract to 086, 091 and 092; UI and analysis-profile execution remain out of scope.
- Plan synthetic A/B, empty/legacy, stale/missing/private-source and separate committed-worktree scenarios without importing actual company data. The referenced data-context/data-manifest pattern is an application example, not a verified universal API.
- The linked spec/plan are prepared for one combined approval. These additions do not start implementation, change backlog state, or alter the parent task's 111 release gate.

## Acceptance Criteria

- A project can initialize both files without overwriting existing content.
- Knowledge sections cover core metrics, analysis criteria, recurring sources, key links, final conclusions, and commonly confused interpretations.
- Artifact entries contain document name, purpose, local path, external link, related issue, reference period, draft/final state, owner, and update date.
- Broken local paths and malformed registry entries are reported by validation without making external links mandatory.
- Sensitive or external-only files can be registered by metadata without being copied into Git.
- Existing memory and decision records are referenced instead of duplicated.
- `product:knowledge` can show the files and recommend the next missing knowledge or registry action.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*knowledge*registry*.py' -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `commands/product-knowledge.md`
- `scripts/project_knowledge.py`
- `scripts/project_memory.py`
- `templates/workspace/`
- `templates/knowledge/`
- `workspace/`
- `tests/`

## Scope Fence

Do not create a second database or copy external/sensitive source files into Git. Markdown registry files remain canonical and portable.

## Workflow Tasks

- [x] spec approved → `specs/090-project-knowledge-and-artifact-registry/spec.md`
- [x] plan approved → `specs/090-project-knowledge-and-artifact-registry/plan.md`
- [x] execute → templates, parser, validation, migration guidance, command updates, and tests; A1–D2 verified
- [x] review → `specs/090-project-knowledge-and-artifact-registry/implementation-review.md` and `integration-verification.md`; direct review, CI and explicit owner merge/deployment approval
- [x] release → PR #47 merged; v0.3.57 published/installed; proof and exclusions in `specs/090-project-knowledge-and-artifact-registry/release.md`

## Related Issues

- follows_up: `003-knowledge-evidence-layer`, `030-project-memory-layer`, `034-memory-capture-and-sync-workflow`, `043-memory-relationship-capture-prompts`, `085-project-production-records-and-playbooks`
- related: `033-business-document-workflow`, `044-product-dashboard-command`, `092-project-home-dashboard`
- blocks: `091-reproducible-analysis-runs-and-template-pack`, `092-project-home-dashboard`
- blocked_by:

## Reference Implementations

- Backstage repository identity and documentation annotations: `https://backstage.io/docs/features/software-catalog/well-known-annotations/`
- Backstage TechDocs Git-native documentation source: `https://backstage.io/docs/features/techdocs/creating-and-publishing/`
- Architecture Decision Record examples and lifecycle: `https://github.com/joelparkerhenderson/architecture-decision-record`

## Sessions

- 2026-07-16: User prioritized the project wiki and artifact registry as the first project-knowledge improvement.
- 2026-09-02: User approved the existing spec/plan for implementation and independent 086 QA preparation. Implementation, integration, release and actual application remain separate evidence.
- 2026-09-03: User approved history-preserving integration, version increase, full verification and PR creation. Integrated source gates passed; see integration-verification.md. Original implementation branch preserved.
- 2026-09-03: User separately approved PR #47 main merge and 0.3.57 publication/installation with rollback backups retained. Delivered from 8869afa; canonical complete transaction txn-0183cd493b66664aea8eebcba03644db passed projected/post-apply validation. No company data migration or fresh host-loading claim.

## Links

- Roadmap: `workspace/roadmap.md`
- Goal: `workspace/goal.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/20
- Spec: [English](../specs/090-project-knowledge-and-artifact-registry/spec.md) / [한국어](../specs/090-project-knowledge-and-artifact-registry/spec.ko.md)
- Plan: [Implementation plan](../specs/090-project-knowledge-and-artifact-registry/plan.md)
- Tasks: [Completed implementation tasks](../specs/090-project-knowledge-and-artifact-registry/tasks.md)
- Simulation: [Synthetic scenario matrix](../specs/090-project-knowledge-and-artifact-registry/simulation-matrix.md)
- Planning review: [한국어 검토·통합 인계](../specs/090-project-knowledge-and-artifact-registry/review-handoff.ko.md)
- Implementation authority: [Approval, ownership and lifecycle limitation](../specs/090-project-knowledge-and-artifact-registry/implementation-approval.md)
- Integration evidence: [Verified integration and delivery](../specs/090-project-knowledge-and-artifact-registry/integration-verification.md)
- PR review: [Purpose-first review packet](../specs/090-project-knowledge-and-artifact-registry/pr.md)
- Release: [0.3.57 delivery evidence](../specs/090-project-knowledge-and-artifact-registry/release.md)

## Outcome

완료: 프로젝트와 채팅을 옮겨도 이전 보고서·정의·결정 근거를 찾도록 짧은 위키와 자료 등록부를 구현했습니다. 흩어진 경로·승인 상태와 결과 저장 후 이슈 연결 누락을 줄이기 위한 기능이며, 실제 회사 도입 효과는 아직 측정하지 않았습니다.

PR #47이 main에 병합됐고 v0.3.57을 배포·설치했습니다. 전체 1,680개 테스트, 합성 시나리오 S01–S14, 병합 CI, 13개 릴리스 검사, 설치 패키지 검증과 새 CLI/MCP 확인을 통과했습니다. 기존 원본·캐시·복구 백업은 보존했습니다. 회사 자료 자동 이관, 086/092 UI와 실제 Codex/Claude 프롬프트 스킬 로딩은 완료 주장에 포함하지 않습니다.

## Next Command

`product:status`
