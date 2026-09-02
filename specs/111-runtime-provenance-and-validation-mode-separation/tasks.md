# Tasks: Runtime Provenance and Validation Mode Separation

Issue: `111-runtime-provenance-and-validation-mode-separation`
Owner: Dongwon Lee
Source: `spec.md`, `plan.md`, 2026-09-02 planning and simulation request.
Phase: plan review; no implementation tasks completed.
Next command: `product:review 111-runtime-provenance-and-validation-mode-separation` (spec/plan review).

This is the progress checklist for the canonical plan, not a second implementation design. Execute inline without subagents; review once per stream, not once per edit.

## Review Gate

- [ ] Review and approve the written spec/plan before behavior implementation; do not infer implementation approval from document creation.

## Stream A — Shared Evidence and Explicit Validation Modes

- [ ] RED/GREEN the shared package reader, startup snapshot and explicit unknown evidence reasons.
- [ ] Add explicit source/installed modes, backward-compatible auto mode and strict source release role checks.
- [ ] Retain runtime assets/fixtures and every existing source gate; reject invalid metadata and runtime omissions.
- [ ] Verify focused tests and commit the reviewed contract changes with Issue 111 linkage.

## Stream B — Package Receipt and Cache Preservation

- [ ] RED/GREEN the injected-runner provenance builder and atomic receipt writer.
- [ ] Prepare and validate packages before exposure; preserve existing cache on write/rename failure.
- [ ] Reuse identical validated packages; reject conflicting same-version payloads without overwriting.
- [ ] Classify package-maintenance writes, update installer fixtures, verify and commit.

## Stream C — Doctor, Status and Persistent MCP

- [ ] RED/GREEN Doctor/MCP early target-role guard, including empty project and source dogfooding cases.
- [ ] Add the same process-scoped runtime provenance to status/Doctor success and error responses.
- [ ] Retain one startup snapshot per persistent MCP; distinguish old process, new process and unknown host skill loading.
- [ ] Preserve Issue 065 soft inventory/staleness diagnostics and recommendations without claiming active runtime.
- [ ] Verify two-project isolation, payload compatibility, command wording and focused tests; commit.

## Stream D — Simulations, Review and Release Evidence

- [ ] Run S01–S12: source, installed, stale, missing/invalid metadata, mismatched source/runtime, wrong target, two projects, separate worktree, interrupted installation and no-write/no-network behavior.
- [ ] Run packaged CLI/MCP smoke without source imports; verify repeated requests and exact executing package path.
- [ ] Run focused/full tests, artifact validation, lifecycle drift, source release gates and diff checks; record actual results.
- [ ] Review AC1–AC8 and resolve required findings; prepare release/rollback evidence.
- [ ] Following explicit publication approval, distinguish remote integration, publication, installed metadata and actual Codex/Claude observations R01/R02. Unknown host evidence stays unavailable, not passed.

## Deferred Beyond 111

Project-material retrieval/company standards/UI simulations belong to 090/091/086/092. Execution-boundary reduction belongs to 112; automation runner integration remains later. These are not hidden completion gates for this issue.
