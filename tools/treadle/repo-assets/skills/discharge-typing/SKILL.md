---
name: discharge-typing
description: Protocol for typing every ledger verdict by its evidence route (Warp W4) - EXHAUSTION, MODEL_CERT, PROOF with named checker, WITNESS, or INDEPENDENCE - and for keeping narrow greens narrow. Use when recording any result, updating a verification ledger, or reviewing whether a claim's status matches its evidence.
---

# Discharge Typing (Warp W4)

<!-- PROMPT-CORE-BEGIN -->
Every recorded verdict cites exactly one discharge route and its checker.

1. Routes: EXHAUSTION (full finite-domain sweep; twin runner),
   MODEL_CERT (certified structure satisfying the theory and falsifying
   the target), PROOF (derivation; name the checker: twin obligation,
   script, proof assistant, or HAND_PENDING_MECHANIZATION), WITNESS
   (certified constructed instance), INDEPENDENCE (MODEL_CERT for a
   non-entailment row).
2. A verdict without a route and checker is a claim, not a result; it
   does not enter the ledger.
3. Narrow greens stay narrow: state what the route checked and, in the
   same entry, what it did not (a route-exact check is not a semantic
   minimality theorem; an in-bounds negative is not an unbounded one; a
   class-relative discharge names its class and annex version).
4. Status vocabulary is the frozen two-axis scheme; the route never
   upgrades a status on its own, and survival never becomes
   confirmation.
5. HAND_PENDING_MECHANIZATION is honest and temporary: it names the
   stability conditions under which the mechanization gate opens, and it
   blocks any downstream reliance the authority calibration reserves for
   machine-checked routes.
<!-- PROMPT-CORE-END -->
