---
id: 2026-09-07-overlap-detection-corpus-measurement
kind: evidence
title: Mechanical Overlap Detection Measured Against the Live Issue Corpus
issue_id: 104-project-aware-natural-language-request-orchestrator
spec: specs/104-project-aware-natural-language-request-orchestrator/plan.md
source_event: corpus-measurement
date: 2026-09-07
tags: [overlap, routing, negative-result, measurement]
summary: Four candidate overlap rules were run over 147 issues (10,731 pairs). All four fail. Title similarity scores 0.00 on five of seven confirmed same-work pairs. The plan's open question is answered — stage 2 must surface candidates, not judge them.
---

# 겹침 판정 규칙 — 코퍼스 실측

`specs/104-.../plan.md`의 Open Questions가 **"먼저 재라"**고 적어 뒀습니다.
쟀습니다. 결과는 **음성**입니다 — 넷 다 못 씁니다.

## 무엇을 쟀나

- 대상: `issues/*.md` **147개**, 쌍 **10,731개**
- 정답 집합: 사람이 선언한 "같은 일" 쌍 **220개**
  (`duplicates:` · `supersedes:` · `**Status: superseded-by-NNN**`)

## 결과

| 규칙 | 걸린 쌍 | 맞음 | 정밀도 | 재현율 |
|---|---|---|---|---|
| A. 제목 유사도 ≥ 0.3 | 30 | 7 | 23.3% | 3.2% |
| A. 제목 유사도 ≥ 0.4 | 8 | 2 | 25.0% | 0.9% |
| A. 제목 유사도 ≥ 0.5 | 3 | 2 | 66.7% | 0.9% |
| B. Entry Points 파일 1개 공유 | 310 | 52 | 16.8% | 23.6% |
| C. 파일 2개 이상 공유 | 63 | 25 | 39.7% | 11.4% |
| D. 제목 ≥ 0.3 **그리고** 파일 공유 | 3 | 1 | 33.3% | 0.5% |

제목 유사도는 낱말 Jaccard(불용어 제거, 3글자 이상). 파일은 `## Entry Points`에서
백틱으로 감싼 `scripts/` `commands/` `skills/` `hooks/` `templates/` `workspace/`
경로.

**가장 잘 맞는 규칙(66.7%)이 220쌍 중 2쌍을 잡습니다.** 가장 많이 잡는
규칙(23.6%)은 310건 중 258건이 오탐입니다.

## 확실한 정답으로 재확인

220쌍에는 계보(lineage)가 섞여 있을 수 있어, **2026-09-06~07에 사람이 직접
읽고 합친 7쌍**으로 다시 쟀습니다. 이건 "같은 일"이 확실합니다.

| 쌍 | 제목 유사도 | 공유 파일 수 |
|---|---|---|
| 144 ↔ 142 | **0.00** | 2 |
| 145 ↔ 142 | **0.00** | 1 |
| 138 ↔ 146 | **0.00** | 0 |
| 136 ↔ 123 | **0.00** | 0 |
| 092 ↔ 143 | 0.14 | 1 |
| 118 ↔ 143 | 0.14 | 0 |
| 130 ↔ 129 | **0.00** | 3 |

**일곱 중 다섯이 0.00입니다.** 최대가 0.14입니다. 이 쌍들을 잡는 임계값은
전부를 잡습니다. 파일 공유도 셋이 0입니다.

## 왜 안 맞나

이 쌍들을 실제로 묶은 것은 **낱말이 아니라 모양**입니다.

- 144·145·142 → *"정해놓고 확인 안 함"*
- 136·123 → *"파일이 있는지만 보고 내용을 안 봄"*
- 138·146 → *"진단이 등급·코드를 버리고 한 덩어리로 나옴"*

세 쌍 다 공유 낱말이 0인데 같은 일입니다. 반대로 `dashboard`라는 낱말을 공유하는
이슈들은 (143이 세는 대로) **서로 다른 네 가지**입니다. 낱말은 이 판단에
**신호가 아닙니다.**

## 그래서 계획을 어떻게 바꾸나

**stage 2는 판정하지 않습니다. 후보를 사람에게 내놓습니다.**

- 해석된 프로젝트의 **열린 이슈 제목 + `## 안 고치면` 한 줄**을 요청 맥락에 넣고,
  읽는 쪽(LLM 또는 사람)이 "이건 142 같다"고 말한다.
- 임계값도, 숫자 규칙도 두지 않는다. 위 표가 그 근거다.
- stage 2는 **아무것도 쓰지 않는다.** 묻고 멈춘다.

목표(`workspace/goal.md`)와 같은 방향입니다 — **보관하고 건네주지, 판정하지
않는다.** 그리고 이 7쌍을 실제로 찾아낸 것도 이슈를 읽은 LLM이었습니다.

## 재현

```
$ python3 - <<'EOF'   # 요약: 제목 Jaccard + Entry Points 경로 교집합
  # 147개 이슈, 10,731쌍, 정답 220쌍 (duplicates/supersedes/superseded-by)
EOF
```

전체 스크립트는 이 기록을 만든 세션의 명령 이력에 있습니다. 표의 숫자는
2026-09-07 트리(`git rev-parse HEAD` = 559253a) 기준입니다.

## 한계

정답 220쌍은 **사람이 선언한 것**이라, 선언되지 않은 겹침은 세지 못합니다.
따라서 위 재현율은 **상한이 아니라 알려진 것에 대한 값**입니다. 규칙이 못 잡는
겹침은 표보다 많을 수 있고, 적을 수는 없습니다.
