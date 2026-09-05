# Tasks: Project-Aware Production Library Dashboard

Issue: `086-project-aware-production-library-dashboard` · Owner: Dongwon Lee
Source: [plan](plan.md). Each task declares the files it expects to own so
`scripts/worker_orchestrator.py` can decide parallel eligibility instead of a
human guessing it. Collectors and the coverage judgment landed on 2026-09-04.

- [x] Implementation: 제작 기록·플레이북 수집기와 세 상태 판정 [files: scripts/project_memory.py]
- [x] QA: 수집기와 판정 테스트 [files: tests/test_dashboard_production_views.py] [depends: T01]
- [x] QA: 기존 세 탭의 생성 결과 동등성 고정 [files: tests/test_project_memory.py]
- [x] Docs: 대시보드 명령에 두 탭과 읽기 전용 경계 기술 [files: commands/product-dashboard.md]
- [x] Implementation: 제작 기록 탭 렌더링 [files: scripts/project_memory.py] [depends: T01]
- [x] Implementation: 플레이북 탭 렌더링 [files: scripts/project_memory.py] [depends: T05]
- [x] Implementation: 제작 기록·플레이북 상세 모달 [files: scripts/project_memory.py] [depends: T06]
- [x] QA: 두 탭 렌더링과 빈 상태 테스트 [files: tests/test_dashboard_production_views.py] [depends: T07]
- [ ] Implementation: 선택기 껍데기와 URL 복원, 한 payload 규율 [files: scripts/project_memory.py] [depends: T03, T07] [shared_state: true]
- [ ] [deferred → 118-portfolio-mode-dashboard] Implementation: 포트폴리오 수집과 전체 프로젝트 요약 [files: scripts/project_memory.py, scripts/project_portfolio.py] [depends: T09] [shared_state: true]

> T10 is deferred, not cancelled — 2026-09-05, approved by Dongwon Lee. Portfolio-mode collection and the `전체 프로젝트` summary move to Issue `118-portfolio-mode-dashboard`. The line is kept in place under C5 so T11's numbering and every `[depends:]` reference stay valid. T09 keeps the selector, the one-payload discipline and `?project=<id>` restoration for a single project; its `all` state moves to 118. See `spec.md` "Amendment — 2026-09-05".
- [ ] Release: 신규 스위트와 자산 등록 [files: scripts/release_check.py, scripts/validate_moduflow.py] [depends: T08] [shared_state: true]
