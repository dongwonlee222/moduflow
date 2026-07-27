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
| FH-002 | Branch containment was treated as authorship | Attribution uses branch contribution, never raw ancestry | superseded by redesign |
| FH-003 | Merged topic minus current main became empty | Historical fork evidence must survive later merges | superseded by redesign |
| FH-004 | Sync-merge direction attributed trunk content to a topic | Merge direction and content sides come from graph structure | regression captured |
| FH-005 | Nested merges leaked inner issue content into the outer issue | Content commits remain single-owner across stacked histories | superseded by redesign |
| FH-006 | A stale local default branch over-collected trunk commits | Base selection compares fork points, not preferred ref tips | open |
| FH-007 | Precedence worked in only one query direction | Apply precedence once after collecting all candidate claims | regression captured |
| FH-008 | Bare and indexed lookup had separate precedence paths | Bare and indexed lookup must project the same attribution result | regression captured |
| FH-009 | Checkout state and unknown branch tails changed the issue registry | Registered issue identity must be historical and fail closed | regression captured |
| FH-010 | Git query failures were flattened into empty attribution | Command failure is distinct from an ordinary negative result | regression captured |
| FH-011 | A disconnected non-issue ref became the repository base | Unrelated refs cannot change a topic's contribution | open |
| FH-012 | A local slash branch was mistaken for a remote counterpart | Ref identity uses full ref namespace and object identity | open |
| FH-013 | Same-tail refs on multiple remotes created false certainty | Equivalent refs collapse by object; distinct lineages stay distinct | open |
| FH-014 | `origin/HEAD` lookup failure was silently ignored | Default-ref discovery failures remain observable diagnostics | regression captured |
| FH-015 | Octopus subject order and deleted refs changed ownership | Subject token order cannot assign content without graph corroboration | open |
| FH-016 | Two-parent multi-name merge subjects relabelled side content | A merge boundary claim is not proof of content ownership | open |
| FH-017 | Normal trunk advancement was reported as base ambiguity | Advancing a base lineage cannot change the historical fork point | open |
| FH-018 | Unrelated historical ambiguity failed the current release | Diagnostics are projected to the caller's commit or issue scope | open |
| FH-019 | Stale fixtures masked shared-index regressions | Fixtures must reproduce each Git boundary and consumer call shape | regression captured |
| FH-020 | Reference oracle repeated implementation assumptions | Truth is declared independently and checked with invariants | superseded by redesign |
| FH-021 | A stricter ref parser broke an unrun consumer fixture | Every changed boundary runs all direct consumer suites before review | regression captured |
| FH-022 | Successful merge-base with empty output became “no base” | Success return codes still require structurally valid output | regression captured |

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
- **Status**: superseded by redesign.

### FH-003 — Current Main Tip Is Not a Historical Base

- **Topology**: a topic branch merged into main; both refs now contain the topic
  commits.
- **Observed failure**: `git rev-list <topic> --not main` returned zero.
- **Invalid assumption**: subtracting the current base tip reconstructs the
  branch's historical contribution.
- **Derived invariant**: contribution is anchored to a merge-base fork point,
  not current containment.
- **Evidence**: 2026-07-26 correction in `status.md`.
- **Status**: superseded by redesign.

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
- **Status**: superseded by redesign.

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
- **Status**: open until the fork-point redesign passes all gates.

### FH-007 — One-Direction Precedence

- **Topology**: a commit with `Issue: beta` sits on issue alpha's branch.
- **Observed failure**: commit-to-issue returned beta while issue-to-commits
  included the commit in both alpha and beta bundles.
- **Invalid assumption**: source precedence could be enforced separately in
  each query path.
- **Derived invariant**: collect candidate claims first, then apply
  `trailer > branch > merge-subject` exactly once.
- **Evidence**: R9-3; corrective commit `ef149a8`.
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
- **Status**: open until per-topic fork-point tests and full gates pass.

### FH-012 — Local Slash Branch Versus Remote Namespace

- **Topology**: a local branch name contains a slash and resembles a
  remote-tracking branch tail.
- **Observed failure**: tail-based comparison collapsed unrelated refs.
- **Invalid assumption**: display-name similarity establishes ref equivalence.
- **Derived invariant**: retain full ref namespace; collapse only refs proven
  equivalent by object identity and lineage.
- **Evidence**: independent review around corrective commit `4f5d14a`.
- **Status**: open under the redesign.

### FH-013 — Same Tail Across Multiple Remotes

- **Topology**: remote-only or local-plus-multiple-remote refs share a branch
  tail but point to equivalent or divergent commits.
- **Observed failure**: name-based matching either duplicated one lineage or
  merged distinct lineages.
- **Invalid assumption**: `<remote>/<tail>` names identify one logical ref.
- **Derived invariant**: identical object ids collapse; distinct fork evidence
  remains distinct and ambiguity is scoped to the affected topic.
- **Evidence**: final attribution review leading to `77ecbbf` and `bfa4157`.
- **Status**: open under the redesign.

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
- **Status**: open under the redesign.

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
- **Status**: open under the redesign.

### FH-017 — Trunk Advance After Topic Fork

- **Topology**: a topic forks from main, then main advances independently.
- **Observed failure**: the current main tip and topic tip became incomparable,
  so ordinary development was reported as ambiguous base selection.
- **Invalid assumption**: the base ref tip must remain an ancestor of the topic
  tip.
- **Derived invariant**: advancing a base lineage after fork does not change
  the topic's merge-base fork point or attribution.
- **Evidence**: final independent quality review at `bfa4157`.
- **Status**: open; primary redesign trigger.

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
- **Status**: open; primary redesign trigger.

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
- **Status**: regression captured.

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

Future findings extend this table rather than replacing it.
