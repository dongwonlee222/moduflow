# ModuFlow 0.3.56 — Issue 111 and Issue 060 Follow-up

Issue: `060-cross-agent-output-format-convention`; includes `111-runtime-provenance-and-validation-mode-separation`.
Owner / decision maker: Dongwon Lee.
Source: approved issue/spec/PR scopes and explicit sequential merge/deployment approval in the current Codex integration task, 2026-09-02.
Phase: PR #45/#46 merged; 0.3.56 published and installed; CLI/MCP verified, fresh Codex/Claude prompt-skill observations pending.
Next command: `product:status` in a fresh host task for post-install observation; 090 implementation is not started by this release.

## 왜 필요한지

정상 설치를 잘못 진단하거나 원본 수정만으로 현재 실행에도 적용됐다고 오해하지 않아야 합니다. 작업 목적을 먼저 설명하는 규칙도 개발 저장소가 아닌 실제 플러그인에 전달돼야 합니다.

## 해결해야 할 문제

배포 전 Codex 캐시는 0.3.48이고 Codex와 Claude 로컬 연결은 기본 체크아웃을 가리켰습니다. 원격 병합만으로 캐시·연결·이미 실행 중인 AI 세션이 함께 갱신되지 않는 문제를 배포 단계별로 확인했습니다.

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
| PR #46 | Retargeted to main; latest-head `ceb6508` CI passed; merged as `2d857dd56369248b57358103cd439ffd089f69f4` at 2026-09-02T09:01:01Z |
| Merged-source CI | Passed: [run 33611811305](https://github.com/dongwonlee222/moduflow/actions/runs/33611811305), exact source `2d857dd`; earlier #45 merge CI also passed |
| Fresh local source release check | All 13 checks passed again on `2d857dd`; source tree is identical to tested PR head `ceb6508` |
| Fresh local full suite | 1,614 tests passed in 290.759s, exit 0; `c6ed2ab` implementation and local roadmap update, with approval-only documentation added during the run; no code changes |
| GitHub 0.3.56 publication | [v0.3.56](https://github.com/dongwonlee222/moduflow/releases/tag/v0.3.56), published 2026-09-02T09:05:58Z; tag resolves to `2d857dd56369248b57358103cd439ffd089f69f4` |
| Codex installed package | `0.3.56+codex.20260810222010`; installed at 2026-09-02T09:03:54.901494+00:00; explicit installed validation passed with 0 errors / 0 warnings |
| Claude existing local connection | Updated to the same validated distribution; Claude manifest base 0.3.56; no marketplace install or fresh Claude-host load claimed |
| Actual new CLI / MCP | Both exit 0, report the installed cache/version; CLI startup 09:04:45.692533Z and MCP startup 09:04:45.827831Z on 2026-09-02; MCP initialize and status agree |
| Fresh Codex/Claude prompt skills (R01/R02) | Not observed. `host`/`session_id` are null; direct CLI/MCP proof is not a host-session reload. Do not mark these plan checkboxes passed |

Archive proof: `git get-tar-commit-id` returned `2d857dd56369248b57358103cd439ffd089f69f4`. Uploaded source SHA-256 is `3952eb116df016c6f204d647f649a73f87caad1802d3f53f280280908581c314`; GitHub's uploaded-asset digest matches. Installed payload SHA-256 is `7704888df1d00333f9baf40212293d75dc36f9c9520ab53ee0bdee619c34cf54` and matches the valid immutable receipt. `docs/output-format.md` matches the approved source byte-for-byte.

Preservation: all 25 existing untracked Issue 103 plans retain their original SHA-256 values and are absent from the export. Old 0.3.48 cache remains. Codex config and personal marketplace JSON are byte-identical to their backups; only the intended plugin symlinks/cache were changed. No default-checkout files or 090/086 task files were edited. Final evidence-only source records may follow the tag; they do not change or overwrite the immutable published package.

## Packaging and Rollback Boundary

Used only the committed approved source export. The persistent source and rollback records are outside Git under the local ModuFlow release directory, with its exact location recorded in the integration task. Previous Codex/user/Claude links all targeted the default ModuFlow checkout. Their link copies and Codex configuration/marketplace backups are preserved; the release directory is owner-only (0700).

A source export has no `.git`; the installer must honestly report unavailable Git provenance rather than borrowing a nearby checkout. Record the exact export commit and archive digest as separate deployment evidence. Keep the published source export in a persistent deployment directory, never an auto-deleted temporary source target. The retained Codex build suffix is not an installation timestamp; 0.3.56 is a new cache identity relative to the installed 0.3.48.

On preparation failure, do not activate. On activation failure, preserve the new/old packages and report the failing stage; restore only the recorded links/settings with approval. Rollback never deletes user artifacts or rewrites shared Git history. Post-install verification covers explicit installed validation, payload hash and a newly launched CLI; Codex/Claude prompt-skill loading needs a fresh host observation and remains separate.
