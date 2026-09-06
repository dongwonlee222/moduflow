# Issue 112 Stream C — Host Adapter Interface

Task T05. Design for review **before** any mapping code is written (T06). Written
2026-09-06 against `scripts/execution_routing.py` as it landed in T01–T04.

## 요약

지금 워커 계획 파일에는 **특정 도구의 사정이 그대로 박혀 있습니다.** 브랜치 이름에
`codex/`가 붙고, 모든 작업 지시문에 OpenAI 모델 이름(`gpt-5.6-sol` 등)이 들어갑니다.
클로드 코드에서 돌려도 그렇게 나옵니다. 라우팅 결과는 **"무엇이 필요한가"만** 담고,
**"어느 도구에서 어떻게 부르는가"는 어댑터가** 맡도록 경계를 긋습니다. 호스트를
하나 더 붙일 때 저장되는 파일은 한 글자도 안 바뀌어야 합니다.

## What leaks today

Spec §8 names three. All three verified in `scripts/worker_orchestrator.py`
on 2026-09-06:

| Leak | Where | What it is |
| --- | --- | --- |
| `"worktree": f"codex/{issue_id}-{task_id.lower()}"` | `:408` | a Codex branch-prefix convention |
| `COGNITIVE_DEMAND_GUIDANCE` naming `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` | `:50-66`, applied into every task prompt at `:388` | OpenAI model vocabulary |
| `subagent: {TypeName: "self", Role, CognitiveDemand, Workspace: "share", Prompt}` | `:412-417` | a Superpowers subagent shape |

The third is the one that is easy to miss. `TypeName`, `Workspace: "share"` and
the prompt's whole structure are one host's way of describing a subagent. A host
without subagents has nothing to put there, and today it would have to write a
field it does not use into a file everyone reads.

**Why it matters beyond tidiness.** `worker-plan.json` is a canonical artifact,
committed and diffed. A plan produced under Claude Code today records a `codex/`
branch and OpenAI model names — the file is wrong about its own provenance, and
the diff between two hosts is noise rather than a change.

## The boundary

**The routing result carries intent. The adapter carries vocabulary.**

The test for which side a field belongs on: *would its value change if the same
work were done on a different host?* If yes, it is vocabulary.

| Intent — stays in `execution_routing` | Vocabulary — moves to the adapter |
| --- | --- |
| `expected_files`, `expected_globs` | worktree or branch naming |
| `dependencies` | merge strategy |
| `cognitive_demand`: `deep` \| `balanced` \| `fast` | which model that maps to |
| `isolation`: `shared` \| `isolated` | how isolation is achieved |
| `backend`: `inline` \| `superpowers-sdd` | the subagent record's shape |
| `routing_reason`, `gaps`, `status` | prompt phrasing |

Two fields must be **added** to each task in the routing result, because the
adapter needs them and the result does not carry them yet:

- `cognitive_demand` — today derived in `worker_orchestrator` from
  `WORKER_COGNITIVE_DEMAND` (`:39-47`), a worker-role table. That mapping is
  intent and belongs upstream of the host.
- `isolation` — `shared` when the task declares shared state or the backend is
  `inline`, `isolated` otherwise. Today this is implied by the worktree string
  existing, which is why the string leaked in the first place.

Neither is a host value. `deep` does not name a model; `isolated` does not name
a worktree.

## Interface

One class per host. Three methods, no state, no I/O.

```python
class HostAdapter:
    host_id: str          # "claude-code" | "codex" | "copilot"

    def isolation(self, issue_id: str, task_id: str, requirement: str) -> dict:
        """`shared` | `isolated` -> this host's isolation record."""

    def model(self, cognitive_demand: str) -> dict:
        """`deep` | `balanced` | `fast` -> this host's model instruction."""

    def dispatch(self, task: dict, plan: dict) -> dict:
        """One routing task -> this host's execution record."""
```

`dispatch` is the only one that can return `{}`. A host with no subagent concept
returns an empty record and the plan is executed inline — that is a legitimate
host, not a broken adapter.

**The adapter never sees the canonical artifact and never writes a file.** It
takes a routing result and returns a host record. `worker_orchestrator` (T09)
holds both and decides what to write. Keeping the adapter pure is what makes
T07's proof cheap: run three adapters over one result and diff nothing.

### Adding a host

One file, one class, one row in the registry, one fixture in
`tests/fixtures/execution-routing/hosts.json`. No change to
`execution_routing.py`, no change to any canonical artifact. If adding a host
requires either, the boundary is in the wrong place and this design has failed.

## What T07 must prove

One routing result, three adapters, and the canonical artifact byte-identical
across all three. That is the whole claim, and it is falsifiable: if
`worker-plan.json` differs between the Claude Code and Codex runs, a host value
is still upstream of the adapter.

## Known Limit

This moves host vocabulary out of the canonical artifact. It does not make the
hosts equivalent. A host without worktrees cannot honour `isolated`, and the
adapter's honest answer is a record saying so — not a silent downgrade to
`shared`. Whether the planner should then refuse is out of scope here; it is a
routing decision, and Gate 3 already owns routing.

## Human Review Decisions

- [확인만] The three leaks named in spec §8 are real and are the scope. Verified
  at `worker_orchestrator.py:408`, `:50-66`, `:388`, `:412-417` on 2026-09-06.
- [확인만] `cognitive_demand` and `isolation` are added to the routing result as
  intent fields. Both are already computed somewhere; the change is where they
  live, not what they mean. `WORKER_COGNITIVE_DEMAND` at `:39-47` is a
  role-to-demand table with no host in it.
- [확인만] The adapter is pure — no file writes, no reads. It is what makes
  T07's proof a diff rather than an integration test.
- [확인만] **Decided 2026-09-06 — refuse.** An unrecognised host stops with a request for an adapter; there is no generic fallback. Record: `memory/decisions/2026-09-06-unregistered-host-refuses-rather-than-falling-back.md`. The reason in one line: something that always works is never replaced, which is exactly how a hardcoded `codex/` prefix survived in every worker plan. The original request is kept below because the alternatives and their costs are what the decision was made against.
  - 왜 이 결정이 필요한가요? 어댑터는 호스트마다 하나씩 붙습니다. 목록에 없는
    호스트에서 돌렸을 때 무엇을 할지는 코드가 정할 수 없는 판단입니다.
  - 지금 무엇이 잘못되고 있나요? 지금은 호스트 구분 자체가 없어서, 클로드
    코드에서 돌려도 `codex/` 브랜치와 OpenAI 모델 이름이 파일에 박힙니다.
    어느 도구에서 만든 계획인지 파일만 봐서는 알 수 없습니다.
  - 실제로 측정된 예시 — `worker_orchestrator.py:408`이 호스트와 무관하게
    `codex/<이슈>-<태스크>`를 씁니다. 이 저장소의 워커 계획은 전부 그렇게
    적혀 있습니다.
  - 다른 선택지와 그 비용 —
    (가) **거부**: 모르는 호스트면 계획을 안 만들고 어댑터를 만들라고 합니다.
    파일에 틀린 값이 들어갈 일이 없지만, 새 도구를 처음 쓰는 사람이 아무것도
    못 하고 막힙니다.
    (나) **일반 어댑터로 대체**: 워크트리 없음·모델 지정 없음·서브에이전트
    없음으로 채웁니다. 항상 동작하지만, 어댑터를 안 만들어도 굴러가서 아무도
    안 만들게 됩니다 — 지금 `codex/`가 박혀 있는 이유와 같은 종류입니다.
  - 승인하면 무엇이 달라지나요? T06 구현에서 미등록 호스트 경로가 정해지고,
    T07의 증명 대상이 "세 호스트"인지 "세 호스트 + 미등록"인지가 결정됩니다.

## Next

T06 — implement the adapter and move the `codex/` prefix and the model-name
prompt text out of the routing result. Blocked on the decision above.
