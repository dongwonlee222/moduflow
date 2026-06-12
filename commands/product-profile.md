---
description: Create or inspect project profile metadata for ownership, environments, links, and integrations.
argument-hint: "[project path] [--write]"
---

# /product:profile

Create project-level context files that make ModuFlow useful across projects and teams.

## Do

1. Inspect existing `.moduflow/project-profile.md`, `.moduflow/environments.json`, and `.moduflow/integrations.json`.
2. Run dry-run first:

```bash
python3 scripts/project_profile.py <project-path>
```

3. Use `--write` to create missing profile files only:

```bash
python3 scripts/project_profile.py <project-path> --write
```

4. Preserve existing files.
5. Keep secrets and sensitive documents out of Git.

## Sensitive Data Rules

- Store links, labels, and secret manager references only.
- Do not store credentials, API keys, private keys, signed originals, seals, identity documents, or direct personal contact/payment identifiers.
- Use environment variable names instead of secret values.

## Next

- `/product:status` after profile creation
- `/product:portfolio` when portfolio support is available
