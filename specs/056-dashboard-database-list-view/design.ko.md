# 디자인: 대시보드 DB/리스트 뷰 화면 구성

> 이 파일은 영문 `design.md`의 한글 읽기용 sidecar입니다. canonical은 영문입니다.

Issue: `056-dashboard-database-list-view`
Spec: `specs/056-dashboard-database-list-view/spec.md`
Next: `product:plan 056-dashboard-database-list-view`

## 참고 패턴

- Notion: 하나의 canonical database를 여러 view로 보여주고, view별 필터/정렬/group/property 표시/page open 방식을 가집니다.
- Jira: 프로젝트 추적은 list/board/timeline/calendar 같은 여러 view를 전제로 하며, 상태/의존성/리포팅이 중요합니다.
- Linear: custom view는 저장 가능한 필터링된 issue/project/initiative 리스트 또는 보드입니다. review-ready 같은 목적형 view가 중요합니다.
- GitHub Projects: project item은 field 기반이며 table/board/roadmap류 view에서 필터와 grouping을 적용합니다.

참고 링크:

- https://www.notion.com/help/views-filters-and-sorts
- https://www.atlassian.com/software/jira/features
- https://linear.app/docs/custom-views
- https://docs.github.com/en/issues/planning-and-tracking-with-projects

## 디자인 결정

`이슈 DB`를 매일 보는 운영 화면으로 둡니다. `이슈 그래프`와 `지식 그래프`는 관계/지식 확인용 보조 view로 유지합니다. 대시보드는 외부 DB나 새 앱이 아니라, 하나의 로컬 이슈 데이터셋을 여러 관점으로 보는 workbench가 됩니다.

V1:

1. `이슈 DB`
2. `이슈 그래프`
3. `지식 그래프`

V2:

1. `칸반`
2. `타임라인`
3. 저장 가능한 필터 hash
4. 오른쪽 상세 preview

## 화면 레이아웃

```text
ModuFlow 프로젝트 뷰

[ 이슈 DB ] [ 이슈 그래프 ] [ 지식 그래프 ] [ 칸반(후속) ] [ 타임라인(후속) ]

┌──────────────────────────────────────────────────────────────────────────┐
│ Search  [ 056 dashboard ...                                      ]       │
│ View    [전체] [진행중] [리뷰필요] [막힘] [누락있음] [완료]              │
│ Group   [상태별 v]       Sort [최근 업데이트 v]       Columns [설정]    │
└──────────────────────────────────────────────────────────────────────────┘

+------+-----------------------------+----------+----------+----------------------+-------------------+--------+--------+
| ID   | Issue                       | Status   | Phase    | Next                 | Artifacts         | Flags  | Memory |
+------+-----------------------------+----------+----------+----------------------+-------------------+--------+--------+
| 056  | Dashboard DB/List View      | active   | plan     | product:plan 056     | I S KO - - -      | no PR  | 0      |
| 057  | Korean Review Packet        | backlog  | spec     | product:spec 057     | I - - - - -       | no spec| 0      |
| 034  | Memory Capture Workflow     | done     | release  | -                    | I S P R PR Rel KO |        | 3      |
+------+-----------------------------+----------+----------+----------------------+-------------------+--------+--------+

Row click -> memory/issue-056-dashboard-database-list-view.html
```

## 상단 탭

작업 스캔을 우선합니다.

1. `이슈 DB` — 기본 탭. "지금 뭘 봐야 하지?"에 답합니다.
2. `이슈 그래프` — 관계/의존성 구조 확인.
3. `지식 그래프` — memory/decision/evidence 확인.
4. `칸반` — 후속. 상태별 이동 view.
5. `타임라인` — 후속. 날짜 메타데이터가 충분할 때 계획 view.

Deep link:

- `#issue-db`
- `#issues`
- `#memory`

## 툴바

툴바는 설명용이 아니라 운영용으로 작게 둡니다.

- Search: id/title/next command 검색.
- View chip:
  - `전체`
  - `진행중`
  - `리뷰필요`
  - `막힘`
  - `누락있음`
  - `완료`
- Group:
  - `상태별`
  - `Goal별`
  - `없음`
- Sort:
  - `최근 업데이트`
  - `이슈 번호`
  - `상태`
  - `메모리 수`
- Columns:
  - v1에서는 생략하거나 비활성 버튼으로 둘 수 있습니다.
  - v2에서 컬럼 hide/show를 지원합니다.

## 테이블 컬럼

기본 노출 컬럼:

| Column | 목적 |
| --- | --- |
| `ID` | 빠른 이슈 lookup과 정렬 |
| `Issue` | 사람이 읽는 제목 |
| `Status` | 운영 상태 |
| `Phase` | 산출물 기반 workflow phase |
| `Next` | 다음 실행 명령 |
| `Artifacts` | 산출물 커버리지 badge |
| `Flags` | 주의 신호 |
| `Memory` | 연결 memory 수 |

후속 선택 컬럼:

- `Goal`
- `Updated`
- `Relations`
- `Owner`
- `PR`
- `Review`

## 산출물 Badge

긴 설명 대신 짧은 badge를 씁니다.

```text
I      issue file 있음
S      spec.md 있음
KO     spec.ko.md 또는 한글 review sidecar 있음
P      plan.md 있음
T      tasks.md 있음
R      review.md 있음
PR     pr.md 있음
Rel    release.md 있음
```

누락은 조용하지만 스캔 가능하게 표시합니다.

```text
I S KO - - -
```

## Attention Flag

flag는 "무엇을 처리해야 하는가?"에 답해야 합니다.

V1 flag:

- `missing_spec`
- `missing_plan`
- `no_next`
- `no_review`
- `no_pr`
- `no_ko`
- `blocked`

표시는 한글 label로 합니다.

```text
spec 없음
plan 없음
다음 없음
review 없음
PR 없음
한글 없음
막힘
```

## Row 동작

V1:

- row 또는 row link 클릭 -> `memory/issue-<id>.html` 열기.
- 기존 생성 issue panel을 그대로 사용합니다.

V2:

- 오른쪽 상세 peek panel 추가.
- 리스트 위치를 유지한 채 artifact preview.
- 기존 049 sidecar 동작으로 `English / 한글` 토글 사용.

## 빈 상태와 fallback

- 이슈 없음: "No issues found."
- 검색 결과 없음: "검색 결과 없음".
- 상태 없음: `unknown`과 `상태 없음` flag.
- 다음 명령 없음: 빈 `Next` 셀과 `다음 없음` flag.
- 생성된 issue panel 없음: row는 유지하고, `product:dashboard` 생성 후 열릴 예상 경로로 링크합니다.

## 시각 톤

이 화면은 운영용 PM dashboard입니다.

- 밀도 있게, 하지만 읽기 쉽게.
- 작은 heading.
- compact control.
- 장식 카드 없음.
- hero 없음.
- badge/chip/table 중심.

## 구현 경계

zero-backend를 유지합니다.

- Python이 row를 수집합니다.
- HTML에 static JSON을 embed합니다.
- Vanilla JavaScript가 filter/sort/render를 처리합니다.
- Git Markdown이 canonical입니다.
- 대시보드에서 write-back하지 않습니다.

## Plan 단계 체크

구현 계획에는 다음이 포함되어야 합니다.

1. issue-row collector
2. artifact coverage detector
3. attention flag builder
4. 세 번째 탭 template 변경
5. static search/filter/sort JS
6. collector와 rendered control 테스트
7. release check
