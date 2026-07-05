# Issue: `064-version-bump-policy-and-enforcement`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.

## Outcome

Two corrections to `063-version-bump-on-done`, both raised by an advisory review of that issue:

1. `feat` commits now bump **patch**, not minor (`MINOR_TYPES` emptied, `PATCH_TYPES = {"feat", "fix"}`), matching this repo's own pre-063 history (`0.2.11` → `0.2.15`, all patch bumps) instead of unilaterally switching a 0.x project to a faster minor cadence.
2. `release_check.py` gains a `version_bump_gate` check: if HEAD's commit message classifies to a non-`none` bump level but `.claude-plugin/plugin.json`'s version is unchanged from `HEAD~1`, the check fails — turning the version-bump step from a convention an agent must remember into something the pre-push hook actually blocks on.

## Why

An advisory review of `063` (requested directly: "어드바이스 해서 이 방향 맞는지 추가 체크") found that 063's own fix was built the same fragile way as the problem it was meant to solve: a documented step (`docs/host-adapter-guidance.md`) that only happens if the next agent remembers to read and follow it — nothing failed if it was skipped. Since `release_check.py` already runs as a pre-push hook, it is the one real enforcement point available; adding the gate there closes that gap. The advisor separately flagged that `feat`→minor was a policy change nobody asked for, made unilaterally during 063's implementation.

Note the asymmetry acknowledged during review: this enforcement pattern applies to `063`'s version bump (a file diff a hook can inspect) but not to `061`'s auto-push policy (a hook cannot force a push that never happens) — `061` remains convention-only by necessity, not oversight.

## Scope

### In

- Change `scripts/version_bump.py`'s classification so `feat` and `fix` both map to `patch`; `major` still comes from `!`/`BREAKING CHANGE:` only.
- Add `check_bump_applied(root, runner=None)` to `scripts/version_bump.py`, using the same injectable-runner pattern as `project_sync.py`/`vendor_freshness.py`, comparing only `HEAD` vs `HEAD~1` (matches the documented single-commit bump workflow).
- Wire `check_bump_applied` into `run_release_check` as a new `version_bump_gate` check.
- Run `scripts/register_codex_personal_marketplace.py .` once to clear the live desync between `.claude-plugin/plugin.json` (`0.3.0`) and `.codex-plugin/plugin.json` (still `0.2.15+codex...`) left over from `063`.
- Update existing `tests/test_version_bump.py` classification expectations; add gate tests (not-a-bump-type, bump-and-changed, bump-and-unchanged, insufficient-history, missing-prior-file).

### Out

- No retroactive re-bump of `0.3.0` back to a patch-cadence number — that version already shipped and was pushed; only the *policy going forward* changes.
- No gate for `061`'s auto-push behavior — structurally not hook-enforceable (see Why).
- No multi-commit range scan (checking every commit between `@{u}` and `HEAD`) — out of scope; the documented workflow always bumps in the same commit as the completion commit, so a HEAD-vs-parent check is sufficient for that workflow.

## Acceptance Criteria

- `classify_bump("feat: ...")` returns `patch`.
- `classify_bump("fix: ...")` returns `patch`.
- `classify_bump("feat!: ...")` / `BREAKING CHANGE:` footer still return `major`.
- `check_bump_applied` returns `ok: False` when HEAD is a `feat`/`fix` commit and `.claude-plugin/plugin.json`'s version matches `HEAD~1`'s.
- `check_bump_applied` returns `ok: True` when the version changed, when the commit type is `none`, or when there isn't enough history (`HEAD~1` doesn't exist).
- `.codex-plugin/plugin.json`'s version base matches `.claude-plugin/plugin.json`'s (`0.3.0`).
- `python3 -m unittest tests.test_version_bump -v` passes.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- follows_up: `063-version-bump-on-done`
- related: `010-codex-version-sync-fix` (the sync mechanism run here, not modified)

## Workflow Tasks

- [x] execute → `scripts/version_bump.py`, `scripts/release_check.py`, `tests/test_version_bump.py`

## Sessions

- 2026-07-05: User asked for an advisory check on 063's direction after it shipped. Advisor flagged: (1) 061/063 are convention-only, not enforced — same failure class 063 was meant to fix; (2) `feat`→minor changed the versioning cadence without being asked; (3) `.codex-plugin/plugin.json` was live-desynced against `.claude-plugin/plugin.json` at that moment; (4) 059–063 were six issues of workflow plumbing with no product-goal progress. User decided via clarifying questions: sync the codex manifest now, switch to `feat`→patch, add the release_check enforcement gate, and move to product work next.
- 2026-07-05: Ran `register_codex_personal_marketplace.py .` (fixed the live desync — `0.3.0+codex.20260626145655`). Implemented the policy change and `check_bump_applied` gate via TDD (RED: 3 classification tests + 5 gate tests failing/erroring; GREEN after implementation). Full suite (208 tests) and `release_check.py` pass, including the new gate itself running clean against this session's own HEAD.

## Links

- Roadmap: `workspace/roadmap.md`
- Prior issue: `issues/063-version-bump-on-done.md`

## Next Command

`/product:status`
