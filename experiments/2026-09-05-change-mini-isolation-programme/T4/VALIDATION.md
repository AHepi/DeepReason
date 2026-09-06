# Validation for: T4 — the commitment seat and the controller hook (S4, S7, S11b)
Sub-tranche T4 of the mini isolation programme. Phase: `dr-validate-change`.
Base: `e83df7dfd` (T3's delivery head). Branch: `claude/mini-isolation-t3-t5-7tsc6d`.

T4 makes R4 real and honours R8 in the one form a promise can be held to: the
commitment seat writes a record the authority layer cannot see, and the
controller hook is declared with nothing behind it and nothing calling it.

## Acceptance checks

**S4, accept 1** — the minimum/rejection pair, verbatim from SPEC.md.

    $ python -c "
    from minireason.forms import resolve_mini_form
    m = resolve_mini_form('mini.commitment.relaxed.v1').wire_model
    m.model_validate({'proposals': [{'about': 'a1', 'body': 'x'}]})   # minimum
    import pydantic
    try: m.model_validate({'proposals': [{'body': 'x'}]}); raise SystemExit('about not required')
    except pydantic.ValidationError: pass
    "
    OK: the minimum is accepted; a proposal naming nothing is refused by the form

: **PASS**

**S4, accept 2** — the seat's suite.

    $ python -m pytest mini/tests/test_mini_commitment_seat.py -q
    5 passed in 1.43s

: **PASS**. A proposal is a RECORD — a Measure event naming `mini:record`,
the kind, the conjecture it is about and a blob holding its body — and after
writing two of them the artifact map, the commitment map and every status are
identical, the replay digest matches, `verify_root` is 0. A proposal naming
nothing in the run is dropped with a typed `mini:record-dropped` event. The
spend lands exactly once. The seats that see everything see the proposal
whole; the critic does not, byte for byte, re-proven with the real writer.

**S4, accept 3** — no rank, admission, immunity or refutation path reads the
kind's name.

    $ python -m pytest mini/tests/test_mini_shape_buys_nothing.py -q
    3 passed in 1.31s

: **PASS**. Three limbs: the authority side of the full harness (scheduler,
adjudication, rules, harness.py, invariants.py, verification,
capabilities/state.py) and mini's nine admit/register/guard/refute functions
never contain `commitment-proposal`, `mini:record`, `mini.commitment` or
`mini.criticism`; every mini schema, enumerated at every nesting depth,
carries none of score, rank, weight, confidence, priority, authority,
severity; a proposal about a standing conjecture and one about a refuted
conjecture moves neither status. Mutation-proven twice (step 33).

**S7, accept 1** — the hook's suite.

    $ python -m pytest mini/tests/test_mini_calibration_hook.py -q
    6 passed in 2.53s

: **PASS**. The default resolves to the no-op and it is the only registered
hook; it returns `None` for every input; zero Call nodes to `calibrate` or
`resolve_mini_calibration_hook` under `src/` or `mini/minireason/` (the
window's ruling, on the AST); briefs byte-identical with the hook consulted;
a duplicate registration refused typed. Mutation-proven: one call from the
loop turns it red (step 35).

**S7, accept 2** — exactly two source lines.

    $ grep -rn "register_mini_calibration_hook" src/ mini/minireason/ | wc -l
    2

: **PASS** — the definition and the one no-op registration.

**S11b** — the map.

    $ python tools/docs_verify.py          -> 6 failed (the six known rows)
    $ python tools/docs_verify.py --audit  -> 1 finding (the known one)
    $ python tools/docs_verify.py --links  -> 0 dangling, 82 documents

: **PASS** — see Map below.

## Full gate

    $ python -m pytest tests/ -q -n 4
    5084 passed, 6 skipped in 1381.85s (0:23:01)     -> 0 failed
    $ python -m pytest mini/tests/ -q
    150 passed, 1 skipped in 11.75s                   -> 0 failed

: **PASS**. The full gate is UNCHANGED from T2 and T3, and this time for the
strongest reason: T4 changed nothing under `src/` at all. Mini's ring went
136 → 150.

## Record-behavior preservation

T4 adds a WRITER to the record — the first since the programme began — and a
writer is held to more than a reader:

- The record it writes is an ordinary Measure event with a blob, the same
  idiom mini's `budget-exhausted` and `mini:commitments-disabled` markers
  already use; no event schema, object schema or manifest field moved.
- After writing, `replay(root).digest() == Session(root).state.digest()` and
  `verify_root(root)["violations"] == []` (`test_a_proposal_is_recorded_and_registers_nothing`,
  `test_limb3_a_proposal_changes_no_status_either_way`).
- The road NOT taken is recorded, with its instrument: an artifact under a
  new provenance role reads `frozen_surface_verdict: CONTACT` (surface:
  harness.py event application; tier SYMBOL_INDIRECT; target `Provenance`),
  and no grant exists. Nothing under `src/` changed, so no committed root's
  verdict can have moved; the spot-check over committed roots is not owed.

## Frozen-surface diff

    $ git diff --stat e83df7dfd..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/ \
        src/deepreason/llm/firewall.py
    (no output)
    $ git diff --stat e83df7dfd..HEAD -- src/
    (no output)

: **PASS** — empty, and the second line is the whole of T4's reach into
`src/`: none. `tools/blast_radius.py` at steps 32 and 34: `CLEAR`.

## Packaging surface

packaging surface untouched — smoke not owed. T4 changed no file under
`src/`, no entry point, no MCP tool, no schema and no wheel layout.

## Map

    docs_verify:            6 failed  : PASS (the same six as T0-T3)
    docs_verify --audit:    1 finding : PASS (the known SEAM-llm-x-rules.md:54)
    docs_verify --links:    0 dangling, 82 document(s) : PASS
    docs_verify --coverage: 2 findings, 22 seams without a Sweep header : PASS —
                            both pre-existing, on seams T4 did not touch
    docs_verify --stale:    22 documents, none of them this tranche's after the
                            three re-derived stamps advanced to 9d87325c3

**New checks added by this change** — five, in the same commits as the code
they describe:

| document | claim now checkable |
|---|---|
| `SUB-minireason.md` | the commitment seat's suite passes |
| `SUB-minireason.md` | `records.py` names no artifact, commitment, warrant or status road (AST) |
| `SUB-minireason.md` | exactly two lines name the hook registration, and the hook suite passes |
| `CON-packs-and-token-economy.md` | the reduced engine keeps to the two public entries |
| `INV-render-layout.md` | the retention knobs are the everything plugin's parameters and not arrangement fields |

Each was shown red under a mutation (steps 33, 35, 36 carry the pastes);
`--audit` flags none as vacuous.

**Record observables added vs sweep probes.** One: the `mini:record` /
`mini:record-dropped` Measure events with their `kind:`, `about:` and `blob:`
inputs. It is a typed record observable and it has no sweep probe — the sweep
is RETIRED as an instrument (operator ruling 2026-08-22) and no tranche may
require sweeping committed roots. The obligation is discharged the way that
ruling says: targeted, mutation-proven tests on the run that produces it
(`test_a_proposal_is_recorded_and_registers_nothing`,
`test_a_proposal_about_nothing_in_the_run_is_dropped_typed`,
`test_the_spend_lands_exactly_once`), plus `mini_records` as the reader that
any later probe would call.

## Requirement sweep

| R | operator's words (short) | disposition after T4 |
|---|---|---|
| R1 | "mini needs to be tested in isolation" | **done** in T1; the fence re-run at every module-adding step (3 passed) |
| R2 | "not limit prose length at all" | **done** on the shell road (T2, T3); the call-layer clip stays PARKED P8, binding on T5 |
| R3 | "cycles with commitments disabled" | **done** in T2 |
| R4 | "a new kind of artifact that generates commitments on conjectures, but does not force a strict format" | **done** — the commitment seat reads a conjecture (its shell and layout, T3) and proposes commitments in free prose; the only requirement is naming the conjecture, refused by the form when absent and dropped typed by the writer when it names nothing in the run; the proposal is RECORDED, never registered as a Commitment, and E3 is not built |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | **done** in T3; re-proven here with the real writer, byte for byte |
| R6 | "conjecturers see everything generated so far and so do commitment artifacts" | **done** in T3; the pool now merges artifacts and records in record order, labelled by kind and never by status |
| R7 | "all three seats … calibrated on the fly and modifiable by the controller" | **the interface half done in T3; the calibration half DECLARED here** — `MiniCalibrationHookV1`, a registry selected by id, one no-op registered, nothing behind it and nothing calling it |
| R8 | "Don't change the controller just yet" | **honoured, and enforced**: zero callers on the AST, exactly two registration lines, a duplicate refused typed |
| R9 | "the mini flow … adjustable in a pluggable way" | seat side done (T3); the flow is T5 |
| R10 | "add new artifact types on the fly" | a new type's form, layout, shell (T2, T3) and now its RECORD road (`record_mini_output(kind, …)`, any kind string) are registrations; the flow stage is T5 |
| R11 | "test this new config in isolation" | **done** in T1 |
| R12 | "starting input should be standard" | **done** in T1 |
| R13 | "within mini, criticism can't overturn anything" | **honoured, and structural now**: a mini seat's non-conjecture output is a record outside the artifact map, so no authority path can reach it; the shape-buys-nothing test enumerates every mini schema |
| R14 | "the point is content generation for now" | **honoured** — nothing under `src/` changed |
| R-stored | "the current default conjecture form … stored but not deleted" | **done** in T2 |
| R-again | episodes | deferred (window: "episodes (R-again, later)") |
| R-history | one more history experiment | deferred (operator: "But before that:") |

## Assumptions carried

- **A7 — "on the fly" means at run configuration time: unchanged, and the
  hook is built to that reading.** `calibrate` takes a cycle number so a
  future controller COULD reshape per cycle, but nothing calls it; when the
  operator says how the controller steps in, the resolved hook is still
  selected once per run by id.
- **Decided without asking (dominant under the operator's recorded values):**
  a proposal is a RECORD, not an artifact. Every value the operator has
  stated points the same way — no frozen surface without a grant (the
  artifact road measured CONTACT), criticism overturns nothing (a record
  cannot be attacked or refuted, an artifact can), smallest correct change
  (nothing under `src/`). Override any time; the cost of the other road is a
  grant on the harness surface.
- **Decided without asking:** SPEC S7's "the mini loop calls it between
  cycles" is SUPERSEDED by the window's later ruling ("zero callers"). The
  later operator word wins; recorded in SUB-minireason.md and CHECKLIST 34.
- A1–A6, A8 carried unchanged. A9 is the operator's ruling.

## Budget

**EXCEEDED and re-baselined, not absorbed.** 332 insertions against 180,
itemised per file in SPEC.md §Budget with code separated from docstring
(`records.py` 134 = 63 / 42 / 3 / 26; `seats.py` +129 = +67 code / +17 doc;
`sources.py` +69 = +27 code). T4 restated as ~330; programme ~2 250. The
T4-specific cause: the record shape was chosen over the artifact shape AFTER
measuring a frozen-surface contact the forecast did not cover.

## Verdict: PASS
