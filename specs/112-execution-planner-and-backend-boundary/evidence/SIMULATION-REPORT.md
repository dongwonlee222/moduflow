# Issue 112 — gate prototype simulation

Run 2026-09-05 against moduflow @ `a5657dd`. Built outside the repo; the
checkout was not modified and stays 0/0 with origin.

Files: `gate_prototype.py`, `test_gate_prototype.py` (31 tests), `simulate.py`.

## What was simulated

| Gate | Rule |
| --- | --- |
| 1 semantic filter | keep unchecked, non-deferred checkboxes not under a gate/evidence section |
| 2 boundary check | every survivor needs a file or glob, and every `depends` must resolve to another survivor |
| 3 routing | exactly one of `inline` / `superpowers-sdd`, with the reason recorded |

Fail-closed at plan level: one boundary-less survivor refuses the whole plan
(benchmark line 68). Refusal writes nothing and returns `needs_plan`.

## Result over all 55 specs

| Verdict | Specs |
| --- | --- |
| `ok` — usable plan | 2 |
| `needs_plan` — refused | 19 |
| `not_applicable` — nothing left to do | 34 |

Three separate effects, deliberately not merged into one ratio. A corpus-wide
"640 checkboxes today → 5 planned tasks" comparison would read as "the planner
emits 99% less work", which is not what happens — most of the drop is whole
specs being refused or recognised as finished, not tasks being filtered.

| Effect | Measure |
| --- | --- |
| Filtering, on the specs that still produce a plan | 15 → 5 worker tasks |
| Specs refused outright (`needs_plan`) | 19 |
| Specs recognised as finished (`not_applicable`) | 34 |

The 34 finished specs are correctly recognised rather than refused. Of the 21
specs with open tasks, 2 produce a plan and 19 are refused — 104 gaps in total.

| Spec | Today | After | Backend |
| --- | --- | --- | --- |
| 027-reduce-approval-popup-friction | 12 | 2 | `inline` |
| 029-antigravity-artifact-sync-connector | 3 | 3 | `superpowers-sdd` |

Worst refusals: 054-github-issue-sync (14 gaps), 047-issue-artifact-drilldown
(12), 068-machine-query-surface (12), 069-issue-dependency-priority-model (11),
059-auto-fetch-in-repo-sync (10).

Sampled 054 by hand: 14 open tasks, all genuine implementation work
(`_parse_owner_repo` covering ssh-alias / ssh / https forms, and similar), none
declaring a file. The refusal is correct — a worker cannot act on that.

## Controls

- **Positive control, real corpus**: 029 has open tasks carrying `[files:]` and
  `[depends: T01]`. It must not be refused, and is not. Without this the run
  could not distinguish "gates work" from "gates reject everything".
- **Finished, not broken**: 023 is fully `[x]` and returns `not_applicable`, a
  different result from `needs_plan`.
- **Parser parity**: the prototype scan is asserted equal to the shipped
  `parse_tasks` on every spec in the corpus, so the simulation is not measuring
  a divergent parser.

## Three defects the simulation surfaced

1. **Substring section matching was too aggressive.** Matching `verification`
   anywhere in a heading swallowed four real test-writing tasks under
   `Stream 3 — Tests + verification (gate)`. Fixed: whole-name match after
   stripping a `Stream X —` prefix, so `Stream D — Verification` is still
   excluded. Gate 1 is now deliberately conservative — anything ambiguous falls
   through to Gate 2, which refuses boundary-less work anyway.
2. **Glob overlap was compared as raw strings.** In 027, `scripts/*` and four
   named `scripts/` files were treated as disjoint and sent to two parallel
   workers on the same files. Fixed with fnmatch containment; 027 now correctly
   routes `inline`.
3. **The dependency rule contradicted shipped behaviour.** The first version
   treated a `depends` pointing at a completed task as a gap. Shipped
   `dispatchable_now` (`w_o.py:246`) treats it as satisfied, and the strict rule
   would have made any spec degrade to `needs_plan` as its own work progressed —
   the positive control 029 would flip the moment its T01 was checked off.
   Fixed: a dep on a done task is satisfied; only a dep on a nonexistent or
   deferred id is a gap. One corpus gap disappeared (105 → 104).

All three have regression tests, including one that checks off 029's T01 and
asserts the spec still plans.

## Decisions this settles

- The 39 bare specs are not one migration burden: 34 of them are finished and
  return `not_applicable`. Each of the remaining refusals names the exact tasks
  missing a boundary, so the work is enumerable rather than open-ended.
- The `Done`-section ambiguity raised in review does not exist. All five
  unchecked boxes under a `Done` heading have empty body text and are already
  skipped by the shipped parser.

## Open question the simulation surfaced and cannot settle

**Is fail-closed right for the 19 live specs?** Those are not finished work —
they hold real open tasks, and after this change `product:workers` returns
`needs_plan` for all of them until someone adds `[files:]` annotations. Three
options:

1. Keep fail-closed. Refusal is honest and the gaps are enumerated. Cost: 19
   specs need annotation before workers can run on them again.
2. Degrade instead of refuse — emit a plan marked `unverified` with the
   boundary-less tasks flagged. Cost: reintroduces the untrustworthy plan the
   issue exists to remove.
3. Fail closed only when the spec declares boundaries anywhere, and treat a
   spec with zero annotations as legacy `not_applicable`. Cost: a silent
   two-tier behaviour that is hard to explain.

Recommendation: option 1, because the refusal names the exact missing tasks and
the benchmark (line 68) calls for failing closed. This is a spec decision for
the owner, not something the run decides.

## What this run does NOT establish

- **AC5 (host-neutral adapter)** — untested. Needs Codex/Claude Code/Copilot
  fixtures; the prototype emits no adapter mapping.
- **AC6 (canonical vs Superpowers completion conflict)** — untested. No
  reconciliation path was built.
- **AC4** — the decision function is tested, dispatch is not. The result
  carries `dispatched: false` and `executed_by: null` and never claims
  otherwise, which is asserted, but nothing was actually executed.
- `project_root` is emitted relative, killing the stale-absolute-path claim,
  but only inside the prototype.

A green run here means the selection and refusal contract holds on real data.
It does not mean Issue 112 is validated.
