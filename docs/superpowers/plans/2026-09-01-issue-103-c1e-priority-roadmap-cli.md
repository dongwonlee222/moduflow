# Issue 103 C1e Priority Roadmap CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development inline. Do not use subagents.

**Goal:** Expose the already-planned conditional roadmap projection through the missing lifecycle transition `--priority` option.

**Architecture:** Add one optional keyword `priority=None` to `transition_lifecycle()`. Valid priorities `p0`–`p3` create `roadmap_change={"priority": priority}`; omission keeps `roadmap_change=None`, so roadmap target selection remains conditional. Add `--priority` as a transition-only CLI option and preserve all existing exit/result behavior.

**Tech Stack:** Python `argparse`, existing lifecycle adapter and transaction planner, `unittest`, `unittest.mock`.

## Constraints

- Preserve all current positional arguments and add only the keyword-only `priority` input.
- Reject values outside `p0`, `p1`, `p2`, and `p3` before engine dispatch.
- `--priority` without `--transition` exits `2` with zero mutation calls.
- No priority means no roadmap target and no roadmap file read/write.
- Do not add dependencies or begin C2/D1/D2/full release gates.

### Task 1: RED Adapter and CLI Tests

- [x] Add an adapter test proving `priority="p1"` creates exactly `roadmap_change={"priority": "p1"}` and omission creates `None`.
- [x] Add CLI tests proving `--priority p1` is forwarded, an unsupported priority exits `2`, and priority outside transition mode exits `2` before dispatch.
- [x] Run the named tests and confirm the current adapter/parser rejects or ignores the missing option.

### Task 2: Minimal Public Connection

- [x] Add `priority=None` to `transition_lifecycle()` and validate it against `p0`–`p3` before loading the engine.
- [x] Pass `roadmap_change={"priority": priority}` only when non-empty.
- [x] Add `parser.add_argument("--priority", choices=("p0", "p1", "p2", "p3"))`, include it in transition-only option detection, and forward it to the adapter.
- [x] Add a real planner assertion that priority selects roadmap while omission does not; preserve all unmanaged roadmap prose.

### Task 3: Verification and Completion

- [x] Run lifecycle, transaction, loop, and issue-schema focused suites plus compilation and `git diff --check` (310 focused tests passed).
- [x] Commit C1e code as `feat(103): expose roadmap priority transition` (`c71a543`).
- [x] Mark C1e and original C1 Steps 1–3 and 5 complete; leave C2/D1/D2 open.

## Completion Gate

- [x] Public Python and CLI priority paths reach one conditional roadmap target.
- [x] Invalid/out-of-mode priority values dispatch zero mutation calls.
- [x] No-priority lifecycle transitions retain their existing target set.
- [x] C1a–C1e collectively satisfy original C1; C2/D1/D2 remain unclaimed.
