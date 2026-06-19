# Spec: Reduce Approval Popup Friction

## Issue

`027-reduce-approval-popup-friction`

## Source Request

User and Antigravity feedback on 2026-06-19 that repeated approval prompts interrupt normal ModuFlow work, especially routine validation scripts and Git/GitHub operations.

## Owner

Dongwon Lee

## Phase

spec

## Problem

ModuFlow currently runs many useful checks through standalone shell commands such as `project_doctor.py`, `validate_project_artifacts.py`, `validate_moduflow.py`, and `release_check.py`. In hosts that treat shell execution as an approval boundary, even safe read-only validation can repeatedly ask the user to proceed. The same friction appears around Git/GitHub operations such as fetch, push, branch cleanup, and account checks.

The safety model is still correct. The problem is that ModuFlow does not clearly distinguish routine local validation from risky writes, network calls, account changes, and destructive Git operations.

## Goals

- Reduce approval prompts during routine local validation.
- Keep shell scripts available for CLI and CI users.
- Refactor validation logic toward importable Python functions that can be called in-process.
- Define a host/tool-adapter path for environments that can call validation tools without shelling out.
- Document which operations still require explicit approval and why.
- Preserve local-only workflows that do not require GitHub/network prompts.

## Non-Goals

- Bypassing Codex, Antigravity, or host approval safety rules.
- Silently performing `.git` writes, network calls, credential changes, account switching, or destructive cleanup.
- Replacing existing validation scripts in one step.
- Building the real subagent execution backend; that belongs to Issue 028.
- Building the Antigravity artifact sync connector; that belongs to Issue 029.

## Design

### Approval Classes

ModuFlow should classify operations by risk:

- Local read-only validation: should be callable in-process when host capabilities allow it.
- Local file writes: require clear summary and one explicit mutation step.
- `.git` writes: require explicit approval and should be batched when possible.
- Network/GitHub operations: opt-in unless sync is requested.
- Account/credential operations: always explicit and preflighted.
- Destructive cleanup: always explicit and never bundled with unrelated changes.

### Importable Validation Engine

Validation scripts should remain executable, but the core logic should be importable:

- `validate_project_artifacts.validate_project(root)`
- `validate_moduflow.validate_moduflow(root)` or equivalent
- `project_doctor.inspect_project(root)`
- `release_check.run_release_check(root)`

Shell entrypoints become compatibility wrappers around these APIs.

### Host Tool Adapter

Where a host supports direct tool calls, ModuFlow should prefer a tool/MCP-style validation adapter for routine checks. Antigravity-specific APIs must be verified before implementation and kept outside the core validation engine.

## Acceptance Criteria

- The 027 plan maps which common operations trigger approvals today.
- Routine validation has an importable API path and no longer requires shell execution in capable hosts.
- Shell entrypoints still work for CLI and CI.
- Documentation explains which prompts are expected and which are avoidable.
- Local-only mode can complete status/doctor/review checks without GitHub API prompts.
- Risky operations remain explicit and auditable.

## Next Command

`/product:plan 027-reduce-approval-popup-friction`
