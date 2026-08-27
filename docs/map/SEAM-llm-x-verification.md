<!-- DR-SEAM-llm-x-verification -->
Verified-at: 814268b46
Verify: python -m pytest tests/test_split_leg_recording.py tests/test_split_budget_protocol.py -q
Owns:
Seams:
Seams-undocumented:

# llm × verification — the record is the whole conversation

## What this seam is

`DR-SUB-llm` WRITES provider evidence. `DR-SUB-verification` READS it back and
decides whether the run is replayable. Between them there is **no import in
either direction** — `invariants.py` names nothing from `llm/`, and `llm/`
names nothing from `invariants.py`. The entire agreement travels inside one
record, `LLMAttempt` (`DR-SUB-ontology`), and consists of what the fields of
that record MEAN.

`check: python -c "
import ast, pathlib
for path, forbidden in (
    ('src/deepreason/invariants.py', 'deepreason.llm'),
    ('src/deepreason/llm/adapter.py', 'deepreason.invariants'),
):
    tree = ast.parse(pathlib.Path(path).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith(forbidden), (path, node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(forbidden), (path, alias.name)
"`

**This document exists because that invisibility had a cost.** `INDEX.md`'s
seam matrix is built from measured import coupling, so a pair with zero
traffic never appears in it — and a pair absent from the matrix reads as "no
interaction", not as "an agreement nothing can measure". The split-budget seat
protocol was written against `attempt_trace` without anything telling its
author what that list already meant to its only reader, and every thinking-ON
run came out replay-invalid (`Traps`, below). A seam that no metric can see is
the seam most in need of a document.

## The agreement, in one sentence each

**`attempt_trace` is the REPAIR LADDER.** Its index means *how many times this
call was told its value was wrong*. `attempt.attempt` must equal the list
index; `e.llm.attempts` must equal the list length; `valid=False` means the
wire validator rejected THIS value, so a diagnostic must accompany it; and
`attempts > 1` means the call's final prompt is a repair prompt and must carry
`DIAGNOSTIC:`. Four checks in `verify_root` say exactly this —
`attempt-order`, `attempt-trace`, `attempt-blobs`, `repair-metadata` — and a
fifth, `attempt-accounting`, requires the entries' tokens to sum to the call's.

**`split_legs` is NOT that.** A split-budget seat call
(`llm/split.py`) makes TWO provider requests that jointly produce ONE value:
a deliberation leg at `B_r` that is allowed to be cut off, and a non-thinking
emission leg at `B_a` that serializes whatever the first produced. Neither is
a telling-it-was-wrong. They hang off the attempt they produced, as
`LLMSplitLegV1` records, and the `split-legs` family reads them.

**`max_tokens` on the attempt is the AUTHORIZED envelope; `max_tokens` on a leg
is the WIRE value.** They are two different true things and neither substitutes
for the other: `attempt-limits` admits only route-authorized caps, and a leg's
share of the ceiling is not one. `B_a` is taken OUT of the ceiling rather than
added to it, so the legs' caps sum to at most the attempt's.

`check: python -c "
from deepreason.ontology.event import LLMAttempt, LLMSplitLegV1
assert 'attempt' in LLMAttempt.model_fields
# A leg has no rung on the ladder and cannot claim one.
assert 'attempt' not in LLMSplitLegV1.model_fields
assert 'split_legs' in LLMAttempt.model_fields
assert not {'split_leg', 'split_max_tokens'} & set(LLMAttempt.model_fields)
"`

## Which fraction of each side is involved

Small, and worth stating so a change here is not scoped as "the adapter" or
"replay validation".

| Side | The part this seam touches |
|---|---|
| `DR-SUB-llm` | `LLMAdapter._split_plan` and `_dispatch_split` only. `llm/split.py` itself is PURE — it plans and renders and records nothing — so it is not part of this seam at all. |
| `DR-SUB-verification` | the per-attempt block inside `verify_root`: the five ladder checks above, plus the `split-legs` family at the end of the function. |
| `DR-SUB-ontology` | `LLMAttempt` and `LLMSplitLegV1`. The record is the seam. |

## The `split-legs` family — six limbs

Every limb is guarded on `attempt.split_legs`, so a record written before this
layer yields nothing from any of them.

| limb | states | why it can fail |
|---|---|---|
| L1 shape | exactly two legs, `("reason", "extract")` in that order | a pair in any other shape is not the protocol that ran |
| L2 accounting | `sum(leg.tokens) == attempt.tokens` | double-counting was the original defect's own signature; under-counting hides a provider request's cost |
| L3 envelope | `sum(leg.max_tokens) <= attempt.max_tokens` | a pair that spent both budgets on top of each other escapes the bound the controller is clamped to |
| L4 continuity | `extract.trace_ref == reason.trace_ref`, or the extract leg names the EMPTY trace and carries the envelope notice | the emission leg serialized the deliberation that preceded it — or says why it could not |
| L5 blobs | every leg's `prompt_ref`, `raw_ref`, `trace_ref` resolves | a leg whose evidence is gone is a claim about a provider call nobody can inspect |
| L6 provenance | the reason leg's prompt blob STARTS WITH the attempt's prompt blob | the limb that lets the two shapes coexist — see below |

**L4 is proof rather than assertion, and the writer is what makes it so.** The
trace is blobbed ONCE and both legs name that ref. Blob refs are content
addresses, so there is no second copy that could drift from the first: a writer
that fed the emission leg something else could not produce two matching refs.

**L6 is why a split call and a genuine repair can both be true of one call.**
`deliberation_request` is the attempt's own request plus a fixed instruction,
so the reason leg's prompt must begin with it. The repair ladder requires its
diagnostic in the call's final prompt; L6 proves that whatever is in that
prompt — a diagnostic included — is what actually reached the provider. The two
readings are then orthogonal facts about one call rather than two competing
readings of one list. A repair turn itself never splits (`_split_plan` returns
an unarmed plan for `attempt != 0`), so the coexisting shape is: attempt 0
split and rejected, attempt 1 an ordinary undivided repair.

`check: python -m pytest tests/test_split_leg_recording.py::test_a_split_call_and_a_genuine_repair_coexist tests/test_split_leg_recording.py::test_each_split_legs_limb_fires_on_a_record_that_violates_it -q`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| what a split leg records | `LLMSplitLegV1` (`ontology/event.py`) **and** the limb that reads the field, same commit | `tests/test_split_leg_recording.py::test_a_split_call_records_two_legs_on_one_attempt` |
| what a split record must satisfy | the `split-legs` family at the end of `verify_root` | `tests/test_split_leg_recording.py::test_each_split_legs_limb_fires_on_a_record_that_violates_it` |
| the ladder's own meaning | DO NOT, without reading `DR-INV-frozen-surfaces` surface 3 first | `tests/test_chaos_invariants.py` |

## Invariants

- `DR-INV-frozen-surfaces` surface 3: `invariants.py` and the replay-validation
  record formats. Reader changes here are granted case by case, in writing,
  before implementation. The 2026-08-27 grant is recorded there.

## Traps

- **A leg recorded as an attempt trips four unrelated checks at once, which
  makes the cause look like four problems.** `llm/adapter.py` spliced the
  deliberation leg into `attempt_trace`, and `verify_root` read it as a repair
  ladder: `attempt-accounting` (the trace summed leg one twice — `15573`
  against a call total of `10001`), `attempt-order` (two entries both claiming
  `attempt=0`), `attempt-blobs` (a diagnostic demanded of a leg that is
  `valid=False` BY DESIGN and was never a validation failure), and
  `repair-metadata` (`attempts>1` demanding `DIAGNOSTIC:` in what was the
  extraction envelope). 260 violations on a run that CONVERGED. The cheapest
  read of a record like that is the RATIO — 1:1:1:2 — which says one cause, not
  four. Fixed 2026-08-27,
  `experiments/2026-08-27-defect-split-leg-recording/`.
- **The same seam had a second, unrelated-looking death: a `None` prompt
  reference.** `_dispatch_split`'s two stand-down returns put `None` in the
  emission-prompt position, and the caller assigned it to `prompt_ref`
  unconditionally while repairing the two neighbouring values one line later.
  It only fires when an ARMED plan stands down at dispatch — an over-envelope
  deliberation request, or a token meter with no headroom to book the emission
  leg — which is why it appeared at a 200 000-token budget and not at 3 000 000.
  The fix deletes the assignment rather than the two returns: the call's
  `prompt_ref` is the seat's own request, and each leg's synthesized envelope
  is reachable through the leg.
`check: python -m pytest tests/test_split_leg_recording.py::test_a_stand_down_at_dispatch_never_writes_a_null_prompt_ref -q && python -c "
import inspect
from deepreason.llm.adapter import LLMAdapter
src = inspect.getsource(LLMAdapter.call)
assert 'prompt_ref = emission_ref' not in src
assert 'attempt_trace.extend' not in src
"`
- **Zero import traffic is not zero coupling.** This pair carries no import in
  either direction and therefore never appeared in `INDEX.md`'s matrix, which
  is built from measured coupling. The agreement is nonetheless load-bearing
  enough that breaking it invalidated every run of a whole operating mode. When
  scoping a change to a RECORD rather than to a function, ask who reads it,
  not who imports you.
