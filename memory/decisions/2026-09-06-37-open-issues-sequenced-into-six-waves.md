---
id: 2026-09-06-37-open-issues-sequenced-into-six-waves
kind: decision
title: 37 open issues sequenced into six waves
issue_id: 
spec: 
source_event: 
source_artifacts: []
review_after: 
supersedes: []
superseded_by: []
depends_on: []
references: []
storage_policy: local
mirror_targets: []
owner: Dongwon Lee
date: 2026-09-06
tags: [priority, sequencing, roadmap]
summary: The 37 open issues are ordered into six waves plus a named parked set. Wave 1 readability (131 stage 1, 129+130 merged). Wave 2 the unblocker (112, then 104, then 131 stage 2). Wave 3 canonical state (132 then 133). Wave 4 existing-project onboarding (105 with the newly reported migration defect). Wave 5 the gates that half-run (122, 128, 136, 123, 140). Wave 6 cleanup (124, 138, 137, 139). Sixteen issues are deferred as a stated judgement, not an oversight.
rationale: Ordering is by what is measurably blocking today, not by priority label. 112 is placed second because it alone unblocks four issues (104, 113, 114, 117) and 117 must not precede it. 131 is split at the router boundary because its own Scope Fence forbids building a second router and 104 owns routing; stage 1 (menu policy, ten labels, /moduflow <name> dispatch, five field labels) is router-independent and delivers the reported relief on its own. 129 and 130 are merged because no checker exists yet and running them apart builds the same checker twice. 132 precedes 133 because 132's three defects (superseded unreachable, pause a no-op, phase from file existence) have unambiguous fixes decidable now, whereas 133 needs a prior design decision about where per-person state lives; today's incident produced findings for both, so it does not break the tie. 105 follows 132 because its migration --apply rides the transaction 132 changes. 105 was pulled out of the parked set: it is p0, both its blockers (102, 103) are done, and the owner reported the same defect independently on 2026-09-06.
evidence: Advisor review 2026-09-06 blocked the first ordering on the 131/104 contradiction; issues/131 Scope Fence and Related Issues; issues/105:5 stale Blocked-by against 102 and 103 both done; owner report 2026-09-06: existing projects do not set up correctly when brought into ModuFlow
alternatives: Strict priority order (p0 first) — rejected: it puts 104 before 112 which blocks it. 133 before 132 — rejected: 133 needs a design decision not yet made. 131 whole in wave 1 — rejected: forces the second router its own fence forbids.
reversal_conditions: Re-read waves 5 and 6 after 112 lands: 117 and possibly 128 change shape once needs_plan exists. Re-read wave 4 after the onboarding investigation reports, in case 105 must be split rather than extended. Any wave may be reordered if a p0 regression lands.
confidence: medium
---

# 37 open issues sequenced into six waves

## Summary

The 37 open issues are ordered into six waves plus a named parked set. Wave 1 readability (131 stage 1, 129+130 merged). Wave 2 the unblocker (112, then 104, then 131 stage 2). Wave 3 canonical state (132 then 133). Wave 4 existing-project onboarding (105 with the newly reported migration defect). Wave 5 the gates that half-run (122, 128, 136, 123, 140). Wave 6 cleanup (124, 138, 137, 139). Sixteen issues are deferred as a stated judgement, not an oversight.

## Rationale

Ordering is by what is measurably blocking today, not by priority label. 112 is placed second because it alone unblocks four issues (104, 113, 114, 117) and 117 must not precede it. 131 is split at the router boundary because its own Scope Fence forbids building a second router and 104 owns routing; stage 1 (menu policy, ten labels, /moduflow <name> dispatch, five field labels) is router-independent and delivers the reported relief on its own. 129 and 130 are merged because no checker exists yet and running them apart builds the same checker twice. 132 precedes 133 because 132's three defects (superseded unreachable, pause a no-op, phase from file existence) have unambiguous fixes decidable now, whereas 133 needs a prior design decision about where per-person state lives; today's incident produced findings for both, so it does not break the tie. 105 follows 132 because its migration --apply rides the transaction 132 changes. 105 was pulled out of the parked set: it is p0, both its blockers (102, 103) are done, and the owner reported the same defect independently on 2026-09-06.

## Evidence

Advisor review 2026-09-06 blocked the first ordering on the 131/104 contradiction; issues/131 Scope Fence and Related Issues; issues/105:5 stale Blocked-by against 102 and 103 both done; owner report 2026-09-06: existing projects do not set up correctly when brought into ModuFlow

## Alternatives

Strict priority order (p0 first) — rejected: it puts 104 before 112 which blocks it. 133 before 132 — rejected: 133 needs a design decision not yet made. 131 whole in wave 1 — rejected: forces the second router its own fence forbids.

## Links

- Issue: 
- Spec: 

## Reversal Conditions

Re-read waves 5 and 6 after 112 lands: 117 and possibly 128 change shape once needs_plan exists. Re-read wave 4 after the onboarding investigation reports, in case 105 must be split rather than extended. Any wave may be reordered if a p0 regression lands.
