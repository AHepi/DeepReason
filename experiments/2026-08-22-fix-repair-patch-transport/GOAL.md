# GOAL — the conjecturer seat exhausts its repair budget and ends the run

Tranche opened: 2026-08-22
Branch: `claude/repair-sibling-pointer-defect-fn3itt`
Route: `deepreason-orchestrator` (defect)

## Map preflight (resolved before any design)

| id | why it is in scope |
|---|---|
| `DR-SUB-llm` | owns `src/deepreason/llm/repair.py` — the patch wire shape and `tolerant_patch_value` |
| `DR-SUB-workflow` | owns the metered repair lifecycle |
| `DR-SEAM-llm-x-workflow` | owns `src/deepreason/workflow/repair_transaction.py`, where a repair turn is prepared, issued, assessed and terminalized |

`INV-frozen-surfaces.md` read before designing. **None of the five frozen
surfaces is in scope.** `llm/repair.py` is declared transport-only ("never
selects a route, changes policy, or manufactures a substantive field") and no
record format, digest, manifest schema or qualification subject is touched.

## The phenomenon (typed, from the record)

Epoch-1 live run `40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c`
(retired as `failed-epoch1-run-…`, tranche
`experiments/2026-08-22-live-reach-rich-run/`) terminated at cycle 2 of 24 with
`state=failed`, `stop_reason=operational_failure`,
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`. The typed cause object
`objects/workflow-route-seat-insufficient-capability-v1/80f0c2db…` gives
`reason=smallest_authorized_contract_schema_exhausted`, role `conjecturer`,
seat 0, `observed_provider_calls 5 / maximum 5`,
`attempt_index 4 / maximum_schema_repairs 4`.

Not the ledgered glm-5.2 cap-burn: `attempts_with_zero_completion_tokens = 0`
across all 41 provider attempts.

## The commissioning premise, and why this goal does not carry it

The tranche was opened on the reading recorded in
`experiments/2026-08-22-live-reach-rich-run/PARKED.md` P7-reach: that the seat
returned "a well-formed patch at the SIBLING INDEX of the authorized pointer",
twice, each time on the contract's final repair attempt.

**That reading is falsified by the record** (see `DIAGNOSIS.md`, Finding 0).
Every one of the 13 repair turns dispatched in the run was answered with a
patch addressed INSIDE its own dispatched authorized set. There were zero
off-target patches. The parked census compared each response against the
attempt's `diagnostic_ref`, which `repair_transaction._terminalize_invalid`
sets to the diagnostic derived AFTER the response — the next envelope, not the
one dispatched.

So this goal is stated over the phenomenon (the seat exhausts its metered
repair budget and kills the run) rather than over the hypothesised mechanism.

## The one bounded, falsifiable goal

> A repair turn whose response carries a legal operation at a pointer inside
> its authorized set must not be discarded — and must not consume one of the
> contract's metered repair grants — merely because the provider spelled the
> patch envelope in a lossless transport variant the harness does not yet
> absorb.

## Success criterion

1. Replaying the recorded raw bytes of the six discarded epoch-1 repair
   responses through the fixed path, every response whose loss was purely a
   lossless transport spelling is applied at its recorded authorized pointer;
   every response whose loss was substantive (information the harness would
   have to invent) remains a typed rejection.
2. The fatal turn is shown to survive: `conjecturer.turn.v6` repair #4 — the
   final grant of the chain that exhausted — applies its recorded patch instead
   of being discarded.
3. No pointer outside a dispatched envelope's `authorized_pointers` becomes
   applicable. `apply_repair_patch`'s scope refusal is unchanged and stays a
   typed outcome in the record.
4. No unmetered retry loop is created: the per-contract repair grant still
   bounds provider calls exactly as it does today.
5. Full gate 0 failed; `python tools/docs_verify.py` full mode; the covering
   map documents move in the same commits.

## Out of scope (PARKED, not fixed here)

- Anything in `llm/firewall.py`, `llm/adapter.py`, or allocation — a parallel
  window owns the P9 lease-mismatch defect there.
- Raising `--maximum-completion-tokens`: the census rules that failure out.
- Reject-without-consuming semantics as a general rule (see `DIAGNOSIS.md`
  §"The fork the record closes").
