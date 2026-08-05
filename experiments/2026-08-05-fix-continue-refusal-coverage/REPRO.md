# Reproduction

Form: **record replay** — `dr-reproduce`'s cheapest form, and here also
the most faithful. The witnesses are committed run roots that really
stopped; nothing is patched, constructed or asserted into existence.

## Artifact

Selection is by PROPERTY, read from each root's own `run-stop.json`, so
no root is named in the test:

    import importlib, json, shutil, subprocess, tempfile
    from pathlib import Path

    REPO = Path("/home/user/DeepReason")

    import deepreason.workflow.lifecycle as L
    import deepreason.runtime.continuation as C

    out = subprocess.run(["git", "-C", str(REPO), "ls-files",
                          "experiments", "runs"],
                         capture_output=True, text=True).stdout
    roots = sorted({Path(l).parent for l in out.splitlines()
                    if Path(l).name == "run-stop.json"})

    witnesses = []
    for r in roots:
        full = REPO / r
        reason = json.loads((full / "run-stop.json").read_text()).get("reason")
        if reason not in L.RESUMABLE_STOP_REASONS:
            witnesses.append((full, reason))

    assert witnesses, (
        "no committed root carries a non-resumable stop; "
        "the refusal has lost its witness"
    )

    for full, reason in witnesses:
        with tempfile.TemporaryDirectory() as td:
            copy = Path(td) / full.name
            shutil.copytree(full, copy)          # never the original
            try:
                C.prepare_continuation(copy, cycles=1, tokens=10,
                                       check_operator_lock=False)
            except ValueError as error:
                assert str(error) == "CONTINUE_TYPED_STOP_REQUIRED"
            else:
                raise AssertionError("non-resumable root was accepted")

## Current output

    PASS: 5 witnesses all refused

Five `operational_failure` roots. Each is copied, never opened in place:
`prepare_continuation` constructs a writable `Harness` before it reaches
the refusal, and a committed root's contents are never modified.

## Confirms diagnosis: yes

Each witness clears every earlier guard — no
`CONTINUE_CHECKPOINT_REQUIRED`, no
`CONTINUE_WORKFLOW_CHECKPOINT_REQUIRED`, no
`CONTINUE_STOP_DIGEST_MISMATCH` — and fails at
`continuation.py:352`, the branch reached only when a run holds neither
a terminal lifecycle decision nor a resume decision.

## Mutation proof: two mutations, and they prove DIFFERENT things

| mutation | result | which assertion fired |
|---|---|---|
| none | `PASS: 5 witnesses all refused` | — |
| widen `RESUMABLE_STOP_REASONS` to include `operational_failure` | `GUARD` | the non-empty witness guard |
| `continuation.py:352` raises `CONTINUE_NOT_AUTHORIZED` instead | `REFUSAL` (5/5 wrong) | the per-witness refusal assertion |
| restored | `PASS` | — |

Both kill the test, so both are valid proofs — but they are not
interchangeable, and treating them as one would leave half the artifact
unproven:

- **Widening the frozenset** empties the selection, so the guard fires.
  It proves the witness set cannot silently become empty. It proves
  NOTHING about the refusal.
- **Neutralising the raise** leaves 5 witnesses selected and all 5
  return the wrong error. It proves the refusal itself.

### A correction to the proposed proof, measured rather than assumed

The instruction proposed mutation-proving "via a temporary
`RESUMABLE_STOP_REASONS` widening". Taken as a proof OF THE REFUSAL that
would have been vacuous, and I checked before relying on it. With the
selection filter held fixed (roots hardcoded to the
`operational_failure` set) and only the frozenset widened:

    baseline : CONTINUE_TYPED_STOP_REQUIRED: 5   other/accepted: 0
    widened  : CONTINUE_TYPED_STOP_REQUIRED: 5   other/accepted: 0

Unchanged. The reason is structural: `continuation.py:352` is reached
when `terminal_lifecycle_decision is None`, and `RESUMABLE_STOP_REASONS`
is consulted at `lifecycle.py:273` inside `build_resumed_lifecycle`,
which only runs when a terminal decision EXISTS. On these roots the
frozenset is never read at all.

It kills the artifact as written only because the artifact's SELECTION
also reads that frozenset. That is a real and useful property — the
witness set is defined against the product's own notion of
resumability, so a product change that reclassifies these stops cannot
leave the test quietly passing over nothing. It is just not a proof that
the refusal works, and both are recorded rather than one standing in for
the other.

## What the witnesses are, and why the set is durable

From DIAGNOSIS.md's census of all 28 committed roots carrying a
`run-stop.json`:

| stop reason | typed receipt | roots | selected |
|---|---|---|---|
| `budget_exhausted` | yes | 16 | no — resumable reason |
| `budget_exhausted` | no | 7 | no — resumable reason |
| `operational_failure` | no | 5 | **yes** |

The 5 selected are the permanent class: `operational_failure` is absent
from `RESUMABLE_STOP_REASONS`, no code path gives it a typed receipt,
and a committed root's stop record never changes. The set can grow; it
cannot shrink without a deliberate product decision, which is exactly
what the guard exists to announce.

**The 7 receipt-less `budget_exhausted` roots are deliberately NOT
selected**, though they reach the same raise (DIAGNOSIS.md probed two of
them). They are the pre-`2d4ca2e1` population, and their reason is now
resumable — selecting them would tie the witness set to a historical
accident rather than to a property, and the doctrine is to anchor to
meaning.

## Cost, measured, because a gate test is paid for on every run

| selection strategy | time | witnesses |
|---|---|---|
| open a `Harness` per root and read `workflow_state` | **63.3 s** | 12 |
| read each root's `run-stop.json` | **0.11 s** | 5 |

Opening 28 harnesses means 28 full replays. The property in the
selection is therefore read from the stop record, not from replayed
state, and the refusal itself does the rest of the work: a witness that
somehow gained a receipt would raise a DIFFERENT error and fail loudly
rather than be skipped.

Copy and probe of the 5 witnesses: **~8 s** (24.7 MB / ~10 700 files for
all 12; 7.3 MB for the selected 5). Excluding `blobs/` from the copy
saved 0.8 s — not worth diverging the fixture from the real root, so the
copy is complete.

Total artifact runtime **~8 s**, against a 707 s gate.

## Post-fix expectation

The artifact becomes a test in `tests/`, and:

    python -m pytest tests/ -q -n 4   -> 3340 passed, 0 failed

with the same two mutations still killing it. Nothing about the current
output changes — this reproduction PASSES today, because the product is
correct and the gap is the absence of a guard. That is the difference
between this tranche and a defect tranche, and it is why the mutation
proof, not the pass, is the evidence that matters.
