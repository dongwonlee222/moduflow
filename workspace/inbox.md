# ModuFlow Inbox

## 2026-06-11

- [handled] Multi-project users need project-local issue management, environment information, dashboards, knowledge artifacts, decisions, migration support, and portfolio views.

- [handled 2026-09-05] 2026-07-06 (user observation): dashboard issue DB buries the `active` status group mid-page under default sort (created_desc) because group order follows row-encounter order. Active group should always render first (active → review → blocked → backlog → done). Small UI fix in project_memory.py groupedRows/status ordering. Source: user couldn't find active issue 071 in the DB view.

## 2026-09-05

- (user requirement): work continues on a second computer and other people will use ModuFlow too. Cloning and continuing **alone** already works — everything is in git and `INSTALL.md` covers the plugin install. Two problems appear only when two people work at the same time.

- (blocker for concurrent work): `.moduflow/state.json` holds a single global `active_issue`, and it is tracked in git. Every lifecycle transition writes it and `workspace/loop-state.json` — both were transaction targets when issues 086 and 119 were completed on 2026-09-05. Two people working at once each write their own issue id into the same field and conflict on every transition; a mis-resolved conflict silently discards the other person's state. "What I am working on right now" is per-person and does not belong in a shared file. Note before designing anything new: `workflow/team-state.json` (issues 005/035) already carries `owner`, `assignee`, `reviewer`, `branch`, `pr`, `lock_state` and `locked_by` per issue. Whether that lock is actually enforced against a transition was **not** checked — check that first, because if it is, this problem is smaller than it looks.

- **Missing primitive: numeric ledger + retraction propagation.** Source: real-world audit of a grant-application project (33 docs, 187 measurements, deadline-driven) run on 2026-09-05. ModuFlow tracks *"is the task done"*; that project needed *"is the sentence I wrote still true"*. Issue state moves forward (todo→doing→done); evidence moves backward — when a server-cost assumption (600k KRW/mo) was replaced by a measurement (80k KRW/mo, ledger id M173), the already-`done` break-even figure (4,706 users) silently went stale in **four** documents, and a retracted metric survived in one doc after being removed from another. 14 instances of the same class in one audit.

  What is missing (verified against this repo on 2026-09-05):
  1. **No artifact to hold a measured value.** Artifacts are issue/spec/plan/decision/knowledge/memory. `knowledge/data-notes/` is a document folder, not a record schema for `{id, value, grade A/B/C/D, source, measured_at}`.
  2. **No citation edge.** `linkage_check.py` links commits↔issues only. There is no way to record "document X's break-even cites M173".
  3. **No reverse query.** `product:evidence` does forward search/summary (issue → evidence). It cannot answer "if M173 changes, what breaks".
  4. **No invalidation state.** Issues have open/closed. A *value* needs `retracted|superseded` + reason + replacement (e.g. 28% retracted by M109, replaced with 0.93x/4.2x).
  5. **`product:converge` is code-only.** Its shape is already right — AC/GC ↔ evidence bundle ↔ independent judge, non-blocking, re-runnable forever. But `project_converge.py` collects git commits as the only evidence source.

  Proposal: do not build a new tool. Widen converge's two slots — AC/GC → *claims*, commit evidence → *numeric ledger*. A working reference implementation already exists by hand in that project (M1~M187 with values, grades, and sources), which is ahead of the current evidence layer.

  **Update 2026-09-05 (same project, deeper audit — ledger now M1~M190).** Three more
  failure modes surfaced, all of them about the *record* rather than the propagation.
  They tell you which fields and gates the `measurement` artifact needs.

  6. **A constant can live in code for twelve months without ever being registered.**
     Two shrinkage baselines (`BASE_RATE` / `BASE_FAIL`, both 0.0275) entered on the
     repository's **first commit** with no ledger id. The commit message said
     "national baseline 2.75%"; the ledger prose said **2.80%**; neither carried a
     formula. Three candidate denominators were measured and **none reproduced
     either number**. Meanwhile three sibling constants from the same commit *were*
     registered with formulas (M17/M18/M19) — so this is not missing discipline,
     it is a missing check. The value was load-bearing: 92.7% of stations have zero
     observed faults, so the displayed "success probability" is mostly that constant.
  7. **A measurement without a reproduce command becomes unverifiable within days.**
     One entry justified a timeout change with "no destination loss across 12
     national points". Re-measured 5 days later on an island point: 7 → 5 destinations,
     i.e. the claim held only inside that sample. **Which 12 points were used is now
     unknown** — the entry never recorded a command. 12 of 34 section-style entries
     have no reproduce command.
  8. **A reference can point at something that is not an entry.** A new measurement
     was written as a *sub-heading inside another entry* rather than its own entry.
     Code then cited it by id, and nothing would have caught that the id did not
     resolve.

  Ledger shape, measured (useful if you write a parser):
  - 4,034 lines / 122KB, ids M1~M190, **no gaps**
  - **two incompatible notations**: 159 table rows (`| id | name | value | formula | grade |`)
    and 34 prose sections (`## id — title` + evidence + reproduce). A parser must read both.
  - grades: A 127 / B 27 / C 1 / **4 with none**
  - 49 intra-ledger id references across 31 targets — *the citation graph already exists,
    it is just not machine-readable*
  - 73 occurrences of retract/wrong/strikethrough/correction wording — **revision is the
    normal case, not the exception**
  - the code side cites 78 distinct ids across 41 source files, and that list exists nowhere

  So the artifact needs `reproduce` as a **required** field (not optional), and the
  layer needs two gates: *every registered id resolves to a real entry*, and *every
  measured constant in code is registered*.

  **A minimal reference implementation of the second gate now exists** in that project
  as a unit test: measured constants are enumerated, each must carry an id in its
  comment block or appear in an `UNREGISTERED` map with a written reason, that map must
  not grow, and every cited id must resolve in the ledger file. Verified by mutation in
  both directions. Two notes from building it: separate **measured** values from
  **chosen** knobs (shrinkage strength, gates, thresholds are not ledger material), and
  keep the failure message short — an assertion that dumps the ledger for context
  produced a 209KB failure log, which then gets piped into a notification channel.

  `retrieval_trigger`: re-read when working on evidence/knowledge layer, converge scope, or any request about tracking whether written claims remain valid.
  Suggested routing: `product:opportunity` (product shaping) — this is not obvious implementation work yet.

- (needed once other people join): the GitHub mirror shows 10 of 122 issues, so someone who looks at GitHub before cloning reads this as a ten-issue project. Three issues that were done locally were still open there (#27/086, #23/093, #21/091) and were closed by hand on 2026-09-05 with a comment. They drifted because nothing runs the sync: `commands/product-issue.md` says projection happens only on explicit request, never automatically. And `scripts/project_github_issues.py` only does `gh issue create` / `edit` / `label` — it has **no close path at all**, so completion cannot be mirrored even on request. Deciding when sync runs means changing the "never automatically" rule, which is a human decision.

## Handled

- 2026-09-05: the `active` group ordering fix landed in `groupedRows`
  (`scripts/project_memory.py`). Verified in a browser, not only by markers.
- 2026-09-05: the 2026-06-11 multi-project note is covered by Issues 102
  (registry/resolver), 086 (project-aware dashboard), 004/036 (portfolio
  workspace and summary) and 118 (portfolio-mode dashboard). Entries are
  marked in place rather than removed so the original wording survives.

- **Bug: `product:migrate` writes a dashboard its own stop hook rejects.** Reproduced
  2026-09-05 on a fresh overlay migration. `scripts/project_migrate.py --mode overlay
  --write` creates `workspace/dashboard.md` containing only `# Dashboard`. The stop
  hook then calls `project_lifecycle.render_dashboard_projection`
  (`scripts/project_lifecycle.py:157`), which does:

  ```python
  pattern = re.compile(r"^##\s+Active Issue\s*$.*?(?=^##\s|\Z)", re.M | re.S)
  if not pattern.search(text):
      raise ValueError("dashboard requires an Active Issue section")
  ```

  So **every session end fails** with a traceback in `.moduflow/logs/hooks.log`.
  Before an issue exists the failure is `ISSUE_RECONCILE_OWNER_UNAVAILABLE`; after
  creating one it becomes this ValueError, so a new adopter hits two different
  errors in a row and neither names the actual fix (add two lines to the file).
  Fix: give the migration's dashboard template the `## Active Issue` section that
  the projection requires. Worth checking `render_roadmap_projection` for the same
  class of mismatch. Note the log line is truncated mid-traceback, which hid the
  exception type — the log writer's length cap should keep the tail, not the head.

- **`product:impact <id>` — reverse lookup. The edges are already stored; the query
  is not.** Verified 2026-09-05 by reading the code, not by name:
  `commands/product-evidence.md` is a 21-line natural-language instruction with **no
  script at all** ("search memory and knowledge for matching issue ID"), and
  `project_converge.py` runs the other direction (`collect_evidence()` at 281 takes
  one issue → its commits/AC). Closest existing pieces, all partial:
  `project_memory.search_memory_entries(issue_id=…)` (636) filters on frontmatter
  exact match only; `_issue_linked_memory()` (1009) actually builds an issue→memory
  map but is render-only with no CLI; `generate_memory_graph()` (799) draws
  `references`/`depends_on`/`supersedes` edges as Mermaid but nothing traverses them
  to answer "what points at X". A grep for `backlink|referenced_by|cited_by|inbound|
  dependents|reverse_|impact` returns only unrelated hits.
  What this cost in the field: one measurement changed (assumed server cost →
  measured), and finding the four documents whose break-even figure stood on it was
  done by hand, a day late. The primitive needed is a traversal layer plus CLI
  exposure over edges that are already parsed.

- **Extend the `canonical_path_guard` pattern to the target project's own source.**
  `scripts/canonical_path_guard.py` already implements exactly the check needed —
  AST-walk source, collect literals, diff against a registry, and report
  **unclassified** (in code, not registered) / **prohibited** / **stale** (registered,
  no longer in code) / duplicate. It is the right shape. Two limits: it scans
  `root/"scripts"` for *ModuFlow's own* canonical folder names, so on an adopting
  project there is nothing to scan; and it is wired only into `release_check.py`
  (382-391), not `product:doctor`. Generalising it means new collection rules
  (which literals count as "a value that must be registered") and diffing against
  `artifacts.md` instead of `config/canonical-path-literals.json`.
  ⚠️ `doctor` and `release_check` are deliberately split by
  `runtime_provenance.inspect_validation_target(requested_role=…)` — "project" vs
  "source". Moving the guard as-is would be a no-op; the role boundary has to be
  part of the design.
  A minimal reference implementation exists in the field project as a unit test:
  measured constants are enumerated, each must carry a ledger id in its comment
  block or sit in an `UNREGISTERED` map with a written reason, the map must not
  grow, and every cited id must resolve. Verified by mutation in both directions.
  It does **not** catch `stale`, which the path guard does — that direction is worth
  keeping.

- (smaller findings from the same 2026-09-05 audit, no action implied)
  `knowledge/index.md` and `memory/index.md` are static template strings
  (`project_knowledge.py:34 INDEX_CONTENT` — empty `## Decisions / ## Benchmarks`
  headings) written once by `write_text_if_missing`; nothing ever fills them, so
  "index" is a promise the code does not keep. And
  `project_artifact_registry.py` states in its docstring that it does no source
  crawling — registration is one entry at a time — which is consistent, but it
  means the registry is empty unless someone registers by hand: running doctor on
  the ModuFlow repo itself reports `artifact_registry.initialized=False, total=0`.

- **Adopting an existing project takes six undocumented steps, and two of them fail
  silently.** Walked end-to-end on 2026-09-06 with a real project (~4k-line codebase,
  190 measurements, hard deadline). What `product:migrate --mode overlay --write`
  leaves you with is not yet a working setup:

  1. migrate writes a dashboard the stop hook rejects (fixed in `83f95c5`)
  2. with zero issues the hook fails `ISSUE_RECONCILE_OWNER_UNAVAILABLE` every session
  3. creating an issue is not enough — registering anything in the artifact registry
     also needs `product:knowledge --write` first, and the error for that is
     `KNOWLEDGE_REQUEST_INVALID: Check metadata, owning issue and initialized
     transaction prerequisites` — which does not name the missing step
  4. `workspace/goal.md` stays `Objective: TBD`, so the SessionStart banner repeats
     `product:status` with nothing behind it
  5. writing eight issues does not populate `state.json`; `active_issue` stays `""`
  6. **`Status: in_progress` is silently ignored.** `project_issue_schema.py` tells the
     user "Set status to backlog, in_progress, or done" (lines 941, 955), but
     `--sync` only resolves an active issue when the file says `Status: active` —
     with `in_progress` it returns `{"active": "", "phase": "select"}` and **no
     diagnostic at all**. Validation still reports `valid: True`. The vocabulary the
     schema recommends and the vocabulary lifecycle resolves are different sets.

  Item 6 is the one to fix first — it is a silent no-op on the value the tool itself
  recommends. Items 2-5 are sequencing: either `--write` should carry the adopter to
  a usable state, or the migration plan output should print the remaining ordered
  steps rather than leaving each to be discovered by hitting its error.

  Worth considering for adoption specifically: an existing project usually already
  states its objective somewhere (README, deadline in docs, recent commits). Seeding
  `goal.md` with a draft from that material — clearly marked as a draft — would beat
  `TBD`, because `TBD` makes the SessionStart banner worthless from day one, which is
  exactly when a new adopter is deciding whether the tool is worth keeping.

- **Nothing writes to `memory/` on its own — the layer is a filing cabinet with no
  hands.** Observed 2026-09-06 while adopting the tool on a real project. `memory/`
  is well shaped for exactly what a project needs to remember: `decisions/`,
  `meetings/`, `deliverables/`, `evidence/`, `releases/`, `notes/`, `references/`,
  and the decision record has the right fields — `alternatives` (what was given up)
  and `reversal_conditions` (when to revisit) are the two people always skip, and
  they are in the schema. `--search <query>` does hit summary and body text, so
  retrieval works better than the frontmatter-only filters suggest.

  But **entries only exist if someone runs `project_memory.py --kind … --title …`.**
  The stop hook watches `issues/*.md` and syncs lifecycle; it never looks at the
  session. So the layer captures nothing unless the operator remembers to file —
  and the moment you need it most (a long working session where four decisions got
  made in conversation) is exactly when nobody stops to file.

  Concretely, in one day this project decided: freeze the 190-entry ledger, stop
  minting new measurement ids, do not split the file, and skip the remote. All four
  lived only in chat until asked about; two were partially recoverable from commit
  messages, two were not recorded anywhere.

  This is the same failure the ledger had: *writing the rule down and having the rule
  run are different things* — which is why the measurement side ended up enforced by
  a unit test rather than by discipline. Decisions cannot be checked the same way,
  but the gap is worth naming. Options, roughly in increasing cost: (a) have
  `product:decision` be routinely suggested by the loop when a phase transition
  happens, (b) let the stop hook notice that issue files changed *and* the session
  was long, and drop a `.candidates/` stub with the diff summary for later promotion —
  `.candidates/` and the "미승격 레코드 n건" line in the SessionStart banner already
  exist for this shape, they are just never populated, (c) full session capture,
  which is probably the wrong trade.

  The `.candidates/` + banner pairing is the interesting one: the plumbing is already
  built and wired into the banner, and nothing feeds it.

- **No index of which script owns what.** 54 scripts, 42,784 lines, and the only
  navigational documents are `docs/architecture.md` (84 lines: Layers, Rule,
  Project Resolution, Transaction Boundary, Artifact Tree) and `AGENTS.md`
  (66 lines, and it is an output-format convention, not a map). Nothing answers
  "which file owns lifecycle drift" without grep.

  Filed here rather than as an issue deliberately: the honest evidence is *weaker*
  than it sounds. Issues 122, 123 and 125 were all written with correct
  `file:line` entry points, so location was not the bottleneck on any of them.
  The one issue that recorded a wrong cause (126) did so because the transaction
  discarded its error list — a tool that knew and did not say, not a codebase
  nobody could navigate. Building a code map would not have prevented it.

  So this is worth doing for onboarding and for anyone who is not the author, and
  is not worth doing as a fix for the 2026-09-05 failures. Two candidate shapes,
  both cheap: per-directory `CODEMAP.md` files listing what each script owns
  (static, drifts), or a generated index keyed off the module docstrings that
  already exist (stays true, needs the docstrings to be honest). Prefer the
  second if the docstrings turn out to be present; check before deciding.
