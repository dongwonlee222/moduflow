# Tasks: Project Knowledge and Artifact Registry

Issue: `090-project-knowledge-and-artifact-registry` · Owner: Dongwon Lee
Source: [existing issue](../../issues/090-project-knowledge-and-artifact-registry.md), 2026-09-02 delegated request.
Phase: A1–D2 source implementation verified at integrated c89fc65: 1,680 tests and all 13 release checks passed. Draft PR preparation; canonical backlog/cursor unchanged, publication not approved.
Prev: [spec](spec.md) / [plan](plan.md) / [approval](implementation-approval.md) · Next: authorized Draft PR; human merge/deployment approval remains separate. See [integration verification](integration-verification.md).

## Stream A — Canonical Schema and Initialization

- [x] A1: Implement one fenced-JSON Markdown parser and deterministic renderer for stable IDs, purpose/read_when, owner, period/as-of/update dates, state and optional original links (AC2/AC3).
- [x] A1: Add six wiki sections and two missing-only workspace templates; preserve legacy memory/knowledge files, reject automatic unstructured migration, report partial initialization and retry remaining files (AC1/AC7).
- [x] A1: Pass schema, empty-project, non-default path, archived-denial and no-overwrite tests before committing.

## Stream B — Metadata Retrieval and Committed Handoff

- [x] B1: Deliver the exact project-scoped R6 read envelope for 086/091/092; metadata-first home/search, total/omitted/truncated, match reasons and read traces; no source body scans (AC4/AC8).
- [x] B1: Implement selected-ID source reads, optional private/external handoff and required/broken/stale diagnostics; state/approval/freshness remain separate (AC3).
- [x] B1: Pin a single commit for wiki/catalog/issue/approval/source reads; reject dirty/uncommitted/ignored rescue, symlink sources, invalid refs and unknown Git evidence (AC5).
- [x] B1/D2: Complete the expanded simulation proof for reused IDs across scopes and renamed sources (S03/S07/S13); observations are in simulation-matrix.md.

## Stream C — Issue-Linked Output Registration

- [x] C1: Add bounded artifact-register intent/target branch to existing 103 transaction; no arbitrary-file API, direct registry writer or new lock engine (AC6).
- [x] C1: Validate owning issue, safe source and metadata preimages; registered output/catalog/backlink succeeds together; lifecycle/state/goal/loop/roadmap/dashboard remain byte-identical (AC6).
- [x] C1: Prove replay noop, conflicting same-ID content, concurrent edits, fault rollback/recovery, and archived/read-only denial before writes (AC6/AC7).
- [x] C2: Integrate opted-in knowledge creation before source write; legacy saves explicitly report unregistered; existing memory/decision registration does not copy or rewrite originals (AC6/AC7).
- [x] C2: Document preview/apply, selected-source reads, missing-prerequisite and migration guidance; external source creation is not part of local atomic rollback.

## Stream D — Diagnostics, Simulation and Handoff

- [x] D1: Integrate the sole parser in Validator/Doctor, distinguish missing optional capability from malformed present registry, and keep original availability separate from metadata validity (AC3/AC7).
- [x] D1: Register exact mutation ownership and package/template/test assets; reconcile 111 source/package validation surfaces without changing its release scope.
- [x] D2: Execute S01–S14 with synthetic A/B, empty/legacy/stale/missing/private/uncommitted sources and a separate committed worktree; record actual observations, read trace and assertion outcomes (AC9).
- [x] D2: Pass focused/full tests, artifact validation, operation/path audits, spec consistency, release check and diff check; run temporary packaged smoke (AC9). Integrated c89fc65: focused 317, full 1,680 and all 13 release checks pass. Incoming-source linkage/version failures remain historical evidence; details in integration-verification.md.
- [x] D2: Append PM/spec, privacy and transaction self-review evidence in implementation-review.md; keep implementation, simulated fresh task, real host observation, remote merge, publication and install claims separate. No independent reviewer or subagent is claimed.

## Approval and Exit Conditions

- [x] Joint spec/plan/tasks/simulation approval is recorded by Dongwon Lee before A1 begins.
- [x] Parent-task 111 release checkpoint is respected; integration/version/PR preparation has separate 2026-09-03 user approval. Main merge/install/publication remain unapproved.
- [x] Every AC maps to observed passing source evidence in implementation-review.md and the later integration-verification.md; the incoming AC9 policy blocker is resolved at c89fc65. Actual host/project use remains unperformed. Planned expected outcomes are never marked passed.

Checked source implementation items link to actual evidence in status.md and integration-verification.md. They do not represent main merge, publication, installation or actual project adoption.
