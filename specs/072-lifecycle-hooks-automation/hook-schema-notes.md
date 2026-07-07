# Hook Schema Notes (V1, verified 2026-07-06)

Verified against official docs via claude-code-guide agent. Binding for A1/A2.

Sources: [hooks.md](https://code.claude.com/docs/en/hooks.md) · [plugins-reference.md](https://code.claude.com/docs/en/plugins-reference.md) · [plugins.md](https://code.claude.com/docs/en/plugins.md)

## Manifest

- Location: `hooks/hooks.json` at **plugin root** (not inside `.claude-plugin/`). Same JSON format as settings.json hooks.
- Placeholders: `${CLAUDE_PLUGIN_ROOT}` (plugin install dir — quote in shell form), `${CLAUDE_PROJECT_DIR}` (project root Claude Code launched from), `${CLAUDE_PLUGIN_DATA}` (persistent data dir).
- Per-hook `timeout` (seconds) supported; command default 600s — we set explicit small timeouts (30s SessionStart, 15s Stop) with a 5s internal self-budget.

## SessionStart

- Matchers: `startup | resume | clear | compact` — **use all four** (spec said three; `resume` added, sessions resuming also need the banner).
- Stdin: JSON incl. `cwd`, `source`, `session_id`.
- **Context injection contract**: exit 0 + stdout JSON:
  ```json
  {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<banner text>"}, "suppressOutput": true}
  ```
- Never blocks by design; non-zero = logged error, session continues — but we still always exit 0 (silence discipline).

## Stop

- Stdin: JSON incl. `cwd`, `session_id`, `transcript_path`.
- **Exit 2 = BLOCKING (forbidden here). `decision: "block"` = forces continuation (forbidden here).** Non-zero non-2 shows stderr first line to the user — therefore fail-open means **always exit 0**; failures go to hooks.log only.
- Non-blocking informational output (our warning channel):
  ```json
  {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "<one-line linkage warning>"}, "suppressOutput": true}
  ```
  `systemMessage` also available for a user-visible spinner-style note — use `additionalContext` (agent-facing) for the linkage warning; it must inform the agent's next turn.

## Execution environment

- Hook CWD = `${CLAUDE_PROJECT_DIR}` (the user's project) — GC5 satisfied natively; scripts still guard by resolving `.moduflow/` from CWD and exiting silently if absent (hook fires in non-ModuFlow projects too, since plugin hooks are global when enabled).
- Hook stdout must be the JSON contract only — all logging to file, never stdout/stderr.

## PostToolUse (rejected path, for the record)

- Matcher filters tool names only (`Write|Edit`); path filtering needs `if` permission-rule syntax. Fires per tool call — Stop-batching remains the right choice (once per turn).

## Implementation deltas vs spec

1. SessionStart matcher set = `startup|resume|clear|compact` (four, not three).
2. Both hooks: stdout reserved for the JSON contract; `suppressOutput: true`; ALL diagnostics to `.moduflow/logs/hooks.log`; exit 0 unconditionally.
3. Non-ModuFlow-project guard: no `.moduflow/state.json` under CWD → emit nothing, exit 0, no log spam (hooks are global to the plugin, not per-project).
4. Manifest timeouts: SessionStart 30, Stop 15 (defense in depth over the 5s self-budget).
