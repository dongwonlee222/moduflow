# Review: Runtime Provenance and Validation Mode Separation

Issue: `111-runtime-provenance-and-validation-mode-separation` · Owner / reviewer: Dongwon Lee
Phase: review complete 2026-09-04. Implementation shipped in 0.3.56; the remaining real-host observations were recorded during the 0.3.62 release.
Source: [spec](spec.md), [plan](plan.md), [status](status.md), [simulation matrix](simulation-matrix.md), [release](release.md).

## What This Issue Set Out To Fix

Nothing could answer "which ModuFlow is actually running". Source, installed package and target project were treated as one thing, so validation applied the wrong standard to each — a correct installation could be checked against source-repository rules and reported as broken — and status could not say which package was live.

## Was It Fixed

Yes, and it was exercised under real conditions on 2026-09-04 rather than only in fixtures.

| Requirement | Evidence |
| --- | --- |
| Three validation roles are distinct | `validate_moduflow.py --mode installed` returned `validation_role: installed` and passed 199 files on the published package, while `--mode source` passed 218 on the repository. Doctor took the project, not the cache |
| Status identifies the loaded runtime | Codex reported `0.3.62+codex.20260904022744` after restart |
| Provenance is recorded, not inferred | The receipt carried `payload_sha256` `f628b458…96ffbe`, `source_commit` `faa5ff3` and `source_dirty: true`. The dirty flag was surfaced unprompted in the Codex Doctor report |
| Source version equality never proves host reload | Demonstrated directly. Every path on disk resolved to 0.3.62 while a newly opened Codex task still reported 0.3.57 |
| Unobserved fields stay unobserved | Codex MCP process startup and direct host-exposed prompt-skill package evidence are recorded as not observed, not inferred from a matching version string |

## The Decisive Observation

The negative result carries this issue's whole argument. A new task inside a running Codex process reported the previous version while the filesystem was already fully switched. Without this issue's separation, the obvious reading would have been "the installation failed, reinstall it" — which would have republished over a correct package. Because source, package and host were separable, the diagnosis was immediate and narrow: the disk is right and the process is stale.

`docs/release-checklist.md` step 7 was corrected as a direct result, from "start a new Codex task" to "restart the Codex process", with the observation recorded as its reason.

## Independent Package Check

Both packages were launched outside any host and probed over stdio. `0.3.62` and `0.3.57` each completed `initialize`, returned their own version, listed five tools and exited cleanly with empty stderr. The Claude session's `CONNECTION_CLOSED` is therefore a host startup failure, not a package defect. One lead is recorded without being claimed: `.mcp.json` interpolates `${CLAUDE_PLUGIN_ROOT}` and both manifests reference that same file; whether Codex populates that variable was not tested.

## Findings Carried Forward

| Finding | Disposition |
| --- | --- |
| Two plugin manifests could drift; `version_bump.py` updated only one and nothing compared them | Fixed during this release. `release_check.py` gained `manifest_version_parity`, verified to catch the exact 0.3.61/0.3.57 mismatch that was found by eye |
| Codex MCP process startup remains unobserved | Left open. It needs a host that states its invocation path; no field available today supplies it |
| A stale 111 branch reference lingers in execution state | Reported by Doctor as an optional warning, not an error. Not addressed here |

## Scope Discipline

No second validation path, no re-publication, no overwriting of a valid installed receipt to fill missing Git provenance, and no host configuration inferred as passing. The unavailable fields stayed unavailable.

## Decision

Accepted. The contract is implemented, shipped, and confirmed on a real host with its limits recorded. The two unobserved fields are documented as unobserved rather than assumed, which is what this issue required of itself.

## Next Command

`product:status`; the remaining implementation order is 086 then 092.
