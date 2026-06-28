---
id: 2026-06-28-visualization-library-benchmark
kind: evidence
title: 무료 시각화 라이브러리 벤치마킹 (이슈 045/047)
date: 2026-06-28
tags: [benchmark, visualization, cytoscape, chartjs, mermaid, cdn, issue-045, issue-047]
summary: ModuFlow 시각화 뷰(045 이슈 그래프, 047 드릴다운 패널)에 쓸 무료 라이브러리를 zero-backend/CDN/vanilla 제약으로 비교. 결론은 용도별 분담 — 그래프=Cytoscape 유지, 차트=Chart.js, 다이어그램=Mermaid, 드릴다운=라이브러리 불필요.
owner: Dongwon Lee
confidence: high
source_event: benchmarking_session
issue_id: 047-issue-artifact-drilldown
source_artifacts:
  - "memory/evidence/2026-06-28-visualization-library-benchmark.md"
references:
  - "https://cdnjs.com/libraries/Chart.js/"
  - "https://mermaid.js.org/intro/getting-started.html"
  - "https://github.com/visjs/vis-network"
  - "https://github.com/leeoniya/uPlot"
reversal_conditions: ModuFlow가 zero-backend 제약을 버리고 빌드 스텝/번들러를 도입하거나, 이슈 규모가 수천 노드로 커져 WebGL 렌더가 필요해지는 경우.
---

# 무료 시각화 라이브러리 벤치마킹 (이슈 045/047)

> 조사 일자: 2026-06-28. 크기는 cdnjs/jsdelivr 실측(raw minified, gzip 아님).

전제(코드 확인): 042는 Cytoscape.js 3.30.2를 cdnjs로 버전 핀, Python이 node/edge JSON emit → 단일 self-contained HTML. 모든 후보는 이 패턴(zero-backend, CDN 핀, vanilla)을 지켜야 한다.

## 용도별 비교

| 도구 | 용도 | 라이선스 | 크기 | 적합성 | 비고 |
|---|---|---|---|---|---|
| **Cytoscape.js 3.30.2** | A 그래프 | MIT | 365 KB | 상 | 042 채택. 44개 이슈엔 충분 |
| vis-network 10.0.2 | A 그래프 | Apache/MIT | 629 KB | 중 | Cytoscape 1.7배, 전환 이유 없음 |
| Sigma.js / D3-force | A 그래프 | MIT/ISC | 가변 | 하 | WebGL·직접구현, 과잉 |
| **Chart.js 4.5.0** | B 차트 | MIT | 203 KB | 상 | 042와 동일 `<script src>` 패턴 |
| ECharts 6 | B 차트 | Apache | 1092 KB | 하 | 무겁고 tree-shake은 빌드 필요 |
| ApexCharts 5 | B 차트 | MIT | 567 KB | 중 | Chart.js 2.8배 |
| uPlot 1.6 | B 차트(시계열) | MIT | 50 KB | 중 | 초경량이나 표준 차트 빈약 |
| **Mermaid 11** | C 다이어그램 | MIT | 29 KB(엔트리) | 상 | ⚠️ ESM 로딩(042와 방식 다름). GitHub/Obsidian 네이티브 렌더 |
| (없음) | D 드릴다운 | — | 0 KB | 상 | Python markdown→HTML 사전 렌더로 충분 |

## 용도별 추천

- **A 그래프 → Cytoscape 유지** (전환 안 함). 045는 042 제너레이터 복제.
- **B 차트 → Chart.js** (cdnjs MIT, 203 KB). `product:analyze`/metrics 산출물 렌더 — 상태 도넛, 번다운 선그래프, RICE 막대.
- **C 다이어그램 → Mermaid 11**. 핵심 강점은 CDN이 아니라 GitHub/Obsidian이 라이브러리 비용 0으로 네이티브 렌더한다는 점. HTML 대시보드 클라이언트 렌더가 필요할 때만 v11 ESM(`<script type="module">`) 핀 — 042의 classic `<script src>`와 로딩 방식이 다름을 spec에 명시.
- **D 드릴다운(047) → 라이브러리 불필요**. 제너레이터가 Python이라 markdown→HTML 사전 변환으로 충분. 메트릭 차트가 섞일 때만 Chart.js 하이브리드.

## 046 리서치와의 접점

다이어그램은 양쪽 리서치의 공통 답 = **Mermaid**. 046에선 "산출물로 작성", B에선 "GitHub가 렌더". 047 패널에 Mermaid 코드펜스만 들어가면 GitHub/Obsidian이 자동으로 그린다.

## 확인된 사실 vs 추론

- 확인: 라이선스·CDN·크기 전부 실측/공식 문서 검증. 042 Cytoscape 핀은 코드 직접 확인.
- 추론: Chart.js 단일로 당분간 충분, Sigma/D3 크기 어림치.
