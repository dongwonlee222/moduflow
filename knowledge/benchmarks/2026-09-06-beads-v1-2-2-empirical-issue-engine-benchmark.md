---
kind: benchmark
title: Beads v1.2.2 empirical issue-engine benchmark
issue_id: 112-execution-planner-and-backend-boundary
spec: specs/112-execution-planner-and-backend-boundary/spec.md
decision_supported: Beads issue-engine adapter shadow pilot versus native implementation
date: 2026-09-06
confidence: high for local single-checkout behavior; low for multi-machine/server behavior
sources:
  - https://github.com/gastownhall/beads
  - https://github.com/gastownhall/beads/releases/tag/v1.2.2
  - knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md
  - knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md
  - workspace/inbox.md
---

# Beads v1.2.2 empirical issue-engine benchmark

## Why This Benchmark Exists

ModuFlow already identified Beads as a reference in the 2026-07-05 competitive
gap benchmark, but that comparison was based on product surfaces and public
documentation. It did not establish whether Beads actually prevents the failure
now observed in ModuFlow: two people can start the same issue and the second
transition silently overwrites `assignee` and `locked_by` in
`workflow/team-state.json`.

This benchmark measures the executable behavior before deciding whether to build
another claim/queue subsystem inside ModuFlow. The decision is not “keep or delete
ModuFlow”; it is which layer should own issue identity, dependency state, ready
queries, and atomic claims while ModuFlow retains product context and gates.

## Test Scope and Environment

| Field | Value |
|---|---|
| Date | 2026-09-06 |
| Host | macOS Darwin, arm64 |
| ModuFlow | source/cache `0.3.67`; 131 Git-native issues |
| Beads | official `v1.2.2`, commit build `6c124203e` |
| Beads asset | `beads_1.2.2_darwin_arm64.tar.gz` |
| SHA-256 | `2aa1245c666419900d2d6993a05049e92c40e0e601d19579cca5b07a7bb8021d` — matched official checksum |
| Isolation | separate temporary Git repository; no ModuFlow repository migration |
| Storage mode | embedded Dolt with task-local `DOLT_ROOT_PATH` |
| Test data | one epic, four child tasks, three blocking edges, one persistent memory |

No system-wide Beads installation or production ModuFlow data conversion was
performed. The trial used a separate repository and manually disabled metrics for
test commands.

## Scenarios and Observed Results

| Scenario | Expected | Observed | Verdict |
|---|---|---|---|
| Initialize a Git project | Create a usable local issue store | Embedded Dolt initialized; Beads created a Git commit | pass, with side effect |
| Parent/child issue graph | Preserve epic hierarchy | Child IDs `mftrial-dj2.1` through `.4` linked to epic | pass |
| Blocking dependencies | Hide a task until all blockers close | Regression task absent from `bd ready` until three blockers closed | pass |
| Atomic claim | Exactly one of two actors claims the same issue | Minsu succeeded; Jisu failed with `issue already claimed by Minsu` | pass |
| Automatic next-work claim | Select one ready non-epic task | `bd ready --claim --exclude-type epic` assigned the regression task to Jisu | pass |
| Persistent project memory | Store and inject one operating rule | `bd remember` value appeared in `bd prime --memories-only` | pass |
| Interchange export | Export issues and memory | Five issues and one memory exported to JSONL | pass, not a backup |
| Embedded diagnostics | Run a health check | `bd doctor` reported that embedded mode is unsupported | gap |
| Restricted-home initialization | Fail safely when user config cannot be written | Attempt to create `~/.dolt` failed and the process panicked | fail-safe gap |

### Atomic-claim evidence

Two independent processes attempted the same claim concurrently using different
actors.

```text
Minsu: exit 0, status=in_progress, assignee=Minsu
Jisu:  exit 1, Error claiming mftrial-dj2.2: issue already claimed by Minsu
```

The equivalent ModuFlow transition probe did not reject the second actor. It
completed successfully and silently replaced Minsu with Jisu. The current
`team-state.json` lock is therefore a descriptive field, not an enforced claim
primitive.

### Dependency evidence

`mftrial-dj2.4` depended on three leaf tasks. Before they closed, it was excluded
from `bd ready`; immediately after all three closed, it appeared as ready and was
atomically claimable. This is the behavior ModuFlow needs for execution handoff,
without treating a shared `active_issue` pointer as the queue.

## Capability Comparison

| Capability | ModuFlow 0.3.67 | Beads 1.2.2 observed | Recommended owner |
|---|---|---|---|
| Product goal and rationale | Rich goal, opportunity, issue, spec and decision artifacts | Minimal issue fields | ModuFlow |
| Acceptance and release gates | Spec, evidence, review and release workflow | General issue status and dependencies | ModuFlow |
| Issue identity and history | Markdown files plus several projections | Hash/hierarchical IDs in versioned Dolt | Beads candidate |
| Dependency-aware ready query | Implemented from Markdown `blocked_by`, but tied to ModuFlow lifecycle projections | Native, machine-readable and directly claimable | Beads candidate |
| Atomic multi-actor claim | Not enforced; second start overwrites ownership | Concurrent claim allowed one winner | Beads candidate |
| Shared active-work model | One global `active_issue`, creating cross-user conflicts | Per-issue status and assignee; no global active pointer required | Beads candidate |
| Team status view | `team-state.json` is directly written and can drift | Queryable issue state | Derive ModuFlow view from backend |
| Agent/worktree execution | Worker planner contains worker/worktree/merge concepts and risks becoming a second runtime | Tracks work; does not replace the host runtime | Codex/Claude/Git host |
| Project memory | Broad taxonomy but no automatic ingestion path; many empty categories | `remember`/`prime` round-trip worked directly | Split: operating hints in Beads, durable product evidence in ModuFlow |
| Diagnostics | Strong project doctor and release checks | `bd doctor` unavailable in embedded mode | ModuFlow plus backend-specific checks |
| Cross-machine sync | Git-native Markdown is portable but shared state conflicts | Requires Dolt remote/server push/pull; JSONL is not source of truth | Unverified; pilot gate |

## Important Product and Operations Caveats

1. **Local concurrency is verified; distributed concurrency is not.** Embedded
   Dolt serialized two processes in one checkout correctly. Two computers,
   independent worktrees, remote divergence, and recovery were not tested.
2. **JSONL is not the database or backup.** Beads itself describes export as an
   interchange/viewer surface. Durable cross-machine operation requires Dolt
   remotes/backups and explicit push/pull discipline.
3. **The latest release is a recovery release.** The official v1.2.2 notes say
   v1.2.0 and v1.2.1 were accidentally published without release testing. v1.2.2
   re-releases the tested 1.1 line; work leases, events journal, sync federation,
   HTTP API, and provenance events from the accidental 1.2 line are not present.
4. **Initialization has global assumptions.** Without a writable home config,
   initialization attempted `~/.dolt` and panicked instead of returning a bounded
   error. Metrics opt-out also attempted `~/.config/bd`. The isolated test needed
   explicit environment containment.
5. **Ready policy needs a guard.** Default `bd ready` included the open epic as well
   as executable leaf tasks. Automated workers should exclude epic/decision types
   and select only implementation tasks.
6. **Initialization mutates Git.** `bd init` created a commit automatically. Adoption
   must run in a clean, reviewed branch rather than silently inside a working tree.

## Architecture Finding

The benchmark supports removing **execution-runtime ownership**, not removing
ModuFlow's product workflow.

ModuFlow should continue to own:

- intake, opportunity, goal, roadmap, spec and acceptance criteria;
- product decisions, evidence and durable project knowledge;
- implementation-readiness policy;
- review, release and stakeholder reporting;
- a host-neutral routing/handoff contract.

The selected issue backend should own:

- issue/task identity;
- dependency edges and ready queries;
- atomic claim and assignee state;
- task status history and close/reopen behavior.

The active host runtime should own:

- actual agent dispatch;
- worktree/process lifecycle;
- retries and cancellation;
- commit, PR and CI execution.

`scripts/worker_orchestrator.py` should therefore retain task extraction, file
boundary analysis, dependency checks and the `inline` versus external routing
decision. Worker ownership, worktree execution, waiting/retrying, and competing
completion state should not become another ModuFlow runtime. This matches Issue
112's explicit scope fence.

## Recommended Shadow Pilot

Do not migrate all 131 issues. Mirror ten active/backlog issues and test one full
operating cycle while keeping existing ModuFlow artifacts canonical.

### Required pilot scenarios

1. Stable ModuFlow ID ↔ Beads ID mapping.
2. Two people concurrently claiming the same issue.
3. Two independent issues claimed and completed in parallel worktrees.
4. Dependency unblock after close and re-block after reopen.
5. Two-computer Dolt push/pull with concurrent edits.
6. Remote outage, interrupted write and recovery.
7. PR/test evidence returned to the owning ModuFlow issue.
8. Dashboard/team view generated from backend state without writing another lock.
9. Rollback to native ModuFlow issue state without losing status history.
10. Version upgrade across every participating clone.

### Pass criteria

- zero duplicate claims;
- zero silent ownership overwrites;
- no unresolved state after concurrent push/pull;
- close/reopen and dependency state round-trip without loss;
- ModuFlow never claims implementation complete without commit/test/PR evidence;
- one authoritative writer for assignee and execution status;
- a documented, tested rollback path;
- acceptable installation, server and backup overhead for a small team.

### Stop criteria

- remote/server operation needs more maintenance than the native issue workload;
- recovery requires manual database repair in ordinary failure scenarios;
- IDs or lifecycle state cannot round-trip without dual authoritative writes;
- the adapter forces Beads-specific concepts into ModuFlow specs, decisions or
  release gates;
- release stability remains below the team's operating threshold.

## Decision Recommendation

Approve a bounded Beads adapter pilot behind Issue 112's host-neutral backend
boundary. Do not approve a full migration or a new ModuFlow scheduler. If the pilot
fails, keep the same architecture and implement only the missing native primitives:
per-issue atomic claim, multiple simultaneous active issues, dependency-aware ready
selection, and derived team projections.

## Retrieval Trigger

Re-read when deciding the Issue 112 execution boundary, replacing global
`active_issue`, changing `team-state.json`, selecting an issue backend, introducing
multi-user worktrees, or proposing a Beads migration.

## Decision Link

- Issue: `112-execution-planner-and-backend-boundary`
- Spec: `specs/112-execution-planner-and-backend-boundary/spec.md`
- Related prior benchmark: `knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md`
- Decision supported: Beads issue-engine adapter shadow pilot versus native implementation

## Next Action

- Record the backend ownership decision with `product:decision`.
- If approved, add the ten-issue shadow pilot as execution work under Issue 112 or
  a narrowly scoped successor rather than creating a second orchestration runtime.
