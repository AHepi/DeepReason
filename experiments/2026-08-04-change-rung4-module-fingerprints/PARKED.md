# Parked — rung 4 (module fingerprints)

Noticed during this tranche, deliberately NOT done here. C2 requires this
file to hold everything observed but not acted on; nothing below is a
licence to act on it in this tranche.

## Scope deliberately left for a later tranche

P1. **The other two registries.** `VerifierRegistry`
(`verification/registry.py:30`) and `WORKLOADS`
(`workloads/registry.py:30`) both pin a fingerprint at registration and
re-check on resolve, exactly as `SCHOOL_POPULATION` does (M4), and
neither writes it into the run's record. A1 was not overridden by
Amendment 4, so this tranche stamps `SCHOOL_POPULATION` only. Extending
the same payload to the other two is mechanical — `ModuleFingerprintV1`
already carries a `registry` field precisely so the list can grow
without a schema change — but it is a second decision and it is the
operator's, not mine.

## Observations about the framework, recorded per C3 (not written to
## docs/ERRATA_EXECUTOR.md — that ledger has one writer)

P2. **`DR-INV-frozen-surfaces`' `Owns:` line and its numbered surface
list disagree about scope, and this rung is where it bit.** The `Owns:`
header names four whole FILES; surface 2's own heading narrows to
"event application and well-formedness". A change touching the
`record_*` seam is inside the file and outside the named behaviour, and
the document does not say which reading governs. This tranche needed an
operator sentence (R18) to resolve what a one-line addition to the
document could resolve permanently. Evidence: `docs/map/
INV-frozen-surfaces.md` header vs. its `### 2.` heading; this tranche's
SPEC.md D6.

P3. **The `Config` precedent in `INV-frozen-surfaces` still reads as an
unqualified invitation.** "Where authority is allowed to live instead"
says "A `Config` value costs nothing to add and is invisible to replay",
and only the final `Traps` entry — 200 lines later — records that this
is false without an explicit `_versioned_source_config_data` line.
Rung 4's M1 re-measured it independently and found the damage is WIDER
than the Traps entry records: the qualification SUBJECT digest moves,
not only the manifest sha. A reader who stops at the invitation gets a
surface-5 violation. Evidence: this tranche's SPEC.md M1/M2.

P4. **`Scheduler.__init__` gates school initialization on
`config.N_SCHOOLS > 0` (`scheduler/scheduler.py:272-276`), so a run with
zero schools resolves no backend at all.** Not a defect and not fixed
here — this tranche's writer deliberately fires outside that gate (D7)
so the record is honest for such runs — but it means "which modules
built this run" and "which modules this run USED" are different
questions, and only the first is answered by rung 4.

P5. **`tools/root_sweep.py` compares four fields and no more.** Its
byte-identity guarantee is therefore exactly as strong as its field
list, which is the gap C13 exists to close. Rung 4 closes it for one new
observable (S6/S12); every observable added before C13 existed remains
unprobed. Whether any of them is worth a retrospective probe is a
question for the operator, not a defect claim.
