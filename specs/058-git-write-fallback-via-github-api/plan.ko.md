# 계획: GitHub API 기반 Git 쓰기 대체 경로

> 이 파일은 영문 `plan.md`의 한글 읽기용 sidecar입니다. canonical은 영문입니다.

Issue: `058-git-write-fallback-via-github-api`
Spec: `specs/058-git-write-fallback-via-github-api/spec.md`
Next: `product:execute 058-git-write-fallback-via-github-api`

## 구현 방향

로컬 Git 쓰기 가능 여부를 먼저 판단하고, 막히면 GitHub API 커밋 경로로 자동 전환하는 표준 판단 계층을 만듭니다. 실제 GitHub API 호출은 호스트 도구가 수행하더라도, ModuFlow가 어떤 경로를 써야 하는지 판단하고 산출물에 기록해야 합니다.

## 작업 흐름

1. Commit preflight
   - repo root와 origin 확인.
   - `.git` 아래에 임시 probe 파일을 만들고 지울 수 있는지 확인.
   - 기존 `index.lock`은 건드리지 않습니다.
   - `local-git-write`, `github-api-commit`, `blocked` 중 하나로 분류합니다.

2. GitHub API fallback 계약
   - `product:pr`, `product:release`, `product:sync` 문서에 fallback 규칙을 추가합니다.
   - 사람이 터미널 명령을 치기 전에 GitHub API 경로를 먼저 시도하도록 명시합니다.

3. 산출물 기록
   - PR/release/status에 commit mode를 남깁니다.
   - API 커밋이면 commit URL/SHA와 local Git skip reason을 기록합니다.

4. 테스트
   - 로컬 Git 쓰기 가능.
   - `.git` 쓰기 막힘.
   - GitHub API 가능 시 fallback.
   - 둘 다 막힌 blocked.

## 다음 명령

`product:execute 058-git-write-fallback-via-github-api`
