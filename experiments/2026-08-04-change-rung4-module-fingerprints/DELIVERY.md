# Delivered: rung 4 — every run records which modules built it
Branch: `claude/delivery-rungs-handover-m22sdy` @ `b5b1c6c3` (pushed, tree clean)
20 commits from tranche base `75783d11`.

## What changed

Every DeepReason run now records which registered module built it, in the
run's own append-only record, on ordinary runs rather than only on the
stochastic capability paths where the only existing fingerprints lived.

A new `src/deepreason/module_events.py` holds the typed payload
(`module-fingerprints.v1`): per module its registry, its id, the mapping
its own `fingerprint()` returns, and a sha256 over that mapping's
canonical JSON, plus a digest over the module list. It carries no
wall-clock, so two runs built by the same modules stamp byte-identical
payloads and any difference between two stamps is a difference in the
modules. The same module also holds `recorded_module_fingerprints`, the
absence-tolerant reader.

`Event` gains one optional `module_fingerprints` field with the same
`exclude_if` shape the five existing payloads use, so absence is absence
from the serialized bytes rather than a null in them — which is why no
committed root's bytes or verdict move. `Event._process_payload_contract`
gains a clause fencing the payload to `Rule.MEASURE` with inputs exactly
`[schema, digest]` and no outputs. `harness.py` gains the
operator-authorized `record_module_fingerprints` appender plus the
`_commit` keyword that carries the payload into the event.
`Scheduler.run` emits the stamp once per run, after workflow recovery,
only when cycles are actually requested.

No new `Rule`, so no new typed channel, so no `report.py` entry is owed
and `verification/` is untouched. `tools/root_sweep.py` gained a
`modules=` probe in its own separate commit, so "sweep byte-identical" is
evidence about the new observable rather than a statement about data the
sweep never reads.

**Proof:** full gate 3323 passed / 0 failed; `docs_verify` 805 checks / 0
failed, `--audit` 0, `--links` 0, `--coverage` 0; the 42-root sweep
byte-identical; three committed roots spanning all three census arms
unchanged at `62614bfc…`; frozen surfaces empty but for the authorized
`harness.py` appender, with `_apply_event` and the well-formedness path
byte-identical to the tranche base.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Route: `dr-change-orchestrator`" | done | phase artifacts in order; VALIDATION S1 |
| R2 | "registered modules stamp a fingerprint … into the run's TYPED RECORD" | done-with-assumption **A1** | `ebf595d6`, `0d1c4f0e`; VALIDATION S2 |
| R3 | "(the `CONTAINED_WORKER_SHA256` precedent …)" | done-with-deviation, recorded | SPEC M3/D2: SHAPE adopted, LOCATION rejected because the precedent only fires on stochastic capability paths. Advisory per C8/C11, not binding |
| R4 | "the fingerprint rides Config and typed log/object records" | **partly superseded by R17** | Config half CLOSED by the operator's own choice of Option B; typed-log half done (`4076d8e4`). Recorded, not quietly dropped |
| R5 | "NEVER a new manifest field" | done | `run_manifest.py` empty diff; VALIDATION S7 |
| R6 | "NEVER anything entering the qualification subject digest" | done | `qualification.py` empty diff; no `Config` field added |
| R7 | "If the design cannot avoid the manifest … DESIGN-AND-STOP" | done | the tranche DID stop; Amendment 4 resolved it |
| R8 | "the reader must treat ABSENCE … as valid before the writer emits it" | done | reader `07321679`/`e186616c`, field `4076d8e4`, writer not until `ebf595d6`; VALIDATION S3 |
| R9 | "Accept: full gate" | done | 3323 passed, 0 failed (`ed50d4cf`) |
| R10 | "sweep byte-identical (absence-tolerant reader proven by the sweep itself)" | done | `b455e987` + probe `6b79df7f`; VALIDATION S5/S12 |
| R11 | "Next Rung" — exactly one rung | done | rungs 5-7 untouched; other registries parked (P1) |
| R12 | "Proceed to dr-spec-change" | done | `50dfb208` |
| R13 | "On Q5: verify against the real write path" | done | SPEC M1-M5, measured against the live tree |
| R14 | "prefer any design with zero frozen-surface contact" | done as a preference | Option C was the zero-contact design, priced and rejected on the record for not delivering R2; operator chose B knowingly |
| R15 | "DESIGN-AND-STOP … do not assume rung 2's approval carries over" | done | no appeal to rung 2; Amendment 4 is this tranche's own authorization |
| R16 | "any new typed channel must land its report.py entry … or not exist yet" | done | no new `Rule` (15 before, 15 after); `verification/` untouched; VALIDATION S9 |
| R17 | "Option B approved." | done | `4076d8e4`, `6fc75bfb`; no `config.py`/`run_manifest.py` hunk |
| R18 | "record_* appender … appender only, no change to _apply_event or well-formedness" | done-with-deviation, declared | `6fc75bfb`; three hunks not two (the `_commit` annotation needs an import), declared in CHECKLIST step 9 BEFORE the commit. Both stated exclusions hold byte-identically |
| R19 | "Ledger this quote … then plan and proceed" | done | `1f9d0f8e` precedes all spec/plan work |
| R20 | "Include the sweep probe proposal for the new observable" | done | SPEC S6/S12; probe committed alone at `6b79df7f` |

No requirement is `not-done`, and none is deferred.

## Assumptions the operator may override

**A1 — the one that most wants your word.** "Registered modules" =
`SCHOOL_POPULATION` only. Your Amendment-4 reply was silent on SPEC.md's
direct question ("`SCHOOL_POPULATION` only, or all three registries?"), so
per the scope contract the smallest reading stands. `VerifierRegistry` and
`WORKLOADS` pin fingerprints the same way and record none;
`ModuleFingerprintV1` already carries a `registry` field precisely so the
list can grow without a schema change. Extending is mechanical — but it is
your decision, not mine.

A2 — the fingerprint rides an optional payload on an existing record
rather than a new channel. Confirmed correct: no channel, no `report.py`
entry, surface 3 untouched.

A3 — C13's rule adopted as written: a byte-identical sweep does not by
itself prove absence-tolerance. Confirmed by the probe's mutation test.

## Deviations you should see

1. **Validation round 1 FAILED, and the failure is kept in the record.**
   The payload had no `Event._process_payload_contract` clause, so an
   event pairing it with `Rule.CONJ` and empty inputs was accepted and the
   reader reported it as a genuine stamp. Invisible to every green
   instrument — gate, 805 map checks, sweep — because no test built such
   an event. Closed by steps 25-30; re-validated PASS.
2. **Two writer-placement defects the gate found**, escalated to SPEC.md
   as D7a/D7b before any code moved: a read-only harness (Scheduler built
   to inspect ranking) and `run(0)` recovery with two live harness handles.
   The stamp moved `__init__` → `run(cycles > 0)`, after workflow
   recovery. Both affected tests then passed UNEDITED, which is what
   distinguishes a code defect from fixture drift.
3. **R18's hunk count**: three, not the two SPEC.md D6 predicted.
4. **Budget overrun ~3.5x**: 210 `src/` lines against an estimated 40-60.
   Under the 300-line stop condition, so no stop fired, but the estimate
   was wrong and the tranche did not notice until step 20.
5. **D9's fixture-drift prediction was too narrow.** It predicted count
   assertions; it did not anticipate an allow-list, nor the content test
   that moved *because the change works*.

## Map delta

**changed:** `docs/map/CON-schools.md` (owns `module_events.py` now; new
check that a mock-endpoint run's recorded fingerprint equals the
registry's pinned one), `docs/map/SEAM-schools-x-scheduler.md`
(`active_backend()` count 2 → 3; new check that the stamp does not fire at
construction, fires once per `run` under `cycles > 0`, and lands after
workflow recovery).
**created:** none.
**new checks:** 2 (805 total, up from 803).

**left stale:** `SUB-harness.md`, `SUB-ontology.md`, `SUB-scheduler.md`,
`SEAM-schools-x-scratch.md` — `Verified-at:` stamps deliberately NOT
advanced, because this tranche did not re-run those documents' full check
sets. Nothing they assert is false (all 805 checks pass), and the new
behaviour is documented at the concept and seam level, where the map's
own seam-before-subsystem rule puts it. Other `--stale` entries predate
this tranche and belong to earlier rungs.

Worth noting: `SUB-ontology.md`'s change recipe is what caught the round-1
FAIL. The map paid for itself this tranche.

## Parked (not done, not promised)

- **P1** — `VerifierRegistry` and `WORKLOADS`: same shape, record nothing.
  The natural next tranche if you widen A1.
- **P2** — `INV-frozen-surfaces`' `Owns:` line and its numbered surface
  list disagree about scope; resolving it needed your sentence (R18) where
  a line in the document could settle it permanently.
- **P3** — the same document's `Config` invitation still reads as
  unqualified 200 lines before the trap that refutes it.
- **P4** — "which modules built this run" and "which modules this run
  USED" are different questions; only the first is answered.
- **P5** — `root_sweep.py` compares five fields now; every observable
  added before C13 existed remains unprobed.
- **P6 / P6a** — `pyproject.toml`'s `dev` extra cannot produce a runnable
  gate: it names neither `pytest-xdist` (which the documented `-n 4`
  command needs) nor `jsonschema` (which a gate test imports). Cost this
  session: one 292-failure `docs_verify` report with no relation to the
  documents.
- **P7** — 14 of 45 committed roots refuse to open at all (pre-v6); any
  "all roots" probe must catch at open, as `root_sweep.py` does.


---

## Post-delivery: A1 resolved (2026-08-04, operator, verbatim)

> A1 confirmed: SCHOOL_POPULATION only, other registries stay parked.

A1 ceases to be an open assumption and becomes a confirmed decision. The
tranche's scope was correct as delivered; `VerifierRegistry` and
`WORKLOADS` remain PARKED (P1) rather than deferred work owed. Nothing in
the delivered change moves as a result.

Also corrected post-delivery: PARKED P6/P6a overclaimed. The missing test
dependencies were already documented in
`docs/HANDOVER_2026-08-03.md`'s "Environment facts that bite" at the
tranche base; the failure was mine for not reading that section first.
See PARKED.md's correction note.
