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

## The repair loop: not collapse, but oscillation

An earlier reading of this run recorded the completion-token sequence
(2735, 7151, 7150, 78, 38, 25, 67, 19, 32, 38) as the model "collapsing toward
empty" under accumulating repair prompts. **That was wrong**, and the raw
blobs say so plainly. The small responses are JSON PATCHES, which is exactly
what `RepairPatchWireContract` asks for; 19-78 tokens is the correct size for
one. There is no degradation.

What actually happened is worse and much more specific. Ordered by attempt,
the model's `to_ref` values were:

    attempt 1   "2469e57fb1b8d91d"   rejected: outside the SCR/NEW namespace
    attempt 2   "NEW_001"            rejected: self-link (from_ref is NEW_001)
    attempt 3   "2469e57fb1b8d91d"   rejected: namespace again
    attempt 4   "NEW_001"            rejected: self-link again -> exhausted

The model oscillated between exactly two invalid values. The reason it could
not escape is structural: the proposal declared exactly ONE new block, so no
legal `to_ref` existed at all. Every candidate target is either that same
block — a self-link — or a key the response never declares. The field was
**unsatisfiable**, and the only correct repair was to remove the link.

The model never tried that, and it had no way to know it should: each
diagnostic reports the violation of the state the document is currently in, so
patching away one violation lands it in the other. Nothing in the repair
channel can say "this field cannot be satisfied; delete the element". The
model clearly knows the `remove` op — it used it on
`/simulation_proposals/1` in the same run — so this is a diagnostic gap, not a
capability gap.

**Fixed** by dropping self-links deterministically at the scratch-proposal
container rather than refusing the turn from inside a nested link model. A
self-link is inert: it adds no edge between distinct blocks, so removing it
cannot change what the graph says. The link model no longer refuses one — the
judgement is a property (`is_self_link`) and the DISPOSAL is on the container,
because a refusal raised from inside a nested item aborts container validation
before it can run. So a directly constructed `ScratchProposalLinkV1` with equal
endpoints now validates; no proposal can carry one past the container. The
closed-namespace rule is unchanged and still refuses an undeclared target.

**Still open, for the operator.** The general defect remains: a repair
diagnostic that is locally satisfiable but globally unsatisfiable will loop
until exhaustion, and the protocol has no way to express "no value works
here". Dropping self-links removes the one instance that killed this run; it
does not remove the class. A principled fix would either report the full
violation set rather than one at a time, or let a diagnostic mark a field
unsatisfiable so the repair prompt can direct a `remove`.

## The substance: the model got the answer right

The failure was bookkeeping, not mathematics. The candidate the run discarded
reads:

> CLAIM H is false. The rule string LR provides a structural refutation. Under
> the (c+1) stride, the rules {L, R} are exact inverses.

`oracle_table.txt` agrees: under these semantics `LR` builds no highway. The
model also avoided the recall trap — the published unit-stride result for `LR`
is a highway at period 104, and asserting that would have been the easy wrong
answer. It reasoned from the specified stride instead.

So the run had a correct refutation of CLAIM H in hand and threw it away over
a self-referential scratch link.

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

---

## 2026-08-01 — the channel the self-link was a substitute for

The self-link in this run was not a random malformation. The model had exactly
one new block and reached for a link from it to itself, which is what you do
when the thing you want to point at is not in the link namespace. The operator's
reading: a scratch note needs to say where it CAME FROM and what it was FOR,
and neither of those is another scratch block.

So the block body gained two optional channels, bounded at four entries each:

    experiment_refs   the simulation request identifier this note came out of
    bears_on_refs     the visible SRC_### artifact this note was aimed at

Both are relevance hypotheses. Nothing in the harness follows either one. That
is the point — a note is written before anyone, the model included, can know
whether the work behind it will ever be strong enough to enter the epistemic
loop, so the channel has to be admissible when the aim turns out to be wrong.

### Size, measured before building

The worry was that provenance would balloon the pad. It cannot: the store cap
is fixed at 131072 bytes. The real cost is CROWDING. Median block across 16 real
ones from this run and `run-b4d6dfda0c20676a864a051fbc97bda4` is 948 bytes.
Against the cap, by the accounting the authoring service actually uses:

    no refs, before these fields existed     ~133 blocks
    no refs, after                            128 blocks
    four refs on each channel                 118 blocks

Four is a deliberate stop: eight each puts a populated block past 1200 accounted
bytes and under 110, and the marginal ref is worth much less than the marginal
block.

The 133 -> 128 step is not the refs — it is two `null` placeholders entering the
accounting, because `validate_proposal` sums `model_dump(mode="json")` while
block identity uses `exclude_none=True`. So the byte ceiling has always charged
for absent fields it never stores. That divergence predates this change and is
PARKED, not fixed here; fixing it would loosen a live budget and belongs in its
own tranche.

### Two things this got wrong first, both caught by the record

**Empty tuples are not absent.** The fields defaulted to `()`. `_canonical_value`
dumps with `exclude_none=True`, which drops `None` and KEEPS an empty tuple, so
two keys entered the canonical bytes of every block and every stored block's id
moved — measured `sha256:ff609dcc…` to `sha256:248b3201…` for identical content.
That would have invalidated replay validation for every root already recorded,
which is wrong by definition. I had asserted hash stability before comparing
against pre-change code; `test_content_only_block_is_valid_and_optionals_remain_absent`
caught what the assertion did not. The defaults are `None`, and the pre-change
digest is now pinned as a literal in `tests/test_scratch_provenance_refs.py`.

**A namespace regex on `experiment_refs` was a contract mismatch.** It named
`SimulationProposalDraftV1.request_identifier`, which is model-chosen free text
bounded only at 1..128 characters. A pattern on the reading end would have
refused references to experiments the simulation contract itself accepted — the
same defect as a prose-only rule, introduced from the other side. The bound now
matches the named field exactly and a test holds the two together.

### The alias problem, and what was NOT done about it

`SRC_###` aliases are minted per call by enumeration (`rules/conj.py`), so the
string stored in a block names a different artifact in a later call. Resolving
to durable ids at admission would need the source alias table threaded to three
admission sites, one of which — the standalone `scratch.block.compact.v1` seat —
has none, so the field would be admissible on one seat and refused on another.

Instead the render layer presents both channels past-tense (`was_aimed_at`,
`came_from_experiments`) so a stale alias reads as a record of intent rather
than a pointer to resolve. Blocks with no refs render exactly as before.

### Residue

- Untested live. The sizing is measured on stored blocks; whether a model
  actually uses these channels, and whether the past-tense keys stop it from
  resolving a stale alias against the aliases in front of it, needs a run that
  survives past cycle 0. Neither run in this tranche did.
- The alias staleness is mitigated in presentation, not removed. A block whose
  aim genuinely matters cannot be resolved back to an artifact mechanically.
- The general repair defect this run exposed is still open: a diagnostic that
  is locally satisfiable and globally unsatisfiable still loops to exhaustion.
  Cycle detection now NAMES it in the record; it does not fix it.
- Parked: the scratch byte ceiling charges for `null` placeholders it never
  stores, so the effective pad is ~4% smaller than the manifest number implies.
