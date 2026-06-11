---
description: Validate ModuFlow installation and project artifacts.
argument-hint: "[project path]"
---

# /product:doctor

Validate setup.

## Do

1. Run `scripts/validate_moduflow.py` for the plugin package.
2. Run `scripts/project_doctor.py <project-path>` for the target project.
3. Check Git repo, GitHub remote, GitHub CLI auth, and required `.moduflow`, `issues`, `specs`, and `workspace` files.
4. Detect likely existing project artifact folders for migration.
5. Report missing files and suggested fix commands.

## Git Checks

- Git repo exists
- Git root matches intended project root
- `origin` remote exists when GitHub sync is expected
- `gh auth status` passes when issue/PR/release sync is expected

## Next

- `product:start` if project is not initialized
- `product:migrate` if existing artifact folders should be mapped first
- `product:status` if healthy
