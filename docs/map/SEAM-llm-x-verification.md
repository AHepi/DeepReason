<!-- DR-SEAM-llm-x-verification -->
Verified-at: 152c7e204
Verify: python -m pytest tests/test_split_leg_recording.py tests/test_split_budget_protocol.py -q
Owns:
Seams:
Seams-undocumented:

# llm × verification — the record is the whole conversation

## What this seam is

`DR-SUB-llm` WRITES provider evidence. `DR-SUB-verification` READS it back and
decides whether the run is replayable. The import traffic between them is
**one-directional**: the verification side names `deepreason.llm` at SEVEN
symbol crossings across six import statements — one at module level, five
inside the functions that use them — while `llm/` names
`deepreason.invariants`, `deepreason.verification` and
`deepreason.signals_read` NOWHERE, in any form, absolute or relative. The
asymmetry is the point rather than an accident: a reader may re-derive a value
with the writer's own function, but a writer that could see its validator
would be marking its own paper.

**Every crossing is a RE-DERIVATION, and none of them carries the agreement.**

| what the verification side imports | from | why it cannot just read the record |
|---|---|---|
| `route_fingerprint` — the one module-level crossing, in `invariants.py`, and again function-local in `verification/report.py` | `llm/firewall.py` | The record carries `route_sha256` on a render receipt and on a v6 work lease. The reader recomputes the digest from the route the frozen manifest granted and compares. The recorded value is the thing under test, so it cannot also be the authority. |
| `ConjecturerOutput`, `AliasTable`, `wire_contract_for`, `ReferenceFreeConjecturerWireContract` | `llm/contracts.py`, `llm/wire.py` | `verify_root` re-derives WHICH contract ids a manifest's (role, output model, transport profile) tuples actually authorize, instead of trusting the `contract_id` the record announces. |
| `HashingEmbedder` | `llm/embedder.py` | The `detection-total` check runs `raw_flags` over the replayed harness and must not fail for an environmental reason; the hashing backend is deterministic and needs no downloaded weights. |

None of the seven touches `attempt_trace` or `split_legs`. The substantive
agreement — what the fields of `LLMAttempt` (`DR-SUB-ontology`) MEAN — travels
inside one record and is carried by no import at all, which is why the
crossings above are a poor guide to what breaking this seam costs.

`check: python -c "
import ast, pathlib
SRC = pathlib.Path('src')
def crossings(targets, prefixes):
    out = set()
    for target in targets:
        top = pathlib.Path(target)
        for path in (sorted(top.rglob('*.py')) if top.is_dir() else [top]):
            parts = list(path.relative_to(SRC).with_suffix('').parts)[:-1]
            tree = ast.parse(path.read_text())
            toplevel = {id(n) for n in tree.body}
            for node in ast.walk(tree):
                at_module_level = id(node) in toplevel
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if any(alias.name == q or alias.name.startswith(q + '.') for q in prefixes):
                            out.add((str(path), alias.name, alias.name, at_module_level))
                    continue
                if not isinstance(node, ast.ImportFrom):
                    continue
                base = '.'.join(parts[:len(parts) - node.level + 1]) if node.level else ''
                mod = base + '.' + node.module if (base and node.module) else (base or node.module or '')
                for alias in node.names:
                    # A leaf import names its module in the ALIAS, not in the
                    # module path: resolving only the path leaves
                    # 'from deepreason import invariants' invisible here.
                    for cand in (mod, (mod + '.' + alias.name) if mod else alias.name):
                        if any(cand == q or cand.startswith(q + '.') for q in prefixes):
                            out.add((str(path), cand, alias.name, at_module_level))
                            break
    return out
forward = crossings(('src/deepreason/invariants.py', 'src/deepreason/verification', 'src/deepreason/signals_read.py'), ('deepreason.llm',))
expected = {
    ('src/deepreason/invariants.py', 'deepreason.llm.contracts', 'ConjecturerOutput', False),
    ('src/deepreason/invariants.py', 'deepreason.llm.embedder', 'HashingEmbedder', False),
    ('src/deepreason/invariants.py', 'deepreason.llm.firewall', 'route_fingerprint', True),
    ('src/deepreason/invariants.py', 'deepreason.llm.wire', 'AliasTable', False),
    ('src/deepreason/invariants.py', 'deepreason.llm.wire', 'ReferenceFreeConjecturerWireContract', False),
    ('src/deepreason/invariants.py', 'deepreason.llm.wire', 'wire_contract_for', False),
    ('src/deepreason/verification/report.py', 'deepreason.llm.firewall', 'route_fingerprint', False),
}
assert forward == expected, sorted(forward ^ expected)
assert len([c for c in forward if c[3]]) == 1, sorted(c for c in forward if c[3])
back = crossings(('src/deepreason/llm',), ('deepreason.invariants', 'deepreason.verification', 'deepreason.signals_read'))
assert back == set(), sorted(back)
"`

The set is pinned EXACTLY, in both directions, and the empty direction is
pinned too — an assertion that something stays absent is the only thing that
keeps it absent. A legitimate eighth crossing therefore turns this check red.
That is the design (`SCHEMA.md`: counts are claims): widen the set in the same
commit that adds the import, and add a row above saying what the new crossing
re-derives. Do not delete the check to make it quiet.

**"In any form" is a claim about the RESOLVER, and it cost this check a
repair.** An `ImportFrom` can name its module in the module path
(`from deepreason.invariants import verify_root`) or in the ALIAS
(`from deepreason import invariants`), and only the first is what
`node.module` holds. The check's first form resolved the path alone, so five
of the nine reverse forms below — including the leaf form `src/` itself uses
29 times across 24 files, and the relative `from .. import invariants` — went
straight through it while the prose above claimed they could not. Each alias
is now resolved BOTH ways. The fourth element of every tuple is the
module-level/function-local flag, which pins the sentence at the top of this
document and `INDEX.md`'s matrix score of 1 for this pair: hoisting
`verification/report.py`'s function-local import to module level is a change
to a counted claim and now turns the check red.

**Nothing else polices the reverse direction properly.** `DR-SUB-llm`'s own
negative grep forbids `llm/` from importing a list of packages, and that list
names `verification` but not `invariants` — so an `llm/` module importing
`deepreason.invariants` would pass it and be caught only here. That grep is
also a dotted-prefix pattern, so it misses the leaf form for `verification`
too; widening its list would not close the hole on its own
(`experiments/2026-08-30-fix-rotted-map-checks/PARKED.md` P-D7). No test in
`tests/` asserts either direction.

**This document exists because that traffic is invisible where people look for
it.** `INDEX.md`'s seam matrix counts module-level imports between the files
each side declares it `Owns:`, so this pair scores ONE — lower than every
other pair the table lists — and until 2026-08-30 it sat there with a dash.
Five of the six statements are function-local, which the metric cannot see at
all. A pair at the bottom of a coupling table reads as "no interaction", not
as "an agreement nothing can measure". The split-budget seat protocol was
written against `attempt_trace` without anything telling its author what that
list already meant to its only reader, and every thinking-ON run came out
replay-invalid (`Traps`, below). A seam whose metric reads near zero is the
seam most in need of a document.

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
- Both files on the verification side of the crossing table — `invariants.py`
  and `verification/report.py` — are surface 3, and `llm/firewall.py`, which
  they import, is frozen-ADJACENT. Correcting this document's claim about
  those crossings changed no code. Removing a crossing to make the old claim
  true would be a frozen-surface edit and needs a written grant first.

## Why this seam carries no `Sweep:` header

`SCHEMA.md` ratchets the header in — a seam without one must gain it the next
time the document is edited — with one stated exception: when every candidate
spec would flag readers rather than enforcement sites, leave it off and say
why. That is this seam's case, and it was measured on 2026-08-30 rather than
assumed. `--coverage` calls a file an enforcement site when the FIELD sits
next to `==` or `!=`, or inside a `raise` line. `verify_root` does neither: it
reads values OFF the field and calls `fail` (`attempt.attempt` against the
list index, the legs' tokens against the call's), and it never names
`LLMAttempt` or `LLMSplitLegV1` at all — it walks the event duck-typed, so it
is not even a candidate. Three specs over `attempt_trace|split_legs` returned
ZERO enforcement sites between them; the four files they matched are readers
(`llm/adapter.py` and `ontology/event.py`, both named above, plus
`run_manifest.py` and `workflow/trace.py`, which belong to other seams). A
header here would sweep nothing and report a clean sweep, which buys this
document credibility it has not earned. The enforcement inventory is the
six-limb table above instead, and each limb carries a test.

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
- **Zero import traffic is not zero coupling — and this pair's traffic was
  never zero.** This entry read "this pair carries no import in either
  direction" until 2026-08-30. The seam's own check said the same thing and
  was wrong: it had never once been executed, because it spans several lines
  and the verifier read checks line by line until
  `experiments/2026-08-29-fix-docs-verify-multiline-checks/` fixed the parser.
  The first execution failed on `invariants.py`'s module-level
  `route_fingerprint` import. The measured traffic is one-directional and
  small, and it WAS invisible to `INDEX.md`'s matrix — five of its six
  statements are function-local and the sixth scores one — so the lesson
  survives its false premise: the agreement is load-bearing enough that
  breaking it invalidated every run of a whole operating mode, and no import
  count would have said so. When scoping a change to a RECORD rather than to a
  function, ask who reads it, not who imports you. And when a claim's own
  check has never run, the claim has never been tested. Corrected 2026-08-30,
  `experiments/2026-08-30-fix-rotted-map-checks/`.

- **A check that names an import FORM is a claim about its resolver, and this
  one asserted more than it resolved.** The replacement check written the same
  day pinned both directions and said "in any form, absolute or relative" —
  but it matched an `ImportFrom` on `node.module` alone, so every import whose
  module sits in the ALIAS resolved to bare `deepreason` and matched nothing.
  Nine reverse forms were planted against it: `from deepreason import
  invariants`, `from .. import invariants`, the same two for `verification`
  and `signals_read`, and their function-local variants all passed GREEN,
  while the three dotted forms the original mutation set had exercised went
  red. `from deepreason import <module>` is not an exotic spelling here: it
  appears 29 times across 24 files in `src/`, which contains no relative
  imports at all. The forward direction had the same hole (`from deepreason
  import llm` added an unpinned eighth crossing, GREEN), and the
  module-level/function-local split was pinned for `invariants.py` only, so
  hoisting `verification/report.py`'s import changed two counted claims
  silently. The lesson is narrower than "test your checks": a mutation set
  that plants only the form the author had in mind measures the author, not
  the check — enumerate the forms the CLAIM covers and plant every one. Found
  by independent review, fixed 2026-08-30, same tranche; the sixteen-form
  table is the check's own proof and is committed beside it.
`check: python experiments/2026-08-30-fix-rotted-map-checks/proof/d1_crossing_forms.py`
