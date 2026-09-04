# Issue 111 Simulation and Host-Observation Matrix

Issue: `111-runtime-provenance-and-validation-mode-separation`
Owner: Dongwon Lee
Source: `spec.md`, `plan.md`, user's 2026-09-02 request for simulation testing.
Phase: S01–S12 executed and passed on 2026-09-02. R01 and R02 were performed on 2026-09-04 during the 0.3.62 release and are recorded in [status.md](status.md); Codex MCP process startup and direct host-exposed prompt-skill package evidence remain unobserved.
Next command: `product:review 111-runtime-provenance-and-validation-mode-separation`.

## Offline Scenarios

All versions, projects, homes and timestamps below are synthetic. Use temporary directories, injected runners and fixed clocks. Do not run installation against the real home or fetch external services.

| ID | Setup / stimulus | Expected result | Owning stream |
|---|---|---|---|
| S01 | Complete source checkout; remove one source-only required file in an isolated copy | Source role fails on that missing file; installed mode does not waive source release gates | A |
| S02 | Complete runtime distribution without `.git`, full test tree or development issue/spec tree | Explicit installed validation passes; role and requirement set are reported | A/B |
| S03 | Remove one required runtime script or safety fixture from S02 | Installed check fails with the exact missing asset; manifest presence alone cannot pass | A |
| S04 | Pass a recognized cache, including copied project-looking files, to Doctor/MCP Doctor; instrument parent/registry calls | Target-role error before parent discovery, project resolution, recovery and artifact validators; no repair | C |
| S05 | Empty project, initialized project A/B, and original source dogfooding project | Appropriate project diagnostics; selected project data never leaks across A/B; runtime package identity stays unchanged | C |
| S06 | Legacy package without receipt; no startup/host/session observation | Package version/path known; commit/install/load/host/session unknown with null/reasons; missing metadata warning, not fabricated history | A/C |
| S07 | Invalid JSON/schema/date or manifest/receipt version mismatch | `PROVENANCE_INVALID`; installed self-check fails; status shows evidence error without declaring unrelated project artifacts invalid | A/C |
| S08 | Inject copy, receipt write, receipt replace and final publication failures | Existing usable cache remains byte-identical; incomplete package is not exposed; exact failure returned | B |
| S09 | Repeat identical install, then attempt different payload under same version; include symlink destination | Identical receipt/install timestamp reused; conflict/symlink rejected without overwriting prior package | B |
| S10 | Persistent MCP starts with A; change package files to B, then query old process and start new one | Old process retains A/start timestamp; new process reports B/new timestamp; host skill reload not inferred | C/D |
| S11 | Inventory includes newer B but live snapshot is A; corrupted inventory entry; unrelated project version manifest | Preserve 065 soft stale/recommendation behavior, expose parse diagnostics, never select B as live runtime or use unrelated project version | C |
| S12 | Separate worktree has `.git` file; temporary installed CLI/MCP uses isolated import path; repeated read-only diagnostics with subprocess/network sentinels | Worktree classified as source; packaged imports work; local diagnostics issue no network/subprocess and leave project/receipt bytes unchanged | A/C/D |

The packaged-process smoke itself may launch local test subprocesses with a 10-second timeout. The no-subprocess assertion applies to diagnostic functions inside that process, not to the outer test harness. Set `PYTHONDONTWRITEBYTECODE=1` for read-only smoke. Track generated directory entries as well as file hashes; interpreter caches are not evidence of business-record writes.

## Actual Host Observations — Not Simulations

| ID | When | Observation required | Honest fallback |
|---|---|---|---|
| R01 | After separately authorized installation, in a fresh Codex task | Invoked CLI/MCP package path, version, source evidence and process startup; host-exposed skill package evidence if available | Host skill loading stays unknown when the host supplies no direct evidence |
| R02 | After separately authorized installation, in a fresh Claude task | Same fields, explicitly distinguishing host registration, MCP process and prompt skills | An unavailable host or unobserved field is marked unavailable, not passed |

Observed results and fixture digest are recorded in `status.md`; executable assertions and synthetic inputs are in `tests/test_runtime_provenance_simulation.py` (`test_S01_` through `test_S12_`). Keep implementation, unit tests, simulations, packaged smoke, remote merge, publication, installed package and actual host application separate. The package tested was temporary, not the user's installed plugin.
