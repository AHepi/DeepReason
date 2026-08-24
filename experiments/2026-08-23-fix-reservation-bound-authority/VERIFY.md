# VERIFY — reservation-bound authority

Tranche: `experiments/2026-08-23-fix-reservation-bound-authority/`.
Branch: `claude/reservation-bound-authority-h4pn7c`, based on `origin/main` at
`5d9b995ce`.

## What changed

`src/deepreason/llm/adapter.py`, three edits and one error type:

| edit | effect |
|---|---|
| `LLMAdapter._completion_cap(endpoint, lease)` | the ONE definition of a dispatch's completion envelope; `preview_request` returns it |
| `call`'s `transport_limits["max_tokens"]` | under an authorization, CONSUMES `reservation_record.completion_bound_tokens` instead of recomputing from the live endpoint |
| the bound guard's refusal | prints both bounds and writes a diagnostic blob carrying both sides and their inputs |
| `WorkflowAuthorizationError` | gains `diagnostic_ref` |

`tests/test_v6_reservation_bound_authority.py`: four regression tests, all
naming run `bb0455384ea09b5b…` in their docstrings.

Map, in the same commit: `docs/map/SEAM-llm-x-workflow.md` (Meter-ownership and
Prompt-freeze rows, the bound-equality section and its `check:`, the
"What breaks first" gloss, a new `Traps` entry), `docs/map/SUB-llm.md` (the
`self.blobs.put` pin), `docs/ERRATA.md` E46 and E47.

## Instruments

| instrument | result |
|---|---|
| regression tests, unfixed tree | **4 failed** — `proof/regression_red_on_unfixed_tree.txt` |
| regression tests, fixed tree | **4 passed** — `proof/regression_green_on_fixed_tree.txt` |
| `python tools/docs_verify.py` (FULL mode) | **63 documents, 995 checks, 0 failed** |
| `python -m pytest tests/ -q -n 4` (full gate) | **3879 passed, 6 skipped, 0 failed** (18:45) |

Note on `docs_verify`: P4-epoch3 records three shallow-clone failures in
`CON-run-identity.md` on a fresh container. This session ran
`git fetch --unshallow` during setup, so those three do not appear and the
baseline here is a complete clone. The two failures the first full run did
report were both mine — a `spend = _spend(` count pinned at 9 and a
`self.blobs.put` count pinned at 8, which this change moves to 10 and 9. Both
pins were advanced in the same commit as the code, which is why they are listed
under "Map" above and not under "pre-existing".

## Scope kept

- `scripts/` untouched — the parallel window's cycle-soak instrument is not in
  this blast radius.
- `lifecycle.py` untouched — P5-epoch3 stays parked.
- No frozen surface contacted, and no operator grant requested. Replay
  validation admits `attempt.max_tokens ∈ {route.max_tokens} ∪ authorized
  controller caps` (`invariants.py:3988-4004`); the booked cap is inside that
  set, so no verdict moves and no committed root changes.
- The wire is unchanged: `transport_limits` feeds the attempt trace and the
  bound check, never `endpoint.complete`.

## Residue

- The fix is proven against the record and offline. **It has not run live.**
  The pre-authorised repeat for epoch 3 is spent (PREREG_EPOCH3.md §5), so no
  live attempt was launched, and a live recurrence remains the one thing not
  demonstrated.
- `repro/cap_divergence.py` describes expressions that no longer both exist. It
  is kept, and marked historical in its own docstring.
- E47's lesson — a negative search result is only as strong as the proof the
  search could have found the thing — is recorded but not mechanised. Parked as
  **P2-bound**.
- `_completion_cap`'s endpoint fallback is unreachable for the production
  endpoint, so a legacy route whose role spec omits `max_tokens` books a zero
  completion bound. Safe by accident, misleading as written, and outside this
  goal. Parked as **P1-bound**.

Both carry ready-to-send prompts in `PARKED.md`.

## Why no run can die of a bound disagreement again

Because there is no longer a second number to disagree with the first: the
completion cap is defined once in `_completion_cap`, booked once by the
workflow, and read back at dispatch off the reservation the workflow already
recorded — and if the live reservation and its own durable record should ever
disagree, the refusal now writes both bounds, both prompt bounds, the request's
length and digest and the live endpoint cap into a blob, so the next reader
finds the answer in the root instead of deriving it from a run that no longer
exists.
