# Issue 121: Constitution Amendment Invalidates Spec Kit Pilot Evidence

**Status: backlog** — created 2026-09-05.
**Priority: p2**

## 요약

헌법을 한 글자만 고쳐도 spec-kit 파일럿 스냅샷 네 개가 통째로 무효가 되고 릴리스 게이트가 막힙니다. 스냅샷에는 사람이 검토한 판단이 들어 있어 기계가 다시 만들 수 없으니, 헌법을 못 고치는 상태가 됩니다.

## Summary

`workspace/constitution.md` is a canonical input to the Spec Kit pilot snapshots, so any constitution amendment changes their `input_hash` and fails `spec_kit_pilot_provenance`. The snapshots contain reviewed findings and a human decision field, so they cannot simply be regenerated. As it stands, the constitution cannot be amended without either falsifying recorded evidence or re-running a human review.

## Source

- Type: blocked amendment, found while executing the approved C12 amendment
- Owner / decision maker: Dongwon Lee
- Date: 2026-09-05
- Link: `workspace/constitution.md` amendment procedure; `specs/098-speckit-selective-validation-adapter/spec.md:213`

## Opportunity

`spec_kit_adapter.canonical_input_paths()` (`scripts/spec_kit_adapter.py:551`) returns the issue file, the spec directory, **and `workspace/constitution.md`**. `validate_host_result` then rejects a stored snapshot whose `input_hash` no longer matches (`scripts/spec_kit_adapter.py:797`, `input_mismatch`). The four committed snapshots under `tests/fixtures/spec-kit-selective-validation/results/` were produced under constitution v1.0.

Verified on 2026-09-05: amending the constitution fails `spec_kit_pilot_provenance` and `tests`; reverting only `workspace/constitution.md` returns the gate to 14/14 with every other change of that session in place. `spec_kit_pilot.py --write` does not self-heal — it runs the same validation and refuses.

The gate is not wrong. It is correctly asserting that a recorded result belongs to the inputs it was produced from. The problem is that nothing resolves the conflict:

- Regenerating the snapshots by hand would rewrite `findings` and `user_decision: "Human decision pending."` — reviewed judgment, not derivable output. That is evidence falsification, not a refresh.
- Re-running the pilot needs a human decision, so a constitution amendment silently acquires a human-review cost nobody documented.
- `docs/release-checklist.md` says nothing about snapshots when the constitution changes. The amendment procedure in the constitution says nothing either.

Nobody hit this before because the constitution has not been amended since v1.0 was ratified on 2026-07-07, and Issue 098 landed after that. The first real amendment attempt found it.

This is itself an instance of the pattern the blocked amendment was written to name: a coupling was built, and no step exists to handle what it produces.

## Scope

### In

- Decide how a constitution amendment and pilot snapshot provenance coexist. At least these are on the table, and the issue must pick one rather than inherit today's behavior:
  - record the constitution version or digest a snapshot was produced under, and treat a newer constitution as *stale evidence to be re-reviewed*, not as an invalid snapshot;
  - narrow the canonical input set so the constitution affects only the functions that actually read it;
  - define an explicit re-review step, with its human cost stated, as part of the amendment procedure.
- Document the chosen path in `docs/release-checklist.md` and in the constitution's amendment procedure, so the next amendment does not rediscover this.
- Land the deferred **C12** amendment once the path exists. Its approved text is preserved below.

### Out

- Rewriting `tests/fixtures/spec-kit-selective-validation/results/*.json` by hand to make the gate green. The `findings` and `user_decision` fields are reviewed evidence.
- Weakening or removing `spec_kit_pilot_provenance`. It caught a real coupling.
- Changing what the Spec Kit adapter does at runtime, or its approved vendor version.
- Any change to the C12 text itself. It was approved as written on 2026-09-05; this issue unblocks it, it does not renegotiate it.

## Acceptance Criteria

- Amending `workspace/constitution.md` no longer fails the release gate through stale snapshot identity alone, by whichever mechanism this issue selects.
- If the selected mechanism requires human re-review, that cost is stated in `docs/release-checklist.md` and in the constitution amendment procedure — an amendment must not acquire a hidden step.
- No snapshot's `findings` or `user_decision` is rewritten by an automated path.
- The C12 amendment is applied, `workspace/constitution.md` and `workspace/constitution.ko.md` move to v2.0, and the amendment log records Dongwon Lee's 2026-09-05 approval with the original approval date preserved.
- `python3 scripts/release_check.py .` passes with the amendment in place.

## Verification

- `python3 -m unittest tests.test_spec_kit_pilot tests.test_spec_kit_adapter tests.test_release_check`
- `python3 scripts/spec_kit_pilot.py . --fixtures tests/fixtures/spec-kit-selective-validation/cases.json`
- `python3 scripts/release_check.py .` — with the C12 amendment applied, not without it
- Confirm by `git diff` that no `findings` or `user_decision` value changed

## Entry Points

- `scripts/spec_kit_adapter.py` (`canonical_input_paths`, `read_canonical_inputs`, `canonical_input_hash`, `validate_host_result`)
- `scripts/spec_kit_pilot.py`
- `tests/fixtures/spec-kit-selective-validation/`
- `workspace/constitution.md` (amendment procedure)
- `docs/release-checklist.md`

## Deferred Amendment Text (approved 2026-09-05, not yet applied)

Preserved verbatim so the approval is not lost while this issue is open. English principle, to be inserted after C11:

> **C12 · SHOULD — An empty slot names who fills it.** When an artifact can display a "missing / unwritten / unverified" state, its spec names *who, when, and in the course of what action* fills it. If no filling path exists in a template or a command step, the indicator is decoration; acceptance criteria test that **the path exists**, not that the indicator renders. *Rationale: 057 designed three sound read paths for the Korean issue overview, but no issue template carried a Korean section, so the automatic paths could never fire; the manual JSON fallback became the only path a new issue could take and stopped at issue 087, leaving 32 issues with no Korean description and 55 more reachable only through that map. Three instances of the same shape landed on 2026-09-05 — 112's parallel-eligibility verdict nothing read, 086's `[deferred]` marker the parser did not know, and 057's `한글 없음` flag with no step behind it.* Origin: 2026-09-05 observation of three recurrences.

Korean sidecar text, to be inserted after C11 in `constitution.ko.md`:

> **C12 · SHOULD — 빈칸에는 채우는 주체가 있어야 한다.** 어떤 산출물이 "없음/미작성/미검증" 상태를 표시할 수 있다면, 그 명세는 *누가 · 언제 · 무엇을 하다가* 그것을 채우는지 명시한다. 템플릿이나 명령 단계에 채우는 경로가 없으면 그 표시는 장식이며, 수용기준은 표시가 뜨는 것이 아니라 **경로가 존재함**을 검사한다. *근거: 057은 한글 개요를 세 경로로 읽도록 제대로 설계했지만 이슈 템플릿에 한글 절이 없어 자동 경로가 발동할 수 없었고, 수동 JSON 폴백이 새 이슈가 탈 수 있는 유일한 경로가 되어 이슈 087에서 끊긴 채 32건이 한글 설명 없이, 55건이 그 파일에만 의존해 남았다. 같은 유형이 2026-09-05 하루에 셋 나왔다 — 112의 병렬 판정을 아무도 읽지 않았고, 086의 `[deferred]` 표시를 파서가 몰랐으며, 057의 `한글 없음` 플래그 뒤에는 아무 단계도 없었다.* 출처: 2026-09-05 세 건 관찰.

Amendment log row (both files; version moves v1.0 → v2.0):

> `| 2026-09-05 | v2.0 | C12 added — an empty slot names who fills it (SHOULD; reporting only, never a gate, so C9's fall-back posture is unchanged) | Claude (agent) | Dongwon Lee (2026-09-05: "ㅇㅇ 그러자고") |`

## Scope Fence

Do not edit `findings` or `user_decision` in any snapshot. Do not delete or weaken the provenance gate. Do not alter the C12 wording above — it is approved text awaiting application.

## Workflow Tasks

- [ ] spec → `specs/121-constitution-amendment-invalidates-pilot-evidence/spec.md` (+ `spec.ko.md`)
- [ ] plan → `specs/121-constitution-amendment-invalidates-pilot-evidence/plan.md` + `tasks.md`
- [ ] execute → chosen mechanism, docs, and the C12 amendment
- [ ] review → `specs/121-constitution-amendment-invalidates-pilot-evidence/review.md`

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `098-speckit-selective-validation-adapter`
- supersedes:
- related: `057-korean-human-review-packet`, `119-dashboard-attention-first-and-one-command-open`, `120-silent-status-fallback-in-issue-parser`

## Sessions

- 2026-09-05: found while applying the approved C12 amendment. Everything else from that session is green at 14/14; only the amendment is held back. The C12 text is preserved above so the approval survives the deferral.

## Links

- Constitution: `workspace/constitution.md`
- Adapter spec: `specs/098-speckit-selective-validation-adapter/spec.md`
- Release checklist: `docs/release-checklist.md`

## Next Command

`product:spec 121-constitution-amendment-invalidates-pilot-evidence`
