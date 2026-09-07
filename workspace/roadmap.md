# ModuFlow Roadmap

## 2026-09-07 — 목표 확정 후 열린 이슈 42건 재판정

기준은 `workspace/goal.md`입니다. 이슈 하나마다 물었습니다 — **이걸 안 고치면
누가 무엇을 못 하는가**, 그리고 그 답이 목표의 일곱 가지(히스토리·메모리·
이슈·로드맵·플레이북·프로세스·스킬) 중 어디를 막는가.

**42건 → 열린 이슈 31건, 그중 진행 대상 27건.** 아래는 전부 2026-09-07에
**적용 완료**했습니다 — 제안이 아니라 파일에 반영된 상태입니다.

### 닫았다 — 5건

목표 어디도 막지 않습니다.

| 이슈 | 왜 |
|---|---|
| `082-cross-host-model-capability-routing` | 112가 호스트 어댑터로 실물 제공. `claude-code`·`codex`·`copilot` 셋이 같은 모양으로 꽂혀 있음 |
| `083-model-routing-evaluation-harness` | 모델 라우팅이 품질을 올리는지 재는 장치. 답이 없어서 막히는 일이 없음 |
| `084-worker-prompt-context-budget` | 워커 지시문이 길어서 실패한 사례 0건 |
| `114-speckit-selective-adapter-1x-compatibility` | 어댑터가 꺼져 있고 켤 계획이 없음. 목표 「안 하는 것」에 "Spec Kit 전체 구현 아님" 명시 |
| `139-five-scripts-have-a-cli-that-nothing-reaches` | 안 불리는 915줄. 동작에 영향 없음 — 정리 대상이지 이슈가 아님 |

### 합쳤다 — 6건이 3건으로

같은 병을 따로 고치면 같은 장치를 두 번 만듭니다.

| 흡수되는 것 | 어디로 | 왜 |
|---|---|---|
| `092-project-home-dashboard`, `118-portfolio-mode-dashboard` | `143` | 대시보드가 이미 넷. 다섯째·여섯째를 만들 게 아니라 넷의 이름부터 정해야 함 |
| `144-the-type-token-is-instructed-not-enforced`, `145-the-verification-plan-is-a-convention-nobody-requires` | `142` | 셋 다 "정해놓고 확인 안 함". 142가 그 검사 자리를 만듦 |
| `138-unsafe-transaction-advice-drops-the-error-code` | `146` | 둘 다 진단이 등급·코드를 버리고 한 덩어리로 나옴. 146이 findings 배열을 만듦 |
| `136-auto-playbook-checks-are-never-executed` | `123` | 둘 다 파일이 **있는지**만 보고 **내용**을 안 봄 |

### 보류 — 4건

범위 안이지만 지금 열 수 없습니다. **닫지 않습니다.**

| 이슈 | 무엇을 기다리나 |
|---|---|
| `107-shared-approved-playbook-layer` | 팀. 공유할 조직이 아직 없음 |
| `108-production-approval-and-verification-gates` | 팀. 승인자가 한 명 |
| `094-risk-based-security-and-quality-review-gate` | 팀. 어댑터를 고를 사람이 한 명 |
| `121-constitution-amendment-invalidates-pilot-evidence` | 헌법 C12 결정. 넣기로 하면 즉시 실물이 됨 |

### 올렸다 — 2건이 p1 → p0

완료 조건 ②(**다른 사람·다른 컴퓨터가 받아도 똑같이 동작한다**)에 정면으로
걸립니다. 기존 p0 `105`와 같은 줄입니다.

- `133-only-one-person-can-work-at-a-time` — 두 컴퓨터에서 활성 이슈 칸을 서로 덮어씀. 사장님이 두 대를 쓰심
- `141-adoption-reports-success-on-an-incomplete-setup` — 기존 프로젝트를 들여오면 clone 후 깨짐

### 목표가 실제로 바꾼 판정은 3건뿐입니다

나머지는 기준 없이 냈던 판정과 같았습니다. 부풀리지 않고 적습니다.

1. **`107` — 닫기 후보에서 빠졌습니다.** 이전 기준("맥락·기록·결정·다음 액션")에
   **플레이북 자리가 없어서** "아무도 안 막힌다"로 나갔습니다. 새 목표에
   플레이북이 명시되면서 **범위 안**이 됐습니다.
2. **`136` — p2에서 p1 격상 후보.** 같은 이유입니다. 플레이북을 보관만 하고
   지켜지지 않으면 보관의 값이 없습니다.
3. **`094` — 닫기에서 보류로.** 108과 똑같이 팀을 기다리는 것인데 하나만
   닫으려 했습니다. 기준이 아니라 제 일관성 문제였습니다.

### 다음

`104` 활성 유지 → 실행. 그 뒤 p0 셋(`105`·`133`·`141`).

---

## 지난 기록

2026-09-02 이후의 636줄을 2026-09-07에 지웠습니다. 「Now」가 `090`을 진행 중으로
적고 있었는데 `090`은 done이었습니다. 다음 세션이 그걸 읽고 이미 끝난 일을
진행 중으로 취급하는 것이 남겨 두는 것보다 비쌉니다.

지운 내용은 git 이력에 있습니다 — `git show e2bd4a6:workspace/roadmap.md`.
