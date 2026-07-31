# Turmite run: the schema held, the prose did not

Dated 2026-07-31. Model glm-5.2, thinking OFF, fresh home.
Run `run-bc3e8797b3e0609eddb324299c8257bd`, state **failed**, 368 s, cycle 0.

## What was asked

Generalized ant automata under semantics deliberately chosen so that recall is
a trap: a stride of (c+1) cells rather than the published unit stride, which
inverts the well-known answers (`RL` builds no highway here; `RLR` does). The
question needs all four channels — parse the rule-string grammar, implement it
in code, simulate to learn anything at all, and use scratch for the mechanism.

## Outcome, in typed order

    setup_rc=0
    qualify_rc=0   qualify_seconds=1     (cache hit; battery ran earlier at 376 s)
    reason_rc=4    reason_seconds=368
    state=failed
    error_type    RunManifestError
    error         V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
                  /workflow/insufficient_capability_by_route_seat:
                  route seat has terminally exhausted its smallest
                  authorized contract
    stop.reason   operational_failure   (cycle 0, stuck_signal false)

## The cause, from the record

`conjecturer.turn.v6` was rejected on every attempt, and the seat then fell
back `standard -> compact` exactly as designed. The atomic contract mostly
worked — 9 slots admitted — but one slot returned literally `{}`
(`raw_ref` = sha256 of `"{}"`, 2 completion tokens), and since the compact
atomic contract IS the smallest authorized contract for that seat, there was
nothing left to fall back to. The run died at cycle 0.

Rejection pointers across all 10 rejected admissions:

    2  /scratch_proposal/links/0
    2  /scratch_proposal/links/0/to_ref
    2  /cases/1/counterexample
    2  /simulation_proposals/1
    1  /cases/0/counterexample
    1  /values

The scratch links the model actually emitted, recovered from the blobs:

    {"from_ref": "NEW_001", "to_ref": "NEW_001"}            x3
    {"from_ref": "NEW_001", "to_ref": "2469e57fb1b8d91d"}   x1

## The finding

**The first is a self-link.** `_not_a_self_link`
(`scratch/proposals.py:59`) forbids it. That rule is one of the nine this
tranche's SWEEP.md listed as NOT EXPRESSIBLE in JSON Schema — it is equality
between two sibling field values, which the standard cannot state without
`$data`. It is also, on this evidence, the rule that killed the run.

So the run is a direct test of operator rule A2 and it cuts both ways:

- Every rule the sweep COULD encode held. The battery for this exact model
  and configuration returned tier `full` with `scratch.link.compact.v1` at
  20/20 first-pass and zero repairs, against 11/20 and 9/20 before the sweep.
- The failure landed precisely on a rule the sweep COULD NOT encode, and which
  therefore still lives only in prose. A2's premise — that with reasoning off
  a prose-only constraint gets violated — is confirmed here in the one place
  the sweep could not reach.

**The second is a namespace violation.** `2469e57fb1b8d91d` does not match
`^(?:SCR|NEW)_[0-9]{3,}$`, and that pattern IS on the field. The schema
correctly refused it; the model emitted it anyway. Under
`output_mechanism: json_text` there is no constrained decoding, so the schema
is advisory text in the prompt rather than a grammar — a rendered pattern
cannot prevent a violation, only diagnose it. That distinction matters for how
much any schema encoding can be expected to buy on this transport.

## A second defect, separate from the above

The repair loop degrades rather than corrects. Completion tokens across the
`conjecturer.turn.v6` attempts, in order:

    2735 -> 7151 -> 7150 -> 78 -> 38 -> 25 -> 67 -> 19 -> 32 -> 38

The model starts by answering at length and, as repair prompts accumulate,
collapses to near-empty responses — ending at `{}` on the atomic fallback.
Whatever the repair prompt is doing, it is not steering the model toward a
valid document; it is suppressing output. This is worth its own tranche and is
NOT explained by the completion cap: every attempt sits far below the 24576
ceiling, and thinking is off, so it is not hidden-reasoning burn either.

## What went right, and should not be lost in the failure

The capability channels were genuinely exercised. The model filed typed
simulation proposals carrying `model_source`, `requested_observables`
(`["RL", "LR", "LRRLL"]`), `rival_predictions` and
`interpretation_conditions`; typed research proposals; and scratch proposals
with new blocks and links. It engaged the actual problem — the blobs carry a
"spiral mechanism" conjecture and a link labelled "Revision of mechanism after
mental simulation failure". The exposure work from the previous tranche is
doing what it was meant to do.

## Residue

- The question was never answered. Nothing here says anything about turmites;
  the oracle's answers in `oracle_table.txt` remain unmatched by any model
  output.
- One run, one model, one configuration. The repair-collapse pattern is from a
  single trajectory and needs reproduction before it is treated as general.
- Whether thinking-off glm-5.2 can do this problem at all is untested: the
  seat died on contract compliance, not on the mathematics, so the question of
  capability is unresolved rather than answered negatively.
- The self-link rule could be made mechanical in the RUNTIME rather than the
  schema — a deterministic repair that drops a self-link instead of rejecting
  the whole turn. That is a design change, not a bug fix, and is not made here.

Accepted does not mean true; failed does not mean incapable.
