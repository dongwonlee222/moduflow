# Issue 143: Four Different Things Are Called "The Dashboard"

**Status: backlog** — created 2026-09-06.
**Priority: p2**

## 요약

"대시보드 보여줘"라고 하면 **네 개 중 뭘 말하는지 알 수 없습니다.** 진행 상황
파일, 의사결정 그래프 HTML, `상태`가 화면에 그리는 표, 프로젝트 전체 목록 —
전부 이름이 "대시보드"입니다. 게다가 **`대시보드`라는 낱말은 어디로도 연결되어
있지 않습니다.** `그래프`만 규칙이 있습니다. 그래서 사람이 그 말을 쓰면 도구가
찍습니다.

## Summary

Four artifacts in this product carry the name "dashboard". They differ in format,
in what they contain, in who writes them, and in whether they are even files.
Sixteen command files use the word. No routing rule maps the word itself to any
of them.

## Source

- Type: finding from the issue 131 command-surface pass, 2026-09-06
- Owner / decision maker: Dongwon Lee
- Surfaced by the owner's question during that pass — "상태만 체크 해도 대시보드가
  나와?" — which could not be answered without first asking which one he meant

## 안 고치면

"대시보드 보여줘"가 넷 중 뭘 말하는지 알 수 없습니다. 로드맵까지 치면 다섯입니다. — 다음 액션

## Opportunity

| Name | What it is | Written by | Tracked |
| --- | --- | --- | --- |
| `workspace/dashboard.md` | progress projection: goal, active issue, phase, blockers | `project_lifecycle.py`, `project_doctor.py`, `project_lifecycle_transaction.py`, `project_migrate.py`, `project_portfolio.py`, `validate_moduflow.py`, `validate_project_artifacts.py` | yes — a required artifact |
| `memory/dashboard.html` | interactive view: issue DB, issue graph, memory graph, production records, playbooks | `product:dashboard` via `project_memory.py` + `project_production.py` | no — `.gitignore`d, derived |
| the `status` terminal render | queue, blockers, team state, retention, sync freshness | `commands/product-status.md:122` `## Dashboard Format` | not a file at all |
| `portfolio-dashboard.md` | every registered project, one line each | `project_portfolio.py:19`, `:272` | in the portfolio root, outside any project |

Two of the four are files in this repository at different paths and different
formats. One is a file outside it. One is screen output that vanishes.

### The word routes nowhere

`commands/moduflow.md:30` and `skills/index/SKILL.md:100` both map `그래프`,
`graph`, `의사결정 그래프` → `product:dashboard`. Neither maps `대시보드` or
`dashboard`. A person using the product's own vocabulary for the thing hits no
rule, and the hub falls through to "pick the closest `product:*` command"
(`commands/moduflow.md:34`) — a guess, among four candidates that are all
plausible.

`commands/moduflow.md:30` even carries the disambiguation in a parenthesis:
"decision-graph dashboard; distinct from progress `workspace/dashboard.md`". The
collision was known, annotated, and left in place.

### It is spreading

Sixteen command files use the word: `moduflow`, `dashboard`, `execute`,
`evidence`, `issue`, `issues`, `knowledge`, `loop`, `portfolio`, `pr`,
`production`, `release`, `review`, `start`, `projects`, `status`, `update`.

Issue 131 added a seventeenth usage on 2026-09-06 — the new quick list says
`/moduflow status  어디까지 왔는지 대시보드로 봅니다`, which is accurate about
the third meaning and adds to the ambiguity. Recording it here rather than
quietly leaving it.

## Scope

### In

- Give each of the four a distinct name a person can say out loud, and use that
  name everywhere it is referred to.
- Route the bare word. Whatever `대시보드` and `dashboard` resolve to, it must be
  one specific thing, and the other three must be reachable by their own names.
- Update the sixteen command files and both routing tables to the chosen names.
- State which one a person means by default, and make that the answer to the
  bare word.

### Out

- Merging or deleting any of the four. They do different jobs; this is a naming
  defect, not a duplication one.
- Changing file paths. `workspace/dashboard.md` is a required artifact referenced
  by seven scripts and by `validate_project_artifacts.py`; renaming the *file*
  is a migration and is not what this issue is about. The **spoken name** is
  what changes.
- The content or ordering of any of them. Issue 119 settled the attention-first
  ordering and is done.
- The word "dashboard" inside prose that is clearly scoped by its sentence.

## Known Limit

Renaming does not stop someone saying "dashboard". The achievable outcome is
that the word resolves to one thing deterministically and the other three have
names of their own — not that the ambiguity becomes unsayable.

## Acceptance Criteria

- Each of the four has a distinct name, and a test asserts the names are used in
  `commands/` and `skills/` rather than the bare word.
- `대시보드` and `dashboard` route to exactly one command, and a test asserts it.
- The other three are each reachable by name, asserted one by one.
- `commands/moduflow.md:30`'s parenthetical disambiguation is unnecessary and
  removed, because the names no longer collide.
- No file is renamed or moved; a test asserts `workspace/dashboard.md` and
  `memory/dashboard.html` still exist at their current paths.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture: the bare word in Korean and English, asserting one resolution.
- Fixture: each of the four by its new name, asserting distinct resolutions.
- A scan of `commands/` and `skills/` for the bare word outside scoped prose.
- Ask the owner to name what he wants and check he gets it. The defect was found
  by him asking a question nobody could answer; the fix is checked the same way.

## Entry Points

- `commands/moduflow.md:30` — the routing rule and its parenthetical admission
- `skills/index/SKILL.md:100`, `:126` — the second routing table
- `commands/product-dashboard.md:37` — `memory/dashboard.html`
- `commands/product-status.md:122` — `## Dashboard Format`, the terminal render
- `scripts/project_portfolio.py:19`, `:272` — `portfolio-dashboard.md`
- `scripts/validate_project_artifacts.py` — where `workspace/dashboard.md` is
  required

## Scope Fence

Do not fix this by renaming `workspace/dashboard.md` on disk. Seven scripts and
the artifact validator reference that path; a rename is a migration with its own
failure modes, and this issue is about what a person calls the thing, not where
it lives.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → four names, routing for the bare word, the sixteen files
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `131-command-surface-is-too-wide-and-english-only` (found it; owns
  invocation and the menu, not vocabulary), `044-product-dashboard-command`
  (done — created the second one), `119-dashboard-attention-first-ordering-and-one-command-open`
  (done — ordering, not naming), `104-project-aware-natural-language-request-orchestrator`
  (owns routing; the bare-word rule should land in whichever of the two ships
  the router)

## Next Command

`product:spec 143-four-different-things-are-called-the-dashboard`
