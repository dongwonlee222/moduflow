# 계획: 한글 사람 검토 패킷

> 이 파일은 영문 `plan.md`의 한글 읽기용 sidecar입니다. canonical은 영문입니다.

Issue: `057-korean-human-review-packet`
Spec: `specs/057-korean-human-review-packet/spec.md` · Next: `product:execute 057-korean-human-review-packet`

## 구현 방향

영어 canonical 산출물은 유지하면서, 사람이 PR/review/release를 확인할 때는 한글 검토면을 먼저 보도록 표준화합니다.

056에서 이미 기본 기능을 dogfood했습니다.

- `project_pr.py --write`가 `human-review.ko.md`를 생성합니다.
- `product:pr`가 GitHub preflight와 local PR-ready fallback을 문서화합니다.
- 이슈 상세 페이지가 생성된 `한글 개요`를 보여줍니다.
- `workspace/issue-descriptions.ko.json`이 모든 이슈의 한글 설명을 제공합니다.

057은 이 흐름을 정식 제품 규칙으로 굳히고, release/review 게이트에서 빠지지 않도록 보강합니다.

## 작업 흐름

1. PR 패킷 생성기
   - `pr.md`와 `human-review.ko.md`를 함께 생성합니다.
   - 한글 패킷에는 대시보드, 상세 페이지, 검증 결과, 보류 조건, 승인 체크리스트가 들어갑니다.

2. 명령 계약
   - `product:pr`는 GitHub PR 생성 전 preflight를 반드시 실행합니다.
   - `product:review`는 한글 패킷을 첫 검토 표면으로 안내합니다.
   - `product:release`는 한글 패킷과 승인 기록을 release 조건에 포함합니다.

3. 대시보드 상세
   - 모든 이슈에 최소한 `한글 개요`를 보여줍니다.
   - full 한글 sidecar가 있으면 같이 보여줍니다.
   - `human-review.ko.md` 같은 한글-only artifact도 보여줍니다.

4. 검증
   - packet 생성 테스트
   - GitHub preflight 테스트
   - 이슈 상세 한글 개요 테스트
   - release gate 전체 통과

## 남은 핵심 작업

- `commands/product-release.md`에 한글 패킷/승인 기록 확인을 명시합니다.
- 057 실행 후 review/pr/human-review artifact를 생성합니다.
- 전체 테스트와 release check를 다시 통과시킵니다.

## 다음 명령

`product:execute 057-korean-human-review-packet`
