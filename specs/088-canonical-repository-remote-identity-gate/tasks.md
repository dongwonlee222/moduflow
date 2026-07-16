# Tasks: Canonical Repository/Remote Identity Gate (088)

Issue: `088-canonical-repository-remote-identity-gate`
Plan: `specs/088-canonical-repository-remote-identity-gate/plan.md`

## Stream A — Identity Core

- [x] A1 — Add failing canonical config and URL normalization tests.
- [x] A2 — Implement the single `git.identity` parser and credential-safe URL normalizer.
- [x] A3 — Add failing Git/provider inspection and operation-policy tests.
- [x] A4 — Implement versioned evidence, reason codes, capabilities, and operation decisions.

## Stream B — Profile And Migration

- [x] B1 — Add explicit profile proposal/write tests that preserve unrelated content.
- [x] B2 — Implement remote/local-only canonical identity proposal and write behavior.
- [x] B3 — Dogfood ModuFlow canonical identity in config/profile and update the template.

## Stream C — Read Surfaces

- [x] C1 — Add doctor/status report-only identity tests.
- [x] C2 — Integrate the shared identity result into doctor and repo-sync/status output.
- [x] C3 — Update profile/doctor/status/sync command guidance.

## Stream D — Local Write Gates

- [x] D1 — Add execute/commit/push first-write-boundary tests.
- [x] D2 — Gate execute before artifact mutation and commit before Git probe/staging.
- [x] D3 — Gate push handoff with fresh fetch/push/base/lifecycle evidence.

## Stream E — GitHub Write Gates

- [x] E1 — Add GitHub issue/PR/release explicit-repository tests.
- [x] E2 — Replace implicit `origin` parsing with canonical `owner/repo` decisions.
- [x] E3 — Block stale URL, provider/default-branch/archive/fork contradictions before writes.
- [x] E4 — Update PR/release command guidance.

## Stream F — Artifact Link Audit

- [x] F1 — Add canonical/mirror/reference/mismatch link tests.
- [x] F2 — Implement the shared repository-bearing link classifier.
- [x] F3 — Integrate warning/error policy into project artifact validation.

## Stream G — Verification And Handoff

- [x] G1 — Run focused identity/profile/consumer tests.
- [x] G2 — Run complete unittest discovery and ModuFlow validators.
- [x] G3 — Dogfood doctor, execute decision, and push/provider decision on ModuFlow.
- [x] G4 — Record status/review/converge evidence and route to `product:pr 088-canonical-repository-remote-identity-gate`.

## Acceptance Coverage

- AC1–AC2 configuration/profile persistence → B1–B3
- AC3–AC4 URL normalization and credential safety → A1–A2
- AC5 inspector schema/evidence → A3–A4
- AC6–AC8 wrong/missing identity and write blocks → A3–A4, C1–C2, D1–D3
- AC9–AC10 lifecycle/local-only policy → A3–A4, B1–B2
- AC11–AC12 GitHub/base/feature-branch behavior → A3–A4, E1–E3
- AC13 single parser → A2, A4, C2, D2–D3, E2, F2–F3
- AC14 focused injected-runner tests → A1, A3, C1, D1, E1, F1
- AC15 full validation → G1–G2
- AC16–AC17 artifact-link audit and explicit GitHub writes → E1–E3, F1–F3

## Next

`product:pr 088-canonical-repository-remote-identity-gate`
