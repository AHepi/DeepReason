# FIX — type the refusal, record it, and make the reader consult what
# `continue` consults

Smallest correct fix for the cause named in DIAGNOSIS.md. Nothing here
changes whether a run terminates, what terminal it reaches, or whether
`continue` succeeds on any configuration. It changes only what is
RECORDED and what is REPORTED.

## F1 — `workflow/lifecycle.py`: the refusal becomes a type

Replace the bare `ValueError("STOPPED refuses unfinished workflow
authority")` at `lifecycle.py:216-217` with

```python
class UnfinishedWorkflowAuthorityError(ValueError):
    code = "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"
```

carrying `outstanding_work_count` and `unconsumed_bound_call_count` off
the snapshot that produced it.

**It SUBCLASSES `ValueError` deliberately.** Every existing handler and
every existing test that catches or matches `ValueError` keeps working
unchanged — `continuation.py:293`'s `except ValueError` wrapper, and
`tests/test_workflow_stop_lifecycle_c4.py:189`'s
`pytest.raises(ValueError, match="unfinished workflow authority")` (the
message still contains that substring, by construction). Typing the
refusal is therefore purely additive at every call site that is not
being fixed.

## F2 — `application/text_runs.py`: a typed refusal gets a typed `except`

`_record_exhaustion_lifecycle_stop` currently returns `None` for three
distinguishable conditions and says which was which nowhere. It now
returns `(stop, refusal)` where `refusal` is a typed record or `None`:

| condition | code |
|---|---|
| the config owns no v1/v2/v3 control plane in an active mode | `TERMINAL_LIFECYCLE_UNSUPPORTED_CONTROL_PLANE` |
| `UnfinishedWorkflowAuthorityError` | `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY` |
| any other `ValueError` from the builder | `TERMINAL_LIFECYCLE_REJECTED` |

The third arm exists because `build_stopped_lifecycle` and
`outstanding_work_snapshot` raise `ValueError` in SEVEN places and the
old handler answered all seven with silence. Splitting it two ways is
the whole point of F1: **the handler can now tell a correct refusal from
a bug.** Both arms still keep the bare stop record, so no run's terminal
moves — but neither is silent any more.

`terminalize_text_run` threads the refusal into the run-result payload as

```json
"terminal_lifecycle_refusal": {
  "schema": "deepreason-terminal-lifecycle-refusal-v1",
  "code": "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY",
  "detail": "...",
  "outstanding_work": 11,
  "unconsumed_bound_calls": 0
}
```

`RunResultV2` is declared `extra="allow"` (`application/models.py:1203`),
so this needs no schema change; `exclude_none=True` means the key is
absent entirely on the ordinary path.

## F3 — `runtime/progress.py`: the polled surface carries the code

`ProgressEvent` gains `terminal_lifecycle_refusal: str | None = None` —
the CODE only, because `progress.jsonl`/`run-status.json` is a flat
operational surface and the structured record lives in F2. The terminal
`progress.emit` in `text_runs.py` passes it.

`ProgressEvent` is `extra="forbid"`, so this field must be declared to be
writable — but it is OPTIONAL with a default, so every historical
`progress.jsonl` line still validates under
`ProgressEvent.model_validate_json`. Checked, not assumed (see PROOF).

## F4 — `application/results.py`: the reader consults `continue`'s own predicate

`_terminal` gains the third half it was missing. `continue`'s gate
(`runtime/continuation.py:218-364`) is

```python
terminal = workflow_state.terminal_lifecycle_decision
current_resume = workflow_state.current_resume_decision
if terminal is not None: ...  elif current_resume is not None: ...
else: raise ValueError("CONTINUE_TYPED_STOP_REQUIRED")
```

so `results` now reads exactly that, from the `Harness` it already
constructs at `results.py:602` — no new file read, no second derivation:

- new fact `continuation_authority`: `True`/`False`, or the typed
  absence `REPLAY_STATE_UNREADABLE` on a root whose state will not
  replay (the reason is already in `ABSENCE_REASONS`);
- new fact `lifecycle_refusal`: the code from `run-result.json`, or the
  typed absence `NO_LIFECYCLE_REFUSAL_RECORD` (added to
  `ABSENCE_REASONS`, whose closure the tests already assert);
- `amend_ready` becomes `valid_typed_terminal AND stop_reason_resumable
  AND continuation_authority` — a conjunction, so it can only ever move
  from `True` to `False`, and only on a root `continue` would refuse.
- the human rendering prints both new facts, glossed.

**Why `amend_ready` and not a new field.** The printed line is *"ready
for `deepreason amend` / `deepreason continue`"* — one claim covering
both verbs. It is false when either verb refuses. P5's separate question
(whether `amend` should also refuse) is untouched: no gate moves, only
the composite claim, and the new `lifecycle_refusal` line names which
verb refuses and why.

## The categorical argument: no committed root's verdict moves

Required by the tranche instruction; stated categorically rather than by
sweep (the root sweep is RETIRED as an instrument, operator ruling
2026-08-22).

1. **No committed root is written to.** Every change is either a
   write-time path (F1, F2, F3) that only executes while a run is
   terminating, or a pure reader (F4) that opens the root
   `read_only=True`.
2. **No replay-validation output moves.** `verify_root`,
   `invariants.py`, `verification/`, `harness.py` event application and
   `capabilities/state.py` digests are UNTOUCHED — the diff does not
   name any of them. `REPLAY_VALIDATION.json` for every committed root
   is therefore byte-identical, and so is the stored verdict `results`
   reports.
3. **No committed root's terminal commitment digest moves.** The new
   run-result key is added to the payload BEFORE `RunResultV2` validation
   and therefore flows into `ensure_terminal_commitment`'s `result_body`
   — for FUTURE runs that carry a refusal only. On every committed root
   the key does not exist and `exclude_none=True` never emits it, so the
   digest input is unchanged byte for byte.
4. **No historical `progress.jsonl` line becomes unreadable.** F3's
   field is optional with a default, so `extra="forbid"` rejects nothing
   that parsed before.
5. **One reader verdict DOES change, and that is the fix.**
   `amend_ready` becomes `False` on a committed root whose STOPPED
   transition was refused. That is not a root's verdict moving; it is
   the reader stopping its false claim about a root whose evidence never
   supported it. The root is unedited and its replay verdict is
   unchanged. P6's own prompt forbids the alternative in terms: *"Do NOT
   'fix' this by making results report resumable... If continue is
   genuinely not supposed to work here, then the terminal is not valid
   and BOTH surfaces must say so."*

## Frozen surfaces

NONE touched. Confirmed against `docs/map/INV-frozen-surfaces.md`: the
five surfaces are `capabilities/state.py`, `harness.py`,
`invariants.py` + `verification/`, `run_manifest.py`, `qualification.py`
(seven paths), plus frozen-ADJACENT `route_fingerprint` in
`llm/firewall.py`. The diff names none of them.

## Regression tests, and how each is mutation-proven

| test | asserts | mutation that turns it RED |
|---|---|---|
| `test_stopped_refusal_is_typed_and_carries_its_counts` | `build_stopped_lifecycle` over a real outstanding snapshot raises `UnfinishedWorkflowAuthorityError` with the counts | restore the bare `ValueError` |
| `test_a_refused_terminal_records_the_refusal_and_results_says_not_ready` | run-result.json + run-status.json carry the code; `results_summary` gives `amend_ready False`, `continuation_authority False`, the refusal code | restore `except ValueError: return None` |
| `test_an_unrefused_terminal_still_reports_ready_and_still_continues` | the CONTROL: an ordinary manifest-launched root keeps `amend_ready True`, carries its lifecycle decision, and emits no refusal key | any change that makes the new conjunct False unconditionally |

**Declared limit of the second test, so nothing is claimed for it that it
does not prove.** It injects the typed refusal at
`build_stopped_lifecycle` rather than manufacturing eleven real
outstanding work orders. What it proves is the CALLER's handling — which
is where the defect is. That the refusal genuinely fires on real
outstanding authority is proven separately by the first test (a real
`outstanding_work_snapshot`) and end-to-end by the 98-second soak in
VERIFY.md, which is too slow to sit in the gate.

## Predicted fixture update, declared BEFORE the change

`tests/test_results_command.py:486-498` asserts the terminal block's key
set is exactly four keys and that `amend_ready == valid_typed_terminal
and stop_reason_resumable`. Both statements are of the two-half formula
this fix replaces. They are updated minimally to the three-half formula
— the key set gains the two new facts, and the `amend_ready` assertion
gains the third conjunct. No assertion is weakened: the test still
derives the expected value from the record rather than from the code.
