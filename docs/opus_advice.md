# 🛠️ 모두플로(ModuFlow) 고도화 가이드북 (for Claude Opus)

본 문서는 Neo4j의 **컨텍스트 그래프(Context Graph)** 및 Anthropic의 **AI 협업 프레임워크(AI Fluency Framework)** 모델을 모두플로(ModuFlow)에 도입하기 위한 아키텍처 가이드라인과 프롬프트 템플릿을 제공합니다.

---

## 1. 아키텍처 비전 (Vision)

모두플로의 기존 마크다운 기반 플랫 파일 저장 모델을 **Git-native 컨텍스트 그래프** 구조로 전환합니다. 각 문서 파일(이슈, 스펙, 계획, 의사결정, 메모리)은 그래프의 **노드(Node)**가 되며, 파일 상단(YAML Frontmatter)의 메타데이터를 통해 명시적인 **관계(Edge)**를 정의합니다.

또한, 인간과 AI의 효과적인 협업을 위해 Anthropic의 4대 원칙인 **위임(Delegation), 기술(Description), 통찰(Discernment), 성실(Diligence)** 단계를 검토 게이트(Gates)로 통합합니다.

```mermaid
graph TD
    subgraph 컨텍스트 그래프 (관계 구조)
        Issue[이슈 노드] -->|정의| Spec[스펙 노드]
        Spec -->|작성| Plan[계획 노드]
        Plan -->|실행| Commit[Git 커밋 / 코드]
        Commit -->|생성| Decision[의사결정 ADR]
        Decision -->|아카이브| LongMemory[장기 메모리]
        
        LongMemory -->|대체| StaleMemory[이전 메모리]
    end

    subgraph AI 협업 (Fluency) 게이트
        D1[위임 레벨 설정] --> D2[지시 맥락 조합]
        D2 --> D3[비판적 검토 리포트]
        D3 --> D4[성실성 정책 체크]
    end
    
    ContextGraph -.->|이전 이력 주입| D2
```

---

## 2. Neo4j 스타일의 에이전트 메모리 (컨텍스트 그래프)

### A. 메모리 파일 스키마 규격화
`memory/` 아래에 저장되는 모든 마크다운 파일 상단에 표준화된 YAML Frontmatter 관계 정보를 정의합니다.

#### 템플릿 예시: `memory/decisions/2026-06-27-caching-policy.md`
```markdown
---
id: decision-use-local-sqlite-cache
title: 빠른 그래프 인덱싱을 위한 로컬 SQLite 사용 의사결정
created: 2026-06-27
kind: decision
tags: [architecture, performance, caching]
references: 
  - "[issue-034](file:///workspace/issues/034-memory-capture-and-sync-workflow.md)"
  - "[spec-034](file:///workspace/specs/034-memory-capture-and-sync-workflow/spec.md)"
relations:
  supersedes: "decision-use-json-caching" # 이전 의사결정 대체
  depends_on: "decision-git-canonical-memory" # 의존하는 의사결정
---
```

### B. 그래프 시각화 및 검색 엔진 구현
CLI 커맨드 `/product:memory --graph` 또는 `scripts/project_memory.py` 스크립트를 업데이트하여 문서 간의 관계를 파싱하고 Mermaid 다이어그램으로 그려주는 파이썬 로직을 설계합니다.

---

## 3. Anthropic AI 협업 4대 원칙 통합 설계

모두플로의 워크플로우 루프와 태스크 관리 시스템에 4대 원칙을 다음과 같이 매핑합니다.

| 원칙 (Principle) | 모두플로 통합 영역 | 세부 구현 사항 |
| :--- | :--- | :--- |
| **위임 (Delegation)** | `workspace/loop-state.json` | 각 작업 단계에 `delegation_level: full (완전 위임) \| review_required (리뷰 필수) \| manual (수동)`을 부여해 인간-AI 통제 권한 관리. |
| **기술 (Description)** | `scripts/worker_orchestrator.py` | 워커 에이전트 구동 시, 작업 관련 파일 내용과 연관된 과거 의사결정 기록(`memory/decisions/`)을 자동으로 분석하여 프롬프트 컨텍스트에 포함. |
| **통찰 (Discernment)** | `product:review` (리뷰 단계) | 원본 스펙 문서와 수정된 코드 차이(Diff)를 비판적으로 대조하여 잠재 오차를 분석해주는 `review_report.md` 자동 생성. |
| **성실 (Diligence)** | `workflow/review-gates.md` | PR 작성 전에 린트, 테스트 패스 여부, 보안 가이드라인 준수 여부를 자동으로 최종 체크하는 게이트웨이 스크립트화. |

---

## 4. Claude Opus 전달용 프롬프트 템플릿

아래 프롬프트를 복사하여 **Claude Opus**와의 대화창에 바로 입력해 보세요.

### 📥 [프롬프트 1] Git-native 컨텍스트 그래프 및 메모리 파서 구현 요청
```markdown
수석 소프트웨어 엔지니어로서 답변해 주세요. 우리 프로젝트(ModuFlow)의 메모리 관리 레이어에 Neo4j 스타일의 "컨텍스트 그래프(Context Graph)" 구조를 Git 로컬 마크다운 파일 기반으로 구현하려고 합니다.

다음 요구사항을 준수하여 코드를 작성해 주세요:
1. `scripts/project_memory.py` 스크립트를 업데이트하여 `memory/` 폴더 내 모든 마크다운 파일의 YAML frontmatter 정보를 파싱하는 기능을 추가해 주세요.
2. YAML의 `relations` 항목에 있는 `supersedes`, `depends_on`, `references` 등의 관계를 그래프의 엣지(Edge)로 모델링해 주세요.
3. `project_memory.py`에 `--graph` 옵션을 구현해 주세요. 이 옵션을 실행하면 현재 로컬 메모리 노드와 엣지를 분석하여 관계도를 한눈에 보여주는 Mermaid 다이어그램 텍스트를 터미널과 `memory/index.md`에 출력해야 합니다.
4. 구현된 관계 파싱 및 다이어그램 생성 로직을 검증하는 단위 테스트를 `tests/test_project_memory.py`에 추가해 주세요.

코드는 모두플로의 가볍고 Git 친화적인(Git-native) 아키텍처 규칙을 준수해야 합니다.
```

### 📥 [프롬프트 2] AI 협업 프레임워크(4대 원칙) 워크플로우 통합 요청
```markdown
제품 아키텍트로서 답변해 주세요. 모두플로(ModuFlow)의 작업 실행 루프와 검토 흐름에 Anthropic의 "AI 협업 프레임워크" 4대 원칙(위임, 기술, 통찰, 성실)을 도입하려고 합니다.

다음 기능들을 설계하고 구현해 주세요:
1. **위임(Delegation)**: `workspace/loop-state.json`에 `delegation_level` 속성("full", "review_required", "manual")을 추가하고, `product:execute` 실행 시 이 권한을 확인하여 필요 시 사용자 확인(Human-in-the-loop)을 거치도록 제어 장치를 추가해 주세요.
2. **기술(Description)**: `scripts/worker_orchestrator.py`를 고도화하여, 특정 태스크를 위해 하위 에이전트를 생성할 때 `memory/decisions/`에 있는 관련 의사결정 이력을 자동으로 추출해 에이전트 지시문(Prompt)에 맥락(Context)으로 결합해 주도록 코드를 변경해 주세요.
3. **통찰(Discernment)**: `product:review` 명령 시, 전체 코드 수정본을 단순히 보여주는 것이 아니라, 스펙 문서(`spec.md`)의 인수 조건과 코드 변경 사항(Diff)을 분석하여 잠재적 예외 상황을 도출하는 자동 검토 체크리스트 보고서(`review_report.md`) 생성 모듈을 만들어 주세요.
4. **성실(Diligence)**: PR 작성(`product:pr`)이 실행되기 전에, 테스트 빌드 검사, 린터 에러 검사, 보안 가이드라인 일치 여부를 종합 판단하는 `workflow/review-gates.md` 검증 자동화 파이프라인을 구축해 주세요.

모든 추가 파일 및 코드는 모두플로 표준 규격을 준수해야 합니다.
```

---

## 5. 코드베이스 대조 어드바이스 (0.2.15 기준)

> 이 섹션은 위 설계안을 실제 0.2.15 코드베이스와 대조해 검토한 결과입니다. 안티그라비티 작업 전 읽어주세요.

### 결론 (BLUF)

이 문서는 좋은 방향이지만 **"신규 아키텍처 도입"으로 과대 포장**돼 있습니다. 제안 4개 중 상당수가 0.2.15에 **이미 구현**돼 있어 — **재구축이 아니라 확장**으로 접근해야 합니다. 그리고 **#2(기술/Description)는 우리 자신의 컨텍스트 격리 규칙과 정면충돌**합니다.

### 항목별 갭 분석 (제안 vs 현 구현)

| 제안 | 현 상태 | 실제 갭 |
| :--- | :--- | :--- |
| **#1 컨텍스트 그래프** | `scripts/project_memory.py`에 `parse_frontmatter` + `supersedes` 관계 **이미 존재**. `memory/` 디렉토리 구조 완비 | `depends_on`/`references` 엣지 파싱 + `--graph` Mermaid 출력 **만** 추가. 좁은 확장 |
| **#2 기술 (메모리 주입)** | `scripts/worker_orchestrator.py`는 Prompt 구성만, 메모리 주입 없음 | ⚠️ **설계 충돌** (아래 참조) |
| **#3 통찰 (review_report.md)** | `commands/product-review.md`가 이미 PM/UX/QA/release 검토 → `specs/<issue>/status.md` 산출 + 서브에이전트 디스패치 설계 보유 | 새 파일 신설은 **중복**. `status.md` 강화가 맞음 |
| **#4 성실 (review-gates)** | `scripts/release_check.py`가 importable validation + 테스트 suite + 필수 문서 **이미 검사**. `workflow/review-gates.md`는 states/roles 문서(실행기 아님) | 빠진 건 **lint + 보안 게이트**뿐. `release_check.py` 확장 |
| **delegation** | `workspace/loop-state.json`에 `delegation_level` 없음 (`execution_backend.type=manual`은 별개 개념) | 진짜 신규. 가장 단순 |

### 가장 중요한 지적: #2가 자기 규칙을 위반

`memory/decisions/` 전체를 워커 프롬프트에 자동 주입하는 설계는, 글로벌 CLAUDE.md **"M/L 컨텍스트 격리 패턴 — 대형 컨텍스트 인라인 전달 시 에이전트 컨텍스트 오염 + 비용 증가, 경로만 전달"** 과 정확히 반대입니다.

→ **decision 본문이 아니라 경로(reference) 또는 관련도 필터링된 요약**만 주입할 것. 스타일 지적이 아니라 미래의 실제 버그(컨텍스트 오염·비용 폭증)를 막는 지점입니다.

### 실행 권고

1. **이슈를 4개로 분할** — 프롬프트 2가 무관한 변경 4개를 한 번에 요구해, 리뷰 불가능한 거대 diff를 낳습니다.
2. **빠른 승부(quick win)부터**: `delegation_level`(loop-state 필드 추가, 거의 trivial) + `--graph`(기존 파서 확장). 이 둘 먼저.
3. **프롬프트 1 수정**: "구현하라"가 아니라 **"기존 `parse_frontmatter`/`supersedes` 로직을 확장하라"** 로 명시 — 안 그러면 Opus가 이미 있는 파싱을 처음부터 다시 짭니다.
4. **#3은 신규 파일 금지** → `status.md` 산출 강화로. **#4는 `release_check.py`에 lint/보안 추가**로 리프레이밍.

### 권장 작업 순서

```text
1단계 (quick win, 독립적)
  ├─ delegation_level → workspace/loop-state.json 필드 추가 + product:execute 게이트
  └─ --graph 옵션 → project_memory.py 기존 파서 확장 (depends_on/references 엣지 + Mermaid)

2단계 (1단계 의존)
  └─ #2 기술 → worker_orchestrator.py에 "경로/요약만" 주입 (본문 인라인 금지)

3단계 (기존 자산 확장, 신규 파일 금지)
  ├─ #3 통찰 → product:review의 status.md 산출 강화
  └─ #4 성실 → release_check.py에 lint + 보안 게이트 추가
```

