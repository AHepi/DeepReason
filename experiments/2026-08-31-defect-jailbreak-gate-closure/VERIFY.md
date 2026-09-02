# Verification

## The one line that matters

    jailbreak_open:  True  ->  False

Same probe, same committed root, same one-byte forgery, on this tranche's
before and after tree. `proof/RED-forge_amend_ready.txt` and
`proof/GREEN-forge_amend_ready.txt`.

## Criterion command + output

GOAL.md's success criterion, run verbatim.

**1. The acceptance probe** —
`python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_amend_ready.py`

| | BEFORE (HEAD `7f11c0718`) | AFTER (HEAD `a05bbb2d5`) |
|---|---|---|
| forged · `verify_root_violations` | `['attempt-route','frozen-route']` | `['attempt-route','frozen-route']` |
| forged · `stored_replay_valid` | `True` | `True` |
| forged · **`amend`** | `ACCEPTED epoch=1` | **`REFUSED AmendmentError: AMEND_RECORD_NOT_VERIFIED: the record does not verify on the security channel: attempt-route, frozen-route`** |
| forged · **`continue`** | `ACCEPTED seq=0` | **`REFUSED ValueError: CONTINUE_RECORD_NOT_VERIFIED: the record does not verify on the security channel: attempt-route, frozen-route`** |
| forged · `results_amend_ready_verify` | `True` | **`False`** |
| **intact · `amend`** | `ACCEPTED epoch=1` | **`ACCEPTED epoch=1`** |
| **intact · `continue`** | `ACCEPTED seq=0` | **`ACCEPTED seq=0`** |
| **`jailbreak_open`** | **`True`** | **`False`** |

Both halves of the criterion are met: the forged arm refuses BOTH verbs, and the
intact arm still accepts both. A gate that refused everything would satisfy the
first half and fail the second.

The prior tranche's `forge_amend_ready.json` was restored byte-for-byte after
each run (`git status` over that directory is empty) — it is that tranche's
recorded measurement, not this one's scratch file. This tranche's copy of the
after-state is `proof/forge_amend_ready_after.json`.

**2. Full gate** — `python -m pytest tests/ -q -n 4`

    4599 passed, 6 skipped in 1098.99s (0:18:18)

**0 failed.** 4590 baseline + 9 new tests in `tests/test_jailbreak_gate.py`. No
assertion weakened, no test skipped, no test root exempted. Exactly ONE fixture
changed, and FIX.md predicted it before the edit: the exact-set golden on the
`terminal` block at `tests/test_results_command.py:504-511` gains the new key
and remains an exact-set equality.

**3. docs_verify** — `python tools/docs_verify.py` (FULL, not `--fast`)

    docs_verify [full]: 71 documents, 1291 checks, 4 workers
    docs_verify: 5 failed

All five are on `docs/AUDIT_BASELINES.md`'s recorded list for this container
class (a shallow clone): `SEAM-llm-x-rules.md:54` (unparseable check, parked
P3), `CON-run-identity.md:211/:213/:215` (git-history checks needing a full
clone), `INV-frozen-surfaces.md:181` (rotted claim, parked P-D3).
**Delta beyond the recorded list: none.** `--audit` reports 1 finding, the same
parked unparseable check.

`python scripts/wheel_smoke.py` — passed; MCP tool set and exact schema shas
unchanged, so the public surface did not move.
`python tools/diff_budget.py e777e3b94 --ceiling 150` — `verdict: WITHIN`,
133 insertions.

## The collision, answered before the fix was written

GOAL.md required the collision diagnosed before designing. It was, and the
answer decided the design: `verify_root`'s FULL violation set answers a broader
question than the operator's law. The 2026-08-30 attempt asked the broad
question and turned eight lifecycle tests red. Three of those eight assert roads
that REPAIR an invalid record, so they were never fixture defects.

Neither horn of GOAL.md's fork was taken blind. The fixtures are NOT invalid
records to be rewritten, and the gate WAS checking more than the security clause
requires. So the check was narrowed — to the SECURITY channel — and the result
measured rather than argued:

    the eight collision node ids, gate ARMED:   8 passed in 580.95s
    the three amend-path files, gate simulated: 65 passed, gate evaluated
                                                48 times, refused 0

Zero of the eight collide. `tests/test_jailbreak_gate.py::test_a_record_that_is_
merely_incomplete_still_passes_the_gate` turns that from a claim into a standing
test over two committed roots that are replay-invalid TODAY (four integrity
findings and one completion finding between them) and still continue and amend.

## Historical roots re-checked

The fix changes gates, not readers, so no committed root's verdict moves. What
was checked instead is that the gate SEPARATES —
`proof/security_channel_separation.json`, `separates: True`,
`predicate_source: shipped`:

| root | `verify_root` checks | SECURITY | gate refuses |
|---|---|---|---|
| `2026-08-26-pc2-rematch/run_h3` | — | — | no |
| `…/retired-transport-timeout180-run-42ad2880…` | — | — | no |
| `…/retired-truncation-cap32768-run-58fb0d20…` | attempt-accounting, attempt-blobs, attempt-order, repair-metadata | — | no |
| `2026-08-13-…/failed-epoch1-run-8e22d043…` | — | — | no |
| `2026-08-13-…/failed-epoch3-run-8e22d043…` | — | — | no |
| `…/selfstudy/runs/failed-epoch4-run-9175f0ec…` | — | — | no |
| `…/referee/runs/run-e542c3c1…` | foreign-criticism | — | no |
| `2026-08-12-live-grounded-extension-expansion/run` (12,991 ev) | — | — | no |
| `2026-08-27-pc2b…/run` (intact) | — | — | no |
| `2026-08-27-pc2b…/run` (**forged**) | attempt-route, frozen-route | **both** | **YES** |

## Mutation proof: the guards are not decoration

`proof/mutation_proof.json` — `baseline_all_green: true`,
`every_mutation_detected: true`. Four mutations of the shipped gate, each
reverted with `git checkout --` before the next:

| mutation | what it kills |
|---|---|
| neutralise the gate (always allow) | behaviour, gate tests |
| drop `continue`'s call site | behaviour, gate tests, CON-run-identity tripwire |
| drop `amend`'s call site | gate tests, tripwire, SUB-amendment code-count pin |
| **widen the channel filter to every violation** | **the collision guard** |

The fourth row is the one worth reading twice: it proves the NARROWING itself is
defended. A future tranche that "simplifies" the filter to the whole violation
set fails a committed test rather than rediscovering the 2026-08-30 collisions
by turning eight lifecycle tests red.

## The per-continue cost, measured, and the regression it caused

The gate is one `verify_root` per `continue` and per `amend`: ~30 ms/event,
essentially LINEAR (log-log exponent 0.91, r² 0.96), **356.76 s ≈ 5.9 min on the
largest committed root** (12,991 events, ~422 MB peak RSS). Not hours. But the
scatter is asymmetric — a pooled linear model under-predicts individual roots by
up to 55-72% — so the honest form is "about 30 ms per event, and budget half
again on top".

**It is paid even when the root would be refused anyway, and that had a
consequence I did not predict precisely enough.** FIX.md predicted "roughly +8
minutes on the full gate" and required this phase to measure rather than repeat
the estimate. Measured:

  - `tests/test_continuation.py` serially: **562.32 s (9:22)**, up from under a
    minute, because `test_a_stop_with_no_typed_receipt_refuses_continuation`
    sweeps 16 committed roots and each now pays a full re-derivation.
  - Full gate under `-n 4`: **18:18**, up from ~14 min — the +8.5 min largely
    parallelises away. Better than predicted.
  - **THREE `SUB-application.md` map checks then exceeded docs_verify's own
    300 s per-check ceiling.** Not flaky: at 562 s serial they could not pass.
    This was FIX.md's stop condition materialising in an instrument.

I did not weaken the gate to get past it and I did not exempt any test root
(the 2026-08-30 tranche's own pre-registered rule P-FIX-3, inherited by
GOAL.md). Each of the three checks paired a cheap `grep` — the actual claim —
with `python -m pytest <whole file>`. They were narrowed to the node ids that
exercise the claim, which is what the timeout message itself instructs and what
`SCHEMA.md` asks of a check. The one that named an expensive in-repo mirror
(`:504`) had it replaced by a grep pinning the SAME coupling — the refusal code
the wheel smoke demands must still be the code the product raises — not by
nothing. Result: 1 s and 21 s, and `--audit` still accepts all three as
falsifiable. A side effect worth naming: `AUDIT_BASELINES.md`'s
CONTAINER-CONDITIONAL row, which had flirted with that ceiling for two days at
54-71% of it, is retired by the same narrowing.

## Verdict

**PASS (offline).** No live run was attempted: GOAL.md's criterion is entirely
offline, this container has no API key, and the defect and its fix are both
fully exhibited on committed roots. Nothing about this fix is stochastic — it is
a deterministic predicate over a replayed record — so a live run would add
nothing a committed root does not already show.

## Residue (honest)

1. **DERIVED security findings are not gated.** The gate reads `verify_root`'s
   own violations. `verify_root_report` also derives security findings the
   replay stream does not produce, and those are invisible to the gate. This is
   deliberate and measured: on the 12,991-event root there are 494 of them, all
   `transaction-authority: unknown v6 task kind 'defended_trial_step'` — version
   skew under the 2026-08-14 law that old runs owe the future nothing, not
   tampering. Gating on them would refuse a lawful root. **What is NOT proven:
   that no real tamper produces ONLY derived-channel findings.** Parked, P1.
2. **A record too corrupt to replay is not refused.** `verify_root` returns the
   single check `open` on the integrity channel, so the gate passes it. `open`
   cannot simply be promoted to the security set: a legitimate v1-manifest root
   produces the same check name, and promoting it resurrects collision 2.
   Whether such a root is continuable at all is UNMEASURED. Parked, P2.
3. **Refusal latency.** An operator continuing a root that stopped for a
   non-resumable reason now waits for a full re-derivation (seconds to ~6
   minutes) before being told something the product could have told them
   immediately. The gate is correct where it sits — last precondition, before
   the first write — but it is not cheap where it does not need to be. Parked,
   P3, with the design sketched.
4. **The cone.** The fix writes `src/deepreason/runtime/continuation.py`, one
   file outside this tranche's declared cone. It is not a frozen surface
   (`blast_radius` returns `frozen_surface_verdict: CLEAR`), there is no in-cone
   alternative that meets the fixed done-criterion, and the 2026-08-30 tranche
   recorded and disposed of the identical discrepancy. Recorded, not smuggled —
   FIX.md states it, and it is the first thing to overrule if the operator meant
   the list strictly.
5. **A law reading that should be visible.** The 2026-08-28 law says "Gates are
   always optional: with warnings." This gate is not switchable, on the reading
   that the 2026-08-29 law names it a "Security boundary, not a convenience".
   One line to change if the operator disagrees.
6. **Not attempted:** narrowing `verify_root` itself so a security-only question
   costs less than a full replay. That would edit frozen surface 3 and is a STOP
   by construction.

## Errata

`docs/ERRATA.md` **E66** and **E67**, both in this tranche's commit.
E66: `gate_collisions.md`'s collision table names the wrong check set for row 2
(measurably `open`, not `run-input, run-manifest-hash, terminal-authority`), the
related PARKED F9 claim that a v1 manifest makes `verify_root` RAISE is wrong in
the same direction (it returns a violation, so no exception-arm special case was
needed), and that document's "What DID ship" table is superseded by the gate
landing. E67: `AUDIT_BASELINES.md`'s docs_verify totals and its two
`SUB-application` line-number anchors had drifted before this tranche touched
them, and moved again in its commit; both rows are re-anchored by what they run.
