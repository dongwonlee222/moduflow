# Issue 120 Specification: Silent Status Fallback in the Issue Parser

**Status:** draft for review — written 2026-09-05.
**Owner:** Dongwon Lee
**Updated:** 2026-09-05

Issue: `120-silent-status-fallback-in-issue-parser`
Prev: issue observation during 119 · Next: `product:plan 120-silent-status-fallback-in-issue-parser`

## 1. Problem

`markdown_status` (`scripts/project_issue_schema.py:608`) resolves any status it
does not recognise to `backlog` and says nothing:

```python
def markdown_status(text):
    status = markdown_status_projection(text)
    if status is None:
        return "backlog"
    if status.startswith("superseded"):
        return "superseded"
    return status if status in LIFECYCLE_STATES else "backlog"
```

`LIFECYCLE_STATES` is `{active, backlog, done}`. Three different facts collapse
into one value on the last line and the one above it:

| Input | Today | The fact |
| --- | --- | --- |
| no `**Status:**` line | `backlog` | metadata missing |
| `**Status: 진행중**` | `backlog` | token unreadable — the regex is ASCII-only |
| `**Status: review**` | `backlog` | token read, then discarded as invalid |
| `**Status: backlog**` | `backlog` | actually in the backlog |

The fallback is directional, which is what makes it dangerous. It always lands
on `backlog` — the state meaning "not started" — so the error always
under-reports progress, never over-reports it.

**It fired on 2026-09-05.** Issue 125 was filed that afternoon with
`**Status: review**`, an invented state. The parser returned `backlog`, so a
finished and tested fix was reported as not started. Nothing logged it. It
surfaced only because someone printed the raw token beside the parsed one while
counting open issues.

A scan of all 125 issue files the same day found exactly one file relying on the
fallback — 125, since corrected. The other seven non-`LIFECYCLE_STATES` tokens
are `superseded-by-<id>`, which line 612 handles explicitly and correctly.

This violates constitution **C2 — no silent exceptions**. The blast radius is
wide precisely because C8 is being honoured: `markdown_status` is correctly the
only status parser, so `project_lifecycle`, the readiness gate, the dashboard
status column and grouping, and `moduflow_ready` all inherit the same silence.

## 2. Goals

1. Separate the three inputs above into three distinguishable results.
2. Emit a diagnostic naming the issue and the raw token whenever a fallback is
   applied, through the schema validator's existing channel.
3. Decide, and write down, whether a non-ASCII status token is an error or a
   reported fallback — rather than leaving the behaviour to a character class
   nobody chose deliberately.
4. Change no behaviour for a valid issue.

## 3. Non-Goals

- Adding, renaming or translating lifecycle states. `LIFECYCLE_STATES` is
  untouched, and `review` does not become a state because 125 wanted one.
- A second status parser. C8 stands.
- Making this a release gate on its own. Whether the validator escalates from
  diagnostic to error is decided in section 6, not assumed here.
- Changing the `backlog` default itself. This issue is about the silence.
- Repairing issue files. 125 was corrected when the firing was found; a scan is
  verification, not scope.
- Touching the `superseded-by-<id>` path, which works.

## 4. Proposed Solution

Keep one parser and one return value for callers that only need the state. Add a
second, richer entry point for callers that need to know how the value was
reached.

```mermaid
flowchart TD
    T["**Status:** line"] --> P{"token readable?"}
    P -->|"no line"| M["state backlog<br/>reason missing"]
    P -->|"non-ASCII"| U["state backlog<br/>reason unreadable"]
    P -->|"yes"| V{"in LIFECYCLE_STATES<br/>or superseded-*?"}
    V -->|"yes"| OK["state as written<br/>reason ok"]
    V -->|"no"| F["state backlog<br/>reason unrecognised<br/>raw token kept"]
    M --> D["validator diagnostic"]
    U --> D
    F --> D
```

`markdown_status(text)` keeps its exact signature and return values, so no
caller changes. A new `markdown_status_result(text)` returns the state plus
`reason` (`ok` / `missing` / `unreadable` / `unrecognised`) and the raw token
when there was one. `markdown_status` becomes a thin wrapper over it, which is
how C8 is preserved — one implementation, two views.

The schema validator calls the richer form and reports any reason other than
`ok`, naming the issue id and the raw token.

## 5. Alternatives Considered

1. **Raise on an unrecognised token — rejected.** A single mistyped word would
   break `product:status`, the dashboard and the readiness gate at once. The
   parser is on too many read paths to be allowed to throw.
2. **Log a warning from inside `markdown_status` — rejected.** It is a pure
   function used in loops over every issue; a print or logger call there would
   emit hundreds of lines and put I/O in a parser.
3. **Return `None` for unrecognised input and let callers decide — rejected.**
   That is the widest possible change: every one of the callers listed in
   section 1 would need a new branch, and any missed one becomes a crash.
4. **Add `review` to `LIFECYCLE_STATES` — rejected, and it is the tempting one.**
   It would make 125 parse and would fix nothing: the next invented word fails
   the same silent way. The vocabulary is not the defect.

## 6. Decision — Non-ASCII Status Tokens

`_markdown_status_token` matches `[A-Za-z0-9_-]+`, so `**Status: 진행중**` does
not match at all and arrives as "no line". That is wrong on the facts — a status
line is present.

**Decision: a non-ASCII token is a reported fallback, not an error**, carrying
`reason: unreadable` distinct from `missing`. Reasons:

- It is consistent with alternative 1. Nothing in this parser raises.
- `missing` and `unreadable` call for different fixes — one means write a status
  line, the other means write it in the supported vocabulary.
- The repository is bilingual by design: issue bodies carry Korean 요약 sections
  and specs ship a `.ko.md` sidecar. Someone writing `**Status: 진행중**` is
  following the document's own convention into a field that does not support it.
  They deserve a message, not silence.

Lifecycle state names stay ASCII (Non-Goals). This decision is about diagnosing
the input, not accepting it.

## Acceptance Criteria

1. `markdown_status` returns exactly what it returns today for every input, and
   the existing suites pass unchanged.
2. `markdown_status_result` reports `ok`, `missing`, `unreadable` or
   `unrecognised`, and carries the raw token whenever one was present.
3. A file with no status line and a file with an unrecognised token produce
   different reasons.
4. `**Status: 진행중**` yields `unreadable`, not `missing`.
5. `**Status: review**` — the token that actually fired — yields `unrecognised`
   with `review` retained as the raw token.
6. `superseded-by-<id>` yields `ok` and resolves to `superseded`, unchanged.
7. The schema validator emits one diagnostic per non-`ok` issue, naming the
   issue id and the raw token; a valid issue adds no diagnostic.
8. Nothing raises on any input, including empty text and a status line with no
   value.
9. `commands/product-issue.md` documents the supported vocabulary and states
   that an unsupported token is reported and treated as `backlog`.
10. A scan across `issues/` reports the count relying on the fallback; it is 0
    at merge.
11. `python3 scripts/release_check.py .` passes and lifecycle drift is unchanged
    before and after.

## Verification Strategy

- Unit tests over the four reasons, plus the empty-text and empty-value edges.
- The `**Status: review**` case is a regression fixture, not a synthetic one —
  it is the token that fired on 2026-09-05.
- `python3 -m unittest tests.test_project_issue_schema`
- `python3 -m unittest discover -s tests`
- `python3 scripts/project_lifecycle.py . --drift` before and after.
- `python3 scripts/release_check.py .`

## Risks and Open Questions

- **A diagnostic nobody reads is the same as silence.** The validator's output
  has to reach a surface a person looks at — `product:doctor` at minimum. If it
  lands only in a JSON blob, this issue will have moved the silence rather than
  removed it. Worth checking during plan.
- **Whether the validator should escalate to an error later** is deliberately
  left open. Getting the diagnostic right first is the prerequisite for that
  conversation.
- The `unreadable` case has no live example in the corpus — it is reasoned from
  the regex, not measured. Its fixture is synthetic and should say so.

## Human Review Decisions

- [확인만] The non-ASCII decision in section 6 — `**Status: 진행중**` reports
  `unreadable`, not `missing`. Measured: `_markdown_status_token` matches
  `[A-Za-z0-9_-]+`, so a Korean token arrives as "no line at all", which is
  wrong on the facts. Section 6 carries the reasoning.
- [확인만] `review` is not added to the vocabulary. Section 7 alternative 4
  records why: it would make issue 125 parse and fix nothing, because the next
  invented word fails the same silent way. The vocabulary is not the defect.
- [사장님 결정] Whether the diagnostic must reach `product:doctor` before this
  issue can close, or whether that is a follow-up.
  - 왜 이 결정이 필요한가요? 진단을 만들어 놓고 사람이 보는 화면에 안 띄우면,
    침묵을 없앤 게 아니라 옮긴 것뿐입니다. 이 이슈를 어디서 끊을지는 판단입니다.
  - 지금 무엇이 잘못되고 있나요? 이슈 파서가 알 수 없는 상태값을 조용히
    `backlog`로 바꿉니다. 이슈 125의 `**Status: review**`가 그렇게 삼켜졌습니다.
  - 실제로 측정된 예시 — `**Status: review**`가 `backlog`로 보고되었고, 토큰은
    읽힌 뒤 버려졌습니다 (`spec.md:32`, `:40`). 사람도 도구도 모른 채 넘어갔습니다.
  - 다른 선택지와 그 비용 — (가) doctor까지 포함해서 닫는다: 이 이슈가 커지고
    doctor 출력 설계가 딸려 옵니다. (나) 진단만 만들고 doctor는 후속으로 뺀다:
    이 이슈는 작게 끝나지만, 후속을 안 하면 JSON 안에서만 사는 진단이 됩니다.
  - 승인하면 무엇이 달라지나요? 어디까지가 이 이슈인지 정해져서, 계획을 쓸 때
    doctor 출력을 설계에 넣을지 말지가 결정됩니다.

Next command after approval: `product:plan 120-silent-status-fallback-in-issue-parser`.
