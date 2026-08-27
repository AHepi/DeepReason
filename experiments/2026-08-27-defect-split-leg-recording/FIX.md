# FIX — record the legs as legs, and teach the reader to read them

Tranche: `experiments/2026-08-27-defect-split-leg-recording/`
Phase: dr-propose-fix. **No production code has been written.** This
document exists before the code, because it carries a frozen-surface
grant request the monitor must be able to review before, not after.

## The principle the fix follows

**A leg is not a repair, and the record should say what happened rather
than wear a borrowed costume.**

`attempt_trace` is the REPAIR LADDER: a list whose index means "how
many times this call was told its value was wrong". The two legs of a
split are not two such tellings — they are two provider requests that
jointly produce ONE value. So they leave the ladder and become a
declared shape of their own, hanging off the attempt they produced.

Under the operator's 2026-08-14 law the record format may take the
shape the truth wants. Here it barely needs the licence: **0 of 3 155
attempts across every committed root carry a non-empty `split_leg`**
(`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` §3.2 item 1; W6
`TABLES.md` T13), so nothing old is touched at all.

---

# PART 1 — FROZEN-SURFACE GRANT REQUEST

**This fix touches frozen surface 3** (replay-validation record
formats — `invariants.py`, `verification/`). The grant is requested
here, before implementation, per the standing discipline and the four
precedent grants recorded in `docs/map/INV-frozen-surfaces.md`
(2026-08-21, 2026-08-22, 2026-08-24, 2026-08-25).

## The gate's own verdict, pasted verbatim

    python tools/blast_radius.py \
      --files src/deepreason/invariants.py \
              src/deepreason/verification/report.py \
              src/deepreason/llm/adapter.py \
              src/deepreason/ontology/event.py \
      --symbols verify_root LLMAttempt LLMSplitLegV1 _dispatch_split split_legs

    "frozen_surface_verdict": "CONTACT"
    "frozen_adjacent_contacts": []
    "wheel_smoke_pins": []

    "frozen_surface_contacts": [
      {
        "surface": "replay-validation record formats (invariants.py)",
        "tier": "DIRECT",
        "target": "src/deepreason/invariants.py",
        "detail": "target file is surface path src/deepreason/invariants.py"
      },
      {
        "surface": "replay-validation record formats (invariants.py)",
        "tier": "SYMBOL_INDIRECT",
        "target": "verify_root",
        "detail": "'verify_root' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"
      },
      {
        "surface": "manifest schemas and validators (run_manifest.py)",
        "tier": "SYMBOL_INDIRECT",
        "target": "LLMAttempt",
        "detail": "'LLMAttempt' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"
      }
    ]

    "qualification_digest": [
      {"target": "LLMAttempt", "tier": "PLAUSIBLE",
       "detail": "referenced in src/deepreason/run_manifest.py"}
    ]

## Disposal, row by row

**Row 1 — DIRECT, `invariants.py`. GRANT REQUESTED.** This is real and
is the whole request. What moves: ONE additive `fail("split-legs", …)`
family at the END of `verify_root`, guarded by `if attempt.split_legs:`,
plus the check's name in `_EPISTEMIC_CHECKS`
(`verification/report.py`). **Insertions only — zero deletions, zero
modifications to any existing check.** No existing finding's name,
shape, order or detail string changes.

Additive here is provable rather than asserted, and more strongly than
in the 2026-08-22 and 2026-08-24 precedents: those checks recognised
their inputs by bodies no older root contains. This one is guarded on
a FIELD THAT DOES NOT EXIST YET. `LLMAttempt.split_legs` is new, its
default is empty, and `FrozenRecord` is `ConfigDict(frozen=True)` with
pydantic's default `extra="ignore"` — so every attempt in every
committed root deserialises with `split_legs == ()` and yields nothing
from any limb. Pinned by a probe against a committed root, not a
fixture (S6 below).

**Row 2 — SYMBOL_INDIRECT, `verify_root` inside `invariants.py`.**
Not a second contact: it is row 1 seen through the symbol filter,
`verify_root` being the function inside the surface file row 1 already
names. Disposed by row 1's grant; nothing additional is requested.

**Row 3 — SYMBOL_INDIRECT, `LLMAttempt` in `run_manifest.py`. FALSE
POSITIVE, by measurement.** `LLMAttempt` occurs in `run_manifest.py`
exactly ONCE, at line 2436, **inside a comment** — the note explaining
why the two `SPLIT_BUDGET_*` knobs are dropped from the config echo.
There is no import of it, no reference to it in code, and no schema,
validator or Pydantic model in that file mentions it. This is the same
shape as the `clamp` false alarm `INV-frozen-surfaces.md` already
models, and it is disposed the same way — by measurement, not by
assurance:

    $ grep -n "LLMAttempt" src/deepreason/run_manifest.py
    2436:    # rather than per manifest -- LLMAttempt.split_leg / split_max_tokens /

That comment names two fields this fix removes, so it is REWRITTEN in
the same commit — a comment edit, not a surface contact. Manifest
schemas, validators and the wire-byte goldens are untouched.

**Row 4 — `qualification_digest` PLAUSIBLE for `LLMAttempt`.** Same
comment, same disposal. `LLMAttempt` is a process/replay record and
reaches no qualification subject. Proven rather than asserted: the
shipped subject-digest pin
(`tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move`)
is re-run in the implementing commit and must not move.

## What is NOT requested

- **`harness.py` event application — ZERO CONTACT, and measured.**
  `harness.py` reads `attempt_trace` in exactly two places
  (`:727-733`, `:910`) and both are attempt-level: `attempt.contract_id`
  over the trace, and `attempt_trace[-1].usage_unknown`. Removing the
  reason leg from the trace leaves harness seeing only real attempts,
  which is strictly more correct and requires no edit. The tranche
  instruction says a design wanting harness contact is a STOP; this
  one does not want it.
- Manifest schemas or validators (surface 4) — untouched.
- Qualification subjects (surface 5) — untouched.
- `capabilities/state.py` (surface 1) — untouched.
- `route_fingerprint` (frozen-adjacent) — untouched; the gate reports
  `frozen_adjacent_contacts: []`.

---

# PART 2 — THE DESIGN

## Writer — `DR-SUB-ontology`, `ontology/event.py`

A new declared record. It is a record KIND rather than fields threaded
through the attempt, because the modularity law (2026-08-26) asks for
a declared shape and because a leg has its own prompt, its own raw, its
own cap and its own outcome — every one of which the attempt also has,
and means differently.

    class LLMSplitLegV1(FrozenRecord):
        leg: Literal["reason", "extract"]
        prompt_ref: str          # this leg's own request
        raw_ref: str             # this leg's own output
        trace_ref: str           # the deliberation PRODUCED (reason)
                                 # or CONSUMED (extract)
        max_tokens: int          # the cap THIS leg put on the wire
        tokens: int
        ms: int
        natural_stop: bool | None
        notice: str
        transport_attempts: int
        transport_diagnostics: list[str]

`trace_ref` is the load-bearing addition and is what makes "the extract
leg must reference its reason trace" a CHECK rather than a hope. Blob
refs are content addresses, so the two legs agreeing on `trace_ref` is
proof that the emission leg served the deliberation that preceded it —
not a claim that it did.

`LLMAttempt` then:

    + split_legs: tuple[LLMSplitLegV1, ...] = ()
    - split_leg: str = ""                       # REMOVED
    - split_max_tokens: int | None = None       # REMOVED
      split_notice: str = ""                    # KEPT

`split_notice` stays because an UNARMED seat records a notice and has
no legs to hang it on. `split_leg` and `split_max_tokens` go because on
the new shape they are a second source of truth for what
`LLMSplitLegV1.leg` and `.max_tokens` already say, and because
`split_max_tokens=512` on an attempt that spent 32 768 across two legs
is not a partial truth but a wrong one.

Removing two fields is safe and measured, not licensed by the
2026-08-14 law alone: `FrozenRecord` sets only `frozen=True`, so
pydantic's `extra="ignore"` default applies and the 717 committed
attempts carrying `"split_leg": ""` still deserialise. S6 pins this
against a real committed root.

## Writer — `DR-SUB-llm`, `llm/adapter.py`

1. `_dispatch_split` builds BOTH legs as `LLMSplitLegV1` and returns
   them together. The emission leg is no longer left to "become" an
   attempt wearing leg fields; it is recorded as the leg it is, and the
   attempt it produces is recorded as the attempt it is.
2. **`attempt_trace.extend(split_legs)` is DELETED** (`:1580`). The
   ladder gets attempts only.
3. **`prompt_ref = emission_ref` is DELETED** (`:1581`), and the sixth
   return element goes away with it. Two things follow, and both are
   fixes:
   - The `prompt_ref=None` crash (defect B) becomes STRUCTURALLY
     impossible. It existed only because two stand-down returns put
     `None` in that position and the caller assigned it unconditionally
     while repairing `split_usage` and `split_fields` two lines later.
     Deleting the assignment deletes the class of bug, rather than
     patching the two returns that happen to reach it today.
   - `e.llm.prompt_ref` becomes the seat's OWN request instead of the
     extraction envelope. That is both more truthful and load-bearing:
     on a repaired split call, `repair-metadata` reads that blob
     looking for `DIAGNOSTIC:`, and the repair prompt is where it
     actually is. The extraction envelope is not lost — it is the
     extract leg's `prompt_ref`.
4. `split_fields` carries `split_legs`, `split_notice` and the extract
   leg's `natural_stop`, stamped onto whichever attempt the emission
   becomes — valid, invalid, or transport failure — exactly as today.

Token accounting then balances with no arithmetic anywhere: the trace
holds one entry per attempt, that entry's `tokens` is the pair's total
(`split_usage`, as today), and `e.llm.tokens` is the sum of the
entries.

## Reader — `DR-SUB-verification`, `invariants.py` + `verification/report.py`

One additive check family, `split-legs`, six limbs, every one guarded
by `if attempt.split_legs:`:

| limb | states |
|---|---|
| L1 shape | exactly two legs, in the order `("reason", "extract")` |
| L2 accounting | `sum(leg.tokens) == attempt.tokens` — the legs account for the attempt, no more and no less |
| L3 envelope | `reason.max_tokens + extract.max_tokens <= attempt.max_tokens` — `split.py`'s own law, "B_a is taken OUT of the ceiling, never added to it", so a pair can never escape the bound the controller is clamped to |
| L4 continuity | `extract.trace_ref == reason.trace_ref`, unless the extract leg carries the envelope notice, in which case it must reference the EMPTY trace — the extract leg served the deliberation that preceded it, or says why it could not |
| L5 blobs | every leg's `prompt_ref`, `raw_ref` and `trace_ref` resolves in the blob store |
| L6 provenance | the reason leg's prompt blob STARTS WITH the attempt's prompt blob (`deliberation_request` is `request + _DELIBERATE`) |

**L6 is the limb that proves the two shapes coexist.** The repair
ladder requires the diagnostic to be in the call's final prompt; L6
proves that whatever is in that prompt — a diagnostic included —
reached the provider through the reason leg. A split call and a
genuine repair are then not two competing readings of one list; they
are two orthogonal facts about one call, each with its own check.

"A leg is never counted against repair grants" needs no new limb and
gains one anyway: with legs off the ladder, `e.llm.attempts ==
len(trace)` counts attempts only, which the EXISTING `attempt-trace`
check already asserts and which S3 below drives with legs and a real
repair together.

## What this fix does NOT do

It does not change what a split does, when it arms, how it divides a
budget, or any notice it records. `llm/split.py` is not modified at
all. This is a recording fix.

---

# PART 3 — STEPS AND THEIR PROOFS

| # | step | done-criterion |
|---|---|---|
| S1 | `LLMSplitLegV1` + `LLMAttempt` field changes | new unit test round-trips a leg through `model_dump`/`model_validate` |
| S2 | adapter: build both legs, delete the two lines | `tests/test_split_budget_protocol.py` updated to read `attempt.split_legs` and green |
| S3 | `verify_root` `split-legs` family + `_EPISTEMIC_CHECKS` | each limb mutation-proven BOTH ways: fires on a violating record, silent on a conforming one |
| S4 | `--case split-legs` exits 0 | A2, A3, A4 all PASS |
| S5 | coexistence: `--case split-legs --induce-repairs 1` | legs AND a genuine repair in one run, `verify_root` clean, repair ladder semantics unchanged |
| S6 | old-root probe | a committed root's attempts deserialise with `split_legs == ()` and its `verify_root` verdict is unmoved |
| S7 | literal `--case pc2b` exits 0 | GOAL.md criterion 2, files materialised UNCOMMITTED |
| S8 | map moves in the same commits | `SUB-llm`, `SUB-verification`, `SUB-ontology`, `INV-frozen-surfaces` grant record, new `SEAM-llm-x-verification.md`, Traps entry naming the pc2b soak |
| S9 | gates | full gate 0 failed; `docs_verify` full; both wheel smokes |

### Fixture updates this design PREDICTS

Required by CLAUDE.md's gate discipline, stated before the code so the
updates are predicted rather than excused. `tests/test_split_budget_protocol.py`
asserts the DEFECTIVE shape directly — `_legs(call)` reads
`[a.split_leg for a in call.attempt_trace]` (`:89`), and `:207`,
`:348`, `:363`, `:364`, `:381` read the removed fields. Those
assertions move to `attempt.split_legs` and say the same things about
the same behaviour. Nothing is weakened: every one of them keeps
asserting the leg it asserted, on the record that now holds it. The
same for `docs/map/SUB-ontology.md`'s `check:` naming the three
fields.

## Size

Est. ~150 lines of production change across four files, of which the
frozen-surface part is one additive block. If it runs materially over,
that is a STOP under the orchestrator's scope contract, not a silent
widening.

---

# AMENDMENT 1 (2026-08-27, after the boundary gate) — a fixture update this document did NOT predict

Recorded as an amendment rather than folded into §"Fixture updates this
design PREDICTS" above, because back-dating a prediction is the one
thing that discipline exists to prevent.

**What went red.** The full gate at the boundary: 1 failed, 4343
passed, 6 skipped.
`tests/test_incident_wave_a_v2_fixtures.py::test_incident_descriptors_and_generated_roots_are_frozen_and_deterministic`
— fixture **A3**'s `generated_root_sha256` moved from `5bccbcafb361…`
to `31aebf8cea4e…`.

**Why my prediction missed it.** I enumerated the tests that ASSERT on
the changed fields by name and updated those. This one asserts on no
field at all: it hashes every byte of a root the test GENERATES, so it
is sensitive to the record's serialized shape without naming any part
of it. That is exactly what a byte-freeze is for, and it is the class
of consumer a name-based search cannot find.

**Cause, measured and bounded rather than inferred.** The A3 root was
generated on this tree and on `ba4720a95` with `src/` swapped between
them and everything else held fixed. `diff -rq` over the two roots
reports ONE differing file, `log.jsonl`, and one differing event
(seq 3), whose whole diff is:

    -    "split_leg": "",
    -    "split_max_tokens": null,
    +    "split_legs": [],
         "split_notice": "",

Two removed fields replaced by one, on one attempt. Nothing semantic
moved: same events, same count, same order, same every other field.
A1 and A2 are byte-identical between the two trees.

**Disposition: update A3's pin, do not weaken the check.** The
descriptor files are untouched (`descriptor_sha256` still passes), so
the fixture's INPUT is unchanged and only what today's code generates
from it moved — which is the change this tranche is. The pin is
re-derived, not deleted, so the freeze keeps catching the next
unintended move. It is NOT a frozen surface: `blast_radius.py` reports
`wheel_smoke_pins: []`, and no committed run root is involved — this
root is built at test time.

`check: python -m pytest tests/test_incident_wave_a_v2_fixtures.py -q`
