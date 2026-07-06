# Status: 075-issue-less-context-capture

Issue: `075-issue-less-context-capture`
Phase: execute
Branch: `codex/075-issue-less-context-capture`
Backend: host-subagent (recorded in `workspace/loop-state.json`)
Updated: 2026-07-06

## Done

- Spec v1 → panel review (2 benchmarks + adversarial) → spec v2 rescope approved by user.
- Plan + tasks written; `spec_consistency` clean (0 errors / 0 warnings / 0 coverage flags).
- Planning artifacts committed on issue branch with `Issue:` trailer (dogfooding the A1 convention): `06afa2b`.
- Worker plan generated (parallel-eligible).

## Done — waves 1-2

- Wave 1 (`2f850f3`): A1 linkage_check module (29 tests), B1 template AI fields, C1 record contracts. Independently verified: 309 tests OK, no silent excepts, HEAD resolves to 075 via trailer.
- Wave 2: A2 release_check repair (silent holes removed, merge-base linkage gate, CI fetch-depth 0) + B2 project_promote.py/product-promote.md (promote dry-run auto-numbers 076, sections prefilled). Both workers were cut off by a session limit AFTER completing file work; coordinator verified outputs independently (31 new tests green) and finished the loose end (plugin bump 0.3.12 — version_bump_gate requires the bump in the completion commit).

## In Progress — wave 3 (coordinator inline, session limit makes subagent dispatch unreliable)

- A3: humans.json + releases/no-issue-declarations.md + human-review packet inclusion
- C2: status unpromoted surfacing + 2-release retention

## Queued

- Wave 4: D1 (074 writeup + docs sweep), self-application gate, review handoff

## Verification log

- 2026-07-06: spec_consistency clean after plan authoring.
- 2026-07-06: wave 1 — full suite 309 OK; linkage smoke test resolves HEAD→075 (trailer).
- 2026-07-06: wave 2 — test_release_check + test_project_promote 31 tests OK; promote dry-run verified; CI fetch-depth diff reviewed.

## Next

Wave-1 verification (independent of implementers), commit, dispatch wave 2.
