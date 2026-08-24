---
name: denotation-tests
description: Compile every example battery into executable checks against the twin so a pin's meaning is machine-validated, not asserted (Reed step 4). Use after a candidate pin is fitted to its battery, and as the standing validation obligation on any record containing a definition.
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
   Adjusting the battery to save a clause requires a written reason in
   the record.
4. Vacuity guard: at least one test must show each certificate row the
   term occurs in is still satisfiable AND still falsifiable under the
   pin (both directions, both recorded).
5. Report format is the fixed vocabulary: per test, PASS | FAIL |
   NOT_APPLICABLE with the instance id; totals never substitute for the
   per-instance list.
<!-- PROMPT-CORE-END -->
