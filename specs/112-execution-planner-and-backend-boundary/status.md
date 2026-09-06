# Status: Execution Planner and Backend Boundary

Issue: 112-execution-planner-and-backend-boundary

T12. The corpus re-run and the dogfood check, measured 2026-09-07 at
`9d38754`, with the gates live.

## 요약

명세 **59개**에 게이트를 다 돌렸습니다. **21개가 거절**됩니다 — 할 일은 있는데
어떤 파일을 건드릴지 안 적혀 있어서입니다. **34개는 이미 끝난 명세**라 시킬 게
없고, **4개만 지금 바로 실행 가능**합니다.

거절 이유는 **109건 전부 "경계를 안 씀"** 한 가지입니다. 이 이슈가 따로 만든
"경계를 썼는데 못 읽는 형태" 판정은 **한 번도 안 걸렸습니다.**

## The distribution

| status | count | share | meaning |
| --- | --- | --- | --- |
| `not_applicable` | 34 | 57% | no unfinished implementation task — the spec is done |
| `needs_plan` | **21** | 35% | work exists, no usable file boundary |
| `ok` | 4 | 6% | dispatchable now |

Gaps: **109, every one `no_boundary`.**

### The four that pass

| spec | backend | why that backend |
| --- | --- | --- |
| `027-reduce-approval-popup-friction` | `inline` | boundaries can touch the same file |
| `029-antigravity-artifact-sync-connector` | `superpowers-sdd` | disjoint boundaries, no shared state |
| `112-…-backend-boundary` | `inline` | T09 declares `shared_state: true` |
| `120-silent-status-fallback-in-issue-parser` | `inline` | one surviving task |

Three of four are `inline`. Spec §6.3 calls `inline` a success rather than a
fallback, and the corpus says it is also the common one.

### The twenty-one refused

```
001 002 003 004 005 006 025 047 054 059 068
069 070 071 072 073 075 079 111 129 131
```

## Against the simulation

`evidence/SIMULATION-REPORT.md` predicted **19 of 55**. The live run is **21 of
59**. The corpus grew by four specs between the simulation and now, and two of
the four new ones refuse.

The share is what matters and it held: 34.5% predicted, 35.6% measured.

## The check that did not fire

`unreadable_notation` — the gap kind for a boundary written in a form the parser
cannot read — **has never fired on real data**, then or now.

Specs 103, 109 and 110 are why the distinction exists: they write
`| Files: … | Depends: A1` instead of `[files: …] [depends: T01]`. But every task
in 103 and 109 is checked, so Gate 1 drops them and they return
`not_applicable` before Gate 2 sees anything. 110 has no `tasks.md` at all.

So the case is real in the corpus and unreachable through the gates today. Its
fixture is synthetic (`tests/fixtures/execution-routing/pipe-notation-tasks.md`,
which copies their actual lines with the checkboxes reopened). Recorded here so
a clean run is not read as evidence the case cannot occur — the same shape as
issue 120's `unreadable` reason, and worth watching for the same reason.

## The dogfood

This issue's own `tasks.md`:

```
status: ok / backend: inline / project_root: "."
task ids: T09 T10 T11 T12   (survivors keep their original numbers)
gaps: []   divergences: []
```

`inline` because T09 declares `shared_state: true`. Survivors start at T09
because T01–T08 are done, and **they are not renumbered** — a human-written
`[depends: T03]` still points at T03 after the filter, and T12's dependency on
the completed T03 resolves as satisfied per §5.

## What the numbers mean

Before this issue, the same corpus produced **640 worker tasks, 514 of them
already done**, with 36 of 55 specs declaring no boundary on any task and the
planner reporting all of it as dispatchable. `specs/001-project-migration`'s only
open task was `Commit and push.`, assigned a worktree and a prompt reading
`Expected files: none`, and reported ready.

Today 001 returns `needs_plan` and writes nothing.

**The 21 refusals are not a regression.** They are 21 specs that were always
unplannable and were being reported as ready.

## Verification

- `python3 -m unittest discover -s tests` — 2056 tests, OK
- `python3 scripts/release_check.py .` — `valid: true`
- Corpus behaviour required by §13: 029 `ok`, 001 `needs_plan`, 023
  `not_applicable` — all three confirmed
