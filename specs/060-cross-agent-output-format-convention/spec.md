# Spec: Cross-Agent Output Format Convention

Issue: `060-cross-agent-output-format-convention`
Prev: `048-artifact-lifecycle-sync`, `059-auto-fetch-in-repo-sync` · Next: `product:execute 060`

## Problem

Antigravity, Claude Code, and Codex each write ModuFlow artifacts and chat-facing status output in their own improvised style. This isn't cosmetic: issues `001`–`040` were written across sessions/agents using at least three incompatible status conventions (`## Lifecycle / Phase: word`, no status field at all, and the `**Status: word** — created...` inline convention from `048`), and `project_lifecycle.py`'s parser only recognizes the last one — silently misreporting ~20 already-completed issues as `backlog`. Nothing tells an agent *how* to format a given kind of content, so each one invents its own, and drift compounds.

## Users

- The user reading agent output across three tools in the same project and having to re-learn each one's conventions.
- Future agent sessions (any of the three) writing a new issue/spec/status update, needing a single reference for format decisions instead of improvising.
- `project_lifecycle.py` and other tooling that parses artifact text — consistent format is what makes parsing reliable in the first place.

## Goals

- One project-root `AGENTS.md` that Antigravity (v1.20.3+), Claude Code, and Codex CLI all read natively, with no connector or sync step (confirmed in `knowledge/benchmarks/2026-07-05-cross-agent-output-format-benchmark.md`).
- Codify a **situation → shape** mapping instead of picking one winning visual style — each of the three tools' current styles is well-suited to a specific situation, not to the tool itself.
- Capture the two structural habits and one spacing habit all three already share by instinct, so they're explicit instead of accidental: bottom-line-first, label-before-explain, and deliberate whitespace rhythm (loose vs tight lists, blank-line/`---` separation between unrelated blocks or before a closing recommendation).

## Non-Goals

- Migrating legacy issues `001`–`040` to the current `Status:` schema. This doc prevents new drift; it does not retroactively fix old files. Track separately if wanted.
- Artifact-to-artifact sync or source-of-truth rules between Antigravity's native files (`task.md`, `implementation_plan.md`) and ModuFlow's Git files — that is `029-antigravity-artifact-sync-connector`'s scope.
- Korean/English tone or language rules beyond what `049-bilingual-artifact-view` and `057-korean-human-review-packet` already define.
- Forcing one single visual style across all output — the situation → shape table is the point; a snapshot, a decision list, and a done-confirmation are different situations and should look different.

## Requirements

1. Create `AGENTS.md` at the moduflow project root containing:
   - The situation → shape table (snapshot → box/table; N-item decision → list + badges + recommendation + question; already-done confirmation → flat labeled sections, no question).
   - The whitespace-rhythm rules: blank line after headers; loose list when items carry nested/multi-line content, tight list when items are flat single-line facts; extra blank line or `---` between unrelated sections and before a closing recommendation/question.
   - A worked before/after example using the `001`–`040` status-field drift.
2. `docs/host-adapter-guidance.md` gets a short pointer to `AGENTS.md` for format questions, rather than restating format rules — it keeps its existing approval-flow/shell-behavior scope.
3. No changes to legacy issue files, `project_lifecycle.py` parsing logic, or any artifact schema — this issue is output-format guidance only.

## Alternatives Considered

- **`docs/output-format-convention.md`** (original draft target): rejected once the benchmark confirmed Antigravity natively reads `AGENTS.md` as of v1.20.3 — a `docs/` sub-page would need each tool's entry point to separately link it, reintroducing the "three separate places to update" problem this issue exists to remove.
- **One single mandated visual style** (e.g., always use tables): rejected — the benchmark shows each observed style is well-matched to its situation; forcing one style would make status snapshots and completion confirmations harder to read, not easier.

## Acceptance Criteria

- `AGENTS.md` exists at the project root with the situation → shape table, the whitespace-rhythm rules, and the before/after example.
- `docs/host-adapter-guidance.md` links to `AGENTS.md` instead of restating format rules.
- `python3 scripts/release_check.py .` passes.

## Risks

- A convention doc only helps if agents actually read it before writing; `AGENTS.md` mitigates this for the three tools in scope by being the file they read natively rather than a doc that must be remembered.
- Over-specifying visual style could reduce agents' ability to adapt to genuinely novel situations not covered by the three named shapes. Mitigation: the doc states the *reasoning* (situation → shape, not just examples) so it generalizes.

## Open Questions

- Whether `GEMINI.md` (Antigravity's higher-priority override file, per the benchmark) should also get a pointer to `AGENTS.md` to guarantee it isn't shadowed. Deferred — no `GEMINI.md` exists in this repo today; revisit if one is added.

## Next Command

`/product:execute 060-cross-agent-output-format-convention`
