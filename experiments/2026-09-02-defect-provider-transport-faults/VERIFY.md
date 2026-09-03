<!-- tranche: 2026-09-02-defect-provider-transport-faults -->

# Verification

## 1. Criterion command + output

`GOAL.md`'s success criterion, run verbatim:

```
$ python -m pytest tests/test_provider_transport_faults.py -q
28 passed
```

The suite pins each of the goal's six clauses, and every test is **mutation-
proven**: ten mutations, ten caught (`proof/mutation.txt`, RED transcripts
inline).

| GOAL clause | test | mutation that catches it |
|---|---|---|
| 1 — fault recorded typed, shape unchanged | `..._reports_zero_byte_faults_separately_...` | classifier returns `other` for everything |
| 2 — per-seat counter in `progress.jsonl` | 3 tests incl. `..._says_so_rather_than_claiming_zero` | `provider_health` defaults to `{}` |
| 3 — `deepreason results` prints it, absence typed | 2 tests | results heading renamed |
| 4 — second attempt not byte-identical | `..._not_answered_with_an_identical_resend` | policy set to `identical-v0` |
| 5 — a stream past the wall completes | `..._streamed_retry_succeeds_where_the_first_attempt_died` + 3 | `stream_options` removed; terminal-chunk guard removed |
| 6 — N zero-byte attempts emit a typed notice | 2 tests | notice never emitted / emitted every time / threshold ignored |

Two of those mutation runs caught weaknesses in the TESTS rather than the code —
a heading assertion that a renamed heading still satisfied because it was a
substring match, and a derivation nothing pinned until a test was added against
the one committed root carrying a real transport failure. Both fixed; both
recorded here rather than quietly.

Whole-tree gate, run THREE times, and all three are recorded because two of them
are part of the evidence rather than noise:

```
run 1  (before the round-trip fix)     1 failed, 4623 passed, 6 skipped   0:27:00
run 2  (after it, before the census fix) 4624 passed, 6 skipped           0:27:02   rc=0
run 3  (the TRUE final tree)           4624 passed, 6 skipped in 1616.93s 0:26:56   rc=0
```

**0 failed on the final tree.** Run 1's single failure in 4 624 was a real defect
in this tranche's design rather than a fixture — §4. Run 3 exists because a code
change (the signal-census fix, §2) landed after run 2, and a gate result on a
tree that is not the one being shipped is not a gate result.

## 2. `docs_verify` — 8 failed, every one dispositioned

```
$ python tools/docs_verify.py
docs_verify [full]: 71 documents, 1297 checks, 4 workers
docs_verify: 8 failed
```

| check | disposition |
|---|---|
| `SEAM-llm-x-rules.md:54` | **BASELINE** — malformed check, lost closing backtick, parked P3 (`AUDIT_BASELINES.md:52`) |
| `INV-frozen-surfaces.md:181` | **BASELINE** — the transport-failure census, red since 2026-08-26, parked P-D3 (`AUDIT_BASELINES.md:53`). The tranche instruction forbade "fixing" it by changing what it counts, and it was not touched |
| `CON-run-identity.md:211`, `:213`, `:215` | **BASELINE** — shallow-clone-only git-history checks; `git rev-parse --is-shallow-repository` returns `true` here (`AUDIT_BASELINES.md:62-66`) |
| `INV-frozen-surfaces.md:364` | **RED BY DESIGN ON THIS BRANCH.** The check is `! git diff --name-only origin/main...HEAD \| grep -qE "...run_manifest\.py..."` — a branch-scoped tripwire that fires whenever a branch touches a frozen surface. This branch does, under the operator's 2026-09-03 grant, so the tripwire is doing its job: flagging the contact for review. It passes again on `main`, where the diff is empty |
| `CON-run-identity.md:298` | **NEW FINDING, NOT THIS TRANCHE'S** — reported `TIMEOUT after 300s`. Re-run ALONE on an idle container per `AUDIT_BASELINES.md`'s own disposition procedure: **`9 passed in 357.19s`** — it passes but still exceeds the 300 s ceiling, so it times out loaded or not. Its files are untouched here. Parked as P7 with a ready-to-send prompt |
| `SUB-scheduler.md:149` | **WAS MINE, FIXED.** The signal census walks every `record_measure` call in `scheduler.py` and reads the string literal at the call site; my emission passed a variable, so the emission was invisible to the very check that catches an undeclared signal — and the check CRASHED (`AttributeError`) rather than reporting. The call site now spells the literal. Verified passing |

Both map checks this tranche ADDED were proven able to fail, not merely to pass:
`SUB-llm.md`'s goes red when a `max_tokens` reference is planted in the policy
module, `SUB-application.md`'s when the results heading is renamed.

## 3. Historical roots

The fix changes a WRITER (the retry path) and adds two READERS; it changes no
validator and no record format, so no committed root's verdict can move. Rather
than assert that, the derivation was run against real committed and read-only
roots and its numbers checked against what the record independently says:

| root | derived | cross-check |
|---|---|---|
| P-A1 `4565139800f5ca02` | `conjecturer#1` 6 faults / streak 6 / 118.0 min; `defender` 4 / 4 / 78.3 min | 118.0 + 78.3 = 196.3 min = **3.27 h**, the figure the P-A1 monitor review reports for the dead calls, derived here independently |
| P-S1 `9e48a36b1dec91ee` | `conjecturer` 54 faults / streak 54 / 13.1 min, kind `connect_failure` | **54**, the count in that run's `workflow-provider-attempt-v1` objects — and a DIFFERENT kind from P-A1's, which is the distinction the policy turns on |
| `retired-transport-timeout180-run-42ad288038dd606c` (committed) | 1 fault, 4 attempts, kind `zero_byte_close` | now a committed-evidence fixture in the suite |

No committed root was written to. The one root opened writably in a test is a
`shutil.copytree` copy under `tmp_path`, never the root itself.

## 4. What the gate caught, and why it is recorded here rather than smoothed

`test_every_dropped_field_the_managed_path_can_set_round_trips` — the regression
test for audit finding P10, where five switches were silently reverted — failed.
Not a fixture nit. The first design made the new knob a nested `Config` MODEL,
and `_strict_carried_value` refuses to coerce a carriage notice's dict back into
a model ("a record must not buy a run by coercion"), so **no pydantic-model
`Config` field can round-trip at all**. A `run-config.yaml` setting it would have
compiled, emitted its notice, and then refused to rebuild — fail-closed rather
than P10's silent revert, but a knob that breaks the run when you use it is not
"customisation is easy" (2026-08-26) and not operations parity (2026-08-13).

Three scalars instead, which is what every other dropped knob already is; all
three verified to round-trip. **The granted frozen-surface contact widened from
ONE `data.pop` line to THREE as a result** — disclosed in `FIX.md` Amendment 3,
in the grant record itself, and in the delivery report, not absorbed. Still
unconditional, still four spaces, still **11 insertions and 0 deletions** against
the tranche base.

## 5. Live attempts — two, the maximum this workflow allows

`GOAL.md` did not require live proof; the tranche instruction offered ONE
optional guarded check "only if P2 held", and `dr-verify-outcome` allows one
relaunch. Both are recorded, including the one that proves less than hoped.

### Attempt 1 (`probe/raw/LIVE_attempt1.json`) — the mechanism, confirmed

The SHIPPED client, not the probe script, at a cap the probe proved cannot
finish inside the wall, policy at its default:

```
transport_diagnostics[0] = "RemoteDisconnected: ..."   <- the wall, ~300 s
fault_kind = "zero_byte_close"   zero_byte_returns = 1
streamed_attempts = 3
transport_diagnostics[1..3] = "_TransientBody: null content (finish_reason='length')"
elapsed 1048.167 s
```

Read precisely: the non-streaming attempt met the wall and was **classified
correctly**; the policy **retried as a stream**; and the streamed attempts **did
not die at the wall** — they ran ~249 s each, were read through to their
terminal chunk, and parsed cleanly into the non-streaming shape (a truncated
body would have raised "stream ended without a terminal chunk", and a
`null content` diagnostic can only arise AFTER a successful parse). That is the
mechanism end to end, on the real endpoint.

What it did NOT produce is a usable answer, and the cause is not the transport:
glm-5.3 with the reasoning knob omitted spent the whole 49 152-token cap on
thinking and returned `finish_reason: 'length'` with null content. That is the
reasoning-burn phenomenon the P-A1 monitor review already recorded, owned by the
model-profile window, reproduced here incidentally by running at P-A1's own
configuration.

**The honest statement for that configuration:** it used to fail as a TRANSPORT
fault after 1215 s of four identical resends; it now fails as a typed,
correctly-attributed CONTENT failure after 1048 s, with the record naming the
wall it met. The wall fix does not make this configuration answer. It stops the
wall being the reason and makes the real reason visible.

### Attempt 2 (`probe/raw/LIVE_attempt2.json`) — INCONCLUSIVE for the fixed path

The relaunch, with `allow_empty_content=True` (the harness's own shape for a leg
where an empty answer is still a leg that ran), to show what attempt 1 could
not — the streamed reply's own usage.

```
elapsed 271.480 s   transport_attempts = 1   streamed_attempts = 0
zero_byte_returns = 0   transport_diagnostics = []
usage = {"prompt_tokens": 75, "completion_tokens": 49152, "total_tokens": 49227}
```

**It never reached the fixed path.** The same call, same cap, same prompt
finished on its FIRST non-streaming attempt in 271.5 s — under the wall — so no
fault occurred and nothing was streamed. Inconclusive for the streamed path, and
said so rather than counted as a pass.

It is not a wasted call. 49 152 completion tokens in 271.5 s is **181 tok/s**,
against the **~92 tok/s** every probe arm measured an hour earlier — a **2x
throughput swing on the same model and cap**. That is a measurement in its own
right, and it explains two things the probe left open: why the same call lands
either side of a fixed 300 s wall from one hour to the next, and P-A1's lone
839 s non-streaming success, which needed no special mechanism if throughput can
halve.

It also shows a non-streamed reply reporting a full usage block. The claim that a
STREAMED reply does too rests on probe arm `H1`, which measured it directly, and
on the offline tests — not on this attempt.

## 6. Verdict

**PASS (offline), CONFIRMED-live for the mechanism, INCONCLUSIVE-live for the
end-to-end answer.**

Every clause of `GOAL.md`'s machine-decidable criterion passes and is
mutation-proven; the whole-tree gate is 0 failed; the live attempt confirms the
wall, its classification, and the streamed retry surviving it on the real
endpoint. What no live attempt showed is a streamed retry returning usable
CONTENT, because the configuration that reliably reaches the wall is also the
one that burns its cap on hidden reasoning. The offline regression remains the
proof of correctness, as this workflow requires.

## 7. Residue (honest)

- **No live call has returned usable content through the streamed retry.** The
  configuration that reaches the wall (large cap, reasoning unset) is the one
  that burns the cap on thinking; a configuration that answers is fast enough to
  finish under the wall. Fixing that is the model-profile window's, not this
  one's. The offline stub proves the reassembly; the live record proves the
  survival; nothing yet proves the pair together.
- **P-A1's 839 s success is now PLAUSIBLY explained** by the 2x throughput swing
  measured in attempt 2, but not demonstrated. Downgraded from "anomaly" to
  "unconfirmed explanation" — no more.
- **The mechanism is narrowed, not identified.** An idle-gap timer and a
  first-byte deadline both predict every measured row; no arm was slow enough to
  its first byte to separate them. Ruled out: a queue-admission deadline, and a
  cap on total duration.
- **The failing component is not named.** Client-side an edge close and a proxy
  close are the same bytes; `recentRelayFailures` clears only this container's
  own relay.
- **One afternoon, one key, one container.** Nothing shows the wall is stable
  over time, across accounts, or across regions.
- **A dead seat still kills a run** (`PARKED.md` P1), and the streak notice does
  not stop a run (operator disposition, road A).
- **`CON-run-identity.md:298` cannot pass** at 357 s against a 300 s ceiling —
  found here, not this tranche's, parked as P7.
- **The granted contact widened from one `data.pop` line to three**, for the
  reason §4 gives. Disclosed, not absorbed.

## 8. Errata

`docs/ERRATA.md` **E68** — `experiments/2026-08-26-pc2-rematch/PREREG.md:479-480`
claimed "six consecutive 180-second socket timeouts" and "NO ERROR TEXT ANYWHERE
IN THE RECORD". Its own diagnostic blob shows FOUR attempts — one client read
timeout at 180 s, then three `RemoteDisconnected` — with the error text present,
and the arithmetic that fits is 300.5 s per disconnect. **The wall was in the
committed record on 2026-08-26 and was read as a client timeout for a week.**
