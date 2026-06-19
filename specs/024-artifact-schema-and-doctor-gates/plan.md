# Artifact Schema And Doctor Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen ModuFlow validation so active-loop artifact drift blocks release and appears in doctor output.

**Architecture:** Add active-loop schema gates to `scripts/validate_project_artifacts.py` and surface the same result from `scripts/project_doctor.py`. Keep release_check unchanged because it already runs both gates.

**Tech Stack:** Python standard library, Markdown artifacts, JSON loop state, `unittest`.

---

### Task 1: RED Tests

- [x] Add missing linked artifact test.
- [x] Add dashboard active issue drift test.
- [x] Add invalid `next_command` test.
- [x] Add doctor schema gate recommendation test.
- [x] Run `python3 -m unittest tests.test_validation_distribution -v` and confirm RED.

### Task 2: Schema Gates

- [x] Parse active issue linked artifacts from backtick paths.
- [x] Check active dashboard and roadmap references.
- [x] Compare actual next command against inferred issue phase.
- [x] Surface schema gate errors through project doctor.

### Task 3: Release

- [x] Run focused validation tests.
- [x] Run full unit tests.
- [x] Run project artifact validation.
- [x] Run plugin validation.
- [x] Run release check.
- [x] Bump plugin version and register local marketplace cache.
