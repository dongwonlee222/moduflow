---
description: Create or inspect project profile metadata and canonical repository identity.
argument-hint: "[project path] [--write] [--canonical-repository <host/owner/repo> | --local-only]"
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
6. For a remote-backed project, inspect the proposal first and then explicitly record the canonical identity:

```bash
python3 scripts/project_profile.py <project-path> \
  --canonical-repository github.com/OWNER/REPOSITORY \
  --provider github \
  --remote-name-hint origin \
  --base-branch main \
  --lifecycle active
```

Add `--write` only after the project owner confirms the canonical repository. An existing `git.remote` is shown as a candidate but is never adopted automatically.

7. For an intentional local-only project, confirm the local policy explicitly:

```bash
python3 scripts/project_profile.py <project-path> \
  --local-only \
  --provider generic \
  --base-branch main \
  --lifecycle active \
  --write
```

8. `active`, `read_only`, and `archived` are policy states. Changing them requires explicit human direction; ModuFlow does not unarchive repositories or mutate remotes.

## Sensitive Data Rules

- Store links, labels, and secret manager references only.
- Do not store credentials, API keys, private keys, signed originals, seals, identity documents, or direct personal contact/payment identifiers.
- Use environment variable names instead of secret values.

## Next

- `/product:status` after profile creation
- `/product:portfolio` when portfolio support is available
