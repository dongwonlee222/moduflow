# 한글 검토 패킷: 111-runtime-provenance-and-validation-mode-separation

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-111-runtime-provenance-and-validation-mode-separation.html`
- Draft PR: [#45 — 실행 근거·검증 모드 분리](https://github.com/dongwonlee222/moduflow/pull/45)
- 브랜치: `codex/111-runtime-provenance-and-validation-mode-separation`
- 리뷰어: `Dongwon Lee`

## 이슈 요약

- 제목: Issue 111: Runtime Provenance and Validation Mode Separation
- 설명: 원본 저장소 검사, 설치된 플러그인 검사, 작업 대상 프로젝트 검사를 분리합니다. 상태·Doctor·MCP가 실제 실행 중인 패키지와 프로세스의 근거를 보여주도록 바꿉니다.

## 변경 범위

- 설치 폴더를 프로젝트로 오인해 파일을 만들지 않도록 진입부에서 차단합니다.
- 설치는 준비 → 검증 → 영수증 기록 → 공개 순서로 진행합니다. 같은 버전의 내용이 다르면 기존 캐시를 덮어쓰지 않습니다.
- 패키지 버전·원본 커밋·내용 해시와 실행 프로세스 근거를 구분합니다. 알 수 없는 호스트·스킬 로드 시각은 추정하지 않습니다.
- 소스 버전은 `0.3.55`입니다. 실제 사용자 플러그인 설치·배포·새 세션 적용은 아직 하지 않았습니다.
- 이슈 090·086 계획과 기존 미추적 이슈 103 문서 25개는 이번 PR에 포함하지 않습니다. 공통 로드맵 정리와 이슈 111 상태 기록은 포함됩니다.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/111-runtime-provenance-and-validation-mode-separation/spec.md` | 가능 |
| `plan.md` | 계획 | `specs/111-runtime-provenance-and-validation-mode-separation/plan.md` | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | `specs/111-runtime-provenance-and-validation-mode-separation/tasks.md` | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | `specs/111-runtime-provenance-and-validation-mode-separation/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | `specs/111-runtime-provenance-and-validation-mode-separation/review.md` | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/111-runtime-provenance-and-validation-mode-separation/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/111-runtime-provenance-and-validation-mode-separation/human-review.ko.md` | 가능 |

## 검증 요약

- 이전 구현 검증: `b5c3ce3`에서 전체 1,610개 테스트 통과(337.291초). 근거 기록 커밋 `8229170` 이후 원본 릴리스 검사도 통과했습니다.
- 이번 PR 재검증: `8229170`에서 전체 1,610개 테스트 통과(359.621초, 종료 코드 0, 생략 없음). 구현 코드는 이전 검증 이후 바꾸지 않았습니다.
- 오프라인 시뮬레이션 S01–S12와 패키지 CLI/MCP 점검은 통과했습니다. 실제 Codex·Claude 새 세션 적용 확인(R01/R02)은 아닙니다.
- `dongwonlee222/moduflow`, 기준 브랜치 `main`의 저장소 식별·인증·API 사전 검사가 통과했습니다.
- 검토 문서 커밋 `83b338e`에서도 원본 릴리스 검사 13개 항목이 모두 통과했습니다.
- 브랜치를 원격에 올리고 Draft PR #45를 생성했습니다. 이 문서 기록 시점의 CI는 대기 중이며, 최신 결과는 [PR 검사](https://github.com/dongwonlee222/moduflow/pull/45/checks)에서 확인합니다. 병합·배포·설치는 아직 하지 않았습니다.

원격 검토 링크: [명세](https://github.com/dongwonlee222/moduflow/blob/codex/111-runtime-provenance-and-validation-mode-separation/specs/111-runtime-provenance-and-validation-mode-separation/spec.md), [검증 기록](https://github.com/dongwonlee222/moduflow/blob/codex/111-runtime-provenance-and-validation-mode-separation/specs/111-runtime-provenance-and-validation-mode-separation/status.md), [릴리스·복구 절차](https://github.com/dongwonlee222/moduflow/blob/codex/111-runtime-provenance-and-validation-mode-separation/specs/111-runtime-provenance-and-validation-mode-separation/release.md).

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

- 직접 자기검토를 수행했습니다. 독립 리뷰나 사람의 병합 승인을 받은 것으로 표시하지 않습니다.
- 패키지 검증 전에 심볼릭 링크를 통해 외부 파일을 쓸 수 있던 경로를 차단했고, MCP 오류 응답에도 실행 근거를 남기도록 수정했습니다.
- 기존 보안·문법 검사 테스트의 가짜 원본에 원본 식별 정보를 추가했습니다. 실제 원본·릴리스 검증 기준은 완화하지 않았습니다.
- 확인된 필수 수정 사항은 반영됐습니다. 실제 호스트 관찰과 병합·배포 승인은 남아 있습니다.

## 한계와 배포 주의사항

- 오래된 설치에 영수증이 없으면 근거 누락으로 표시합니다. 현재 실행 환경을 최신 캐시와 같다고 가정하지 않습니다.
- 같은 버전의 다른 패키지는 설치 충돌입니다. 새 버전·빌드 식별자를 선택해야 하며 기존 캐시를 지우지 않습니다.
- 패키지 공개 전 검증과 호스트 설정 복구는 별개입니다. 호스트 설정 전체의 원자적 복구를 보장하지 않습니다.
- 이번 작업은 UI 변경이 없어 데스크톱·모바일 화면 검증 대상이 아닙니다. 위 대시보드는 로컬 읽기용 요약이며 설치 증거가 아닙니다.

## 보류 조건

- 테스트 또는 release check가 실패했습니다.
- 대시보드/상세 페이지가 생성되지 않았거나 최신 변경을 반영하지 않습니다.
- PR diff가 이슈 범위를 벗어났습니다.
- 사람이 이해할 수 있는 한글 개요 또는 검토 패킷이 없습니다.
- 검토 패킷이 최신 PR diff 또는 로컬 변경 범위를 반영하지 않습니다.
- merge/release 승인자와 승인 근거가 명확하지 않습니다.

## 승인 체크리스트

- [ ] 대시보드 DB에서 이슈 상태와 설명을 확인했습니다.
- [ ] 이슈 상세 페이지의 `한글` 탭을 확인했습니다.
- [ ] PR diff 또는 로컬 변경 범위를 확인했습니다.
- [ ] 검증 결과가 통과했거나 실패 사유를 이해했습니다.
- [ ] release 대상이면 rollback/post-release check와 승인 기록을 확인했습니다.
- [ ] 보류 조건에 해당하지 않습니다.

## 다음 액션

- Draft PR과 최신 커밋의 CI 결과를 확인한 뒤 병합 여부를 검토합니다. 자기 PR이라 GitHub 승인이 불가능하면 명시적 승인 기록을 사용합니다.
- 이번 진행 승인은 브랜치 push·Draft PR·CI 확인까지만입니다. 병합과 배포·실제 설치는 별도 승인이 필요합니다.
- 보류하면 `product:review 111-runtime-provenance-and-validation-mode-separation`로 되돌려 수정합니다.
