# FIX — absorb the lossless transport spellings; change nothing else

Cause fixed: `DIAGNOSIS.md` Finding 1.
Blast radius: `src/deepreason/llm/repair.py`, `src/deepreason/llm/wire.py`
(one call site). No frozen surface. Nothing in `llm/firewall.py`,
`llm/adapter.py`, or allocation.

## The principle the fix holds to

> **An echo is not information.** The harness may discard from a patch response
> exactly those bytes it supplied itself, may unwrap a container that could
> never be a valid patch, and may rename a field to its own spelling when the
> target field is absent. It may not supply a value the model did not give.

Everything below is an instance of that. Nothing below widens
`authorized_pointers`, and `apply_repair_patch`'s scope refusal
(`RepairScopeViolation`) is untouched: a pointer outside the dispatched
authorized set remains a typed rejection recorded in the run.

## Change 1 — `tolerant_patch_value` takes the dispatched envelope

    def tolerant_patch_value(value, envelope=None)

Both existing call sites already hold it and must pass it, because the code
requires them to stay in exact agreement:

- `V6PatchRepairSession.candidate_from_raw` -> `turn.diagnostic_envelope`
- `wire.py::RepairPatchWireContract.validate_value` -> `self.envelope`

`envelope=None` keeps the pure-value behaviour for any other caller; the echo
rule is simply inert without one.

## Change 2 — four bounded, ordered normalizations

Applied in this order, each at most twice, no recursion:

1. **Container unwrap (widened).** Today only a single-key dict whose key is
   `repair.patch.v1` is unwrapped. Widen the closed key set to the container
   names the record actually shows: `repair.patch.v1`, `patch`, `patches`,
   `operations`. Provably lossless: `RepairPatchV1` forbids extra fields and
   declares none of these names, so a dict whose single key is one of them can
   never itself be a valid patch. The existing single-element-list unwrap is
   unchanged and still runs on the inner value.
2. **Echo drop.** With an envelope present, remove a key whose value is
   *exactly* what the harness sent: `contract` == `envelope.contract`,
   `baseline_sha256` == `envelope.baseline_sha256`. Also `schema` ==
   `"repair.patch.v1"`, which is `RepairPatchV1.schema_`'s default and only
   legal value, so removing it changes no validated result. Exact equality
   only — a differing value is the model's and stays, so a wrong `schema`
   literal still fails.
3. **Container unwrap, once more**, in case step 2 exposed a lone container
   (`{"contract", "operations":[…], "schema"}` -> `{"operations":[…]}`).
4. **Field-name synonym.** Rename `pointer` -> `path` when `path` is absent
   and `pointer` is a non-empty string, under exactly the guard the existing
   `operation` -> `op` rename already uses. Both renames apply in the same
   pass.

The key sets are **record-driven, not imagined**: every name added appears in
a recorded epoch-1 response. No name is added speculatively.

## What the fix deliberately does NOT do

- **`old`/`new` are not read as `value`.** `atomic-candidate #1` stays a typed
  rejection. Reading them would be an inference about intent, not a rename of
  a field the harness supplied — the line in `DIAGNOSIS.md` Finding 2.
- **No reject-without-consuming.** The grant meters provider calls, and the
  call has already happened when the spelling is seen; not consuming it would
  issue a sixth call against a five-call ceiling. The metering is what makes
  the terminal finite and typed. Rejected with its reason in `DIAGNOSIS.md`.
- **No prompt change.** `patch_repair_prompt` and
  `repair_patch_response_schema` are untouched, so no prompt digest, run
  identity or qualification subject moves. (A worked example in the prompt is
  PARKED, not done here.)
- **No change to `apply_repair_patch`, `enforce_repair_subtree`, the envelope
  format, or any record format.**

## Predicted fixture update (declared before the code, per gate discipline)

`tests/test_v6_patch_repair_and_wire.py::test_schema_name_keyed_patch_wrappers_are_tolerated`
asserts today that `{"patch": {...}}` passes through unchanged:

    assert tolerant_patch_value({"patch": dict(patch)}) == {"patch": dict(patch)}

That assertion encodes the defect: `{"patch": {...}}` is one of the six
discarded epoch-1 responses. It becomes an assertion that the wrapper IS
unwrapped. The two neighbouring ambiguity assertions in the same test —
`{"repair.patch.v1": …, "extra": 1}` (a foreign second key) and
`{"repair.patch.v1": [patch, patch]}` (two patches) — must stay unchanged and
still pass; they are the standing proof that ambiguity is never tolerated.

No other fixture is expected to move.

## Regression tests (mutation-proven both ways)

New, in `tests/test_v6_patch_repair_and_wire.py`, docstrings naming
`run-40e713b30a147dfc` :

1. `test_recorded_epoch1_patch_spellings_are_tolerated` — the five recovered
   responses, verbatim recorded bytes, each asserted to parse to the operation
   and the pointer the run's dispatched envelope authorized.
2. `test_recorded_epoch1_substantive_patch_loss_is_still_rejected` — the
   `old`/`new` response still raises. This is the mutation guard in the other
   direction: a fix that swallows it fails here.
3. `test_envelope_echoes_are_dropped_only_when_they_match` — a `contract` or
   `baseline_sha256` value that DIFFERS from the envelope's is kept and still
   fails validation; a `schema` literal other than `repair.patch.v1` still
   fails.
4. `test_off_target_patch_remains_a_typed_scope_violation` — a well-formed
   patch in a now-tolerated wrapper, addressed outside `authorized_pointers`,
   still raises `RepairScopeViolation`. This is the closest offline analogue
   of the shape the tranche was commissioned on, and it holds.

## Success criterion (from `GOAL.md`)

`repro.py` exits 0; assertions 1-4 above; full gate 0 failed; `docs_verify`
full mode; the covering map documents (`SUB-llm.md`,
`SEAM-llm-x-workflow.md`) gain a `Traps` entry naming
`run-40e713b30a147dfc` in the same commit as the code.
