# Goal: `continue_run` over MCP no longer answers a completed non-resumable run with an ERROR; decide which side is stale by measuring the response body first
Class: defect
Observed: at `c45b9dff`, `python -u scripts/wheel_operational_smoke.py`
exits 1 with
`{"schema":"deepreason-wheel-operational-failure-v4",
"stage":"continuation_rejection","failure_kind":"assertion_failed",
"timeout":false,"mcp_liveness":"alive","cleanup_completed":true}`. The
raising site is `MCPClient.tool_error`, which requires the response to
BE an MCP error:

    is_error, text = self._response_text(response, stage=stage)
    if not is_error:
        raise OperationalSmokeFailure(stage=stage, failure_kind=FAILURE_ASSERTION)

The smoke calls `continue_run` on a run it has just driven to a
completed, non-resumable terminal state and expects the facade to refuse
with `CONTINUE_TYPED_STOP_REQUIRED` (`_assert_non_resumable_rejection`
accepts exactly `"CONTINUE_TYPED_STOP_REQUIRED"` or
`"ValueError: CONTINUE_TYPED_STOP_REQUIRED"`). A NON-error response came
back instead, so the refusal never reached the assertion that inspects
its text. Evidence:
`experiments/2026-08-05-fix-qualification-inventory-pins/PARKED.md` V1
and `VERIFY.md`.

Success criterion (machine-decidable):

    python -u scripts/wheel_operational_smoke.py
    -> exits 0

    python -m pytest tests/ -q -n 4
    -> ends "0 failed" (3338 today; no existing assertion weakened)

    python scripts/wheel_smoke.py
    -> exits 0

    python tools/docs_verify.py
    -> "docs_verify: 0 failed"

In scope (3):
- `scripts/wheel_operational_smoke.py` — `_assert_non_resumable_rejection`
  and its `tool_error` call, IF the measurement shows the refusal is
  present as a structured non-error result.
- `src/deepreason/application/text_runs.py` +
  `src/deepreason/mcp/` — the continue dispatch and the MCP facade that
  wraps it, IF the measurement shows the refusal is absent or the run
  actually continues. **Gated: operator words required before any `src/`
  edit** (see below).
- The tranche directory.

NOT in scope: **V2**, the set-vs-tuple `EXPECTED_MCP_TOOLS` duplication
across the two smokes. The operator's instruction: it "stays parked
unless the fix touches those pins anyway." This tranche has no reason to
touch them; if a fix somehow lands on them, that is recorded as a
widening before the edit, not after. Also not in scope: every stage
BEYOND `continuation_rejection`, which has never run in this container
and may hold its own staleness — that is a separate finding if it fires,
not this tranche's goal.

Budget: <=150 changed lines, 1 commit, ~2 hours.
Stop conditions inherited from orchestrator: yes.

## The operator's method constraint, binding on `dr-diagnose`

> "First measurement before any theory: call continue_run over MCP on a
> completed run and capture the FULL response body."

No hypothesis is admissible before the body is in hand. The smoke is
payload-free by design and structurally cannot show it, so the
measurement needs a client that can — against a retained run, not
against a committed root.

The two readings the body separates, and they need different fixes:

1. **Surface shape changed** — the typed `CONTINUE_TYPED_STOP_REQUIRED`
   refusal IS present, delivered as a structured NON-error result rather
   than an MCP error. Then the smoke's reader is the stale side: fix
   `_assert_non_resumable_rejection` to assert on the structured
   refusal, and establish WHEN and WHY the shape changed so the
   same-commit pin rule covers it. No `src/` change.
2. **Product regression** — the refusal is absent, or the run actually
   continues. Then diagnose from the typed record and bisect since
   2026-07-27. **Frozen surfaces are in play and the tranche STOPS for
   operator words before any `src/` fix.**

Neither is established. Assuming either before the body is read is the
mistake this tranche is explicitly instructed to avoid.

## Map preflight (resolved ids)

- `DR-CON-run-identity` — owns start-vs-continue dispatch. Its table
  names `application/text_runs.py` :: `TextRunApplicationService.start`,
  `.continue_run`, `._launch` as the site, and a check at line 95 pins
  the `RUN_ALREADY_STARTED` ordering inside `_launch`. Read before the
  record.
- `DR-SUB-application` — owns `text_runs.py`; its check at line 102
  pins `continue_run` as a method of `TextRunApplicationService`.
- `DR-SUB-periphery` — owns the MCP/CLI edge the smoke drives.
- `DR-INV-frozen-surfaces` — read. **None of the five surfaces names
  the continue dispatch or the MCP facade.** The governing principle
  still bites on reading 2: a refusal that stops being a refusal changes
  what a future run may do, which is ordinary work, but if the stop
  TYPING itself moved then past roots' stop reasons are implicated.
  Measure the difference rather than assume it; `tools/root_sweep.py`
  is the instrument if reading 2 holds.

### Two map findings, recorded at preflight

- **`application × periphery` is an unwritten seam, and is not even in
  `INDEX.md`'s matrix.** Per `INDEX.md`, absence from the table means no
  measured import traffic — but this tranche's defect lives exactly on
  that pair (an MCP tool wrapping an application-service method). Either
  the traffic is function-local, as it is for `periphery × verification`,
  or the pair is genuinely uncoupled and the MCP facade reaches the
  service some other way. Which one is a question for the measurement,
  not an assumption.
- **`SUB-application.md`, `SUB-periphery.md` and `SUB-amendment.md`
  exist on disk but appear in no `INDEX.md` table.** `--links` checks
  that `DR-` references resolve, not that every document is routable
  from the index, so this gap is invisible to the instrument. Recorded
  here; parked unless the fix touches those documents anyway.
