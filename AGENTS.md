# AGENTS.md — ModuFlow Output Format Convention

This file is read natively by Antigravity (v1.20.3+), Claude Code, and Codex CLI. It governs how any of them writes ModuFlow artifacts (issues, specs, plans, PR/review notes, commit messages) and chat-facing status output.

Goal: not one mandated visual style, but a shared **situation → shape** mapping, so the same kind of content looks the same regardless of which tool wrote it. See `knowledge/benchmarks/2026-07-05-cross-agent-output-format-benchmark.md` for the evidence behind this, and `specs/060-cross-agent-output-format-convention/spec.md` for the full spec.

## Situation → Shape

| Situation | Shape | Why |
|---|---|---|
| Snapshot of fixed fields (project, branch, phase) | Box panel or table | Fixed-width alignment is glanceable; a table beats prose when the same fields repeat |
| N comparable items where the reader must decide something | Numbered/bulleted list, inline status badges (`` `id` `` `(state → state)`), bold label before each explanation (`**내용**:`), closing recommendation, then a direct question | Reader skims badges/labels and only reads prose for the item they care about |
| Task already done, reader just needs to confirm | Flat labeled sections (e.g. `변경:`, `검수:`), no closing question | Nothing to decide — end on the last verification fact, not a prompt |

Don't force one shape onto all three situations. A status snapshot forced into a decision-list format buries the fields; a completed-task report forced into a question format asks the reader something that was never in doubt.

## Shared Baseline (all situations)

1. **Bottom-line first.** State the result/status in the first line; explain after.
2. **Label before explanation.** A table header, a bold badge, or a `key:` prefix — the reader should know what a line is about before reading its content.
3. **Tables/checklists need 2+ comparable fields.** Don't reach for a table to describe one item.

## Purpose First — ModuFlow Rule

Follow the bundled [ModuFlow output rule](docs/output-format.md): **왜 필요한지 → 해결해야 할 문제 → 기대 효과**, followed by implementation and verification. This is the plugin's shared rule, not a personal preference confined to this repository. Preserve the short bottom-line status sentence and situation-to-shape rules above.

## Whitespace Rhythm

Spacing is a signal, not decoration:

- Always one blank line after a header, before its content.
- **Loose list** (blank line between items) when each item carries a nested, multi-line explanation — one visual block per item, so the eye has somewhere to rest between items.
- **Tight list** (no blank lines) when items are flat, single-line facts with nothing nested — density is fine when there's nothing to separate.
- An extra blank line, or a `---` rule, between unrelated sections — signals "topic changed," not just "next item."
- A `---` rule before a closing recommendation or question — visually separates "information" from "the thing you're being asked."

## Worked Example: Before / After

**Before** (no shared convention — this actually happened across issues `001`–`040`, three incompatible status conventions in the same repo):

```
## Lifecycle
- Phase: done
```
```
(no status field at all)
```
```
**Status: done** — created 2026-07-01, started 2026-07-01, done 2026-07-01.
```

`project_lifecycle.py`'s parser only recognizes the third form, so the first two were silently read as `backlog` — misreporting roughly 20 already-completed issues.

**After** (this convention applied — one form, everywhere):

```
**Status: word** — created <date>, started <date>, done <date>.
```

Same rule generalizes beyond status lines: pick one shape per situation (see table above) and use it every time that situation recurs, so both humans and parsers can rely on it.

## Module Size — 개념 수가 기준이지 줄 수가 아니다

**경고이지 게이트가 아니다.** 막으면 `_part2.py` 같은 것이 생겨서 지금보다
나빠진다.

한 모듈이 **1,000줄을 넘고 동시에 최상위 심볼(모듈 바깥의 함수·클래스)이 40개를
넘으면** 쪼갤 때가 된 것이다. **둘 다** 넘어야 한다.

**줄 수만으로는 판정하지 않는다.** pandas의 `frame.py`는 20,180줄인데 최상위
심볼이 **4개**다 — 한 가지를 자세히 하는 파일이고 길어도 읽힌다. 이 저장소의
`project_lifecycle_transaction.py`는 7,524줄에 심볼이 **208개**, 이름 갈래만
106종이다. 길어서 문제가 아니라 **한 파일이 열 가지 일을 해서** 문제다.

두 숫자의 출처: **1,000**은 `pylint`의 `max-module-lines` 기본값이고, 기본으로
켜지는 유일한 도구다 (eslint의 `max-lines`는 꺼져 있고, ruff에는 규칙이 없고,
Google Python 스타일 가이드에는 파일 상한이 없다). **40**은
`wemake-python-styleguide`가 라인이 아니라 **멤버 수**로 재는 것에서 왔다 —
그쪽이 원인에 더 가깝다.

**500줄 상한은 채택하지 않았다.** 1차 자료가 `openai/codex`의 `AGENTS.md` 하나뿐이고,
거기 적힌 이유는 **머지 충돌**이지 읽기 어려움이 아니다. Home Assistant는 pylint의
`too-many-lines`를 *"가독성을 위해 강제하지 않는다"*는 주석과 함께 끄고 4,258줄
파일을 유지한다. 조사 근거는 2026-09-07 서브에이전트 보고에 있다.

넘는 파일을 **따로 리팩터링하지 않는다.** 그 파일을 다른 이유로 건드릴 때 같이
쪼갠다. 현재 넘는 것 7개 (2026-09-07 실측):

| 줄 | 심볼 | 파일 |
|---:|---:|---|
| 7,524 | 208 | `project_lifecycle_transaction.py` (클래스 35 — 패키지가 되어야 한다) |
| 4,167 | 119 | `project_lifecycle_transaction_storage.py` |
| 2,958 | 74 | `project_memory.py` (클래스 0 — 함수 묶음, 이음매가 뚜렷하다) |
| 2,555 | 73 | `project_issue_schema.py` (클래스 0 — 같음) |
| 1,310 | 48 | `spec_kit_adapter.py` |
| 1,199 | 41 | `project_production.py` |
| 1,068 | 47 | `project_analysis_run.py` |

**쪼개는 이유는 "에이전트가 못 읽어서"가 아니라 "한 파일이 여러 개념을 담아서"다.**
7,524줄을 470줄 16개로 나눠도 가로지르는 변경에 필요한 맥락은 안 줄어든다. 얻는
것은 **한 번의 읽기가 완결되고 grep 결과 하나가 해석 가능해지는 것**이고, 그건
줄 수가 아니라 개념 분리에서 온다.

## Non-Goals

- This file does not define artifact-to-artifact sync rules between Antigravity's native files (`task.md`, `implementation_plan.md`) and ModuFlow's Git files — see `issues/029-antigravity-artifact-sync-connector.md`.
- This file does not define Korean/English language rules — see `issues/049-bilingual-artifact-view.md` and `issues/057-korean-human-review-packet.md`.
- This file does not retroactively migrate legacy issues `001`–`040` to the current `Status:` line format.
