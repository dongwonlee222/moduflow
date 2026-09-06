# Issue 131: Command Surface Is Too Wide And English Only

**Status: backlog** — created 2026-09-06; scope corrected by the owner 2026-09-06.
**Priority: p1**

## 요약

`/` 메뉴에 명령이 **41개**, 스킬이 **11개** 뜨는데 설명이 전부 영어에 내부 용어라
읽고 고를 수가 없습니다. 기본 진입점은 **`/moduflow` 하나**로 하고, 그 뒤에는
**한국어든 영어든** 평소 쓰는 말을 씁니다. 메뉴에는 **핵심 명령 10개만** 보이게 하고
접두사 `product:`는 뗍니다 — **`/moduflow inbox`처럼 이름만 쓰면 실행**됩니다.
옛 `product:xxx` 형태는 **더 이상 보증하지 않습니다**(파일은 남기되 테스트도 안내도
안 합니다). 지우는 건 별도 정리 작업입니다. 저장된 필드 이름은 하나도 안 바꿉니다.

## Summary

ModuFlow 0.3.67 exposes 41 source commands and 11 top-level skills, all described
in English using internal vocabulary. Choosing one requires already knowing the
product's internal model. The fix is a narrow visible menu, one primary entry point
that accepts ordinary Korean or English, and Korean-first labels — with no rename
of any command or stored field.

## Source

- Type: user-requested; scope confirmed and then corrected by the owner on
  2026-09-06 in the same session
- Owner / decision maker: Dongwon Lee
- Reported through `workspace/inbox.md`, revised the same day from Korean-only to
  bilingual
- Benchmark:
  `knowledge/benchmarks/2026-09-06-agent-skill-discoverability-and-bilingual-command-surface.md`

## Opportunity

Counts measured on this repository, 2026-09-06:

| Surface | Count | Verified |
| --- | --- | --- |
| `commands/*.md` | 41 | yes — 40 are `product-*`, one is `moduflow.md` |
| top-level `skills/` | 11 | yes |
| generated Codex `source-command-*` skills | 27 | **확인 못 함** — the report states 27; no such directory or generator was found. Confirm before citing |

The evidence that matters is not the count. It is that the owner, who commissioned
this product and uses it daily, said during a working session on 2026-09-06:
"너가 하는말의 반은 못알아 들어" — half of what the tool says does not land. Two
attempts to explain one approval decision in that same session both failed, the
second after deliberately simplifying, because the explanation still described the
mechanism rather than the choice.

A product whose premise is human-in-the-loop review fails at its premise if the
human cannot read the surface they are reviewing.

### This is a follow-up, not a duplicate

Issues 009, 055, 020 and 044 are all `done` — 009 built the `/moduflow` hub and
shipped it as 0.2.4. What changed since is that the surface grew to 41 while the
hub stayed one entry among many.

### Scope corrected 2026-09-06

An earlier draft concluded that only two entries would be memorised — `/moduflow`
and a **new** `/inbox` command. **The owner had not agreed to that.** What he
confirmed: `/moduflow` is the primary entry point, the visible menu keeps ten core
commands alongside it, and dropping the `product:` prefix applies to the
**displayed name only**. No command is renamed and no new short command is
created. The earlier text is replaced rather than annotated, so nobody implements
the wrong version.

## Scope

### In

**One primary entry point plus a ten-command visible menu.**

`/moduflow` is what a person has to remember. Behind it, ordinary Korean or
English. These ten stay visible for anyone who prefers picking from a list:

`inbox` · `issue` · `decision` · `benchmark` · `memory` · `status` · `loop` ·
`execute` · `review` · `release`

- **`/moduflow <name>` runs the command.** `/moduflow inbox` executes what
  `product:inbox` executes. That is the form the owner asked for on 2026-09-06:
  "moduflow inbox 이렇게만 해도 실행 되게". The prefix is not typed and not shown.
- `/moduflow inbox` is the hub dispatching on its first argument, not a second
  command named `inbox`. No new top-level command file appears.
- **The old `product:<name>` form is not promised.** Decided by the owner
  2026-09-06: it does not need to keep working. Nothing is deleted or renamed in
  this issue — the files stay and will keep functioning — but no compatibility
  guarantee is made and no test asserts it. Removing them is a separate cleanup,
  deliberately not bundled here.
- Everything written from now on uses `/moduflow <name>`: the menu, the labels,
  every `## Next Command` line, the templates, and the docs.
- Everything else is hidden from the menu and keeps working when typed:
  `knowledge`, `evidence`, `research`, `report`, `promote`, `profile`, `migrate`,
  `portfolio`, `workers`, bridges, routers, policies, and the duplicate generated
  `source-command-*` skills.

**Each visible command gets four things:** a short Korean-first description, an
English action name for recognition, a Korean input example, an English input
example.

**Bilingual routing.** Each pair reaches the same handler:

| 한국어 | English | Goes to |
| --- | --- | --- |
| `결정으로 남겨줘` | `record this decision` | decision |
| `비교해줘` | `compare` | benchmark |
| `기억해줘` | `remember this` | memory |
| `찾아줘` | `find` | search |
| `상태 보여줘` | `show status` | status |
| `다음에 뭐 해?` | `what is next?` | next action |
| `진행해줘` | `execute` | execute |
| `검토해줘` | `review` | review |
| `출시해줘` | `release` | release |

Single English words — `decide`, `compare`, `remember`, `find`, `next` — are
supported **as natural-language intent after `/moduflow`**, not as commands. No
command file is created for any of them.

**`product:decision` accepts one sentence.**

```
/moduflow 결정으로 남겨줘: 로그인은 이메일부터
/moduflow record this decision: build email login first
```

Issue, reason, alternatives and supporting material are inferred first from the
conversation and the project's own documents. Exactly one question is asked, and
only when the reason is genuinely unrecoverable:
`이 선택을 한 가장 큰 이유가 무엇이었나요?`

**Internal field names are never shown as-is.** Display only — the stored key is
untouched:

| Stored key | Shown to the reader |
| --- | --- |
| `rationale` | 왜 이렇게 정했나요? |
| `alternatives` | 다른 선택은 무엇이었나요? |
| `caveats` | 조심할 점이 있나요? |
| `retrieval_trigger` | 언제 다시 살펴보면 될까요? |
| `evidence` | 참고한 자료가 있나요? |

### Out

- **Renaming or deleting anything in this issue.** Command names, skill names,
  stored field names and artifact vocabulary are untouched here. The old
  invocation form loses its guarantee, not its files — see the cleanup note in
  Scope In. Stored field names never change at all. `rationale` remains
  `rationale` in the file and reads as `왜 이렇게 정했나요?` on screen.
- **Shorthand aliases.** `/product:d`, `/product:m`, `/product:rev` and similar
  were put to the owner and refused: an abbreviation is another language to learn.
  They are neither created nor suggested.
- **Creating a new short command** such as `/inbox`. The prefix disappears from
  the menu label only.
- **The quality of a decision or approval request once written.** That is issue
  130. The boundary: 130 owns whether a human can *read* a decision or approval;
  131 owns how they *invoke* it and what the menu shows.
- **Natural-language routing in general.** Issue 104 owns project-aware
  Korean/English routing and follows 112. This issue must not build a second
  router.
- Translating stored artifacts, and the Korean summary coverage gap — 32 issues
  render in English and 55 depend on a legacy map. `commands/product-issue.md`
  step 7 already owns that.
- Final copy for every label. The menu and the routing pairs are in scope;
  wording review belongs to the owner.

## Known Limit

Hiding a command is not deleting it, and someone who knew the old name must still
reach it. Any design that makes a hidden command unreachable has failed this issue
rather than satisfied it. And a menu of ten is still ten — this narrows the list,
it does not remove the need to know what the product does.

## Acceptance Criteria

- `/moduflow <name>` executes the command for all ten names, asserted one by one.
  `/moduflow inbox` and `product:inbox` reach the same handler and produce
  identical output.
- The visible menu lists `/moduflow` plus exactly the ten commands above, each
  displayed without the `product:` prefix and carrying all four items.
- No test asserts the old `product:<name>` form. It is unsupported, not broken —
  the distinction is recorded so a later cleanup is free to remove it.
- Every hidden command is still reachable through `/moduflow <name>`, asserted for
  all 41. Hiding must never become removing.
- Each of the nine Korean/English pairs reaches the same handler, asserted
  pairwise.
- The five single English words are handled as intent after `/moduflow` and do
  **not** appear as command files. A test asserts no command file was added.
- **No command file is renamed and no stored key changes.** A test compares the
  command filename set and the memory record schema against the current set and
  fails on any difference.
- `product:decision` produces a complete record from one sentence plus at most one
  follow-up question, on a fixture where reason, alternatives and issue are
  recoverable from context.
- No output shown to the reader contains `rationale`, `alternatives`, `caveats`,
  `retrieval_trigger` or `evidence` as bare field names.
- The owner completes one decision, one memory write and one status check without
  consulting a command list. This is the only criterion that matters and it cannot
  be automated — it is checked by asking him.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture: the nine Korean/English pairs, asserting identical routing.
- Fixture: all 41 names invoked as `/moduflow <name>`, asserting each reaches its
  handler.
- Fixture: the command filename set and the memory record schema, asserting
  nothing was renamed.
- Fixture: a one-sentence decision with a recoverable reason, and one without —
  assert one question in the second case and none in the first.
- A scan of user-facing strings for the five bare field names.
- Hand the menu to the owner and confirm he can pick without a list.

## Entry Points

- `commands/` — 41 files; the menu policy decides which are *shown*, not which exist
- `skills/` — 11 top-level skills
- `commands/moduflow.md` — the hub shipped by issue 009; the router that must
  accept both languages
- `commands/product-decision.md` — the one-sentence input path
- `scripts/project_memory.py` — the field names surfaced to the reader
- `knowledge/benchmarks/2026-09-06-agent-skill-discoverability-and-bilingual-command-surface.md`
- `workspace/inbox.md` — the originating report and its same-day revision

## Scope Fence

Narrow what is shown, not the product and not its vocabulary. If satisfying this
issue requires deleting a capability, renaming a command, or changing a stored
key, the design is wrong. **Nothing is deleted, renamed or migrated before the
owner approves the change list.**

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → menu policy, bilingual routing, one-sentence decision, display labels
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- follows_up: `009-moduflow-hub-command` (done — built the hub this issue makes
  primary), `055-command-surface-onboarding` (done),
  `020-user-facing-simple-loop-ux` (done), `044-product-dashboard-command` (done)
- related: `130-decision-requests-a-human-cannot-read` — deliberate boundary. 130
  owns whether a written decision or approval can be read; 131 owns invocation and
  the menu. The five display labels appear in both; whichever lands first owns
  them and the other cites it.
- related: `104-project-aware-natural-language-request-orchestrator` — owns
  project-aware Korean/English routing, follows 112. Do not build a second router.
- related: `112-execution-planner-and-backend-boundary` — settles what ModuFlow
  executes versus what the host executes, which decides what `진행해줘` can
  truthfully claim.

## Next Command

Report the change list to the owner in plain Korean — files to touch, skills to
hide, commands to keep, compatibility risks — **before** any code change.
Then `product:spec 131-command-surface-is-too-wide-and-english-only`.
