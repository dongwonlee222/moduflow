---
id: 2026-06-27-github-platform-benchmark
kind: evidence
title: GitHub 2025-2026 PM 플랫폼 벤치마킹
date: 2026-06-27
tags: [benchmark, github, pm, ai-agent, copilot, knowledge, comparison]
summary: GitHub의 프로젝트 관리(Projects v2, Issues, Discussions, Wiki), AI 기능(Copilot Coding Agent, Copilot PR Review), CI/CD(Actions, CodeQL), Releases 기능을 ModuFlow Git-native PM 방식과 종합 비교 분석.
owner: Dongwon Lee
confidence: high
source_event: benchmarking_session
source_artifacts:
  - "memory/evidence/2026-06-27-github-platform-benchmark.md"
references:
  - "https://docs.github.com/en/issues/planning-and-tracking-with-projects"
  - "https://github.com/features/copilot"
reversal_conditions: GitHub이 git-native 오프라인 PM 기능을 출시하거나, ModuFlow가 GitHub 소셜/알림 레이어를 구현하는 경우.
---

# GitHub 2025–2026 PM 플랫폼 벤치마킹

> 조사 일자: 2026-06-27. GitHub 공식 문서, 블로그, 커뮤니티 리포트 기반.

---

## 핵심 요약 스코어카드

| 기능 영역 | GitHub | ModuFlow | 비고 |
|---|---|---|---|
| 이슈 추적 | ⭐⭐⭐⭐ | ⭐⭐⭐ | GitHub UI 풍부; ModuFlow AI 컨텍스트 우세 |
| 스펙/PRD | ⭐⭐ | ⭐⭐⭐⭐⭐ | spec.md 전용 구조 |
| 로드맵 | ⭐⭐⭐ | ⭐⭐⭐ | Projects Roadmap vs Now/Next/Later |
| 지식/의사결정 기록 | ⭐⭐ | ⭐⭐⭐⭐ | ModuFlow knowledge/ 레이어 우세 |
| AI 코딩 에이전트 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Copilot Coding Agent 최강 |
| PR 리뷰 (AI) | ⭐⭐⭐⭐ | ⭐⭐ | Copilot 심각도 라벨링 우세 |
| CI/CD + 보안 | ⭐⭐⭐⭐⭐ | ⭐ | Actions + CodeQL + Dependabot |
| 릴리스 | ⭐⭐⭐⭐ | ⭐⭐⭐ | GitHub 불변 릴리스+Sigstore; ModuFlow 롤백 아티팩트 |
| 오프라인/이식성 | ⭐ | ⭐⭐⭐⭐⭐ | ModuFlow 압도적 우세 |
| 벤더 독립성 | ⭐ | ⭐⭐⭐⭐⭐ | 순수 git = 락인 없음 |
| AI 컨텍스트 풍부함 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 구조화된 마크다운 = LLM 컨텍스트 최적 |
| 팀 협업/소셜 | ⭐⭐⭐⭐⭐ | ⭐⭐ | GitHub 알림/CODEOWNERS/멘션 |

---

## GitHub가 ModuFlow 대비 앞서는 영역

1. **Copilot Coding Agent (GA 2025)**: 이슈를 AI에게 직접 할당 → 비동기 코드 작성 → Draft PR 생성. GitHub 런타임 환경에 깊이 통합.
2. **팀 소셜 레이어**: 알림, @멘션, CODEOWNERS, 리뷰 요청 — git-markdown만으로 복제 불가.
3. **공급망 보안**: 불변 릴리스(Immutable Releases) + Sigstore 증명 + CodeQL + Dependabot — 완전한 보안 포스처.
4. **이슈→PR 자동 연결**: PR 병합 시 연결된 이슈 자동 종료 + Projects 상태 업데이트.
5. **서브이슈 (Sub-issues, GA 2025)**: 8단계 네이티브 부모-자식 계층 + 진행률 자동 롤업.

---

## ModuFlow가 GitHub 대비 앞서는 영역

1. **스펙 우선(Spec-first) 구조**: spec.md가 주요 아티팩트. 이슈 본문보다 AI 에이전트에게 훨씬 풍부한 컨텍스트(페르소나, 인수기준, 리스크, 롤백).
2. **PM 아티팩트의 완전한 git 버전 관리**: 이슈/스펙/플랜/지식 파일 모두 커밋된 마크다운. `git log`, `git blame`이 PM 히스토리에도 동작.
3. **로컬 우선, 오프라인 가능**: 전체 PM 상태가 텍스트 파일 디렉토리. 인터넷 없이도 기획/스펙 작성/지식 캡처 가능.
4. **AI 에이전트 네이티브 설계**: product:loop, product:execute, 워커 모델이 LLM 에이전트 기반 PM 워크플로우를 위해 설계됨.
5. **지식 레이어 일급 시민**: decisions/, evidence/, research/ 폴더가 이슈/스펙과 프론트매터로 연결. GitHub에 동등한 것 없음.
6. **벤더 독립**: 순수 마크다운 + YAML + git. GitHub/GitLab/Gitea 어디서도 동작.

---

## GitHub Projects v2 주요 신기능 (2025)

- **Sub-issues GA**: 8단계 네이티브 계층, 진행률 자동 롤업
- **Dependencies GA**: "Blocked by" / "Blocking" 링크
- **Cross-repo Milestones GA**: 여러 레포 이슈를 하나의 마일스톤으로
- **Issue Types**: 조직 단위 공유 타입 (Bug, Task, Feature, Initiative)
- **50,000 items/project**: 용량 한도 증가
- **Advanced Search**: Boolean AND/OR/괄호 검색

## Copilot 신기능 (2025-2026)

- **Copilot Coding Agent**: 이슈→코드→Draft PR 완전 자동화 (GA)
- **Custom Agents**: 팀 맞춤 에이전트 정의/공유
- **Copilot PR Review**: 심각도 라벨(High/Medium/Low), 그룹화된 제안
- **분석 깊이 조절**: Low/Medium 티어로 비용/품질 균형
- **`.github/copilot-instructions.md`**: 프로젝트별 리뷰 커스텀 지침

## GitHub Actions 보안 강화 (2025-2026)

- **CodeQL 워크플로우 파일 스캔**: CI/CD YAML 자체의 취약점(script injection 등) 감지
- **Immutable Releases**: 릴리스 후 에셋 변경/삭제 불가 + Sigstore 서명
- **SHA256 다이제스트**: 모든 릴리스 에셋 자동 체크섬
- **Custom Deployment Protection Rules**: 외부 서비스(Datadog, ServiceNow) 연동 게이트

---

## ModuFlow에 대한 시사점

### 즉시 적용 가능한 아이디어
1. **Copilot Coding Agent 통합**: `product:execute` 시 GitHub에서 이슈를 Copilot에 할당하는 옵션 추가 가능
2. **Sub-issues 스타일 계층**: 이슈 파일에 `parent_issue_id` 프론트매터 추가로 GitHub Sub-issues와 동등한 구조 구현 가능
3. **PR auto-close 연동**: product:pr 완료 시 GitHub closing keywords를 이슈 파일에 기록하는 훅 추가

### ModuFlow가 계속 차별화해야 할 영역
1. **스펙-먼저 (Spec-first) 철학 유지**: GitHub Copilot이 이슈 본문만 읽는 동안 ModuFlow는 spec.md 전체를 에이전트에 주입
2. **지식 레이어 강화**: decisions/, evidence/ 폴더를 더 자동으로 채우는 것이 GitHub Discussions 대비 핵심 차별점
3. **오프라인/이식성**: GitHub의 본질적 클라우드 의존성은 극복 불가. ModuFlow의 git-native 접근이 영구적 강점
