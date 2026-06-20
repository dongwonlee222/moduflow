# Spec: Goal-driven Autonomous Benchmarking and Issue Generation

Issue: 031-goal-driven-autonomous-benchmarking-and-issue-generation

## Problem

ModuFlow는 이미 작성된 Issue와 Spec을 실행하는 데 뛰어난 자동화 루프를 가집니다. 그러나 새로운 아이디어나 "Goal"이 제시되었을 때, 이를 어떤 구체적인 개발 태스크(Issue)로 쪼개고, 각 이슈에 어떤 기술적 마일스톤이나 벤치마킹 분석을 포함해야 할지는 인간 PM(혹은 엔지니어)의 수작업 기획에 의존하고 있습니다.

## Solution

사용자의 상위 수준 "Goal"을 분석하고 외부 우수 사례(웹 검색 기반)를 자율적으로 벤치마킹하여, ModuFlow 스키마 및 템플릿에 완전히 부합하는 다수의 구체적 하위 Issue 파일(`issues/0xx-*.md`)을 자동 생성하는 기획 보조 모듈(`issue_generator.py`)을 설계 및 구현합니다.

## Key Design & Architecture

### 1. Goal 분석 및 웹 검색 연동 (Benchmarking)
- 사용자가 설정한 Goal(예: `"OAuth2 인증 도입 및 세션 관리 구현"`)을 획득합니다.
- `search_web` 도구를 사용하여 Goal에 매핑되는 최근 모범 구현 패턴, 오픈소스 트렌드, 보안 고려 사항 등을 벤치마킹합니다.

### 2. 세부 개발 Task 분할 로직 (Decomposition)
- 벤치마킹한 분석 데이터를 기반으로 대형 Goal을 `3~5개 내외`의 독립적이고 논리적인 Issue들로 조각냅니다.
- 예: OAuth2 Goal
  - Issue A: OAuth2 스키마 및 DB 설계
  - Issue B: 인증 미들웨어 및 세션 토큰 검증 구현
  - Issue C: 카카오/구글 소셜 로그인 프론트엔드 연동

### 3. ModuFlow 표준 템플릿 파일 생성 (Issue Generator)
- 생성되는 이슈 파일명은 `issues/0xx-[issue-slug].md` 형식을 준수합니다.
- `issues/` 폴더 내 가장 높은 번호 다음 순번을 자동으로 찾아 부여합니다.
- 이슈 파일 내부에 `Summary`, `Opportunity`, `Scope (In/Out)`, `Acceptance Criteria`, `Workflow Tasks`가 완벽하게 구성되어야 합니다.

## Acceptance Criteria

- Goal에 대해 자율 벤치마킹 후 신규 이슈 마크다운을 올바르게 제안 및 자동 빌드하는 모듈 구현
- **[이슈 완료 자동화 강제]** 생성된 마크다운 파일들의 스키마 포맷 유효성 통과 및 `project_doctor.py` & `validate_moduflow.py` 검증의 무조건적인 Green(Exit Code 0) 유지
- **[회귀 방지]** 기존 ModuFlow 테스트 스위트 전체(80+ tests)가 손상 없이 통과되며 신규 테스트 스위트 추가 완료
- 웹 검색 및 이슈 생성을 통합 검증하는 단위 테스트 완료

## Next Command

`/product:plan 031-goal-driven-autonomous-benchmarking-and-issue-generation`
