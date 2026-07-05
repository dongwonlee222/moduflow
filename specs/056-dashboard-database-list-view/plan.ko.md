# 계획: 대시보드 DB/리스트 뷰

> 이 파일은 영문 `plan.md`의 한글 읽기용 sidecar입니다. canonical은 영문입니다.

Issue: `056-dashboard-database-list-view`
Spec: `specs/056-dashboard-database-list-view/spec.md` · Design: `specs/056-dashboard-database-list-view/design.md` · Next: `product:execute 056-dashboard-database-list-view`

## 구현 형태

기존 프로젝트 대시보드 렌더러에 이슈 테이블 데이터 경로를 추가합니다. 현재 그래프 수집기와 패널 생성은 유지합니다.

1. **이슈 row 수집기** (`scripts/project_memory.py`)
   - `_collect_issue_table(root)`를 추가합니다.
   - `issues/*.md`를 파일명 기준으로 안정적으로 스캔합니다.
   - 제목/상태/goal/관계 정보는 가능하면 `_collect_issue_graph(root)`를 재사용합니다.
   - 연결 memory 수는 `_issue_linked_memory(root)`를 재사용합니다.
   - `## Next Command`는 느슨한 markdown regex로 읽습니다.
   - `number`, `href`, `phase`, `artifact_coverage`, `attention_flags`, `relationship_count`, `updated`를 계산합니다.

2. **산출물 커버리지 감지**
   - 테이블 row에서는 전체 파일 읽기보다 파일 존재 체크를 우선합니다.
   - 대상: issue, spec, spec_ko, plan, plan_ko, tasks, tasks_ko, status, review, pr, release, human_review_ko.
   - sidecar는 신호이지 게이트가 아닙니다.

3. **Attention flag 생성**
   - V1 flag:
     - `missing_spec`
     - `missing_plan`
     - `no_next`
     - `no_review`
     - `no_pr`
     - `no_ko`
     - `blocked`
   - JSON key는 영어로 안정화하고 UI label은 한글로 표시합니다.

4. **프로젝트 뷰 템플릿**
   - `const ISSUE_ROWS = __ISSUE_ROWS__;`를 추가합니다.
   - 세 번째 탭 `이슈 DB`를 추가하고 기본 탭으로 둡니다.
   - `이슈 그래프`, `지식 그래프`는 계속 동작해야 합니다.
   - hash 지원:
     - `#issue-db`
     - `#issues`
     - `#memory`

5. **정적 테이블 UI**
   - compact toolbar:
     - search input
     - view chip: `전체`, `진행중`, `리뷰필요`, `막힘`, `누락있음`, `완료`
     - group select: `상태별`, `Goal별`, `없음`
     - sort select: `최근 업데이트`, `이슈 번호`, `상태`, `메모리 수`
   - 기본 컬럼:
     - ID, Issue, Status, Phase, Next, Artifacts, Flags, Memory
   - row 클릭 또는 링크로 `issue-<id>.html`을 엽니다.

6. **대시보드 명령 동작**
   - `--dashboard` 출력 경로는 그대로 `memory/dashboard.html`.
   - `memory/issue-<id>.html`과 memory panel 사전 생성은 유지합니다.
   - 런타임 의존성은 추가하지 않습니다.

## 작업 스트림

### Stream A — 데이터 수집

- `_collect_issue_table(root)` 추가.
- helper 함수 추가:
  - 이슈 번호 추출
  - next command 파싱
  - 산출물 기반 phase 추론
  - artifact coverage
  - attention flag
  - updated date fallback
- 임시 issue/spec/memory 파일로 row 추출 테스트.

### Stream B — HTML/UI 렌더링

- `PROJECT_VIEW_TEMPLATE` 확장.
- `ISSUE_ROWS` payload 추가.
- `issue-db` tab/show 로직 추가.
- table render/search/filter/group/sort 추가.
- graph resize/fit은 graph tab에서만 동작하게 분리.

### Stream C — 검증과 문서

- `tests/test_project_memory.py` 테스트 추가/수정.
- `memory/dashboard.html` 생성 후 시각 확인.
- `product:dashboard` 동작 설명이 낡았다면 command docs 갱신.
- release gate 실행.

## 테스트

`tests/test_project_memory.py`에 집중 테스트를 추가합니다.

- `_collect_issue_table`이 모든 issue file을 나열.
- row에 status/title/next command/artifact coverage/linked memory count/href 포함.
- 누락 필드가 있어도 깨지지 않고 fallback/flag 생성.
- artifact coverage가 영문 파일과 한글 sidecar를 감지.
- `render_project_view`에 다음이 포함:
  - `이슈 DB`
  - `ISSUE_ROWS`
  - search/filter/sort control
  - `issue-` row link pattern
- 기존 memory dashboard, issue graph, panel sidecar, linked memory 테스트는 계속 통과.

## 수동 QA

구현 후:

1. `python3 scripts/project_memory.py . --dashboard` 실행.
2. `memory/dashboard.html` 열기.
3. 기본 탭이 `이슈 DB`인지 확인.
4. `056` 검색.
5. `누락있음` 필터.
6. 이슈 번호/메모리 수 정렬.
7. 056 row를 열어 `memory/issue-056-dashboard-database-list-view.html` 로드 확인.
8. `이슈 그래프`, `지식 그래프`로 전환해 기존 그래프 동작 확인.

## 게이트

- `python3 -m unittest tests.test_project_memory`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`
- 생성된 `memory/dashboard.html` 사람 눈 확인.

## 롤백

추가형 변경이므로 구현 커밋 하나를 revert하면 됩니다.

- `_collect_issue_table`과 helper 제거
- `ISSUE_ROWS` payload 제거
- `이슈 DB` 탭/table UI 제거
- 기존 graph와 issue-panel 코드는 유지

Git 산출물 스키마나 외부 데이터 마이그레이션은 없습니다.

## 범위 밖

- 대시보드 write-back 편집.
- 외부 서비스 sync.
- 칸반/타임라인 구현.
- URL hash 외 저장된 사용자 설정.
- 오른쪽 peek panel.
