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

Whole-tree gate:

```
$ python -m pytest tests/ -q -n 4
4624 passed, 6 skipped in 1622.68s (0:27:02)     rc=0
```

**0 failed.** Not on the first attempt: the gate found one failure in 4 624, and
it was a real defect in this tranche's design rather than a fixture — see §4.

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

## 5. Live attempt

_PENDING — the single guarded live check is running; its typed result is appended here when it lands._
