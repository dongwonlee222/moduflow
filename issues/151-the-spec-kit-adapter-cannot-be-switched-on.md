# Issue 151: The Spec Kit Adapter Cannot Be Switched On

**Status: done** — 2026-09-07에 만들고 같은 날 끝냈습니다. `--enable` 스위치, 부르는 법 문서화, `doctor`의 꺼짐 보고 셋 다 들어갔습니다. 기본값은 그대로 꺼짐입니다 — fail-closed는 098의 의도이고 되돌리지 않았습니다.
**Priority: p1**

## 요약

spec-kit 어댑터는 **프로젝트가 켜야 도는 구조**인데, **켜는 코드가 없습니다.**
`--configure --write`를 해도 `enabled: False`가 쓰입니다. 하드코딩입니다.
손으로 `.moduflow/capabilities.json`을 만들어 `true`로 바꾸니 **바로
`outcome: ready`가 나왔습니다.** 5,786줄이 죽어 있던 게 아니라 **스위치가 없어서
못 켠 것**입니다.

## Summary

The adapter is opt-in by design and nothing implements the opt-in.
`_config_payload` hardcodes `"enabled": False`, so `--configure --write` writes a
disabled config. The only way to enable it is to hand-write
`.moduflow/capabilities.json`, which no command, skill or document mentions.

## Source

- Type: bug — 2026-09-07, 사장님이 "스펙킷 사용이 안 되고 있던데 충격이다"라고
  하셔서 실제로 켜보다 발견
- Owner / decision maker: Dongwon Lee

## 안 고치면

만들어 둔 5,786줄을 아무도 못 씁니다. 목표의 일곱 가지 중 **프로세스**가 막힙니다 — 명세를 검토하는 길이 있는데 닫혀 있습니다.

## 원인

```
$ sed -n '/^def _config_payload/,/^}/p' scripts/spec_kit_adapter.py
def _config_payload(functions):
    return {
        "schema": CONFIG_SCHEMA,
        "capabilities": {
            "spec-kit": {
                "enabled": False,          ← 하드코딩. 인자도, 분기도 없다
                ...

$ grep -n "enabled.*=.*True" scripts/spec_kit_adapter.py
(출력 없음)

$ python3 scripts/spec_kit_adapter.py . --configure --functions analyze,clarify
{... "spec-kit": {"enabled": false, ...}}      ← --write 를 붙여도 같다

$ ls .moduflow/capabilities.json
ls: .moduflow/capabilities.json: No such file or directory
```

**켠 뒤 실제로 돌린 결과** — 손으로 설정 파일을 만들어 `enabled: true`로 두고:

```
$ python3 scripts/spec_kit_adapter.py . \
    --issue-id 112-execution-planner-and-backend-boundary \
    --request "spec kit analyze the spec" --host-available
{
  "outcome": "ready",
  "function": "analyze",
  "inputs": ["specs/112-.../spec.md", "specs/112-.../plan.md",
             "specs/112-.../tasks.md", "workspace/constitution.md"],
  "template": "vendor/spec-kit/0.16.1/commands/analyze.md",
  "output_artifact": "specs/112-.../validation.md"
}
```

**어댑터는 멀쩡합니다.** 입력 넷을 찾고, 템플릿을 짚고, 산출물 경로를 냅니다.

### 두 번째 벽 — 부르는 법을 아무도 모른다

문구가 정확히 맞아야 합니다. 인정되는 문장이 **1,064개**이고, 전부
`spec kit` / `speckit` / `스펙 킷` / `스펙킷` 으로 시작해야 합니다.

```
"analyze this spec for inconsistencies"  → unsupported
"spec kit analyze the spec"              → ready
```

`commands/`·`skills/`·`docs/` 어디에도 이 문법이 안 적혀 있습니다. 맞는 문장을
찾으려면 소스의 `CANONICAL_REQUESTS`를 읽어야 합니다.

### 세 번째 — 안 켜졌다는 것을 아무도 말해주지 않는다

`product:doctor`도, 대시보드도, `product:status`도 "이 기능이 꺼져 있다"고
알려주지 않습니다. 그래서 **만든 지 4주가 지나도록 아무도 몰랐습니다.**

## Scope

### In

- `--configure --write`가 실제로 켤 수 있게 한다. 켜고 끄는 것이 명시적이어야
  하고, 기본값은 지금처럼 꺼짐이어야 한다 (fail-closed는 098의 설계 의도이고
  그건 옳다).
- 부르는 문법을 사람이 볼 수 있는 곳에 적는다. 1,064개를 다 적을 필요는 없고,
  **형태 하나와 함수 넷**이면 된다: `spec kit <analyze|clarify|checklist|converge> the spec`.
- `/moduflow` 허브에서 닿게 한다 — 지금은 `skills/spec-kit-validation-bridge`가
  있지만 켤 수 없으니 도달해도 소용이 없다.
- 꺼져 있는 선택 기능을 `product:doctor`가 보고한다. 이 이슈에서 어디까지 할지는
  좁게 잡는다 — spec-kit 하나만이라도 나오면 된다.

### Out

- **spec-kit 1.x 로 올리는 일.** 그건 `114`이고, 오늘 닫혔다. 이 이슈는 0.16.1
  그대로 켜지게만 한다.
- `CANONICAL_REQUESTS` 1,064개를 줄이거나 문법을 느슨하게 하는 일. 엄격한 것은
  098의 의도다 — 애매한 요청이 전문 도구를 부르지 않게 한다. 여기서는 **적는
  것**만 한다.
- 어댑터를 기본으로 켜는 일. 프로젝트가 명시적으로 켜는 구조를 유지한다.
- 다른 선택 기능들의 활성화 상태 보고 전반. 그건 별건이다.

## Known Limit

켤 수 있게 만들어도 **쓸모가 있는지는 별개**입니다. 파일럿 24/24는 **합성
픽스처**였고 (보고서가 스스로 `Synthetic fixture latency: 0 ms; it is not
presented as live performance`라고 적었습니다), 실제 명세에 돌려서 쓸 만한
지적이 나오는지는 아직 아무도 모릅니다. 이 이슈는 **켤 수 있게** 할 뿐입니다.

## Acceptance Criteria

- `--configure --write`로 켠 뒤 `--issue-id`/`--request` 호출이 `ready`를 낸다.
- 켜지 않은 프로젝트는 지금처럼 `disabled`를 낸다 — 테스트로 단언.
- 부르는 문법이 한 곳에 적히고, `commands/` 또는 `skills/`가 그것을 가리킨다.
- `product:doctor`가 spec-kit이 꺼져 있음을 보고한다.
- `.moduflow/capabilities.json`이 없는 프로젝트가 깨지지 않는다 — 라이브 트리로
  확인 (이 저장소에 지금 그 파일이 없다).
- `python3 scripts/release_check.py .` 통과, 최상위 `valid` 확인.

## Verification

- 픽스처: 껐다 켰다 하며 `disabled` ↔ `ready` 전이.
- 픽스처: 설정 파일이 없는 프로젝트 → `disabled`, 예외 없음.
- 실제 이슈(`112`)에 돌려서 `ready`와 입력 넷을 확인 — 이미 한 번 확인했다.
- 명세가 없는 이슈(`132`)에 돌려서 `unavailable` 확인 — 이것도 확인했다.
- `tests/test_spec_kit_adapter.py`.

## Entry Points

- `scripts/spec_kit_adapter.py` — `_config_payload` (하드코딩 지점),
  `configure_project`, `load_project_config`, `classify_request`,
  `CANONICAL_REQUESTS`, `FUNCTION_PHRASES`
- `skills/spec-kit-validation-bridge/SKILL.md` — 도달 경로
- `commands/moduflow.md` — 허브가 이 다리를 언제 로드하는지
- `scripts/project_doctor.py` — 꺼진 기능 보고가 들어갈 자리
- `specs/098-speckit-selective-validation-adapter/pilot-report.md` — 합성
  픽스처였다고 스스로 적은 곳

## Scope Fence

**기본값을 켜짐으로 바꾸지 않는다.** fail-closed는 098이 의도한 것이고, 이
이슈는 그 설계를 되돌리는 게 아니라 **스위치를 다는 것**이다.

`CANONICAL_REQUESTS`의 엄격한 문법을 느슨하게 하지 않는다. 애매한 요청이
외부 도구를 부르지 않게 하는 것이 그 엄격함의 목적이다.

버전을 올리지 않는다 — `0.16.1`과 SHA 핀은 그대로 둔다.

## Workflow Tasks

- [x] execute → 스위치, 문법 문서화, doctor 보고

명세·계획 파일은 만들지 않았습니다. 149와 같은 이유입니다 — 원인이 한 줄
(`"enabled": False` 하드코딩)이고 결정이 하나(기본값을 유지할 것인가)뿐이라,
네 파일을 쓰는 쪽이 고치는 일보다 큽니다. 테스트 5건이 붙잡고 있습니다
(`tests/test_spec_kit_adapter.py`의 `SpecKitEnableSwitchTests`).

**허브 연결은 하지 않았습니다.** `/moduflow`가 이 다리에 닿는 경로는 이미
`commands/moduflow.md`에 있고, 막고 있던 것은 스위치였습니다. 그게 풀렸으니
따로 배선할 것이 없습니다.

## Related Issues

- follows_up: `098-speckit-selective-validation-adapter` (done — 어댑터를 만들고
  스위치를 안 달았다)
- related: `114-speckit-selective-adapter-1x-compatibility` (2026-09-07 닫힘 —
  버전 올리기이고, 이 이슈와 다른 문제다. 닫은 판정은 유효하다),
  `121-constitution-amendment-invalidates-pilot-evidence` (같은 파일럿에 걸려
  있다), `146-the-validator-throws-away-severity-at-the-last-step` (꺼진 기능을
  보고할 자리를 만든다)

## Next Command

`product:spec 151-the-spec-kit-adapter-cannot-be-switched-on`
