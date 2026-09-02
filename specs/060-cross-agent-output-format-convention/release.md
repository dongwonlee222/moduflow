# ModuFlow 0.3.56 — Issue 111 and Issue 060 Follow-up

Issue: `060-cross-agent-output-format-convention`; includes `111-runtime-provenance-and-validation-mode-separation`.
Owner / decision maker: Dongwon Lee.
Source: approved issue/spec/PR scopes and explicit sequential merge/deployment approval in the current Codex integration task, 2026-09-02.
Phase: PR #45 merged; PR #46 retargeted to main; publication authorized, final CI and installation pending.
Next command: `product:release 060-cross-agent-output-format-convention`.

## 왜 필요한지

정상 설치를 잘못 진단하거나 원본 수정만으로 현재 실행에도 적용됐다고 오해하지 않아야 합니다. 작업 목적을 먼저 설명하는 규칙도 개발 저장소가 아닌 실제 플러그인에 전달돼야 합니다.

## 해결해야 할 문제

기존 Codex 캐시는 0.3.48이며, Codex와 Claude 로컬 플러그인 연결은 기본 체크아웃을 가리킵니다. 원격 병합만으로 캐시·연결·이미 실행 중인 AI 세션이 함께 갱신되지 않습니다.

## 기대 효과

검사 대상별 진단과 실행 근거, 목적·문제·기대 효과 우선 설명을 실제 배포 패키지에서 사용할 수 있습니다. 이미 실행 중인 대화의 자동 재로드나 모든 호스트의 규칙 준수를 보장하지 않습니다.

## Approval and Review Surfaces

- Dongwon Lee approved the Korean proposal to merge PR #45 then #46 and deploy 0.3.56. Scope/CI summary was presented in the current task; direct dashboard/diff viewing was not observed.
- Approval records: [PR #45](https://github.com/dongwonlee222/moduflow/pull/45#issuecomment-5507008053), [PR #46](https://github.com/dongwonlee222/moduflow/pull/46#issuecomment-5507008342).
- Korean packets: [060](human-review.ko.md), [111](../111-runtime-provenance-and-validation-mode-separation/human-review.ko.md). PR handoffs: [060](pr.md), [111](../111-runtime-provenance-and-validation-mode-separation/pr.md).
- Local projections: `memory/dashboard.html#issue-db`, `memory/issue-111-runtime-provenance-and-validation-mode-separation.html`, `memory/issue-060-cross-agent-output-format-convention.html`; UI code is not changed by this release.
- 090/086 implementation, company data migration, unrelated plugin changes and old-cache deletion are excluded. A failing integration/release gate holds publication.

## Execution Evidence

| Stage | Observed status |
|---|---|
| PR #45 | Latest-head CI passed at `d5e143b`; merged 2026-09-02 as `973f342a7a78b38a16315a9583a7725582452756` |
| PR #46 | Retargeted to main after #45 merge; prior `c6ed2ab` CI passed; approval/evidence documentation update and latest-head CI pending |
| Fresh local source release check | All 13 checks passed on the `c6ed2ab` implementation plus the local roadmap-only update |
| Fresh local full suite | 1,614 tests passed in 290.759s, exit 0; `c6ed2ab` implementation and local roadmap update, with approval-only documentation added during the run; no code changes |
| GitHub 0.3.56 publication | Not performed |
| Codex installed package / Claude local connection | Not changed yet |
| Actual CLI / host prompt-skill load | Not observed yet; existing task must not be reported as reloaded |

## Packaging and Rollback Boundary

Use only a committed approved source export. Do not package the 25 untracked Issue 103 plans or silently include working-tree changes. Keep the default checkout and existing task worktrees unchanged. Preserve the existing Codex 0.3.48 cache, exact previous symlink targets and relevant host registration/configuration backups outside Git before activation.

A source export has no `.git`; the installer must honestly report unavailable Git provenance rather than borrowing a nearby checkout. Record the exact export commit and archive digest as separate deployment evidence. Keep the published source export in a persistent deployment directory, never an auto-deleted temporary source target. The retained Codex build suffix is not an installation timestamp; 0.3.56 is a new cache identity relative to the installed 0.3.48.

On preparation failure, do not activate. On activation failure, preserve the new/old packages and report the failing stage; restore only the recorded links/settings with approval. Rollback never deletes user artifacts or rewrites shared Git history. Post-install verification covers explicit installed validation, payload hash and a newly launched CLI; Codex/Claude prompt-skill loading needs a fresh host observation and remains separate.
