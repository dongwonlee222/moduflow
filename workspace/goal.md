# Goal: ModuFlow Visual Workbench

## Objective

Move ModuFlow from a chat-driven workflow toward a visual workbench: see and (eventually) act on issues, their relationships, memory, and work direction through a node graph — while keeping Git-native Markdown as the canonical source of truth.

## Owner

Dongwon Lee

## Information architecture (the target this goal serves)

The vision is the L0–L3 drill-down already documented in `docs/visual-workbench-and-planning-harness.md`:

```
L0 portfolio   project cards (state, next action)          ← 036
L1 project     goal + issue graph + memory graph           ← per-project
L2 issue       its spec / benchmark / scenario / IA / journey / screens / diagrams + history
L3 memory      decision graph (why, evidence, deliverables) ← 042
```

Memory and specs are already **per-project** by construction: `memory/` and `specs/` are repo-local, `project_memory.py` takes a `<project-path>`, and portfolio (036) rolls up across projects. The gap is L2 (per-issue artifact drill-down) and the artifacts themselves.

## Work axes (the cluster, organized)

Three axes, not a single linear ladder. Issues belong to an axis, not a step number.

**Axis A — View (show it)**
- `042-decision-graph-dashboard` ✅ done — memory graph (Cytoscape from `memory/` frontmatter).
- `044-product-dashboard-command` ✅ done — `product:dashboard` / `/moduflow 그래프`, ModuFlow-native, `dashboard.html` is `.gitignore`d/derived. Routed in `moduflow.md` + `skills/index/SKILL.md`.
- `045-issue-graph-visualization` ✅ done — grew into the **L1 project view**: two-tab 이슈 그래프 + 지식 그래프, cross-linked via `issue_id`, goal-box grouping, detail panels for both. Spun off `049` (Korean artifact bodies).
- `047-issue-artifact-drilldown` ✅ done — L2 panel: `product:dashboard --issue <id>` → `memory/issue-<id>.html`. Shows only artifacts that exist; never forces empty sections. All-CDN (`marked`+`mermaid`, zero Python dep).

**Axis B — Data quality (have something worth showing)**
- `043-memory-relationship-capture-prompts` ✅ done — write-time relationship capture: `--list-ids` candidates, command-doc capture step, `project_doctor` isolated-node soft hint. Guided, never auto-inferred (042's anti-goal).

**Axis C — Planning-artifact depth (selective, not forced)**
- `046-planning-artifact-templates` ✅ done — enhanced `product:spec` template with clarify-first + required Non-Goals/Alternatives + default Mermaid + pipeline pointers; dogfooded via `specs/046/spec.md` (core 3 first). Heavier artifacts (scenario/IA/journey/screens) deferred, demand-driven.

**Later — Write/Execute (interactive workbench)**
- Create/edit issues and direct work from the UI. Crosses the static-file boundary, needs a running backend. Depends on `021-git-binding-and-execution-backend`, `028-real-subagent-execution-backend`. Front-end approach (chat-backed vs standalone) deferred — see Open Questions.

**Cross-cutting — Lifecycle sync (not an axis, but blocks trust in all views)**
- `048-artifact-lifecycle-sync` ✅ done — issue `Status:` is canonical; `project_lifecycle.py --sync` propagates to `state.json`/`dashboard.md`; consensus drift is a hard gate; legacy `loop-state.json` retired from the gate. Keeps views honest automatically.

## Suggested order

`046` ✅ → `047` ✅ → `045` ✅ → `043` (relationship data — fills 045's sparse cross-links). `048` (lifecycle sync) + `049` (Korean artifact bodies) run alongside. Views are now built; `043` makes them rich.

## Completion Criteria

- Memory and issue graphs are viewable through a ModuFlow command (not a chat-client-only skill).
- Issue relationships render with status color and edge semantics.
- An issue's planning artifacts (those that exist) are viewable in one L2 drill-down, per project.
- Planning-artifact templates are strong enough that a PM reaches for them when an issue warrants depth — without being forced to fill them on every issue.
- A decided, staged path exists for interactive authoring without breaking the Git-native artifact model.

## Constraints

- Git-tracked Markdown stays canonical — any future authoring UI writes back to `.md`, never a side store.
- Read stages stay zero-backend (Python-generated static HTML + CDN render lib).
- Interactive/execution stages reuse, not bypass, existing execution-backend work (`021`, `028`).

## Open Questions

- Interactive front-end: **(A)** chat-backed visual surface (sendPrompt-driven, works today, Claude-client only) vs **(B)** standalone app with its own backend (true "not chat", weeks+). Recommendation: validate with (A) before committing to (B).
- Issue relationship source for stage 3: brittle "Related Issues" text parsing vs giving issues frontmatter (artifact-model schema change — separate decision).

## Budget

- Stages 1-3 are cheap (Python + CDN render). Stage 4 is a separate project-scale effort, gated on proven value from (A).
