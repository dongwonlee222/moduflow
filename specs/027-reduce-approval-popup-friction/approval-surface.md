# Approval Surface Map: Reduce Approval Popup Friction

## Issue

`027-reduce-approval-popup-friction`

## Summary

This map separates routine ModuFlow checks from operations that genuinely need user approval. The goal is not to bypass host safety. The goal is to stop treating safe local validation as if it were the same kind of action as Git writes, network calls, credential changes, or destructive cleanup.

## Approval Classes

| Class | Meaning | Default Policy |
| --- | --- | --- |
| Local read-only | Reads repo files and returns diagnostics | Prefer importable function or host tool call |
| Local write | Creates or updates PM artifacts in the current project | Ask once with a clear write summary |
| Git read | Reads local Git state | Read-only, but host may still require approval depending on sandbox |
| Git write | Commit, merge, branch delete, checkout, reset, rebase, tag | Explicit approval; batch when safe |
| Network/GitHub | fetch, pull, push, GitHub API, remote sync | Opt-in unless user requested sync |
| Account/credential | `gh auth`, account switching, credential setup | Always explicit |
| Destructive | Delete files/branches, rewrite history, overwrite non-symlink paths | Always explicit and isolated |

## Current Validation Scripts

| Entry Point | Current Behavior | Class | Approval Friction | 027 Direction |
| --- | --- | --- | --- | --- |
| `scripts/validate_project_artifacts.py` | Exposes `validate_project(path)` and a CLI wrapper | Local read-only | Avoidable when imported directly | Keep function API; use it from tools/adapters |
| `scripts/project_doctor.py` | Exposes `inspect_project(path)` but also shells out to `git` and `gh` for preflight | Local read-only plus Git read plus GitHub account check | Partly avoidable; `git`/`gh` checks may still prompt | Split pure artifact doctor from Git/GitHub preflight |
| `scripts/validate_moduflow.py` | CLI-oriented `main()` checks required package files and manifests | Local read-only | Avoidable after extracting `validate_moduflow(root)` | Add importable validation function |
| `scripts/release_check.py` | Uses subprocess to run validation scripts and tests | Shell execution bundle | High; repeatedly shells out | Convert validation parts to imports; keep tests as shell/runner boundary |
| `python3 -m unittest ...` | Runs tests | Shell execution | Host-dependent and often approval-triggering | Keep for CI; use focused importable checks for routine status/review where possible |

## Project Mutation Scripts

These are expected to write files and should remain explicit mutation steps:

| Script | Writes | Class | Policy |
| --- | --- | --- | --- |
| `project_migrate.py --write` | `.moduflow/`, `workspace/`, `issues/`, `specs/`, `knowledge/`, `workflow/` | Local write | Ask once, show planned writes first |
| `project_profile.py --write` | `.moduflow/project-profile.md`, environments, integrations | Local write | Ask once, preserve existing files |
| `project_knowledge.py --write` / `--kind` | `knowledge/` structure or evidence artifact | Local write | Ask once, preserve existing files |
| `project_workflow.py --write` / `--record` | `workflow/` files and records | Local write | Ask once, preserve existing files |
| `project_portfolio.py --write` / `--render` | portfolio metadata and rendered dashboards | Local write | Ask once, preserve existing files |
| `worker_orchestrator.py --write` | worker plan JSON/Markdown | Local write | Ask once, issue-scoped |
| `project_loop.py --step` | loop-state and derived workflow artifacts | Local write | One safe step only, then stop |

## Git And GitHub Commands

| Surface | Operation | Class | Policy |
| --- | --- | --- | --- |
| `product:status` | `git fetch`, `git rev-list` | Network/Git read | Explain upfront; skip network in local-only mode |
| `product:start` | `git rev-parse`, `git remote get-url origin`, optional `gh auth status` | Git read / account check | Preflight only; GitHub optional |
| `product:doctor` | `git rev-parse`, `git remote get-url origin`, `gh auth status` | Git read / account check | Split from pure validation where possible |
| `product:pr` | `gh pr create` or related PR commands when requested | Network/GitHub write | Explicit approval |
| branch cleanup | local branch delete or remote delete | Git write / destructive | Explicit, isolated, never bundled silently |
| push/pull | remote sync | Network/Git write | Explicit unless user requested sync |

## Immediate Refactor Targets

1. Extract `validate_moduflow(root)` from `scripts/validate_moduflow.py`.
2. Change `release_check.py` to call importable validation functions for:
   - ModuFlow package validation
   - project artifact validation
   - project doctor artifact checks where possible
3. Keep subprocess for test execution, because tests are intentionally a runner boundary.
4. Split doctor into:
   - pure file/artifact checks
   - Git/GitHub/account preflight checks
5. Document local-only mode for `status`, `doctor`, and `review`.

## Next Handoff

다음은 importable validation API 구현이 맞습니다.

이유:
- 승인 피로의 가장 쉬운 첫 개선은 safe validation을 shell이 아니라 함수 호출로 바꾸는 것입니다.
- `validate_project_artifacts.py`는 이미 함수형이라 기준점으로 쓸 수 있습니다.
- `validate_moduflow.py`와 `release_check.py`가 다음 병목입니다.

다음 액션:
1. `validate_moduflow(root)` 함수 추가
2. 기존 CLI `main()`은 그 함수를 호출하도록 유지
3. focused test로 함수 API와 CLI 호환성을 검증

그 뒤 우선순위:
- 027: importable validation API 구현
- 027: release_check subprocess 축소
- 027: doctor pure/preflight 분리

👉 바로 진행: 제가 `validate_moduflow(root)` 함수화부터 진행하면 됩니다.
