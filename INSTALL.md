# Install Notes

This directory is the ModuFlow source package.

## Claude

Use this package as a Claude plugin source:

- `.claude-plugin/plugin.json` is the plugin manifest.
- `commands/` contains `/product:*` commands.
- `skills/` contains ModuFlow bridge skills.
- `.mcp.json` is intentionally empty until a concrete MCP server is needed.

For local Claude usage, symlink this source package:

```bash
mkdir -p ~/.claude/plugins/local
ln -sfn /Users/dongwon.lee/workhub/company/shared/context-tools/moduflow ~/.claude/plugins/local/moduflow
```

Keep this source package in Git and treat installed copies/caches as derived.

## Codex

Codex can use the same workflow through companion skills or by copying selected `skills/*` into the Codex skills directory.

Recommended:

1. Keep this package as the canonical source.
2. Install only bridge skills needed by Codex.
3. Keep upstream-specific behavior in `adapters/`.
4. Run `python3 scripts/validate_moduflow.py .` after changes.

The package also includes `.codex-plugin/plugin.json` for Codex-side plugin experiments.

### Show As `@ModuFlow`

Codex plugin UI discovery uses a personal marketplace entry.

Run:

```bash
python3 scripts/register_codex_personal_marketplace.py .
python3 /Users/dongwon.lee/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py .
```

The registration script installs the local package into the personal marketplace, creates the
Codex local link, populates the Codex plugin cache, and enables `moduflow@personal` in
`~/.codex/config.toml`.

Then restart Codex or start a new Codex thread and use `@ModuFlow`.

### Slash Commands

ModuFlow keeps `/product:*` command definitions in `commands/`, but Codex intercepts leading `/` as native slash commands before plugin text is routed. In Codex, use the alias without the leading slash:

```text
@ModuFlow product:start
@ModuFlow product:status
```

Short aliases are supported:

```text
@ModuFlow start
@ModuFlow status
@ModuFlow issue
@ModuFlow 상태
```

## Updates

Update upstreams through `vendor.lock.json` and `vendor/`.

Local ModuFlow customizations should stay in:

- `overlays/`
- `adapters/`
- `commands/`
- `skills/`
