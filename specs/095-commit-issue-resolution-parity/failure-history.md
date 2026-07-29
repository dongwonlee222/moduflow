# Failure History: 095 Commit-to-Issue Attribution

## Purpose

This is the durable failure corpus for Issue 095. It preserves failed
topologies, invalid assumptions, and the invariants learned from them so future
design and review do not restart from the latest passing test suite.

The detailed chronological narrative remains in `status.md`. This file is the
stable, design-facing index.

## Append-Only Policy

- Record a failure before implementing its fix.
- Never delete or rewrite an entry because a patch passes. Add evidence and
  change its status with a dated note.
- Link every entry to a minimal reproduction, regression test, commit, or
  independent review finding.
- A focused-suite pass may change an entry to `regression captured`; it cannot
  close an entry.
- Closure requires the relevant invariant test, full unittest discovery,
  release check, and independent review to agree.
- Every new Critical or Important attribution finding receives an `FH-*` entry
  before implementation resumes.
- Future attribution specs, plans, and reviews must map each requirement and
  invariant test to one or more `FH-*` ids.

## Entry Schema

Each entry records:

- **Topology**: the smallest Git arrangement that exposes the failure.
- **Observed failure**: what the resolver or a consumer reported incorrectly.
- **Invalid assumption**: the design belief that made the failure possible.
- **Derived invariant**: the rule future implementations must preserve.
- **Evidence**: reproduction, test, review round, or commit.
- **Status**: `open`, `regression captured`, `superseded by redesign`, or
  `closed by verified redesign`.

`superseded by redesign` means an earlier patch exists but is not accepted as
the architectural closure.

## Failure Index

| ID | Failure family | Derived invariant | Status |
| --- | --- | --- | --- |
| FH-001 | Consumers used different ownership rules | All query directions use one attribution result and policy | superseded by redesign |
| FH-002 | Branch containment was treated as authorship | Attribution uses branch contribution, never raw ancestry | regression captured |
| FH-003 | Merged topic minus current main became empty | Historical fork evidence must survive later merges | regression captured |
| FH-004 | Sync-merge direction attributed trunk content to a topic | Merge direction and content sides come from graph structure | regression captured |
| FH-005 | Nested merges leaked inner issue content into the outer issue | Content commits remain single-owner across stacked histories | regression captured |
| FH-006 | A stale local default branch over-collected trunk commits | Base selection compares fork points, not preferred ref tips | regression captured |
| FH-007 | Precedence worked in only one query direction | Apply precedence once after collecting all candidate claims | regression captured |
| FH-008 | Bare and indexed lookup had separate precedence paths | Bare and indexed lookup must project the same attribution result | regression captured |
| FH-009 | Checkout state and unknown branch tails changed the issue registry | Registered issue identity must be historical and fail closed | regression captured |
| FH-010 | Git query failures were flattened into empty attribution | Command failure is distinct from an ordinary negative result | regression captured |
| FH-011 | A disconnected non-issue ref became the repository base | Unrelated refs cannot change a topic's contribution | regression captured |
| FH-012 | A local slash branch was mistaken for a remote counterpart | Ref identity uses full ref namespace and object identity | regression captured |
| FH-013 | Same-tail refs on multiple remotes created false certainty | Equivalent refs collapse by object; distinct lineages stay distinct | regression captured |
| FH-014 | `origin/HEAD` lookup failure was silently ignored | Default-ref discovery failures remain observable diagnostics | regression captured |
| FH-015 | Octopus subject order and deleted refs changed ownership | Subject token order cannot assign content without graph corroboration | regression captured |
| FH-016 | Two-parent multi-name merge subjects relabelled side content | A merge boundary claim is not proof of content ownership | regression captured |
| FH-017 | Normal trunk advancement was reported as base ambiguity | Advancing a base lineage cannot change the historical fork point | regression captured |
| FH-018 | Unrelated historical ambiguity failed the current release | Diagnostics are projected to the caller's commit or issue scope | regression captured |
| FH-019 | Stale fixtures masked shared-index regressions | Fixtures must reproduce each Git boundary and consumer call shape | regression captured |
| FH-020 | Reference oracle repeated implementation assumptions | Truth is declared independently and checked with invariants | superseded by redesign |
| FH-021 | A stricter ref parser broke an unrun consumer fixture | Every changed boundary runs all direct consumer suites before review | regression captured |
| FH-022 | Successful merge-base with empty output became “no base” | Success return codes still require structurally valid output | regression captured |
| FH-023 | Ref movement mixed snapshot-time and query-time graph state | Graph queries use snapshot object IDs, not live ref names | regression captured |
| FH-024 | One arbitrary criss-cross merge base became a unique fork | Fork selection consumes every best merge base or fails scoped ambiguity | regression captured |
| FH-025 | Tests never exercised comparable fork candidates | Invariant tests must fail when ancestry-maximal selection is removed | regression captured |
| FH-026 | A yielded long-running test was reported green before exit | Verification evidence includes the terminal process exit and summary | open |
| FH-027 | Fault-injection fixtures still matched the retired Git command | Boundary migrations update every direct failure fixture before review | regression captured |
| FH-028 | Topic-fork diagnostics disappeared at live attribution | Every live consumer preserves scoped diagnostics through compatibility surfaces | regression captured |
| FH-029 | Publication recovery probed Git per history record | Snapshot traversal must not make subprocess count grow with history length | regression captured |
| FH-030 | A compatibility wrapper retained the retired global-base policy | Compatibility paths delegate per topic or are removed | regression captured |
| FH-031 | Range-truncated snapshots rejected valid topology output | Topology inventory is complete and range projection is separate | regression captured |
| FH-032 | Structured diagnostics duplicated flat compatibility errors | Compatibility messages are stable and deduplicated without losing diagnostic scope | regression captured |
| FH-033 | Traceability accepted IDs without proving their invariants | Every mapping executes the complete derived invariant, not only a named test | open |
| FH-034 | Failure remediation overwrote prior state or omitted implementation evidence | Corrections preserve prior text and append fixing commit plus executable evidence | open |
| FH-035 | Line-wrapped terminal evidence failed a literal-string assertion | Process evidence assertions tolerate Markdown wrapping while preserving exact fields | open |
| FH-036 | Required-component manifest copied the mutable mapping | Every required component is declared independently and every deletion turns the audit red | open |

## Failure Records

### FH-001 — Divergent Consumer Rules

- **Topology**: one issue branch with branch-only commits and a smaller set of
  trailer or merge-subject commits.
- **Observed failure**: converge collected 1 of 44 commits initially and later
  10 while linkage attributed 53 over the comparable history.
- **Invalid assumption**: two consumers could independently implement the same
  ownership question without drifting.
- **Derived invariant**: commit-to-issue and issue-to-commits queries project
  one shared attribution result.
- **Evidence**: Issue 095 founding measurement in `status.md`; original spec.
- **Executable invariant evidence (T08 audit)**:
  `CommitDirectionTests.test_bare_and_full_result_resolution_use_same_policy`
  exercises the two public directions against one projected result;
  `8221ea0`, `efda995`, and `94ca3d4` are the implementation evidence.
- **T08 I2 remediation evidence**: the FH-001 composite now also executes
  `GroundTruthTests.test_trailer_disagrees_with_branch` for issue-to-commits
  truth and
  `FailureInvariantMutationTests.test_fh001_composite_detects_broken_issue_to_commits`;
  the latter proves that replacing issue-to-commits with an empty result is
  caught rather than merely loading a test name.
- **Status**: superseded by redesign. The shared resolver exists, but its graph
  model still requires replacement.

### FH-002 — Containment Is Not Authorship

- **Topology**: a topic branch cut from main, carrying all main ancestors.
- **Observed failure**: raw containment attributed 279 commits where the branch
  contributed 52.
- **Invalid assumption**: every ancestor reachable from an issue branch belongs
  to that issue.
- **Derived invariant**: a branch claim covers only its contribution after its
  historical fork, with stacked-issue exclusions.
- **Evidence**: 2026-07-26 implementation correction in `status.md`.
- **Recurrence evidence**: T03 independent spec review at `fd08636` merged an
  incomparable non-issue lineage into a topic before publication. Publication
  recovery discarded that ordinary base candidate, selected the main fork
  without ambiguity, and included unrelated lineage content in the topic
  delta.
- **Second recurrence evidence**: T03 independent quality review at `bea07b3`
  cut a topic from incomparable `develop=A`, sync-merged `main=F` as second
  parent, then published to main. A first-parent alias walk never reached
  recovered fork `F` but still removed `A`, silently attributing base content.
- **Third recurrence evidence**: T03 independent quality review at `414a81f`
  cut `develop=A` from recovered main fork `F`, then cut and published topic
  `T` from `A`. The alias walk reached `F` and wrongly removed comparable real
  base `A`, attributing `{A,T}` instead of only `{T}`.
- **Resolution evidence**: `0f35406` retained ordinary candidates behind the
  earliest publication side, while `2a000c0` limited live alias suppression to
  the segment above the latest observed publication side. The cumulative T03
  gate reached terminal exit 0 with 231/231 tests; independent spec and quality
  reviews reported no Critical, Important, or Minor findings.
- **Status**: regression captured.

### FH-003 — Current Main Tip Is Not a Historical Base

- **Topology**: a topic branch merged into main; both refs now contain the topic
  commits.
- **Observed failure**: `git rev-list <topic> --not main` returned zero.
- **Invalid assumption**: subtracting the current base tip reconstructs the
  branch's historical contribution.
- **Derived invariant**: contribution is anchored to a merge-base fork point,
  not current containment.
- **Evidence**: 2026-07-26 correction in `status.md`.
- **Recurrence evidence**: T03 independent spec review at `83913d9`
  reproduced `happy_merge` with `fork_point == topic tip`,
  `commits == set()`, and no diagnostic. The first B2 implementation therefore
  repeated the original failure after replacing the global-base path.
- **Second recurrence evidence**: T03 independent quality review at `db7aee8`
  published topic tip `T1`, advanced the live topic ref to `T2`, and observed
  fork `T1` with only `{T2}` returned. Previously published contribution was
  silently lost with no diagnostic.
- **Third recurrence evidence**: T03 independent quality review at `9c03d0f`
  published `T1`, advanced to `T2`, and published again. Fork selection moved
  to `T1`, returning only `{T2}` instead of the full `{T1, T2}` contribution.
- **Fourth recurrence evidence**: T03 independent quality review at `8786ae0`
  retained a non-issue ref at the first published tip `T1`. That ordinary
  candidate dominated recovered fork `F`, again returning only `{T2}` after
  the second publication.
- **Fifth recurrence evidence**: T03 independent spec review at `9bf98e4`
  renamed that alias from `release/last-topic` to sorting-earlier
  `archive/last-topic`. The alias entered ordinary candidates before main
  exposed publication metadata, so ref order again moved the fork to `T1`.
- **Sixth recurrence evidence**: T03 independent quality review at `c43bd73`
  kept a non-issue alias at `Tmid`, a first-parent topic commit between
  publications `T1` and `T2`. Exact publication-side filtering missed it, so
  fork selection advanced to `Tmid` and returned only `{T2}`.
- **Seventh recurrence evidence**: T03 independent quality review at `0f35406`
  published `T1` once, advanced the live topic through `Tmid` to `T2`, and
  kept a non-issue alias at `Tmid` without republishing. Alias suppression
  compared only observed publication sides and omitted the live topic tip as
  the upper anchor, so fork selection advanced to `Tmid` and returned only
  `{T2}` instead of `{T1, Tmid, T2}`.
- **Resolution evidence**: publication recovery and alias-boundary fixes from
  `f9aad10` through `2a000c0` now preserve the pre-publication fork across
  first publication, repeated publication, ref-order aliases, aliases between
  publications, and aliases above the latest publication. The cumulative T03
  gate passed 231/231 with both independent reviews clean.
- **Status**: regression captured.

### FH-004 — Sync-Merge Direction

- **Topology**: main is merged into `codex/alpha`, not alpha into main.
- **Observed failure**: the merge second-parent side was interpreted as alpha's
  contribution and trunk content crossed into the issue.
- **Invalid assumption**: second-parent content always belongs to the issue
  named by the checked-out or subject branch.
- **Derived invariant**: merge direction and content sides are established
  from the graph before ownership policy is applied.
- **Evidence**: review round 4; declared topology in the differential suite.
- **Status**: regression captured.

### FH-005 — Nested Merge Content Leakage

- **Topology**: issue A merges into issue B, then B merges into main.
- **Observed failure**: B's evidence bundle included A's content commit rather
  than only the shared merge boundary.
- **Invalid assumption**: subtracting one global base is sufficient for stacked
  issue branches.
- **Derived invariant**: content commits are single-owner; pairwise fork points
  above the non-issue fork become stacked-issue exclusions.
- **Evidence**: R9-1 in review round 9; corrective commit `ef149a8`.
- **Resolution evidence**: T03 added ancestry-maximal stacked exclusions plus
  cached failure regressions. `2a000c0` passed the 231/231 cumulative gate and
  both independent reviews without an open finding.
- **Recurrence evidence**: T04 independent quality review at `59a4d69`
  reversed the existing nested fixture's issue-id order: inner
  `102-beta` merged into outer `101-alpha`, then the outer branch merged to
  main and both refs were deleted. Both inner and outer merge passes emitted
  equal `branch/content` candidates for the inner commit, and
  `finalize_claims()` broke the tie lexicographically, silently relabelling the
  beta commit as `101-alpha` with no diagnostic.
- **Second recurrence evidence**: T04 independent quality re-review at
  `7d873f6` retained exact refs for stacked A/B sides in a real octopus merge,
  with B forked from A and listed before A. Both parent side sets contained
  A's shared ancestor commit because they subtracted only main history; stable
  same-source ordering assigned that shared commit to B. Reversing octopus
  parent order changed ownership even though the corroborating refs and graph
  were otherwise identical.
- **Third recurrence evidence**: the same `7d873f6` review reduced the defect
  to a conventional merge: B forks from A after commit `a`, adds `b`, and only
  B merges to main while both refs remain. The broad merge-side B candidate
  arrived before the more specific live topic deltas and attributed both
  `a` and `b` to B instead of preserving `a → A`, `b → B`.
- **Fourth recurrence evidence**: T04 independent spec re-review at `d629281`
  retained exact refs for stacked A/B octopus sides but deleted only the third
  C side's ref. The presence of that one unresolved side disabled partitioning
  for all already-corroborated mapped sides, so B-first parent order again
  assigned A's shared commit to B. Unresolved evidence on C's distinct side
  did not guard the overlapping A/B content.
- **Fifth recurrence evidence**: T04 independent quality re-review at
  `585a2f7` built a conventional outer D merge over unique ancestor A, an
  intermediate same-tip B/C ambiguity, and unique descendant D. Seeing B/C on
  one tip made `partition_topic_side_commits()` abort the entire partition;
  the outer fallback silently attributed A, the ambiguous segment, and D all
  to D with no error. Ambiguity on one interval must not erase uniquely
  provable ownership on the other intervals.
- **Resolution evidence**: `5b06879` preserved inner ownership across reversed
  issue ids; `d629281` partitioned overlapping mapped and conventional side
  content by retained topic topology; `585a2f7` kept mapped partitions active
  beside unresolved siblings; and `24bfd3c` scoped same-tip ambiguity to its
  own ancestry interval. The controller's cumulative T04 gate passed 267/267
  at terminal exit, and independent spec and quality reviews reported no
  Critical, Important, or Minor findings.
- **Status**: regression captured.

### FH-006 — Stale Local Default Branch

- **Topology**: local `main` is stale while `origin/main` has advanced before
  the topic fork.
- **Observed failure**: the resolver selected the stale tip and collected trunk
  commits that predated the issue branch.
- **Invalid assumption**: a preferred ref name identifies the correct global
  base.
- **Derived invariant**: compare per-topic merge bases; equivalent candidates
  that produce the same fork point are harmless.
- **Evidence**: Q4 in review round 5, reopened in round 8, R9-2; corrective
  commits `4f5d14a`, `77ecbbf`, and `bfa4157` did not close the architecture.
- **Resolution evidence**: T02 `b711c06`/`d25bbdd` established per-topic
  ancestry-maximal fork selection; T03 preserved that fork through live and
  published deltas. The cumulative gate passed 231/231 at `2a000c0`, followed
  by clean independent spec and quality reviews.
- **Status**: regression captured.

### FH-007 — One-Direction Precedence

- **Topology**: a commit with `Issue: beta` sits on issue alpha's branch.
- **Observed failure**: commit-to-issue returned beta while issue-to-commits
  included the commit in both alpha and beta bundles.
- **Invalid assumption**: source precedence could be enforced separately in
  each query path.
- **Derived invariant**: collect candidate claims first, then apply
  `trailer > branch > merge-subject` exactly once.
- **Evidence**: R9-3; corrective commit `ef149a8`.
- **T08 I2 remediation evidence**:
  `SourcePrecedenceInvariantTests.test_complete_precedence_chain` asserts all
  three levels through `finalize_claims()`, while
  `FailureInvariantMutationTests.test_fh007_composite_detects_branch_first_precedence`
  proves the composite fails under `branch > trailer > merge-subject`.
- **Status**: regression captured.

### FH-008 — Bare Versus Indexed Lookup

- **Topology**: the same conflicting-source commit is resolved once with a
  prebuilt index and once without it.
- **Observed failure**: the bare path short-circuited on a trailer before
  `SOURCE_PRECEDENCE`; only the indexed path consulted the declared policy.
- **Invalid assumption**: duplicated paths would stay semantically aligned.
- **Derived invariant**: all public wrappers project the same index; call shape
  cannot affect ownership.
- **Evidence**: R9-4; corrective commit `ef149a8`.
- **Status**: regression captured.

### FH-009 — Checkout-Dependent and Phantom Issue Registry

- **Topology**: byte-identical history checked out on different branches, or
  `codex/999-not-a-real-issue` with no registered issue artifact.
- **Observed failure**: `git ls-files issues` changed attribution by checkout;
  a fabricated branch tail also satisfied the linkage gate.
- **Invalid assumption**: current worktree files and branch syntax are proof
  that an issue exists historically.
- **Derived invariant**: registered issue identity is loaded from historical
  repository evidence and unknown claims fail closed.
- **Evidence**: review rounds 6 and 8; commit `21d1290`.
- **Status**: regression captured.

### FH-010 — Swallowed Graph Failures

- **Topology**: ancestry, merge-base, or graph queries return a command error or
  negative terminated return code.
- **Observed failure**: failure was interpreted as no ancestor, no ref, or no
  attribution.
- **Invalid assumption**: false and failed are interchangeable at Git
  boundaries.
- **Derived invariant**: ordinary negative results, command failures, and
  terminated calls have separate outcomes and diagnostics.
- **Evidence**: corrective commit `881d81d`; independent quality review.
- **Recurrence evidence**: T03 independent quality review at `db7aee8`
  failed only the stacked beta/alpha `merge-base --all` query. The fatal error
  was recorded, but beta still returned both alpha and beta content.
- **Second recurrence evidence**: T03 independent spec review at `76e8f97`
  failed a publication-parent merge-base query with another good base present.
  The first delta was empty, but a second call on the same snapshot reused the
  cached fatal and returned work plus a base commit.
- **Third recurrence evidence**: T03 independent spec review at `95be177`
  failed only the stacked fork-to-pair ancestry query. The first beta delta was
  empty, but the same snapshot's second call reused the cached fatal and
  returned three commits including alpha content.
- **Fourth recurrence evidence**: T03 independent quality review at `9c03d0f`
  cached an incomplete publication ancestry as `None`. The first delta closed,
  but a second call lost the cached fatal context and returned topic content;
  repeated membership projection also lost its compatibility error signal.
- **Fifth recurrence evidence**: T03 independent quality review at `8786ae0`
  cached a stacked pairwise merge-base failure. Attribution stayed empty, but
  the second membership build returned `errors=[]` and `degraded=[]` because
  the fatal early return omitted query metadata from the delta payload.
- **Sixth recurrence evidence**: T05 independent quality review at `a4065f6`
  forced the live topic `merge-base --all` query to fail after the snapshot
  loaded. `build_attribution()` collected the membership fatal but continued
  candidate calculation, so a trailer-bearing commit remained attributed and
  the bare resolver returned an issue id together with `fatal_errors`.
- **Resolution evidence**: `95be177`, `9c03d0f`, `290aa62`, `4fc5525`,
  `bea07b3`, and `414a81f` made fresh and cached fork, ancestry, publication,
  and stacked-membership failures replay the same scoped compatibility signal
  while keeping the affected delta empty. T03 passed 231/231 and final quality
  review explicitly rechecked cached failure behavior.
- **Resolution evidence**: `8221ea0` makes every post-snapshot membership or
  registry fatal return empty attribution, preserves records/order/unmatched
  and scoped diagnostic surfaces, and prevents whole-result and bare resolvers
  from returning an owner. The cumulative T05 gate passed 279/279, and
  independent spec and quality reviews reported no finding.
- **Status**: regression captured.

### FH-011 — Disconnected Non-Issue Base

- **Topology**: a non-issue ref points to history unrelated to a topic branch.
- **Observed failure**: repository-wide scoring could elect it as the base or
  turn it into global ambiguity.
- **Invalid assumption**: every non-issue ref participates in one base
  election.
- **Derived invariant**: a candidate without a usable merge base for the topic
  is irrelevant to that topic and cannot affect other topics.
- **Evidence**: independent review around corrective commit `4f5d14a`.
- **Resolution evidence**: T02 per-topic fork invariants and T03 delta
  regressions keep disconnected refs irrelevant while scoping true
  incomparability to the affected topic. The T03 cumulative gate passed
  231/231 with clean independent reviews.
- **Status**: regression captured.

### FH-012 — Local Slash Branch Versus Remote Namespace

- **Topology**: a local branch name contains a slash and resembles a
  remote-tracking branch tail.
- **Observed failure**: tail-based comparison collapsed unrelated refs.
- **Invalid assumption**: display-name similarity establishes ref equivalence.
- **Derived invariant**: retain full ref namespace; collapse only refs proven
  equivalent by object identity and lineage.
- **Evidence**: independent review around corrective commit `4f5d14a`.
- **Resolution evidence**: T02's full-ref/object snapshot regressions and T03's
  ref-order publication regressions passed the 231/231 cumulative gate at
  `2a000c0`.
- **Status**: regression captured.

### FH-013 — Same Tail Across Multiple Remotes

- **Topology**: remote-only or local-plus-multiple-remote refs share a branch
  tail but point to equivalent or divergent commits.
- **Observed failure**: name-based matching either duplicated one lineage or
  merged distinct lineages.
- **Invalid assumption**: `<remote>/<tail>` names identify one logical ref.
- **Derived invariant**: identical object ids collapse; distinct fork evidence
  remains distinct and ambiguity is scoped to the affected topic.
- **Evidence**: final attribution review leading to `77ecbbf` and `bfa4157`.
- **Resolution evidence**: T02 covers equal-object collapse and divergent
  same-tail ambiguity; T03 preserves that diagnostic through live membership
  and cached projection. The cumulative gate passed 231/231 with clean
  independent reviews.
- **Status**: regression captured.

### FH-014 — Silent `origin/HEAD` Failure

- **Topology**: symbolic default-ref lookup is absent, malformed, or its Git
  command fails.
- **Observed failure**: fallback selection continued without exposing why the
  authoritative candidate was unavailable.
- **Invalid assumption**: default-ref lookup failure is equivalent to the ref
  not existing.
- **Derived invariant**: Git boundary failures remain structured diagnostics;
  fallback use is observable.
- **Evidence**: corrective review and commits `77ecbbf`, `bfa4157`.
- **T08 I2 remediation evidence**:
  `DiagnosticProjectionTests.test_ref_inventory_failure_is_structured_and_fails_closed`
  asserts fatal/compatibility projection and empty attribution when immutable
  ref discovery fails; the composite also executes
  `SharedOwnershipTests.test_live_resolution_has_no_global_base_election_or_origin_head_probe`
  to prove no silent named fallback is reintroduced.
- **Status**: regression captured; must be preserved by the redesign.

### FH-015 — Octopus Merge Subject Order

- **Topology**: an octopus merge names several issue branches, refs are later
  deleted, and subject tokens are reordered.
- **Observed failure**: subject position was paired with parent position,
  changing or losing content ownership.
- **Invalid assumption**: prose order is graph evidence.
- **Derived invariant**: subject order may label a merge boundary but cannot
  assign side content without graph corroboration.
- **Evidence**: review rounds 7–9 and the later historical octopus regression.
- **Resolution evidence**: T04 separates boundary claims from content claims,
  requires exact retained-ref corroboration for complex sides, partitions
  overlapping mapped topic content independently of parent order, and leaves
  unresolved sides unowned with scoped diagnostics. The cumulative gate
  passed 267/267 at `24bfd3c` with clean independent reviews.
- **Status**: regression captured.

### FH-016 — Two-Parent Multi-Name Merge

- **Topology**: a normal two-parent merge subject mentions more than one
  registered issue.
- **Observed failure**: names in prose were treated as ownership evidence for
  one content side.
- **Invalid assumption**: every issue name in a merge subject describes a
  distinct merged lineage.
- **Derived invariant**: merge boundary claims and content-side claims are
  separate; ambiguous side content stays unresolved.
- **Evidence**: final quality review before the redesign.
- **Recurrence evidence**: T04 independent quality re-review at `5b06879`
  created trailer-free work `W` reachable from both `codex/101-alpha` and
  `codex/102-beta`, then merged the shared tip with a two-name subject. The
  merge pass emitted `merge-side-unresolved`, but live membership later added
  equal `branch/content` candidates for both issues and `finalize_claims()`
  selected the first one, silently guessing `101-alpha` despite the unresolved
  side diagnostic. The existing fixture's Alpha trailer masked this path.
- **Second recurrence evidence**: T04 independent quality re-review at
  `3f7b863` nested that unresolved A/B boundary inside outer issue C, merged C
  conventionally to main, and deleted all three refs. The first suppression
  fix saw only C as the remaining content candidate, ignored the earlier A/B
  unresolved evidence because their ids did not intersect C, and silently
  relabelled `W` as C. A broader outer branch is not evidence that resolves an
  inner merge-side ambiguity.
- **Resolution evidence**: `3f7b863` introduced explicit unresolved candidate
  evidence, `7d873f6` preserved its graph-specific ordering against broader
  outer claims, and `24bfd3c` localized ambiguous same-tip intervals while
  still allowing stronger trailer or earlier mapped evidence to resolve
  ownership. The controller gate passed 267/267 and both independent reviews
  reported no finding.
- **Status**: regression captured.

### FH-017 — Trunk Advance After Topic Fork

- **Topology**: a topic forks from main, then main advances independently.
- **Observed failure**: the current main tip and topic tip became incomparable,
  so ordinary development was reported as ambiguous base selection.
- **Invalid assumption**: the base ref tip must remain an ancestor of the topic
  tip.
- **Derived invariant**: advancing a base lineage after fork does not change
  the topic's merge-base fork point or attribution.
- **Evidence**: final independent quality review at `bfa4157`.
- **Resolution evidence**: T02's advancing-trunk invariant and T03's live and
  published delta regressions preserve the historical merge-base fork. The
  cumulative gate passed 231/231 at `2a000c0`.
- **Status**: regression captured.

### FH-018 — Unscoped Historical Ambiguity

- **Topology**: an ambiguous historical octopus merge exists outside the
  release range being checked.
- **Observed failure**: focused tests passed 221/221, but full discovery failed
  2 of 885 and release linkage failed because a flat global error leaked into
  the current release.
- **Invalid assumption**: any ambiguity anywhere invalidates every consumer
  query.
- **Derived invariant**: diagnostics are attached to commits, issues, or refs
  and projected only to the caller's requested scope; snapshot failures remain
  globally fatal.
- **Evidence**: historical merge
  `777b04e6fe531d46a123aadbb236fcf3cb33e5c7`; redesign trigger at `bfa4157`.
- **Resolution evidence**: `d5da824` makes linkage collect behavior commits
  first, build attribution once with exactly those SHAs, and reuse the whole
  result. The same historical ambiguity is excluded when outside the release
  scope and fails closed when inside it; neutral-only ranges build no
  attribution. The T06 cumulative gate passed 281/281 with clean independent
  reviews.
- **Recurrence evidence**: T07 independent quality review at `efda995` passed
  an unscoped prebuilt attribution result into
  `resolve_commits_for_issue(..., target_issue_ids={beta})`. The resolver used
  `index or build_attribution(...)` unchanged, so Alpha's same-tail ambiguity,
  compatibility error, and degradation leaked into the Beta bundle despite
  the explicit issue scope.
- **Resolution evidence**: `94ca3d4` reprojects prebuilt whole-result
  diagnostics to the requested issue while always preserving fatal errors,
  rebuilds compatibility errors/degraded without a Git retry, and explicitly
  rejects incomplete attribution-only indexes. The controller gate passed
  335/335; final independent reviews reported no finding.
- **Status**: regression captured.

### FH-019 — Fixture and Call-Shape Masking

- **Topology**: FakeRunner or GitRepo fixtures omit remote refs, detached HEAD,
  failed commands, or the consumer's shared-index call shape.
- **Observed failure**: focused suites passed because the broken path was never
  constructed, or because stale fixtures exercised a private path no consumer
  used.
- **Invalid assumption**: unit-level happy-path parity represents the real Git
  boundary and both consumer entry points.
- **Derived invariant**: each Git boundary has real-topology coverage plus
  ordinary-negative, failure, terminated-return, bare, and indexed cases.
- **Evidence**: review rounds 1–4; fixture alignment commits `235f357` and
  `5ccdbb5`.
- **T08 I2 remediation evidence**: the FH-019 composite executes snapshot log
  and ref inventory, ordinary-negative versus failed merge-base, terminated
  ancestry, malformed successful merge-base and range output, and
  `CommitDirectionTests.test_bare_and_full_result_resolution_use_same_policy`
  for both public call shapes.
- **T08 I2 boundary-completion evidence**: the executable set additionally
  injects structured log and ref-inventory failures, a terminated live
  merge-base call, and a failed live rev-list call so each current graph
  boundary family participates in the fail-closed audit.
- **Status**: regression captured; invariant coverage remains a completion
  gate.

### FH-020 — Shared-Oracle Blind Spot

- **Topology**: resolver and reference oracle independently run the same
  base-ref heuristic against stale, stacked, or mis-elected bases.
- **Observed failure**: implementation and oracle agreed on the same wrong
  answer; four review rounds reopened “closed” findings.
- **Invalid assumption**: a second implementation is independent merely
  because it lives in a different file.
- **Derived invariant**: fixtures declare literal ownership truth, reviewers
  audit declarations, and metamorphic tests assert properties that do not
  depend on one expected topology.
- **Evidence**: review rounds 4, 5, 7, 8, and 9.
- **Executable invariant evidence (T08 audit)**:
  `DeclarationSanityTests.test_no_reference_oracle_remains`, together with
  every generated `DeclarationCoverageTests.test_declared_*` and
  `GroundTruthTests.test_*` case, enforces literal truth without a derived
  oracle; `f6cfdb3` is the implementation evidence.
- **T08 I2 remediation evidence**: the executable composite selects both
  declaration coverage and ground-truth resolution for the conflicting-source
  shape, asserts that real work is recorded, asserts the derived oracle file
  remains absent, and runs the subject-order metamorphic invariant.
- **Status**: superseded by redesign; the reference oracle stays deleted.

### FH-021 — Stale Consumer Fixture Outside the Focused Gate

- **Topology**: `build_attribution()` begins requiring full
  `<ref> <object-id>` records, while a linkage FakeRunner still returns ref
  names without object ids.
- **Observed failure**: the graph snapshot correctly failed closed, but Task
  T01's selected focused suites passed because `tests.test_linkage_check` was
  not run; the direct consumer suite remained red.
- **Invalid assumption**: resolver and unit suites cover every consumer whose
  fixtures encode the changed Git boundary.
- **Derived invariant**: changing a shared Git boundary requires running every
  direct consumer suite and updating fixtures to the complete command-output
  contract without weakening fail-closed parsing.
- **Evidence**: T01 independent code-quality review at `1ceb153`,
  `tests/test_linkage_check.py:180`.
- **Resolution evidence**: `8068f98` updated the linkage fixture to the full
  ref-record contract. The direct graph, resolver, parity, and linkage consumer
  suites then passed 105/105, and independent quality re-review found no open
  Critical, Important, or Minor findings.
- **Status**: regression captured.

### FH-022 — Empty Successful Merge-Base Output

- **Topology**: `git merge-base` returns code 0 with empty stdout.
- **Observed failure**: `merge_base()` returned `sha: None` with no fatal
  errors, making malformed successful output indistinguishable from return
  code 1 meaning no common ancestor.
- **Invalid assumption**: return code 0 proves the command output is
  structurally usable.
- **Derived invariant**: every successful Git boundary validates its required
  output fields; empty or malformed success is a fatal command-output error.
- **Evidence**: T01 independent code-quality review at `1ceb153`,
  `scripts/commit_graph.py:55`.
- **Resolution evidence**: `8068f98` added RED/GREEN coverage for empty and
  multi-token successful merge-base output and made both fail closed. The
  direct graph, resolver, parity, and linkage consumer suites passed 105/105.
- **Recurrence evidence**: T03 independent spec review at `76e8f97` returned
  rc=0 range output `not-a-snapshot-sha extra`. The projection silently
  filtered it to no commits and exposed no error.
- **Resolution evidence**: `fd08636` validates every nonempty successful range
  line as exactly one known snapshot SHA while accepting valid empty output.
  Malformed and unknown output now fail closed observably; the cumulative T03
  gate passed 231/231.
- **Status**: regression captured.

### FH-023 — Snapshot Ref Movement Mixed Graph Times

- **Topology**: load a graph snapshot, then move `refs/heads/main` to the topic
  tip before deriving the topic fork.
- **Observed failure**: the snapshot retained the old main object ID, but
  `derive_fork_point()` queried Git with the live ref name and returned the
  moved topic tip as the fork without diagnostics or fatal errors.
- **Invalid assumption**: an immutable ref inventory remains immutable when
  later graph queries use ref names instead of the captured object IDs.
- **Derived invariant**: every graph query associated with a snapshot uses the
  snapshot's object IDs for both command arguments and cache identity; ref
  names are reporting metadata only.
- **Evidence**: T02 independent code-quality review at `ccffbce`,
  `scripts/commit_graph.py:128`.
- **Resolution evidence**: `b711c06` changed fork queries and cache identity to
  snapshot object IDs and added ref-movement, duplicate-ref, and cached-fatal
  regressions. The T02 direct consumer gate passed 117/117 at `d25bbdd`.
- **Status**: regression captured.

### FH-024 — Arbitrary Criss-Cross Merge Base

- **Topology**: a valid criss-cross graph where `git merge-base --all` returns
  two incomparable best merge bases for one topic/base pair.
- **Observed failure**: the single-result merge-base query returned one SHA,
  and `derive_fork_point()` accepted it as the unique fork with no diagnostic.
- **Invalid assumption**: default `git merge-base` output is the complete set
  of best common ancestors.
- **Derived invariant**: fork derivation consumes every best merge-base
  candidate; incomparable maxima yield an issue-scoped ambiguity instead of
  selecting Git's arbitrary single output.
- **Evidence**: T02 independent code-quality review at `ccffbce`,
  `scripts/commit_graph.py:62` and `scripts/commit_graph.py:128`.
- **Resolution evidence**: `b711c06` added complete `merge-base --all`
  candidate handling and an executable criss-cross fixture that returns a
  scoped ambiguity. `d25bbdd` also made every fixture merge truth-explicit.
- **Status**: regression captured.

### FH-025 — Comparable Fork Candidate Path Was Untested

- **Topology**: two distinct fork candidates where the older candidate is a
  strict ancestor of the newer candidate.
- **Observed failure**: replacing `is_ancestor()` with an always-false answer
  still left all seven T02 invariant tests green.
- **Invalid assumption**: single, equal, and incomparable candidate cases also
  prove ancestry-maximal elimination.
- **Derived invariant**: the test suite must exercise a comparable candidate
  chain and fail if the dominated candidate is not removed.
- **Evidence**: T02 independent code-quality review at `ccffbce`,
  `tests/test_commit_graph.py:265`.
- **Resolution evidence**: `b711c06` added a comparable-chain invariant whose
  result fails when ancestry elimination is disabled and selects only the
  newer unique maximal fork.
- **Status**: regression captured.

### FH-026 — Yielded Test Process Reported Green Before Exit

- **Topology**: the graph, resolver, differential, parity, and linkage command
  runs longer than the execution tool's initial yield window.
- **Observed failure**: T03 reported the cumulative gate as exit 0, while an
  independent run completed after 99 seconds with 200 tests and seven failures.
- **Invalid assumption**: no output at a yield boundary means the process
  completed successfully.
- **Derived invariant**: verification evidence is valid only after polling the
  same process session to a terminal exit code and recording its final test
  summary.
- **Evidence**: T03 independent controller run at `4d20a19`,
  `python3 -m unittest tests.test_commit_graph tests.test_commit_resolution
  tests.test_commit_resolution_differential tests.test_commit_resolution_parity
  tests.test_linkage_check -q`.
- **Resolution evidence**: the controller polled the same process to terminal
  exit 0 at `2a000c0`: 231 tests passed in 204.678 seconds. Independent spec
  review repeated the full command with 231/231 and terminal exit 0.
- **Historical state (preserved)**: regression captured. This was the current
  state after the T03 terminal run and before the T08 recurrence below
  reopened the failure; preserving it does not replace the current status.
- **T08 audit evidence**: the six Issue 095 suites were polled in the same
  session to terminal exit 0: 338 tests passed in 173.165 seconds, including
  the three executable traceability checks.
- **Recurrence evidence**: T08 independent spec review at `e62d3fe` removed
  the new T08 audit evidence and the process-gate test still passed by matching
  the older T03 terminal-exit sentence elsewhere in this record.
- **T08 I2 remediation evidence**:
  `ProcessGateInvariantTests.test_t08_audit_evidence_records_terminal_exit_and_summary`
  isolates the unique `T08 audit evidence` block and requires its six-suite,
  terminal-exit, count, and duration fields;
  `FailureInvariantMutationTests.test_fh026_current_audit_block_removal_is_detected`
  removes that exact block and proves the process invariant turns red.
- **T08 I2 green evidence**: the remediated six-suite command was polled in
  the same session to terminal exit 0: 343 tests passed in 226.614 seconds.
- **T08 I3 terminal evidence**: after the second remediation, the six Issue
  095 suites were polled in the same session to terminal exit 0: 350 tests
  passed in 223.391 seconds.
- **Status**: open until the process-gate test identifies the current T08
  evidence specifically and fails when that evidence is removed.

### FH-027 — Retired Git Command Left Stale Failure Fixtures

- **Topology**: live topic deltas migrate from single-result
  `git merge-base <ref> <ref>` to complete
  `git merge-base --all <object-id> <object-id>`, while resolver failure
  fixtures still intercept only the old command.
- **Observed failure**: terminated and failed merge-base tests no longer
  injected the failure, so branch work was attributed instead of failing
  closed; origin-HEAD tests also asserted a command the live global-base path
  intentionally removed.
- **Invalid assumption**: replacing a Git boundary in production code does not
  require migrating direct consumer fault-injection fixtures and retired-path
  expectations.
- **Derived invariant**: every boundary migration updates all direct failure
  fixtures to the exact current command shape and removes assertions for
  intentionally retired commands before the task can be green.
- **Evidence**: T03 controller gate at `4d20a19`,
  `tests/test_commit_resolution.py:714-821`.
- **Resolution evidence**: T03 migrated the failure fixtures to
  `merge-base --all` object-id queries, removed retired `origin/HEAD`
  expectations, and passed the cumulative 231/231 gate.
- **Recurrence evidence**: T05 implementation at `e9d141e` removed the
  explicitly retired bare `git show` resolver, but three direct linkage
  fixtures still stubbed or failed only that command. The new single
  `build_attribution(target_shas={sha})` path therefore received no usable
  snapshot in two ownership tests, while the old git-show failure test asserted
  an obsolete error boundary. Restoring a production fallback would recreate
  the duplicated policy D1 is required to remove.
- **Resolution evidence**: `a4065f6` migrated all three linkage fixtures to
  the current snapshot/graph boundary and removed the bare `git show` policy
  path. The T05 direct-consumer gate passed 279/279 at `8221ea0` with clean
  independent reviews.
- **T08 I2 remediation evidence**: the FH-027 composite executes the current
  snapshot-contract trailer fixture, a real-repository branch fixture,
  structured snapshot failure projection, and trailer-versus-branch
  precedence through the direct linkage consumer.
- **Status**: regression captured.

### FH-028 — Topic Diagnostics Disappeared at Live Attribution

- **Topology**: same-tail remote histories produce incomparable per-topic fork
  candidates and an `ambiguous-topic-fork` diagnostic.
- **Observed failure**: `topic_delta()` detected the ambiguity, but
  `build_attribution()` returned `errors: []`; two differential shapes lost
  the existing live compatibility warning.
- **Invalid assumption**: computing a scoped diagnostic is sufficient even
  when the live builder drops it before consumer-facing output.
- **Derived invariant**: live membership and attribution preserve every
  per-topic diagnostic through the current compatibility error surface until
  Stream D introduces the final structured projection.
- **Evidence**: T03 controller gate at `4d20a19`,
  `tests/test_commit_resolution_differential.py:156`.
- **Recurrence evidence**: T03 independent quality review at `8786ae0`
  showed that a second membership projection over a cached pairwise graph
  failure stayed empty but dropped both the compatibility error and degraded
  marker.
- **Resolution evidence**: `83913d9`, `4fc5525`, `bea07b3`, and `414a81f`
  preserve same-tail ambiguity and cached fork/ancestry/publication failures
  through every membership projection. Final quality review at `2a000c0`
  explicitly verified the fresh/cached fail-closed contract.
- **Status**: regression captured.

### FH-029 — Publication Recovery Scaled Git Calls with History

- **Topology**: a published topic is recovered by scanning every snapshot
  record and issuing cached ancestry queries for candidate commits.
- **Observed failure**: the correctness gate passed, but implementation
  self-review found that the number of Git subprocesses could grow with commit
  history; the 201-test cumulative gate expanded to 121.281 seconds.
- **Invalid assumption**: cached per-commit graph probes satisfy the
  command-count contract merely because duplicate pairs do not rerun.
- **Derived invariant**: publication recovery traverses the already-loaded
  parent graph in memory and issues only a bounded number of Git commands per
  topic/ref topology, independent of unrelated history length.
- **Evidence**: T03 implementation self-review at `f9aad10`,
  `scripts/commit_graph.py` publication-fork recovery.
- **Recurrence evidence**: T03 independent spec re-review at `b2ddde6` used a
  long-lived branch cut before the topic and merged after topic publication.
  `_publication_forks()` misclassified it as another publication boundary,
  increasing Git calls from 6 to 7 without changing the result.
- **Resolution evidence**: `b2ddde6`/`db7aee8` moved publication topology
  recovery to bounded snapshot traversal and added unrelated-history and
  pre-topic long-lived-branch command-count metamorphic regressions. Final
  quality review confirmed live alias handling adds no Git subprocesses.
- **Status**: regression captured.

### FH-030 — Retired Global-Base Compatibility Wrapper

- **Topology**: the live resolver uses per-topic deltas, but a direct
  `base_ref()` compatibility call still probes `origin/HEAD`, scores repository
  refs globally, and elects one base.
- **Observed failure**: no live caller remained, yet the callable wrapper
  preserved the exact repository-wide policy B2 was required to remove.
- **Invalid assumption**: dead compatibility code is harmless even when it
  exposes the superseded ownership model as an importable function.
- **Derived invariant**: unsupported global-base helpers are removed with their
  stale tests; any retained compatibility surface requires an explicit topic
  and delegates to per-topic fork derivation.
- **Evidence**: T03 independent quality review at `db7aee8`,
  `scripts/commit_resolution.py:175`.
- **Resolution evidence**: T03 removed the `base_ref()` election path and its
  stale tests. The remaining empty `ORIGIN_HEAD_ARGS` import is inert
  compatibility only; the live-resolution regression proves no global-base
  election or `origin/HEAD` query occurs.
- **Status**: regression captured.

### FH-031 — Range-Truncated Topology Snapshot

- **Topology**: a live topic has commits `A` then `B`, and resolution requests
  `rev_range=A..B`.
- **Observed failure**: the snapshot inventory contained only `B`; topic
  `rev-list` correctly emitted `A` and `B`, but validation treated `A` as
  malformed and returned an empty result plus a fatal error.
- **Invalid assumption**: the caller's output range is also a complete graph
  inventory for topology validation.
- **Derived invariant**: attribution loads a complete topology snapshot,
  validates graph output against it, and projects the final attribution onto
  the requested range separately.
- **Evidence**: T03 independent quality review at `db7aee8`,
  `scripts/commit_graph.py:484` and `scripts/commit_graph.py:567`.
- **Recurrence evidence**: T03 independent quality review at `9c03d0f`
  showed that `HEAD..HEAD` was rejected as malformed despite being a valid
  empty range, while `build_attribution(A..B)` returned `order=[B]` but kept
  out-of-range `A` in its public attribution map.
- **Second recurrence evidence**: T03 implementation self-review at `290aa62`
  allowed empty output only when the two range endpoint strings were equal.
  Distinct refs resolving to the same commit and other graph-equivalent empty
  ranges still failed despite a successful Git result.
- **Resolution evidence**: `380e23e`, `fd08636`, and later range fixes load
  full topology independently, project both order and public attribution to
  the requested range, accept rc=0 empty ranges regardless of endpoint text,
  and fail closed on malformed or failed projections. The cumulative T03 gate
  passed 231/231.
- **Status**: regression captured.

### FH-032 — Duplicated Flat Compatibility Errors

- **Topology**: one unresolved merge produces several structured diagnostics
  for its boundary, affected SHAs, and affected issue ids.
- **Observed failure**: `compatibility_errors()` copied every diagnostic
  message verbatim, so one logical unresolved merge appeared four to six times
  in the legacy flat `errors` list.
- **Invalid assumption**: preserving structured diagnostic multiplicity also
  requires duplicating the compatibility message surface.
- **Derived invariant**: structured diagnostics retain every scoped record,
  while compatibility errors preserve first-seen order and deduplicate equal
  fatal strings and diagnostic messages.
- **Evidence**: T05 independent quality review at `a4065f6` reproduced six
  identical errors for `octopus_mapping_ambiguous` and four each for
  `two_parent_multi_name_ambiguous_no_trailer` and
  `stacked_partial_ambiguity_conventional_merge`.
- **Resolution evidence**: `8221ea0` deduplicates fatal strings and diagnostic
  messages in first-seen order while retaining every structured SHA/issue
  diagnostic. The cumulative gate passed 279/279 and final quality review
  independently rechecked both surfaces.
- **T08 I2 remediation evidence**: the FH-032 composite executes the synthetic
  first-seen dedupe contract plus octopus and multi-name real-topology cases
  that first assert duplicate structured messages exist and then assert one
  flat compatibility message remains.
- **Status**: regression captured.

### FH-033 — Traceability Without Invariant Coverage

- **Topology**: a failure id is mapped to a loadable test whose assertions
  cover only a narrower behavior than the record's derived invariant.
- **Observed failure**: T08 traceability stayed green when issue-to-commits was
  broken for FH-001 and when precedence was changed to `branch > trailer` for
  FH-007; several other mappings likewise checked only names, absence, or one
  boundary variant.
- **Invalid assumption**: loading and running one named test proves the full
  invariant merely because its docstring contains the same `FH-*` id.
- **Derived invariant**: every traceability mapping must execute assertions
  covering the complete recorded invariant, including both directions,
  precedence order, observable diagnostics, and required boundary variants.
- **Evidence**: T08 independent spec review at `e62d3fe`, including mutation
  probes for FH-001 and FH-007 and coverage review of FH-014, FH-019, FH-020,
  FH-027, and FH-032.
- **T08 I2 remediation evidence**:
  `FailureHistoryTraceabilityTests.test_every_failure_record_maps_to_executable_invariant_tests`
  expands one-to-many mappings, executes every unique qualified test, rejects
  missing/duplicate/skipped/failing components, and is backed by explicit
  mutation probes for FH-001, FH-007, and FH-026.
- **T08 I2 green evidence**: the composite traceability gate passed, both
  reviewer mutations were first reproduced as surviving the old mapping, all
  three new mutation probes caught their injected defect, and the six-suite
  terminal gate passed 343/343 in 226.614 seconds.
- **Recurrence evidence**: T08 spec re-review at `04bae8d` forced
  commit-to-issue resolution to return the same wrong issue in both bare and
  indexed paths; all FH-001 components still passed because they asserted
  agreement but not commit-direction truth. Removing the FH-001
  commit-direction component also left the audit green because it validated
  only that the remaining tuple was nonempty.
- **T08 I3 remediation evidence**: the first remediation implementation
  `04bae8d` is preserved as the exact commit that introduced executable
  composites but left this recurrence. The follow-up adds
  `CommitDirectionTruthTests.test_bare_and_indexed_resolution_match_declared_truth`
  for literal commit-direction truth,
  `FailureInvariantMutationTests.test_fh001_composite_detects_same_wrong_commit_issue`
  for the same-wrong-result mutation, and
  `FailureInvariantMutationTests.test_fh033_required_manifest_detects_removed_fh001_commit_truth`
  for required-component deletion.
- **T08 I3 implementation evidence**: `910a19c` adds the literal truth
  assertion, same-wrong-result mutation, canonical required-component
  manifest, and component-removal mutation.
- **T08 I3 green evidence**: the focused remediation set passed 12/12 in
  37.759 seconds, then the six-suite process reached terminal exit 0 with
  350/350 passing in 223.391 seconds.
- **Status**: open until mutation-sensitive or composite invariant tests cover
  each mapped requirement and the traceability audit fails when any component
  is removed.

### FH-034 — Non-Append-Only Failure Remediation

- **Topology**: a review reopens a previously regression-captured failure and
  the remediation edits its status while adding a new failure record.
- **Observed failure**: T08 replaced FH-026's prior `regression captured`
  status text with `open` instead of preserving the historical state, and the
  new FH-033 record omitted the fixing implementation commit `04bae8d`.
- **Invalid assumption**: changing current status and adding review evidence
  is sufficient when earlier state text disappears or implementation evidence
  is incomplete.
- **Derived invariant**: remediation preserves prior status text as history,
  appends the current status, and records the exact fixing commit plus
  qualified executable test evidence.
- **Evidence**: T08 spec re-review at `04bae8d`, FH-026 and FH-033.
- **Executable acceptance evidence**:
  `FailureEvidenceInvariantTests.test_fh026_preserves_historical_regression_state`
  requires the parser-safe historical state and exactly one current status;
  `FailureEvidenceInvariantTests.test_fh033_records_first_remediation_commit_and_qualified_evidence`
  requires the exact first-remediation commit and qualified proof names; and
  `FailureEvidenceInvariantTests.test_fh034_record_declares_append_only_remediation_contract`
  keeps this contract executable.
- **Resolution candidate evidence**: `910a19c` restores the preserved FH-026
  state, records `04bae8d` in FH-033, and makes the append-only acceptance
  checks executable.
- **Terminal verification evidence**: the six Issue 095 suites were polled in
  the same session to terminal exit 0: 350 tests passed in 223.391 seconds.
- **Status**: open until historical status is restored append-only and fixing
  commit plus executable evidence are recorded and validated.

### FH-035 — Line-Wrapped Terminal Evidence Rejected

- **Topology**: a terminal-evidence sentence wraps between `Issue` and `095`
  under the repository's Markdown line length.
- **Observed failure**: after the six-suite process passed 350/350, the focused
  evidence run exited 1 with two failures because
  `ProcessGateInvariantTests.test_t08_audit_evidence_records_terminal_exit_and_summary`
  required the contiguous literal `six Issue 095 suites`.
- **Invalid assumption**: semantic evidence fields remain contiguous in the
  Markdown source after normal line wrapping.
- **Derived invariant**: process evidence assertions tolerate whitespace
  wrapping between semantic tokens while continuing to require the exact
  suite label, terminal exit code, test count, and duration.
- **Evidence**: T08 I3 focused evidence run after `910a19c`: 12 tests, two
  failures, terminal exit 1.
- **Recurrence evidence**: the first whitespace fix covered only the suite
  label. The next 12-test focused run still exited 1 with three failures:
  count/duration wrapping remained literal-sensitive, and the new FH-035
  heading exposed FH-034's next-heading delimiter as incomplete.
- **Executable remediation evidence**:
  `ProcessGateInvariantTests.test_t08_audit_evidence_records_terminal_exit_and_summary`
  uses whitespace-tolerant suite-label and summary patterns,
  `FailureEvidenceInvariantTests.test_fh034_record_declares_append_only_remediation_contract`
  isolates FH-034 at the next failure heading, while
  `FailureInvariantMutationTests.test_fh026_current_audit_block_removal_is_detected`
  still proves that deleting the complete current evidence block turns the
  invariant red.
- **Green evidence**: the corrected focused set passed 12/12 in 36.576
  seconds. The final six-suite rerun was polled in the same session to terminal
  exit 0: 350 tests passed in 208.494 seconds.
- **Status**: open until the focused and six-suite gates pass with terminal
  exits after this correction.

### FH-036 — Self-Derived Required-Component Manifest

- **Topology**: `REQUIRED_FAILURE_COMPONENTS` is initialized by copying every
  entry from mutable `FAILURE_INVARIANT_TESTS`, then only selected failure ids
  are independently overridden.
- **Observed failure**: T08 spec review at `45788df` removed one FH-035
  component and reloaded the module; both the mapping and its supposed
  canonical manifest lost the same component, so `_required_component_gaps()`
  returned `{}`.
- **Invalid assumption**: a snapshot comprehension over the mutable mapping is
  an independent oracle merely because later runtime mutation of the already
  loaded mapping is detectable.
- **Derived invariant**: every failure id and every required qualified test is
  declared independently from the mutable execution mapping, and removing any
  single declared component must produce a nonempty gap for that failure id.
- **Evidence**: T08 independent spec review at `45788df`, FH-035 component
  deletion/reload mutation.
- **Status**: open until an exhaustive every-id/every-component mutation test
  fails against the self-derived manifest and passes against an independent
  literal manifest.

## T08 Executable Invariant Audit

This append-only matrix records the executable reference and implementation
evidence audited for every failure family. The qualified test names are also
validated by
`FailureHistoryTraceabilityTests.test_every_failure_record_maps_to_a_loadable_invariant_test`;
`FH-026` is a process gate and is therefore checked against terminal-exit
evidence rather than product behavior.

| Failure | Executable invariant test | Implementation evidence |
| --- | --- | --- |
| FH-001 | `CommitDirectionTests.test_bare_and_full_result_resolution_use_same_policy` | `8221ea0`, `efda995`, `94ca3d4` |
| FH-002 | `TopicDeltaTests.test_base_history_is_not_topic_work` | `0f35406`, `2a000c0` |
| FH-003 | `TopicDeltaTests.test_published_no_ff_topic_recovers_pre_publication_fork` | `f9aad10`–`2a000c0` |
| FH-004 | `MergeClaimInvariantTests.test_subject_token_order_does_not_change_content` | `59a4d69` |
| FH-005 | `TopicDeltaTests.test_stacked_issue_excludes_inner_content` | `24bfd3c` |
| FH-006 | `ForkPointInvariantTests.test_advancing_trunk_does_not_change_fork_point` | `b711c06`, `d25bbdd` |
| FH-007 | `CommitDirectionTests.test_bare_and_full_result_resolution_use_same_policy` | `ef149a8`, `8221ea0` |
| FH-008 | `CommitDirectionTests.test_bare_and_full_result_resolution_use_same_policy` | `ef149a8`, `8221ea0` |
| FH-009 | `TestHistoricalIssueRegistry.test_issue_on_another_checkout_is_registered` | `21d1290`, `8221ea0` |
| FH-010 | `SnapshotTests.test_merge_base_distinguishes_no_base_from_failure` | `881d81d`, `8221ea0` |
| FH-011 | `ForkPointInvariantTests.test_disconnected_ref_does_not_change_connected_topic` | `b711c06` |
| FH-012 | `ForkPointInvariantTests.test_same_tail_slash_ref_stays_a_distinct_equivalent_base_ref` | `b711c06` |
| FH-013 | `ForkPointInvariantTests.test_incomparable_maximal_forks_are_scoped_to_topic` | `b711c06`, `83913d9` |
| FH-014 | `SharedOwnershipTests.test_live_resolution_has_no_global_base_election_or_origin_head_probe` | `77ecbbf`, `bfa4157`, `76e8f97` |
| FH-015 | `MergeClaimInvariantTests.test_deleted_refs_keep_boundary_but_not_unproven_content` | `59a4d69`, `24bfd3c` |
| FH-016 | `MergeClaimInvariantTests.test_two_parent_multi_name_subject_does_not_relabel_side` | `59a4d69`, `24bfd3c` |
| FH-017 | `ForkPointInvariantTests.test_advancing_trunk_does_not_change_fork_point` | `b711c06`, `2a000c0` |
| FH-018 | `FindUnlinkedBehaviorCommitsTests.test_out_of_range_ambiguity_does_not_fail_release_linkage` | `d5da824`, `94ca3d4` |
| FH-019 | `SnapshotTests.test_terminated_ancestry_query_is_a_failure` | `8068f98`, `f6cfdb3` |
| FH-020 | `DeclarationSanityTests.test_no_reference_oracle_remains` | `f6cfdb3` |
| FH-021 | `ResolveIssueForCommitTests.test_trailer_resolution` | `8068f98` |
| FH-022 | `SnapshotTests.test_merge_base_rejects_empty_or_multitoken_success_output` | `8068f98`, `fd08636` |
| FH-023 | `ForkPointInvariantTests.test_snapshot_ref_movement_uses_captured_object_ids` | `b711c06` |
| FH-024 | `ForkPointInvariantTests.test_criss_cross_best_bases_fail_closed_as_ambiguous` | `b711c06` |
| FH-025 | `ForkPointInvariantTests.test_newer_comparable_candidate_is_the_unique_maximal_fork` | `b711c06` |
| FH-026 | `FailureHistoryTraceabilityTests.test_process_gate_records_terminal_exit_and_summary` | `2a000c0` and T08 terminal exit 0, 338 tests |
| FH-027 | `ResolveIssueForCommitTests.test_trailer_resolution` | `a4065f6` |
| FH-028 | `TopicDeltaTests.test_cached_topology_failure_reaches_membership_on_every_build` | `83913d9`, `414a81f` |
| FH-029 | `TopicDeltaTests.test_publication_recovery_ignores_unrelated_history_for_command_count` | `b2ddde6`, `db7aee8` |
| FH-030 | `SharedOwnershipTests.test_live_resolution_has_no_global_base_election_or_origin_head_probe` | `76e8f97` |
| FH-031 | `TestRangeProjection.test_live_range_projects_only_target_topic` | `380e23e`, `fd08636` |
| FH-032 | `DiagnosticProjectionTests.test_compatibility_errors_dedupe_in_first_seen_order` | `8221ea0` |

## T08 I2 Composite Traceability Override

The earlier single-test matrix remains as append-only RED evidence. For the
reviewed families below, this composite matrix is authoritative and every
qualified test is executed by
`FailureHistoryTraceabilityTests.test_every_failure_record_maps_to_executable_invariant_tests`.

| Failure | Executed composite invariant |
| --- | --- |
| FH-001 | commit-to-issue bare/indexed parity + issue-to-commits declared truth + empty issue-to-commits mutation |
| FH-007 | exact trailer/branch/merge-subject chain + both public call shapes + branch-first mutation |
| FH-014 | structured ref-inventory fatal projection + absence of a silent named fallback |
| FH-019 | snapshot sources + ordinary/failed/terminated/malformed Git results + bare/indexed call shapes |
| FH-020 | literal declaration coverage + ground truth + nonempty truth sanity + no oracle + metamorphic subject order |
| FH-026 | current T08 terminal evidence + exact-block-removal mutation |
| FH-027 | current snapshot fixture + real branch topology + structured consumer failure + consumer precedence |
| FH-032 | first-seen flat dedupe + structured octopus multiplicity + structured multi-name multiplicity |
| FH-033 | FH-001 literal truth + same-wrong mutation + FH-007/FH-026 mutations + canonical component-removal mutation |
| FH-034 | preserved FH-026 state + exact FH-033 remediation commit + qualified acceptance evidence |
| FH-035 | whitespace-tolerant current terminal evidence + exact-block-removal mutation |
| FH-036 | independent required manifest + exhaustive every-component deletion mutation |

## Required Design Traceability

The redesign maps its requirements to this corpus:

| Redesign requirement | Failure ids |
| --- | --- |
| One shared policy and projection path | FH-001, FH-007, FH-008 |
| Per-issue fork points | FH-002, FH-003, FH-006, FH-011, FH-017 |
| Stacked-issue exclusions | FH-005 |
| Ref identity and candidate equivalence | FH-012, FH-013, FH-014 |
| Graph-corroborated merge content | FH-004, FH-015, FH-016 |
| Historical issue registry and fail-closed commands | FH-009, FH-010 |
| Caller-scoped diagnostics | FH-018 |
| Independent invariant and boundary testing | FH-019, FH-020 |
| Complete consumer gates and successful-output validation | FH-021, FH-022 |
| Snapshot-time graph identity and complete fork candidates | FH-023, FH-024 |
| Executable ancestry-maximal selection proof | FH-025 |
| Terminal verification and migrated failure fixtures | FH-026, FH-027 |
| Live scoped-diagnostic preservation | FH-028 |
| History-independent graph command count | FH-029 |
| Removal of superseded compatibility policy | FH-030 |
| Complete topology with separate range projection | FH-031 |
| Stable flat compatibility messages over structured diagnostics | FH-032 |
| Mutation-sensitive executable invariant coverage | FH-033 |
| Append-only remediation evidence | FH-034 |
| Markdown-wrap-tolerant terminal evidence | FH-035 |
| Independently declared required-component completeness | FH-036 |

Future findings extend this table rather than replacing it.
