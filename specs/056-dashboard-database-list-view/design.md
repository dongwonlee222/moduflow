# Design: Dashboard Database/List View Screen Composition

Issue: `056-dashboard-database-list-view`
Spec: `specs/056-dashboard-database-list-view/spec.md`
Next: `product:plan 056-dashboard-database-list-view`

## Source Patterns

- Notion: one canonical database can expose multiple views, with per-view filters, sorts, groups, property visibility, and page-open behavior.
- Jira: project tracking expects list/board/timeline/calendar-style views over the same work, with status, dependencies, and reporting visible.
- Linear: custom views are durable filtered issue/project/initiative lists or boards; saved filters and review-ready views matter.
- GitHub Projects: project items are field-backed and can be shown as table/board/roadmap-like views; fields drive filtering and grouping.

Reference links:

- https://www.notion.com/help/views-filters-and-sorts
- https://www.atlassian.com/software/jira/features
- https://linear.app/docs/custom-views
- https://docs.github.com/en/issues/planning-and-tracking-with-projects

## Design Decision

Make `이슈 DB` the daily operating view. Keep `이슈 그래프` and `지식 그래프` as relationship/knowledge views. The dashboard becomes a workbench over one local issue dataset, not a new app and not an external database.

V1 should ship:

1. `이슈 DB`
2. `이슈 그래프`
3. `지식 그래프`

V2 can add:

1. `칸반`
2. `타임라인`
3. saved filter hashes
4. right-side detail preview

## Screen Layout

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

## Top Navigation

The tab order should prioritize work scanning:

1. `이슈 DB` — default tab. Answers "what needs attention?"
2. `이슈 그래프` — relationship topology and dependency shape.
3. `지식 그래프` — memory/decision/evidence navigation.
4. `칸반` — later, grouped status movement.
5. `타임라인` — later, date-based planning when date metadata is reliable.

Deep links:

- `#issue-db`
- `#issues`
- `#memory`

## Toolbar

The toolbar should be compact and operational, not explanatory.

- Search input: id/title/next command text search.
- View chips:
  - `전체`
  - `진행중`
  - `리뷰필요`
  - `막힘`
  - `누락있음`
  - `완료`
- Group select:
  - `상태별`
  - `Goal별`
  - `없음`
- Sort select:
  - `최근 업데이트`
  - `이슈 번호`
  - `상태`
  - `메모리 수`
- Columns button:
  - v1 can be non-interactive or omitted if too much for the first cut.
  - v2 can support hide/show columns.

## Table Columns

Default visible columns:

| Column | Purpose |
| --- | --- |
| `ID` | Fast issue lookup and ordering |
| `Issue` | Human-readable title |
| `Status` | Operational state |
| `Phase` | Workflow phase inferred from artifacts |
| `Next` | The command to run next |
| `Artifacts` | Compact coverage badges |
| `Flags` | Attention signals |
| `Memory` | Linked memory count |

Optional later columns:

- `Goal`
- `Updated`
- `Relations`
- `Owner`
- `PR`
- `Review`

## Artifact Badges

Use short badges rather than long prose:

```text
I      issue file exists
S      spec.md exists
KO     spec.ko.md or Korean review sidecar exists
P      plan.md exists
T      tasks.md exists
R      review.md exists
PR     pr.md exists
Rel    release.md exists
```

Missing artifacts should be visually quiet but scannable:

```text
I S KO - - -
```

## Attention Flags

Flags should answer "what needs action?" quickly.

V1 flags:

- `missing_spec`
- `missing_plan`
- `no_next`
- `no_review`
- `no_pr`
- `no_ko`
- `blocked`

Visible labels can be Korean:

```text
spec 없음
plan 없음
다음 없음
review 없음
PR 없음
한글 없음
막힘
```

## Row Interaction

V1:

- Click row or row link -> open `memory/issue-<id>.html`.
- Preserve existing generated issue panel.

V2:

- Add right-side peek panel.
- Keep list position while previewing issue artifacts.
- Add `English / 한글` toggle inside the preview through existing 049 sidecar behavior.

## Empty And Fallback States

- No issues: show a small empty state with "No issues found."
- Search no result: show "검색 결과 없음".
- Missing status: show `unknown` and flag `상태 없음`.
- Missing next command: empty `Next` cell plus `다음 없음` flag.
- Missing generated issue panel: row remains visible; link can still point to the expected path after `product:dashboard` generation.

## Visual Tone

This is an operational PM dashboard, not a landing page.

- Dense but readable.
- Small headings.
- Compact controls.
- No decorative cards.
- No oversized hero.
- Use badges/chips/tables, not marketing-style sections.

## Implementation Boundary

This design is still zero-backend:

- Python collects rows.
- HTML embeds static JSON.
- Vanilla JavaScript filters, sorts, and renders.
- Git Markdown remains canonical.
- No write-back from the dashboard.

## Acceptance Check For Planning

The implementation plan should include:

1. issue-row collector
2. artifact coverage detector
3. attention flag builder
4. template changes for the third tab
5. static search/filter/sort JS
6. tests for collector and rendered controls
7. release check
