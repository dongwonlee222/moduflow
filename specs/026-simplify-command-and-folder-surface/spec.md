# Spec: Simplify Command And Folder Surface

## Issue

`026-simplify-command-and-folder-surface`

## Source Request

User feedback on 2026-06-19 that ModuFlow feels uncomfortable because the repository exposes 18 top-level folders, many workflow commands, and raw project-mode labels that normal users should not need to understand.

## Owner

Dongwon Lee

## Phase

spec

## Problem

ModuFlow's internal architecture is useful for maintaining commands, scripts, templates, skills, workers, and adapters, but that architecture currently leaks into the user experience. A user looking at the ModuFlow folder sees 18 top-level directories and may assume every adopted project will receive that same heavy footprint. The same confusion appears in status output when internal labels such as `lightweight`, `dogfooding`, and `heavy` are shown without clear guidance.

## Goals

- Present a small default mental model: `status`, `next`, `issue`, `done`, and `/moduflow` before advanced commands.
- Explain the 18 source-repo folders as grouped internal tooling, PM artifacts, validation assets, and optional integrations.
- Make target-project guidance clear: normal adopted projects should keep only durable PM artifacts and state, while central tooling stays in the plugin/source repo.
- Translate raw project-mode labels into user-facing guidance while preserving raw labels in JSON and debug output.
- Update docs and status surfaces so users can quickly tell whether a project is clean, tool-heavy, or intentionally the ModuFlow source repo.

## Benchmark Findings

See `specs/026-simplify-command-and-folder-surface/benchmark.md` for the full benchmark notes. The consistent pattern across GitHub Actions, GitHub Apps, ESLint, Prettier, Husky, create-next-app, Terraform, VS Code extensions, and agent/plugin ecosystems is:

- The tool or plugin repository may contain many implementation folders.
- The adopted project receives only a small configuration, policy, state, or generated-artifact contract.
- Runtime code, templates, adapters, validators, examples, and package internals stay central.
- User-facing docs lead with simple tasks and stable public surfaces, while advanced internals are documented separately.

## Non-Goals

- Removing advanced direct `product:*` commands.
- Reorganizing or deleting source-repo folders before a separate technical design.
- Changing the Git-native artifact model.
- Completing Issue 025 start/migrate write-behavior changes.

## Design

### Default Command Surface

User-facing docs and status output should lead with a compact command set:

- `status`: show current work, health, and next action.
- `next`: recommend the next safe workflow step.
- `issue`: capture or inspect durable work items.
- `done`: guarded completion when artifacts and verification are present.
- `/moduflow`: hub entrypoint for users who do not want to pick internal commands.

Advanced `product:*` commands remain documented, but behind an "advanced commands" section.

### Folder Grouping

The 18 source-repo folders should be explained by job:

- User PM artifacts: `issues`, `specs`, `knowledge`, `workspace`, `workflow`.
- Command/runtime tooling: `commands`, `scripts`, `skills`, `templates`, `workers`, `adapters`, `overlays`.
- Product/site assets: `assets`, `dashboard`, `docs`, `portfolio`.
- Validation and dependency material: `tests`, `vendor`.

This grouping should make the dogfooding repo feel intentional, while clearly stating that adopted target projects should not need all of these folders.

### Project Mode Copy

Raw labels stay available for machines:

- JSON output and debug logs may keep `lightweight`, `dogfooding`, and `heavy`.

User-facing output should translate them:

- `lightweight`: "프로젝트 설정이 가볍고 정상입니다."
- `dogfooding`: "모두플로 도구 저장소라 폴더가 많은 것이 정상입니다."
- `heavy`: "프로젝트 안에 도구 폴더가 있어 정리를 권장합니다."

## Acceptance Criteria

- Benchmark findings are captured in the 026 spec folder and used to guide implementation.
- README or equivalent user docs show the compact command set before the advanced command list.
- A folder reference groups the 18 top-level folders and marks which ones are source-repo internals versus target-project artifacts.
- Status/doctor-facing copy no longer requires normal users to learn `lightweight`, `dogfooding`, and `heavy`.
- Raw mode labels remain available in JSON/debug output for automation and tests.
- Validation passes after documentation and status surface updates.

## Next Command

`/product:plan 026-simplify-command-and-folder-surface`
