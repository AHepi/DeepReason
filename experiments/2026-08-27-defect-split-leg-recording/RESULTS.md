# RESULTS — the split-budget protocol's record

Dated, honest-ledger segments. What the record shows, and the residue.
"Accepted does not mean true."

---

## 2026-08-27 — a leg is not a repair, and the record now says so

**What was wrong.** `llm/split.py`'s two-leg seat protocol wrote both
of its provider LEGS into `LLMCall.attempt_trace`, which
`invariants.py::verify_root` reads as a REPAIR LADDER — a list whose
index means *how many times this call was told its value was wrong*.
Every thinking-ON run was therefore replay-invalid. Diagnosis committed
first, on another branch, at
`experiments/2026-08-27-pc2b-symmetric-reasoning/BLOCKER.md`
(`ee0563cf1`); this tranche cited it, confirmed it independently, and
extended it.

**Two defects, not one.** The four checks the BLOCKER named are one
cause seen four ways. The `LLMAttempt.prompt_ref=None` crash it
reported but did not place is a SECOND defect on a different path:
`_dispatch_split`'s two stand-down returns put `None` in the emission
prompt-ref position, and the caller assigned it unconditionally while
repairing the two neighbouring values one line later. It only fires when
an ARMED plan stands down at dispatch, which is why it appeared at
P-C2b's 200 000-token budget and not at 3 000 000.

**Confirmed independently before anything was fixed.** A soak case
authored here — the committed P-C1 ARM H config with exactly one line
deleted, `reasoning: "none"` — reproduced the same violation bytes as
the pc2b soak on the other branch:

    attempt-accounting  event seq=27: trace tokens=15573 but call tokens=10001

Two instruments, authored separately, same bytes. And the run that
produced them **CONVERGED**: nothing about the reasoning went wrong,
only the record of it. That is the sharpest form of the finding and the
reason it was worth stopping P-C2b for.

The crash was PREDICTED and then produced: DIAGNOSIS.md §B said it needs
a stand-down and that pc2b hit it through its budget; moving only
`--token-budget` to 200 000 reproduced the message byte-identically at
the same cycle-2 death depth.

### The fix

A leg stops being an attempt. `LLMSplitLegV1` is a declared record
carrying one leg's own request, output, deliberation trace, wire cap and
outcome; both legs hang off the ONE attempt they jointly produced;
`attempt_trace` goes back to holding attempts. `verify_root` gains an
additive six-limb `split-legs` family that READS that shape, so a leg
recorded wrongly still fails — the record is not merely accepted.

Two adapter lines were DELETED rather than patched. `prompt_ref =
emission_ref` was the whole of defect B, and deleting it also restores
`e.llm.prompt_ref` to the seat's own request — which is where the repair
ladder looks for its diagnostic on a repaired split call.

### Evidence, typed

| instrument | before | after |
|---|---|---|
| `cycle_soak --case split-legs` | exit 1, **260** violations, cycle 13/24 | **exit 0, 0 violations, 24/24** |
| the same at `--token-budget 200000` | exit 1, `prompt_ref=None` operational failure, cycle 2/24 | **exit 0, 0 violations, 24/24** |
| `cycle_soak --case pc2b` (literal, materialised uncommitted) | exit 1, 50 violations + the crash | **exit 0, A2/A3/A4 all PASS** |
| `verify_root` check breakdown | 11/11/11/22 across four checks | **0** |

The last row is the P-C2b STOP's own acceptance criterion, met.

### The residue — what remains unproven

Stated because a tranche that reports only its wins is not a ledger.

1. **Nothing here has run against a real provider.** Every result above
   is against the deterministic stub. The protocol's PROVIDER behaviour
   at a real ceiling was measured by P-C2 and is unchanged by this
   tranche — `llm/split.py` was not modified at all — but "the record a
   live thinking-ON run writes is valid" is proven offline and inferred
   live. P-C2b's launch is the thing that would prove it.
2. **The soak cannot exercise legs and a repair together.** Its
   `--induce-repairs` flag arms and is then absorbed by the
   unconstrained deliberation leg: 96 calls, zero repair attempts
   (PARKED P1). The coexistence case is proven by a mutation-proven unit
   regression instead. That is a stronger proof of the property and a
   real blind spot in the instrument, and both halves are true at once.
3. **L3 (the envelope limb) has never fired on a real record.** It
   states `split.py`'s own law — `B_a` comes out of the ceiling, never
   on top of it — and is mutation-proven, but no run has produced a pair
   that violates it. It is a guard against a future writer, not a
   finding about the present one.
4. **The four relieved checks are proven silent on ONE shape.** They are
   asserted absent on a thinking-ON record with and without a repair.
   Nothing here proves they are silent on every shape a split can take;
   the soak's 24 cycles and the unit matrix are the coverage, not a
   proof of exhaustion.

### What was NOT touched

`harness.py` (frozen surface 2) — zero contact, measured rather than
assumed. `verification/report.py` — untouched; the grant NARROWED during
implementation because `split-legs` falls through to the `integrity`
channel where its four siblings already sit. `llm/split.py` — untouched;
this was a recording defect, not a protocol one. The paused P-C2/P-C2b
window — untouched: its two files were materialised from `git show` for
one verification run and removed before any commit.
