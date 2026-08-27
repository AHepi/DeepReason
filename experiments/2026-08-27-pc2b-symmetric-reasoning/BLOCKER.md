# BLOCKER — the split-budget protocol writes a replay-INVALID record

> **LIFTED 2026-08-27.** Fixed on main by merge `0a23ae081`: a split-budget
> leg is now a typed leg structure on ONE attempt, and `verify_root` reads it
> as such. Merged here at `919dd378a` (two additive conflicts, both resolved
> keeping both sides). `cycle_soak.py --case pc2b` re-run VERBATIM on the
> merged tree: **exit 0**, A3 from 50 violations to 0, A2 from
> `operational_failure` to `budget_exhausted`, A4 from cycle 1 to 24 of 24 —
> with A5 and A6 still green, so the fix did not quiet the organs under test.
> Report: `soak-pc2b.out`. The diagnosis below stands as written; it is kept
> because it is the evidence the fix was built from, and because errata E59
> records the general lesson: "never exercised" licenses no verdict about
> soundness in either direction.


**P-C2b is STOPPED before any provider call.** The soak the operator required
caught this; the key has not been used.

## The finding

`python -u scripts/cycle_soak.py --case pc2b` → **exit 1**.

    [PASS] A1-typed-terminal          state='failed' stop_reason='operational_failure'
    [FAIL] A2-no-operational-failure  '1 validation error for LLMAttempt
                                       prompt_ref: Input should be a valid string,
                                       input_value=None'
    [FAIL] A3-verify-root-clean       50 violation(s)
    [FAIL] A4-cycles-reached          reached cycle 1 of 24
    [PASS] A5-in-run-checker-fired    3 demonstrative fail warrants
    [PASS] A6-discharge-channel       {'discharge-reask': 5}

The 50 violations fall into exactly four checks:

    20  repair-metadata      "repaired call lacks field diagnostic in final prompt"
    10  attempt-accounting   "trace tokens=15573 but call tokens=10001"
    10  attempt-blobs        "attempt=0: missing diagnostic ref"
    10  attempt-order        "attempt=1: recorded attempt index=0"

## Root cause, in one sentence

**`llm/split.py` writes its two LEGS into `attempt_trace`, and
`invariants.py::verify_root` reads that list as a REPAIR LADDER**, so every
thinking-ON run produces a record replay validation rejects.

Each violation is that one mismatch seen from a different angle:

| check | `invariants.py` | why a split leg trips it |
|---|---|---|
| `attempt-accounting` | L3720: `sum(a.tokens for a in trace) != llm.tokens` | the trace sums BOTH legs; the call records one |
| `attempt-order` | L3801: `a.attempt != index` | both legs carry `attempt_index=0`, at list indices 0 and 1 |
| `attempt-blobs` | L3814: a diagnostic ref is REQUIRED when `not a.valid` | the reason leg is invalid BY DESIGN and has no diagnostic — it is not a validation failure |
| `repair-metadata` | L4019: `attempts > 1` ⇒ the final prompt must contain `DIAGNOSTIC:` | the extract leg's prompt carries the reasoning trace, not a diagnostic |

The `LLMAttempt.prompt_ref=None` crash in A2 is the same seam: a leg that is
not a repair has no repair prompt to reference.

## Why nobody caught it

**No committed root has ever exercised this protocol.** Checked all 54 roots
in `ROOT_INVENTORY.json`: **0 carry a `split_leg`.** The split protocol ships,
is unit-tested, and defaults to `"auto"` — but `"auto"` arms only seats whose
route says they think, and until P-C2 every run on this tree ran with
`reasoning: "none"` inherited from P-C1. The first run ever to turn thinking
on was P-C2's ARM H3, four hours ago.

Confirmed by contrast, which is the cleanest evidence available:

| root | thinking | split | `verify_root` |
|---|---|---|---|
| P-C2 ARM H2 (`run/`) | OFF | not armed | **0 violations** |
| P-C2 retired ARM H3 (32768) | ON | armed | **15 violations**, same four checks |
| P-C2b soak | ON | armed | **50 violations**, same four checks |

## This also amends CORRECTION.md

`CORRECTION.md` said the retired 32 768 attempt "was working". That is true of
the PROVIDER legs — all three extraction legs returned valid with a natural
stop — and **false of the record it wrote**, which carries 15 replay
violations. Both statements are now on the record. In this project the record
is the only admissible evidence, so a run whose legs succeed and whose record
fails validation is not a usable run.

## Why P-C2b cannot proceed

PREREG §2 inherits P-C2's design, whose whole epistemology is that the typed
record is the only admissible evidence. A run that cannot pass `verify_root`
produces no admissible evidence, so ARM H would spend 200 000 tokens and
settle nothing.

## What is needed, and why it is the operator's call

**`invariants.py` and replay-validation record formats are FROZEN SURFACES**
(CLAUDE.md). The fix has to teach `verify_root` that a split leg is not a
repair attempt — either by excluding legs from the repair-ladder checks, or by
recording legs somewhere other than `attempt_trace`. Both touch a frozen
surface, and neither may be done without explicit operator approval.

**Ready-to-send prompt:**

    Defect: llm/split.py's two-leg protocol writes both legs into
    attempt_trace, which invariants.py::verify_root reads as a repair ladder.
    Every thinking-ON run is therefore replay-invalid: 4 checks fire
    (attempt-accounting, attempt-order, attempt-blobs, repair-metadata) plus
    an LLMAttempt.prompt_ref=None crash. Evidence:
    experiments/2026-08-27-pc2b-symmetric-reasoning/BLOCKER.md; reproduced by
    `python -u scripts/cycle_soak.py --case pc2b` (exit 1), and contrasted
    against a thinking-OFF root that verifies clean. No committed root has
    ever exercised the protocol (0 of 54 carry a split_leg), which is why it
    shipped unnoticed.

    Route: dr-change-orchestrator. TOUCHES A FROZEN SURFACE (invariants.py /
    replay-validation record formats) -- get explicit operator approval on the
    design before writing code. The design fork is whether a leg stops being
    an `attempt` (a separate typed list, which changes a record format) or
    `attempt_trace` gains a leg-aware reading (which changes an invariant).

    Acceptance: `cycle_soak.py --case pc2b` exits 0 with A2/A3/A4 green, and a
    thinking-OFF root still verifies byte-identically.
