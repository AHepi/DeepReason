# VERIFY.md — qualification circuit breaker (defect P7-A)

Verified 2026-08-29 against `GOAL.md`'s six falsifiable criteria. Offline by
construction: no provider credential exists in this container, so no live run
was attempted and none is claimed.

## Criterion command and output

    $ python <criterion.py>          # one assertion block per GOAL.md criterion

      PASS  C1 bounded+per-route: dead route 20 cases (was 80); healthy routes
            40 each; 8/10 pairs still qualified
      PASS  C2 transient does not trip: circuit_breaker None, all 80 cases
            dispatched
      PASS  C3 records differ: 401 -> ['CIRCUIT_OPEN_ENDPOINT_HTTP_401',
            'ENDPOINT_HTTP_401']; 429 -> ['CIRCUIT_OPEN_ENDPOINT_HTTP_429',
            'ENDPOINT_HTTP_429']
      PASS  C4 OFF is exhaustive + typed warning, never a refusal; the second
            road to OFF (empty prefixes) warns too
      PASS  C5 report complete and round-trips: 20 synthesized cases,
            case_count 200 == 10x20
      PASS  C6 no Config field added: source_config_hash unchanged at
            6c2d01f6b8cbe65e...

      6/6 criteria PASS

`GOAL.md` criterion 5 is the modularity obligation, and the script above
tested the record instead. Run separately, as its own criterion:

    $ python -m pytest tests/test_qualification_circuit_modularity.py -q
    9 passed in 5.76s

Recorded rather than quietly re-mapped, because a criterion checked by the
wrong command is exactly the failure this tranche was reviewed for.

## Ring

    $ python -m pytest <8 doctor/qualification/endpoint test files> -q
    216 passed in 173.68s

Baseline on the clean tree before the fix: **190 passed** (`proof/ring_before.out`).
+26 tests, 0 failed.

## Criterion-by-criterion verdict

| # | GOAL.md criterion | verdict | evidence |
|---|---|---|---|
| 1 | stops after a bounded number of cases, PER ENDPOINT/ROUTE | PASS | dead route 20 of 80 cases; four healthy routes fully measured; 8/10 pairs still qualified |
| 2 | a transient condition that clears does NOT trip it | PASS | 19 failures + 1 success leaves `circuit_breaker is None` and dispatches all 80 |
| 3 | the record distinguishes the two conditions | PASS | pre-fix both wrote `{'ENDPOINT_ERROR': 360}`; now `ENDPOINT_HTTP_401` vs `ENDPOINT_HTTP_429` plus distinct `CIRCUIT_OPEN_*` |
| 4 | switchable OFF by configuration, with a TYPED WARNING | PASS | `..._DISABLED`; and the second road to OFF (`code_prefixes=()`) emits `..._INERT` |
| 5 | behaviour change never requires a code edit | PASS | 9 architecture tests, incl. a 500-status sweep and a retarget-by-environment pair |
| 6 | no new knob moves a qualification subject digest | PASS | no `Config` field exists; `source_config_hash` byte-unchanged |

## The offline evidence, regenerated

    $ python .../proof/measure_account_level_battery_cost.py     # 18.7 s

| mode | HTTP calls | mandated wait | record |
|---|---|---|---|
| PRE-FIX 401 | 360 | 0 s | `{'ENDPOINT_ERROR': 360}` |
| PRE-FIX 429 | 1440 | **5040 s (84.0 min)** | `{'ENDPOINT_ERROR': 360}` |
| FIXED 401 | 20 | 0 s | `ENDPOINT_HTTP_401` + `CIRCUIT_OPEN_…401` |
| FIXED 429 | 80 | 280 s | `ENDPOINT_HTTP_429` + `CIRCUIT_OPEN_…429` |

Pre-fix, the two reports are identical in **all 83 035 bytes**, not merely in
their failure-code multiset. Independently re-derived from source: 15 pairs ×
20 = 300, +3 re-exercised pairs × 20 = 360 executed cases; a 429 walks 4 calls
and 3 sleeps of 2+4+8 = 14 s, so 360 × 4 = 1440 calls and 360 × 14 = 5040 s.

## Historical roots

Not applicable, and stated rather than skipped: this fix changes no reader and
no validator. It adds one OPTIONAL top-level field to a doctor report and
changes the VALUE of `cases[].failure_code` for transport conditions. 62 of 63
committed doctor reports still load; the one failure
(`experiments/live_engaged_2026-07-27/run-f4fa6663…`, `DOCTOR_REPORT_NONCANONICAL`)
is **pre-existing** — it fails identically at the tranche base `08c2d7bd1`.

## Live attempt

None. No `OLLAMA_API_KEY` and no provider reachable. Every claim above is a
compile-time or read-time property of committed code and generated offline
evidence.

## Verdict

**PASS-offline. Live: NOT ATTEMPTED** (not "inconclusive" — nothing was run).

## The part of this record that matters most: it passed once while wrong

The first implementation (`70fdef7e6`) satisfied its own criteria, its own
review, and a full gate at **4475 passed / 0 failed** — and was wrong in six
places. They were found by an independent skeptic re-running the claims rather
than reading them, and every one is fixed with a regression test:

| # | defect that shipped | how it was caught |
|---|---|---|
| 1 | **R7 and R8 were vacuous** — both green on a tree with no breaker in it; deleting the short-circuit left four tests green | ran the assertions verbatim against `git archive 08c2d7bd1` |
| 2 | **"never trips ⇒ byte-identical" was over-broad** — true for an all-admitted battery, false for 1-19 transport failures per block | generated reports on both trees and compared bytes |
| 3 | **the resolver crashed the battery** on `'²'` (`isdigit()` true, `int()` raises), contradicting its own docstring | hostile-value sweep |
| 4 | **a reconfigured gate that never fired left zero trace** | ran a non-default policy against a healthy battery |
| 5 | **`code_prefixes=()` silently disabled the gate** — two roads to OFF, one silent | constructed the second road |
| 6 | **the explicit road refused what the environment clamped** | called both roads with the same value |

Two claims of mine were also overstated and are corrected on the record:
"that battery took about a minute" was an INFERENCE stated as a measurement
(the invocation was manual and has no committed timing at all), and C1's
target list is FOUR documents, not two.

## Residue — honest

- **No live run, and none possible here.** The breaker has never fired against
  a real provider. Every direction is proven against the shipped code with the
  socket and clock faked, which is strong evidence about the harness and no
  evidence at all about a real 429.
- **The bound is guaranteed only for a uniformly-arming block.** With the
  shipped `minimum_block_failures = 20`, a single non-arming failure anywhere
  in a block prevents that block from opening the circuit, so a subject where
  every block carries one such failure degrades to the full pre-fix cost.
  GOAL.md criterion 1 holds as measured, not universally. The knob lowers the
  threshold and lowering it now emits a warning.
- **Per-route keying is not observable on the default subject.** All 15 pairs
  of a single-profile qualification subject share one `(endpoint_id,
  route_sha256)`. It becomes load-bearing only for seat-bound or multi-route
  configurations; the 10-pair, 5-endpoint test fixture is where it is proven.
- **`derive_route_seat_model_classification` consumes synthesized cases.**
  Cases no provider ever answered flow into a model-behaviour classification
  and yield `unqualified_exact_behavior`. The verdict is unchanged from
  pre-fix (an exhaustive 401 battery produced the same class), so this is not
  a regression — but §1's frozen-surface disposition presented itself as
  complete and did not analyse it.
- **`cases[].failure_code` reaches the BUNDLE digest**, so a battery with some
  transport failures writes different bundle bytes than it would have
  pre-fix. It does NOT reach the SUBJECT digest — `pair_payload()` excludes
  `cases` — so no home owes a re-battery.
- **Parked and untouched:** C1 (now an ERRATA entry, below), C3, C4 (needs
  frozen surface 5), C5 (made strictly less reachable), C6.
- **No committed test exercises determinism with the breaker ACTIVE.** The
  committed parallelism test uses a fixture whose only failure code is
  `SCHEMA_EXHAUSTED`, which does not arm the breaker. The reviewer closed the
  gap by hand (sequential vs 8-worker with randomised sleeps: reports equal,
  openings identical); it is not committed as a test.

Accepted does not mean true.

## Errata

**Three entries, landed in the same commit as this file:**

- **E62** — the "18 minutes" figure is unsupported by any committed record,
  and FOUR documents carry it (not two). The cited evidence file records a
  401 from an empty key; a 401 is not retryable, so the ladder never slept.
  The only provenance any carrier offers is a wall-clock interval that appears
  nowhere in the repository but its own sentence.
- **E63** — `BATCH.md` §5 published 260 cases / 3640 s as its headline
  evidence; those are the lost lane's figures and match no commit in this
  branch's ancestry (the subject has been 15 pairs throughout). Corrected in
  place on the operator's instruction, superseded figures preserved.
- **E64** — `AUDIT_BASELINES.md` states the docs_verify corpus at "1212 checks
  over 69 documents"; `main` already holds 70 documents and 1246 checks. The
  FAILURE list, which is what the baseline exists to pin, is exact. Left
  uncorrected: that file is outside this cone and the restatement wants a full
  clone.
