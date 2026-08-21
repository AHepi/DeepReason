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
