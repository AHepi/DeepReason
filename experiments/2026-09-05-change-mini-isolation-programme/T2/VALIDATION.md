# Validation for: T2 — relaxed forms and the commitment switch (S2, S3)
Sub-tranche T2 of the mini isolation programme. Phase: `dr-validate-change`.
Base: `577365da4` (T1's delivery head). Branch: `claude/mini-isolation-t0-t2-upwc47`.

T2 makes R2 and R3 real, and they are one change rather than two: relaxing what
a mini seat may say buys nothing while the mandatory well-formedness commitment
destroys every free-prose candidate on arrival.

## Acceptance checks

**S2, accept 1** — every registered form, no bound.

    $ python -c "
    from minireason.forms import resolve_mini_form, mini_form_ids
    import json
    assert 'mini.conjecturer.legacy-v0' in mini_form_ids()
    for fid in mini_form_ids():
        schema = json.dumps(resolve_mini_form(fid).wire_model.model_json_schema())
        assert 'maxLength' not in schema, (fid, 'a mini form bounds a string')
    "
    SPEC S2 accept: OK -> ('mini.commitment.relaxed.v1',
                           'mini.conjecturer.legacy-v0',
                           'mini.conjecturer.relaxed.v1',
                           'mini.critic.relaxed.v1')

: **PASS**. The committed test widens it to `maxItems` as well, and checks the
whole rendered schema rather than the fields this tranche wrote — a bound added
later to a nested model would be just as much a limit and just as invisible.

**S2, accept 2** — the registry's own suite.

    $ python -m pytest mini/tests/test_mini_forms.py -q
    9 passed in 0.45s

: **PASS**

**S2, accept 3 (R-stored)** — the stored form's rendered wire schema is
byte-identical to today's, pinned by a golden committed in the same step.

    $ python -m pytest mini/tests/test_mini_forms.py::test_the_stored_form_is_byte_identical -q
    1 passed

Committed at `mini/tests/goldens/mini_stored_conjecturer_form.json` (1 236
bytes), **before** the registry that would have made changing it easy.
Mutation-proven: nudging one title turns it red with a message that says what
to do instead — register a form beside it.

: **PASS**

**S3, accept 1** — the two-line accept, verbatim from SPEC.md.

    $ python -c "
    from minireason.checks import compile_checks
    from minireason.policy import MiniCommitmentPolicyV1
    off = MiniCommitmentPolicyV1(mandatory_skeleton_wf=False, model_authored_forbidden=False)
    assert compile_checks('free prose, no skeleton', policy=off) == []
    assert compile_checks('free prose, no skeleton') != []   # default unchanged
    "
    OK

: **PASS**

**S3, accept 2** — a run under the disabled policy records ≥1 surviving
conjecture AND a typed commitments-disabled warning.

    summary   {stop: queue-exhausted, cycles: 3, problems: {pi-0: 6}, refuted: 0}
    survivors 6
    warning markers in the record:
      mini:commitments-disabled:skeleton-wf
      mini:commitments-disabled:model-authored-forbidden
      mini:commitments-disabled: these cycles ran without skeleton-wf,
                                 model-authored-forbidden
    replay digest matches: True

    $ python -m pytest mini/tests/test_mini_commitment_policy.py -q
    6 passed in 1.27s

: **PASS**. The same free-prose endpoint under the DEFAULT policy ends 6
admitted, 6 refuted, zero survivors — the design's own measurement, now a
committed test rather than a proof file. The flip is the whole of R3.

**C4** — the full harness's two briefs stay byte-identical.

    $ python -m pytest tests/test_conj_pack_legacy_golden.py \
        tests/test_crit_pack_legacy_golden.py -q
    15 passed in 0.40s

: **PASS**

## Full gate

    $ python -m pytest tests/ -q -n 4
    5084 passed, 6 skipped in 1320.70s (0:22:00)      -> 0 failed
    $ python -m pytest mini/tests/ -q
    116 passed, 1 skipped in 6.05s                    -> 0 failed

: **PASS**. The full gate is UNCHANGED from T1, which is the expected result
rather than a coincidence: `git diff --stat 577365da4..HEAD -- src/` is empty.
Mini's ring went 101 → 116.

## Record-behavior preservation

The commitment policy changes what a run COMPILES, never what a compiled
commitment means, and never the record's shape. Proven:

- `replay(root).digest() == Session(root).state.digest()` on a run with both
  channels off (`test_with_both_channels_off_free_prose_survives`).
- The default policy compiles exactly what it compiled before
  (`test_the_default_policy_is_unchanged` compares `compile_checks(text)` with
  `compile_checks(text, policy=MiniCommitmentPolicyV1())`).
- The warning is recorded through the existing `Session.measure` idiom — the
  same one `budget-exhausted` already uses — so it is an ordinary Measure
  event and no event schema moved.

## Frozen-surface diff

    $ git diff --stat 577365da4..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/
    (no output)
    $ git diff --stat 577365da4..HEAD -- src/
    (no output)

: **PASS** — empty, and the second line is stronger: T2 changed no file under
`src/` at all.

**A frozen-surface FALSE POSITIVE, disposed as SPEC.md predicted.** Declaring
the bare symbol `run` to `blast_radius.py` returned `CONTACT` on all five
surfaces plus the frozen-adjacent one, because `run` is a substring of ordinary
words in each of those files. SPEC.md's own forecast documents this exact shape
(disclosure (2), the `clamp` false alarm's sibling) and says the lesson is to
declare precise symbols. Re-run with precise symbols:

    frozen_surface_verdict: CLEAR   contacts: []   adjacent: []

The mechanical tripwire above agrees, which is why it exists.

## Map

    docs_verify:            6 failed  : PASS (the same six as T0 and T1)
    docs_verify --audit:    1 finding : PASS (the same known row)
    docs_verify --links:    0 dangling, 81 document(s) : PASS
    docs_verify --stale:    23 document(s), none of them this tranche's

**New checks added by this change** — three, in `SUB-minireason.md`, in the
same commit as the code they describe:

| claim now checkable |
|---|
| the mini form suite and the commitment-policy suite both pass |
| both channels switch independently, the default warns not at all, and the disabled policy emits exactly three markers |
| no registered form's schema, at any nesting depth, carries a score, rank, weight, confidence, priority, authority or severity field |

One existing row was CORRECTED rather than added to: it said mini owns "which
commitments a candidate must satisfy", which this change makes wrong in a way
that matters. Mini owns which channels it COMPILES; it never owns what a
commitment means.

**Record observables added vs sweep probes.** One: the
`mini:commitments-disabled` markers in a run's Measure events. It is a typed
record observable, and it has no sweep probe — but the sweep is RETIRED as an
instrument (operator ruling 2026-08-22, CLAUDE.md: "it just wastes time"), and
no tranche may require sweeping committed roots. The obligation is discharged
the way that ruling says to: two targeted, mutation-proven regression tests on
the run that produces it, one asserting the markers are present and name both
channels, one asserting their ABSENCE under the default policy.

**wheel smoke:** packaging surface untouched — smoke not owed. T2 changed no
entry point, no MCP tool, no schema and no wheel layout; it changed no file
under `src/` at all.

## Requirement sweep

| R | operator's words (short) | disposition after T2 |
|---|---|---|
| R1 | "mini needs to be tested in isolation" | **done** in T1 |
| R2 | "mini artifact forms need to not limit prose length at all" | **done for two of the three limits, and the third is named.** No `max_length` or `maxItems` on any field of any registered form, and no required skeleton. The third limit — the truncation of what a seat is SHOWN — belongs to the brief and is T3's (S5) |
| R3 | "run its full conjecture/criticism cycles with commitments disabled" | **done** — two independent switches, a typed warning per disabled channel in the record, and 6 survivors where there were 0 |
| R4 | "a new kind of artifact that generates commitments" | its FORM ships here (`mini.commitment.relaxed.v1`, whose only requirement is naming its conjecture); its seat is T4 (S4) |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | owned by T3 (S5) |
| R6 | "conjecturers see everything generated so far" | owned by T3 (S5) |
| R7 | "all three seats … the same pluggable interface with relaxed forms" | the RELAXED FORMS half is done — one per seat, registered and versioned; the shells are T3 (S6) |
| R8 | "Don't change the controller just yet" | **honoured** — no hook declared, no controller called |
| R9 | "the mini flow … adjustable in a pluggable way" | file-declared half done in T0; the flow is T5 |
| R10 | "add new artifact types on the fly" | a form for a new artifact type is now a registration; the rest is T5 |
| R11 | "test this new config in isolation" | **done** in T1 |
| R12 | "starting input should be standard" | **done** in T1 |
| R13 | "within mini, criticism can't overturn anything" | **honoured, and now enforced** — the critic and commitment forms carry no score, rank, weight, confidence, priority, authority or severity field, checked by enumerating every registered schema; no elimination road exists |
| R14 | "the point is content generation for now" | **honoured** — no authority path changed |
| R-stored | "the current default conjecture form … stored but not deleted" | **done** — registered beside the relaxed one, holding the shipped contract instance, pinned byte-for-byte by a golden committed before the registry |
| R-again | episodes | deferred (window: "episodes (R-again, later)") |
| R-history | one more history experiment | deferred (operator: "But before that:") |

## Assumptions carried

- **A1 — "commitments disabled" means BOTH channels: EXERCISED and confirmed
  here.** The committed before-state test reproduces the measurement A1 rests
  on — with only the model-authored channel disabled, `skeleton-wf` still
  refutes every free-prose candidate on arrival. Both switches remain
  independent, so the operator can restore either.
- **A2 — "not limit prose length at all" means all three limits: two
  discharged, the third named and assigned to T3.**
- A3, A4, A5, A7, A8 — unchanged, none decided by T2.
- **A6** — amended in T1; unchanged since.
- A9 — Q-A is an operator ruling (E1 only), not an assumption.

## Budget

**EXCEEDED and re-baselined, not absorbed.** 413 insertions against 175,
itemised per file in SPEC.md §Budget with code separated from docstring
(`forms.py` 305 = 150 code / 69 docstring / 13 comment / 74 blank;
`policy.py` 72; `checks.py` 16; `loop.py` 20). Trimmed before disclosing: two
near-identical passthrough contracts merged and the module docstring cut,
319 → 306 on `forms.py`.

**Parked as P7**, because this is the second consecutive overrun and both have
the same cause: SPEC.md's numbers priced the MECHANISM, not the obligations the
standing laws attach to it. T3–T7's numbers were written the same way and
should be read as lower bounds.

## Verdict: PASS
