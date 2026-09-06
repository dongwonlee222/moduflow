# ModuFlow Inbox

## 2026-06-11

- [handled] Multi-project users need project-local issue management, environment information, dashboards, knowledge artifacts, decisions, migration support, and portfolio views.

- [handled 2026-09-05] 2026-07-06 (user observation): dashboard issue DB buries the `active` status group mid-page under default sort (created_desc) because group order follows row-encounter order. Active group should always render first (active → review → blocked → backlog → done). Small UI fix in project_memory.py groupedRows/status ordering. Source: user couldn't find active issue 071 in the DB view.

## 2026-09-05

- (user requirement): work continues on a second computer and other people will use ModuFlow too. Cloning and continuing **alone** already works — everything is in git and `INSTALL.md` covers the plugin install. Two problems appear only when two people work at the same time.

- (blocker for concurrent work): `.moduflow/state.json` holds a single global `active_issue`, and it is tracked in git. Every lifecycle transition writes it and `workspace/loop-state.json` — both were transaction targets when issues 086 and 119 were completed on 2026-09-05. Two people working at once each write their own issue id into the same field and conflict on every transition; a mis-resolved conflict silently discards the other person's state. "What I am working on right now" is per-person and does not belong in a shared file. Note before designing anything new: `workflow/team-state.json` (issues 005/035) already carries `owner`, `assignee`, `reviewer`, `branch`, `pr`, `lock_state` and `locked_by` per issue. Whether that lock is actually enforced against a transition was **not** checked — check that first, because if it is, this problem is smaller than it looks.

  **Update 2026-09-06 — lock 확인 및 Beads v1.2.2 격리 실측.**
  Source: ModuFlow의 실제 전이 함수를 임시 프로젝트에서 호출한 재현 시험 + 공식
  Beads macOS ARM64 v1.2.2 바이너리(공식 SHA-256 일치)를 별도 Git 저장소에서
  실행한 비교 시험. Owner: Dongwon Lee. Confidence: high for the tested local
  single-checkout behavior; unverified for multi-machine/server operation.

  확인 결과 `team-state.json`의 lock은 전이에 강제되지 않는다. 같은 이슈를 먼저
  Minsu가 시작하고 이어 Jisu가 시작하자 두 번째 전이가 성공하면서 `assignee`와
  `locked_by`가 Jisu로 조용히 덮어써졌다. 따라서 기존 메모의 미확인 가정은
  **미강제**로 확정됐고, 문제 범위는 단순 표시 드리프트가 아니라 이중 실행을 허용하는
  상태 모델 결함이다.

  같은 시나리오를 Beads에서 실행한 결과는 달랐다.

  1. `bd update <id> --claim`을 Minsu/Jisu가 동시에 호출하자 Minsu 한 명만
     `in_progress`로 선점했고 Jisu는 `issue already claimed by Minsu`로 실패했다.
  2. 세 선행 이슈를 blocker로 둔 회귀 테스트는 `bd ready`에서 제외됐고, 세 이슈를
     닫은 직후 자동으로 ready가 됐다. `bd ready --claim --exclude-type epic`은 다음
     작업 하나를 Jisu에게 원자적으로 배정했다.
  3. `bd remember`로 저장한 프로젝트 원칙은 다음 `bd prime --memories-only`에서
     실제로 주입됐다.
  4. 다만 기본 embedded 모드는 로컬 Dolt DB이며, JSONL은 교환용일 뿐 원본이나
     백업이 아니다. 여러 PC/worktree의 진짜 팀 운영은 Dolt remote/server와
     push/pull을 별도로 검증해야 한다. “설치만 하면 다인 동시성이 해결된다”는 결론은
     아직 성립하지 않는다.
  5. 제품 성숙도 경고도 있었다. 쓰기 권한이 없는 `~/.dolt` 초기화 실패가 정상 오류가
     아니라 panic으로 끝났고, embedded 모드에서 `bd doctor`는 미지원이다. `bd ready`
     기본 결과에는 epic도 포함돼 실행 에이전트가 `--exclude-type epic` 같은 정책을
     갖춰야 한다. 최신 v1.2.2는 실수로 배포된 1.2.0/1.2.1을 검증된 1.1 계열로
     되돌린 recovery release라서, work leases·events journal·HTTP API 등 1.2 전용
     기능은 현재 릴리스에 없다.

  개선 방향은 **전면 교체가 아니라 경계가 분명한 shadow pilot**이다.

  - Beads 후보 소유권: issue identity, dependency graph, ready query, atomic claim,
    assignee/status history.
  - ModuFlow 잔존 소유권: goal, opportunity, spec/AC, decision, evidence, review/release
    gates, stakeholder reporting.
  - `.moduflow/state.json.active_issue`는 공유 SSoT에서 제거하고 작업자 로컬 또는
    Beads의 claim 결과에서 파생한다. `team-state.json`도 직접 쓰는 lock 저장소가
    아니라 이슈 엔진에서 생성하는 projection으로 낮춘다.
  - issue 112의 backend boundary에서만 Beads를 호출하고, ModuFlow 안에 별도
    scheduler/queue/lock 상태기를 또 만들지 않는다.
  - 실제 ModuFlow 이슈 전체를 옮기기 전에 active/backlog 10건만 양쪽에 병행해
    ID 매핑, close/reopen, dependency, worktree, 두 컴퓨터 push/pull, 장애 복구를
    검증한다. 통과 기준에는 무손실 왕복, 중복 선점 0건, silent overwrite 0건,
    rollback 가능성을 포함한다.
  - v1.2.2 recovery-release 안정성과 remote 운영비가 기준을 통과하지 못하면,
    Beads 채택 없이도 동일 원칙(원자적 claim, 복수 active, derived projection)을
    ModuFlow에 최소 구현한다.

  `retrieval_trigger`: re-read when working on issue 112, multi-user concurrency,
  active-issue state, team-state locks, issue-engine adapters, or any Beads adoption
  decision.
  Suggested routing: `product:opportunity` for the Beads/native boundary decision,
  then attach the selected implementation to issue 112 or a narrowly scoped successor;
  do not create a second orchestration runtime.

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

- **Non-Latin titles collapse the generated filename.** `project_knowledge.py --kind
  benchmark --title "해외 4곳은 충전소 선택을 어떻게 푸는가"` wrote
  `knowledge/benchmarks/2026-09-06-4.md` — the slug kept only the one ASCII character
  in the title. Every Korean-titled artifact created on the same day therefore
  collides on `<date>-<digit>` or produces a name that says nothing. `ls
  knowledge/benchmarks/` is unreadable as an index, which matters because that
  directory listing is the cheapest way to see what has already been researched.
  Content search still finds them, so this is a browsability bug, not a data-loss
  one. Options: transliterate, keep the original characters (paths handle UTF-8
  fine), or fall back to a short hash plus the title in frontmatter — anything but
  silently dropping the title. Worth checking `--kind decision` in
  `project_memory.py` too: that one produced `2026-09-06-m190.md` from
  "원장을 M190 에서 동결하고…", i.e. the same rule, and it only looked reasonable
  because the title happened to contain "M190".

- **A project cannot declare its own completion gate.** Every check ModuFlow ships is
  *generic* — issue schema fields, artifact registry fields, doctor structure. There
  is no place to say "in this project, an issue may not be closed until its
  documentation impact is resolved". `product:review` is intake for external reviews
  (SARIF/CodeQL/human) recorded as evidence, not a per-project exit gate.

  Observed 2026-09-06: this project needs three rules ModuFlow has no slot for —
  every issue must carry a `## Docs Impact` section; closing as `done` requires that
  section to show resolution rather than intent; measured constants in code must
  resolve to a ledger id. All three ended up enforced as **unit tests**, which works
  but is a workaround: the rules live in `tests/`, invisible to `doctor`, and a
  newcomer reading the ModuFlow artifacts would not know they exist.

  A modest shape: let `.moduflow/config.json` name project-local gate scripts (or
  required issue sections) that `doctor` runs alongside its own checks, so the
  project's rules appear in the same report as the built-in ones. The pieces exist —
  `project_issue_schema.py` already validates section structure, and `doctor`
  already aggregates diagnostics from several modules.

  Related to the adoption entry above: a project adopting ModuFlow usually *already
  has* rules, written in a CONTRIBUTING or CLAUDE.md. Right now those stay outside
  the tool entirely.

- **A fully Korean project reports `korean descriptions 0/8`.** On a project whose
  issues are written entirely in Korean — titles, summaries, scope, acceptance
  criteria — `project_doctor.korean_description_coverage` counts zero, and every row
  in the dashboard gets a `한글 없음` badge. The resolution path only consults
  `specs/<id>/*.ko.md` sidecars and the legacy `workspace/issue-descriptions.ko.json`;
  a project that has not created specs scores 0 no matter how the issues are
  actually written. The dashboard then renders the Korean summary **and** the
  "no Korean" badge next to each other, which reads as a bug to the user even
  though the check is informational-only by design (C9).

  For a Korean-first tool this is the wrong default: the common case is that the
  issue body already *is* the Korean description. Detecting Korean text in the
  issue's own summary before falling back to sidecars would make the number mean
  what its name says. As it stands the metric measures "has spec sidecars", not
  "has Korean".

- **`evaluate_auto_checks()` is implemented and never called.**
  `scripts/project_production.py:213` parses a playbook's `[auto]` required checks
  and evaluates the three rule forms (`section:`, `forbidden:`, `approved-copy:`)
  against a document. A grep across `scripts/` for the function name returns only
  its own definition — nothing invokes it. So a playbook author writes
  `CHK001 [auto] section:측정 조건`, reasonably expects that to be enforced, and
  nothing happens. The `[auto]` / `[review]` distinction currently has no runtime
  meaning: both are prose.

  This matters more than a normal dead function because the playbook mechanism's
  whole pitch is "select a playbook and the required checks are filled in
  automatically". The checks are filled in; they are just never run. Wiring it into
  whatever validates an analysis run (or into `doctor` for projects that have
  playbooks) would make `[auto]` mean what it says.

  Reproduced by adopting it on a real project 2026-09-06: wrote a playbook with five
  `[auto]` checks, then wrote an analysis document that violated two of them — no
  error from any ModuFlow command. Ended up re-implementing the evaluator as a unit
  test in the project (`tests/test_docs.py`, ~70 lines) to get the behaviour the
  playbook already described.

  Two smaller things found in the same pass:
  - `process_ref_kind` accepts only `skill`, `document`, `none`. A playbook whose
    process is a **script** has no honest value — `document` is the least wrong.
  - The seven required sections are reported **one at a time** (`missing section: X`),
    so authoring a playbook from scratch takes five failed attempts to discover the
    full list. Report them all at once.

- **Reduce the visible command/skill surface and make it bilingual, Korean-first.** Confirmed
  with the user on 2026-09-06 after benchmarking Anthropic Skills, Claude Code's
  invocation controls, OpenAI's skill-authoring guidance, Superpowers and Basic
  Memory. ModuFlow 0.3.67 currently exposes 41 source commands, 11 top-level skills
  and 27 generated Codex `source-command-product-*` skills. English descriptions
  and internal terms make the working `/` palette difficult to scan.

  The user explicitly rejected shorthand such as `/product:d`, `/product:m` and
  `/product:rev`; those abbreviations create another language to memorize. The
  primary interaction should be one remembered entry point followed by ordinary
  Korean **or English**, with both forms routed identically: `/moduflow 결정으로
  남겨줘: ...` / `/moduflow record this decision: ...`, `/moduflow 비교해줘:
  ...` / `/moduflow compare ...`, `/moduflow 기억해줘: ...` / `/moduflow
  remember: ...`, `/moduflow 전에 뭐로 정했지?` / `/moduflow what did we
  decide?`, `/moduflow 다음에 뭐 하면 돼?` / `/moduflow what should I do
  next?`.

  Proposed visible allowlist: `/moduflow` plus `product:inbox`, `product:issue`,
  `product:decision`, `product:benchmark`, `product:memory`, `product:status`,
  `product:loop`, `product:execute`, `product:review` and `product:release`. Give
  each one a short Korean-first bilingual action label, plain descriptions and
  realistic Korean and English examples. Keep knowledge/evidence/research/report/promote, workflow plumbing,
  advanced administration, bridges, routers, policies and duplicate generated
  source-command skills internal while preserving their behavior through the hub.

  `product:decision` must accept one sentence from the human. Infer issue, reason,
  alternatives and supporting context from the conversation and project; ask only
  `이 선택을 한 가장 큰 이유가 무엇이었나요?` when the reason is genuinely
  absent. In user-facing output translate internal schema terms: rationale → `왜
  이렇게 정했나요?`, alternatives → `다른 선택은 무엇이었나요?`, caveats →
  `조심할 점이 있나요?`, retrieval_trigger → `언제 다시 살펴보면 될까요?`.

  Memory routing follows the user's words rather than exposing folders, and each
  Korean/English pair is equivalent: `메모해줘`/`note this` → inbox,
  `기억해줘`/`remember this` → durable memory, `정했어`/`we decided` →
  decision, `비교해줘`/`compare` → benchmark, `찾아줘`/`find` → cross-record
  search. Meetings, references and knowledge remain storage details.

  Full benchmark and acceptance criteria:
  `knowledge/benchmarks/2026-09-06-agent-skill-discoverability-and-bilingual-command-surface.md`.
