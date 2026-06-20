# Spec: Multi-Language Goal Benchmarking and Core MCP Server Integration

Issue: 032-multi-language-goal-benchmarking-and-core-mcp-server-integration

## Problem

현재 ModuFlow의 `issue_generator.py`는 유용한 벤치마킹 분석을 제공하지만, 한국어로 상상(Goal)을 입력했을 때 영문 자료를 풍부하게 벤치마킹하는 것과 이를 다시 일관성 있는 한국어 명세로 번역/로컬라이제이션하는 로직이 완성되지 않았습니다. 또한 CLI 실행 방식은 IDE 플러그인(호스트 에이전트)에 탑재할 때 Command 승인 절차를 반복하게 하여 UX 마찰을 일으킵니다.

## Solution

1. **다국어 벤치마킹 로컬라이제이션**: 영문 기획 분석 결과를 받아 자동으로 직관적이고 표준적인 한국어 마크다운 이슈로 매핑/요약 번역해 주는 로컬라이저 인터페이스를 작성합니다.
2. **MCP 서버 구현**: `scripts/mcp_server.py`를 신규 작성하여, 호스트 에이전트(Claude Desktop 등)가 쉘 커맨드가 아닌 Model Context Protocol 도구 호출(`moduflow_status`, `moduflow_generate_issues`)만으로 이 모든 워크플로우를 통제할 수 있도록 지원합니다.

## Next Command

`/product:plan 032-multi-language-goal-benchmarking-and-core-mcp-server-integration`
