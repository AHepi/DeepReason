---
name: denotation-tests
description: Executable checks of a pin against the twin (Reed 4), including the option-level discrimination check (FR-20) - for every pair of live candidate options, name the observable that separates them or declare the choice observationally vacuous.
---

# Denotation Tests (Reed 4)

<!-- PROMPT-CORE-BEGIN -->
A pin without passing denotation tests is prose, not a pin.

1. For each battery instance, emit one executable check against the
   twin: the pin HOLDS on every positive, FAILS on every negative, and
   the boundary case's observed behavior is recorded (not asserted).
2. Tests are validation obligations: they ship inside the pin record,
   run green before sealing, and re-run whenever the pin, the battery,
   or the twin changes. A red test blocks sealing; it never gets edited
   green without an amendment note saying which side moved.
3. Direction of fit is fixed: when a test fails, first ask whether the
   BATTERY expresses the intent correctly; only then adjust the clause.
   Adjusting the battery to save a clause requires a written reason.
4. Vacuity guard: each certificate row the term occurs in is still
   satisfiable AND still falsifiable under the pin; both recorded.
5. DISCRIMINATION CHECK (FR-20): when the record offers the decider
   more than one live option, then for EVERY pair of options either
   name the battery instance (or constructed fixture) whose observed
   status separates them, or declare the pair OBSERVATIONALLY
   INSEPARABLE. Inseparable means the choice is convention, not
   semantics, and the decider must be told before deciding - a fixture
   that "obviously would" separate them does not count until it has
   been run (FR-25). The source cycle found a three-option decision
   with NO separating fixture, late and by accident; this check makes
   that discovery mandatory and early.
6. PROVE THE GUARD (FR-18): every test in the record has been seen to
   FAIL once - against the planted wrong reading, or with the fix
   reverted. A test never seen red is not yet a test; record when and
   how each went red.
7. Report format per test: PASS | FAIL | NOT_APPLICABLE with instance
   id; totals never substitute for the per-instance list.
<!-- PROMPT-CORE-END -->
