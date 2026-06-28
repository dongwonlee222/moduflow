# Goal: ModuFlow Visual Workbench

## Objective

Move ModuFlow from a chat-driven workflow toward a visual workbench: see and (eventually) act on issues, their relationships, memory, and work direction through a node graph — while keeping Git-native Markdown as the canonical source of truth.

## Owner

Dongwon Lee

## Stages (read cheap first, write/execute later)

1. **Read — memory graph** ✅ done (`042-decision-graph-dashboard`)
   Cytoscape dashboard generated from `memory/` frontmatter.
2. **Read — dashboard command** ✅ done (`044-product-dashboard-command`)
   ModuFlow-native invocation (`product:dashboard` / `/moduflow 그래프`), not a Claude-only skill. Generates `dashboard.html` (`.gitignore`d, derived); renders in chat when a visualization MCP is present. Routed in both `moduflow.md` and `skills/index/SKILL.md`.
3. **Read — issue graph** (`045-issue-graph-visualization`)
   Do for issues what 042 did for memory: nodes = issues, edges = supersedes/related/depends, color = status.
4. **Write/Execute — interactive workbench** (later; depends on execution backend)
   Create/edit issues and direct work from the UI. This crosses the static-file boundary and needs a running backend. Depends on `021-git-binding-and-execution-backend`, `028-real-subagent-execution-backend`. Front-end approach (chat-backed vs standalone app) deferred — see Open Questions.

## Completion Criteria

- Memory and issue graphs are viewable through a ModuFlow command (not a chat-client-only skill).
- Issue relationships render with status color and edge semantics.
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
