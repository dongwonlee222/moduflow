# Spec Kit Selective Validation Pilot Report

Issue: `098-speckit-selective-validation-adapter`
Evidence type: deterministic offline evidence from the real router and adapter; no live model or Spec Kit CLI execution.
Synthetic fixture latency: `0 ms`; it is not presented as live performance.
Human decision: pending
Wider/default activation: prohibited

## Outcome

- Pilot passed: `yes`
- Cases: `24/24` passed
- Canonical English/Korean successes: `8`
- Availability fallbacks: `4`
- Conservative grammar fallbacks: `12`

## Aggregate Metrics

| Metric | Value |
| --- | ---: |
| Actionable unique findings | 8 |
| Elapsed time (ms) | 0 |
| Loaded context (characters) | 512940 |
| Estimated loaded context (tokens) | 128235 |
| False-positive rate | 0.1429 |
| Native-overlap rate | 0.2857 |
| Ownership escapes | 0 |
| Unauthorized writes | 0 |
| Template fan-out violations | 0 |
| False execution claims | 0 |

## Per-Function Evidence

| Function | Findings | Unique | Elapsed ms | Chars | Tokens | False positive | Native overlap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| analyze | 4 | 2 | 0 | 162396 | 40599 | 0.0000 | 0.5000 |
| checklist | 4 | 2 | 0 | 94790 | 23698 | 0.5000 | 0.0000 |
| clarify | 2 | 2 | 0 | 91326 | 22832 | 0.0000 | 0.0000 |
| converge | 4 | 2 | 0 | 164428 | 41107 | 0.0000 | 0.5000 |

## Case Evidence

| Case | Class | Function / boundary | Passed |
| --- | --- | --- | --- |
| disabled-analyze | disabled | analyze | yes |
| disabled-clarify | disabled | clarify | yes |
| grammar-git | grammar | git | yes |
| grammar-implementation | grammar | implementation | yes |
| grammar-korean-git | grammar | git | yes |
| grammar-korean-mixed | grammar | mixed | yes |
| grammar-lifecycle | grammar | lifecycle | yes |
| grammar-mixed | grammar | mixed | yes |
| grammar-multiple-functions | grammar | multiple-functions | yes |
| grammar-no-prefix | grammar | unknown | yes |
| grammar-punctuation | grammar | punctuation | yes |
| grammar-release | grammar | release | yes |
| grammar-review | grammar | review | yes |
| grammar-unknown-target | grammar | unknown | yes |
| success-analyze-en | success | analyze | yes |
| success-analyze-ko | success | analyze | yes |
| success-checklist-en | success | checklist | yes |
| success-checklist-ko | success | checklist | yes |
| success-clarify-en | success | clarify | yes |
| success-clarify-ko | success | clarify | yes |
| success-converge-en | success | converge | yes |
| success-converge-ko | success | converge | yes |
| unavailable-checklist | unavailable | checklist | yes |
| unavailable-converge | unavailable | converge | yes |

## Decision Boundary

Deterministic checks prove fixture integrity, bounded cost accounting, and zero recorded safety violations.
Reviewer dispositions are committed pilot evidence, but the human value/activation decision remains pending.
The next command is `product:review 098-speckit-selective-validation-adapter`.
