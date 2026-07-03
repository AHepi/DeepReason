"""Anti-relapse gate (spec §3, §11.5) — mandatory before Conj commit.

Three stages, cheap first:
1. Hash: candidate id matches an existing refuted artifact => block.
2. Semantic trigger: embedding NN against the refuted index within
   NEAR_DUP_EPS => run stage 3 against that prior.
3. Battery equivalence: verdict-vector over the active battery matches a
   refuted prior's (~=_B, Def 3.5) => block UNLESS the candidate carries a
   warrant against that prior's refuter. Verdicts differ => admit; log the
   near-miss (capture diagnostic §11.3).

Near-duplicates of ACCEPTED artifacts are never blocked — attention-deduped
only (blocking them would be a diversity gate adjudicating, forbidden §0).
Negative case law lives here, at the gate — never rendered into packs.
"""


def check(candidate, state, refuted_index) -> bool:
    """True iff the candidate may register. TODO(P1: stages 1+3; P2: stage 2)."""
    raise NotImplementedError
