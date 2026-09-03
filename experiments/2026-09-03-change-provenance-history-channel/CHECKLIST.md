# CHECKLIST — Phase 2 implementation of the provenance history channel

State: NOT STARTED. Phase 1 ends at this document plus `SPEC.md`, both awaiting
operator approval (C8, C9). **No step below may be executed until that approval
lands**, and one stop is open first (SPEC §4 / C13, the critic default).

Every step has ONE done-criterion whose output must be pasted when the step is
checked. Steps run one per `dr-execute-step` invocation. The order is chosen so
that anything which could force a redesign fails EARLY and cheaply.

---

## Phase 2A — the things that can still kill the design (do these first)

**Step 1 — source failed objections outside `att`, or prove it cannot be done.**
PARKED P7 established that a not-landed attack mints no warrant and so leaves no
edge; sustain rate is 1.000 across 6 roots and 630+ targets. S15's second limb
and S1's `attacks(X)` not-landed half both depend on a source that does not
exist yet.
*Done when:* a read-only script over a committed root emits at least one
objection that was RAISED and did NOT land, sourced from criticism records
rather than `att` — or a written finding that the record does not retain them,
in which case §2 and §6 of SPEC.md are amended to drop the not-landed half and
say so.
*Why first:* it is the only open question that can invalidate two specified
items. Everything after it assumes an answer.

**Step 2 — confirm the exposure-policy `Config` fields are digest-preserving on
the REAL field names.** Grant G1 covers the SHAPE; `PRICE_EXPOSURE_POLICY.txt`
priced two placeholder names.
*Done when:* `source_config_hash` is byte-identical at all six schema versions
with the actual field names added and popped, and the fields are absent from
`engine_config_json`. Paste the probe output.
*Stop if:* any version moves. That is a fresh frozen-surface stop, not covered
by G1.

**Step 3 — name the fields so no existing tripwire turns red.**
`DR-SEAM-manifest-x-schools` holds, with a check, that the words `stance`,
`lineage`, `crossover` and `reseed` never occur in `run_manifest.py`. The F3
knobs were renamed for exactly this reason, and `lineage` is a word this
tranche's vocabulary uses freely (S1's `lineage` query).
*Done when:* the chosen names are in `run_manifest.py` and
`python tools/docs_verify.py` is green.

---

## Phase 2B — the channel, behind its interface

**Step 4 — the closed query vocabulary as a versioned enum.** S1, S2, S3.
*Done when:* a query naming a kind outside the enum is refused typed; a test
mutates a per-kind bound and goes RED; the same query twice over one root
returns byte-identical answers.

**Step 5 — the channel registry on the P9 plugin shape.** S4, copying
`successor/registry.py` + `route.py` + the `aftercycle` hook, not reinventing.
*Done when:* a law-line test forbids every DECIDING package from naming the
registry with an EMPTY permitted-exception list, and it passes.

**Step 6 — `episode.pool` as a registered destination.** S5, and REQUEST.md Q6
decides its shape: reading the JSONL trace keeps surface 3 untouched; requiring
a first-class record object is a PRICED STOP.
*Done when:* the channel resolves through the registry with no caller naming
it, and the frozen-surface forecast in SPEC §7 still holds.

**Step 7 — a channel that cannot answer COMPILES.** S6.
*Done when:* a topology with no episode log compiles and records the typed
"channel unavailable" notice; a test asserts the notice exists, not merely that
the run survived.

---

## Phase 2C — exposure, recording, bounds

**Step 8 — the per-seat exposure policy, keyed by SEAT INSTANCE.** S7, S9.
*Done when:* two seats of the same role carry independent policies, proven by a
test that gives them different ones.

**Step 9 — switching a channel off emits a findable typed WARNING.** S8, and
this is C1's law plus the P10 audit finding, where five switches reverted
silently.
*Done when:* a test reads the notice back OUT OF THE RECORD after switching a
channel off. "The channel is off" is not the criterion; "a reader can find out
why" is.

**Step 10 — query results recorded as `workflow-context-exposure-v2`.** S12,
reusing the existing shape, which is what keeps surface 3 at zero contact.
*Done when:* a query produces a receipt of that schema, `verify_root` is green
on the resulting root, and NO new object kind appears.

**Step 11 — answers bounded against the pack budget.** S13.
*Done when:* an answer that would exceed the remaining non-schema budget is
truncated BEFORE render, with the truncation stated in the answer text; a test
mutates the budget and the bound moves with it.

---

## Phase 2D — defaults, docs, gate

**Step 12 — defaults: conjecturer history ON, critic BLIND.** S10, S11.
*Done when:* a default run exposes provenance to conjecturer seats and not to
critic seats, and both are switchable per run with no code edit.

**Step 13 — the map moves in the SAME commit as the code.** `docs/map/` has no
`CON-provenance` and no `SEAM-rules-x-verification`; the preflight recorded both
gaps. Every load-bearing claim needs a `check:` that would FAIL if the behaviour
regressed.
*Done when:* the new documents exist and `python tools/docs_verify.py` (FULL
mode, not `--fast`) is green, plus `--audit` refuses no new check.

**Step 14 — the gate.** `python -m pytest tests/ -q -n 4`, 0 failed, plus the
wheel smokes if the public surface moved.
*Done when:* the output is pasted with "N passed, 0 failed". Never weaken an
assertion to get green.

---

## Carried forward, NOT part of Phase 2

- **PARKED P1** — a clean four-cycle run leaves a terminal `continue` refuses.
  Its own defect tranche; the prompt is written.
- **PARKED P5** — managed runs get the hashing embedder while CLAUDE.md says
  otherwise. Fork between a code defect and a docs drift; unresolved.
- **PARKED P2, P3, P4, P6** — the env-knob ergonomics finding, and three
  not-defects recorded so nobody opens a tranche on them.
- **The blind-judging protocol is UNRUN.** It is the only registered measure
  that could have discriminated on M3, and the only one that speaks to quality
  at all for M1. Running it needs no new code and no new runs — the four
  committed arms hold the candidates.
- **M2's live sweep** — descoped by operator instruction; its offline
  sub-measurement (schema share) is complete and is what SPEC §5 rests on.
