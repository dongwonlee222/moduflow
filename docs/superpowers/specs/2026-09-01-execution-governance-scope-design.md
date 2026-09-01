# Execution Governance Scope Design

**Date:** 2026-09-01  
**Status:** approved scope; implementation specs/plans remain issue-local  
**Owner:** Dongwon Lee  
**Evidence:** `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`

## Outcome

Keep ModuFlow lightweight by making it the canonical management and execution-governance layer, while delegating actual implementation to one selected host/Superpowers execution path and keeping Spec Kit optional and read-only.

## Ownership Boundary

| Layer | Owns | Must not own |
| --- | --- | --- |
| ModuFlow | issue/spec/plan/tasks truth, project context, routing decision, lifecycle/review state, approval evidence, roadmap | agent runtime, duplicate implementation loop |
| Spec Kit adapter | optional `clarify`, `checklist`, `analyze`, `converge` advice | `implement`, Git, lifecycle, review approval, release |
| Superpowers SDD | TDD, bounded task execution discipline, implementation/review loop | canonical product state or roadmap |
| Codex/Claude/Copilot host | actual tools, subagents, worktrees/sessions, runtime lifecycle | independent product truth |

## Decomposition

### Issue 112 — planner and backend boundary

One deliverable: a trustworthy execution-routing contract. It filters canonical tasks to concrete unfinished implementation work, refuses unusable worker plans, and selects exactly one `inline` or `superpowers-sdd` path without dispatching it.

### Issue 113 — review lifecycle and exception approval

One deliverable: a durable review state machine. It separates code completion, pending review, required fixes, explicit approval, and verified merge, and records a scoped human exception before extra remediation rounds.

### Issue 114 — Spec Kit 1.x compatibility

One deliverable: a reviewed adapter refresh. It compares and pins only the four allowed templates after exact-version compatibility and safety verification.

## Data Flow

1. ModuFlow reads canonical issue/spec/plan/tasks artifacts.
2. Issue 112 produces one host-neutral execution-routing result.
3. The selected host executes inline or maps the result to Superpowers SDD.
4. Execution evidence returns to ModuFlow without independently mutating canonical completion state.
5. Issue 113 advances review state only with matching evidence and approval.
6. Spec Kit may advise at approved validation points but never executes or advances state.

## Error and Safety Rules

- No concrete executable task boundary means `needs_plan`, not a guessed worker plan.
- Simple or shared-context work yields `inline`, not forced delegation.
- Unavailable host capability yields a truthful fallback with no execution claim.
- Reviewer findings cannot be suppressed by the coordinating executor.
- Approval and merge require distinct evidence.
- Spec Kit stays disabled/unavailable-safe and version/hash pinned.
- Issue 103 owns atomic state projection and recovery.

## Roadmap Integration

- Finish active Issue 103 first.
- Keep Issue 111 parallel and required before the next plugin release.
- Run Issue 112 before Issue 104 so the request orchestrator consumes the new boundary.
- Run Issue 113 after Issues 103 and 112.
- Run Issue 114 after Issue 112 without blocking ordinary ModuFlow releases unless that release claims the refreshed adapter.
- Leave Issue 084 as a later prompt-budget optimization rather than expanding Issue 112.

## Self-Review

- No placeholders or unresolved ownership decisions remain.
- The three issues each produce an independently testable deliverable.
- No new scheduler, queue, execution backend, or full Spec Kit lifecycle is introduced.
- The benchmark supports the architecture direction while explicitly limiting its conclusion to current official product guidance.
