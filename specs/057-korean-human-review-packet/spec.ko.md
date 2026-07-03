# 스펙: 한글 사람 검토 패킷

> 이 파일은 영문 `spec.md`의 한글 읽기용 sidecar입니다. canonical은 영문입니다.

Issue: `057-korean-human-review-packet`

## 문제

ModuFlow는 토큰 비용과 도구 호환성을 위해 주요 산출물을 영어 canonical로 작성해 왔습니다. 이 선택은 여전히 유효하지만, 사람이 PR을 승인할 때는 불편합니다. 한국어 사용자가 모든 영문 spec, plan, review, PR handoff를 읽어야만 승인 여부를 판단하는 흐름은 맞지 않습니다.

## 목표

- 영어 산출물은 canonical로 유지합니다.
- PR, review, release 게이트에서 한국어 우선 검토 표면을 제공합니다.
- `product:pr` 실행 시 이슈별 `human-review.ko.md`를 자동 생성합니다.
- 대시보드 이슈 상세 페이지에서 모든 이슈가 최소한 한글 개요를 갖게 합니다.
- full 한글 sidecar가 없는 경우도 숨기지 않고 검토 한계로 보이게 합니다.
- 리뷰어는 한글 패킷부터 보고, 필요할 때만 영문 원문으로 내려갑니다.

## 비범위

- 런타임 번역 API는 사용하지 않습니다.
- 한글을 canonical로 바꾸지 않습니다.
- 기존 모든 산출물의 전체 소급 번역을 요구하지 않습니다.
- 자동 승인이나 자동 merge는 하지 않습니다.
- 검토되지 않은 기계 번역을 검토 완료된 한글 문서처럼 보이게 하지 않습니다.

## 설계

계층 구조로 해결합니다.

1. 영어 canonical 산출물은 계속 진실의 원천입니다.
2. `spec.ko.md`, `plan.ko.md`, `tasks.ko.md`, `review.ko.md` 같은 한글 sidecar는 사람이 읽는 대응 문서입니다.
3. `workspace/issue-descriptions.ko.json`은 대시보드 스캔용 짧은 한글 이슈 설명입니다.
4. 이슈 상세 페이지는 이 설명을 사용해 모든 이슈에 `한글 개요`를 제공합니다.
5. `human-review.ko.md`는 PR 게이트용 한글 검토 패킷입니다. 변경 요약, 확인할 항목, 검증 결과, 보류 조건, 승인 체크리스트를 담습니다.

## 제품 동작

`product:pr {issue}`는 다음 명령을 실행합니다.

```bash
python3 scripts/project_pr.py <project-path> --issue-id {issue} --write
```

생성되는 파일:

- 해당 이슈의 `pr.md`
- 해당 이슈의 `human-review.ko.md`

한글 패킷에는 다음 링크가 들어갑니다.

- `memory/dashboard.html#issue-db`
- 대시보드 이슈 상세 페이지
- PR URL 또는 local PR-ready marker
- 핵심 source artifact

## 대시보드 동작

이슈 DB 리스트는 가능한 경우 한글 설명을 보여줍니다.

이슈 상세 페이지의 `한글` 탭은 다음을 보여줍니다.

- 모든 이슈의 한글 개요.
- 존재하는 full 한글 sidecar.
- `human-review.ko.md` 같은 한글-only artifact.

## 승인 기준

- `project_pr.py --write`가 `pr.md` 옆에 `human-review.ko.md`를 생성합니다.
- `pr.md`가 한글 패킷을 링크합니다.
- `product:pr`, `product:review` 문서가 한글 패킷부터 검토하라고 안내합니다.
- dashboard issue detail page가 full sidecar가 없어도 한글 개요를 보여줍니다.
- 패킷 생성과 상세 페이지 한글 개요 테스트가 있습니다.
- `python3 scripts/release_check.py .`가 통과합니다.

## 다음 명령

`product:plan 057-korean-human-review-packet`
