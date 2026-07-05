# Upgrade Guide

## Claude Code Plugin

The installed plugin does NOT auto-update when new versions are pushed to the repo. The marketplace clone under `~/.claude/plugins/marketplaces/moduflow` and the install pointer in `installed_plugins.json` both stay frozen until updated explicitly:

```bash
claude plugin marketplace update moduflow
claude plugin update moduflow@moduflow
```

Run both after each release (or whenever `product:status` output looks older than the repo), then restart Claude Code to apply.

## Existing Users

Existing commands remain available:

- `product:start`
- `product:status`
- `product:issue`
- `product:spec`
- `product:plan`
- `product:execute`

New layers are opt-in:

- `product:migrate`
- `product:profile`
- `product:knowledge`
- `product:portfolio`
- `product:handoff`

## Existing Projects

1. Run `product:doctor`.
2. Run `product:migrate` in dry-run mode if the project already has its own structure.
3. Run `product:profile --write` to add project metadata.
4. Run `product:knowledge --write` to add evidence folders.
5. Run `product:handoff --write` to add team workflow artifacts.
6. Run `python3 scripts/validate_project_artifacts.py <project-path>`.

## Codex

After changing the plugin package, refresh the cachebuster and run the local bootstrap installer:

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py .
python3 scripts/register_codex_personal_marketplace.py .
```

The bootstrap installer:

- links the source package to `~/plugins/moduflow`
- updates `~/.agents/plugins/marketplace.json`
- links the package to `~/.codex/plugins/local/moduflow`
- populates `~/.codex/plugins/cache/personal/moduflow/<version>`
- enables `[plugins."moduflow@personal"]` in `~/.codex/config.toml`

The cache copy excludes source-repo planning and verification artifacts: `issues/`, `specs/`,
`tests/`, and `sessions/`. Keep those files in Git as development context, not in the runtime
plugin bundle.

Start a new Codex thread after running it.

## Claude

Use the local plugin source or symlink described in `INSTALL.md`. Reopen the client after changing plugin metadata.
