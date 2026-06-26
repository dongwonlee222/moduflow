# ModuFlow Roadmap

## Now

Business document workflow after project memory: make ModuFlow produce decision-ready business documents with sources, assumptions, calculations, validation, exports, memory, and small-team execution workflows.

Active goal: `business-document-workflow`

### `034-memory-capture-and-sync-workflow`

- Outcome: ModuFlow can suggest, approve, store, retrieve, and mirror durable project memories while keeping full deliverables separate from memory summaries.
- Reason: The memory prototype works, but users need clear save triggers, a reviewable capture flow, search/retrieval behavior, and Google Drive or similar mirror options that do not replace Git as the source of truth.
- Confidence: high
- Dependency: project memory layer, business document workflow, artifact schema gates, and external memory pattern review
- Next command: `product:review 034-memory-capture-and-sync-workflow`
- Status: implementation complete; review needed before release/versioning.

### `035-team-issue-branch-pr-workflow`

- Outcome: Small teams and TFs can create, assign, start, review, and complete work through ModuFlow while developers use Git branches and PRs underneath.
- Reason: PMs should be able to run team work in natural language, while developers need deterministic issue, branch, PR, review, and memory-capture state.
- Confidence: high
- Dependency: Git binding, intake-to-goal graph, worker routing, artifact validation, and memory candidate workflow
- Next command: `product:status`
- Status: complete and versioned as 0.2.14.

### `036-portfolio-team-dashboard`

- Outcome: Portfolio dashboards show each project's active work, review queue, blockers, and next command from project-local state.
- Reason: Small teams and TFs need a cross-project 현황판, not only per-project team state.
- Confidence: high
- Dependency: team issue branch PR workflow
- Next command: `product:status`
- Status: complete and versioned as 0.2.15.

### `033-business-document-workflow`

- Outcome: ModuFlow business documents become project-local, source-backed, decision-ready artifacts, starting with market-entry analysis.
- Reason: Users need more than issues; project work also needs durable deliverables, decisions, calculations, validation results, and polite executive-report style.
- Confidence: high
- Dependency: project memory layer and business-plan skill
- Next command: `product:status`
- Status: review complete, with skill routing, templates, test artifact, validation, and local plugin cache deployment in place.

### `032-multi-language-goal-benchmarking-and-core-mcp-server-integration`

- Outcome: Extend benchmarking with English-to-Korean translation and build light MCP server layer.
- Reason: Reduce terminal command execution friction and support multi-lang insights.
- Confidence: high
- Dependency: 031-goal-driven-autonomous-benchmarking-and-issue-generation
- Next command: `product:status`
- Status: complete.

### `031-goal-driven-autonomous-benchmarking-and-issue-generation`

- Outcome: AI agent can autonomously search, benchmark, and generate structured issues from a high-level goal.
- Reason: Enable self-driven product design and issue tracking.
- Confidence: high
- Dependency: none
- Next command: `product:status`
- Status: complete.

### `025-lightweight-project-adoption`

- Outcome: Normal projects adopt ModuFlow in light mode with only state and PM artifacts in the project; tool commands, scripts, skills, and templates stay central.
- Reason: The current dogfooding repo shape makes ModuFlow feel too invasive when users imagine applying it to every project.
- Confidence: high
- Dependency: project migration/profile flows and artifact schema gates
- Next command: `product:status`
- Status: complete.

### `026-simplify-command-and-folder-surface`

- Outcome: Users see a small default command/folder model first, with advanced internals available only when needed.
- Reason: Many folders and commands are maintainable internally but uncomfortable as the first user experience.
- Confidence: high
- Dependency: simple loop UX and `/moduflow` hub command
- Next command: `product:status`
- Status: complete.

### `027-reduce-approval-popup-friction`

- Outcome: Approval prompts become predictable, batched where possible, and routine validation can run through importable/tool-call paths instead of repeated shell prompts.
- Reason: Repeated prompts during Git/GitHub cleanup and validation checks make otherwise normal workflows feel noisy.
- Confidence: medium
- Dependency: Git binding and doctor/preflight checks
- Next command: `product:status`
- Status: complete.

### `028-real-subagent-execution-backend`

- Outcome: Worker plans can dispatch safe independent tasks to real host-provided subagents when available.
- Reason: Static worker plans are useful, but host environments such as Antigravity may support actual parallel coding agents.
- Confidence: medium
- Dependency: worker routing/isolation and host API verification
- Next command: `product:status`
- Status: complete.

### `029-antigravity-artifact-sync-connector`

- Outcome: Antigravity-native artifacts and ModuFlow Git artifacts stay synchronized without duplicate writing.
- Reason: Duplicate `task.md`/`implementation_plan.md` and ModuFlow issue/spec/status files fragment the record.
- Confidence: medium
- Dependency: artifact schema gates and host artifact model verification
- Next command: `product:spec 029-antigravity-artifact-sync-connector`

### `030-project-memory-layer`

- Outcome: Projects manage portable long-term memory for deliverables, decisions, evidence, operating context, and reusable project context, not only issues.
- Reason: ModuFlow's current `knowledge/` layer is initialized but passive; each project needs a durable `memory/` model that can register, search, and retrieve project artifacts and decisions over time while staying self-contained when the project is moved.
- Confidence: high
- Dependency: knowledge evidence layer migration, artifact schema gates, and personal-memory contract review
- Next command: `product:spec 030-project-memory-layer`
- Status: prototype available; full spec and knowledge migration path still open.

## Backlog / Existing Capabilities

### `024-artifact-schema-and-doctor-gates`

- Outcome: Doctor validates artifact relationships, state drift, Git binding, intake records, worker plans, and next-command consistency, not only file existence.
- Reason: A richer loop model needs stronger consistency checks.
- Confidence: high
- Dependency: loop state from 019, Git binding from 021, intake routing from 022, and worker routing from 023
- Next command: `product:status`

### `023-worker-routing-and-isolation`

- Outcome: Worker assignment and parallel execution are now deterministic, file/dependency aware, and sequential by default when unsafe.
- Reason: Workers should help only when work can be safely split and merged.
- Confidence: high
- Dependency: Git binding from 021 and intake routing from 022
- Next command: `product:status`

### `022-intake-to-goal-graph`

- Outcome: Loose requests classify into active issue attachment, new issue candidates, goal graph candidates, or inbox routing records.
- Reason: This is the main product value beyond Spec Kit and coding agents.
- Confidence: high
- Dependency: simple UX from 020 and goal graph from 019
- Next command: `product:status`

### `021-git-binding-and-execution-backend`

- Outcome: Issues and loop steps are tied to branches, commits, PRs, releases, and optional execution backends such as Copilot Cloud Agent, Codex, Claude Code, OpenHands, or manual work.
- Reason: ModuFlow should orchestrate execution rather than compete with coding agents.
- Confidence: high
- Dependency: loop state model from 019
- Next command: `product:status`

### `020-user-facing-simple-loop-ux`

- Outcome: Simple aliases shipped for `상태`, `다음`, `이거 해줘`, and guarded `완료` while preserving direct `product:*` commands.
- Reason: Internal loop complexity must not increase user complexity.
- Confidence: high
- Dependency: loop state model from 019
- Next command: `product:status`

### `019-loop-kernel-and-state-model`

- Outcome: Durable goal-loop state model shipped for Goal 1:N Issue, active cursor, attempts guard, and drift-aware validation.
- Reason: This is the core foundation for making ModuFlow a PM loop orchestrator instead of a collection of workflow commands.
- Confidence: high
- Dependency: current artifact tracking and doctor gates
- Next command: `product:status`
