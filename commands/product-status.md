---
description: Show current product execution state and next recommended command.
argument-hint: "[issue id]"
---

# /product:status

Make progress visible.

## Do

1. Run repo sync preflight. `project_sync.py` fetches remote refs itself (5s timeout, non-interactive) before comparing — no manual `git fetch` step needed:

```bash
python3 scripts/project_sync.py <project-path>
```

Status reads local files only, so without a fresh fetch it can show a stale snapshot as if current — this is why the fetch happens inside the preflight call itself rather than being a separate manual step.
   - If local is behind, report "원격이 N커밋 앞섬 — pull 필요" in the dashboard.
   - If the upstream branch is gone, report "현재 브랜치의 원격이 삭제됨 — main 동기화 필요".
   - If `origin/main` has issue files missing locally, report those issue IDs before rendering the local queue.
   - If the working tree is clean, recommend (or run after confirming) `git pull` before rendering, so status reflects the latest.
   - If the working tree is dirty or `@{u}` is unset, do NOT auto-pull — surface the state and let the user decide.
   - If `unmerged_branch_work` is non-empty, report it plainly (e.g. "다른 브랜치에 완료된 이슈가 있음: `<branch>` — 056, 057") before rendering the queue — this catches finished work on a branch the user forgot about (e.g. from another tool/session), which a `origin/main`-only comparison misses.
   - If `fetched` is `false` in the preflight result, report the `fetch_warning` plainly (e.g. "원격 확인 실패 — 마지막 fetch 기준 정보입니다") instead of presenting the freshness numbers as current.
2. Read `.moduflow/state.json`, `workspace/loop-state.json` when present, issues, specs, tasks, PR notes, releases, and roadmap.
3. Render a Korean-first terminal-style dashboard before detailed prose.
4. Report current phase, active issue, active/recent sessions, blockers, queue, risks, changed files, and next command.
5. In `git-files` mode, explain that GitHub repo files under `issues/*.md` are canonical; GitHub Issues objects are optional mirrors and may be empty.
6. If project mode is available from doctor/status context, show plain guidance such as "프로젝트 설정이 가볍고 정상입니다" instead of raw labels like `lightweight`, `dogfooding`, or `heavy`.
7. If `workflow/team-state.json` exists, include the PM-friendly team view:

```bash
python3 scripts/project_workflow.py <project-path> --team-status
```

8. When status is shown after a completed action, render the same structured next handoff used by `product:loop`: next work, reasons, concrete actions, follow-on priority, and exact command when useful.
9. When status is shown after a resumed or interrupted task, include the resume banner before the dashboard.
10. Do not mutate local artifact files during normal status display (the `git fetch` in step 1 is read-only; an approved `git pull` is the only allowed sync).
11. If source artifacts look stale or inconsistent, report the mismatch and recommend `product:doctor`.

## Output

Default `상태` output is concise and Korean-first. When `workspace/loop-state.json` exists, use it for the active goal, active issue cursor, phase, blocker, and next command. Do not expose raw JSON, full artifact lists, attempts counters, or long queues unless the user asks for diagnostics or details.

```text
현재 목표: <goal>
현재 이슈: <issue> (<phase>)
다음: <plain-language next action>
명령: <product:* command>
막힘: 없음 | <blocker>
```

After completed work, prefer the richer handoff format from `product:loop` over this compact status block.

When resuming work, prepend:

```text
이어받음: <goal or issue id>
완료됨: <already completed items>
지금: <current action>
다음: <next handoff target>
```

Detailed status mode may include:

- Current phase
- Active/recent sessions when available
- Queue
- Blockers and risks
- Team work queues from `workflow/team-state.json` when present
- Source artifact links when useful
- Loop status and attempts
- Next recommended command

### Next-Command Guidance (issue 055)

Always close with a ranked, concrete list of at most 3 next commands (the single best one first) — never the full command index. Rank by the loop state: e.g. an issue in `spec` phase gets `product:plan` first; a completed review gets `product:pr`. When the user seems unsure what any command does, point to `product:loop` ("다음 단계를 알아서 골라줌") instead of explaining the whole surface. New-project states (no goal, no issues) rank `product:goal` → `product:issue` → `product:status`, matching `product:start`'s first-run guidance.

## Dashboard Format

Use this structure as the default. Keep it compact and adapt missing fields gracefully.

```text
╭─ 🧭 ModuFlow 상태 ─────────────────────────╮
│ 프로젝트  <project name>                    │
│ 모드      <git-files|github-sync>           │
│ 브랜치    <branch> <동기화: 최신|N커밋 뒤> │
│ 원격      <upstream|gone|없음>              │
│ 단계      <emoji> <phase>                   │
╰────────────────────────────────────────────╯

🎯 현재 이슈
  <issue id>
  <issue summary>

🧵 진행 세션
  <active/recent sessions or "아직 기록된 세션 없음">

📌 대기열
  1. <next issue>
  2. <next issue>
  3. <next issue>

🚧 블로커
  <blockers or "없음">

🌿 다른 브랜치 미병합 작업
  <one line per unmerged_branch_work entry: "<branch> — <ahead>커밋, done 이슈: <ids>" or omit this whole section when unmerged_branch_work is empty>

➡️ 다음 명령
  <next command>
```

The 🌿 section only appears when `unmerged_branch_work` is non-empty — omit it entirely on the clean path, per the "adapt missing fields gracefully" rule above. This is the field `062-detect-unmerged-branch-work` added; it must render here, not just exist in the JSON, or a done-but-unmerged issue on another branch stays invisible to the person reading the dashboard.

## Emoji Guidance

- 🟢 healthy, done, or unblocked
- 🟡 in progress, warning, or needs attention
- 🔴 blocked or failing
- ⚪ not started or optional

Prefer Korean labels. Use emojis sparingly for scanning, not decoration.
