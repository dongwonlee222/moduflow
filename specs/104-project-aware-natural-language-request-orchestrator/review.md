# Review: Project-Aware Natural-Language Request Orchestrator

Issue: 104-project-aware-natural-language-request-orchestrator

Eleven tasks, all closed 2026-09-07. 47 tests. Versions 0.3.80 → 0.3.87.

## What shipped

`scripts/request_routing.py` — five stages behind one public entry, called in a
fixed order. Each stage calls a module that already worked and carries its
result verbatim; nothing is re-implemented.

```
route_request(request, registry_path, *, chosen_issue=None, commit=False)
  ├─ stage_resolve      project_registry.resolve_project
  ├─ stage_overlap      the resolved project's open issues
  ├─ stage_capability   capability_routing.route_request
  ├─ stage_execution    execution_routing.build_routing
  └─ stage_commit       project_lifecycle.transition_lifecycle
```

`commands/moduflow.md` routes a bare sentence here. **No new command file** —
41 before, 41 after, frozen by test.

## Did it work

Yes, and the proof is that it was run against the live registry rather than only
against fixtures. `/moduflow Bot Ops 현재 상태 확인해줘` returns `ok` / `commit` /
33 candidates / `written: []`. `/moduflow 현재 상태 확인해줘` stops at `resolve`
and asks one question. Both through the installed 0.3.87 package, not the
working tree.

Five source scenarios, all with `written: []`:

| Scenario | Outcome |
|---|---|
| Existing work, revision | `ok` · `attach` · the existing issue id |
| New deliverable | `ok` · no issue file created, asserted by directory listing |
| Ambiguous project | `ambiguous` · one question · zero candidates, zero capability calls |
| Unavailable capability | `ok` · `outcome: none` — not a refusal |
| State-write failure | `blocked` · every contract field still present |

## The two decisions that changed the design

**Stage 2 does not judge overlap, because nothing can.** The plan's open question
asked for a threshold and said to measure first. Measured over 147 issues and
10,731 pairs against 220 human-declared same-work pairs, all four candidate rules
fail — best precision (67%) finds 2 of 220. Re-checked against seven pairs a
person read and merged, **five score 0.00** on title similarity and three share
no file. So the stage returns candidates and the reader names the overlap.
`test_no_score_rank_or_verdict` is there to fail if a threshold returns.

**`commit` defaults to False.** R6 says stage 5 commits and does not say when it
is asked to. Taken literally, asking "what would this do?" changes state in order
to answer. Recorded in the spec as a deviation, with the one line to change named.

## What running it for real found that 45 green tests did not

Two defects, both fixed, and this is the part worth keeping.

1. **`unresolved` was reported as `ambiguous`.** The live registry's three
   projects all had unreachable roots; the resolver said so correctly and this
   module asked the person to pick among three broken projects. No answer helped.
2. **`stage` said `resolve` on a request that cleared all five stages**, because
   only the stages that stopped or wrote were setting it.

And one defect underneath, filed and fixed as **issue 149**: every root in the
live registry was written with a `~` that nothing expanded, so all three
registered projects resolved to paths that had never existed — while the registry
still loaded as `valid: true`. That is why `/moduflow` did nothing when the owner
first tried it.

**None of the 45 tests could have caught any of these**, because every fixture
builds its own registry with absolute paths that exist. That is the limit of a
fixture, and it is why the last task was "run it for real".

## Seven sabotage checks

Each break deliberately introduced, each reverted:

| Break | Tests that caught it |
|---|---|
| Drop the open-state filter → `done` issues become candidates | 2 |
| Skip the candidate check → any id attaches | 1 |
| Read a sibling project's `issues/` | **6** |
| Swallow a broken capability registry as `none` | 1 |
| Let `needs_plan` through to the writing stage | 1 |
| Ignore the `commit` flag and always write | 1 |
| Report a failed transaction as success | 1 |

The third matters most: the two isolation tests **passed at step 1 while
asserting nothing**, since stages 2-5 read no files. The class docstring said so
at the time rather than letting them read as proof, and step 2 made them real.

## What this did not do

- **103's rollback is not re-tested.** 103 owns proving a refused transaction
  leaves no half-written state. This module asserts only that it stops and
  reports `written: []` rather than success.
- **No capability is invoked.** Stage 3 routes; running a specialist is not this.
- **Overlap candidates carry no `## 안 고치면` line outside this repository.**
  The rule shipped here and has not spread, so a candidate list from another
  project is titles only. Recorded in that project's inbox, not filed as an
  issue here.

## Cost

About 1,100 lines of `scripts/` and ~700 of tests. Measured the same day: the
repository is 44,843 script lines across 117 closed issues — roughly 383 lines
per issue, and no small set of commits explains it (the seven largest total 19%).
This issue is at that average, not below it. Worth stating in a review of an
issue whose own goal file says the product should be getting lighter.

## Next Command

`product:status`

---

## 사후 추가 — spec-kit `analyze` 가 찾은 것 (2026-09-07)

이 이슈가 `done` 이 된 뒤, spec-kit 어댑터를 켜고(151) 이 명세에 처음으로
`analyze` 를 돌렸습니다. **아래는 고쳐 쓴 것이 아니라 덧붙인 것입니다** — 헌법
C5(Findings are append-only)가 기존 산출물 내용을 다시 쓰는 것을 금합니다.
`plan.md` 의 틀린 줄은 그대로 두고, 여기에 정정을 적습니다.

| ID | 등급 | 위치 | 발견 | 사실인가 |
|---|---|---|---|---|
| D1 | CRITICAL(도구 판정) | `specs/104-*/` | **C9 한국어 사이드카(`spec.ko.md`)가 없다.** 저장소의 25개 명세는 갖고 있다 | 사실. 다만 **C9는 SHOULD** 이고 *"missing sidecars fall back, never gate"* 라 위반은 아니다 |
| C1 | HIGH | `spec.md` R6 ↔ `tasks.md` T09 | **R6은 "산출물을 검증한 뒤 커밋"인데 T09는 전이만 한다.** 산출물 검증에 매핑된 태스크가 0개 | **사실.** 명세를 좁혔어야 했는데 안 했다 |
| A1 | MEDIUM | `spec.md` R3 | "high-confidence overlap" 이 측정 불가 표현이다 | **헛방.** R3 개정문이 이미 그 점을 인정하고 답했는데, 원문 표현만 보고 지적했다 |
| F1 | MEDIUM | `plan.md` Approach | `stage_capability → capability_routing.route` 라 적혀 있으나 실제 함수는 **`route_request`** | **사실** |
| F2 | LOW | `plan.md` Approach | `route_request(request, root, *, host=None)` 로 적혀 있으나 실제는 `registry_path` 를 받고 `chosen_issue`·`commit` 이 더 있다 | **사실** |

**커버리지: 요구사항 6개 중 5개 완전, R6이 부분 — 83%.**

### 이 도구가 실제로 한 일

**분석은 모델이 했습니다.** 어댑터가 한 것은 **입력 파일 넷을 찾아 주고 검사
항목표(템플릿)를 건네준 것**입니다. 그게 설계이고(advisory only, 아무것도 안
씀), 그 이상을 하지 않습니다.

그래도 값이 있었습니다. 혼자였으면 **중복·모호·미명세·헌법 정렬·커버리지·용어
표류** 여섯 갈래를 빠짐없이 훑지 않았을 것이고, **특히 헌법 대조는 안 했을
것**입니다. D1이 거기서 나왔습니다. 5건 중 4건이 사실이고 1건이 헛방입니다.

### 안 고친 것과 그 이유

`plan.md` 의 F1·F2를 **고쳐 쓰지 않았습니다.** C5가 금합니다. 다음 사람이
`plan.md` 를 믿고 잘못 읽지 않도록 이 표가 정정 기록입니다.

`spec.ko.md` 는 만들지 않았습니다 — C9는 SHOULD 이고 fallback 이 명시돼
있습니다. 다만 25개 명세가 갖고 있으니, 사이드카를 언제 만들고 언제 안 만드는지
자체가 정해져 있지 않다는 뜻입니다. 별건입니다.
