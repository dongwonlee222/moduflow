---
description: 할 일 하나를 이슈 파일로 만듭니다. (create an issue)
argument-hint: "<opportunity id or issue title>"
---


# /product:issue

Create the durable work item.

## 사용 예시

```
/moduflow issue 결제 재시도가 카드를 두 번 청구한다
/moduflow issue payment retry charges the card twice
```

## Do

1. **먼저 물어봅니다 — 이걸 안 고치면 누가 무엇을 못 합니까?** 답을 `## 안 고치면`에 한 문장으로 씁니다. **답이 "아무도 막히지 않는다"이면 이슈를 만들지 않습니다.** 결함을 찾았다는 것과 고쳐야 한다는 것은 다릅니다.

   그리고 그 답이 `workspace/goal.md`의 네 가지 — **맥락·기록·결정·다음 액션** — 중 어디를 막는지 말해야 합니다. 넷 중 어디도 아니면 모두플로 일이 아닙니다. 목표 문장 그대로: *"모두플로는 맥락·기록·결정·다음 액션을 관리하고, 실제 작업은 외부 도구가 한다."*

   **조사 한 건에서 이슈 하나.** 조사하다 결함을 여럿 찾으면 제일 아픈 하나를 이슈로 만들고 나머지는 그 안에 적습니다. 2026-09-06 조사 5건에서 이슈 8개가 나왔고, 그중 넷(142·144·145·146)은 같은 병이었습니다.
2. Check existing issues for overlap before creating a new issue.
3. Create or update `issues/<id>-<slug>.md`.
4. Include lifecycle metadata as the canonical inline `**Status:**` line near the top (`backlog|active|done|superseded`, plus created/started/completed dates in prose after it) — not a separate `## Lifecycle` block (048/069 convention).
5. Link opportunity, owner, scope, priority, acceptance criteria, related issues, sessions, and related artifacts.
6. Dependency/priority fields (069): add `**Priority: p0|p1|p2|p3**` near the top, right after the `**Status:**` line (absent ⇒ defaults to `p2`). Add `**Blocked-by: <id>, <id>**` when the issue cannot start until other issues finish (absent ⇒ no blockers). Both are additive inline metadata — same convention as the canonical Status line (048), no frontmatter. `python3 scripts/project_lifecycle.py . --ready` lists unblocked backlog issues sorted by priority; `moduflow_ready` (MCP) returns the same list.
7. Add a **Workflow Tasks** checklist. Every artifact-producing step (spec, plan, design, execute, review) is a tracked task with its artifact link and status — never produce an artifact off the books. As each step runs, check its box and link the artifact. This keeps the workflow itself visible inside the issue.
8. Write a **`## 요약`** section in Korean, one or two sentences, directly above `## Summary`. This is what the dashboard shows as the issue description and what the `한글 개요` panel is built from; without it the row renders `EN` with a `한글 없음` flag. The slot exists so the path is taken at creation time rather than remembered later; issue 121 proposes making that a constitution principle.
9. Do **not** add the issue to `workspace/issue-descriptions.ko.json`. That map is legacy: it was the only working path until 2026-09-05, it stopped being updated after issue 087, and 32 issues now render in English with a further 55 depending on this map alone. Entries still win as an override so old rows keep rendering, but adding a key there rebuilds the manual path that failed.
10. **Assign `- Type:` under `## Source`. Do not ask the user for it — infer it and write it.** The first word must be one of four, optionally followed by ` — ` and any prose (the prose is where provenance goes, e.g. `- Type: bug — reported by the owner, 2026-09-06`):

   | Token | When | What the issue must then carry |
   | --- | --- | --- |
   | `bug` | something that should work does not | **`## 원인`** — pasted command output, or the literal `원인 미상` |
   | `feature` | something that did not exist | nothing extra |
   | `chore` | behaviour unchanged; tidying, moving, version bumps | nothing extra |
   | `spike` | "go find out" | `## Goal` and `## Findings` |

   `chore` is the leftover bucket and deliberately requires nothing — a bucket that demands sections stops being a bucket. The line between `chore` and `spike`: a spike produces **findings**, a chore produces a **changed repository**.

   There is no `opportunity` token. Work that is not yet shaped belongs in `workspace/opportunities.md` via `/moduflow opportunity`; a file existing in `issues/` already means that stage is past (`commands/product-promote.md`: "do NOT create a hollow issue").

   Assigning rather than asking is the point. kubernetes keeps twelve `kind/` labels and its four issue templates each force exactly one; ModuFlow's 142 free-prose `Type:` values are what happens without that gate. Issues written before this rule keep their prose and are skipped, not failed.
11. **`## 원인` holds only what was run.** Paste the command and its output, or write `원인 미상`. Hedging — `추측`, `~것 같`, `~로 보임`, `hypothesis`, `likely`, `probably` — fails validation inside that section. An issue with a symptom and no cause is complete and correct; `원인 미상` is the honest answer, not a gap. Issue 126 labelled its guess as unverified and still sent the next reader to the wrong function, which is why labelling is not enough.
12. If GitHub CLI is available and requested, create or sync the GitHub issue (see GitHub Issue Sync below).
13. **전문용어는 본문에, 설명은 그 뒤 괄호에.** `## 요약`과 `## 원인`의 기준은 말이 어려운지가 아니라 **읽는 사람이 그 말을 아는지**입니다. 알면 그냥 씁니다(`라우터`, `트랜잭션`). 모르면 용어 먼저 쓰고 괄호에 한 줄 답니다(`투영(지금 상태를 베껴 만든 사본)`). **이미 이름이 있는 것에 새 이름을 지어내지 마십시오** — 검색도 안 되고 문장만 길어집니다. 예시는 `commands/product-spec.md`의 「전문용어」를 보십시오.


## GitHub Issue Sync (opt-in)

Project a git-file issue to a GitHub Issue only when the user explicitly asks — never automatically. Skips itself when `.moduflow/config.json`'s `git.github_sync` is `"off"`.

```bash
python3 scripts/project_github_issues.py . --issue-id <id> --sync
```

- First sync creates the GitHub Issue (title from the issue heading, body from `## Outcome`, label `moduflow:<status>`) and writes `- GitHub: <url>` into the issue file's `## Links` section.
- Later syncs reuse that link and refresh the status label on the existing GitHub Issue — no duplicates.
- Missing `moduflow:backlog|active|done|superseded` labels are created in the repo before use.
- One-way only: `issues/<id>.md` stays canonical; the GitHub Issue is a projection. GitHub-side edits never flow back.

## Granularity Rule

One issue = one deliverable with its own lifecycle. The workflow steps that produce planning artifacts (spec, plan, design) are **tasks inside that issue**, not separate top-level issues — this avoids infinite regress (a "write the spec" issue would itself need a spec). The artifact is always tracked; only the unit is the issue's task list. Split into a new issue only when a step grows into its own deliverable.

## Fast Path Shaping

Clear issue requests stay fast:

```text
"이슈 만들어줘: README 설치법 추가" -> product:issue
```

Do not ask interview questions when the deliverable, target artifact, and verification path are already clear. If the request is ambiguous, broad, strategic, or risky, ask at most 1-3 shaping questions first or route through `/product:opportunity`. When the user explicitly wants speed, create a discovery issue and record unknowns in `Opportunity`, `Acceptance Criteria`, or `Scope Fence` instead of blocking.

## Lifecycle Actions

Support short commands and Korean natural-language equivalents:

- `issue <id> start`, `<id> 시작해줘`: set phase, started date, active issue, dashboard, and issue index.
- `issue <id> update "..."`, `<id>에 진행 내용 추가`: append progress to the issue or current session log.
- `issue <id> pause`, `<id> 멈춰줘`: summarize current progress and next action.
- `issue <id> resume`, `<id> 다시 시작해줘`: make it active and show recent context.
- `issue <id> complete`, `<id> 완료 처리해줘`: set completed date, phase, dashboard, roadmap, and issue index.

## Related Issue Check

Before creating a new issue, scan `issues/*.md` and `workspace/issues.md` when present. If the request overlaps an existing issue, recommend one of:

- update existing issue
- create a follow-up issue
- link as related
- mark as duplicate

## Session Convention

Use `sessions/<issue-slug>/<date>-<agent-or-purpose>.md` for repeated work logs when detailed context should be preserved.

## Next

- `/moduflow spec` for new product work
- `/moduflow plan` for small obvious work
- `/moduflow roadmap` when priority changed
