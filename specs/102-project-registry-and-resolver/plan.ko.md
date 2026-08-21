# 구현 계획 요약: 프로젝트 레지스트리와 Resolver

Issue: `102-project-registry-and-resolver`
상태: 계획 완료 · 구현 미착수
Canonical plan: `specs/102-project-registry-and-resolver/plan.md`

## 구현 원칙

- 등록된 프로젝트만 후보로 사용하며 형제/상위 폴더를 탐색하지 않는다.
- 프로젝트가 하나로 확정되기 전에는 후보 프로젝트의 issue, config, memory, production record, playbook, state를 읽거나 쓰지 않는다.
- Issue 093의 `configured_project_paths`와 이슈 parser를 그대로 재사용한다.
- `projects.v1`은 계속 읽고 migration proposal만 보여준다.
- v2의 canonical 경로는 모두 등록 root 안의 상대 경로이며 외부 경로·`..`·symlink 이탈은 차단한다.
- 기존 단일 프로젝트 root 인자는 계속 지원하지만 형제 프로젝트 접근 권한으로 확대하지 않는다.
- 구현은 모든 행동 변경을 테스트 실패부터 시작하는 TDD 방식으로 진행한다.

## 작업 순서

1. **A1 — Registry parser:** `projects.v2`, 진단, alias 정규화, 경로 포함 범위를 만든다.
2. **A2 — Resolver:** 명시 ID → CWD → 이름/별칭 → active project → 최근 선택 순서를 구현하고 모호하면 fail-closed한다.
3. **B1 — 호환 계층:** v1 migration proposal, explicit-root context, recent selection을 추가한다.
4. **B2 — Portfolio:** 새 portfolio template과 현재 dogfood registry를 v2로 전환한다.
5. **C1 — 핵심 소비자:** intake, loop, lifecycle, Doctor, migration의 직접 경로 조합을 제거한다.
6. **C2 — 조회 계층:** production, memory/knowledge, dashboard, MCP가 같은 context를 사용하도록 한다.
7. **C3 — 쓰기 계층:** execute, PR, GitHub sync, promote, issue generator가 canonical issue/spec/workspace에만 쓴다.
8. **D1 — 검증:** 배포 manifest, spec consistency, 전체 테스트, project validation, lifecycle drift, release check를 통과한다.

## 핵심 계약

Resolver 결과는 다음 필드를 고정한다.

```yaml
schema: moduflow.project-resolution.v1
status: resolved | ambiguous | unresolved
project_id:
reason_code:
candidates: []
canonical_root:
relative_paths: {}
paths: {}
trust_scope:
warnings: []
question:
```

`ambiguous`와 `unresolved`에서는 root/path/trust_scope가 비어 있고 후보는 ID와 이름만 보여준다.

## 구현 전 게이트

- 계획 작성은 소스 구현 승인이 아니다.
- 실행 시 `codex/102-project-registry-and-resolver` 분리 브랜치/워크트리를 사용한다.
- 기존 `.playwright-mcp/` 및 PNG 파일은 stage하지 않는다.
- 다음 단계는 별도 실행 승인 후 `product:execute 102-project-registry-and-resolver`다.
