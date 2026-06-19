# Plan: Reduce Approval Popup Friction

Goal: Reduce approval fatigue by separating safe in-process validation from operations that genuinely require shell, Git, network, credential, or destructive permissions.

Architecture: Keep existing scripts as CLI wrappers, but expose importable validation functions and document approval classes. Defer host-specific Antigravity integration until its API surface is verified.

Tech Stack: Python standard library, existing validation scripts, Markdown command docs, ModuFlow issue/spec/status artifacts.

## Task 1: Approval Surface Map

- [x] List common ModuFlow commands and scripts that trigger shell, Git, network, credential, or destructive approvals.
- [x] Classify each operation as local read-only, local write, Git write, network/GitHub, account/credential, or destructive.
- [x] Document which prompts are expected and which can be avoided.

## Task 2: Importable Validation API

- [x] Add or normalize importable functions for project artifact validation.
- [x] Add or normalize importable functions for ModuFlow package validation.
- [x] Ensure project doctor and release check use importable functions internally where feasible.
- [x] Keep CLI wrappers backward-compatible.

## Task 3: Host Tool Adapter Guidance

- [x] Define how a host can call validation without shelling out.
- [x] Document Antigravity as a candidate host integration pending API verification.
- [x] Keep host-specific adapters separate from core validation logic.
- [x] Define resume banner behavior for interrupted or resumed ModuFlow work.

## Task 4: Verification

- [x] Add focused tests for importable validation APIs.
- [x] Run focused validation tests.
- [x] Run `python3 scripts/validate_project_artifacts.py .`.
- [x] Run `python3 scripts/validate_moduflow.py .`.
- [x] Run `python3 scripts/release_check.py .`.

## Next Command

`/product:review 027-reduce-approval-popup-friction`
