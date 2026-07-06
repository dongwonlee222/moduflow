# Plan: Lifecycle Hooks Automation (072)

Issue: `072-lifecycle-hooks-automation`
Spec: `specs/072-lifecycle-hooks-automation/spec.md`
Prev: spec · Next: `product:execute 072-lifecycle-hooks-automation`

## Global Constraints

Binding on every task:

1. **Thin triggers only**: hooks import/invoke `project_lifecycle.py` (sync) and `linkage_check.py` (resolution); they never reimplement sync or linkage logic.
2. **Fail-open, always**: every hook script path exits 0; every exception is caught and appended to `.moduflow/logs/hooks.log`; a 5-second self-enforced budget (start-time check, bail with a log line) — no hook may block or visibly slow the session.
3. **No gating**: the linkage warning is one informational line, deduped by fingerprint; hooks never deny, fail, or gate anything.
4. **Schema before code**: no hook code is written until the manifest schema (event names, matcher syntax, script invocation contract, context-injection channel) is verified against current official Claude Code plugin docs and superpowers' shipped hooks. V1 produces `specs/072-lifecycle-hooks-automation/hook-schema-notes.md`; A-stream tasks cite it.
5. **Project-path resolution from the working directory** — hooks run from the installed plugin cache; they must resolve the *user project's* `.moduflow/`, never the plugin's own repo (026/065 boundary).
6. **Banner budget**: ≤10 lines; if a data source is slow (e.g. retention count), drop it from the banner rather than exceed ~1s typical.
7. **Write surface**: hooks write only `.moduflow/logs/hooks.log`, the sync marker `.moduflow/state/.last-sync`, the warning fingerprint `.moduflow/state/.linkage-warned`, plus whatever `project_lifecycle.py --sync` itself writes. Nothing else.
8. **`hooks/` is a behavior path**: extend `linkage_check.classify_changed_paths` behavior prefixes with `hooks/` (+ test) — the new surface must be covered by the 075 gate from day one. (This is 072's one sanctioned edit to linkage_check: a data-list addition, not logic.)
9. Coordination hygiene: a parallel session (028 chip) is editing `scripts/validate_project_artifacts.py` — 072 tasks must not touch that file, and commits use targeted `git add` (never `-A`).

## Interfaces

- **hooks.log line**: `<iso-ts> <hook> <level:warn|error> <message>` — consumed by B1 doctor tail.
- **Sync marker** `.moduflow/state/.last-sync`: single line, SHA-256 over the sorted `(path, mtime, size)` list of `issues/*.md` at last successful sync — A2 change detection compares current hash to it.
- **Warning fingerprint** `.moduflow/state/.linkage-warned`: SHA-256 of the sorted unlinked behavior-path set last warned about; identical set → no re-warn; changed set (grew/shrank/resolved) → warn anew and update.
- **Banner contract** (session_start stdout, consumed by the hook context channel): ≤10 lines Korean-first: goal, active issue + phase, next command, blocker (if any), unpromoted-record count (if fast).

## Work Streams

### Stream V — verification (first, blocks A)

- **V1. Hook schema verification** — read current Claude Code plugin-hooks docs (claude-code-guide agent or docs fetch) AND superpowers' shipped `hooks/` as reference implementation. Record in `hook-schema-notes.md`: exact hooks.json shape for a plugin, SessionStart matcher values (`startup|clear|compact`), Stop event name + payload (stdin JSON shape), how a SessionStart hook injects context (stdout? specific JSON field?), timeout/exit-code semantics, and the plugin-cache CWD behavior (GC5). Cite doc URLs.

### Stream A — hook implementation (after V1; A1 ∥ A2, disjoint files)

- **A1. Manifest + SessionStart** — `hooks/hooks.json` (both hooks declared per V1 schema) + `hooks/session_start.py` (banner per Interfaces; corrupt/missing state → silent + log). Tests: banner content from fixture state files, missing files → empty output + log entry, exit 0 on all paths.
- **A2. Stop hook** — `hooks/on_stop.py`: ① issues-changed detection via sync marker → invoke `project_lifecycle.py --sync` (subprocess, cwd = resolved project) → update marker on success; ② linkage quick-check: `git status --porcelain` + current branch/trailer via `linkage_check`; unlinked behavior paths → one warning line + fingerprint update per Interfaces. Tests: marker roundtrip, sync triggered/skipped correctly, warning emitted/deduped/re-warned-on-change, git failure → log + exit 0, timeout bail path.

### Stream B — doctor + gate coverage (parallel with A after V1)

- **B1. Doctor log surfacing** — locate doctor implementation (`scripts/project_doctor.py` / `product-doctor.md`), add hooks.log tail (last 7 days or 20 lines) as warnings; absent/empty log → silence. Tests.
- **B2. Gate coverage for `hooks/`** — add `hooks/` to `linkage_check` behavior prefixes + test (GC8). One-line data change; separate task so its diff stays reviewable alone.

### Stream D — dogfood + docs (after A)

- **D1. Dogfood + docs** — direct-invocation dogfood on this repo: mutate a fixture issue Status → run `on_stop.py` → assert state propagated; run `session_start.py` → banner matches current state. Update `commands/product-doctor.md` (hook health note) and `commands/product-status.md` (sessions now open with the banner — status stays the detailed view). Verify installed-plugin path resolution reasoning documented.

## Parallelism & Merge Order

V1 → (A1 ∥ A2 ∥ B1 ∥ B2) → D1. File ownership: `hooks/hooks.json`+`session_start.py` → A1; `on_stop.py` → A2; doctor script/doc → B1; `scripts/linkage_check.py` (data list only) + its test file → B2; D1 touches command docs only. No shared files across parallel tasks (A1/A2 both create under `hooks/` but different files; hooks.json is A1's).

## Gates

- **Test**: full `unittest discover` green; every hook path has an exit-0 test.
- **Self-application**: after A2 lands, the Stop-hook script run against this very repo must correctly stay silent (branch `codex/072-*` links everything) — and a deliberate unlinked scratch edit must produce exactly one warning.
- **Review**: `product:review 072` (converge auto-run included per 071).
- **Deploy**: version bump in completion commit; `release_check` green (linkage gate covers `hooks/` per B2 — the new surface gates itself).
- **Rollback**: revert merge commit; hooks are additive files + one data-list line in linkage_check; removing `hooks/` restores pre-072 behavior entirely.

## Non-Goals Reminder

No daemon, no auto-commit, no blocking, no Codex hooks, no sync/linkage reimplementation — see spec.
