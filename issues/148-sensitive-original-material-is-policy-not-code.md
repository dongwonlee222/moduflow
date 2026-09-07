# Issue 148: Sensitive Original Material Is Policy, Not Code

**Status: backlog** — created 2026-09-07.
**Priority: p1**

## 요약

목표 파일에 **"민감한 원본 데이터는 저장소 밖에 둔다"**고 적혀 있는데, **그걸
막는 코드가 없습니다.** 사장님이 2026-09-07에 **메일·회의 의사결정·기타
자료도 메모리로 관리**해 달라고 하셨습니다. 지금 그대로 하면 메일 본문과
회의록 원본이 **git에 그대로 들어갑니다.** 한 번 커밋되면 이력에 남아서
지우기 어렵습니다.

## Summary

The "keep sensitive originals outside the repository" constraint has been in
`workspace/goal.md` since 2026-09-04 and is enforced by no code. The owner has
now asked for mail, meeting decisions and other project material to be managed
through memory, which is the first request that actually exercises the
constraint.

## Source

- Type: chore — 2026-09-07, 목표 문서를 다시 쓰면서 실측
- Owner / decision maker: Dongwon Lee
- 사장님 원문: *"그외 프로젝트의 주요 내용 메일이나 의사결정 회의내용 기타
  자료 정보등도 알아서 메모리 관리를 통해서 프로젝트가 잘 수행 되는게 목적이야"*

## 안 고치면

메일·회의록을 메모리로 관리하는 순간 민감한 원본이 git 이력에 들어갑니다. 목표의 일곱 가지 중 **메모리**가 막힙니다.

## 원인

```
$ grep -rln "민감\|sensitive" scripts/
scripts/project_profile.py
scripts/project_review.py
scripts/review_intake.py
scripts/project_sync.py
scripts/execution_host_adapter.py

$ grep -n "sensitive_data_policy" scripts/project_profile.py
80:  "sensitive_data_policy": "Store references only. Do not store secret values."
104: "sensitive_data_policy": "Store links and labels only. Do not store credentials."
127: "sensitive_data_policy": "Do not store credentials, secrets, signed originals,
     seals, identity documents, or direct personal contact/payment identifiers."

$ grep -n "sensitive" scripts/project_review.py
51:    sensitive = any(
77:        reasons.append("sensitive_path")

$ ls -d memory/references
ls: memory/references: No such file or directory
```

Five files match and **not one of them guards what lands in memory.**

- `project_profile.py` writes `sensitive_data_policy` as a **string into a
  profile**. It is a declaration a reader may see. Nothing reads it back and
  refuses a write.
- `project_review.py:51` and `review_intake.py:413` compute `sensitive_path` for
  **code-review routing** — flagging which files in a diff need a security pass.
  Unrelated to stored material.
- `project_sync.py:378` and `execution_host_adapter.py:43` are the word in a
  help string and a comment.

And `KNOWLEDGE_DIRS` in `scripts/project_knowledge.py` already lists
`references` — the slot for pointing at outside material rather than copying
it — but `memory/references/` **does not exist**, so the pattern has never
been used.

## Scope

### In

- A check that refuses a knowledge write whose body carries an original rather
  than a reference. What "an original" means has to be **stated first** — this
  issue's first task is the definition, not the check.
- `memory/references/` becomes the landing place for mail, meeting notes and
  outside documents: a pointer, a date, a one-line summary, and who to ask.
  Not the body.
- The refusal names the file and says where the original should live instead,
  in Korean.
- `project_profile.py`'s `sensitive_data_policy` string is either read by the
  check or removed. A policy nobody reads is worse than no policy — it reads
  as a guarantee.

### Out

- Scanning the existing 146 issues and 9 evidence files for material already
  committed. If something is in there, removing it is a history rewrite with
  its own approval; **this issue stops new writes only.** A separate issue
  handles what is already there, if anything is.
- Deciding where originals do live (Obsidian vault, mail client, drive). That
  is the owner's, and the reference only has to point somewhere he named.
- Automatic ingestion of mail or calendar. The owner asked for the material to
  be managed; the fetching mechanism is separate work and must not ship before
  the guard does.
- Secret scanning of code. `release_check.py` has `security_check` and it
  passes; this is about prose bodies, not keys in source.

## Known Limit

A check can refuse an obvious original — a long body, an `From:`/`To:` header
block, a transcript. It cannot tell a summary someone wrote from a summary
someone pasted. What this removes is the case where the whole thing is copied
in, not the case where a sentence of it is quoted.

## Acceptance Criteria

- "원본"과 "참조"의 구분이 한곳에 문장으로 적히고, 명령 문서가 그것을 가리킨다.
- A knowledge write carrying an original is refused; the message names the file
  and says where it should go, in Korean.
- A write carrying a reference passes.
- `memory/references/` exists with at least one real entry and a README stating
  the shape.
- `project_profile.py`'s `sensitive_data_policy` is read by the check, or gone.
- 기존 146개 이슈와 9개 evidence는 건드리지 않는다 — 라이브 트리로 확인.
- `python3 scripts/release_check.py .` 통과, 최상위 `valid` 확인.

## Verification

- 픽스처: 메일 헤더 블록이 든 본문 → 거부.
- 픽스처: 회의록 전문 → 거부.
- 픽스처: 링크 한 줄 + 요약 한 줄 → 통과.
- 라이브 트리 전체에 돌려서 새로 실패하는 파일이 **0건**임을 단언.
- `tests/test_project_knowledge.py`.

## Entry Points

- `scripts/project_knowledge.py` — `KNOWLEDGE_DIRS`, `references`가 이미 있는 곳
- `scripts/project_profile.py:80`, `:104`, `:127` — 읽히지 않는 정책 문자열
- `scripts/project_intake.py` — 바깥에서 들어오는 다른 길
- `workspace/goal.md` 「안 하는 것」 — 이 제약이 적힌 곳
- `scripts/project_review.py:51` — 이름만 같고 상관없는 `sensitive_path`

## Scope Fence

메일·캘린더 자동 수집을 이 이슈에서 만들지 않는다. 막는 장치보다 들이는
장치가 먼저 나오면, 제약이 처음 시험받는 순간에 제약이 없다.

이미 커밋된 것을 지우려고 `git` 이력을 고쳐 쓰지 않는다. 그건 승인이 필요한
별개의 일이다.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → 원본/참조 정의, 검사, `memory/references/`, 정책 문자열 처리
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `003-knowledge-evidence-layer` (done — 이 층을 만들었고, 가드는
  안 만들었다), `085-project-production-records-and-playbooks` (done — 같은
  저장 층), `142-the-per-issue-artifact-set-is-named-but-never-required`
  (같은 모양: 이름만 있고 강제가 없다),
  `144-the-type-token-is-instructed-not-enforced` (같은 모양)

## Next Command

`product:spec 148-sensitive-original-material-is-policy-not-code`
