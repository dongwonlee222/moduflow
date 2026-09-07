# Status: 104 — Project-Aware Natural-Language Request Orchestrator

2026-09-07. All eleven tasks done. 45 tests, suite green, `release_check` valid.

## T04 — the overlap measurement

Three candidate rules over the live corpus, plus a fourth combination.
**All four fail**, which is the result and not a setback: it is what changed
stage 2 from a judge into a list.

| Rule | Precision | Recall |
|---|---|---|
| Title Jaccard ≥ 0.3 / 0.4 / 0.5 | 23% / 25% / 67% | 3.2% / 0.9% / 0.9% |
| Entry Points share ≥ 1 file | 16.8% | 23.6% |
| Entry Points share ≥ 2 files | 39.7% | 11.4% |
| Title ≥ 0.3 **and** a shared file | 33.3% | 0.5% |

147 issues, 10,731 pairs, 220 human-declared same-work pairs. Re-checked against
the seven pairs a person read and merged on 2026-09-06/07: **five score 0.00**
on title similarity and three share no file.

Full record:
`memory/evidence/2026-09-07-overlap-detection-corpus-measurement.md`.

## T11 — the five source scenarios

| # | Scenario | Outcome | `written` |
|---|---|---|---|
| 1 | Existing work, revision | `ok` · `action: attach` · the existing issue id | `[]` |
| 2 | New deliverable | `ok` · `issue: null` · **no issue file created**, asserted by directory listing before and after | `[]` |
| 3 | Ambiguous project | `ambiguous` · stops at `resolve` · one question, no newline · zero candidates, zero capability calls | `[]` |
| 4 | Unavailable capability | `ok` · `outcome: none` — a project with no adapters, which is not a refusal | `[]` |
| 5 | State-write failure | `blocked` · stops at `commit` · every contract field still present | `[]` |

Scenario 4 is the one worth naming. Reading "no adapters configured" as a
refusal would refuse every request ModuFlow handles itself, which is most of
them. A registry that exists and **does not parse** is a different fact and
returns `blocked`.

## What was checked by sabotage rather than by passing

Seven deliberate breaks, each reverted, each confirming a test has teeth:

| Break | Tests that caught it |
|---|---|
| Drop the open-state filter → `done` issues become candidates | 2 |
| Skip the candidate check → any id attaches | 1 |
| Read a sibling project's `issues/` | **6**, including both isolation directions |
| Swallow a broken capability registry as `none` | 1 |
| Let `needs_plan` through to the writing stage | 1 |
| Ignore the `commit` flag and always write | 1 |
| Report a failed transaction as success | 1 |

The third matters most. Those two isolation tests **passed at step 1 while
asserting nothing** — stages 2-5 read no files, so nothing could leak whatever
the code did. The class docstring said so at the time rather than letting them
read as proof, and step 2 made them real.

## Deviations, both recorded in the spec

1. **R1 gained `overlap_candidates`.** The field list was written when stage 2
   was still expected to return a verdict. The measurement removed the verdict
   and left the candidates, which need somewhere to land.
2. **`commit` defaults to False.** R6 says stage 5 commits and does not say when
   it is asked to. Taken literally, asking "what would this do?" changes state
   in order to answer. The spec names the one line to change and the two tests
   that pin it, should the owner want the other behaviour.

## What this issue did not do

- **103's rollback is not re-tested here.** 103 owns proving a refused
  transaction leaves no half-written state. This module's tests assert the
  narrower thing it is responsible for: that it stops and reports `written: []`
  rather than success.
- **No capability is invoked.** Stage 3 routes; running the specialist is not
  this issue.
- **No new command file.** 41 before, 41 after, frozen by test.

## Next Command

`product:review 104-project-aware-natural-language-request-orchestrator`
