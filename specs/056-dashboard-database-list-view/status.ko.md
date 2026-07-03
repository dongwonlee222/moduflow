# 상태: 대시보드 DB/리스트 뷰

> 이 파일은 영문 `status.md`의 한글 읽기용 sidecar입니다. canonical은 영문입니다.

Issue: `056-dashboard-database-list-view`
Phase: execute complete; review next
Updated: 2026-07-03
Next: `product:review 056-dashboard-database-list-view`

## 구현됨

- Git-native issue/spec/memory 산출물에서 이슈 DB row를 만드는 `_collect_issue_table(root)`를 추가했습니다.
- 이슈 번호 추출, next command 파싱, artifact coverage 감지, phase 추론, attention flag, relationship count, linked memory count, updated-date fallback을 추가했습니다.
- `render_project_view(root)`에 `ISSUE_ROWS`를 추가했습니다.
- `memory/dashboard.html`의 기본 탭으로 `이슈 DB`를 추가했습니다.
- compact search/filter/sort/group control을 추가했습니다.
- ID, Issue, Status, Phase, Next, Artifacts, Flags, Memory 컬럼을 가진 테이블 row를 추가했습니다.
- `이슈 그래프`, `지식 그래프`, 기존 그래프 동작, 사전 생성 issue/memory panel은 유지했습니다.

## 검증

- `python3 -m unittest tests.test_project_memory`
- `python3 -m unittest discover -s tests`
- `python3 scripts/project_memory.py . --dashboard`
- `python3 -m py_compile scripts/project_memory.py`
- 생성 HTML에 `이슈 DB`, `ISSUE_ROWS`, search control, missing filter, 056 issue row link 포함 확인
- 생성 dashboard script가 Node `new Function`으로 parse됨
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`

## 메모

- Playwright 브라우저 자동 검증은 로컬 Playwright browser binary가 없고 설치된 Chrome channel도 sandbox 제약으로 종료되어 수행하지 못했습니다.
- 생성된 `memory/dashboard.html`은 사람 화면 검토용으로 로컬에서 열었습니다.
