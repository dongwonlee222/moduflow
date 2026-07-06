# 스펙: GitHub API 기반 Git 쓰기 대체 경로

> 이 파일은 영문 `spec.md`의 한글 읽기용 sidecar입니다. canonical은 영문입니다.

Issue: `058-git-write-fallback-via-github-api`

## 문제

Codex가 파일은 수정할 수 있지만 `.git` 메타데이터는 쓸 수 없는 환경이 있습니다. 실제로 056/057에서 `git add`가 `.git/index.lock`을 만들지 못해 실패했습니다. 이때 사람이 터미널에서 명령을 치게 넘기지 말고, 가능한 경우 GitHub API로 브랜치/커밋을 만들어야 합니다.

## 목표

- stage/commit/push 전에 로컬 Git 쓰기 가능 여부를 감지합니다.
- 로컬 Git 쓰기가 막히면 GitHub API 커밋 경로로 전환합니다.
- status, PR, release 산출물에 어떤 방식으로 커밋했는지 기록합니다.
- 사람 승인 의미는 그대로 유지합니다.
- 로컬 Git과 GitHub API가 모두 불가능할 때만 사람에게 이유와 대안을 안내합니다.

## 비범위

- 자동 merge는 하지 않습니다.
- GitHub token을 repo에 저장하지 않습니다.
- GitHub Issues 동기화는 하지 않습니다. 그 작업은 054입니다.
- force push나 파괴적인 Git 복구는 하지 않습니다.

## 동작

커밋 가능성을 세 가지로 분류합니다.

- `local-git-write`: 로컬 `.git` 쓰기가 가능해 일반 stage/commit/push를 진행할 수 있습니다.
- `github-api-commit`: 로컬 `.git` 쓰기는 막혔지만 GitHub API로 브랜치와 커밋을 만들 수 있습니다.
- `blocked`: 로컬 Git과 GitHub API가 모두 불가능합니다.

`github-api-commit`을 쓰면 다음 근거를 기록합니다.

- repository owner/name
- branch
- base branch 또는 base commit
- commit message
- commit URL
- file list
- 로컬 Git을 건너뛴 이유

## 승인 기준

- Git write preflight가 `mode`, `ok`, `reason`, `recommendations`를 포함한 JSON을 반환합니다.
- `.git/index.lock` 권한 실패를 GitHub API fallback 후보로 분류합니다.
- 명령 문서가 사람에게 터미널 명령을 넘기기 전에 GitHub API fallback을 시도하라고 안내합니다.
- PR/release 산출물이 API-created commit을 기록할 수 있습니다.
- mode 결정 테스트가 있습니다.
- `python3 scripts/release_check.py .`가 통과합니다.

## 다음 명령

`product:plan 058-git-write-fallback-via-github-api`
