# Issue 090 — Implementation Self-Review

Issue: `090-project-knowledge-and-artifact-registry` · Owner: Dongwon Lee
Result: scoped implementation and synthetic behavior verified; release-policy readiness remains blocked, not approved.
Authority: [implementation approval](implementation-approval.md). Evidence: [status](status.md), [simulations](simulation-matrix.md).
Review date: 2026-09-03. Base: `22c01c9`; reviewed implementation: A1–D1 commits through `e812104` plus the D2 changes accompanying this record.

## Why / Problem / Expected Benefit

A future task needs to find the correct project material without inheriting hidden chat context. Unscoped search, source duplication and conflated approval/availability make that handoff unreliable. The implementation provides stable scoped references, selective source reads and issue-linked registration; actual adoption or productivity benefit has not been measured.

## Review Method and Limits

The implementation owner inspected the approved spec, changed runtime boundaries, failure paths, tests and packaging inventory. This is a self-review, not independent agent review. Work stayed inline as explicitly authorized. TDD regression checks and verification-before-completion guided the review; a passing feature suite does not waive release policy or establish installed-host behavior.

The spec/plan retain their original pre-approval wording as a historical baseline; implementation-approval.md is the subsequent authority. Canonical 090 backlog and the 111 active cursor remain unchanged and integration-owned.

## Acceptance-Criteria Evidence

| Criterion | Implemented boundary / observed evidence | Assessment |
| --- | --- | --- |
| AC1 | Missing-only wiki/catalog initialization, legacy-byte preservation, partial retry, archived denial and exclusive-create race regression; S01/S02/S12. | Pass in synthetic/local tests |
| AC2 | One fenced-JSON parser/renderer, exact fields, UUIDv4 IDs, six wiki sections, dates/period/owner/read_when; schema tests and S01/S07. | Pass |
| AC3 | Validator/Doctor consume the canonical facade, including entries beyond default limit; required/optional/private/external/stale axes remain separate; S04–S07/S14. | Pass |
| AC4 | Content-read spy sees only wiki/catalog before selection; explicit source body, A/B reused ID and poisoned default paths; S03/S08/S13. | Pass |
| AC5 | One resolved OID for wiki/catalog/issue/evidence/source; real detached worktree, author-only/dirty/staged/ignored content and symlink/gitlink rejection; S09/S10/S14. | Pass in local Git simulation |
| AC6 | Bounded existing 103 transaction owns catalog/backlink/optional new output. Eight replacement faults, recovery, idempotence, preimage/source conflicts and unchanged lifecycle bytes; transaction suite and S11. | Pass |
| AC7 | Legacy results explicitly unregistered; existing memory source bytes retained; CLI preview/apply and manual migration guidance, denial before mutation; S02/S12 and CLI tests. | Pass; no automatic migration |
| AC8 | Project ID plus stable artifact ID and snapshot envelope; null/unbound identity, missing IDs, supersession and root/context mismatch explicit; S03/S07/S13. | Facade contract verified; no downstream UI implementation claimed |
| AC9 | S01–S14, temporary packaged CLI, focused 317, project/package/operation/path/spec checks pass. Full suite: 1,678 pass / 2 release-check wrapper failures out of 1,680; linkage/version gates remain failing. | Partial / release-policy blocker |

## Findings Resolved During D2

- Reused the existing issue-ID validator instead of a numeric-only duplicate, retaining supported IDs such as BIZ-103.
- Rejected orphan/incomplete metadata blocks while preserving non-record prose; duplicate IDs still never choose a winner.
- Enforced empty issue-list and draft approval constraints; rejected credential-bearing URL fragments as well as queries.
- Added safe relative diagnostic locations without echoing rejected paths or private values.
- Rejected non-object registration JSON with a structured CLI error before transaction work.
- Made missing-only initialization use exclusive creation, so a file created concurrently by a person is preserved.
- Preserved the owning issue's complete original byte prefix, including trailing blank lines, when appending its artifact backlink.

Each runtime fix has a regression assertion in the focused suite. No parser, validator, permission, mutation audit or release gate was weakened to produce a pass.

## Privacy and Transaction Boundaries

- Fixtures contain only synthetic projects, IDs, sources, dates and canaries. No actual company source, credential or private pathname is stored in this packet.
- Home/search reads metadata only. Explicit local reads use no-follow path handling; shared reads use committed regular blobs. Private/external locators are handoffs, never network probes or permission to retrieve.
- Metadata can itself be confidential. Schema/path checks are not DLP, proof of share authorization, or proof that recorded approval is analytically correct.
- Registration has a bounded entry/new-knowledge intent, not arbitrary target bytes. Existing lock/journal/rollback/recovery owns writes; catalog and issue preimages plus source identity/content are checked again under lock.
- Existing originals are never rewritten or rolled back. Generated supported knowledge output participates in the transaction. Separate external/source creation is outside local atomicity.
- No new database, crawler, scheduler, transaction engine, UI or shared-state authority was introduced.

## Remaining Integration Conditions

Behavior commits `3cd88b1` and `2420417` lack accepted issue linkage, and the source version remains 0.3.56. Release check therefore remains invalid. The integration task was notified and explicitly directed continuation without rewriting history, bumping version, changing installed cache or editing the shared 111 state. The final implementation commit includes an Issue trailer; that does not retroactively repair the earlier commits.

The integration owner must resolve the release-policy and single-active lifecycle conditions before treating 090 as integrated/released. Remote push/PR/merge/publication, installed runtime and real fresh-host/project observations are unperformed and outside this work's authority.
