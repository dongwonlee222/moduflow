# 노드 기반 비주얼 프로그래밍 — ModuFlow 대시보드 시각화 리서치

> 목적: 채팅-only 시각화의 직관성 한계를 보완할 대시보드 설계 시 참고할 외부 사례.
> 조사일: 2026-06-27. star 수는 조사 시점 GitHub 기준.

## 핵심 결정 (이 리서치의 spine)

시각화 외부 활용은 **두 종류로 갈리며 메커니즘이 다르다**:

- **skill-vendorable** (Mermaid, 시각화 MCP/스킬) → ModuFlow `source-adapter-policy`(vendor/overlays/adapters)로 정식 vendoring 가능.
- **code-dependency** (React Flow, Rete, Rivet 등 JS 라이브러리) → 스킬이 아니라 npm 코드 의존. `source-adapter-policy` 대상이 **아님**. 별도 대시보드 앱의 의존성으로 분리해 다뤄야 함.

→ **ModuFlow 경로 = Mermaid-first.** Git-native·경량·0-코드 렌더 정신에 가장 부합.

## 렌더링 라이브러리 (대시보드를 코드로 만들 때)

| 라이브러리 | ★ | 유지보수 | 스택 | 비고 |
| :--- | --: | :--- | :--- | :--- |
| React Flow (xyflow/xyflow) | 37.3k | 🟢 | TS/MIT | 1순위. 미니맵·줌·커스텀노드·자동레이아웃 |
| Rete.js | 12.1k | 🟢 | TS/MIT | 실행형 노드엔진 성격 강함 |
| litegraph.js | 8.1k | 🔴 ('24) | JS/MIT | ComfyUI 기반, 유지보수 정체 |
| Drawflow | 6.0k | 🔴 ('24) | JS/MIT | 경량이나 정체 |

## AI 노드 기반 앱 (아키텍처·UX 영감)

| 앱 | ★ | ModuFlow 적용 포인트 |
| :--- | --: | :--- |
| n8n | 194k | 트리거→액션 멘탈모델 = loop 단계 매핑. 이미 MCP로 친숙 |
| Langflow | 150k | 좌측 팔레트 + 노드 인스펙터 UX |
| Dify | 147k | 워크플로우 빌더 + observability |
| ComfyUI | 118k | 로컬-first 캔버스 철학 |
| Flowise | 54k | 드래그 노드 그래프 단순성 |
| **LangGraph** | 36k | 🎯 **개념적 쌍둥이** — 노드(단계)+엣지(조건부 제어흐름)+HITL 체크포인트+영속 상태 = ModuFlow loop+delegation gate+loop-state.json |
| Sim | 29k | 2026-native 깔끔한 오케스트레이션 UX |
| node-RED | 23k | 노드 status 점(상태 표시) 패턴 |
| Coze Studio | 21k | ByteDance, 루프/커스텀 실행 노드 |
| Rivet | 4.6k | Ironclad(계약테크 기업) 제작. 실행 추적·디버깅 시각화 IDE |

## ModuFlow 대시보드 — 두 갈래 시각화

| | A. 지식 그래프 | B. 실행 그래프 |
| :--- | :--- | :--- |
| 노드 | 이슈·스펙·의사결정 아티팩트 | loop phase 단계 |
| 엣지 | supersedes·depends_on·defines | 조건부 제어 흐름 |
| 색/상태 | 아티팩트 종류 | gate_state(pending/passed) |
| 레퍼런스 | React Flow + elkjs 자동배치 | LangGraph Studio + Rivet |
| 현재 출발점 | 037 Mermaid 그래프 인덱싱 | loop-state.json |

## 단계적 경로

```text
1. Mermaid (지금, 0-코드)      ← GitHub/Obsidian 네이티브 렌더. 직관성 즉시 개선
2. 시각화 MCP/스킬 어댑터       ← source-adapter-policy로 정식 vendoring (채팅 인라인)
3. React Flow 대시보드 (웹앱)   ← npm 의존. 직관성 부족이 실제 병목으로 입증될 때만
```

## 설계 메모

- 노드 **수동 배치 금지** → `elkjs`/`dagre` 자동 레이아웃 (아티팩트는 계속 증가)
- 엣지 스타일 = 관계 종류(supersedes 실선 / depends_on 점선) — 037 Mermaid 규칙 승계
- node-RED식 상태 점으로 gate 상태 표시

## 출처

- https://github.com/xyflow/awesome-node-based-uis
- https://github.com/xyflow/xyflow · https://github.com/retejs/rete
- https://github.com/langchain-ai/langgraph · https://github.com/langgenius/dify
- https://github.com/Ironclad/rivet · https://github.com/simstudioai/sim · https://github.com/coze-dev/coze-studio
