# ModuFlow Project Constitution

Version: **v1.0** (ratified 2026-07-07 — see amendment log)
Jurisdiction: engineering principles for this project. Output/format conventions for agents live in `AGENTS.md` (issue 060 boundary) — the two do not overlap.

## Amendment procedure

1. Anyone (human or agent) may **propose** an amendment: a diff to this file plus rationale.
2. **Adoption requires explicit human approval**, recorded in the amendment log (date, change, proposer, human approver). This applies to v1.0 ratification itself. An agent never fills the approver field on its own authority.
3. Version bumps: **major** — principle added/removed or its force (MUST/SHOULD) changed; **minor** — wording clarification with no change in obligation.
4. **Unlogged edits are void**: a change to the principles without a matching approved log entry has no force. Revert path: `git log -- workspace/constitution.md`, revert any commit lacking a logged human approval.
5. A plan may **tighten** a principle for one issue as a plan-specific *addition* — that is not an amendment and needs no entry here.

## Principles

Each principle: force · rule · rationale · origin (the practiced law it codifies — nothing here was invented for this document).

- **C1 · MUST — Injectable runner.** All git/subprocess access in scripts goes through an injected command runner. *Rationale: testability without live processes; every gate is FakeRunner-testable.* Origin: 075 A1 / `project_sync.py` pattern, universal in `tests/`.
- **C2 · MUST — No silent exceptions in gate paths.** A failure in any gate/check surfaces as an explicit error result; `except: pass` and empty-result-on-error are forbidden. *Rationale: the pre-075 `release_check` holes passed vacuously in CI.* Origin: 075 GC2 and the repaired `release_check.py`.
- **C3 · MUST — Behavior changes ship with focused tests.** TDD where behavior changes; every code task lands with focused unittest coverage including error paths. *Rationale: 439-test suite is the project's regression floor.* Origin: superpowers execution bridge; every plan 007→072.
- **C4 · MUST — Session hooks fail open.** Hook scripts always exit 0, keep a hard time budget, and log diagnostics to file only; blocking channels (Stop exit 2, `decision:"block"`) are forbidden. *Rationale: a hook failure must never cost a session.* Origin: 072 spec + `hook-schema-notes.md`.
- **C5 · MUST — Findings are append-only.** Automated passes (converge, retention, sync) append; they never rewrite, renumber, reorder, or delete existing artifact content, and a no-op run leaves files byte-for-byte unchanged with no empty headers. *Rationale: history is evidence; spec-kit guardrail adopted verbatim.* Origin: 071 guardrails.
- **C6 · MUST — Human gate on canonical transitions.** Merges to main, releases, no-issue declarations, record→issue promotion adoption, and constitution amendments require explicit human approval; agents propose, humans adopt. *Rationale: the agent must not be able to launder its own approvals.* Origin: 075 (identity-gated declarations), practiced across PRs #7–#10.
- **C7 · SHOULD — Model-tier dispatch.** Judgment (scope, authorship, synthesis, user communication) stays in the main loop; mechanical implementation, research sweeps, and independent verification dispatch to cheaper tiers, named explicitly per dispatch. *Rationale: reserve the expensive tier for what needs it; verification stays independent of implementation.* Origin: 067 convention (2026-07-05), practiced in 075/071/072 waves.
- **C8 · MUST — Single parser per artifact.** Each artifact format is parsed in exactly one place; every consumer uses that parser's output. *Rationale: dual validators diverge (OpenSpec #498).* Origin: 071 GC1; `linkage_check`/`project_converge` practice.
- **C9 · SHOULD — Korean sidecar for new human-facing artifacts.** New specs/packets ship a `.ko.md` sidecar; English stays canonical; missing sidecars fall back, never gate. *Rationale: the first review surface for the Korean-speaking human.* Origin: 049 convention.
- **C10 · MUST — Commit↔issue linkage for behavior changes.** Behavior-affecting work happens on `codex/<issue-id>*` branches or carries an `Issue: <id>` trailer; the release gate enforces, the Stop hook warns in-session. *Rationale: 074's silent threshold crossing must stay impossible.* Origin: 075 linkage convention + 072 warning.
- **C11 · SHOULD — No silent caps.** Any truncation, sampling, or bound in a tool's output reports itself explicitly (`truncated` fields, dropped-count lines). *Rationale: silent truncation reads as full coverage.* Origin: 071 evidence bundles; 075 review practice.

## Amendment log

| Date | Version | Change | Proposer | Approver (human) |
| --- | --- | --- | --- | --- |
| 2026-07-07 | v1.0 | Initial ratification — 11 principles extracted from practiced law (075/071/072 plan GCs; 067/049/060 conventions) | Claude (agent) | Dongwon Lee (merge approval of PR #11, 2026-07-07: "비준하고 병합합시다") |
