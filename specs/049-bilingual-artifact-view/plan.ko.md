# 계획: 이중 언어 산출물 뷰

이슈: `049-bilingual-artifact-view`
명세: `specs/049-bilingual-artifact-view/spec.md` · 다음: `product:execute 049`

> 영문 `plan.md`의 한글 읽기용 sidecar입니다. canonical은 영문.

## 변경 (작음 — 047 패널 확장)

1. **`_collect_issue_artifacts`** (`project_memory.py`): 각 산출물에 `<이름>.ko.md` 형제를 `ko` 필드로 첨부(없으면 `null`); `*.ko.md`는 별도 산출물로 나열하지 않음.
2. **`ISSUE_PANEL_TEMPLATE` / `render_issue_panel`**: `English / 한글` 토글 추가(sidecar가 1개 이상 있을 때만 표시). 렌더를 `renderArtifacts()` 함수로 리팩토링; **영문 모드는 모든 산출물을 영문으로, 한글 모드는 한글본이 있는 산출물만 한글로** 표시(없으면 숨김). 기본 영문. 토글 시 Mermaid 재실행.
3. **정책** (`commands/product-spec.md`): 신규 산출물 작성 시 `.ko.md` sidecar를 함께 쓴다고 문서화 — 컨벤션일 뿐 게이트 아님. 영문은 canonical 유지.

## 테스트 (`tests/test_project_memory.py`)

- sidecar 첨부: `spec.ko.md` 있으면 산출물에 `ko`; `*.ko.md`는 별도 산출물로 안 나옴.
- 패널: sidecar 있으면 토글 마크업 존재; 없으면(어지럽힘 없음) 없음.
- 폴백: 페이로드에 영/한 본문이 모두 들어가 클라이언트가 전환 가능; sidecar 없는 산출물은 `ko: null`.

## 게이트

- `python3 -m unittest tests.test_project_memory` + `release_check` exit 0.
- Dogfood: `specs/049-bilingual-artifact-view/spec.ko.md`·`plan.ko.md` 작성 후 토글 렌더 확인.

## 범위 밖

- stale sidecar drift 게이트(향후 `--drift` 확장으로 노트); 기존 명세 소급 번역; 기계 번역; 한글 canonical.
