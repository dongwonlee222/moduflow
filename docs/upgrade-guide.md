# Upgrade Guide

## Purpose-First PRs and Work Reports (060 follow-up / 0.3.56)

The bundled `docs/output-format.md` now governs why work is needed, the concrete problem and expected user benefits before implementation/tests. Entry/artifact skills and PR/report/update/status/weekly commands load it from the executing package, not the target project's AGENTS.md.

PR generation copies explicit `Why Needed`, `Problem`, `Expected Benefits` sections (or Korean equivalents) from the issue, then its configured spec per missing field. Legacy artifacts without those sections remain readable; their generated rationale is marked unrecorded until the author fills it from evidence. No existing project files are bulk-migrated, and generated Korean packets preserve source language for faithful author translation.

This source version is release preparation, not proof of publication, installation or host reload. Existing installations need the separately approved upgrade process below. Short status updates remain compact; JSON/MCP schemas are unchanged.

## Validation and Runtime Identity (111)

Source maintenance uses `validate_moduflow.py <source> --mode source --json` and the existing strict release check. An installed distribution uses `--mode installed --json`; target projects use `project_doctor.py <project>`. The compatibility default `auto` reports its inference but is not a replacement for explicit release roles.

The Codex installer stages and validates the package, records an atomic `.moduflow-package.json`, and only then exposes the cache. Identical validated retries preserve the original receipt; differing content/source identity at the same version fails without deleting the old cache. Preparation failure leaves activation untouched. Later registration/link failures are separate activation failures, not a claim that all host configuration rolled back atomically.

Status/Doctor/MCP show `runtime_provenance`: known fields have sources and unknown fields have null/reasons. A persistent MCP keeps its original startup snapshot until restarted. A CLI reports only itself. Neither implies the host's prompt skills reloaded. Legacy hosts/packages without receipts remain explicitly unknown; diagnostics do not install metadata into them. The receipt is local build evidence, not a signed attestation. A Codex build suffix is not an installation timestamp.

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
