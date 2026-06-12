---
description: Validate ModuFlow installation and project artifacts.
argument-hint: "[project path]"
---

# /product:doctor

Validate setup.

## Do

1. Run `scripts/validate_moduflow.py` for the plugin package.
2. Run `scripts/project_doctor.py <project-path>` for the target project.
3. Run `scripts/validate_project_artifacts.py <project-path>` when the project is initialized.
4. Separate required setup errors from optional capability warnings.
5. Check Git repo, GitHub remote, GitHub CLI auth, and required `.moduflow`, `issues`, `specs`, and `workspace` files.
6. Detect likely existing project artifact folders for migration.
7. Report missing files and suggested fix commands.

## Korean Output

Render a Korean-first health check:

```text
╭─ 🩺 ModuFlow Doctor ───────────────────────╮
│ 프로젝트  <project name>                    │
│ 상태      <emoji> <healthy|warning|error>   │
│ 모드      <git-files|github-sync>           │
╰────────────────────────────────────────────╯

✅ 필수 체크
  Git repo: OK
  .moduflow: OK
  issues/: OK
  workspace/: OK

⚠️ 선택 체크
  GitHub origin: 없음 (GitHub sync 필요 시 설정)
  profile: 없음 (필요 시 product:profile)
  knowledge: 없음 (필요 시 product:knowledge)
  workflow: 없음 (필요 시 product:handoff)

➡️ 추천
  product:status
```

Missing optional capabilities are warnings, not failures, in `git-files` mode.

## Git Checks

- Git repo exists
- Git root matches intended project root
- `origin` remote exists when GitHub sync is expected
- `gh auth status` passes when issue/PR/release sync is expected

## Next

- `product:start` if project is not initialized
- `product:migrate` if existing artifact folders should be mapped first
- `product:status` if healthy
