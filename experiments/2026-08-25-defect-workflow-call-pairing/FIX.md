# Fix: give the verifier's pairing check the same empty→absent translation its writer performs

Cause (DIAGNOSIS.md): `invariants.py:398` compares `attempt.raw_ref == call.raw_ref` across two
types that spell absence differently — `ProviderAttemptV1.raw_ref: str | None` (absence is
`None`) and `LLMCall.raw_ref: str` (absence is `""`). The writer that builds the one from the
other applies `or None`; this reader does not.

## The change

    # src/deepreason/invariants.py, inside the workflow-call-pairing exact-pair comparison
    -                and attempt.raw_ref == call.raw_ref
    +                # LLMCall spells an absent raw blob "", ProviderAttemptV1 spells it None;
    +                # record_provider_attempt writes the attempt through `call.raw_ref or None`,
    +                # so the reader must compare on the writer's side of that translation.
    +                and attempt.raw_ref == (call.raw_ref or None)

One comparison. The right-hand side is copied verbatim from
`workflow/transaction_service.py:529` (the writer) and from `workflow/replay.py:2499` (replay's
copy of these same six agreements), so the three sites now spell one rule one way instead of two
ways. The comment states the constraint the code cannot show, per CLAUDE.md's comment rule; it
does not narrate the change.

**Not** widening `LLMCall.raw_ref` to `str | None` instead. That is the writer/format side of a
frozen surface, it would move the shape of every logged `llm` payload, and `INV-frozen-surfaces`
governs the choice directly: "readers may be fixed freely, writers and formats may not."

Accompanying, in the same commit:

  1. `scripts/cycle_soak.py` — empty `EXPECTED_RED`. Its sole entry, `D4-reservation-bound`, is
     STALE: `experiments/2026-08-23-fix-reservation-bound-authority/` landed, and this tranche's
     own soak run reports `[PASS] D4-reservation-bound`. The owning tranche's parked prompt
     required whoever cleared it to delete the entry; it was not deleted. Leaving it makes exit 3
     meaningless, which is what `docs/AUDIT_BASELINES.md` warns against. With the map empty,
     `_verdict`'s `only_expected_red` is `bool(failed_seams) and all(None ...)` → always False, so
     exit 3 becomes unreachable rather than silently wrong — the honest state.
  2. `docs/AUDIT_BASELINES.md` — the `--induce-repairs` paragraph currently records "the soak
     currently exits 1 on a `workflow-call-pairing` violation, parked as P1". That becomes exit 0.
  3. `docs/map/SUB-verification.md` and `docs/map/SEAM-llm-x-workflow.md` — a `Traps` entry each,
     naming this reproduction, with an executable `check:`. Same commit as the code, per SCHEMA.md.
  4. `docs/map/INV-frozen-surfaces.md` — the granted contact recorded under surface 3.

Expected diff: well under the 150-line budget; one production line, the rest tests and documents.

## FROZEN SURFACE GRANT REQUEST — surface 3, `invariants.py` (requested BEFORE implementation)

The tranche instruction forecast this contact and directed that the grant be requested here for
the monitor to review, not in chat. `tools/blast_radius.py --files src/deepreason/invariants.py
--symbols verify_root` reports, verbatim:

    "frozen_surface_verdict": "CONTACT"
    "frozen_surface_contacts": [
      {"surface": "replay-validation record formats (invariants.py)", "tier": "DIRECT",
       "target": "src/deepreason/invariants.py",
       "detail": "target file is surface path src/deepreason/invariants.py"},
      {"surface": "replay-validation record formats (invariants.py)", "tier": "SYMBOL_INDIRECT",
       "target": "verify_root",
       "detail": "'verify_root' referenced in src/deepreason/invariants.py
                  (grep-based; not proof of semantic contact)"}
    ]
    "frozen_adjacent_contacts": []
    "qualification_digest": []      "wheel_smoke_pins": []

Disposition of each row:

  - **DIRECT, `invariants.py`.** Accepted, and unavoidable: the defect IS this file. The change is
    a READER fix — the class of contact this surface has been granted three times before
    (2026-08-21 seat-instance anchor, 2026-08-22 `standing-integrity`, 2026-08-24
    `cascade-integrity`).
  - **SYMBOL_INDIRECT, `verify_root`.** Same file, same one comparison; no new finding name, no
    new check, no change to `_EPISTEMIC_CHECKS`, `report.py`, or any channel classification. The
    `SUB-verification` trap "a new `fail()` name defaults to integrity" does not apply — no name
    is added.
  - **`qualification_digest` and `wheel_smoke_pins` both empty.** No manifest field, no `Config`
    field, no console entry point, no MCP schema. Surfaces 4 and 5 stay at zero.

### The reader-vs-writer asymmetry, argued

The governing principle of `INV-frozen-surfaces` is an asymmetry, not a prohibition: *"readers
may be fixed freely, writers and formats may not,"* because *"a change that alters what a FUTURE
run may do is ordinary work; a change that alters how a PAST run verifies is a defect."* This
change is on the permitted side of both halves:

  - **It is a reader.** No record is written differently. `ProviderAttemptV1`, `LLMCall`, the log
    envelope, the object store and every digest are untouched. A run recorded before this fix and
    a run recorded after it are byte-identical.
  - **It only ADDs an authorized value.** `DR-SUB-verification`'s own `Traps` section states the
    sanctioned direction for this exact file: *"the predicate may only ever ADD authorized
    values, never remove one, or a committed root changes meaning."* Before: the pair is accepted
    iff `attempt.raw_ref == call.raw_ref`. After: that, plus the single case
    `attempt.raw_ref is None and call.raw_ref == ""`. Every pair accepted before is accepted
    after; exactly one new pair is accepted, and it is the pair the writer is guaranteed to
    produce.
  - **No committed root can reach the changed predicate — measured, not asserted.** The predicate
    can only re-decide an event whose `LLMCall.raw_ref` is empty. Across all 14 committed run
    roots carrying `objects/workflow-provider-attempt-v1/` — 459 attempts in total — there are
    **0** with `outcome: "transport_failure"` and **0** with `"raw_ref": null`. Every committed
    attempt is a `provider_result` with a real blob. The census, recomputable in seconds, is the
    instrument the 2026-08-21 grant established as stronger than a sweep, because it says why no
    verdict COULD move rather than that none did:

        find experiments runs -path '*workflow-provider-attempt-v1/*.json' \
          -exec grep -l 'transport_failure' {} + | wc -l      # -> 0
        find experiments runs -path '*workflow-provider-attempt-v1/*.json' \
          -exec grep -l '"raw_ref": null' {} + | wc -l        # -> 0

### One honest difference from the three prior grants

Those were **insertions-only** (52+1, 87+1, 11+0 lines, zero deletions), and additivity carried
the safety argument on its own. This one is a **one-line modification** — `-1 +1` — so that
argument is not available and is not being claimed. The safety argument here is the census above
plus the ADD-only direction of the predicate: no committed root contains an event this line can
decide differently, and no accepted pair becomes rejected. Stated plainly so the monitor is
weighing the real shape of the change.

### What the fix must not become

The check must not go blind. `attempt.raw_ref is None` may pair with an ABSENT call raw and
nothing else — a call that carried a body while the durable attempt recorded none is still a
violation, and so is the mirror. REPRO.md's six mutation tests exist to hold that line, and their
evidential value is post-fix: they are only meaningful once the unmutated root verifies clean.

## Verification plan (GOAL.md's success criterion)

    python -m pytest tests/test_v6_transport_failure_pairing.py -q          # 7 passed
    python -m pytest tests/test_v6_controller3_replay_verification.py \
                     tests/test_v6_engaged_repair_verification.py \
                     tests/test_v6_live_repair_transactions.py \
                     tests/test_invariant_call_outcomes.py -q               # ring, while iterating
    python -u scripts/cycle_soak.py --case epoch3 --induce-repairs 2        # exit 0
    python -u scripts/cycle_soak.py --case epoch3                           # exit 0 (bare baseline)
    python -m pytest tests/ -q -n 4                                         # gate: 0 failed
    python tools/docs_verify.py                                            # full, not --fast

Plus a re-run of the census above at HEAD, to show the two zeroes did not move.
