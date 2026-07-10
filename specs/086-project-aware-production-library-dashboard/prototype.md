# 프로토타입: 프로젝트 인식형 제작 라이브러리 대시보드

Issue: `086-project-aware-production-library-dashboard`
상태: 승인
승인자: Dongwon Lee, 2026-07-10

## 산출물

- 인터랙티브 프로토타입: `prototype.html`
- 한글 디자인 검토본: `design.ko.md`
- 영문 디자인 정본: `design.md`
- 제품 스펙: `spec.ko.md`
- 베이스라인: 실제 생성된 `memory/dashboard.html`의 이슈 DB와 Cytoscape 그래프

## 확인 가능한 동작

- 현재 등록 프로젝트 `ModuFlow`를 실제 설정값으로 표시.
- 등록 프로젝트가 하나일 때 선택기를 비활성화하고, 둘 이상일 때만 전환 가능하게 하는 계약.
- 기존 이슈 DB, 이슈 그래프, 지식 그래프 화면이 제거되지 않고 같은 위치와 스타일로 유지됨.
- 실제 전체 이슈 DB 행, Cytoscape 이슈 그래프 87 nodes/198 edges, 지식 그래프 14 nodes/4 edges 유지 확인.
- 현재 활성 이슈 `086-project-aware-production-library-dashboard`에 `.current` 강조, 중앙 이동, 기존 zoom 1.15 적용 확인.
- 기존 이슈 DB의 검색, filter chip, 정렬, grouping과 상세 이동 유지.
- 기존 그래프의 관계선·지식 배지 토글, node interaction, hash deep link 유지.
- 제작 기록과 플레이북 탭이 기존 화면을 대체하지 않고 추가됨.
- 현재 ModuFlow 프로젝트에 데이터가 없을 때 정직한 빈 상태 표시.

## 시각 검토 결정

첫 탐색안은 새 앱 shell과 오른쪽 고정 상세 패널을 사용했고, 다음 수정안은 기존 이슈 DB와 그래프를 샘플로 다시 그렸습니다. 두 방식 모두 기존 동작 보존을 증명하지 못해 기각했습니다. 최종 프로토타입은 실제 생성된 ModuFlow 대시보드를 그대로 베이스로 사용하고 Issue 086에 필요한 컨트롤만 추가합니다.

ModuFlow 저장소에는 아직 실제 제작 기록과 승인 플레이북이 없으므로 새 탭은 샘플 브랜드 데이터를 섞지 않고 빈 상태를 표시합니다.

## 구현 참고

- 프로토타입의 이슈·지식 데이터는 실제 ModuFlow 생성 대시보드에서 가져왔습니다.
- 새 스타일을 만들기 전에 기존 대시보드 CSS class를 재사용합니다.
- 제작 기록 데이터가 있는 등록 프로젝트의 검색·필터·딤 모달은 구현 단계에서 Issue 085 fixture와 실제 등록 프로젝트로 검증합니다.
- 구현에서는 키보드 focus 관리와 Escape 처리를 완성합니다.
- 프로젝트와 제작 기록 데이터는 Issue 085·086의 canonical collector에서 가져옵니다.
