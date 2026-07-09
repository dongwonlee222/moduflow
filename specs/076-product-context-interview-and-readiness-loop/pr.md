# PR 핸드오프: 076-product-context-interview-and-readiness-loop

## 요약

모두플로의 요청 라우터를 “명확한 요청은 빠르게 이슈 생성, 애매하거나 전략적인 요청만 짧게 shaping”하는 구조로 개선했습니다.

핵심 변경:

- `scripts/project_intake.py`에 `fast`, `short`, `panel` shaping 경로를 추가했습니다.
- 명확한 실행 요청은 질문 없이 `product:issue`로 갑니다.
- 제품 채택, 포지셔닝, 전략처럼 맥락이 부족한 요청은 `product:opportunity`로 보내고 1-3개 질문만 생성합니다.
- 실제 요청 예시 13개를 회귀 테스트로 고정했습니다.
- README와 `product:*` 명령 문서에 “AI가 제품 맥락을 잊지 않게 하는 작업 루프” 포지셔닝과 adapter 기반 방법론을 반영했습니다.
- 후속 개선 이슈 077-080을 등록했습니다.

## PR 정보

- PR: `https://github.com/dongwonlee222/moduflow/pull/12`
- 브랜치: `codex/076-product-context-interview-and-readiness-loop`
- 원격 브랜치: `origin/codex/076-product-context-interview-and-readiness-loop`
- 리뷰어: `Dongwon Lee`
- 상태: Draft PR
- 병합 조건: 사람 승인, PR diff 확인, 필요한 상태 체크 통과

## 사람이 먼저 볼 것

- 한글 검토 패킷: `specs/076-product-context-interview-and-readiness-loop/human-review.ko.md`
- 이슈: `issues/076-product-context-interview-and-readiness-loop.md`
- 스펙: `specs/076-product-context-interview-and-readiness-loop/spec.md`
- 계획: `specs/076-product-context-interview-and-readiness-loop/plan.md`
- 리뷰 노트: `specs/076-product-context-interview-and-readiness-loop/review.md`

## 검증

- RED 확인: 신규 intake 테스트가 구현 전 실패했습니다. 실패 원인은 `shaping_path` 필드 부재와 애매한/전략 요청이 기존 `create_issue`로 가는 동작이었습니다.
- GREEN 확인: `python3 -m unittest tests.test_project_intake.ProjectIntakeTests -v` 통과, 13 tests OK.
- `python3 scripts/validate_moduflow.py .` 통과.
- `python3 scripts/validate_project_artifacts.py .` 통과. 기존 optional memory warning만 있습니다.
- `python3 scripts/release_check.py .` 통과.

## 테스트한 요청 예시

빠른 이슈 생성으로 유지:

- `README 문구 개선 이슈 만들어줘`
- `로그인 버그 수정하고 테스트 추가해줘`
- `경쟁사 조사해서 벤치마크 문서 만들어줘`
- `대시보드 지표가 왜 떨어졌는지 분석해줘`
- `결제 API 구현 계획 이슈 만들어줘`

짧은 shaping 또는 panel shaping으로 라우팅:

- `사용자들이 모두플로를 안 쓰는 이유 찾아줘`
- `모두플로 온보딩 개선 방향 잡아줘`
- `AI 작업 루프 제품 전략 다시 정리해줘`
- `모두플로 인기가 없는 이유 개선해줘`

복합 실행 요청은 goal graph로 라우팅:

- `사업계획서 만들고 랜딩 디자인하고 결제 기능 구현해줘`

## 리뷰 결과

차단 이슈는 없습니다.

남은 리스크:

- 현재 라우팅은 키워드 기반 휴리스틱입니다. 실제 사용 예시가 더 쌓이면 회귀 테스트를 추가하면서 조정해야 합니다.
- `dev`, `design`, `data`, `docs`, `ops`, `research`, `business`처럼 실행 도메인이 명확하면 `왜`나 `개선`이 들어가도 fast path로 둡니다. 전략 질문에 실행 도메인 단어가 섞인 경우 false negative가 생길 수 있어 후속 튜닝 대상입니다.
- panel shaping은 실제 다중 에이전트 엔진이 아니라 압축된 라우팅 메타데이터와 문서 규칙으로 구현했습니다. 실제 skill matrix 자동화는 079에서 다룹니다.

## 운영 원칙

앞으로 라우터나 discipline 추천을 최적화할 때는 감으로 바꾸지 않고, 여러 실제 요청 예시를 모아 회귀 테스트로 고정한 뒤 RED/GREEN으로 조정합니다.

## 다음 액션

1. PR diff를 확인합니다.
2. `human-review.ko.md` 기준으로 사람이 검토합니다.
3. 괜찮으면 Draft 해제 후 approve/merge합니다.
4. merge 후 `product:release 076-product-context-interview-and-readiness-loop`를 진행합니다.
