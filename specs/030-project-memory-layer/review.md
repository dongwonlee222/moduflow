# Review: Project Memory Layer Legacy Status Audit

Issue: `030-project-memory-layer`
Date: 2026-07-21
Owner / decision maker: Dongwon Lee
Current phase: superseded
Next command: `product:status`

## Verdict

Supersede the unfinished legacy prototype through `090-project-knowledge-and-artifact-registry`. Keep the project-memory foundation that shipped in commit `5929502`, while treating Issues 034, 040, 043, and 085 as the delivered extensions and Issue 090 as the owner of the remaining structured knowledge, artifact-registry, and migration scope.

## Evidence

- Commit `59295021cbf7be1ee4fc177085b763d74f8a4ffc` added the initial `project_memory.py`, `product:memory`, memory template, decision record, doctor checks, validation, and tests on 2026-06-24.
- `python3 -m unittest tests.test_project_memory tests.test_project_migration -v` passed 48 tests on 2026-07-21.
- `python3 scripts/project_memory.py . --search "portable project memory"` retrieved the original Issue 030 decision from project-local Markdown.
- `python3 scripts/project_doctor.py .` confirmed the repository and lifecycle are valid, but reported the optional memory capability as not fully initialized because four memory directories are absent.
- Before this audit, `specs/030-project-memory-layer/spec.md`, `plan.md`, `status.md`, and `review.md` did not exist even though the issue linked to spec/status paths.

## Acceptance-Criteria Disposition

| Original criterion | Disposition |
| --- | --- |
| Formal spec for memory model, schema, folders, and relationships | Not completed; do not fabricate a retroactive spec. Remaining registry definition belongs to Issue 090. |
| Register and find deliverables without knowing the issue number | Shipped through project-local memory search and filters. |
| Decision records include rationale, evidence, alternatives, owner, confidence, and reversal conditions | Shipped in the memory entry contract and tests. |
| Search by query, type, issue, spec, roadmap item, or tag | Mostly shipped; query/kind/issue/spec/tag exist, while a dedicated roadmap filter does not. Registry work belongs to Issue 090. |
| Doctor validates initialization and broken memory links | Shipped, with incomplete optional initialization visible in the current doctor result. |
| Project stays self-contained when moved | Shipped through Git-tracked Markdown and relative project-local links. |
| External indexes remain rebuildable adapters | Shipped as the canonical memory policy and export guidance. |
| Existing knowledge migrates without loss or overwrite | Partially covered by non-overwriting migration initialization; structured knowledge-to-memory/artifact migration remains with Issue 090. |

## Successor Mapping

- `034-memory-capture-and-sync-workflow`: candidate capture, approval, retrieval metadata, external mirror policy, and released human-review path.
- `040-automatic-memory-candidate-capture`: automatic candidate generation and approval lifecycle.
- `043-memory-relationship-capture-prompts`: content-verified relationship capture and isolated-memory hints.
- `085-project-production-records-and-playbooks`: structured recurring deliverable knowledge.
- `090-project-knowledge-and-artifact-registry`: remaining project wiki, artifact registry, validation, and migration ownership.

## Historical Number Collision

Issue `066-legacy-issue-status-migration` contains an older note that called `030` done using commit `7843122`. That commit belongs to the separate `030-worker-cognitive-demand-model-routing` issue, not `030-project-memory-layer`. The later Issue 066 follow-up correctly kept this memory issue in backlog. This audit resolves the ambiguity using the full issue slug and the actual memory implementation commit `5929502`.

## Human Approval

Dongwon Lee approved the `superseded` disposition on 2026-07-21 after the shipped foundation, missing artifacts, incomplete acceptance criteria, successor issues, and current verification evidence were summarized.
