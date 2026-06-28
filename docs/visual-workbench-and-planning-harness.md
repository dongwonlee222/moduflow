# 비주얼 워크벤치 + 기획 하네스 분석 — ModuFlow 적용

> 목적: 외부 "기획 하네스" 패턴을 분석하고, 동원님이 구상한 비주얼 워크벤치를 ModuFlow의 플러그인 기반(source-adapter-policy) 위에 어떻게 적용할지 정리.
> 조사일: 2026-06-28. 출처: https://news.hada.io/topic?id=30870 · 원문 https://maily.so/makersnote/posts/1gz2e564z3q

## 1. 기획 하네스(Planning Harness) 분석

**정의**: AI가 일관된 규칙·컨텍스트 하에서 기획서를 쓰도록 통제하는 시스템. 로컬 `CLAUDE.md`로 규칙을 강제.

**4요소**: 컨텍스트(정책 고정) · 도구 정의(전용 스킬) · 가드레일(위험 시 사람 승인) · 자동 검증(산출물 검수).

**워크플로**: `spec.md` 입력 → 폴더 `CLAUDE.md` 자동 로드 → 단일 명령 → 순차 자동화(시퀀스 다이어그램 → 유저 플로우 → HTML 대시보드) → 로컬 파일 직접 저장 → GitHub 팀 공유.

**스킬 예시**: `/search-documents` `/sequence_diagram` `/user-flow` `/logic-check` `/split-requirements` `/release-note` `/deploy-jira`.

원문 저자 예측: "Claude Design / Figma MCP가 하네스에 붙으면 비주얼 작업도 자동화될 것" — 이것이 비주얼 워크벤치 방향과 정확히 일치.

### ModuFlow와 비교 — 같은 계열, ModuFlow가 상위 집합

| 요소 | 기획 하네스 | ModuFlow |
|---|---|---|
| 규칙 강제 | CLAUDE.md | CLAUDE.md + 도메인 규칙 |
| 전용 스킬 | /sequence_diagram 등 | `product:*` 35개 |
| 가드레일 | 위험 시 승인 | doctor + delegation gate |
| 자동 검증 | 산출물 검수 | `release_check`/`validate_*` |
| Git 공유 | GitHub 배포 | Git-native 핵심 |
| HTML 대시보드 | index.html | `dashboard.html` (042) |
| 범위 | 기획서 1건 | goal→issue→spec→plan→execute→memory 전체 |
| 관계 그래프 | 없음 | 메모리 그래프 (042) |
| 포트폴리오 | 없음 | 있음 (036) |

기획 하네스의 스킬셋(시퀀스/플로우/로직체크/디자인)은 ModuFlow에 이미 **vendored 어댑터로 존재**한다(spec-kit, product-design). 새로 만들 게 아니라 이미 흡수돼 있음.

## 2. 비주얼 워크벤치 아이데이션 (동원님 요구사항 정리)

| 요구 | 워크벤치 요소 |
|---|---|
| 채팅으로 정한 내용 확인 | 추적성(provenance) — 채팅 결정 → 아티팩트 캡처 → 그래프 역추적 |
| 이슈 리스트 + 히스토리 | 이슈 그래프 + 타임라인 (상태색·관계·이력) |
| goal/이슈 상세: 계획·실행 | 드릴다운 뷰 (spec→plan→execute) |
| 프로젝트별 | 포트폴리오 계층 |
| 산출물 → 메모리 그래프 | 메모리 그래프 (042) |

### 정보 계층 (4단계 드릴다운)

```
L0 포트폴리오   프로젝트 카드 (상태·다음 액션)        ← 036 연계
L1 프로젝트     goal + 이슈 그래프 + 메모리 그래프     ← 3개 뷰
L2 이슈         spec·plan·execute·히스토리 + 관계엣지
L3 메모리/산출물 의사결정 그래프 (왜·근거·산출물)       ← 042
```

### 핵심 신규 개념: 추적성(provenance)

가장 ModuFlow다운 아이디어. 메모리엔 이미 `source_event` 필드가 있으니, 채팅 결정이 이슈/메모리로 캡처될 때 출처를 기록하고 그래프에서 역추적한다. 채팅(휘발) → 아티팩트(영속) → 그래프(가시화)의 추적 사슬.

## 3. ModuFlow 적용 매핑 (source-adapter-policy 기준)

ModuFlow는 직접 만들지 않고 어댑터로 흡수하는 게 원칙. 비주얼 워크벤치를 그 기준으로 가르면:

| 구분 | 무엇 | 어떻게 |
|---|---|---|
| **기존 어댑터 재사용 (안 만듦)** | 기획 산출물 스킬 | sequence/flow/logic → `spec-kit`, design brief/prototype/image-to-code → `product-design`, metric 대시보드 → `data-analytics`. 하네스 스킬셋은 이미 vendored |
| **CDN 핀 (code-dependency, 어댑터 대상 아님)** | 그래프 렌더 라이브러리 | Cytoscape CDN 핀 — 042 결정 그대로 |
| **ModuFlow 코어 (고유, 아무도 vendoring 안 함)** | 아티팩트→노드/엣지 추출, provenance, 포트폴리오 롤업 | `project_memory.py` 패턴 확장 |
| **나중 + 백엔드** | 인터랙티브 저작/실행 | `superpowers` 실행 어댑터 + 신규 백엔드. `021`/`028`에 게이트 |

하네스의 "단일 명령 → 순차 산출물 연쇄" UX는 ModuFlow의 loop + spec-kit 체인으로 이미 가능하다 — 새 의존성이 아니라 UX 다듬기. (백로그: 산출물 연쇄 UX 개선)

## 4. 열린 결정 (여기서 해결하지 않음)

- **인터랙티브 프론트엔드**: (A) 채팅 백엔드 비주얼 vs (B) 독립 앱. 추천: (A)로 검증 후 (B). → goal `visual-workbench` Open Question.
- **이슈 관계 소스**: "Related Issues" 텍스트 파싱 vs 이슈에 frontmatter 부여(아티팩트 모델 스키마 변경). → `045` spec에서 결정.

## 결론

비주얼 워크벤치 = (vendored 산출물 스킬) + (CDN 렌더) + (ModuFlow 코어: 그래프·추적성·포트폴리오). 새 이슈는 필요 없다 — 이 분석은 `visual-workbench` goal과 `044`/`045`를 확인하고, 대부분이 이미 vendored임을 식별한다. ModuFlow는 기획 하네스의 상위 집합이며, 비주얼 워크벤치는 그 위에 그래프·추적성 레이어를 얹는 일이다.

## 부록: 산출물 영속화 점검 (2026-06-28)

용도: 추후 문제 발생 시 사람이 산출물을 파일로 확인할 수 있어야 한다. 실증 점검 결과:

| 산출물 | 파일 영속화 | 비고 |
|---|---|---|
| spec / plan / tasks / status | ✅ | `specs/NNN/`에 실제 파일 |
| business (brief·calc·validation·decision) | ✅ | `business/`에 |
| memory (decision·evidence·deliverable) | ✅ | `memory/`에 |
| design-brief / prototype | ⚙️ 정의됨, 미실행 | `adapters/product-design.yaml`의 `writes`에 `specs/*/design-brief.md`·`specs/*/prototype.md` 정의 — 단 현재 `specs/`에 실제 생성물 없음 |
| 시퀀스 다이어그램 / 유저 플로우 | ❌ 갭 | 전용 파일 0개, spec 임베드 1/40. 어댑터 `writes`에도 없음. 생성 스킬(`flow-design`/`diagram-gen`)은 사용자 글로벌 스킬이라 ModuFlow 배포에 없음 |

결론: 텍스트 산출물은 사람 확인 가능. 시각 산출물(다이어그램/플로우)이 유일한 실질 갭.

최소 고침(원할 때만): spec/plan 단계에서 mermaid를 `spec.md`에 임베드 표준화 → GitHub/Obsidian이 정본 아티팩트 안에서 렌더 → 사람이 canonical 파일을 열면 다이어그램을 본다. 042 인사이트 재사용, 새 파일/기계 불필요. (백로그)
