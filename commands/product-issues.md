---
description: Show the current project's issue overview.
argument-hint: "[status|active|queue|done]"
---

# /product:issues

Show all issues in the current project.

## Do

1. Identify the project root.
2. Read `workspace/issues.md` when present.
3. If `workspace/issues.md` is missing, scan `issues/*.md` and recommend creating the issue index.
4. Render a Korean-first issue overview in chat.
5. Keep this command read-only unless the user asks to update or regenerate the issue index.

## Output

- Active issues
- Accepted or in-progress issues
- Queued issues
- Blocked issues
- Done issues
- Related issue hints when available
- Next recommended command

## Portfolio Distinction

Use `product:issues` for one project.
Use `product:portfolio` for multiple projects.

## Example

```text
📋 이슈 전체보기

🎯 진행 중
  005-issue-index-and-portfolio-view

🟡 대기
  002-multi-session-issue-workflow
  004-doctor-validation-workflow

✅ 완료
  001-plugin-development-issue-workflow
  003-korean-status-dashboard
  006-natural-language-command-routing

➡️ 다음 명령
  product:status
```
