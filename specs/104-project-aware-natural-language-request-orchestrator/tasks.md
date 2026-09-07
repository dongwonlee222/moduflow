# Tasks: Project-Aware Natural-Language Request Orchestrator

Issue: 104-project-aware-natural-language-request-orchestrator

## Stream A — Contract and resolve

- [x] T01 Define `moduflow.request-routing.v1` and assert every field is present in every status [files: scripts/request_routing.py, tests/test_request_routing.py]
- [x] T02 Stage 1 resolve, with the ambiguous path asking exactly one question and writing nothing [files: scripts/request_routing.py, tests/test_request_routing.py] [depends: T01]
- [x] T03 Assert stage order by mock, and that a stage refuses without its predecessor's fields [files: tests/test_request_routing.py] [depends: T02]

## Stream B — Overlap

- [x] T04 Measure three candidate overlap rules over the live issue corpus and record the counts as evidence [files: specs/104-project-aware-natural-language-request-orchestrator/status.md] [depends: T02]
- [x] T05 Stage 2 overlap, attaching to an existing issue and never writing an issue file [files: scripts/request_routing.py, tests/test_request_routing.py] [depends: T04]

## Stream C — Capability and execution

- [x] T06 Stage 3 capability, carrying the 097 result verbatim and treating `none` as a normal outcome [files: scripts/request_routing.py, tests/test_request_routing.py] [depends: T02]
- [x] T07 Stage 4 execution, consuming 112's result unchanged and stopping on `needs_plan` with `written: []` [files: scripts/request_routing.py, tests/test_request_routing.py] [depends: T06]

## Stream D — Isolation

- [x] T08 Project A/B isolation fixtures in Korean and English, both directions [files: tests/fixtures/request-routing/projects.json, tests/test_request_routing.py] [depends: T05]

## Stream E — Commit and wiring

- [x] T09 Stage 5 commit through the 103 transaction, rolling back on validation failure [files: scripts/request_routing.py, tests/test_request_routing.py] [depends: T07] [shared_state: true]
- [x] T10 Route a bare sentence from the hub, adding no command file [files: commands/moduflow.md, tests/test_request_routing.py] [depends: T09]
- [x] T11 Run the five source scenarios end to end and record the outcomes [files: specs/104-project-aware-natural-language-request-orchestrator/status.md] [depends: T08, T10]

## Required Gates

- [x] `python3 -m unittest discover -s tests` green with the new suite present.
- [x] Stage order asserted by mock, not by outcome.
- [x] `python3 scripts/release_check.py .` valid.
- [x] No new top-level command file.
