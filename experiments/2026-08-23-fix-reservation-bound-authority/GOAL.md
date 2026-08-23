# GOAL — one authority for the dispatch reservation bound

Route: `deepreason-orchestrator` (defect). Opened from
`experiments/2026-08-22-change-epoch3-second-lineage/PARKED.md` **P6-epoch3**,
which is the authority for this tranche's scope.

## The goal, in one sentence

A work item's reservation bound is computed **once, by one component, over one
set of inputs**, and every other party consumes that number — so a dispatch can
no longer die because two sites disagreed about what the bound is; and whatever
the guard still compares is recoverable from the committed root afterwards.

## Two obligations, one mechanism (operator instruction, 2026-08-23)

1. **ONE AUTHORITY.** The bound is computed once and consumed everywhere else.
   Which component owns it is the diagnosis's call. "Keep two computations in
   agreement" is explicitly out of scope: that is the drift-generator shape this
   repo already rejected once, ledgered as `docs/ERRATA.md` **E26** (the
   single-run-path law — "parity by construction", not parity by agreement).
   This is that law applied at the call boundary.
2. **CLOSE THE OBSERVABILITY GAP.** Whatever the guard compares must be
   recoverable from the record. Store the missing quantity (or its hash plus
   inputs) so a future disagreement is diagnosable from the root alone. Typed,
   per-attempt, additive.

Reproduction obligation: rebuild the attempt-3 rendering shape offline — this
configuration's operator-authored `predicate:` criteria, attached-evidence
manifest and supplements — and show the two bounds diverging **with no
provider**. The fix must make that divergence structurally impossible, proven by
mutation.

## Map ids (preflight, `dr-drive-harness` §4)

Resolved from `docs/map/INDEX.md` before design:

| id | document | why it is in scope |
|---|---|---|
| `DR-SEAM-llm-x-workflow` | `docs/map/SEAM-llm-x-workflow.md` | **the** seam: "the workflow books; the adapter only checks the arithmetic" |
| `DR-SUB-llm` | `docs/map/SUB-llm.md` | `preview_request`, `_render_request`, `call` |
| `DR-SUB-workflow` | `docs/map/SUB-workflow.md` | `reserve_dispatch`, `TokenReservationV2`, replay |
| `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` | workflow v6 transaction record formats |
| `DR-SUB-scheduler` | `docs/map/SUB-scheduler.md` | the controller Traps entry corrected by E43 |

Prior corrections on this same reserve-vs-dispatch agreement, read before
designing: `docs/ERRATA.md` **E42** (a census joined on a convenient key rather
than the frozen one), **E43** (the route-lease `max_tokens` ceiling — the change
that made a *narrowed* cap lawful), **E26** (parity by construction).

## Out of scope — PARKED, not fixed

Anything that is not the bound-authority seam. In particular P5-epoch3 (whether
a token-bounded run should reach a resumable terminal) is a different tranche
and is not touched here, even though it lives in the same two files.

`scripts/` is off limits: a parallel window is building a cycle-soak instrument
there. This tranche's blast radius is the adapter/transaction seam only.

## End state

- `DIAGNOSIS.md` naming ONE cause, derived from the typed record and the source,
  not from a re-run.
- `REPRO.md`: the divergence exhibited offline, no provider.
- `FIX.md`: the single-authority mechanism, with any frozen-surface contact
  requested in writing BEFORE code.
- Regression tests naming run `bb0455384ea09b5b…` in their docstrings, shown RED
  on the unfixed tree.
- Map moves in the same commits as the code.
- Full gate 0 failed; `docs_verify` full mode.
- `VERIFY.md` closing with one line: why no run can die of a bound disagreement
  again, and how the record would show it if one somehow did.
