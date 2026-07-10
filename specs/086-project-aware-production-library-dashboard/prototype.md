# 프로토타입: 프로젝트 인식형 제작 라이브러리 대시보드

Issue: `086-project-aware-production-library-dashboard`
상태: 승인
승인자: Dongwon Lee, 2026-07-10

## 산출물

- 인터랙티브 프로토타입: `prototype.html`
- 한글 디자인 검토본: `design.ko.md`
- 영문 디자인 정본: `design.md`
- 제품 스펙: `spec.ko.md`

## 확인 가능한 동작

- `모두의충전`, `애드팝콘`, `전체 프로젝트` 전환.
- 모든 대시보드 탭 위에서 프로젝트 범위 유지.
- 기존 이슈 DB, 이슈 그래프, 지식 그래프 화면이 제거되지 않고 같은 위치와 스타일로 유지됨.
- 기존 ModuFlow DB 컨트롤로 제작 기록 검색과 필터링.
- 테이블 폭을 줄이지 않고 딤 모달로 제작 기록 상세 열기.
- Artifacts, Decisions, Failed Attempts, Reusable Patterns와 분리된 외부/내부 문장 확인.
- 닫기 버튼 또는 딤 영역 클릭으로 모달 닫기.
- 선택 프로젝트를 유지하면서 기존 탭과 새 탭 전환.

## 시각 검토 결정

첫 탐색안은 새 앱 shell과 오른쪽 고정 상세 패널을 사용했지만 기존 UI 변화가 커서 기각했습니다. 승인안은 기존 ModuFlow 제목, 시스템 폰트, 파란 탭, 필터, 테이블, 테두리, 정보 패널과 이슈 DB·이슈 그래프·지식 그래프를 유지하고 Issue 086에 필요한 컨트롤만 추가합니다.

## 구현 참고

- 프로토타입 데이터는 예시 fixture이며 canonical 프로젝트 데이터가 아닙니다.
- 새 스타일을 만들기 전에 기존 대시보드 CSS class를 재사용합니다.
- 구현에서는 키보드 focus 관리와 Escape 처리를 완성합니다. 프로토타입은 레이아웃과 기본 pointer 동작을 검증합니다.
- 프로젝트와 제작 기록 데이터는 Issue 085·086의 canonical collector에서 가져옵니다.
