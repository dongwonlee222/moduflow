# 스펙: Spec Kit 선택형 검증 어댑터

이슈: `098-speckit-selective-validation-adapter`
이전: 이슈 097 라우팅 계약과 사용자 설계 승인 · 다음: `product:plan`

## 결론

전체 Spec Kit을 설치하지 않는다. 공식 0.16.1의 `clarify`, `analyze`, `checklist`,
`converge` 명령 템플릿 4개만 승인된 SHA에 고정하고, ModuFlow 안전 오버레이를 함께
적용한다. 프로젝트가 명시적으로 opt-in하고 사용자가 요청한 경우에만 템플릿 하나를
로드한다.

## 왜 이 방식인가

네 기능은 독립적인 `specify` CLI 서브커맨드가 아니라 에이전트용 Markdown 명령
템플릿이다. 전체 초기화를 사용하면 `.specify`, 스크립트, 훅, 에이전트 명령과 별도
라이프사이클이 생긴다. 이는 “평소에는 가볍고 필요할 때만 사용”한다는 제품 방향과
충돌한다.

선택형 어댑터는 공식 reasoning 패턴은 사용하되 ModuFlow가 이슈, 스펙, 계획, 태스크,
Git, 리뷰, PR, 릴리즈의 소유권을 유지하게 한다.

## 사용자에게 달라지는 점

- 평소에는 Spec Kit 컨텍스트가 전혀 로드되지 않는다.
- 프로젝트에서 한 번 opt-in한 뒤 “스펙킷으로 분석해줘”처럼 요청하면 된다.
- 별도 Spec Kit 명령어나 `.specify` 구조를 기억할 필요가 없다.
- Spec Kit이 없거나 꺼져 있으면 기존 ModuFlow 검사로 안전하게 대체된다.
- 결과에는 사용 함수, 버전, SHA, 입력, 한계, 권한, 산출물과 다음 액션이 표시된다.

## 지원 기능

| 기능 | 동작 | 자동 변경 여부 | 기본 대체 기능 |
| --- | --- | --- | --- |
| `clarify` | 최대 5개 핵심 질문을 한 번에 하나씩 제안 | 스펙 자동 수정 없음 | ModuFlow 짧은 명확화 |
| `analyze` | spec/plan/tasks 정합성과 누락을 읽기 전용 분석 | 없음 | `spec_consistency.py` |
| `checklist` | 요구사항의 완전성·명확성·측정 가능성 체크 후보 생성 | 없음 | 네이티브 수용 기준/준비도 검사 |
| `converge` | 구현 후 남은 작업 후보를 분류 | tasks/code 자동 변경 없음 | `project_converge.py` 보고 모드 |

## 구성

프로젝트별 `.moduflow/capabilities.json`에 `spec-kit.enabled`, 승인 버전/SHA, 허용
함수 목록을 기록한다. 파일이 없거나 꺼져 있거나 버전·무결성이 맞지 않으면 사용
불가로 판단한다. 호스트 가용성과 프로젝트 opt-in이 모두 참이어야 실행 가능하다.

공식 템플릿은 `vendor/spec-kit/0.16.1/commands/` 아래 네 파일만 보관한다. 로컬 정책은
`overlays/spec-kit/selective-validation-policy.md`에 두고, 실제 연결은
`adapters/spec-kit.yaml`과 `scripts/spec_kit_adapter.py`가 담당한다.

## 안전 경계

- upstream 템플릿에 적힌 prerequisite script, shell/PowerShell/Python helper, extension
  hook, Git 명령, handoff, 구현 명령은 실행하지 않는다.
- `.specify` 폴더나 두 번째 스펙 라이프사이클을 만들지 않는다.
- 요청한 함수 템플릿 하나만 로드한다.
- Spec Kit 결과는 advisory이며 ModuFlow 승인 없이 `spec.md`, `plan.md`, `tasks.md`, 코드,
  Git 상태를 수정하지 않는다.
- 결과를 저장할 때는 기존 `specs/<issue>/validation.md`에 append-only로 기록한다.
- 동일 입력·함수·upstream SHA의 중복 실행은 파일을 전혀 바꾸지 않는다.
- 기능/설정/경로/무결성이 불명확하면 실패를 숨기지 않고 네이티브 fallback을 제시한다.

## 검증과 파일럿

네 함수별 성공 1건과 비활성/미설치 1건을 포함해 최소 8개 픽스처를 만든다. 구현,
라이프사이클, Git, 리뷰, PR, 릴리즈 요청이 Spec Kit으로 넘어가지 않는 음성 사례도
검증한다.

파일럿은 함수별로 다음을 기록한다.

- 사람이 인정한 고유한 유용성
- 응답 시간
- 로드된 템플릿·입력 컨텍스트 추정량
- 오탐률
- 기존 ModuFlow 검사와 중복률
- 무단 쓰기, 명령 실행, fan-out, 거짓 실행 주장 여부

어떤 함수도 자동 실행으로 승격하지 않는다. 경계 위반이 0이고 네이티브 검사보다
추가 가치가 있다는 근거가 있어야 별도 이슈에서 노출 수준을 다시 검토한다.

## 완료 기준

- 미설정 프로젝트는 기존과 동일하게 작동한다.
- opt-in 프로젝트는 자연어로 네 기능을 각각 요청할 수 있다.
- 요청당 템플릿 하나만 로드된다.
- 버전/SHA/템플릿 무결성이 고정된다.
- upstream 스크립트·훅·Git·구현 명령이 실행되지 않는다.
- 결과가 이슈, 원본 스펙, 버전, 권한, 한계, fallback과 연결된다.
- Spec Kit이 구현, 라이프사이클, Git, 리뷰, 릴리즈 소유권을 가져가지 않는다.
- 최소 8개 기능/fallback 사례와 음성 경계 사례가 통과한다.
- 무단 쓰기, fan-out, 거짓 실행 주장은 0이다.
- 전체 테스트와 release check가 통과한다.

## 다음 명령

`product:plan 098-speckit-selective-validation-adapter`
