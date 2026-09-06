# Issue 131: Command Surface Is Too Wide And English Only

**Status: backlog** — created 2026-09-06.
**Priority: p1**

## 요약

`/` 팔레트에 명령이 **41개**, 스킬이 **11개** 뜨는데 설명이 전부 영어에 내부 용어라
읽고 고를 수가 없습니다. 보이는 것을 **10개로 줄이고**, `/moduflow` 하나만 기억하면
나머지는 **한국어든 영어든 평소 쓰는 문장**으로 되게 합니다. 줄이는 것은 *보이는
표면*이지 기능이 아닙니다 — 나머지는 허브를 통해 그대로 동작합니다.

## Summary

ModuFlow 0.3.67 exposes 41 source commands and 11 top-level skills, all described
in English using internal vocabulary. Choosing one requires already knowing the
product's internal model. The fix is a narrow visible allowlist plus a single
remembered entry point that accepts ordinary Korean or English, with both routed
identically.

## Source

- Type: user-requested, confirmed with the owner 2026-09-06
- Owner / decision maker: Dongwon Lee
- Reported through `workspace/inbox.md`; revised by the reporter the same day
  from Korean-only to bilingual
- Benchmark:
  `knowledge/benchmarks/2026-09-06-agent-skill-discoverability-and-bilingual-command-surface.md`
  (benchmarked against Anthropic Skills, Claude Code invocation controls,
  OpenAI's skill-authoring guidance, Superpowers and Basic Memory)

## Opportunity

Counts measured on this repository, 2026-09-06:

| Surface | Count | Verified |
| --- | --- | --- |
| `commands/*.md` | 41 | yes — `ls commands/*.md` |
| top-level `skills/` | 11 | yes — `ls -d skills/*/` |
| generated Codex `source-command-product-*` skills | 27 | **확인 못 함** — the report states 27; no such directory or generator was found under `scripts/` or `.codex-plugin/`. Confirm before citing this number |

The evidence that matters is not the count. It is that the owner, who commissioned
this product and uses it daily, said during a working session on 2026-09-06:
"너가 하는말의 반은 못알아 들어" — half of what the tool says does not land. Two
attempts to explain one approval decision in that same session both failed, the
second one after deliberately simplifying, because the explanation still described
the mechanism rather than the choice.

A product whose whole premise is human-in-the-loop review fails at its premise if
the human cannot read the surface they are reviewing.

**The owner explicitly rejected shorthand.** `/product:d`, `/product:m`,
`/product:rev` and similar were considered and refused: an abbreviation is another
language to memorise, which is the problem, not the fix.

### This is a follow-up, not a duplicate

Four adjacent issues are all `done`: 009 built the `/moduflow` hub command and
shipped it as 0.2.4; 055 covered command-surface onboarding; 020 covered
loop UX; 044 covered the dashboard command. The hub exists. What has happened
since is that the surface grew to 41 while the hub stayed one of many entries.

## Scope

### In

- A visible allowlist: `/moduflow` plus `product:inbox`, `product:issue`,
  `product:decision`, `product:benchmark`, `product:memory`, `product:status`,
  `product:loop`, `product:execute`, `product:review`, `product:release`.
- Each visible entry gets a short Korean-first bilingual action label, a plain
  description, and a realistic example in both languages.
- `/moduflow` accepts ordinary Korean **or** English, routed identically:
  `결정으로 남겨줘` / `record this decision`, `비교해줘` / `compare`,
  `기억해줘` / `remember`, `전에 뭐로 정했지?` / `what did we decide?`,
  `다음에 뭐 하면 돼?` / `what should I do next?`.
- Memory routing follows the words, not the folders, with each pair equivalent:
  `메모해줘`/`note this` → inbox, `기억해줘`/`remember this` → durable memory,
  `정했어`/`we decided` → decision, `비교해줘`/`compare` → benchmark,
  `찾아줘`/`find` → cross-record search.
- `product:decision` accepts one sentence. Issue, reason, alternatives and
  context are inferred from the conversation and project; the only question
  asked, and only when the reason is genuinely absent, is
  `이 선택을 한 가장 큰 이유가 무엇이었나요?`.
- User-facing output translates internal schema terms: rationale →
  `왜 이렇게 정했나요?`, alternatives → `다른 선택은 무엇이었나요?`, caveats →
  `조심할 점이 있나요?`, retrieval_trigger → `언제 다시 살펴보면 될까요?`.
- Everything else stays internal but keeps working: knowledge, evidence,
  research, report, promote, workflow plumbing, administration, bridges,
  routers, policies, and any duplicate generated source-command skills.

### Out

- Removing or renaming any command's behaviour. This narrows what is *shown*.
  A command that stops working is a regression, not a simplification.
- Shorthand aliases. Refused by the owner, on the record above.
- Translating stored artifacts. Issue files, specs and memory records keep the
  bilingual convention they already have (`## 요약` above `## Summary`); this
  issue is about the command surface, not the corpus.
- The Korean summary coverage gap — 32 issues render in English and 55 depend on
  a legacy map. Same theme, different artifact, and `commands/product-issue.md`
  step 7 already owns it.
- Deciding the wording of every label. The allowlist and the routing pairs are
  in scope; copy review belongs to the owner.

## Known Limit

A narrower palette hides commands rather than deleting them. Someone who knew the
old name and cannot find it must still be able to reach it. Any design that makes
an internal command unreachable has failed this issue, not satisfied it.

## Acceptance Criteria

- The visible palette lists exactly the eleven entries above, each with a Korean
  label, a plain description, and one Korean and one English example.
- Every command not on the allowlist still executes when named explicitly, and a
  test asserts this for all 41, so hiding never becomes removing.
- The five Korean routing phrases and their five English equivalents each reach
  the same handler, asserted pairwise.
- `product:decision` produces a complete record from one sentence plus at most
  one follow-up question, on a fixture where reason, alternatives and issue are
  recoverable from context.
- No output shown to the owner contains `rationale`, `alternatives`, `caveats` or
  `retrieval_trigger` as bare English field names.
- The owner can complete one decision, one memory write and one status check
  without consulting a command list. This is the only criterion that matters and
  it cannot be automated — it is checked by asking him.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture: each of the ten Korean/English phrase pairs, asserting identical
  routing.
- Fixture: every one of the 41 commands invoked by name, asserting none became
  unreachable.
- Fixture: a one-sentence decision whose reason is present, and one where it is
  absent — assert one question in the second case and none in the first.
- A scan of user-facing strings for the four bare field names.
- Hand the palette to the owner and confirm he can pick without a list.

## Entry Points

- `commands/` — 41 files; the allowlist decides which stay visible
- `skills/` — 11 top-level skills
- `commands/product-moduflow.md` or the hub entry shipped by issue 009 — the
  router that must accept both languages
- `scripts/project_memory.py` — the field names surfaced to the reader
- `commands/product-decision.md` — the one-sentence input path
- `knowledge/benchmarks/2026-09-06-agent-skill-discoverability-and-bilingual-command-surface.md`

## Scope Fence

Narrow the surface, not the product. If satisfying this issue requires deleting
a capability, the design is wrong. And do not solve it with abbreviations — that
option was put to the owner and refused.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → allowlist, bilingual routing, field-name translation
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- follows_up: `009-moduflow-hub-command` (done — built the hub this issue makes
  primary), `055-command-surface-onboarding` (done), `020-user-facing-simple-loop-ux`
  (done), `044-product-dashboard-command` (done)
- related: `130-decision-requests-a-human-cannot-read` — the same failure one
  layer down. 130 makes a decision request readable inside a spec; this makes the
  command that creates it readable. The Korean field-name translations appear in
  both; whichever lands first owns them.
- related: `104-project-aware-natural-language-request-orchestrator` — owns
  natural-language routing generally, and is blocked on 112. This issue must not
  build a second router; check 104's design before implementing the hub side.

## Next Command

`product:spec 131-command-surface-is-too-wide-and-english-only`
