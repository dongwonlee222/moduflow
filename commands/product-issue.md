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

1. Check existing issues for overlap before creating a new issue.
2. Create or update `issues/<id>-<slug>.md`.
3. Include lifecycle metadata as the canonical inline `**Status:**` line near the top (`backlog|active|done|superseded`, plus created/started/completed dates in prose after it) — not a separate `## Lifecycle` block (048/069 convention).
4. Link opportunity, owner, scope, priority, acceptance criteria, related issues, sessions, and related artifacts.
5. Dependency/priority fields (069): add `**Priority: p0|p1|p2|p3**` near the top, right after the `**Status:**` line (absent ⇒ defaults to `p2`). Add `**Blocked-by: <id>, <id>**` when the issue cannot start until other issues finish (absent ⇒ no blockers). Both are additive inline metadata — same convention as the canonical Status line (048), no frontmatter. `python3 scripts/project_lifecycle.py . --ready` lists unblocked backlog issues sorted by priority; `moduflow_ready` (MCP) returns the same list.
6. Add a **Workflow Tasks** checklist. Every artifact-producing step (spec, plan, design, execute, review) is a tracked task with its artifact link and status — never produce an artifact off the books. As each step runs, check its box and link the artifact. This keeps the workflow itself visible inside the issue.
7. Write a **`## 요약`** section in Korean, one or two sentences, directly above `## Summary`. This is what the dashboard shows as the issue description and what the `한글 개요` panel is built from; without it the row renders `EN` with a `한글 없음` flag. The slot exists so the path is taken at creation time rather than remembered later; issue 121 proposes making that a constitution principle.
8. Do **not** add the issue to `workspace/issue-descriptions.ko.json`. That map is legacy: it was the only working path until 2026-09-05, it stopped being updated after issue 087, and 32 issues now render in English with a further 55 depending on this map alone. Entries still win as an override so old rows keep rendering, but adding a key there rebuilds the manual path that failed.
9. **Assign `- Type:` under `## Source`. Do not ask the user for it — infer it and write it.** The first word must be one of four, optionally followed by ` — ` and any prose (the prose is where provenance goes, e.g. `- Type: bug — reported by the owner, 2026-09-06`):

   | Token | When | What the issue must then carry |
   | --- | --- | --- |
   | `bug` | something that should work does not | **`## 원인`** — pasted command output, or the literal `원인 미상` |
   | `feature` | something that did not exist | nothing extra |
   | `chore` | behaviour unchanged; tidying, moving, version bumps | nothing extra |
   | `spike` | "go find out" | `## Goal` and `## Findings` |

   `chore` is the leftover bucket and deliberately requires nothing — a bucket that demands sections stops being a bucket. The line between `chore` and `spike`: a spike produces **findings**, a chore produces a **changed repository**.

   There is no `opportunity` token. Work that is not yet shaped belongs in `workspace/opportunities.md` via `/moduflow opportunity`; a file existing in `issues/` already means that stage is past (`commands/product-promote.md`: "do NOT create a hollow issue").

   Assigning rather than asking is the point. kubernetes keeps twelve `kind/` labels and its four issue templates each force exactly one; ModuFlow's 142 free-prose `Type:` values are what happens without that gate. Issues written before this rule keep their prose and are skipped, not failed.
10. **`## 원인` holds only what was run.** Paste the command and its output, or write `원인 미상`. Hedging — `추측`, `~것 같`, `~로 보임`, `hypothesis`, `likely`, `probably` — fails validation inside that section. An issue with a symptom and no cause is complete and correct; `원인 미상` is the honest answer, not a gap. Issue 126 labelled its guess as unverified and still sent the next reader to the wrong function, which is why labelling is not enough.
11. If GitHub CLI is available and requested, create or sync the GitHub issue (see GitHub Issue Sync below).
12. **처음 쓰는 말은 풀어씁니다.** `## 요약`과 `## 원인`은 이 이슈를 처음 보는 사람이 읽습니다. 그 사람이 처음 보는 말은 그 자리에서 풀어쓰고, 못 풀겠으면 쓰지 않습니다. 판별법 하나 — **이 말을 처음 보는 사람이 뜻을 알까?** 모르겠으면 풀어씁니다. 기계는 검사할 수 없습니다. 예시는 `commands/product-spec.md`의 「처음 쓰는 말은 풀어쓴다」를 보십시오.


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
