---
description: Show current product execution state and next recommended command.
argument-hint: "[issue id]"
---

# /product:status

Make progress visible.

## Do

1. Run a non-destructive `git fetch` first, then compare local against upstream (`git rev-list --left-right --count HEAD...@{u}`). Status reads local files only, so without this it can show a stale snapshot as if current.
   - If local is behind, report "원격이 N커밋 앞섬 — pull 필요" in the dashboard.
   - If the working tree is clean, recommend (or run after confirming) `git pull` before rendering, so status reflects the latest.
   - If the working tree is dirty or `@{u}` is unset, do NOT auto-pull — surface the state and let the user decide.
2. Read `.moduflow/state.json`, `workspace/loop-state.json` when present, issues, specs, tasks, PR notes, releases, and roadmap.
3. Render a Korean-first terminal-style dashboard before detailed prose.
4. Report current phase, active issue, active/recent sessions, blockers, queue, risks, changed files, and next command.
5. If project mode is available from doctor/status context, show plain guidance such as "프로젝트 설정이 가볍고 정상입니다" instead of raw labels like `lightweight`, `dogfooding`, or `heavy`.
6. If `workflow/team-state.json` exists, include the PM-friendly team view:

```bash
python3 scripts/project_workflow.py <project-path> --team-status
```

7. When status is shown after a completed action, render the same structured next handoff used by `product:loop`: next work, reasons, concrete actions, follow-on priority, and exact command when useful.
8. When status is shown after a resumed or interrupted task, include the resume banner before the dashboard.
9. Do not mutate local artifact files during normal status display (the `git fetch` in step 1 is read-only; an approved `git pull` is the only allowed sync).
10. If source artifacts look stale or inconsistent, report the mismatch and recommend `product:doctor`.

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

## Dashboard Format

Use this structure as the default. Keep it compact and adapt missing fields gracefully.

```text
╭─ 🧭 ModuFlow 상태 ─────────────────────────╮
│ 프로젝트  <project name>                    │
│ 모드      <git-files|github-sync>           │
│ 브랜치    <branch> <동기화: 최신|N커밋 뒤> │
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

➡️ 다음 명령
  <next command>
```

## Emoji Guidance

- 🟢 healthy, done, or unblocked
- 🟡 in progress, warning, or needs attention
- 🔴 blocked or failing
- ⚪ not started or optional

Prefer Korean labels. Use emojis sparingly for scanning, not decoration.
