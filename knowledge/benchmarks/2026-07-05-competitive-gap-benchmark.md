---
kind: benchmark
title: Competitive gap benchmark — trackers, spec workflows, plugin ecosystem
date: 2026-07-05
issue_id: ""
decision_supported: "post-benchmark backlog 068-073 prioritization"
sources:
  - https://github.com/MrLesk/Backlog.md
  - https://github.com/steveyegge/beads
  - https://github.com/eyaltoledano/claude-task-master
  - https://github.com/github/spec-kit
  - https://github.com/Fission-AI/OpenSpec
  - https://kiro.dev
  - https://github.com/anthropics/claude-plugins-official
  - https://github.com/obra/superpowers
---

# Competitive Gap Benchmark (2026-07-05)

Three parallel research passes (git-native/agent-native trackers; spec-driven workflows; Claude Code plugin ecosystem) compared against ModuFlow v0.3.6. Full findings summarized here; prioritization decided in the main session.

## Convergent gaps (priority order)

1. **Machine query surface** (trackers + plugin passes converged): `.mcp.json` registers nothing; `scripts/mcp_server.py` is a 2-tool stub; no `--json` flags anywhere on the `product:*` surface. Agents parse Korean ASCII dashboards or trigger Bash-approval prompts for pure reads. beads/Task Master/Backlog.md all treat JSON/MCP as the primary agent interface (beads `bd ready --json`; TM ships 36 MCP tools). → issue `068-machine-query-surface`.
2. **Flat issue data model**: no `blocked_by`/`blocks`, no priority, no complexity/estimate — "what can I start now" requires reading prose. beads' entire thesis (`bd ready`, atomic `--claim`, hash IDs); TM `next`/`clusters`. Close additively on markdown (fields, not a DB). → issue `069-issue-dependency-priority-model`.
3. **Consistency checks cover process, not content**: lifecycle drift gate compares state files; nothing validates spec↔plan↔tasks coherence pre-execution (spec-kit `/speckit.analyze`) or code↔spec convergence post-implementation (spec-kit `/speckit.converge`, OpenSpec `/opsx:verify` as archive gate). ModuFlow's own superpowers/spec-kit adapter notes flagged converge as unabsorbed. → issues `070-spec-consistency-analyze`, `071-spec-code-converge-check`.
4. **No hooks**: lifecycle propagation is remember-to-run (the exact failure mode 048 documented — dashboard silently stale across five issues). superpowers uses a SessionStart hook for context injection. → issue `072-lifecycle-hooks-automation`.
5. **No standing constitution/steering**: Global Constraints are re-authored per plan.md; spec-kit versions a constitution every pass checks against; Kiro steering adds glob-conditional auto-loading. → issue `073-project-constitution-steering`.

## Verified defects (fixed same day)

- `plugin.json`'s `interface` block is an unrecognized field (`claude plugin validate --strict`): displayName/category/logo all ignored by Claude Code — marketplace shows raw `moduflow`. Recognized top-level `displayName` was missing; `marketplace.json` lacked a top-level `description` and per-entry `category`.

## Deliberate non-adoptions (ModuFlow already ahead — all three passes concurred)

- Release-gate depth (release_check: tests/validation/lint/security/version/drift + pre-push hook + CI) — none of the six comparators ship enforced gates.
- Korean human-review packets as a release gate; bilingual sidecars.
- Dual-verdict review (spec compliance vs quality, read-only reviewers, no finding suppression).
- Model-tier worker orchestration (cognitive-demand routing).
- Artifact taxonomy beyond issues (decisions/benchmarks/research, goal→issue hierarchy, portfolio roll-up).

## Noted but deferred (no issue registered)

- spec-kit extensions/presets/bundles ecosystem; 30+ agent support matrix (ModuFlow intentionally targets Claude/Codex).
- OpenSpec delta-specs merging into a standing behavior corpus; cross-repo "Stores".
- Kiro SMT-based formal requirements analysis (research-grade; heuristic analyze in `070` first).
- Backlog.md drag-and-drop kanban web UI; beads-style compaction/memory-decay (revisit at 100s of issues); TM PRD auto-decomposition; per-task GitHub issue fan-out (`taskstoissues`); Task Master tag workstreams.
