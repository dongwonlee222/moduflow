# Review: Execution Planner and Backend Boundary

Issue: 112-execution-planner-and-backend-boundary

Twelve tasks, five required gates, all closed 2026-09-07.

## What shipped

Two new modules and one rewritten path. `scripts/execution_routing.py` holds the
three gates, typed gaps and divergence detection.
`scripts/execution_host_adapter.py` holds three host adapters and refuses a
fourth. `scripts/worker_orchestrator.py` consumes the routing result instead of
iterating checkboxes, writes nothing on a refusal, and no longer contains the
`codex/` prefix or any model name.

Commits `f6ba4c8` → `3119811`. `moduflow.worker-plan.v2`. Version 0.3.77.

## Did it work

- Corpus, 59 specs: 34 `not_applicable`, 21 `needs_plan`, 4 `ok`. 109 gaps, all
  `no_boundary`.
- §13's three named specs: 029 `ok`, 001 `needs_plan`, 023 `not_applicable`.
- Under `claude-code`: `project_root` `"."`, no `codex/`, no `gpt-5.6`, no
  `/Users/`. Under `codex`, the same spec yields `codex/029-…-t01`.
- 2056 tests, OK. `release_check` valid, 14 of 14.

The number that matters: **001's only open task was `Commit and push.`**, and it
was being handed a worktree, a prompt reading `Expected files: none`, and a
`dispatchable` verdict. It now refuses and writes nothing.

## What the twelve tasks actually cost

The split between building and connecting was not what the plan implied. T01–T08
built parts and touched nothing anyone used; **T09 was the whole change**, and it
alone rewrote a 567-line file and broke 23 existing tests across two files.

That ratio is worth remembering for the next issue shaped like this one: the
tasks that produce new modules are cheap and safe, and the single task that makes
them load-bearing carries all the risk. Splitting T09 and T10 would have left the
suite red between two commits, which is how a real regression gets waved through.

## Five things found and corrected mid-flight

- **The `codex/` prefix and model names were never in the routing result.** My
  T06 brief said to move them out of it. They were only ever in
  `worker_orchestrator.py`, the file T06 was forbidden to touch. So T06 built the
  destination and T09 did the removal. The agent said so rather than quietly
  doing something adjacent.
- **The dogfood test was rewritten twice by one mistake.** v1 pinned the literal
  task list, so recording progress broke it. v2 pinned status `ok`, and T12's own
  completion turned the honest answer into `not_applicable` — v2's failure
  message had predicted exactly that. A fixture that forbids the thing it
  measures from changing is not a fixture.
- **`issue_id` was required by §7 and never emitted.** A contract this issue
  wrote and did not meet. Fixed in T08 rather than filed: a missing field in your
  own current work is a bug in the work.
- **Three prompt-text assertions had to go.** They checked that every prompt
  contained `gpt-5.6-sol` — assertions that passed precisely while the behaviour
  was wrong. Replaced by exact per-host model records plus a guard that no model
  name reaches any prompt on any host. Stronger, not weaker; zero tests deleted.
- **Spec 023's v1-compatibility criterion is now false.** Struck through in place
  with the reason, rather than left as two specs disagreeing in silence.

## Known gaps

- **`unreadable_notation` has never fired.** Specs 103, 109 and 110 are why the
  distinction exists, and all three are unreachable through the gates — two have
  every task checked, one has no `tasks.md`. The fixture is synthetic. Recorded
  in `status.md`; the same shape as issue 120's `unreadable` reason.
- **T07 proves less than the design doc claims.** The doc says the canonical
  artifact is byte-identical across three hosts. `worker-plan.json` necessarily
  differs — it carries the host record. What T07 proves is the precondition: the
  routing result is unchanged after each adapter runs, and one input yields three
  distinct host records. The doc's sentence should be read as scoped to the
  routing result; §9 names the canonical three as `spec.md`, `plan.md`,
  `tasks.md`.
- **Adapter vocabulary is unverified per host.** The adapters separate cleanly.
  Whether `opus` is the right `deep` model for Claude Code, or whether Copilot
  truly has no isolation control, rests on one day's research.
- **The `Role` field has no source.** Superpowers' subagent record wants a worker
  role that lives in `worker_orchestrator`, not in the routing result. It falls
  back to the task id. Cosmetic today, and it will look wrong to whoever reads a
  Codex plan first.
- **Eleven committed `worker-plan.json` files still carry v1**, absolute paths
  and `codex/`. Deliberate — they are rewritten the next time someone runs the
  command, and the version bump is what makes them distinguishable.

## What this unblocks

104, 113, 114 and 117. 104 is the one that matters: it owns Korean and English
request routing, and issue 131's stage 2 waits on it.

## Next

`/moduflow loop`.
