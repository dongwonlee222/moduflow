# 이슈 112 명세: 실행 플래너와 백엔드 경계

**상태:** 검토 대기 초안 — 2026-09-05 작성
**책임자:** 이동원
**갱신:** 2026-09-05

이슈: `112-execution-planner-and-backend-boundary`
이전 산출물: `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`,
`docs/superpowers/specs/2026-09-01-execution-governance-scope-design.md` ·
다음: `product:plan 112-execution-planner-and-backend-boundary`

> 정본은 같은 폴더의 `spec.md`입니다. 이 문서는 한국어 읽기용 사이드카입니다.

## 1. 문제

`worker_orchestrator.build_worker_plan`은 `tasks.md`의 체크박스를 전부 워커 작업으로
바꿉니다. 각각에 프롬프트, worktree 이름, 인지부하 힌트가 붙습니다. 의미를 구분하지
않고, 파일 경계를 요구하지 않고, 의존성을 검증하지 않고, `worker-plan.json`과
`worker-plan.md`를 **항상** 씁니다.

2026-09-05 기준 이 저장소(HEAD `a5657dd`, spec 55개)에서 측정한 값입니다.

- 워커 작업 640개가 생성되고 **그중 514개(80%)가 이미 `done`** 입니다.
- **55개 중 39개(71%)** 는 어떤 작업에도 파일·glob 경계를 선언하지 않습니다.
- `Required Gates` 섹션 하나가 체크박스 34개를 차지합니다. 예: *"Issue 102의 수용
  기준 13개 전부에 테스트 또는 상태 근거가 있다."* `WORKER_RULES`(`w_o.py:17`)가
  `acceptance`·`criteria`를 `pm-strategist`로 보내므로, 수용 기준이 **설계상**
  워커 작업이 됩니다.
- 구체적 실패 사례 `specs/001-project-migration`: 남은 미완료 작업은 `Commit and
  push.` 하나입니다. 이것이 `implementation-worker`에 배정되고, worktree
  `codex/001-project-migration-t08`을 받고, 프롬프트에 `Expected files: none`이
  적히고, `dispatchable`로 보고됩니다. 경계가 없는 git 작업이 실행 가능한 구현
  작업으로 제시됩니다.

같은 쓰기 경로에 결함이 둘 더 있습니다.

- `build_worker_plan`이 **절대경로** `project_root`(`w_o.py:430`)를 git 추적
  대상인 `worker-plan.json`에 기록합니다. 한 컴퓨터의 파일 구조가 산출물에
  박힙니다.
- `write_worker_plan`은 `capabilities.write`를 검사하지만(`w_o.py:526`)
  **저장소 신원 게이트가 없습니다.** 형제 쓰기 경로인 `project_execution.main`
  (`p_e.py:349-353`)은 `inspect_repository_identity`와 `operation_decision`을
  호출합니다. 쓰기 경로는 둘인데 신원 검사는 하나입니다. 이건 독립 결함이라
  여기서 고치지 않고 **이슈 122**로 뺐습니다(3절 참조).

결과는 "망가진 플랜"이 아니라 **권위 있어 보이지만 아닌 플랜**입니다. 사람이 매번
플랜 전체를 읽고 어느 줄이 진짜 작업인지 판정해야 하고, 이 코퍼스에서 그 답은
대개 "거의 없음"입니다.

## 2. 목표

1. canonical `tasks.md`에서 미완료·비연기 구현 작업만 선택한다. 결정·Hard Gate·
   수용 기준·검증 게이트·완료된 작업은 절대 워커 작업이 되지 않는다.
2. 추측하지 말고 거절한다. 구체적 파일·glob 경계가 없거나 의존성이 해소되지
   않는 작업이 있으면 worker-plan 파일을 쓰지 않고 `needs_plan`을 반환한다.
3. 실행 경로를 정확히 하나(`inline` 또는 `superpowers-sdd`) 선택하고 그 사유를
   기록하되, dispatch 했다고 주장하지 않는다.
4. 라우팅 결과를 호스트 중립으로 유지해 Claude Code·Codex·Copilot이 canonical
   산출물 변경 없이 같은 결과를 매핑할 수 있게 한다.
5. `spec.md`·`plan.md`·`tasks.md`를 canonical로 유지하고, Superpowers 실행
   상세는 링크만 한다. 완료 진실을 두 곳이 갖지 않게 한다.
6. `project_root`를 저장소 상대경로로 기록한다.

## 3. 비목표

- ModuFlow 안에 스케줄러·큐·에이전트 트리·worktree 엔진·서브에이전트 런타임을
  만들지 않는다. ModuFlow는 선택·상태·근거·정책을 갖고, 실행은 선택된 호스트가
  갖는다.
- Superpowers SDD를 ModuFlow 안에 재구현하지 않는다.
- Spec Kit `implement`를 쓰지 않고, Spec Kit이 git·라이프사이클·리뷰·릴리즈를
  소유하지 않는다.
- 자동 병렬·fleet 모드를 만들지 않는다. `inline`은 정상 성공이다.
- `dispatchable_now()`를 다시 계획하지 않는다(5절 참조).
- 리뷰 상태기계(이슈 113)와 Spec Kit 1.x 어댑터 갱신(이슈 114)은 여기서 다루지
  않는다. 같은 설계 문서가 셋을 함께 다루더라도 마찬가지다.
- 프롬프트 컨텍스트 예산 최적화(이슈 084)는 범위 밖이다.
- 기존 `tasks.md`에 경계 주석을 소급해서 달지 않는다.
- **워커 쓰기 경로의 저장소 신원 게이트는 다루지 않는다.** 결함은 실재하고
  측정됐지만(1절), 이 이슈의 승인·계획·실행을 기다릴 이유가 없는 독립 결함이라
  **이슈 122**로 분리했다.

## 4. 의존 관계

`103 원자적 라이프사이클 트랜잭션`(완료) → **112**(이 명세) → `104 요청
오케스트레이터`(p0) · `113 리뷰 라이프사이클`(p1) · `114 Spec Kit 1.x 어댑터`(p1),
그리고 `104` → `108 운영 승인 게이트`(p1).

103이 완료됐으므로 이 이슈는 착수 가능합니다. 하위 4개를 막고 있으며, 특히 104는
두 번째 계약이 아니라 이 경계를 소비해야 합니다. 도식은 `spec.md` 4절에 있습니다.

## 5. 이미 착지한 것 — 이 명세에서 제외

`dispatchable_now(planned_tasks)`(`w_o.py:225`)와 렌더 결과의 `Dispatchable Now`
섹션(`w_o.py:481`)은 커밋 `ba1269a`로 반영됐고 HEAD의 조상임을 확인했습니다. 이
명세는 이를 다시 계획하지 않습니다.

여기서 6.2절을 구속하는 사실이 하나 나옵니다. `dispatchable_now`는 **완료된 작업에
대한 의존성을 충족으로 처리**합니다(`w_o.py:246`). 관문 2도 같은 의미를 써야
합니다. 반대로 하면 이미 착지한 동작과 모순되고, 어떤 spec이든 자기 작업이
진행될수록 계획 가능에서 거절로 퇴화합니다.

## 6. 관문 계약

`product:workers` **한 번의 실행 안**에 관문 셋이 들어갑니다. 사용자가 실행하는
명령 수는 그대로입니다. 달라지는 건 플래너가 이제 거절할 수 있다는 점입니다.

흐름: `tasks.md` → 관문 1 → 관문 2 → 관문 3 → `inline` 또는 `superpowers-sdd` →
호스트 런타임이 실행. 관문 1에서 실행 가능한 게 없으면 `not_applicable`, 관문 2에서
경계가 빠지면 `needs_plan`(파일을 쓰지 않음). 도식은 `spec.md` 6절에 있습니다.

### 6.1 관문 1 — 의미 필터

다음을 모두 만족할 때 통과시킵니다.

- 체크되지 않았다
- `[deferred → …]`가 아니다
- 속한 섹션이 게이트·근거 섹션이 아니다

섹션 배제는 `Stream <x> —` 접두를 떼어낸 뒤 **전체 이름 일치**로 판정합니다. 대상:
`required gates`, `gates recap`, `acceptance coverage`, `acceptance criteria`,
`verification`, `verification per task`, `converge findings (auto)`, `next`,
`next command`.

전체 이름 일치는 취향이 아니라 필수입니다. `verification` 부분일치는
`Stream 3 — Tests + verification (gate)` 아래의 **진짜 테스트 작성 작업 4건**을
삼키는 것으로 측정됐습니다. 관문 1은 의도적으로 보수적입니다. 애매한 것은 관문
2로 흘려보내고, 거기서 쓸 수 없는 작업이 어차피 거절됩니다.

작업 ID는 원본 파일의 위치로 정해지며 **필터링 전에** 부여합니다. 통과한 작업의
번호는 절대 다시 매기지 않습니다. 사람이 손으로 쓴 `[depends: T01]`은 어떤 작업이
빠지든 같은 원본 줄을 계속 가리켜야 합니다.

### 6.2 관문 2 — 경계 검증

통과한 모든 작업은 `[files:]` 또는 `[globs:]`를 최소 하나 선언해야 합니다. 선언된
모든 의존성은 다른 통과 작업이거나 이미 `done`인 작업으로 해소돼야 합니다. 존재하지
않는 ID나 다른 이슈로 연기된 작업을 가리키면 gap입니다.

관문 2는 **플랜 단위로 fail-closed** 입니다. gap이 하나라도 있으면 플랜 전체를
거절합니다. `worker-plan.json`도 `worker-plan.md`도 쓰지 않고, 결과에 모든 gap을
작업 ID와 함께 나열하며, `next_command`는 `product:plan`입니다.

두 부정 결과를 구분합니다. 실행할 게 없으면 `not_applicable`(끝난 spec), 실행할
작업은 있는데 경계가 없으면 `needs_plan`(작성이 필요한 spec). 같은 사건이
아닙니다.

### 6.3 관문 3 — 경로 선택

백엔드는 정확히 하나, 사유와 함께 기록합니다.

| 조건 | 백엔드 |
| --- | --- |
| 통과 작업이 1개 | `inline` |
| 공유 상태를 건드리는 작업이 있음 | `inline` |
| 두 작업의 경계가 같은 파일에 닿을 수 있음 | `inline` |
| 그 외 | `superpowers-sdd` |

경계 충돌은 **문자열 일치가 아니라 경로 포함 관계**로 판정합니다. glob은 상대
작업의 선언 파일과 대조해야 합니다. `specs/027-reduce-approval-popup-friction`에서
측정: `scripts/*`와 `scripts/` 하위 파일 4개가 서로 무관한 것으로 처리돼 같은
파일에 워커 둘이 병렬 배정됐습니다.

`inline`은 실패 대체가 아니라 정상 성공입니다. 단일파일·순차·맥락공유 작업은
위임하지 말고 직접 하라는 것이 Anthropic의 현재 지침이며
(`knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md` 39행),
벤치마크의 로드맵 결정 1이 이를 요구합니다.

## 7. 결과 스키마

스키마 `moduflow.execution-routing.v1`. 필수 필드는 `schema`, `issue_id`,
`project_root`(저장소 상대경로, 절대경로 금지), `status`(`ok`·`needs_plan`·
`not_applicable`), `backend`(`inline`·`superpowers-sdd`·null), `routing_reason`
(모든 상태에서 비어 있지 않음), `gaps`, `tasks`, `written`(두 거절 상태에서는
빈 배열), `dispatched`(항상 false), `executed_by`(항상 null), `next_command`.

`dispatched`와 `executed_by`를 생략하지 않고 명시 필드로 두는 이유는, "ModuFlow가
실행하지 않았다"를 암시가 아니라 테스트로 단언할 수 있게 하기 위해서입니다.

## 8. 호스트 어댑터 경계

라우팅 결과에는 호스트 고유 값이 없어야 합니다. 지금은 있습니다.
`isolation.worktree`에 `codex/` 접두가 하드코딩돼 있고(`w_o.py:408`), 모든 작업
프롬프트에 OpenAI GPT-5.6 모델명이 `COGNITIVE_DEMAND_GUIDANCE`를 통해
박힙니다(`w_o.py:50-66`, 적용 지점 `w_o.py:388`).

결과는 의미적 의도만 담습니다 — 인지부하, 격리 요구, 파일 경계, 의존 순서.
호스트별 어댑터가 그 의도를 각 호스트의 서브에이전트·worktree·모델 어휘로
번역합니다. 호스트가 늘면 어댑터가 늘 뿐 canonical 산출물은 바뀌지 않습니다.

## 9. Canonical 산출물 소유권

`spec.md`·`plan.md`·`tasks.md`가 유일한 완료 진실입니다. Superpowers 설계·계획
문서는 실행 상세로 링크될 뿐 ModuFlow 작업을 완료 처리할 수 없습니다. 둘이 같은
작업을 다르게 말하면 canonical이 이기고, 그 불일치는 조용히 해소하지 않고
보고합니다.

## 10. 마이그레이션 입장

현재 코퍼스에 적용하면 2개가 플랜을 내고, 19개가 거절되고, 34개가 완료로
인식됩니다. 19개는 살아있는 작업이며 `[files:]` 주석이 붙기 전까지 `needs_plan`을
받습니다.

이 명세는 **fail-closed**를 채택합니다(11절에서 검토한 세 안 중 1안). 거절이 경계
없는 작업의 이름을 정확히 대므로 조치 대상이 열거 가능합니다. 이 이슈가 그 19개에
주석을 달지는 않습니다. 각 spec은 자기 작업을 다음에 집을 때 주석을 답니다.

## 11. 검토한 대안

1. **플랜을 계속 쓰되 `unverified`로 표시 — 기각.** 이 이슈가 없애려는 바로 그
   산출물을 남깁니다. 믿기 전에 사람이 감사해야 하는 플랜은 현재 실패에 이름표만
   바꾼 것입니다.
2. **주석이 하나도 없는 spec은 legacy로 통과 — 기각.** 보이지 않는 파일 이력에
   따라 같은 명령이 다르게 동작하는 2단 구조가 생깁니다.
3. **경계 없는 작업만 버리고 나머지로 플랜 — 기각.** 부분 플랜은 완전한 것처럼
   읽힙니다. 14개 중 12개가 조용히 빠진 플랜은 거절보다 더 위험합니다.
4. **섹션 대신 키워드로 필터 — 기각.** `WORKER_RULES`가 이미 그 실패를 보여줍니다.
   애초에 `acceptance`를 워커로 보내는 게 키워드 라우팅입니다.
5. **ModuFlow가 직접 dispatch — 기각.** 호스트 런타임 기능을 중복 구현하고 낡은
   상태·비용·거짓 실행 주장을 만듭니다(벤치마크 정합성 표, "ModuFlow creates
   another dispatcher").

## 12. 수용 기준

이슈의 기준 7개에 대응합니다. 2026-09-05에 발견한 신원 게이트 결함은 의도적으로
빠져 있습니다 — 이슈 122입니다.

1. 결정문·Hard Gate·수용 기준·검증 게이트·연기 작업·완료 작업은 `tasks`에 절대
   나타나지 않는다.
2. 테스트 작성은 구현 작업이며, 섹션명에 verification이 들어가도 관문 1을
   통과한다.
3. `tasks`의 모든 작업은 파일 또는 glob을 최소 하나 선언하고, 모든 의존성은
   통과 작업이나 완료 작업으로 해소된다.
4. 완료된 작업에 대한 의존성은 충족으로 처리한다(`dispatchable_now`와 동일).
5. 작업을 버려도 통과 작업의 번호는 다시 매기지 않으며 기존 `[depends:]`가
   그대로 해소된다.
6. gap이 있으면 `needs_plan`을 내고, `written`이 비어 있고, 실행 후 디스크에
   `worker-plan.*`가 없으며, `next_command`가 `product:plan`이다.
7. 실행 가능한 작업이 없으면 `needs_plan`이 아니라 `not_applicable`이다.
8. `inline`/`superpowers-sdd` 중 정확히 하나를 반환하고 `routing_reason`이 비어
   있지 않다.
9. 다른 작업의 선언 파일을 덮는 glob이 있으면 `inline`으로 간다.
10. 모든 결과에서 `dispatched`는 false, `executed_by`는 null이다.
11. 모든 결과에서 `project_root`는 저장소 상대경로다.
12. 같은 라우팅 결과가 Claude Code·Codex·Copilot 픽스처에 canonical 산출물 변경
    없이 매핑된다.
13. canonical 산출물과 링크된 Superpowers 상세가 동시에 완료를 주장할 수 없고,
    불일치는 보고된다.
14. 이슈 103 트랜잭션, 구현 준비도, capability 게이트가 그대로 권위를 유지한다.

## 13. 검증 전략

관문 1~3의 프로토타입을 저장소 밖에 만들어 2026-09-05에 55개 spec 전체에
돌렸습니다. 테스트 34개가 통과했고, 그중에는 프로토타입 스캔이 shipped
`parse_tasks`와 모든 spec에서 동일한 결과를 낸다는 동등성 단언이 포함됩니다.
근거와 그 실행이 잡아낸 결함 3건은 이 이슈의 리뷰 패킷에 기록돼 있습니다. 이
실행은 기준 1~11을 원리적으로 덮으며, 저장소 테스트로 재현돼야 합니다.

필요한 픽스처:

- `specs/001-project-migration` — `needs_plan`, 아무것도 쓰지 않음
- `specs/023-worker-routing-and-isolation` — 전부 완료, `not_applicable`
- `specs/029-antigravity-artifact-sync-connector` — **양성 대조군.** 실제 경계와
  `[depends: T01]`을 가진 미완료 작업이 있으므로 쓸 수 있는 플랜이 나와야 한다.
  이것까지 거절하는 관문은 과하다.
- 위 029에서 첫 작업을 체크한 상태 — `ok`를 유지해야 하며 기준 4를 증명한다
- `specs/086-…` — 경계를 가진 연기 작업이 절대 작업이 되지 않아야 한다
- 합성 픽스처: 중간 작업 제거, 존재하지 않는 의존 ID, 연기된 의존, 빈 `- [ ]`,
  `Stream <x> — Verification`, `Stream 3 — Tests + verification (gate)`,
  glob이 파일을 덮는 경우, 서로 다른 트리의 glob 둘
- 기준 12를 위한 Claude Code·Codex·Copilot 교차 호스트 픽스처

기존 스위트는 계속 통과해야 합니다: `tests/test_worker_orchestration.py`,
`tests/test_project_execution.py`, `python3 scripts/release_check.py .`.

## 14. 리스크와 미해결 질문

- **기준 12와 13은 검증되지 않았습니다.** 프로토타입은 선택·거절·라우팅만
  시험했습니다. 호스트 중립 어댑터와 canonical 대 Superpowers 대조는 아직 근거가
  없고, 이 이슈의 구현 리스크가 거기 몰려 있습니다.
- **섹션 배제 목록은 코퍼스에서 뽑은 것입니다.** 앞으로 목록에 없는 게이트 섹션
  이름이 생길 수 있습니다. 관문 2가 피해를 줄이지만 없애지는 못하므로, 목록이
  자랄 자리를 문서로 정해야 합니다.
- **19개 거절은 실제 비용**이며 10절에서 의도적으로 감수했습니다. 실사용에서
  주석 달기가 비현실적으로 드러나면, 가정이 아니라 사용 근거를 들고 1안을 다시
  검토해야 합니다.
- **공유 상태 판정은 여전히 키워드 기반**(`SHARED_STATE_KEYWORDS`, `w_o.py:27`)
  이며 대안 4에서 비판한 약점을 그대로 물려받습니다. 이 이슈의 범위는 아니지만
  믿을 만한 것으로 취급하면 안 됩니다.

## 15. 사람이 승인해야 할 결정

- 플랜 단위 fail-closed와 그 결과인 19개 spec 거절(10절)
- 전체 이름 일치 섹션 배제 목록과 그 확장 경로(6.1절)
- 완료된 작업에 대한 의존성을 충족으로 보는 것(6.2절)
- `inline` 조건, 특히 공유 상태가 `inline`을 강제하는 것

승인 후 다음 명령: `product:plan 112-execution-planner-and-backend-boundary`
