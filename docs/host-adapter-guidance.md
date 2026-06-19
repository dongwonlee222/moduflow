# Host Adapter Guidance

ModuFlow should keep routine status, doctor, and review flows calm in hosts that ask for approval before shell commands. The plugin should prefer in-process validation for local read-only checks and reserve shell, Git, GitHub, account, and destructive operations for moments where the user clearly needs them.

## Default Order

1. Read local artifacts first: `.moduflow/state.json`, `workspace/loop-state.json`, `workspace/goal.md`, `issues/`, and `specs/`.
2. Use importable validation APIs for routine checks:
   - `validate_project_artifacts.validate_project(root)`
   - `validate_moduflow.validate_moduflow(root)`
   - `project_doctor.inspect_project(root, include_preflight=False)`
   - `release_check.run_release_check(root)` when a full local release gate is requested
3. Show a resume banner when work is resumed after a long task, context compaction, approval pause, or validation loop.
4. Run full Git/GitHub preflight only when sync, branch, PR, release, or account state matters.

## Resume Banner

When a ModuFlow action resumes after an interruption or a long validation sequence, show a short banner before continuing. This tells the user that work is being continued, not restarted.

```text
이어받음: <goal or issue id>
완료됨: <already completed items>
지금: <current action>
다음: <next handoff target>
```

Keep it concise. Do not list every command already run. Prefer durable artifacts and phases over internal execution details.

Example:

```text
이어받음: 027 approval friction
완료됨: spec/plan, importable validation, doctor no-preflight
지금: host adapter guidance 작성
다음: 027 review
```

## When To Use Local-Only Checks

Use local-only checks for:

- `product:status` rendering after completed work
- `product:doctor` health display when GitHub sync is not the question
- `product:review` artifact consistency checks before closing an issue
- resume banners and loop handoffs
- routine "다음" recommendations

Local-only checks must not call:

- `git fetch`, `git pull`, `git push`, `git commit`, or branch mutation
- `gh auth status`, `gh issue`, `gh pr`, or `gh api`
- package publishing commands
- file deletion or history rewrite commands

## When Full Preflight Is Expected

Full preflight is appropriate when:

- the user asks to sync with GitHub
- a PR, release, branch, push, pull, merge, or commit is requested
- branch-to-issue binding must be verified before execution
- the user asks why GitHub state differs from local state
- a release gate must represent CI/CLI behavior exactly

When full preflight is needed, say why before running it.

## Host Adapter Boundary

Host-specific integrations such as Antigravity should live outside core validation logic. The core should expose stable Python functions and CLI wrappers. A host adapter may call those functions directly, or expose them through MCP/tool calls, but it should not force routine read-only checks through repeated shell prompts.

Antigravity-specific APIs are pending verification. Until verified, ModuFlow should document the expected adapter behavior rather than depending on private host details.
