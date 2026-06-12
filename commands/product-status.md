---
description: Show current product execution state and next recommended command.
argument-hint: "[issue id]"
---

# /product:status

Make progress visible.

## Do

1. Read `.moduflow/state.json`, issues, specs, tasks, PR notes, releases, and roadmap.
2. Render a Korean-first terminal-style dashboard before detailed prose.
3. Report current phase, active issue, active/recent sessions, blockers, queue, risks, changed files, and next command.
4. Do not mutate files during normal status display.
5. If source artifacts look stale or inconsistent, report the mismatch and recommend `product:doctor`.

## Output

- Korean status dashboard
- Current phase
- Active issue
- Active/recent sessions when available
- Queue
- Blockers and risks
- Source artifact links when useful
- Next recommended command

## Dashboard Format

Use this structure as the default. Keep it compact and adapt missing fields gracefully.

```text
╭─ 🧭 ModuFlow 상태 ─────────────────────────╮
│ 프로젝트  <project name>                    │
│ 모드      <git-files|github-sync>           │
│ 브랜치    <branch>                          │
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
