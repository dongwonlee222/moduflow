---
id: 2026-09-07-unreferenced-is-a-detection-result-not-a-fact
kind: decision
title: "안 불린다"는 탐지 결과이지 사실이 아니다 — 이 저장소는 동적 로드로 잇는다
issue_id: 139-five-scripts-have-a-cli-that-nothing-reaches
spec: 
source_event: 2026-09-07 로드맵 3단계에서 14개를 손으로 확인
source_artifacts:
  - issues/139-five-scripts-have-a-cli-that-nothing-reaches.md
review_after: 
supersedes: []
superseded_by: []
depends_on: []
references:
  - workspace/roadmap.md
storage_policy: local
mirror_targets: []
owner: Dongwon Lee
date: 2026-09-07
tags: [detection, weight, correction]
summary: "안 불리는 코드가 무게다"라는 가설을 버린다. 정규식 스캔이 세 번 다른 답(915·6,735·5,929줄)을 냈고, 손으로 확인하니 334줄이었다. 이 저장소는 release_check·project_doctor·.mcp.json이 동적 로드로 스크립트를 부르므로, import 문과 python3 호출만 세는 어떤 스캔도 틀린다.
rationale: 세 번의 스캔이 세 번 다른 답을 냈다는 것 자체가 방법이 틀렸다는 증거다. 손으로 14개를 확인하니 12개가 쓰이고 있었고, 부르는 방식이 load_script_module 과 spec_from_file_location 이었다. 실제로 안 불리는 것은 334줄이고 그마저 config/project-operation-entrypoints.json 에 등록돼 있어 확정이 아니다.
evidence: release_check.py:382 load_script_module("canonical_path_guard", ...) · project_doctor.py:87 spec_from_file_location("project_loop", path) · .mcp.json 이 mcp_server.py 를 부름 · commit_resolution 은 linkage_check 가, commit_graph 는 commit_resolution 이 부름. canonical_path_guard 는 2026-09-07 에 실제로 커밋 하나를 막았다.
alternatives: import 추적 도구를 만든다 — 또 도구를 만드는 것이고 그것이 틀리면 같은 자리로 돌아오므로 기각. 334줄을 새 이슈로 낸다 — 아무것도 막지 않고 등록 파일에 이름이 있어 판단 근거가 없으므로 기각.
reversal_conditions: 무엇을 지우려면 손으로 확인한다. 자동 탐지 결과를 근거로 코드를 지우지 않는다. 동적 로드를 세는 방법이 생기면 그때 다시 잰다.
confidence: high
---

# "안 불린다"는 탐지 결과이지 사실이 아니다

## Summary

**"안 불리는 코드가 무게다"라는 가설을 버린다.** 걷어낼 것을 찾으러 갔는데
걷어낼 것이 없었다.

## Rationale

같은 질문에 세 번 다른 답이 나왔다.

| 방법 | 결과 |
|---|---|
| 정규식 (`commands/`·`skills/`·`hooks/`) | 14개 / 6,735줄 |
| 정규식 (문서까지 포함) | **0개** |
| 정규식 (실행 경로만) | 13개 / 5,929줄 — **오늘 직접 배선한 `request_routing` 까지 고아로 찍음** |
| **손으로 하나씩** | **2개 / 334줄** |

세 번 다르다는 것 자체가 방법이 틀렸다는 증거다.

## Evidence

**이 저장소는 동적 로드로 잇는다.** `import` 문도 `python3 X.py` 도 아니다:

```
scripts/release_check.py:382
  canonical_path_guard = load_script_module("canonical_path_guard", "scripts/canonical_path_guard.py")

scripts/project_doctor.py:87
  spec = importlib.util.spec_from_file_location("project_loop", path)
```

손으로 확인한 14개 중 **12개가 쓰이고 있었다.** `release_check` 가 다섯,
`project_doctor` 가 둘, `.mcp.json` 이 하나, `validate_moduflow` 가 셋,
`commit_resolution` 이 하나를 부른다.

`canonical_path_guard` 는 **2026-09-07에 실제로 커밋 하나를 막았다** — 내가
`root / "issues"` 를 직접 이어 붙였을 때다. 죽은 코드가 아니라 일하는 게이트다.

## Alternatives

- **import 추적 도구를 만든다** — 또 도구를 만드는 것이고, 그것이 틀리면 같은
  자리로 돌아온다. 기각.
- **334줄을 새 이슈로 낸다** — 아무것도 막지 않고, 둘 다
  `config/project-operation-entrypoints.json` 에 등록돼 있어 "죽었다"고 단정할
  근거가 없다. 기각.

## Reversal Conditions

**무엇을 지우려면 손으로 확인한다.** 자동 탐지 결과를 근거로 코드를 지우지
않는다. 동적 로드를 세는 방법이 생기면 그때 다시 잰다.

## 같은 날 세 번째 반복

- `114`(spec-kit) — "안 쓴다" → 실은 **못 쓴다**
- `139`(안 불리는 코드) — "안 불린다" → 실은 **탐지가 못 찾는다**

둘 다 관찰은 맞았고 결론이 틀렸다. **관찰과 원인은 다르다.**
