# Spec Kit Selective Validation Pilot Report

Issue: `098-speckit-selective-validation-adapter`
Evidence type: deterministic offline evidence from the real router and adapter; no live model or Spec Kit CLI execution.
Synthetic fixture latency: `0 ms`; it is not presented as live performance.
Human decision: pending
Wider/default activation: prohibited

## Outcome

- Pilot passed: `yes`
- Cases: `13/13` passed
- Ordinary validation probes: `14/14` passed
- Canonical lifecycle/Git ownership probes: `69/69` passed
- Adjacent lifecycle/Git phrase probes: `19/19` passed
- Metamorphic lifecycle/Git insertion probes: `14/14` passed

## Aggregate Metrics

| Metric | Value |
| --- | ---: |
| Actionable unique findings | 4 |
| Elapsed time (ms) | 0 |
| Loaded context (characters) | 266018 |
| Estimated loaded context (tokens) | 66505 |
| False-positive rate | 0.1429 |
| Native-overlap rate | 0.2857 |
| Boundary violations | 0 |
| Unauthorized writes | 0 |
| Unwanted fan-out | 0 |
| False execution claims | 0 |

## Per-Function Evidence

| Function | Findings | Unique | Elapsed ms | Chars | Tokens | False positive | Native overlap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| analyze | 2 | 1 | 0 | 83644 | 20911 | 0.0000 | 0.5000 |
| checklist | 2 | 1 | 0 | 49723 | 12431 | 0.5000 | 0.0000 |
| clarify | 1 | 1 | 0 | 47991 | 11998 | 0.0000 | 0.0000 |
| converge | 2 | 1 | 0 | 84660 | 21165 | 0.0000 | 0.5000 |

## Case Evidence

| Case | Class | Function / boundary | Passed |
| --- | --- | --- | --- |
| disabled-analyze | disabled | analyze | yes |
| disabled-clarify | disabled | clarify | yes |
| ownership-git | ownership | git | yes |
| ownership-implementation | ownership | implementation | yes |
| ownership-lifecycle | ownership | lifecycle | yes |
| ownership-release | ownership | release | yes |
| ownership-review | ownership | review | yes |
| success-analyze | success | analyze | yes |
| success-checklist | success | checklist | yes |
| success-clarify | success | clarify | yes |
| success-converge | success | converge | yes |
| unavailable-checklist | unavailable | checklist | yes |
| unavailable-converge | unavailable | converge | yes |

## Decision Boundary

Deterministic checks prove fixture integrity, bounded cost accounting, and zero recorded safety violations.
Reviewer dispositions are committed pilot evidence, but the human value/activation decision remains pending.
The next command is `product:review 098-speckit-selective-validation-adapter`.
