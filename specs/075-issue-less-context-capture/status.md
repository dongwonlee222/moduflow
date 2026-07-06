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

## In Progress — wave 1 (parallel, disjoint files)

- A1 `scripts/linkage_check.py` + tests — standard-tier worker
- B1 issue template AI-first fields — light-tier worker
- C1 record contract docs across 4 capture commands — light-tier worker

## Queued

- Wave 2: A2 (release_check repair, after A1) ∥ B2 (product:promote, after B1+C1)
- Wave 3: A3 (human identity + declarations) ∥ C2 (status surfacing + retention)
- Wave 4: D1 (074 writeup + docs sweep), self-application gate, review handoff

## Verification log

- 2026-07-06: spec_consistency clean after plan authoring.

## Next

Wave-1 verification (independent of implementers), commit, dispatch wave 2.
