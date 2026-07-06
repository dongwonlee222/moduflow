# Issue 032: Multi-Language Goal Benchmarking and Core MCP Server Integration

**Status: done** — body and status.md say `Phase: done` (commit db3edda, `scripts/mcp_server.py` live). Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

ModuFlow 플러그인의 완성도를 넥스트 레벨로 올리기 위해 다음 두 가지 핵심 개선 사항을 구현합니다.
1. **다국어 벤치마킹 로컬라이제이션**: `issue_generator.py`에 웹 검색 결과를 바탕으로 한 기획 문서 생성 시, 영문 자료 요약 분석 및 한국어 가이드라인 자동 매핑 기능을 고도화합니다.
2. **MCP (Model Context Protocol) 서버 완벽 통합**: `.mcp.json`과 연동되어 호스트 에이전트(Claude Desktop, Antigravity 등)가 쉘 명령어가 아닌 도구 호출(Tool Call)만으로 ModuFlow의 이슈/스펙 기획 흐름을 제어할 수 있도록 MCP 스펙 및 파이썬 mcp 서버 인터페이스를 구축합니다.

## Source

- Type: product improvement / Plugin Core
- Link: conversation, 2026-06-20
- Date: 2026-06-20

## Lifecycle

- Phase: done
- Created: 2026-06-20
- Started: 2026-06-20
- Target End: 2026-06-20
- Completed: 2026-06-20
- Last Updated: 2026-06-20

## Opportunity

사용자가 한글로 Goal을 입력하면 다국어 검색 결과를 분석하여 한국어 기획 문서를 매끄럽게 번역 및 요약 생성할 수 있어야 하며, 쉘 명령어 호출 방식보다 MCP Tool Call을 사용하게 함으로써 승인 팝업(Command Approval) 피로도를 획기적으로 낮추고 IDE에 원활하게 밀착 연동할 수 있습니다.

## Scope

### In

- `issue_generator.py` 내 검색 결과 다국어(영-한) 통합 번역 및 기획 요약 템플릿 강화
- Python 기반의 경량 MCP 서버 구축 및 외부 툴 노출 규격 정의 (`product_start`, `product_status`, `generate_issues_from_goal` 등)
- `.mcp.json` 연동 설정 구성
- MCP 동작 여부 및 다국어 요약 기능 테스트 구현

### Out

- 외부 상용 클라우드 번역 API 유료 연동 (로컬 LLM 혹은 호스트 번역 자원을 유연하게 타도록 설계)

## Acceptance Criteria

- 한글 Goal 입력 시 영어 모범 사례를 포함한 벤치마킹 후 매끄러운 한국어 이슈 파일들을 안정적으로 생성함
- MCP 도구 목록 확인(Tools List) 및 도구 실행(Tool Call) 인터페이스가 작동함
- `project_doctor.py` 및 `validate_moduflow.py` 검증의 무조건적인 Green(Exit Code 0) 유지
- 회귀 방지를 위해 전체 100여 개 테스트 스위트 통과

## Workflow Tasks

- [x] spec -> specs/032-multi-language-goal-benchmarking-and-core-mcp-server-integration/spec.md
- [x] plan -> specs/032-multi-language-goal-benchmarking-and-core-mcp-server-integration/plan.md
- [x] execute -> PR / commits
- [/] review -> review notes
- [x] 다국어 번역 기획 템플릿 통합
- [x] MCP 서버 스크립트 작성 및 도구 스펙 연동
- [x] 단위 테스트 작성 및 전체 파이프라인 검증

## Links

- Spec: `specs/032-multi-language-goal-benchmarking-and-core-mcp-server-integration/spec.md`
- Status: `specs/032-multi-language-goal-benchmarking-and-core-mcp-server-integration/status.md`

## Next Command

`product:spec 032-multi-language-goal-benchmarking-and-core-mcp-server-integration`
