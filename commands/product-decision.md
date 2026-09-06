---
description: 정한 것을 이유와 함께 남깁니다. 한 문장이면 됩니다. (record a decision)
argument-hint: "<title> [--issue-id id] [--spec path]"
---


# /product:decision

Record why a product or technical decision was made.

## 사용 예시

```
/moduflow decision 로그인은 이메일부터 만든다
/moduflow decision build email login first
```

## Script

```bash
python3 scripts/project_knowledge.py . --kind decision --title "Payment priority" --issue-id 003-payment --spec specs/003-payment/spec.md --decision-supported "Prioritize card onboarding"
```

## 한 문장으로 받기 (issue 131)

한 문장이면 기록이 만들어집니다. 나머지는 먼저 **찾아본 뒤에** 묻습니다.

```
/moduflow 결정으로 남겨줘: 로그인은 이메일부터
/moduflow decision build email login first
```

1. 이슈·이유·다른 선택지·근거를 **대화와 프로젝트 문서에서 먼저 찾습니다.**
2. 찾은 것은 묻지 않습니다.
3. 이유를 도저히 복원할 수 없을 때만, **정확히 한 개** 묻습니다:
   `이 선택을 한 가장 큰 이유가 무엇이었나요?`

Ask **at most one** follow-up question. Two questions is a defect, not
thoroughness — the person already told you the decision.

## 화면에 보일 이름

저장되는 키는 그대로 두고, 사람에게는 이 문장으로 보여줍니다.

| 저장 키 | 화면 |
| --- | --- |
| `rationale` | 왜 이렇게 정했나요? |
| `alternatives` | 다른 선택은 무엇이었나요? |
| `reversal_conditions` | 언제 이 결정을 뒤집나요? |
| `retrieval_trigger` | 언제 다시 살펴보면 될까요? |
| `evidence` | 참고한 자료가 있나요? |

Never print the left column to a reader. The keys do not change.

## Required Fields

- issue ID when applicable
- spec path when applicable
- decision supported
- evidence
- next action

`caveats` was listed here and is written by nothing — it appears in neither
`scripts/project_knowledge.py` nor `scripts/project_memory.py`. Removed rather
than implemented; `reversal_conditions` is the field that actually carries
"when does this stop being true".

## Next

- `/moduflow evidence` to review supporting material
- `/moduflow roadmap` when priority changes

## Record Contract (issue 075)

Every decision record this command writes carries shared frontmatter so `product:promote` and retention tooling can operate on it:

- `kind`: `decision`
- `date`: ISO date
- `summary`: one line
- `retrieval_trigger`: when a future session should re-read this record (semantic cue, required for new records)
- `promoted_to`: issue id, written by `product:promote` only
- `superseded_by`: record id — supersede, never delete or move record files

Write discipline (AI writers create records for free, so creation is NOT the default):

1. Before creating, search existing records of this kind for the same subject.
2. Prefer UPDATE (extend the existing record) or SUPERSEDE (new record + `superseded_by` on the old one) over ADD.
3. NOOP when nothing genuinely new — do not write a file to log activity.
