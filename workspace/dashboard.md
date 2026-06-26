# ModuFlow Dashboard

## Current Phase

Core goal loop, business document workflow, memory capture workflow, team issue-to-branch workflow, and portfolio team-status dashboard are released locally.

## Active Goal

- `business-document-workflow`: make ModuFlow produce decision-ready business documents, starting with market-entry analysis, while preserving sources, assumptions, calculations, validation, exports, and project memory.

## Active Issue

- None.

## Recently Completed

- `035-team-issue-branch-pr-workflow`: completed PM-friendly team-state helpers, PM team status, PR state binding, completion-memory suggestions, validation drift checks, and command docs; versioned as 0.2.14.
- `036-portfolio-team-dashboard`: portfolio dashboard now reads each project's `workflow/team-state.json` and shows active/review work per project; versioned as 0.2.15.
- `033-business-document-workflow`: added business-document routing, market-entry analysis references, polite Korean writing gate, and a test market-entry artifact package.
- `030-project-memory-layer`: portable project memory prototype added with init/write/search/get, doctor validation, command docs, and a repo-local decision memory entry.
- `032-multi-language-goal-benchmarking-and-core-mcp-server-integration`: completed stdio mcp server bridge, direct tool calling logic, and translation helpers.
- `031-goal-driven-autonomous-benchmarking-and-issue-generation`: completed autonomous benchmarking engine, issue parsing tests, and workflow regression prevention.
- `029-antigravity-artifact-sync-connector`: completed sync connector script, bidirectional task merging, and drift checks.
- `028-real-subagent-execution-backend`: completed host-subagent execution backend adapter for Antigravity integration.
- `027-reduce-approval-popup-friction`: completed approval surface mapping, importable validation paths, local-only doctor mode, host adapter guidance, and resume banner contract.
- `026-simplify-command-and-folder-surface`: completed lightweight project footprint, plugin cache packaging, user-facing mode guidance, and goal-loop completion handoff.
- `025-lightweight-project-adoption`: completed lightweight project footprints, mode guidance, and start/migrate lightweight write behavior.
- `0.2.11-goal-loop`: merged to `main` and pushed to GitHub.

## Queue

- `034-memory-capture-and-sync-workflow`: implementation complete for candidate capture, approval, retrieval explanations, validation, export guidance, and PM-friendly docs; versioned as 0.2.13 and committed.

## Blockers

- None.

## Verification

- ModuFlow plugin version: `0.2.15+codex.20260626145655`.
- `python3 -m unittest tests.test_business_document_workflow -v` passed (3 tests).
- `python3 -m unittest discover -s tests -v` passed (122 tests).
- `python3 scripts/release_check.py .` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.

## Next Command

`product:status`
