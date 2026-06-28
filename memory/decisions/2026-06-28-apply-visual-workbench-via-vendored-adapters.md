---
id: 2026-06-28-apply-visual-workbench-via-vendored-adapters
kind: decision
title: Apply visual workbench via vendored adapters, CDN render, and ModuFlow core
issue_id: 
spec: 
owner: Dongwon Lee
date: 2026-06-28
tags: [visual-workbench, planning-harness, adapters, graph, provenance]
references: [2026-06-26-use-git-canonical-memory-with-optional-adapters]
summary: 비주얼 워크벤치는 새로 짓지 않고 layer로 가른다 — 기획 산출물 스킬은 기존 vendored 어댑터(spec-kit/product-design/data-analytics) 재사용, 그래프 렌더는 CDN 핀(Cytoscape), 아티팩트→노드/엣지 추출·추적성·포트폴리오만 ModuFlow 코어. 인터랙티브 저작은 superpowers + 신규 백엔드로 나중(021/028 게이트).
rationale: ModuFlow는 source-adapter-policy로 다른 플러그인 위에 선 메타 플러그인이라, "기획 하네스"가 보여준 산출물 스킬셋은 이미 흡수돼 있다. 직접 재구현은 중복이며, 고유 가치는 아티팩트 관계 그래프와 채팅→아티팩트 추적성에 있다.
evidence: docs/visual-workbench-and-planning-harness.md
alternatives: 비주얼 워크벤치를 처음부터 새 앱으로 구축; 기획 하네스 스킬을 ModuFlow 코어에 재구현.
reversal_conditions: vendored 어댑터가 그래프/추적성 요구를 못 따라가 코어로 흡수해야 하는 경우.
confidence: medium
---

# Apply visual workbench via vendored adapters, CDN render, and ModuFlow core

## Summary

비주얼 워크벤치 적용 입장: 레이어로 가른다.

- **재사용(어댑터)**: 기획 산출물 스킬 → `spec-kit`/`product-design`/`data-analytics` 이미 vendored.
- **CDN 핀**: 그래프 렌더(Cytoscape) — code-dependency, 042 결정.
- **ModuFlow 코어**: 아티팩트→노드/엣지 추출, 추적성(provenance), 포트폴리오 롤업.
- **나중+백엔드**: 인터랙티브 저작/실행 → `superpowers` + 신규 백엔드, `021`/`028` 게이트.

전체 분석·근거·정보구조·열린 결정은 evidence 문서 참조: `docs/visual-workbench-and-planning-harness.md`.

이 결정은 [[2026-06-26-use-git-canonical-memory-with-optional-adapters]]의 "Git canonical + optional adapters" 어댑터 경계 원칙 위에 선다 — 같은 철학을 시각화 레이어에 적용.
