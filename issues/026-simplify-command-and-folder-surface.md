# Issue 026: Simplify Command And Folder Surface

## Summary

Make ModuFlow easier to understand by reducing the visible command/folder surface and introducing a small default mental model for users who do not need the full internal workflow map.

## Source

- Type: user feedback
- Link: conversation, 2026-06-19
- Date: 2026-06-19

## Lifecycle

- Phase: complete
- Created: 2026-06-19
- Started:
- Target End:
- Completed: 2026-06-19
- Last Updated: 2026-06-19

## Opportunity

The repo currently exposes 18 non-hidden top-level folders: `adapters`, `assets`, `commands`, `dashboard`, `docs`, `issues`, `knowledge`, `overlays`, `portfolio`, `scripts`, `skills`, `specs`, `templates`, `tests`, `vendor`, `workers`, `workflow`, and `workspace`. This separation helps maintainability, but it overwhelms users who only want to know "what is active, what changed, and what should I do next?"

The same applies to project layout modes. `lightweight`, `dogfooding`, and `heavy` are useful internal diagnostic labels, but users should not need to learn or choose among three modes during normal use.

## Scope

### In

- Define a compact user-facing folder explanation.
- Reduce or group the visible top-level folder surface where possible.
- Hide or de-emphasize internal command complexity behind `/moduflow`, `status`, `next`, `issue`, and `done`.
- Add a "why these folders exist" reference for the tool repo and a shorter target-project reference for light mode.
- Group commands by job-to-be-done instead of exposing the full list first.
- Update status output to separate "user workspace" from "internal ModuFlow tooling".
- Treat `lightweight/dogfooding/heavy` as internal diagnostic states and translate them into simple user-facing guidance.

### Out

- Removing advanced direct commands.
- Flattening the internal repo architecture without a separate technical design.
- Replacing Git artifacts with a database or hosted service.

## Acceptance Criteria

- README and status surfaces present a small default command set before the full advanced list.
- Users can see which folders are safe project artifacts and which folders are internal tooling.
- The 18-folder top-level surface has a documented grouping or reduction plan.
- `product:status` or `/moduflow` can explain the current mode without dumping implementation detail.
- Normal users do not have to understand the three project modes; the UI says what matters, such as "project setup is clean", "this is the ModuFlow tool repo", or "tool folders are present and cleanup is recommended".
- Completed ModuFlow actions always use goal/loop state to tell the user what the next recommended action is, why it is next, the concrete next steps, and the follow-on priority when useful.
- Folder/command docs make the dogfooding repo feel intentional rather than accidental clutter.

## Workflow Tasks

Every artifact-producing step is a tracked task here - never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec -> `specs/026-simplify-command-and-folder-surface/spec.md`
- [x] plan -> `specs/026-simplify-command-and-folder-surface/plan.md`
- [x] benchmark -> `specs/026-simplify-command-and-folder-surface/benchmark.md`
- [x] execute -> PR / commits
- [x] review -> `specs/026-simplify-command-and-folder-surface/review.md`
- [x] revise README command/folder sections
- [x] propose folder grouping/reduction from the current 18 top-level folders
- [x] exclude source planning and verification artifacts from Codex plugin cache bundles
- [x] create only minimal PM folder structure in target projects, not tool/runtime folders
- [x] update status/moduflow command copy
- [x] replace raw mode labels in user-facing output with plain guidance while keeping raw labels in JSON/debug output
- [x] require completed actions to include next recommended action and command
- [x] add tests or fixtures for lightweight project footprint output

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `009-moduflow-hub-command`, `020-user-facing-simple-loop-ux`
- supersedes:
- related: `025-lightweight-project-adoption`

## Sessions

- 2026-06-19: User asked why there are 18 folders inside the ModuFlow folder and described the current experience as uncomfortable.
- 2026-06-19: User noted that requiring people to understand `lightweight`, `dogfooding`, and `heavy` every time would itself be uncomfortable.
- 2026-06-19: User clarified that ModuFlow should proactively tell the next action after completing work, before the user asks.

## Links

- Spec: `specs/026-simplify-command-and-folder-surface/spec.md`
- Status: `specs/026-simplify-command-and-folder-surface/status.md`
- Review: `specs/026-simplify-command-and-folder-surface/review.md`
- Sessions: `sessions/026-simplify-command-and-folder-surface/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:spec 027-reduce-approval-popup-friction`
