# Issue: `060-cross-agent-output-format-convention`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.

## Outcome

A project-root `AGENTS.md` that Antigravity, Claude Code, and Codex all read natively (no connector needed as of 2026 — see benchmark) before writing ModuFlow artifacts (issues, specs, plans, PR/review notes, commit messages) and chat-facing status output — so numbered lists vs bullets vs tables vs checklists vs inline `key: value` lines are chosen by *situation*, the same way regardless of which agent wrote them.

Benchmark: `knowledge/benchmarks/2026-07-05-cross-agent-output-format-benchmark.md`.

## Why

Issue 059's session surfaced a concrete failure mode of *not* having this: issues `001`–`040` were written across different sessions/agents using at least three different status schemas (`## Lifecycle / Phase: word`, no status field at all, and the current `**Status: word** — created...` inline convention from issue 048). `project_lifecycle.py`'s parser only recognizes the newest convention, so it silently misreports ~20 already-completed issues as `backlog`. The root cause isn't the parser — it's that nothing tells each agent *how* to format a given kind of content, so each one improvised independently.

The user separately asked (2026-07-05) to make Antigravity, Claude Code, and Codex communicate the same way — specifically calling out list style (numbered vs bulleted) as the example. Scoped to **output formatting only** for this issue; artifact schema fields (Status/Phase, etc.) and cross-tool artifact sync are `029-antigravity-artifact-sync-connector`'s concern, not this one.

## Scope

- A project-root `AGENTS.md`, read natively by all three tools (Antigravity ≥ v1.20.3, Claude Code, Codex CLI — confirmed in benchmark), covering a **situation → shape** table rather than one fixed style:
  - fixed-field snapshot → box panel / table
  - N comparable items needing a decision → numbered/bulleted list with inline status badges + closing recommendation + question
  - task already done, reader just confirms → flat labeled sections, no closing question
  - shared baseline regardless of situation: bottom-line-first, label-before-explain, deliberate whitespace rhythm
- `docs/host-adapter-guidance.md` gets a pointer to `AGENTS.md` (it already contains one shape example — the Resume Banner — that should be cited, not duplicated).
- A short "before" / "after" example using the 001–040 status-field drift as the worked example.

### Out

- Migrating the ~20 legacy issues (001–040) to the current `Status:` schema — that's cleanup work this doc would prevent going forward, not retroactively fix. Track separately if wanted.
- Artifact-to-artifact sync/source-of-truth rules between Antigravity's native files and ModuFlow's Git files — that's `029-antigravity-artifact-sync-connector`.
- Tone/language rules (Korean vs English) beyond what `049-bilingual-artifact-view` and `057-korean-human-review-packet` already define.

## Acceptance Criteria

- `AGENTS.md` exists at the moduflow project root with the situation → shape table and concrete before/after examples, not just abstract rules.
- `docs/host-adapter-guidance.md` links to it instead of restating format rules.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `029-antigravity-artifact-sync-connector` (artifact *source-of-truth* sync, not formatting)
- related: `048-artifact-lifecycle-sync` (introduced the `Status:` convention this issue generalizes)
- caused-by: `059-auto-fetch-in-repo-sync` (session where the schema-drift symptom was found)

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/060-cross-agent-output-format-convention/spec.md`
- [x] execute → `AGENTS.md`, `docs/host-adapter-guidance.md`

## Sessions

- 2026-07-05: Captured from a `product:status` session that found ~20 issues misclassified as `backlog` due to inconsistent status-field conventions across agents/sessions; user asked to unify output format across Antigravity/Claude/Codex, scoped to format rules only (not artifact schema/sync).
- 2026-07-05: User pointed out the Antigravity example's whitespace/line-break rhythm was deliberate, not incidental — benchmark and spec updated to include loose/tight list and `---`-separation rules before writing `AGENTS.md`.
- 2026-07-05: Wrote `AGENTS.md`, linked it from `docs/host-adapter-guidance.md`, verified with `release_check.py`. Done.

## Links

- Roadmap: `workspace/roadmap.md`
- Benchmark: `knowledge/benchmarks/2026-07-05-cross-agent-output-format-benchmark.md`
- Spec: `specs/060-cross-agent-output-format-convention/spec.md`
- Deliverable: `AGENTS.md`

## Next Command

`/product:status`
