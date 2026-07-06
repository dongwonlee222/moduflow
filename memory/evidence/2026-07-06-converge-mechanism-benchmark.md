---
id: 2026-07-06-converge-mechanism-benchmark
kind: evidence
title: Converge Mechanism Benchmark (spec-kit vs OpenSpec)
issue_id: 071-spec-code-converge-check
spec: specs/071-spec-code-converge-check/spec.md
source_event: subagent-source-reading
retrieval_trigger: when implementing or revising the converge command, its verdict taxonomy, append format, or gate semantics; or when spec-kit/OpenSpec ship converge/verify changes
date: 2026-07-06
tags: [benchmark, converge, spec-kit, openspec, mechanism]
summary: Source-level reading of spec-kit /speckit.converge and OpenSpec /opsx:verify — taxonomies, evidence scoping (both prompt-only), append/report contracts, reported failure modes, and what 071 keeps/adjusts.
---

# Converge Mechanism Benchmark (source-level)

Researched 2026-07-06 by web-research subagent reading actual upstream sources, to concretize 071 beyond the existence-level 2026-07-05 competitive-gap benchmark.

## spec-kit `/speckit.converge`

Source: `templates/commands/converge.md` (270-line prompt template), commit 0c29d890, [PR #3001](https://github.com/github/spec-kit/pull/3001).

- Taxonomy (4): `missing` / `partial` / `contradicts` / `unrequested`. No `unverifiable` — replaced by "little/no code → classify all as missing, don't fail".
- Evidence scoping is **prompt-only** (no deterministic collection, "no git, no change tracking"): reads spec/plan/tasks/constitution; code scope = files named in plan/tasks + agent keyword search → **non-deterministic per run**. Compares **current code state**, not diff.
- Output: appends one `## Phase N: Convergence` section to tasks.md only when findings exist. Line format: `- [ ] T{ID} <imperative> per <source-ref> (<gap-type>)` — source-ref (FR-003/SC-002/constitution principle) builds provenance in. Severity CRITICAL/HIGH/MEDIUM/LOW; constitution violations first.
- No semantic dedup across re-runs — only ID uniqueness; unresolved gaps can re-append.
- Guardrails (verbatim, worth copying): *"The command's **only** write is appending a new `## Phase N: Convergence` section to `tasks.md`. It MUST NOT: modify `spec.md` or `plan.md` in any way; rewrite, renumber, reorder, or delete any existing task."* And: fully converged → *"leave `tasks.md` **byte-for-byte unchanged** (no empty Convergence header)"*.

## OpenSpec `/opsx:verify`

Source: `src/core/templates/workflows/verify-change.ts`, spec `openspec/specs/opsx-verify-skill/spec.md`.

- Verifies change implementation vs change artifacts (delta spec, tasks, design) on 3 dimensions: Completeness / Correctness / Coherence.
- **Correction to our issue text**: verify is NOT a mandatory archive gate — it is an optional, non-blocking quality report ("without blocking progress"). What blocks `openspec archive` is a **deterministic delta-spec validator**, and even that had an exit-0-on-failure bug ([#1311](https://github.com/Fission-AI/OpenSpec/pull/1311)).
- Report-only: scorecard + severity groups + `file.ts:123` refs; no automatic routing of failures back to work items.
- Artifact scoping deterministic (artifact graph), code-side evidence still agent grep.

## Reported failure modes

- OpenSpec [#498](https://github.com/Fission-AI/OpenSpec/issues/498): two validators disagree (`validate --strict` passes, `archive` fails) — dual-parser divergence.
- OpenSpec [#1311](https://github.com/Fission-AI/OpenSpec/pull/1311): gate failure with exit 0 — silent CI pass.
- OpenSpec [#1073](https://github.com/Fission-AI/OpenSpec/issues/1073): planning residue (unused APIs, mock branches) passes lint/test/verify — the hole an `unrequested` category would close.
- OpenSpec [#880](https://github.com/Fission-AI/OpenSpec/issues/880): community asks for current-code-vs-living-spec checking (verify only covers changes) — exactly 071's chosen target.
- spec-kit [discussion #3148](https://github.com/github/spec-kit/discussions/3148): token cost of full re-reads; unclear blast radius → conservative re-verification.

## 071 keeps (validated as ahead of upstream)

1. Hybrid deterministic evidence bundle — both upstreams are prompt-only on code evidence; 071's linkage-based bundle is the real differentiator and answers the #3148 cost concern via caps.
2. Verdict superset `+unrequested +unverifiable` — OpenSpec's missing `unrequested` is empirically a hole (#1073); spec-kit lacks `unverifiable`.
3. Normalized-text dedup with idempotent re-runs — spec-kit ships without dedup.
4. Non-gate v1 — matches upstream reality (neither agent-check actually blocks).

## 071 adjustments adopted

1. CV lines carry source-ref: `- [ ] CV-<n> [<severity>] <finding> — <AC#k|plan-constraint>, from converge <date>`; dedup key includes the source ref.
2. spec-kit guardrail sentences copied near-verbatim, including byte-for-byte no-op + no empty section header.
3. `missing` vs `no-evidence` split: commits exist but no code for an AC → `missing`; no resolvable commits at all → `no-evidence` report, no judging.
4. Single-parser principle (#498): AC parsing happens once in the evidence script; judge/report/append all consume that output.
5. Exit-code contract (#1311): non-zero on git/bundle failure in both JSON and human modes.
6. Emission order: high first; plan Global-Constraint violations auto-high (constitution analog).

## Correction applied

Issue 071's "OpenSpec `/opsx:verify` as mandatory archive gate" wording corrected — it is optional/non-blocking; the blocking part is the deterministic artifact validator.
