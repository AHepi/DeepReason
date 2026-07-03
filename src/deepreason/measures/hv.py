"""Hard-to-vary (spec §6, Def 3.6; §7 hv-floor).

Lazy spot-check on accepted artifacts: variator emits k bounded edits via
mu(.|a); HV_B(a) = 1 - Pr[edit passes B(a) and is inequivalent]. Count only
inequivalent survivors (a rename is the same explanation).

Structural kernel mu_struct is mandatory where content parses as a skeleton
(§10): substitute at role level — mechanism, motive, causal link, scope —
not merely reword (the Persephone test). Rewording-only mu is insufficient
for D5.

hv_estimator (the hv-floor commitment program, §7): B0 = battery minus all
HV-type commitments (stratification is mandatory — HV over a battery
containing itself does not terminate). Verdict pass iff 1 - s_hat >= HV_MIN.
Fail packages an ordinary demonstrative warrant with a four-clause validity
node (kernel fairness, k sufficiency, ~=_{B0} adequacy, B0-for-B adequacy).
"""


def hv_spot_check(artifact, variator, k: int) -> float:
    """Lazy HV estimate; logged with k, re-estimable later. TODO(P2)."""
    raise NotImplementedError


def hv_estimator(candidate, commitment, state, adapter) -> str:
    """hv-floor verdict: pass | fail | overrun. Replay-deterministic. TODO(P2)."""
    raise NotImplementedError
