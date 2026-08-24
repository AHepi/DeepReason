---
name: discharge-typing
description: Every ledger verdict types its evidence route (Warp W4) - EXHAUSTION, MODEL_CERT, PROOF, WITNESS, INDEPENDENCE - keeps narrow greens narrow, and now enforces run-over-read (FR-25).
---

# Discharge Typing (Warp W4)

<!-- PROMPT-CORE-BEGIN -->
Every recorded verdict cites exactly one discharge route and its checker.

1. Routes: EXHAUSTION (full finite-domain sweep; twin runner),
   MODEL_CERT (certified structure satisfying the theory and falsifying
   the target), PROOF (derivation; name the checker, incl.
   HAND_PENDING_MECHANIZATION), WITNESS (certified constructed
   instance), INDEPENDENCE (MODEL_CERT for a non-entailment row).
2. A verdict without a route and checker is a claim, not a result; it
   does not enter the ledger.
3. RUN OVER READ (FR-25): a claim about what CODE does admits only
   executed routes - the demonstration script and its actual output, or
   a test that pins it. "Established by reading the source" is PROSE
   and enters no ledger. The source cycle's score: claims checked by
   execution survived or were corrected decisively; claims from reading
   alone failed at roughly a coin-flip rate. Reading is for finding
   what to run.
4. Narrow greens stay narrow: state what the route checked and, in the
   same entry, what it did not. A review's green is scoped to its
   packet (semantic-round-trip rule 5); an instrumented measurement is
   scoped to the fixtures it swept, stated as a lower bound.
5. Status vocabulary is the frozen scheme; a route never upgrades a
   status on its own, and survival never becomes confirmation.
6. HAND_PENDING_MECHANIZATION is honest and temporary: it names the
   conditions under which the mechanization gate opens and blocks any
   downstream reliance reserved for machine-checked routes.
<!-- PROMPT-CORE-END -->
