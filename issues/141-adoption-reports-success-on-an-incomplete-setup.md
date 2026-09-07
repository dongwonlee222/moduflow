# Issue 141: Adoption Reports Success on an Incomplete Setup

**Status: backlog** — created 2026-09-06.
**Priority: p0**

## 요약

이미 돌아가고 있던 프로젝트를 모두의플로로 들여올 때 `product:migrate --write`는
"14개 만들었다"고 성공을 알립니다. 그런데 그 14개 중 **5개는 빈 폴더라서 git이
기억하지 못합니다.** 커밋하고 다른 컴퓨터에서 clone 하면 `issues/`와 `specs/`가
사라지고, 필수 항목이 없다며 진단이 실패합니다. 게다가 그 프로젝트는 **포트폴리오
목록에 등록되지 않고**(등록해 주는 명령이 아예 없습니다), 이미 있던 `TASKS.md`의
미완료 항목들은 **가져오지도, 남았다고 알려주지도 않습니다.**

## Summary

`product:migrate --write` is the documented path for adopting a project that
already exists (`README.md:179-183`, `commands/product-migrate.md`). On a
realistic in-flight repository it exits 0 and reports fourteen written paths.
Three of the things a person would assume that success means are not true:

1. Five of the fourteen are bare directories. Git does not track a directory, so
   the adoption does not survive a clone — and two of the five are *required*
   artifacts.
2. The project is not entered into the registry, and no command in the product
   can enter it.
3. The work already in flight in the repository is neither imported nor
   mentioned.

The command is honest about what it wrote. It is the definition of "set up" that
is short.

## Source

- Type: owner defect report, 2026-09-06 — "이미 하고 있던 프로젝트를 모두의플로로
  마이그레이션 할때 잘 세팅이 안되는거 같은데"
- Owner / decision maker: Dongwon Lee
- Reproduced against a purpose-built fixture: a 4-commit repository on a
  non-`main` default branch (`develop`) with no remote, carrying `README.md`,
  `src/`, `docs/`, `.github/workflows/`, `CLAUDE.md`, `AGENTS.md`, and a
  `TASKS.md` with three open items.

## 안 고치면

기존 프로젝트를 들여오면 clone 후 깨집니다. 사장님이 신고하셨습니다. — 맥락

## Opportunity

Three defects, each reproduced. Everything below is command output from that
fixture.

### 1. Five of the fourteen written paths are invisible to Git

`apply_migration_plan` creates the PM directories with `write_dir_if_missing`
(`scripts/project_migrate.py:208-212`), called for each of
`MINIMAL_PM_DIRECTORIES` (`:29`) at `:228-231`. Nothing is placed inside them.

```
$ python3 scripts/project_migrate.py <fixture> --mode overlay --write
exit=0
written: [".moduflow/config.json", ".moduflow/state.json",
          "issues", "specs", "knowledge", "memory", "workflow",
          "workspace/inbox.md", "workspace/opportunities.md",
          "workspace/roadmap.md", "workspace/dashboard.md",
          "workspace/goal.md", "workspace/transactions/.gitkeep",
          "workspace/loop-state.json"]
```

```
$ git add -A && git status --porcelain
A  .moduflow/config.json
A  .moduflow/state.json
A  workspace/dashboard.md
A  workspace/goal.md
A  workspace/inbox.md
A  workspace/loop-state.json
A  workspace/opportunities.md
A  workspace/roadmap.md
A  workspace/transactions/.gitkeep

$ git diff --cached --name-only | grep -E '^(issues|specs|knowledge|memory|workflow)/'
NONE — no file under any of the five directories is staged
```

Doctor passes on the machine that ran the migration:

```
$ python3 scripts/project_doctor.py <fixture>     # after --write
exit=0   moduflow.initialized: True   schema_gates.valid: True
```

Then the adoption is committed and cloned, which is the point of a git-native
product:

```
$ git commit -m "chore: adopt ModuFlow (product:migrate --write)" && git clone <fixture> clone
$ python3 scripts/project_doctor.py clone
exit=1
moduflow.initialized: False
moduflow.missing: ['issues', 'specs']
schema_gates.valid: False
schema_gates.errors:
  - Missing required project artifact: issues
  - Missing required project artifact: specs

$ python3 scripts/validate_project_artifacts.py clone
"valid": false,
"errors": ["Missing required project artifact: issues",
           "Missing required project artifact: specs"]
```

`issues` and `specs` are appended to the required list at
`scripts/validate_project_artifacts.py:465-467`, so this is not an optional
warning — it is the gate. A teammate, a CI runner, or the owner on a second
machine gets a project that ModuFlow declares broken, having done nothing but
clone what the migration itself wrote.

This exact bug was already found once, and fixed for one directory only.
`specs/103-atomic-lifecycle-state-transaction/review.md:8` records it: "Test
fixtures pre-created `workspace/transactions`, but an initialized real project
did not. Migration now creates and tracks `workspace/transactions/.gitkeep`."
That is the same failure — a directory the tool needs, present in the fixture,
absent in a real project — diagnosed correctly and repaired one directory wide.
`transactions/.gitkeep` (`scripts/project_migrate.py:44`) is the only `.gitkeep`
the migration writes, and it sits sixteen lines above the five directories that
still do not get one.

`.gitignore:22-25` states the rule in the plainest terms available: "The
directory itself must stay tracked via `.gitkeep`:
`project_lifecycle_transaction.py:6232` refuses to plan with
`PLAN_ARTIFACT_PREREQUISITE_MISSING` when it is absent."

This repository practises what adoption does not give away. It carries nine
`.gitkeep` files of its own — `specs/`, `memory/.candidates/`, and all six
`knowledge/` subdirectories — none of which `project_migrate.py` creates. The
dogfooding project has the placeholders; the projects it onboards do not.

### 2. The adopted project is never registered, and nothing can register it

`build_migration_plan` and `apply_migration_plan` resolve context through
`project_registry.project_context_for_root` (`scripts/project_migrate.py:54`,
`:171`, `:217`), which is the explicit-root compatibility path
(`scripts/project_registry.py:764-794`) — it synthesises a context from the
directory and writes nothing. No line in `scripts/project_migrate.py` touches
`projects.json`.

Nor can the user fix that afterwards. `project_portfolio.py` creates the registry
**empty** (`scripts/project_portfolio.py:14-18`, `"projects": []`) and its only
operations are `--write`, `--render`, `--resolve`, and `--select`
(`:286-289`). `--select` requires the project to already be there:

```
$ python3 scripts/project_portfolio.py <portfolio> --select legacy-app
{"status": "error", "message": "project is not registered: legacy-app"}
```

(`scripts/project_registry.py:937`.)

There is no `--add`, no `--register`, and no `product:*` command that appends a
project. The live registry at `~/projects/.portfolio/projects.json` holds three
projects on schema `moduflow.projects.v1` while the resolver's canonical is
`moduflow.projects.v2` — consistent with a file that has only ever been
hand-edited. So a freshly adopted project is absent from `product:projects`,
`product:weekly`, and the portfolio dashboard until someone edits JSON by hand.

### 3. Work already in flight is not imported, and the user is not told

`discover_candidate_paths` (`scripts/project_doctor.py:260-269`) matches only the
directory names in `CANDIDATE_PATHS` (`:65-74`). That table contains no
`TASKS.md`, `TODO.md`, `AGENTS.md`, or `CLAUDE.md` — it cannot see a file.

The fixture's `TASKS.md` carries three unchecked items and `TODO.md` two more:

```
$ python3 scripts/project_migrate.py <fixture> --mode overlay
candidates: {}

$ grep -c -i "TASKS\|TODO\|AGENTS\|CLAUDE.md" plan.json
0
$ grep -c -i "TASKS.md\|TODO.md\|AGENTS.md" doctor.json
0
```

Neither the plan nor the doctor report names them once. `workspace/inbox.md` is
written as `# Inbox\n\n` (`scripts/project_migrate.py:32`) and the loop then
recommends `product:goal` against an empty backlog, in a repository whose open
work is sitting in a tracked file two directories up. Not importing is a
defensible default — the migration promises not to touch existing files. Not
*saying so* is the defect: the person believes their project came across.

### Why these three belong together

Each one is the same shape: the adoption succeeded at the step it measured and
did not check the thing the user meant. `product:start` makes it worse rather
than better — it has no script at all (`ls scripts/ | grep -iE 'start|init'` →
none; `commands/product-start.md` has `## Do`, `## Modes`, `## Output` and no
`## Script`), so the verb a person actually reaches for when setting something up
is a page of prose an agent interprets, while the deterministic path is filed
under a word — "migrate" — that describes moving, not adopting.

## Scope

### In

- Give the five `MINIMAL_PM_DIRECTORIES` a tracked placeholder, the way
  `workspace/transactions` already has one, so a committed adoption survives a
  clone. A `.gitkeep` is sufficient; a short `README.md` in each is better
  because it also tells a reader what the directory is for.
- Assert the survival property in a test: apply a migration, `git add -A`,
  commit, clone, and run `validate_project_artifacts.py` on the clone expecting
  `valid: true`. Testing the working tree cannot catch this class of bug.
- Give the product one way to register an adopted project into `projects.json`,
  and have adoption offer it. Whether that is a `project_portfolio.py --add`, a
  flag on `project_migrate.py`, or a step in `product:start` is a design
  decision for the spec.
- Report existing in-flight work in the migration plan: a `detected_existing_work`
  section naming the files found (`TASKS.md`, `TODO.md`, `AGENTS.md`,
  `CLAUDE.md`, and the directory candidates already discovered) with a one-line
  statement that they are left in place and not imported.
- Decide and document which of `product:start` and `product:migrate` an existing
  project should be pointed at, and make the other one say so.

### Out

- Importing `TASKS.md` items into `issues/` automatically. Parsing someone's
  checklist into lifecycle artifacts is a judgment call, and getting it wrong
  writes files the user did not ask for. Detection and disclosure only.
- Moving, renaming, or rewriting any existing project file. The non-destructive
  guarantee in `commands/product-migrate.md:16` stands unchanged.
- Doctor output grouping, safe auto-fix classification, migration idempotence,
  and legacy schema value normalization — issue 105 owns all of those.
- Repository identity and remote configuration — issue 088 shipped that gate, and
  the fixture confirms adoption completes without a remote.
- Building a project-discovery crawler. Issue 102's scope fence forbids scanning
  unregistered sibling directories, and registration here must stay explicit.

## Known Limit

A `.gitkeep` keeps the directory but not its meaning: a clone will pass the gate
with five empty directories, which is correct but not informative. That is the
right trade — the alternative is generating placeholder issues, which is worse.

Registration also cannot be made automatic in the general case: `projects.json`
lives outside the adopted repository, in a portfolio root the migration is not
given. The realistic outcome is that adoption *prompts* for registration and
provides the one command that performs it, not that it registers silently.

## Acceptance Criteria

- A migration applied to a fixture, committed, and cloned yields
  `validate_project_artifacts.py <clone>` → `valid: true` with zero errors. A
  test asserts this through an actual `git clone`, not by inspecting the source
  working tree.
- Every path reported in the migration's `written` list is present in
  `git status --porcelain` output after `git add -A`. A test asserts the two
  lists match.
- One documented command registers an adopted project in `projects.json`, and
  running it makes that project appear in `product:projects` output.
- A migration plan run against a repository containing `TASKS.md` with open items
  names that file in its output. A test asserts the filename appears.
- Running the migration twice still writes nothing the second time — the existing
  `write_*_if_missing` guards must keep holding once placeholders are added.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture: a git repository with several commits, no remote, a non-`main` default
  branch, existing source, `README.md`, `docs/`, `TASKS.md` with open items,
  `TODO.md`, `CLAUDE.md`, `AGENTS.md`, and `.github/workflows/`. The
  investigation fixture reproduces all three defects and should be the basis.
- Clone-survival scenario as described in the acceptance criteria.
- Registration scenario against a throwaway portfolio root — never against
  `~/projects/.portfolio`.
- Double-apply idempotence scenario.
- `tests/test_project_migrate.py`, `tests/test_project_doctor.py`,
  `tests/test_validate_project_artifacts.py`.

## Entry Points

- `scripts/project_migrate.py:29` — `MINIMAL_PM_DIRECTORIES`, the five untracked
  directories
- `scripts/project_migrate.py:44` — `transactions/.gitkeep`, the fix already
  applied to exactly one directory
- `scripts/project_migrate.py:208-212` — `write_dir_if_missing`, creates a bare
  directory
- `scripts/project_migrate.py:228-231` — the loop that calls it
- `scripts/validate_project_artifacts.py:465-467` — `issues` and `specs` appended
  to the required list
- `scripts/project_doctor.py:65-74` — `CANDIDATE_PATHS`, directories only
- `scripts/project_portfolio.py:14-18` — `projects.json` created empty
- `scripts/project_portfolio.py:286-289` — the four portfolio operations, none of
  which add a project
- `scripts/project_registry.py:764-794` — `project_context_for_root`, the
  explicit-root path that bypasses the registry
- `commands/product-start.md` — the command with no script
- `commands/product-migrate.md:12-16` — the documented adoption procedure
- `.gitignore:22-25` — the same lesson, already written down for one directory
- `specs/103-atomic-lifecycle-state-transaction/review.md:8` — the same bug
  diagnosed and fixed one directory wide

## Scope Fence

Do not resolve this by having adoption write issue files derived from the user's
`TASKS.md`. The product's one credible promise to an existing project is that it
touches nothing it did not create; inventing artifacts from a parsed checklist
breaks that promise on the very first command, and a wrong import is harder to
undo than no import.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → tracked placeholders, clone-survival test, registration path,
      existing-work disclosure
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `001-project-migration` (done — shipped `project_migrate.py` and the
  three modes; the placeholder and registration gaps date from it),
  `103-atomic-lifecycle-state-transaction` (done — its review found this exact
  bug in `workspace/transactions` and fixed that one directory),
  `025-lightweight-project-adoption` (done — defined the light footprint these
  five directories belong to), `102-project-registry-and-resolver` (done — owns
  `projects.json` and forbids discovery by crawling, so registration must be
  explicit), `105-schema-migration-and-doctor-triage` (backlog, p0 — owns doctor
  triage output and migration plan/apply semantics; does not cover untracked
  directories, registration, or existing-work disclosure),
  `088-canonical-repository-remote-identity-gate` (done — remote identity, out of
  scope here), `131-command-surface-is-too-wide-and-english-only` (the
  `start`-versus-`migrate` naming question overlaps its surface work)

## Next Command

`product:spec 141-adoption-reports-success-on-an-incomplete-setup`
