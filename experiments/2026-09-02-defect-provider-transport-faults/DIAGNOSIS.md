<!-- tranche: 2026-09-02-defect-provider-transport-faults -->

# Diagnosis: a zero-byte remote hang-up is classified "transient" and answered by four byte-identical resends, and the resulting fault reaches no surface an operator or a monitor reads

Map documents read before the record, in the order `dr-drive-harness` §4 fixes:
`INDEX.md` -> `INV-frozen-surfaces.md` -> `SEAM-llm-x-workflow` /
`SEAM-llm-x-verification` -> `SUB-llm` / `SUB-application`. The `Traps` sections
were read first, and one of them **already contains this defect's lesson applied
to the neighbouring branch** — see "Recurrence" below.

## Primary cause

`llm/endpoints.py::request_with_retries` sorts every transport exception into
two classes. A `TimeoutError` is recognised by `_timed_out()` and handled by a
bounded, *escalating* ladder — attempt 1 waits `timeout_s`, one retry waits
`2 x timeout_s`, and a second read timeout is terminal (`TIMEOUT_FACTORS = (1,
2)`). Everything else — including `http.client.RemoteDisconnected`, the remote
end hanging up having written **no body at all** — falls through to the generic
`except (URLError, ConnectionError, TimeoutError, OSError, HTTPException)` arm,
which sleeps 2 s / 4 s / 8 s and **resends the byte-identical request**, four
attempts in total, with no bound on total elapsed time and no change to the
request between attempts. When the thing closing the connection is a fixed
timer on the path rather than a transient fault, all four attempts are
guaranteed to fail the same way at the same second, and the call spends
4 x wall + 14 s producing nothing. The fault is then written faithfully into the
per-attempt trace and into a `workflow-provider-attempt-v1` object — and into
no surface that a watching operator, a monitor script, or `deepreason results`
reads. Both halves are needed for the observed outcome: the retry policy
manufactures the 20-minute dead call, and the surfacing gap is why 4.94 hours
went by with nobody able to see it.

## Evidence

### E1 — The wall is a TIMER, not noise, and the harness's own timeout is not it

Re-derived first-hand from `run/log.jsonl` of P-A1 root `4565139800f5ca02`
(read-only worktree of `origin/claude/live-reasoning-p-a1-bv65kl`):

```
cd <root> && python3 - <<'PY'
import json, statistics
faults=[]
for line in open('log.jsonl'):
    e=json.loads(line); l=e.get('llm')
    if not l: continue
    for a in l.get('attempt_trace') or []:
        if a.get('transport_diagnostics'):
            faults.append((e['seq'], a['ms'], a['transport_attempts'], a['timeout_s'], a['max_tokens']))
per=[(ms-14000)/n/1000 for _,ms,n,_,_ in faults]
print(len(faults), [round(p,1) for p in per])
print(set(t for *_,t,_ in faults), set(m for *_,m in faults))
PY
```

Output:

```
10 [300.2, 300.2, 300.3, 300.3, 300.3, 259.3, 300.2, 246.8, 300.3, 300.4]
{1800} {49152, 30720}
```

Eight of the ten land in a **0.2-second band around 300.3 s**. A flaky network
does not produce a 0.06 s standard deviation. `timeout_s` was **1800** on every
one of them, so the harness's own read timeout cannot be the cutter — and the
subtraction of exactly the `_BACKOFFS` total (2+4+8 = 14 s) from `ms` before
dividing by `transport_attempts` = 4 is what makes the number fall out clean.
The two shorter ones are explained inside the record too: seq 274's first
diagnostic is `HTTPError:HTTP-500`, a fast refusal, not a wall; seq 255 is a
four-disconnect call whose total is 1 051 274 ms rather than ~1 215 000 ms.

The same arithmetic on a root committed six days earlier gives the same answer
from different equipment. `experiments/2026-08-26-pc2-rematch/retired-transport-
timeout180-run-42ad288038dd606c`, blob
`blobs/41/4132d994891c4c491df3ccea4b153d609d314bf714a2a7335233d9ad60dad68d`:

```json
{"attempt": 0, "contract": "conjecturer.turn.v6",
 "error": "transport failed after retries: Remote end closed connection without response",
 "transport_diagnostics": ["TimeoutError:The read operation timed out",
                           "RemoteDisconnected:Remote end closed connection without response",
                           "RemoteDisconnected:Remote end closed connection without response",
                           "RemoteDisconnected:Remote end closed connection without response"]}
```

That root's `ms` is 1 095 567 with `timeout_s: 180`: one client read timeout at
180 s, then three disconnects — `(1095.6 - 180 - 14) / 3 = ` **300.5 s each**.
Two runs, two models (glm-5.2 / glm-5.3), two caps (100 000 / 49 152), two
client timeouts (180 s / 1800 s) — and the same ~300.4 s.

### E2 — The retry is byte-identical and the ladder is unbounded in wall time

`transport_attempts: 4` on all ten faults; the four diagnostic strings on each
are the same string repeated (39 `RemoteDisconnected` + 1 `HTTPError` across the
run, all on the glm-5.3 endpoint, zero on any other model). `endpoints.py`'s
`_once()` closure captures `request` — one `urllib.request.Request` object built
once at `endpoints.py:423-427`, outside the retry loop — so every attempt sends
the identical URL, headers and body. Nothing between attempts shrinks the cap,
changes the leg, or stands the seat down.

### E3 — A hard total-duration cut is REFUTED by the same record

The successful glm-5.3 attempts in the same run:

```
ms: [3903, 5282, 9247, 10765, 13828, 19149, 44437, 59407,
     245344, 247537, 258373, 259832, 272502, 278726, 839028]
tokens: [929, 943, 1038, 1223, 1465, 2288, 4842, 6391,
         22509, 23644, 24506, 24597, 24914, 32458, 43281]
```

One non-streaming call ran **839 s and returned 43 281 tokens**. So whatever
closes at ~300 s is not a cap on total request duration. That single datum is
what makes the mechanism genuinely UNMEASURED and is why this tranche's Phase 0
is a probe rather than a design.

### E4 — The fault reaches no surface anyone reads

- `progress.jsonl` of P-A1 and of P-S1 both carry exactly one key set, 24 keys,
  and **none matches `transport|provider|health|endpoint|attempt|fail|error`**.
  `ProgressEvent` (`runtime/progress.py:34-65`) is `extra="forbid"`, so the
  absence is structural, not an omission.
- `application/results.py`'s `ABSENCE_REASONS` (17 codes, `results.py:28-48`)
  contains no transport-shaped code, and `render_results` (`results.py:589-687`)
  has no provider block. `grep -n notice src/deepreason/application/results.py`
  returns nothing.
- P-S1 run `9e48a36b1dec91ee`: **54** typed `transport_failure` attempt objects
  out of 280, all on one seat (glm-5.2 conjecturer seat 0), 215 of the 216
  diagnostic strings `URLError:<urlopen error [Errno 111] Connection refused>`.
  Fifteen of 24 cycles ran with that seat dead, confirmed three independent
  ways: zero-token attempts bucketed between cycle markers (cycles 9, 11-23),
  `token_spend` frozen at 1 319 932 across `progress.jsonl` cycles 10-24, and
  1 293 `Spawn` events total against `FLOW_CENSUS.md`'s 1 293 recorded "at cycle
  9 of 24" — **zero spawns in the last fifteen cycles**.
- Across the **13** summary documents of that tranche: `transport` 0,
  `RemoteDisconnected` 0, `ConnectionError` 0, `provider health` 0. Word-boundary
  `fault` hits 4 times, none about transport. The 15 dead cycles are reported as
  a milestone **met**: `PAPER.md:290` `| M3 | reached 24 cycles ... | **MET** |`;
  `PREREG-3.md:55` "**PASS**: eight of eight assertions, 24 of 24 cycles, clean".
- P-A1's own `monitor.sh`, written for this exact signature, classified a failed
  attempt by `t.get("error") or t.get("failure") or t.get("status") == "error"`.
  The attempt trace's 24 keys carry none of those three. 40 faults, 0 alerts.

**One place the run-level record DOES carry it, unlabelled:** P-S1's
`REPLAY_VALIDATION.json` records `"attempts": 280, "calls": 280,
"provider_transport_attempts": 442`. 442 - 280 = 162 = 54 x 3 extra retries. The
number exists; nothing names it, and nothing prints it.

## Recurrence — the trap is already written down, for the other branch

`docs/map/SUB-llm.md` Traps, verbatim:

> **Retrying an identical wait after a read timeout fails identically.** Two
> variator calls were dropped live after four 120s waits while ~110s
> generations were succeeding at the same endpoint. `TIMEOUT_FACTORS = (1, 2)`
> makes the retry wait twice as long and makes a second read timeout terminal,
> bounding total wait at 3x rather than opening a ladder.

That is this defect, one branch to the left. The lesson was learned for
`TimeoutError` and encoded in `_timed_out()`; `RemoteDisconnected` — a strictly
worse case, because zero bytes arrived and the wall is on the far side — kept
the unbounded identical ladder. This is a recurrence, which per `dr-diagnose` is
the cheapest diagnosis available, and it earns a rewritten Traps entry rather
than a new one.

## Implicated code (3 sites, the maximum this phase allows)

1. `src/deepreason/llm/endpoints.py:69-95` — `request_with_retries`: the generic
   arm that retries a zero-byte disconnect identically, and `_BACKOFFS = (2,4,8)`
   giving four attempts with no wall-time bound.
2. `src/deepreason/llm/endpoints.py:423-427, 452-486` — the `Request` built once
   outside the loop and the `_once()` closure whose `_timed_out()` gate is the
   only thing that ever changes an attempt's behaviour.
3. `src/deepreason/runtime/progress.py:34-65` (`ProgressEvent`, `extra="forbid"`)
   and `src/deepreason/application/results.py:28-48, 589-687, 735-748`
   (`ABSENCE_REASONS`, `render_results`, `results_summary`) — the two surfaces
   with no provider-health field between them.

## Falsifiable prediction (what `dr-reproduce` must show)

**Offline, against a stub provider** that accepts a connection, waits N seconds,
then closes it having written no body:

    python -m pytest tests/test_provider_transport_faults.py -q

- the call raises `EndpointError` only after **four** attempts;
- `last_transport_attempts == 4` and `last_transport_diagnostics` is the same
  string four times;
- total elapsed ~= `4*N + 14` s;
- the four request bodies captured by the stub are **byte-identical**;
- `progress.jsonl` written by a run over that stub contains no key matching
  `transport|provider|fault`, and `deepreason results` prints no provider block.

**Live, Phase 0 probe** (pre-registered in `PREREG.md` before the first call):

- P1: a non-streaming call whose generation exceeds ~300 s is closed by the
  remote end -> expect `RemoteDisconnected` at 300.2-300.5 s, with the
  container proxy's `recentRelayFailures` still `[]` (which discriminates an
  Ollama-edge close from a container-proxy abort).
- P2: the same call with `"stream": true` survives past 300 s.
- P3: the wall is the same second for glm-5.3 and deepseek-v4-pro:0813 when both
  are forced past it.

If P1 fails to reproduce a ~300 s close, this diagnosis's wall half is wrong and
the tranche returns here with the measurement.

## Ruled out

**"glm-5.3 is simply slow; these were long generations that eventually
succeeded."** This was the P-A1 window's own F5 finding and it is refuted by the
record: every one of the ten has `tokens: 0`, `usage_unknown: true`,
`raw_ref: ""` and a non-empty `transport_diagnostics`. Nothing generated. The
distinction matters because it changes the fix from "raise the cap" to "stop
resending into the wall".

**"The harness's own read timeout fired."** Refuted twice: `timeout_s` is 1800
on all ten P-A1 faults, and a client read timeout raises `TimeoutError`, which
`_timed_out()` routes to the two-attempt escalating ladder — the record shows
four attempts and `RemoteDisconnected`, which is the other branch. The 2026-08-26
tranche made exactly this misattribution (`PREREG.md:479-480`, "six consecutive
180-second socket timeouts") and its own blob falsifies it: one timeout, three
disconnects.

**"A hard cap on total request duration."** Refuted by E3's 839 s success.

## Second cause found, PARKED not pursued

The `dropped-call` signal is already consumed by the allocation controller to
*lengthen the transport timeout* (`SEAM-llm-x-scheduler.md` Traps: "the
controller will answer a lease violation by widening a wait", parked at
`experiments/2026-08-22-fix-route-lease-maxtokens/FIX.md`). A new transport
policy reacting to faults would be the second consumer of an overloaded signal.
Recorded in PARKED.md as P6; not touched here.
