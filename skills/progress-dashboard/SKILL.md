---
name: progress-dashboard
description: Use when ModuFlow needs to show work progress, blockers, current phase, next action, dashboard summaries, or Productivity-style web/status views.
---

# Progress Dashboard

Make progress visible without moving source of truth out of Git.

## Dashboard Fields

- issue ID
- active goal
- title
- phase
- owner
- last updated
- blocker
- mode
- branch
- active/recent sessions
- queue
- loop status
- next command
- PR/release status

Use `workspace/dashboard.md` as the default low-friction dashboard. A web dashboard can be generated from the same files.

## Chat Status View

When the user asks for `status`, `상태`, "현재 상황", or "다음에 뭐 하지?", show a Korean-first text dashboard in chat before prose.

Default sections:

- 🧭 project summary: project, mode, branch, phase
- 🎯 active goal: objective, linked issue, loop status
- 🎯 current issue: issue ID and short summary
- 🧵 sessions: active/recent sessions when available
- 📌 queue: next issues or roadmap items
- 🚧 blockers: blockers, warnings, or "없음"
- ➡️ next command: one recommended ModuFlow command, usually `product:loop` when an active goal exists

Status display should normally be read-only. If files are missing, stale, or inconsistent, recommend `product:doctor` rather than silently rewriting state.
