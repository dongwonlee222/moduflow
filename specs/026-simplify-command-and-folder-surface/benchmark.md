# Benchmark: Lightweight Tool Adoption Patterns

## Summary

The benchmark strongly supports ModuFlow's lightweight adoption direction: source/plugin repositories can be structurally rich, but adopted target projects should keep only the small contract they need to operate, configure, and preserve product-management artifacts.

## Benchmarked Patterns

### GitHub Tooling

- GitHub CLI keeps its implementation in the installed CLI package and does not copy its source tree into every repository that uses `gh`.
- GitHub Actions keeps reusable examples and templates in catalog/source repositories, while target repositories normally add only selected workflow YAML files under `.github/workflows/`.
- GitHub Apps are commonly installed as permissions and behavior, not as source-code copies into every selected repository.
- Probot and create-probot-app show the same split: the framework/generator can be complex, while generated or adopted projects receive a focused app/config surface.

Sources:

- [GitHub CLI repository](https://github.com/cli/cli)
- [GitHub Actions workflows docs](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows)
- [actions/starter-workflows](https://github.com/actions/starter-workflows)
- [Probot repository](https://github.com/probot/probot)
- [create-probot-app](https://github.com/probot/create-probot-app)

### CLI And Developer Tools

- ESLint and Prettier leave thin project-level configuration such as `eslint.config.*`, `.prettierrc*`, or a `prettier` key in `package.json`; the rule engine and plugins remain package-managed.
- Husky writes the small hook policy surface, such as `.husky/pre-commit` and a `prepare` script, instead of copying its implementation into the project.
- create-next-app has a large generator/template source tree, but the generated target project is controlled through scaffold choices and explicit flags such as `--empty`, `--skip-install`, and `--disable-git`.
- Terraform separates user-authored configuration from tool-managed hidden state/cache, and its state behavior shows why generated state must be documented carefully.

Sources:

- [ESLint configuration files](https://eslint.org/docs/latest/use/configure/configuration-files)
- [Prettier configuration](https://prettier.io/docs/configuration)
- [Husky get started](https://typicode.github.io/husky/get-started.html)
- [create-next-app CLI](https://nextjs.org/docs/app/api-reference/cli/create-next-app)
- [Terraform init](https://developer.hashicorp.com/terraform/cli/init)

### Plugin, Agent, And Extension Ecosystems

- Codex/Claude-style skills keep `SKILL.md`, scripts, references, and assets inside a skill/plugin package; projects should only receive the durable project context or artifacts they need.
- VS Code extensions use a manifest and extension source in the extension package; user workspaces receive settings and user data, not the extension implementation.
- Cursor and MCP-style setups use small config pointers such as `.cursor/mcp.json` and environment-variable references rather than copying server implementations or secrets into every project.

Sources:

- [VS Code extension anatomy](https://code.visualstudio.com/api/get-started/extension-anatomy)
- [Claude Code memory and project instructions](https://code.claude.com/docs/en/memory)
- [Cursor docs](https://cursor.com/docs)

## Implications For ModuFlow

- Source repo folders are allowed to be numerous when they are clearly documented as central tooling.
- Target projects should not receive `commands/`, `scripts/`, `skills/`, `templates/`, `workers/`, `adapters/`, `overlays/`, `vendor/`, or runtime assets by default.
- Target projects should keep the durable product-management contract: `.moduflow/`, `issues/`, `specs/`, `knowledge/`, `workspace/`, and `workflow/` where needed.
- If ModuFlow writes runtime/cache/state files, those files need clear commit guidance and `.gitignore` rules where appropriate.
- User-facing status should separate "project footprint" from "ModuFlow internal tooling" before exposing raw diagnostic labels.
- Raw labels like `lightweight`, `dogfooding`, and `heavy` should stay in JSON/debug output, but normal status copy should say what the user needs to do.

## Recommended Rule

Keep this rule as the design anchor for Issue 026:

> Tooling lives in the ModuFlow plugin/source repo; target projects keep only PM artifacts, project state, and intentionally selected integration files.
