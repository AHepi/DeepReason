# Verification

## Criterion command + output

**1. The reproduction the tranche inherited — `--induce-repairs`, the repair ladder reached.**

    $ python -u scripts/cycle_soak.py --case epoch3 --induce-repairs 2
      [PASS] A1-typed-terminal          state='completed' stop_reason='budget_exhausted' typed_error=None
      [PASS] A2-no-operational-failure  stop_reason='budget_exhausted'
      [PASS] A3-verify-root-clean       0 violation(s)
      [PASS] A4-cycles-reached          reached cycle 8 of 8 requested; the deepest recorded death was cycle 2
      [PASS] D1..D4 (all four seams reached)
      attempts.repairs == 1
    [soak] exit 0 (clean)

Before the fix, byte-for-byte on the same invocation: `exit 1`, `A3-verify-root-clean FAIL,
1 violation(s): [{'check': 'workflow-call-pairing', 'detail': 'event seq=31: provider result
differs from its authorized attempt'}]`. `repairs == 1` in BOTH runs: the repair ladder is
still exercised after the fix, not bypassed.

**2. The bare soak — the AUDIT_BASELINES baseline, unmoved.**

    $ python -u scripts/cycle_soak.py --case epoch3
      A1..A4 all PASS, A3-verify-root-clean 0 violation(s)
    [soak] exit 0 (clean)

Exit 0 is genuine rather than downgraded: `EXPECTED_RED` is now empty, so `_verdict` cannot
return 3 at all.

**3. The unit regression, mutation-proven in both directions.**

    $ python -m pytest tests/test_v6_transport_failure_pairing.py -q
    7 passed in 3.62s

    fix reverted     -> test_a_transport_failure_attempt_pairs_with_the_call_that_produced_it FAILS
    check blinded    -> test_a_dropped_raw_blob_still_fails_closed FAILS
    (`and (attempt.raw_ref is None or attempt.raw_ref == call.raw_ref)`, i.e. an absent attempt
     raw pairing with ANY call raw: `1 failed, 6 passed`)

Both directions matter and neither is redundant. The first says the fix is doing work; the
second says it did not buy that by going blind. Six mutations break one of the six pairing
agreements each and all still require the finding back.

**4. Ring, then gate.**

    $ python -m pytest tests/test_v6_controller3_replay_verification.py \
        tests/test_v6_engaged_repair_verification.py tests/test_v6_live_repair_transactions.py \
        tests/test_invariant_call_outcomes.py tests/test_v6_transaction_qualification.py \
        tests/test_v6_bridge_transactions.py tests/test_v6_contract_schema_repair_runtime.py -q
    123 passed in 372.68s

    $ python -m pytest tests/ -q -n 4
    4175 passed, 6 skipped in 814.33s (0:13:34)         # 0 failed

    $ python tools/docs_verify.py
    docs_verify: 3 failed        # the three known pre-existing shallow-clone CON-run-identity
                                 # checks named in the session handover; both new checks green
    $ python tools/docs_verify.py --links     ->  0 dangling reference(s), 64 document(s)
    $ python tools/docs_verify.py --audit     ->  0 finding(s)

    $ python tools/diff_budget.py origin/main --ceiling 150 \
        --paths src/deepreason/invariants.py scripts/cycle_soak.py
    "verdict": "WITHIN"

None of the five MCP-thread tests the handover flagged as flaky under `-n 4` flaked in this run.
The wheel smokes were NOT run and are not owed: `blast_radius.py` reports `wheel_smoke_pins: []`
and no console entry point, MCP tool, schema or wheel-layout surface was touched.

## Historical roots re-checked

The fix is a reader change, so rung 2 of the ladder applies. Targeted before/after over every
committed root carrying `objects/workflow-provider-attempt-v1/` — 14 roots, 459 attempts — with
the pre-fix `invariants.py` run from an isolated `git worktree` at `origin/main` so the working
tree was never swapped:

    failed-epoch1-run-40e713b30a147dfc…   0  {}                          <- the 17-repair reach-rich root
    run-f4fa6663e5412d64df943a5a22342baf  6  {"foreign-criticism": 6}
    void-inert-battery-run-6913328037a…   1  {"attempt-validity": 1}
    run-ac1836b6237b6e9d80b3b0cb492b39f5  6  {"foreign-criticism": 6}
    run-faa5feae126bc2558ea9c6d8d200a90c  3  {"foreign-criticism": 3}
    run-6dab80d615a437a8b3fa489a279df847  4  {"foreign-criticism": 4}
    run-c5ab654afd1b4aa131aede83bdca0f03  0  {}
    run-9ae94bb478990cbecca373fc3bcb1345  0  {}
    run-15a53aca8a6fc66a39f382fc688c5346  2  {"foreign-criticism": 2}
    failed-attempt3-run-bb045538…         0  {}
    failed-attempt2-run-bb045538…         0  {}
    failed-epoch{1,2,3}-run-8e22d0431…    0  {}   (each)

`diff before.txt after.txt` is EMPTY. Every violation class and count is unchanged, including
the 21 `foreign-criticism` and the 1 `attempt-validity` findings that were already there and
that this tranche did not touch and does not summarize away. The census explains why no verdict
could have moved: 0 of those 459 attempts are `transport_failure` and 0 have `"raw_ref": null`,
so no committed root contains an event the changed line can decide at all. The root sweep is
retired as an instrument (operator ruling 2026-08-22); this targeted before/after is the
cheaper and stronger form CLAUDE.md prescribes in its place.

## Live attempt

None, and none was owed. GOAL.md's success criterion is fully offline, and the tranche
instruction states it explicitly: "No API call is needed anywhere in this tranche; the soak
reproduces it offline." Zero provider spend.

## Verdict: PASS

## Which witness class proved it — the decision the parking note required

The defect rests on the **INDUCED witness plus a structural argument**, not on a natural one,
and this is stated rather than glossed. There is no natural witness in the committed record:
across 14 roots and 459 provider attempts, zero are `transport_failure`. The reach-rich epoch-1
root's 17 repair attempts are all `provider_result` with real raw blobs, and so is every attempt
in the epoch-3 lineage.

Their absence does not dismiss the defect, and the structural argument is what upgrades it past
"it happened once under a synthetic fault". The check was **unsatisfiable by construction** for
the whole `outcome="transport_failure"` class: `record_provider_attempt` builds every attempt
through `call.raw_ref or None`, so an empty call raw ALWAYS yields `attempt.raw_ref is None`,
and the old comparison was `None == ""`. Any dispatch that reaches a provider and gets no usable
body — an HTTP 500, a timeout, a reset — makes a run fail its own verifier. That is a plainly
reachable input, and the induced fault is a faithful stand-in for it rather than a special case.
Corroborating it from inside the surface itself: `verify_root`'s own `blobs` check already
permits exactly this empty raw (`empty_raw_allowed = bool(trace and trace[-1].usage_unknown)`),
so the file contradicted itself and one of the two readings had to be wrong on its own terms.

## Residue (honest)

- **No natural witness, and none may ever appear in the committed record.** Live runs against a
  healthy provider do not produce transport failures; that is why 459 attempts contain none. The
  fix is proven offline and structurally, not by a wild sighting. Recorded as such.
- **The other five agreements are guarded only by mutation tests, not by live records.** No
  committed root pairs a mismatched contract id or route lease either, so the six mutation tests
  are the whole of their behavioural coverage.
- **`--induce-repairs` reaches the repair ladder via a TRANSPORT fault, not a schema fault.**
  The inducer's HTTP 500s produce `transport_failure`; the soak reports `repairs == 1`, so a
  repair transaction is prepared, but the failing event this tranche fixed is the transport one.
  A schema-invalid-body repair attempt that dispatches and returns a well-formed but unusable
  response is a DIFFERENT shape, and it remains without an offline witness. Parked as P3.
- **`D1-seat-contract` reports `[PART]` on the bare soak.** Partial is not coverage, per the
  soak tranche's own standing honesty rows. Unchanged by this tranche and not this tranche's.

## Errata

`docs/ERRATA.md` E53 (PARKED.md P1 framed a transport failure as a repair defect and named two
suspects, neither of which was the cause) and E54 (`cycle_soak.py`'s `EXPECTED_RED` claimed a
fix was still in flight nine days after it landed), both added in the same commit as this file.

## One line, as the tranche instruction asked for it

**The repair ladder now writes what it always wrote — an attempt whose absent raw blob is spelled
`None` beside a call that spells the same absence `""` — and `verify_root` accepts it, because
the checker was given the translation its own writer performs; proved by the INDUCED witness
class (the offline cycle soak) plus the structural argument that the old check was unsatisfiable
for every transport-failure attempt, there being no natural witness in any of the 459 committed
provider attempts.**
