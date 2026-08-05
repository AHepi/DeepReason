# Reproduction

Form: end-to-end against the installed wheel, through the public MCP
surface only — no repo imports of `src/`, no internals, no live
provider. The retained `--keep` temp root from the failing smoke
(`/tmp/deepreason-wheel-operational-s1jn0e1v`) supplies the venv and a
warm qualification cache, so each subject run costs ~1 minute instead of
~15.

Record-replay and an offline unit test were both available and both
insufficient for the question actually asked. `dr-reproduce` orders by
cheapest SUFFICIENT form, and the operator's question is *"is (a)
reachable **from the facade**"* — a `prepare_continuation` unit test
would prove the raise site is live while saying nothing about whether
the smoke can drive a subject into that state through `start_run` /
`cancel_run` / `continue_run`. The facade is the claim, so the facade is
the instrument.

## Artifact

Runnable as-is against any retained `--keep` temp root (substitute the
path). It reads `run-stop.json` only to display the terminal; every
decision comes from MCP responses.

    python - <<'PY'
    import json, sys, time
    from pathlib import Path
    sys.path.insert(0, "/home/user/DeepReason/scripts")
    import wheel_operational_smoke as S

    temp = Path("/tmp/deepreason-wheel-operational-s1jn0e1v")
    home, work = temp / "blank home", temp / "unrelated empty directory"
    mcp = S._venv_executable(
        temp / "installed environment with spaces", "deepreason-mcp")
    env = S._environment(
        home,
        provider_port=S._unused_loopback_port(),
        provider_state_path=temp / "v1-repro-provider-counts.json",
    )
    client = S.MCPClient(mcp, cwd=work, env=env)
    S._tool_list(client)

    def call(name, arguments):
        return client.request(
            "tools/call", {"name": name, "arguments": arguments})

    def text_of(r):
        return ((r.get("result") or {}).get("content") or [{}])[0].get("text")

    def status(run_id):
        return json.loads(text_of(call("run_status", {"run_id": run_id})))

    started = call("start_run", {
        "question": "Can a cancelled inquiry be resumed as if it had "
                    "merely paused?",
        "budget": {"cycles": 12, "token_budget": 200000},
    })
    run_id = json.loads(text_of(started))["run_id"]

    # Cancel at the first observed cycle boundary: 11 cycles of margin
    # before the run could reach a terminal of its own.
    for _ in range(240):
        state = status(run_id)
        if state.get("cycle", 0) >= 1 or state.get("state") not in {
            "starting", "running"}:
            break
        time.sleep(1)
    call("cancel_run", {"run_id": run_id})
    for _ in range(600):
        terminal = status(run_id)
        if terminal.get("state") in {"completed", "failed", "cancelled"}:
            break
        time.sleep(1)

    root = home / ".deepreason" / "runs" / run_id
    print("terminal state:", terminal.get("state"),
          "stop_reason:", terminal.get("stop_reason"))
    print("continuations.jsonl BEFORE:",
          (root / "continuations.jsonl").exists())
    response = call("continue_run", {
        "run_id": run_id, "budget": {"cycles": 6, "token_budget": 100000}})
    print(json.dumps(response, indent=2, sort_keys=True))
    print("continuations.jsonl AFTER :",
          (root / "continuations.jsonl").exists())
    print("state AFTER               :", status(run_id).get("state"))
    client.close()
    PY

## Current output — half 1: the refusal IS reachable

    start_run isError: False
    start_run body   : {"run_id": "run-3e2472bdf0743de48ff609f0b028bad4",
                        "state": "running", ...}
    state at cancel  : {'state': 'running', 'cycle': 1,
                        'phase': 'convergence'}
    cancel_run isError: False
    cancel_run body   : {"run_id": "run-3e2472bd...",
                         "safe_boundary": "completed-cycle",
                         "state": "cancellation-requested"}
    terminal state   : cancelled  stop_reason: operator_cancelled
    run-stop.json    : {"digest":"57e77c3a...","event_seq":43,
                        "metrics":{...,"cycle":2,...},
                        "policy_digest":"76a98a16..."}
    continuations.jsonl BEFORE: False

    === continue_run FULL RESPONSE BODY (cancelled run) ===
    {
      "id": 142, "jsonrpc": "2.0",
      "result": {
        "content": [{"type": "text",
                     "text": "ValueError: CONTINUE_TYPED_STOP_REQUIRED"}],
        "isError": true
      }
    }

    isError                             : True
    CONTINUE_TYPED_STOP_REQUIRED present: True
    continuations.jsonl AFTER : False
    state AFTER               : cancelled

## Current output — half 2: budget exhaustion continues, twice

Two independent runs, so the behaviour is stable rather than a single
observation:

| run | origin | stop.reason | `continue_run` | continuations.jsonl |
|---|---|---|---|---|
| `run-656a6e38…` | the smoke's own first reason run | `budget_exhausted` | non-error | absent → present |
| `run-2357b4f2…` | minted fresh in DIAGNOSIS.md's measurement | `budget_exhausted` | non-error, `isError:false` | absent → present |

Both moved to `activity: "continuation prepared"`, `phase: "resume"`.

## Confirms diagnosis: yes

The mechanism predicted it exactly. `text_runs.py` records the typed
STOPPED receipt only inside `if stop_reason == "budget_exhausted"`; a
cancellation takes `stop_reason = "operator_cancelled"` and falls
through to `write_stop_record`, leaving no terminal lifecycle decision —
so `continuation.py:352` is reached and raises. Same code, same day,
two different subjects, two opposite and correct answers. The refusal
was never removed; only the smoke's subject stopped qualifying for it.

## The finding that decides the fix's shape

**`_assert_non_resumable_rejection` does not need to change.** It
already accepts exactly `"ValueError: CONTINUE_TYPED_STOP_REQUIRED"`,
which is byte-for-byte what the cancelled run returns. The stale thing
is the SUBJECT the stage points it at, not the assertion. That makes
option (a) a re-pointing rather than a rewrite, and it means the fix
cannot be accused of weakening an assertion to reach green — the
assertion survives untouched and starts passing for the right reason.

## Two coverage facts found while proving this

1. **`CONTINUE_TYPED_STOP_REQUIRED` has no product test anywhere in the
   gate.** Repo-wide, the string appears in exactly four places: the
   raise site (`continuation.py:352`), the smoke's matcher (two lines),
   and `tests/test_wheel_operational.py:1383` — which is a unit test of
   the smoke's own string matcher, not of the product path. So the
   operational smoke was the ONLY end-to-end witness that the facade can
   refuse a continuation, and it has been unable to reach that stage in
   this container since 2026-07-27. Losing it silently to option (b)
   would have left the refusal with zero coverage of any kind.
2. **`cancel_run` is pinned in `EXPECTED_MCP_TOOLS` but never called.**
   `grep -n cancel scripts/wheel_operational_smoke.py` returns the pin,
   two lifecycle constants and two status-polling sets — no invocation.
   Option (a) exercises a tool whose presence was pinned and whose
   behaviour was not.

## Post-fix expectation

    python -u scripts/wheel_operational_smoke.py -> exits 0

with `STAGE_CONTINUATION_REJECTION` asserting the SAME
`_assert_non_resumable_rejection` against a cancelled run
(`isError: true`, continuations.jsonl still absent, terminal unchanged),
and a new assertion witnessing that a budget-exhausted run continues
(`isError: false`, continuations.jsonl written, status `resume`) — both
halves of `2d4ca2e1`'s decision proven end to end, per the operator.

## Fidelity note carried into FIX.md

The cancel lands at "the next safe completed-cycle boundary", so the
subject run must keep cycles in reserve when the cancel is issued. This
reproduction requested 12 cycles and cancelled at the first observed
cycle boundary, terminating at cycle 2 — 10 cycles of margin. A stage
that cancelled without margin could race the run to its own terminal and
land on `budget_exhausted` instead, which would make the stage flaky in
exactly the direction that hides the defect. FIX.md must state the
margin as a design constraint, not leave it to the timing that happened
to work here.
