# 코드리뷰 접수: 2026-08-21-issue-102-post-release-validation

## 출처

- 유형: `ai`
- 제공자: `external-project-validation`
- 작성자/도구: `external-project-validation`
- 보관: `reference`
- 대상: `github.com/dongwonlee222/moduflow@010eee8eeec3`

## 어댑터 실행

- 호출: manual-review-document, superpowers-review
- 생략: github-review, security-review, spec-kit

## Finding

### F-001 — high

- 관찰: Several project-aware consumers still construct knowledge, workflow, workspace, issue, memory, and spec paths directly from the project root instead of consuming the resolved project context.
- 권장: Audit every project path consumer and migrate it to project_registry.canonical_path through an explicit resolved project context, with non-default-path contract tests.
- 원인 가설: Issue 102 migrated the planned initial consumer set but its broader all-consumer completion claim was not backed by an exhaustive direct-path audit.
- 리뷰어 확신도: `high`
- 검증 상태: `confirmed`
- 판정: `accept`
- 경로: `pre_release`
- Provider 상태: `해당 없음`
- Provider dismiss 사유: `해당 없음`

### F-002 — high

- 관찰: The resolver returns archived and read-only projects as resolved without exposing project_status or operation capabilities, and mutating workflows do not share a project capability gate.
- 권장: Add project_status plus read, write, execute, and publish capabilities to resolved context and require every mutating workflow to fail closed on the relevant denied capability.
- 원인 가설: Resolution identity and operation authorization were modeled as one success state even though registry status and trust scope are separate policy inputs.
- 리뷰어 확신도: `high`
- 검증 상태: `confirmed`
- 판정: `accept`
- 경로: `pre_release`
- Provider 상태: `해당 없음`
- Provider dismiss 사유: `해당 없음`

### F-003 — medium

- 관찰: The installed plugin cache passes package validation but fails the source repository release check and project Doctor because those commands require Git history, full source tests, and project artifacts intentionally omitted from the cache.
- 권장: Separate source release validation, installed plugin self-check, and target project Doctor into explicit modes with mode-appropriate requirements and messages.
- 원인 가설: Validation entry points identify their target from the supplied path without a package/source/project role contract.
- 리뷰어 확신도: `high`
- 검증 상태: `confirmed`
- 판정: `accept`
- 경로: `post_release_refactor`
- Provider 상태: `해당 없음`
- Provider dismiss 사유: `해당 없음`

### F-004 — medium

- 관찰: Product status and Doctor do not show the actually loaded runtime version, package path, source commit, or loaded-at timestamp, so source, installed cache, and current-session versions cannot be distinguished reliably.
- 권장: Publish a runtime provenance record through product status and Doctor with version, package path, source commit, loaded-at, and host/session source.
- 원인 가설: Existing installed-plugin checks compare versions for staleness but do not model the active runtime instance.
- 리뷰어 확신도: `high`
- 검증 상태: `confirmed`
- 판정: `accept`
- 경로: `post_release_refactor`
- Provider 상태: `해당 없음`
- Provider dismiss 사유: `해당 없음`

## 확정 이슈 매핑

- `F-001` → `109-canonical-project-context-consumer-convergence` (P0, Issue 103 차단)
- `F-002` → `110-project-operation-capability-enforcement` (P0, Issue 103 차단)
- `F-003`, `F-004` → `111-runtime-provenance-and-validation-mode-separation` (P1, 병렬 가능·다음 플러그인 릴리스 전 필수)

네 finding은 기존 Issue 065, 088, 102, 103, 105와 대조했다. 동일 deliverable은 없었고, 검증 모드와 runtime provenance는 하나의 운영 진단 계약으로 묶어 중복 이슈를 만들지 않았다.
