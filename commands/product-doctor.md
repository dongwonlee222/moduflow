---
description: Validate ModuFlow installation and project artifacts.
argument-hint: "[project path]"
---

# /product:doctor

Validate setup.

## Do

1. Run `scripts/validate_moduflow.py <package-path> --mode installed --json` for an installed plugin, or `--mode source --json` for the source checkout. Select the role explicitly; source release gates must never fall back to installed mode. This package path is separate from the project path below.
2. Run `scripts/project_doctor.py <project-path>` for the target project.
3. Run `scripts/validate_project_artifacts.py <project-path>` when the project is initialized.
4. Separate required setup errors from optional capability warnings.
5. Check Git repo, canonical repository identity, actual fetch/push URLs, configured base ref, GitHub provider evidence, GitHub CLI auth, and required `.moduflow`, `issues`, `specs`, and `workspace` files.
6. Detect likely existing project artifact folders for migration.
7. Preserve raw `mode` in JSON diagnostics, but render `mode_guidance.message` and `mode_guidance.details` before any raw mode labels in user-facing output.
8. Report missing files and suggested fix commands.
9. Render the versioned `repository_identity` result as expected identity, observed identity, lifecycle, capabilities, reason codes, and exact remediation. Doctor is report-only even on mismatch.
10. For approval-sensitive hosts, call `inspect_project(path, include_preflight=False)` or `scripts/project_doctor.py <project-path> --no-preflight` first, then run full preflight only when Git/GitHub sync state is needed. The result explicitly lists `repository_identity` as skipped.
11. Render project operation policy independently from resolution: raw `policy_inputs`, normalized `project_status` / `policy_trust_scope`, all four `capabilities`, and each `capability_reasons` entry. Doctor remains a diagnostic read even when mutation is denied.
12. Render `recovery` as `healthy`, `incomplete`, or `unsafe`. Doctor reads journal control metadata only; it never performs recovery.
13. Render `runtime_provenance` separately from project health and installed inventory. Unknown fields remain null with reasons; process startup is not proof of AI-host skill loading. For `TARGET_ROLE_MISMATCH` or `TARGET_ROLE_AMBIGUOUS`, use the recommended package check instead of initializing/repairing the cache as a project. Diagnostics never install, update or reload.

## Korean Output

Render a Korean-first health check:

```text
╭─ 🩺 ModuFlow Doctor ───────────────────────╮
│ 프로젝트  <project name>                    │
│ 상태      <emoji> <healthy|warning|error>   │
│ 모드      <git-files|github-sync>           │
│ 설정      <mode_guidance.message>           │
╰────────────────────────────────────────────╯

<mode_guidance.details>

✅ 필수 체크
  Git repo: OK
  Canonical repo: github.com/owner/repository
  Fetch / push: 일치
  Base branch: main
  .moduflow: OK
  issues/: OK
  workspace/: OK

⚠️ 선택 체크
  GitHub origin: 없음 (GitHub sync 필요 시 설정)
  profile: 없음 (필요 시 product:profile)
  memory: 없음 (필요 시 product:memory)
  knowledge: 없음 (필요 시 product:knowledge)
  workflow: 없음 (필요 시 product:handoff)

➡️ 추천
  product:status
```

Missing optional capabilities are warnings, not failures, in `git-files` mode.

An archived, read-only, or unknown-policy project may still be inspected. Do not describe `status: resolved` as writable; use `capabilities.write`, `capabilities.execute`, and `capabilities.publish`. If a repair requires mutation, show the policy reason and recommendation rather than attempting the repair.

## Git Checks

- Git repo exists
- Git root is reported as observed evidence
- configured canonical repository matches every fetch/push URL used by the operation
- configured base branch exists; the current feature branch may differ
- remote names such as `origin` are hints and never identity evidence by themselves
- lifecycle is one of `active`, `read_only`, or `archived`
- `gh auth status` passes when issue/PR/release sync is expected
- explicit canonical GitHub `nameWithOwner`, default branch, archive state, and fork state are reported when provider evidence is available

Git and GitHub CLI checks are preflight checks. They are skipped in local-only mode so routine doctor/status rendering can avoid approval popups.

## Transaction Recovery

- `healthy`: no valid incomplete transaction journal is present; emit no recovery action.
- `incomplete`: show each exact transaction ID, journal phase, affected logical role/path, and expected/proposed hash. Show the shell-safe `python3 scripts/project_lifecycle.py <project-root> --recover <transaction-id>` command, but do not run it.
- `unsafe`: discovery or strict control-journal parsing failed. Fail closed, show the stable error code, and do not guess a transaction ID or recovery command.

Doctor never acquires a lifecycle lock, reads preimage or staged payload bodies, changes a journal, or removes a recovery workspace. Archived/read-only projects remain diagnosable because inspection requires only `read`; the separately invoked recovery command remains subject to the project `write` gate.

## Next

- `product:start` if project is not initialized
- `product:migrate` if existing artifact folders should be mapped first
- `product:status` if healthy
- Review and explicitly run the reported `project_lifecycle.py --recover` command if recovery is incomplete

## Hook Health (issue 072)

Doctor surfaces recent entries from `.moduflow/logs/hooks.log` (last 7 days, 20 max) as warnings — hook failures are fail-open at runtime, so this log is the only place they become visible. An absent or empty log is silence, not an error. Recurring entries suggest a broken hook script or an environment problem; hook state files live under `.moduflow/state/` and are machine-local (gitignored).
