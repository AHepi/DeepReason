# DIAGNOSIS — one seam, two defects, both from the same borrowed costume

Tranche: `experiments/2026-08-27-defect-split-leg-recording/`
Phase: dr-diagnose. Record first; code second.

## Primary cause (cited, not re-derived)

The committed diagnosis is
`experiments/2026-08-27-pc2b-symmetric-reasoning/BLOCKER.md` at commit
`ee0563cf1` on branch `claude/p-c2-rebuild-harness-n9mguu`, and this
tranche adopts it verbatim:

> `llm/split.py` writes its two LEGS into `attempt_trace`, and
> `invariants.py::verify_root` reads that list as a REPAIR LADDER, so
> every thinking-ON run produces a record replay validation rejects.

Typed evidence supporting it, all from that STOP commit:

- `python -u scripts/cycle_soak.py --case pc2b` → **exit 1**, 50
  violations across exactly four checks, plus a crash.
- Contrast table, three roots: thinking OFF → **0** violations;
  thinking ON (retired ARM H3 root) → **15**; the pc2b soak → **50** —
  the same four checks throughout.
- **0 of 54** roots in `ROOT_INVENTORY.json` carry a `split_leg`. The
  protocol has never run live, so no committed record constrains the
  shape the fix may choose.

## What this tranche adds: the exact writer lines, and a SECOND defect

The record says WHAT is wrong. These are the lines that make it so, on
this tree at `ba4720a95`. Nothing here contradicts the cited diagnosis;
it locates it and extends it by one crash the BLOCKER named but did not
place.

### A. The reason leg is appended to the repair ladder

`llm/adapter.py:1082` builds the deliberation leg as an `LLMAttempt`
and `llm/adapter.py:1580` splices it into the ladder:

    attempt_trace.extend(split_legs)   # the reason leg
    prompt_ref = emission_ref          # (see B)

The emission leg is not recorded there: it *becomes* the caller's
ordinary attempt, stamped with `split_fields`
(`_natural_stop_field`, `adapter.py:142`). So ONE split seat call
leaves TWO entries in `attempt_trace`, both with `attempt=0`, and each
of the four reader checks sees the same mismatch from its own angle:

| check | why it fires |
|---|---|
| `attempt-accounting` (`invariants.py:3720`) | the reason leg records leg-1 tokens; the emission attempt records `split_usage`, which is **both** legs. The trace therefore sums leg1 twice: `15573` vs a call total of `10001`. |
| `attempt-order` (`invariants.py:3801`) | both entries carry `attempt=0`, at list indices 0 and 1. |
| `attempt-blobs` (`invariants.py:3814`) | a diagnostic ref is REQUIRED when `not attempt.valid`; the reason leg is `valid=False` **by design** (`adapter.py:1096`, "Prose is not a contract value and was never asked to be one") and is not a validation failure, so it has no diagnostic to give. |
| `repair-metadata` (`invariants.py:4019`) | `attempts = max(attempt+1, len(attempt_trace))` (`adapter.py:1348`) reads 2, and `attempts > 1` demands `DIAGNOSTIC:` in the final prompt — which is the extraction envelope. |

### B. `prompt_ref=None` — a real second defect, now placed

The BLOCKER reported the crash and named the seam correctly without
locating the line. It is here, `adapter.py:1043` and `:1046`:

    return None, stand_down(NOTICE_ENVELOPE),    [], None, None, None
    return None, stand_down(NOTICE_NO_HEADROOM), [], None, None, None

Both stand-downs return `None` in the sixth position — the emission
prompt ref — and the caller assigns it unconditionally at
`adapter.py:1581`:

    prompt_ref = emission_ref        # None on either stand-down

`split_usage` and `split_fields` are both repaired two lines later by
the `if not plan.armed:` branch (`adapter.py:1586-1591`). **`prompt_ref`
is not.** The next `LLMAttempt(prompt_ref=prompt_ref, …)` therefore
raises

    1 validation error for LLMAttempt
    prompt_ref: Input should be a valid string, input_value=None

which the run records as a typed `operational_failure`. This is the
soak's A2 failure, and it fires on a path that has NOTHING to do with
the four checks: an armed plan that stands down at dispatch because the
deliberation request exceeds the frozen request envelope, or because
the token meter has no headroom for the emission leg.

### C. A third consequence, not yet observed but structural

`ProposalReceiptV1.attempt_count` is `Field(ge=1, le=3)`
(`workflow/models.py:438`) and is written as `max(1, len(trace))`
(`workflow/shadow.py:634`). A split call that also repairs once puts
four entries in the trace, which that field cannot hold. Recorded here
because it is the same cause and the fix removes it; it is NOT chased
separately.

## The one sentence

**A leg is not an attempt, and every one of these follows from
recording it as one.** `attempt_trace` is the repair ladder — a list
whose index means "how many times this call was told it was wrong" —
and the split protocol borrowed it to hold something with no place in
that ordering.

## Why this shipped

`INDEX.md`'s seam matrix has no `llm × verification` row at all.
`invariants.py` imports nothing from `llm/`; the entire agreement
between the writer and the reader is carried by the `LLMAttempt`
record, so the coupling metric that builds that matrix is blind to it
and no document told the split protocol's author what `attempt_trace`
already meant. Combined with `auto` mode arming only routes that think
— and every run on this tree until P-C2 inheriting `reasoning: "none"`
— the protocol shipped, unit-tested and unexercised.

The unit tests do not catch it because they assert the defective shape
directly: `tests/test_split_budget_protocol.py:41`,

    def _legs(call):
        return [a.split_leg for a in call.attempt_trace]

and then `assert _legs(call) == [SPLIT_LEG_REASON, SPLIT_LEG_EXTRACT]`.
They test that the legs land in the ladder. None of them runs
`verify_root`.

## Reproduction plan (dr-reproduce)

The cited reproduction (`--case pc2b`) depends on two files that exist
only on the paused P-C2b branch, which this tranche may not touch. The
reproduction authored here is the same shape with a smaller surface:
`experiments/2026-08-27-defect-split-leg-recording/run-config.yaml` is
the committed P-C1 ARM H config with **exactly one line deleted**,
`reasoning: "none"` — which is the whole of the wiring that arms the
protocol — driven by `scripts/cycle_soak.py --case split-legs` through
P-C1's own builder, imported rather than copied.

Criterion 2 of GOAL.md still demands the literal `--case pc2b`; it is
run by materialising that window's two files UNCOMMITTED and removing
them before any commit.
