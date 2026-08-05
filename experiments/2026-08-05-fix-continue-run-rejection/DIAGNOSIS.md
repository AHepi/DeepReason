# Diagnosis: the smoke's run is no longer non-resumable — owner decision 4a made `budget_exhausted` continuable on 2026-07-27, and the smoke still encodes the world before it

Primary cause: `_assert_non_resumable_rejection` asserts a property the
product deliberately stopped having. The smoke's first `deepreason
reason` run halts with `stop.reason == "budget_exhausted"`, and commit
`2d4ca2e1` (2026-07-27 23:54) — **"Make budget-exhausted public runs
typed, continuable stops"** — added `budget_exhausted` to
`RESUMABLE_STOP_REASONS` and gave the exhaustion stop the typed STOPPED
lifecycle receipt that `prepare_continuation` keys on. With a terminal
lifecycle decision present, `continuation.py:352` — the sole
`CONTINUE_TYPED_STOP_REQUIRED` raise site, reached only when the run has
NEITHER a `terminal_lifecycle_decision` NOR a `current_resume_decision` —
is never reached. `continue_run` therefore does the correct thing: it
resumes the run and answers with a non-error handle. The smoke's
`tool_error` call, which requires the response to BE an MCP error,
raises on the non-error.

**This is neither of the two readings GOAL.md set out.** The refusal is
not present-but-reshaped (reading 1), and the run continuing is not a
regression (reading 2): it is an owner decision, implemented
deliberately, covered by a gate test and written into the map. The
tranche stops for operator words anyway — see "What this means for the
fix" — because the remedy is a judgement call about instrument coverage,
not because a frozen surface is in play.

## The measurement, taken first and in full

Per the operator's binding constraint, the FULL response body before any
theory. The smoke's own root could not answer it — the failing run had
already resumed it — so an equivalent root was minted in the same
retained venv (`--keep` temp root
`/tmp/deepreason-wheel-operational-s1jn0e1v`, qualification cache warm):

    run_id            : run-2357b4f22d11442e7049ff8b77184be3
    state             : completed
    stop.reason       : budget_exhausted
    continuations.jsonl exists BEFORE : False

    continue_run FULL RESPONSE BODY:
    {
      "id": 4, "jsonrpc": "2.0",
      "result": {
        "content": [{"type": "text", "text":
          "{\n  \"result_operation\": \"run_result\",\n
             \"run_id\": \"run-2357b4f22d11442e7049ff8b77184be3\",\n
             \"state\": \"running\",\n
             \"status_operation\": \"run_status\"\n}"}],
        "isError": false
      }
    }

    isError                             : False
    CONTINUE_TYPED_STOP_REQUIRED present: False
    continuations.jsonl exists AFTER    : True
    run_status AFTER                    : activity "continuation prepared",
                                          phase "resume"

The refusal is **absent, not reshaped**. The run **actually continues**:
a continuation record is written where none existed, and status moves to
`resume`. Reading 1 is refuted by the same body that refutes reading 2's
`isError` expectation.

## Evidence (record pointers)

- `<retained>/blank home/.deepreason/runs/run-656a6e38…/run-stop.json` →
  `{"reason":"budget_exhausted","digest":"c637415618ca…","event_seq":146,
  "schema":"deepreason-run-stop-v1"}` — the smoke's own first run stops on
  budget exhaustion, not on a failure terminal.
- The same root's `run-status.json` after the failing smoke →
  `{"activity":"continuation prepared","message":"resuming after
  c637415618ca","phase":"resume","state":"running","seq":15}`, and a
  non-empty `continuations.jsonl` carrying
  `{"schema":"deepreason-continuation-v1","seq":0,"prior_stop_digest":
  "c637415618ca…","resume_decision_ref":"sha256:d9f67832…"}`. The smoke's
  own `continue_run` call resumed the run — the assertion fired only
  afterwards, on the response shape.
- `git log -S"_record_exhaustion_lifecycle_stop"` and
  `-S"test_budget_exhausted_terminal_is_a_typed_resumable_stop"` both
  return exactly ONE commit: `2d4ca2e1`, 2026-07-27. No bisect needed —
  the change has a single, dated, self-describing site.
- `2d4ca2e1`'s message: *"Owner decision 4a, made explicit today: a run
  that halts on budget exhaustion must be continuable… budget_exhausted
  joins converged in RESUMABLE_STOP_REASONS; failure terminals stay
  non-resumable. The old pin test asserting non-resumability now proves
  the reverse."* It updated the TEST and did not know about the smoke.
- `src/deepreason/workflow/lifecycle.py:28` →
  `RESUMABLE_STOP_REASONS = frozenset({"converged", "budget_exhausted"})`.
- `docs/map/SUB-application.md` Traps already carries this as a named
  trap with a live check: *"A budget-exhausted run must end with a typed
  STOPPED receipt, or it can never be continued"*, checking
  `tests/test_v6_resumed_terminal_revalidation.py::
  test_budget_exhausted_terminal_is_a_typed_resumable_stop`. The map
  documented the behaviour; nothing pointed the smoke at it.

## Why "regression" is ruled out, explicitly

The operator's branch 2 triggers on the observation ("the run actually
continues") and concludes "product regression on the MCP/continue
surface". The record refutes the conclusion while confirming the
observation:

1. The change is a stated **owner decision**, named as such in its own
   commit message.
2. It is **gate-enforced** by a test written in the same commit, which
   the map cites by nodeid.
3. It is **documented** in `DR-SUB-application`'s Traps.
4. It **narrowed nothing**: `failure terminals stay non-resumable`, so
   `CONTINUE_TYPED_STOP_REQUIRED` remains reachable and the protocol is
   intact.

No `src/` change is owed. No frozen surface is touched — and the
governing principle does not bite either: this alters what a FUTURE run
may do (ordinary work), not how a PAST run verifies. Committed roots
keep their stop records unchanged; `RESUMABLE_STOP_REASONS` is consulted
at continuation time, never at replay of a stop that already happened.
The root sweep is therefore not the instrument here, and the tranche
does not run it.

## Why it took until now to see

`2d4ca2e1` landed 2026-07-27 at 23:54 — **after** the last clean
operational-smoke run the operator recalled from that date, and hours
before the sitecustomize shadowing (S1) made the smoke unable to reach
this stage in this container at all. Three defects stacked in front of
it: the entry-point reader, the shadowed loopback fixture, and the
stale qualify pins. Each fix moved the smoke one stage further, and this
is the stage that was waiting.

## Implicated code (2 sites, both in the instrument)

- `scripts/wheel_operational_smoke.py:2059` —
  `_assert_non_resumable_rejection`, which accepts only
  `CONTINUE_TYPED_STOP_REQUIRED`.
- `scripts/wheel_operational_smoke.py:3393` — the `tool_error` call at
  `STAGE_CONTINUATION_REJECTION`, which requires an MCP error before the
  text is ever inspected.

## Falsifiable prediction (what `dr-reproduce` must show)

    # The refusal must still be REACHABLE -- if it is not, the stage has
    # nothing left to test and the diagnosis is incomplete:
    a run whose terminal is a FAILURE (not converged, not
    budget_exhausted) -> continue_run answers isError=true with
    CONTINUE_TYPED_STOP_REQUIRED

    # And the exhausted case must be stably continuable, not flakily so:
    a second budget_exhausted run -> continue_run isError=false,
    continuations.jsonl written, status phase "resume"

If the first half fails, `CONTINUE_TYPED_STOP_REQUIRED` is dead code and
the stage cannot be repaired by choosing a better subject — which would
change the fix.

## What this means for the fix, and why the tranche pauses here

The stage is named `continuation_rejection` and exists to prove the
public facade refuses a run that must not be resumed. Two remedies are
available and they are not equivalent:

- **(a) Keep the coverage.** Point the stage at a genuinely
  non-resumable run — `2d4ca2e1` says failure terminals stay
  non-resumable — so the refusal is still exercised end to end.
- **(b) Follow the product.** Replace the assertion with what now holds:
  a budget-exhausted run continues, and assert the continuation instead.

(b) is cheaper and (a) is what the stage was for. Choosing (b) silently
would delete the only end-to-end proof that the facade can refuse a
continuation at all — the same class of loss as weakening an assertion
to get green. `dr-reproduce` establishes whether (a) is even available;
the choice between them is proposed in FIX.md, not made here.

## Ruled out

- **Reading 1 (surface shape changed).** The body contains no
  `CONTINUE_TYPED_STOP_REQUIRED` in any form, error or structured
  result, and `continuations.jsonl` goes from absent to present. Nothing
  was reshaped; the refusal simply does not apply.
- **The MCP facade mis-wrapping an error as a result.** Refuted by the
  same evidence: a mis-wrap would leave the run untouched, and this run
  moved to `resume`.
- **V2 (the set-vs-tuple pin duplication).** Untouched and still
  parked, per the operator; nothing in this diagnosis reaches those pins.
