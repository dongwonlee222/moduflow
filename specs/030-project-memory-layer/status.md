# Status: Project Memory Layer

Issue: `030-project-memory-layer`
Owner / decision maker: Dongwon Lee

**Status: superseded-by-090** — created 2026-06-24, prototype shipped 2026-06-24, superseded 2026-07-21.

## Snapshot

| Field | Value |
| --- | --- |
| Phase | superseded |
| Foundation commit | `5929502` |
| Primary successor | `090-project-knowledge-and-artifact-registry` |
| Review | `specs/030-project-memory-layer/review.md` |
| Next command | `product:status` |

## Preserved Foundation

- Repo-local Markdown memory initialization, write, search, and get behavior.
- Decision-memory schema and portable-link policy.
- Doctor and validation integration.
- Tests and the original portable-memory decision record.

## Delivered Follow-ups

- Issue 034: capture, approval, retrieval, and sync/mirror policy.
- Issue 040: automatic candidate capture.
- Issue 043: relationship capture.
- Issue 085: production records and playbooks.

## Transferred Scope

- Issue 090 owns the remaining structured project wiki, artifact registry, validation, and migration guidance.
- No retroactive spec or plan is created for the historical prototype.

## Verification

- 2026-07-21: `python3 -m unittest tests.test_project_memory tests.test_project_migration -v` passed 48 tests.
- 2026-07-21: project-local memory search retrieved the original Issue 030 decision.
- 2026-07-21: project doctor reported the optional memory structure is not fully initialized, preserving the known residual gap rather than treating it as completed scope.

## Next

`product:status`
