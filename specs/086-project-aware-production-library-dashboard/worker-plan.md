# Worker Plan: 086-project-aware-production-library-dashboard

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `implementation-worker` | `group-1` | done | scripts/project_memory.py | - | Implementation: 제작 기록·플레이북 수집기와 세 상태 판정 |
| T02 | `qa-reviewer` | `group-2` | done | tests/test_dashboard_production_views.py | T01 | QA: 수집기와 판정 테스트 |
| T03 | `qa-reviewer` | `group-2` | ready | tests/test_project_memory.py | - | QA: 기존 세 탭의 생성 결과 동등성 고정 |
| T04 | `release-manager` | `group-3` | ready | commands/product-dashboard.md | - | Docs: 대시보드 명령에 두 탭과 읽기 전용 경계 기술 |
| T05 | `implementation-worker` | `group-1` | ready | scripts/project_memory.py | T01 | Implementation: 제작 기록 탭 렌더링 |
| T06 | `implementation-worker` | `group-1` | ready | scripts/project_memory.py | T05 | Implementation: 플레이북 탭 렌더링 |
| T07 | `implementation-worker` | `group-1` | ready | scripts/project_memory.py | T06 | Implementation: 제작 기록·플레이북 상세 모달 |
| T08 | `qa-reviewer` | `group-2` | ready | tests/test_dashboard_production_views.py | T07 | QA: 두 탭 렌더링과 빈 상태 테스트 |
| T09 | `implementation-worker` | `sequential` | ready | scripts/project_memory.py | T03, T07 | Implementation: 전역 프로젝트 선택기와 URL 복원 |
| T10 | `release-manager` | `sequential` | ready | scripts/release_check.py, scripts/validate_moduflow.py | T08 | Release: 신규 스위트와 자산 등록 |

## Isolation

- T01: `codex/086-project-aware-production-library-dashboard-t01`
- T02: `codex/086-project-aware-production-library-dashboard-t02`
- T03: `codex/086-project-aware-production-library-dashboard-t03`
- T04: `codex/086-project-aware-production-library-dashboard-t04`
- T05: `codex/086-project-aware-production-library-dashboard-t05`
- T06: `codex/086-project-aware-production-library-dashboard-t06`
- T07: `codex/086-project-aware-production-library-dashboard-t07`
- T08: `codex/086-project-aware-production-library-dashboard-t08`
- T09: `codex/086-project-aware-production-library-dashboard-t09`
- T10: `codex/086-project-aware-production-library-dashboard-t10`

## Merge Order

- T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09 → T10

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 9 touches shared state: Implementation: 전역 프로젝트 선택기와 URL 복원
- Task 10 touches shared state: Release: 신규 스위트와 자산 등록
- scripts/project_memory.py is expected by T01 and T05
- scripts/project_memory.py is expected by T01 and T06
- scripts/project_memory.py is expected by T01 and T07
- tests/test_dashboard_production_views.py is expected by T02 and T08
- scripts/project_memory.py is expected by T01 and T09

## Next Command

`product:execute 086-project-aware-production-library-dashboard`
