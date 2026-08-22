# Parked — Rung 1b-ii

## P1 — R37-R41: attribution-priority allocation forms

**What.** The v2 program's Amendment 3 table lands R37-R41 (the token-optimisation
system prioritising attribution creation, multiple forms, detection signals for
which form is needed, a config-routed depth-vs-breadth sensitivity dial that
functions automatically but stays adjustable) "at Rung 1b-ii". This tranche's
operator message scopes the window to clauses (2), (4), (5) plus the migration
debt and names none of that work. Recorded rather than resolved.

### Ready-to-send prompt

```
Rung 1b-iii of the v2 calculus program: attribution-priority allocation forms.
Route through dr-change-orchestrator.

AUTHORITY: experiments/2026-08-14-change-calculus-reconciliation-v2/REQUEST.md
Amendment 3 (R37-R41), operator verbatim: "the gap needs to be filled by
upgrading the token optimisation system ... multiple different forms. Each
prioritising attribution creation differently. There will need to be signals
specifically designed to detect when particular forms are necessary. This will
probably be routed through config with options for users to adjust sensitivity:
a depth vs breadth sort of setup. Whatever the setup, this system needs dials
that can function automatically, but still be adaptable for user needs."

READ FIRST: experiments/2026-08-21-change-rung1b-ii-signal-consumption/
DELIVERY.md (the consumption side: seat-instance keying, the policy-referenced
signal set, open-loop notices), then docs/map/INV-signal-contract.md and
docs/map/REC-add-signal.md.

SCOPE: R38 (multiple forms), R39 (signals declared through the contract that
detect when a form is necessary), R40 (config-routed depth-vs-breadth
sensitivity), R41 (automatic by default, adjustable). R42's experiment program
is NOT this tranche.

HARD CONSTRAINTS carried from Amendment 3's own guardrails: allocation touches
EFFICIENCY, NEVER EVIDENCE; H1 is not reopened (failure -> attention is legal,
failure -> problem is not); formalism-optional; all configurations compile with
a typed open-loop notice.

SEQUENCING, recorded by the program itself: ship the channel and ONE
deliberately dumb producer first (Rung 2) before tuning multiple forms against
live data. The reverse order repeats the E28 pattern.
```

## P2 — the blast-radius gate fires CONTACT on every controller change

**What.** `tools/blast_radius.py` matches frozen-surface contact by grep.
`Controller`, `cap_envelope` and `is_generator_knob` are all NAMED inside
`src/deepreason/invariants.py`, so any tranche declaring one of them as a target
symbol gets `frozen_surface_verdict: CONTACT` and a mandatory operator STOP,
whether or not it intends to touch `invariants.py` at all. The gate says so
itself in each detail string ("grep-based; not proof of semantic contact"), so
this is disclosed, not hidden — but the cost lands on every future controller
tranche.

Not a defect of this tranche and not fixed here: changing the gate's matching
rule would change what every future spec is required to disclose, which is an
operator decision about disclosure, not an implementation detail.

### Ready-to-send prompt

```
Route through deepreason-orchestrator (dr-set-goal first).

GOAL CANDIDATE: tools/blast_radius.py reports frozen_surface_verdict CONTACT
for any change declaring Controller, cap_envelope or is_generator_knob as a
target symbol, because those names appear inside src/deepreason/invariants.py
and SYMBOL_INDIRECT contact is decided by grep. Evidence:
experiments/2026-08-21-change-rung1b-ii-signal-consumption/SPEC.md,
"Frozen-surface contact forecast" (the tool's own verbatim output, including
a demonstrated FALSE POSITIVE on `clamp` vs clamp_reserved_attention_fractions
in run_manifest.py, measured at M3).

THE QUESTION FOR THE OPERATOR, not for the implementer: is a grep-wide
SYMBOL_INDIRECT tier the disclosure they want (every controller tranche stops),
or should SYMBOL_INDIRECT resolve the symbol before claiming contact? Both are
defensible; the gate exists to make the operator's words informed, and an
alarm that always fires informs nothing.

DO NOT weaken the gate without those words. The recorded reason the gate exists
at all is docs/ERRATA_EXECUTOR.md X9/XE1 and the 2026-08-09 incident where a
frozen-surface stop written in prose was silently outrun.
```

## P3 — a sweep probe for the `open_loop` observable

**What.** The `open_loop` key on the `controller-authority` Measure payload is a
new typed-record observable. No sweep probe is owed today and the reason is
recorded rather than assumed: zero of the 107 committed roots contain a
controller policy body or an authority record at all, so any probe would read
"-" on every row. It becomes owed the first time a live run records one. (See
P4: the sweep itself is being retired, so this may be discharged by that tranche
instead of by a probe.)

## P4 — remove the root sweep (R21)

**What.** The operator, 2026-08-22, verbatim: "ok. root sweep needs removal. It
doesn't matter whether old records still verify." This is the 2026-08-14 law
("old runs do not need to be valid or returnable") carried to its conclusion:
the instrument goes, not just the obligation.

Not done in the Rung 1b-ii tranche because it is a different goal with its own
blast radius. Measured census, outside `experiments/` (whose committed tranche
artifacts are immutable records and must not be edited): **50 references.**

    tools/root_sweep.py                          the instrument itself
    CLAUDE.md                                    the "42-root sweep" rule under
                                                 Build and test
    .claude/skills/dr-drive-harness/SKILL.md     §4 instruments
    .claude/skills/dr-spec-change/SKILL.md       the sweep-probe rule in step 4
    .claude/skills/dr-ask-the-right-question/SKILL.md
    .claude/skills/dr-audit-broken/SKILL.md      an audit dimension runs it
    docs/AUDIT_BASELINES.md                      its recorded baseline
    docs/map/  INV-frozen-surfaces.md, SUB-verification.md,
               SEAM-harness-x-verification.md, SEAM-harness-x-workflow.md,
               SEAM-evaluation-x-rules.md, SEAM-manifest-x-schools.md,
               SEAM-periphery-x-verification.md, SEAM-schools-x-scheduler.md,
               SEAM-schools-x-scratch.md
    docs/harness-spec-v1.7-amendment.md
    docs/proposals/  DETERMINISTIC_GATES_PREPLAN.md,
                     CRITICISM_SYMMETRY_RESEARCH_PREPLAN.md,
                     RECORD_LIFECYCLE_DEFECT_PLAN.md
    tests/test_diff_budget.py

One reference was already handled, because it collided with work in flight:
`SUB-verification.md`'s anchoring trap MANDATED the sweep, and that tranche was
editing that exact trap. The mandate is gone; the census replaced it.

### Ready-to-send prompt

```
Remove the root sweep. Route through dr-change-orchestrator.

AUTHORITY: the operator, 2026-08-22, verbatim: "ok. root sweep needs removal.
It doesn't matter whether old records still verify." This completes the
2026-08-14 law already in CLAUDE.md ("old runs do not need to be valid or
returnable by the way. What's important is that new versions are optimised for
new functions") -- that law retired the OBLIGATION; this removes the
INSTRUMENT.

READ FIRST: experiments/2026-08-21-change-rung1b-ii-signal-consumption/
PARKED.md P4, which carries the measured 50-reference census, and
REQUEST.md Amendment 2 there, which carries the operator's words verbatim.

SCOPE: delete tools/root_sweep.py and remove every live obligation to run it
-- CLAUDE.md's "42-root sweep" rule, the four skills that name it
(dr-drive-harness §4, dr-spec-change's sweep-probe rule in step 4,
dr-ask-the-right-question, dr-audit-broken), docs/AUDIT_BASELINES.md's
baseline row, nine docs/map documents, the v1.7 amendment, three
docs/proposals plans, and tests/test_diff_budget.py.

DO NOT EDIT experiments/*: committed tranche artifacts are immutable records
of what was done at the time, and rewriting them to hide a retired
instrument would be falsifying the ledger. They keep their sweep references
and stay true.

REPLACEMENT, not just deletion -- decide and record it: several map traps
name the sweep as the instrument that must confirm a reader change moved
nothing. SUB-verification.md's anchoring trap has already been converted to
the CENSUS (count the committed roots carrying the input the changed
predicate reads; if zero, no verdict can move). That is cheaper by two
orders of magnitude and stronger -- it says why none COULD move rather than
that none DID. Either generalise it or state, per the operator, that the
question is no longer owed an answer at all.

STOP AND ASK if removal would leave a gate with no instrument for a
CURRENT-version claim: the operator retired old-root obligations, not
within-version integrity, which is the epistemology itself (CLAUDE.md's
scope boundary on that law).

GATE: full gate 0 failed; docs_verify full (3 pre-existing CON-run-identity
shallow-clone failures are baseline); both wheel smokes. Map moves in the
same commits.
```
